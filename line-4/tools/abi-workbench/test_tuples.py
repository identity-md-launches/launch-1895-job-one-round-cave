"""Tuple encoding and decoding, including nested relative offsets."""
import contextlib
import io
import json
from pathlib import Path
import unittest
from unittest.mock import patch

import abi_workbench as abi

EXAMPLE = Path(__file__).with_name('tuple-example.json')


class TupleTests(unittest.TestCase):
    def test_dynamic_tuple_matches_explicit_word_layout(self):
        params = [{'type': 'tuple', 'components': [
            {'type': 'uint256'}, {'type': 'string'}]}]
        expected = (abi.word(32) + abi.word(7) + abi.word(64) + abi.word(2)
                    + b'hi' + b'\0' * 30)
        self.assertEqual(abi.canonical(params[0]), '(uint256,string)')
        self.assertEqual(abi.encode_tuple(params, [[7, 'hi']]), expected)
        self.assertEqual([x['value'] for x in abi.decode_tuple(params, expected)],
                         [[7, 'hi']])
        self.assertEqual(abi.encode_tuple(params, [[7, 'hi']]),
                         abi.encode_tuple(params, [x['value'] for x in
                                                    abi.decode_tuple(params, expected, strict=True)]))

    def test_static_tuple_is_inline_and_expands_parent_head(self):
        pair = {'type': 'tuple', 'components': [
            {'type': 'uint8'}, {'type': 'bool'}]}
        params = [pair, {'type': 'uint16'}]
        expected = abi.word(3) + abi.word(1) + abi.word(9)
        self.assertFalse(abi.dynamic(pair))
        self.assertEqual(abi.head_words(pair), 2)
        self.assertEqual(abi.encode_tuple(params, [[3, True], 9]), expected)
        self.assertEqual([x['value'] for x in abi.decode_tuple(params, expected)],
                         [[3, True], 9])

    def test_nested_tuple_and_array_components(self):
        nested = {'type': 'tuple', 'components': [
            {'type': 'tuple', 'components': [{'type': 'uint8'}, {'type': 'bool'}]},
            {'type': 'uint16[]'}]}
        params = [nested]
        values = [[[5, False], [8, 13]]]
        encoded = abi.encode_tuple(params, values)
        self.assertEqual(abi.canonical(nested), '((uint8,bool),uint16[])')
        self.assertEqual([x['value'] for x in abi.decode_tuple(params, encoded, strict=True)], values)

    def test_bad_nested_offset_and_bool_rejected(self):
        params = [{'type': 'tuple', 'components': [
            {'type': 'uint256'}, {'type': 'string'}]}]
        encoded = bytearray(abi.encode_tuple(params, [[7, 'hi']]))
        encoded[64:96] = abi.word(0)
        with self.assertRaisesRegex(ValueError, 'offset'):
            abi.decode_tuple(params, bytes(encoded))
        static = [{'type': 'tuple', 'components': [{'type': 'bool'}]}]
        with self.assertRaisesRegex(ValueError, 'bool'):
            abi.decode_tuple(static, abi.word(2))

    def test_nested_signature_selection_and_cli_round_trip(self):
        self.assertEqual(abi.function_reference('put((uint,bool))'),
                         ('put', 'put((uint256,bool))'))
        args = '[ [7,"hi"] ]'
        output, error = io.StringIO(), io.StringIO()
        with patch('sys.argv', ['abi', 'encode', '--abi', str(EXAMPLE),
                                '--function', 'put((uint256,string))', '--args', args]), \
                contextlib.redirect_stdout(output), contextlib.redirect_stderr(error):
            status = abi.main()
        self.assertEqual((status, error.getvalue()), (0, ''))
        result = json.loads(output.getvalue())
        self.assertEqual(result['signature'], 'put((uint256,string))')
        self.assertTrue(result['calldata'].startswith('0x'))

        output, error = io.StringIO(), io.StringIO()
        with patch('sys.argv', ['abi', 'decode-call', '--abi', str(EXAMPLE),
                                '--function', 'put((uint256,string))',
                                '--data', result['calldata']]), \
                contextlib.redirect_stdout(output), contextlib.redirect_stderr(error):
            status = abi.main()
        self.assertEqual((status, error.getvalue()), (0, ''))
        self.assertEqual(json.loads(output.getvalue())['arguments'][0]['value'], [7, 'hi'])

        expected = (abi.word(32) + abi.word(7) + abi.word(64) + abi.word(2)
                    + b'hi' + b'\0' * 30)
        output, error = io.StringIO(), io.StringIO()
        with patch('sys.argv', ['abi', 'decode', '--abi', str(EXAMPLE),
                                '--function', 'get', '--strict', '--data', '0x'+expected.hex()]), \
                contextlib.redirect_stdout(output), contextlib.redirect_stderr(error):
            status = abi.main()
        self.assertEqual((status, error.getvalue()), (0, ''))
        self.assertEqual(json.loads(output.getvalue())['outputs'][0]['value'], [7, 'hi'])

    def test_tuple_shape_validation_and_arrays_of_tuples_stay_explicitly_unsupported(self):
        with self.assertRaisesRegex(ValueError, 'components array'):
            abi.canonical({'type': 'tuple'})
        with self.assertRaisesRegex(ValueError, 'at least one component'):
            abi.canonical({'type': 'tuple', 'components': []})
        with self.assertRaisesRegex(ValueError, 'unsupported'):
            abi.canonical({'type': 'tuple[]', 'components': [{'type': 'uint8'}]})


if __name__ == '__main__':
    unittest.main()

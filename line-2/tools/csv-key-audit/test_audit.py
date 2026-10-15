"""Behavioral tests; temporary fixtures stay under test/scratch/."""
import contextlib
import io
import json
from pathlib import Path
import tempfile
import unittest

import audit as tool


class KeyAuditTests(unittest.TestCase):
    def setUp(self):
        scratch = Path('test/scratch')
        scratch.mkdir(parents=True, exist_ok=True)
        self.temp = tempfile.TemporaryDirectory(dir=scratch)
        self.addCleanup(self.temp.cleanup)
        self.directory = Path(self.temp.name)

    def csv(self, name, data):
        path = self.directory / name
        with path.open('w', encoding='utf-8', newline='') as stream:
            stream.write(data)
        return path

    def test_composite_key_resolves_single_column_duplicates(self):
        p = self.csv('a.csv', 'item,place\nlamp,north\nlamp,south\n')
        self.assertFalse(tool.audit([p], ['item'])['passes'])
        self.assertTrue(tool.audit([p], ['item', 'place'])['passes'])

    def test_duplicate_identical_rows_are_still_ambiguous(self):
        p = self.csv('a.csv', 'id,v\na,same\na,same\n')
        r = tool.audit([p], ['id'])['datasets'][0]
        self.assertEqual(r['duplicate_groups'], 1)
        self.assertEqual(r['duplicate_records'], 2)
        self.assertEqual(r['duplicate_examples'][0]['records'], [2, 3])
        self.assertEqual(r['eligible_keys'], 0)

    def test_empty_component_can_also_be_duplicate(self):
        p = self.csv('a.csv', 'id,part\n,x\n,x\na,\nb,c\n')
        r = tool.audit([p], ['id', 'part'])['datasets'][0]
        self.assertEqual(r['empty_key_records'], 3)
        self.assertEqual(r['empty_key_groups'], 2)
        self.assertEqual(r['duplicate_groups'], 1)
        self.assertEqual(r['eligible_keys'], 1)
        self.assertFalse(r['passes'])

    def test_multiline_bom_and_exact_string_semantics(self):
        p = self.csv('a.csv', '\ufeffid,part\n"a\nb",x\n01,x\n1,x\n" ",x\n')
        r = tool.audit([p], ['id', 'part'])['datasets'][0]
        self.assertTrue(r['passes'])
        self.assertEqual(r['eligible_keys'], 4)

    def test_composite_tuple_collision_is_not_concatenated(self):
        p = self.csv('a.csv', 'a,b\nab,c\na,bc\n')
        self.assertTrue(tool.audit([p], ['a', 'b'])['passes'])

    def test_overlap_excludes_ambiguous_and_empty_keys(self):
        a = self.csv('a.csv', 'id,v\na,x\nb,y\nd,z\nd,z\n,x\n')
        b = self.csv('b.csv', 'v,id\ny,b\nz,c\nz,d\nx,\n')
        r = tool.audit([a, b], ['id'])['datasets'][1]['overlap_with_first']
        self.assertEqual(r, {'shared_eligible_keys': 1, 'only_first': 1, 'only_this': 2})

    def test_empty_input_has_no_key_evidence(self):
        p = self.csv('a.csv', 'id,v\n')
        r = tool.audit([p], ['id'])
        self.assertFalse(r['passes'])
        self.assertEqual(r['datasets'][0]['issues'], ['no_data_records'])

    def test_sample_caps_preserve_totals_and_report_omissions(self):
        p = self.csv('a.csv', 'id\na\na\na\nb\nb\n')
        r = tool.audit([p], ['id'], examples=1)['datasets'][0]
        self.assertEqual(r['duplicate_groups'], 2)
        self.assertEqual(r['omitted_duplicate_groups'], 1)
        self.assertEqual(r['duplicate_examples'][0]['records'], [2])
        self.assertEqual(r['duplicate_examples'][0]['omitted_records'], 2)
        r = tool.audit([p], ['id'], examples=0)['datasets'][0]
        self.assertEqual(r['duplicate_examples'], [])
        self.assertEqual(r['omitted_duplicate_groups'], 2)

    def test_long_key_previews_do_not_masquerade_as_full_values(self):
        value = 'α' * 200
        p = self.csv('a.csv', 'id\n' + value + '\n' + value + '\n')
        sample = tool.audit([p], ['id'])['datasets'][0]['duplicate_examples'][0]['key_preview']['id']
        self.assertEqual(sample, {'text': 'α' * 160, 'characters': 200, 'truncated': True})

    def test_invalid_options_and_missing_columns(self):
        p = self.csv('a.csv', 'id\na\n')
        for keys in ([], ['id', 'id'], [''], ['missing']):
            with self.subTest(keys=keys), self.assertRaises(tool.InputError):
                tool.audit([p], keys)
        for paths, examples in (([], 5), ([p] * 9, 5), ([p], -1), ([p], 21)):
            with self.subTest(paths=paths, examples=examples), self.assertRaises(tool.InputError):
                tool.audit(paths, ['id'], examples)

    def test_invalid_later_file_has_no_partial_success_output(self):
        a = self.csv('a.csv', 'id,v\na,x\n')
        b = self.csv('b.csv', 'id,v\na\n')
        out, err = io.StringIO(), io.StringIO()
        with contextlib.redirect_stdout(out), contextlib.redirect_stderr(err):
            code = tool.main([str(a), str(b), '--key', 'id'])
        self.assertEqual(code, 2)
        self.assertEqual(out.getvalue(), '')
        self.assertIn('error', json.loads(err.getvalue()))

    def test_outside_workspace_rejected_before_open(self):
        with self.assertRaises(tool.InputError):
            tool.audit([Path.cwd().parent / 'never-open.csv'], ['id'])
        link = self.directory / 'outside.csv'
        link.symlink_to(Path.cwd().parent / 'never-open.csv')
        with self.assertRaises(tool.InputError):
            tool.audit([link], ['id'])

    def test_cli_exit_status_and_text_report(self):
        for csv, expected in (('id\na\n', 0), ('id\na\na\n', 1), ('id,v\na\n', 2)):
            p = self.csv('a.csv', csv)
            out, err = io.StringIO(), io.StringIO()
            with contextlib.redirect_stdout(out), contextlib.redirect_stderr(err):
                code = tool.main([str(p), '--key', 'id'])
            self.assertEqual(code, expected)
            json.loads(err.getvalue() if expected == 2 else out.getvalue())
        text = tool.render_text(tool.audit([self.csv('a.csv', 'id\na\na\n')], ['id']))
        self.assertIn('REVIEW', text)
        self.assertIn('duplicate_key', text)
        self.assertIn('"records": [2, 3]', text)
        self.assertIn('do not prove stable identity', text)


if __name__ == '__main__':
    unittest.main()

"""Delivered alignment regressions, adapted from Gathering 28, plus text review checks."""
import importlib.util
import json
from pathlib import Path
import subprocess
import sys
import tempfile
import unittest

SCRIPT = Path(__file__).resolve().with_name('align.py')
spec = importlib.util.spec_from_file_location('gathering_align', SCRIPT)
align = importlib.util.module_from_spec(spec)
spec.loader.exec_module(align)


class ColumnAlignTests(unittest.TestCase):
    def setUp(self):
        root = Path('test/scratch')
        root.mkdir(parents=True, exist_ok=True)
        self.temp = tempfile.TemporaryDirectory(dir=root)
        self.addCleanup(self.temp.cleanup)
        self.before = Path(self.temp.name) / 'before.csv'
        self.after = Path(self.temp.name) / 'after.csv'

    def compare(self, before, after, keys=('id',), maps=(('id', 'code'),)):
        self.before.write_bytes(before.encode())
        self.after.write_bytes(after.encode())
        return align.reconcile_aligned(self.before, self.after, list(keys), maps)

    def test_renamed_key_does_not_hide_exact_integer_change(self):
        r = self.compare('id,v\na,9007199254740992\n', 'code,v\na,9007199254740993\n')
        self.assertEqual(r['summary']['changed'], 1)
        self.assertEqual(r['changed'][0]['fields'][0]['after'], '9007199254740993')

    def test_composite_keys_are_tuples(self):
        r = self.compare('id,part,v\nab,c,1\na,bc,2\n', 'code,part,v\na,bc,2\nab,c,1\n',
                         keys=('id', 'part'))
        self.assertTrue(r['equal'])
        self.assertEqual(r['summary']['unchanged'], 2)

    def test_duplicate_keys_remain_ambiguous(self):
        r = self.compare('id,v\na,1\na,2\n', 'code,v\na,1\n')
        self.assertFalse(r['complete'])
        self.assertEqual(len(r['ambiguous'][0]['before']), 2)
        self.assertEqual(r['summary']['changed'], 0)

    def test_unmapped_schema_columns_remain_visible(self):
        r = self.compare('id,old\na,1\n', 'code,new\na,1\n')
        self.assertFalse(r['equal'])
        self.assertEqual(r['schema']['removed_before_columns'], ['old'])
        self.assertEqual(r['schema']['added_after_columns'], ['new'])

    def test_explicit_target_is_not_silently_reused(self):
        r = self.compare('id,code\na,old\n', 'code\na\n')
        self.assertEqual(r['schema']['removed_before_columns'], ['code'])

    def test_mapping_collisions_and_missing_targets_are_refused(self):
        for maps in [(('id', 'code'), ('v', 'code')), (('id', 'code'), ('id', 'v')),
                     (('id', 'missing'),), (('absent', 'code'),)]:
            with self.subTest(maps=maps), self.assertRaises(ValueError):
                self.compare('id,v\na,1\n', 'code,v\na,1\n', maps=maps)

    def test_malformed_rows_refused(self):
        for after in ['code,v\na\n', 'code,code\na,1\n', 'code,v\na,1,extra\n']:
            with self.subTest(after=after), self.assertRaises(ValueError):
                self.compare('id,v\na,1\n', after)

    def test_cli_mapping_and_error_exit_codes(self):
        self.compare('id,v\na,1\n', 'code,v\na,1\n')
        common = [sys.executable, '-B', str(SCRIPT), str(self.before), str(self.after), '--key', 'id']
        good = subprocess.run(common + ['--map', 'id', 'code'], capture_output=True, text=True)
        self.assertEqual(good.returncode, 0, good.stderr)
        self.assertTrue(json.loads(good.stdout)['equal'])
        bad = subprocess.run(common + ['--map', 'id', 'absent'], capture_output=True, text=True)
        self.assertEqual((bad.returncode, bad.stdout), (2, ''))
        self.assertIn('error', json.loads(bad.stderr))


    def test_text_review_covers_each_change_and_source_names(self):
        r = self.compare('id,old\na,1\nb,2\nc,3\n',
                         'code,new\na,4\nc,3\nd,5\n',
                         maps=(('id', 'code'), ('old', 'new')))
        text = align.render_text(r)
        self.assertIn('"old" -> "new": "1" -> "4"', text)
        self.assertIn('before record 3: {"id": "b", "old": "2"}', text)
        self.assertIn('after record 4: {"code": "d", "new": "5"}', text)
        self.assertIn('"unchanged": 1', text)
        self.assertIn('"id" -> "code"', text)

    def test_text_review_retains_all_duplicate_records(self):
        r = self.compare('id,v\na,1\na,2\n', 'code,v\na,3\na,4\n')
        text = align.render_text(r)
        self.assertIn('Complete: no', text)
        self.assertIn('Ambiguous keys (never paired)', text)
        for value in ('1', '2', '3', '4'):
            self.assertIn('"v": "' + value + '"', text)
        self.assertIn('"record": 3', text)

    def test_text_quotes_terminal_controls_multiline_and_unicode(self):
        r = self.compare('id,v\na,"first\nsecond\x1b[31mé"\n', 'code,v\na,last\n')
        text = align.render_text(r)
        self.assertNotIn('\x1b', text)
        self.assertIn(r'first\nsecond\u001b[31m\u00e9', text)
        self.assertTrue(text.isascii())

    def test_schema_only_change_does_not_claim_equality(self):
        r = self.compare('id,old\na,1\n', 'code,new\na,1\n')
        text = align.render_text(r)
        self.assertIn('alignment: different', text)
        self.assertIn('Unpaired before columns: ["old"]', text)
        self.assertIn('Unpaired after columns: ["new"]', text)
        self.assertIn('only to paired columns', text)

    def test_text_cli_has_same_status_and_no_partial_error_output(self):
        self.compare('id,v\na,1\n', 'code,v\na,2\n')
        command = [sys.executable, '-B', str(SCRIPT), str(self.before), str(self.after),
                   '--key', 'id', '--map', 'id', 'code', '--format', 'text']
        good = subprocess.run(command, capture_output=True, text=True)
        self.assertEqual(good.returncode, 1, good.stderr)
        self.assertIn('Changed rows:', good.stdout)
        self.after.write_bytes(b'code,v\na\n')
        bad = subprocess.run(command, capture_output=True, text=True)
        self.assertEqual((bad.returncode, bad.stdout), (2, ''))
        self.assertIn('error', json.loads(bad.stderr))


if __name__ == '__main__':
    unittest.main()

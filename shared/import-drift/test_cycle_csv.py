"""Cross-line regression tests; fixtures live only in workspace scratch."""
import contextlib
import csv
import hashlib
import io
import json
from pathlib import Path
import tempfile
import unittest
from unittest import mock

import cycle_csv as tool


class CycleCSVTests(unittest.TestCase):
    def setUp(self):
        scratch = Path('test/scratch')
        scratch.mkdir(parents=True, exist_ok=True)
        self.temp = tempfile.TemporaryDirectory(dir=scratch)
        self.addCleanup(self.temp.cleanup)
        self.root = Path(self.temp.name)
        self.put('a.py', 'import b\nimport b\nraise RuntimeError("do not execute")\n')
        self.put('b.py', 'import a\n')

    def put(self, name, text):
        path = self.root / name
        path.parent.mkdir(parents=True, exist_ok=True)
        path.write_text(text)
        return path

    def save(self, name, text):
        return self.put(name, text)

    def cli(self, *args):
        out, err = io.StringIO(), io.StringIO()
        with contextlib.redirect_stdout(out), contextlib.redirect_stderr(err):
            code = tool.main(list(args))
        return code, out.getvalue(), err.getvalue()

    def test_real_sites_duplicate_occurrences_and_digests(self):
        text, evidence = tool.snapshot(self.root)
        rows = list(csv.DictReader(io.StringIO(text)))
        self.assertEqual([(r['from'], r['to']) for r in rows], [('a', 'b'), ('b', 'a')])
        sites = json.loads(rows[0]['sites'])
        self.assertEqual([s['line'] for s in sites], [1, 2])
        self.assertEqual(sites[0]['source_sha256'], hashlib.sha256((self.root / 'a.py').read_bytes()).hexdigest())
        self.assertEqual(evidence['summary']['witness_count'], 1)
        self.assertEqual(self.cli('snapshot', str(self.root))[0], 1)

    def test_no_reread_or_source_execution(self):
        with mock.patch.object(Path, 'read_bytes', side_effect=AssertionError('second read')):
            with mock.patch.object(tool.import_map, 'source_files', side_effect=AssertionError('second walk')):
                text, _ = tool.snapshot(self.root)
        self.assertEqual(len(list(csv.DictReader(io.StringIO(text)))), 2)

    def test_removed_cycle_is_two_removed_rows(self):
        before = self.save('before.csv', tool.snapshot(self.root)[0])
        self.put('b.py', 'VALUE = 1\n')
        after = self.save('after.csv', tool.snapshot(self.root)[0])
        result = tool.compare(before, after)
        self.assertEqual(result['summary']['removed'], 2)
        self.assertTrue(result['complete'])
        self.assertEqual(self.cli('compare', str(before), str(after))[0], 1)

    def test_line_only_change_is_visible_without_key_churn(self):
        before = self.save('before.csv', tool.snapshot(self.root)[0])
        self.put('a.py', '\nimport b\nimport b\nraise RuntimeError("do not execute")\n')
        after = self.save('after.csv', tool.snapshot(self.root)[0])
        result = tool.compare(before, after)
        self.assertEqual(result['summary']['changed'], 1)
        self.assertEqual(result['summary']['added'], 0)
        self.assertEqual(result['changed'][0]['key'], {'anchor': 'a', 'from': 'a', 'to': 'b'})

    def test_empty_witness_sets_are_valid_equal_inputs(self):
        self.put('b.py', '')
        a = self.save('a.csv', tool.snapshot(self.root)[0])
        self.assertTrue(tool.compare(a, a)['equal'])
        self.assertEqual(self.cli('snapshot', str(self.root))[0], 0)

    def test_budget_refusal_emits_no_csv(self):
        code, out, err = self.cli('snapshot', str(self.root), '--max-files', '1')
        self.assertEqual((code, out), (2, ''))
        self.assertEqual(json.loads(err)['error']['budget'], 'files')
        self.assertNotIn('inventory', json.loads(err))

    def test_module_collision_refuses_export(self):
        self.put('a/__init__.py', 'import b\n')
        code, out, err = self.cli('snapshot', str(self.root))
        self.assertEqual((code, out), (2, ''))
        self.assertIn('collision', json.loads(err)['error']['detail'])

    def test_parse_and_dynamic_warnings_retained(self):
        self.put('bad.py', 'def bad(\n')
        self.put('dynamic.py', '__import__("a")\n')
        code, _, err = self.cli('snapshot', str(self.root))
        evidence = json.loads(err)
        self.assertEqual(code, 1)
        self.assertTrue(evidence['issues'])
        self.assertTrue(evidence['dynamic_imports'])

    def test_self_loop_and_determinism(self):
        self.put('a.py', 'import a\n')
        self.put('b.py', '')
        first, evidence = tool.snapshot(self.root)
        self.assertEqual(first, tool.snapshot(self.root)[0])
        self.assertEqual(evidence['witnesses'][0]['import_path'], ['a', 'a'])
        self.assertEqual(len(list(csv.DictReader(io.StringIO(first)))), 1)

    def test_bad_csv_schema_duplicate_and_empty_keys_refused(self):
        valid = self.save('valid.csv', tool.snapshot(self.root)[0])
        for name, text in [('bad.csv', 'wrong\nvalue\n'),
                           ('dup.csv', valid.read_text() + valid.read_text().splitlines()[1] + '\n'),
                           ('empty.csv', ',a,b,[],[]\n')]:
            candidate = self.save(name, text if name != 'empty.csv' else ','.join(tool.COLUMNS)+'\n'+text)
            code, out, _ = self.cli('compare', str(valid), str(candidate))
            self.assertEqual((code, out), (2, ''))

    def test_html_is_inert_and_all_rows_shown(self):
        a = self.save('a.csv', tool.snapshot(self.root)[0])
        self.put('b.py', '# </pre><script>bad</script>\nimport a\n')
        b = self.save('b.csv', tool.snapshot(self.root)[0])
        code, html, _ = self.cli('compare', str(a), str(b), '--format', 'html')
        self.assertEqual(code, 1)
        self.assertIn('<!doctype html>', html)
        self.assertNotIn('<script>', html)
        self.assertIn('Changed fields', html)

    def test_outside_source_refused(self):
        code, out, _ = self.cli('snapshot', str(Path.cwd().parent))
        self.assertEqual((code, out), (2, ''))


if __name__ == '__main__':
    unittest.main()

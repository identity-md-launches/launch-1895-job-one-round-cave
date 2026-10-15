"""Regression checks; fixtures stay beside this file and are removed afterwards."""
import contextlib
import io
import json
from pathlib import Path
import random
import tempfile
import unittest
from unittest import mock

import import_map


class MapperTests(unittest.TestCase):
    def setUp(self):
        self.temporary = tempfile.TemporaryDirectory(dir=Path(__file__).parent)
        self.addCleanup(self.temporary.cleanup)
        self.root = Path(self.temporary.name)

    def put(self, path, source):
        target = self.root / path
        target.parent.mkdir(parents=True, exist_ok=True)
        target.write_text(source, encoding='utf-8')

    def test_package_collision_reports_both_paths_and_package_precedence(self):
        self.put('pkg.py', 'import shadow_only\nraise RuntimeError("must not execute")\n')
        self.put('pkg/__init__.py', 'from . import engine\n')
        self.put('pkg/engine.py', 'raise RuntimeError("must not execute")\n')
        self.put('main.py', 'import pkg\n')
        report = import_map.inspect(self.root)
        collision, = report['issues']
        self.assertEqual(collision['type'], 'module_collision')
        self.assertEqual(collision['paths'], ['pkg.py', 'pkg/__init__.py'])
        self.assertEqual(collision['selected'], 'pkg/__init__.py')
        self.assertEqual(next(m['path'] for m in report['modules'] if m['module'] == 'pkg'),
                         'pkg/__init__.py')
        self.assertEqual(report['edges'], [{'from': 'main', 'to': 'pkg'},
                                           {'from': 'pkg', 'to': 'pkg.engine'}])
        self.assertIn('shadowed source not analyzed: pkg.py', import_map.format_text(report))
        with contextlib.redirect_stdout(io.StringIO()):
            self.assertEqual(import_map.main([str(self.root), '--strict', '--json']), 1)
        self.assertEqual(report, import_map.inspect(self.root))

    def test_nested_collision(self):
        self.put('outer/item.py', '')
        self.put('outer/item/__init__.py', '')
        report = import_map.inspect(self.root)
        self.assertEqual(report['issues'][0]['module'], 'outer.item')
        self.assertEqual(report['issues'][0]['selected'], 'outer/item/__init__.py')

    def test_original_example_and_no_execution(self):
        report = import_map.inspect(Path(__file__).parent / 'examples')
        self.assertEqual(report['summary'], {'module_count': 4, 'local_edge_count': 3,
                         'cycle_count': 1, 'issue_count': 1, 'entrypoints': ['main']})
        self.assertEqual(report['cycles'], [['pkg.engine', 'pkg.helper']])
        self.put('trap.py', 'raise RuntimeError("source executed")\nif __name__ == "__main__": pass\n')
        self.assertEqual(import_map.inspect(self.root)['summary']['entrypoints'], ['trap'])

    def test_deep_graph(self):
        nodes = [f'n{i:05}' for i in range(5000)]
        graph = {node: {nodes[i + 1]} if i + 1 < len(nodes) else set()
                 for i, node in enumerate(nodes)}
        self.assertEqual(import_map.cycles(graph), [])
        graph[nodes[-1]].add(nodes[0])
        self.assertEqual(import_map.cycles(graph), [nodes])

    def test_cycles_against_independent_reachability(self):
        rng = random.Random(22)
        for _ in range(100):
            nodes = list('abcdefgh')
            graph = {n: {m for m in nodes if rng.random() < .18} for n in nodes}
            reach = {}
            for node in nodes:
                seen, pending = set(), list(graph[node])
                while pending:
                    target = pending.pop()
                    if target not in seen:
                        seen.add(target)
                        pending.extend(graph[target])
                reach[node] = seen
            expected = set()
            for n in nodes:
                group = tuple(m for m in nodes if m in reach[n] and n in reach[m])
                if len(group) > 1 or n in graph[n]:
                    expected.add(group)
            self.assertEqual(import_map.cycles(graph), sorted(map(list, expected)))

    def test_parse_error_and_self_cycle(self):
        self.put('broken.py', 'def nope(\n')
        self.put('loop.py', 'import loop\n')
        report = import_map.inspect(self.root)
        self.assertEqual(report['cycles'], [['loop']])
        self.assertEqual(report['issues'][0]['type'], 'parse_error')

    def test_python_source_encodings_preserve_imports_and_line_numbers(self):
        # compile() is an independent acceptance check; its result is never run.
        cases = {
            'utf8_bom': (b'\xef\xbb\xbfimport helper\n', 1),
            'utf8_bom_cookie': (b'\xef\xbb\xbf# coding: utf-8\nimport helper\n', 2),
            'latin1': (b'# coding: latin-1\nlabel = "caf\xe9"\nimport helper\n', 3),
            'second_line': (b'#!/usr/bin/python3\n# coding: cp1252\nlabel = "\x80"\nimport helper\n', 4),
            'crlf': (b'# coding: latin-1\r\nlabel = "caf\xe9"\r\nimport helper\r\n', 3),
            'default_utf8': ('label = "caf\u00e9"\nimport helper\n'.encode('utf-8'), 2),
        }
        self.put('helper.py', 'raise RuntimeError("source must not execute")\n')
        for name, (source, line) in cases.items():
            with self.subTest(name=name):
                compile(source, name + '.py', 'exec')
                (self.root / (name + '.py')).write_bytes(source)
        report = import_map.inspect(self.root)
        self.assertEqual(report['issues'], [])
        self.assertEqual(report['summary']['local_edge_count'], len(cases))
        for module in report['modules']:
            if module['module'] in cases:
                with self.subTest(name=module['module']):
                    self.assertEqual(module['imports'], [
                        {'line': cases[module['module']][1], 'target': 'helper',
                         'kind': 'local', 'resolved': 'helper'}])

    def test_bom_entrypoint_relative_import_cycle_and_strict_json(self):
        self.put('pkg/__init__.py', '')
        (self.root / 'pkg/first.py').write_bytes(
            b'\xef\xbb\xbffrom . import second\nif __name__ == "__main__":\n'
            b'    raise RuntimeError("source must not execute")\n')
        (self.root / 'pkg/second.py').write_bytes(
            b'# coding: latin-1\nlabel = "caf\xe9"\nfrom . import first\n')
        output = io.StringIO()
        with contextlib.redirect_stdout(output):
            status = import_map.main([str(self.root), '--json', '--strict'])
        report = json.loads(output.getvalue())
        self.assertEqual(status, 1)  # The cycle is still an issue in strict mode.
        self.assertEqual(report['issues'], [])
        self.assertEqual(report['cycles'], [['pkg.first', 'pkg.second']])
        self.assertEqual(report['summary']['entrypoints'], ['pkg.first'])

    def test_bad_source_encodings_report_errors_and_continue(self):
        cases = {
            'unknown_codec': b'# coding: nonexistent_codec\nimport helper\n',
            'bom_conflict': b'\xef\xbb\xbf# coding: latin-1\nimport helper\n',
            'invalid_utf8': b'label = "\xff"\nimport helper\n',
            'invalid_declared_ascii': b'# coding: ascii\nlabel = "\xff"\n',
            'late_cookie': b'label = 1\n# coding: latin-1\nlabel = "\xe9"\n',
            'null_byte': b'import helper\n\x00',
        }
        self.put('helper.py', '')
        self.put('healthy.py', 'import helper\n')
        for name, source in cases.items():
            with self.subTest(name=name):
                with self.assertRaises((SyntaxError, ValueError) if name == 'null_byte' else SyntaxError):
                    compile(source, name + '.py', 'exec')
                (self.root / (name + '.py')).write_bytes(source)
        report = import_map.inspect(self.root)
        self.assertEqual(report['summary']['issue_count'], len(cases))
        self.assertEqual({i['path'] for i in report['issues']},
                         {name + '.py' for name in cases})
        self.assertTrue(all(i['type'] == 'parse_error' for i in report['issues']))
        self.assertEqual(report['edges'], [{'from': 'healthy', 'to': 'helper'}])
        with contextlib.redirect_stdout(io.StringIO()):
            self.assertEqual(import_map.main([str(self.root), '--strict']), 1)

    def test_bom_clean_scan_cli_succeeds(self):
        (self.root / 'bom.py').write_bytes(b'\xef\xbb\xbfimport json\n')
        output = io.StringIO()
        with contextlib.redirect_stdout(output):
            status = import_map.main([str(self.root), '--json', '--strict'])
        report = json.loads(output.getvalue())
        self.assertEqual(status, 0)
        self.assertEqual(report['issues'], [])
        self.assertEqual(report['modules'][0]['imports'],
                         [{'line': 1, 'target': 'json', 'kind': 'external'}])

    def test_python39_null_byte_valueerror_retains_healthy_edges(self):
        real_parse = import_map.ast.parse
        def legacy_parse(source, **kwargs):
            if b'\x00' in source:
                raise ValueError('source code string cannot contain null bytes')
            return real_parse(source, **kwargs)
        sources = {'bad.py': b'\x00', 'good.py': b'import helper\n', 'helper.py': b''}
        with mock.patch.object(import_map.ast, 'parse', side_effect=legacy_parse):
            report = import_map.inspect(self.root, source_bytes=sources)
        self.assertEqual(report['edges'], [{'from': 'good', 'to': 'helper'}])
        self.assertEqual(len(report['issues']), 1)
        self.assertEqual(report['issues'][0]['type'], 'parse_error')
        self.assertEqual(report['issues'][0]['path'], 'bad.py')

    def test_unrelated_parser_valueerror_is_not_hidden(self):
        with mock.patch.object(import_map.ast, 'parse', side_effect=ValueError('unexpected')):
            with self.assertRaisesRegex(ValueError, 'unexpected'):
                import_map.inspect(self.root, source_bytes={'good.py': b'import json\n'})


if __name__ == '__main__':
    unittest.main()

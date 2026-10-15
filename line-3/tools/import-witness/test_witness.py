"""Behavioral tests using workspace fixtures and in-memory source; standard library only."""
import contextlib
import importlib.util
import io
import json
from pathlib import Path
import random
import tempfile
import unittest

SPEC = importlib.util.spec_from_file_location('witness', Path(__file__).with_name('witness.py'))
W = importlib.util.module_from_spec(SPEC)
SPEC.loader.exec_module(W)
M = W.load_budget().load_mapper()


def mapped(sources):
    return M.inspect(Path('.'), source_bytes={p: s.encode() for p, s in sources.items()})


def graph_report(graph):
    return mapped({name + '.py': ''.join('import ' + n + '\n' for n in sorted(targets))
                   for name, targets in graph.items()})


class WitnessTests(unittest.TestCase):
    def test_directed_cycle_is_not_alphabetical_component_order(self):
        report = mapped({'a.py': 'import c\n', 'b.py': 'import a\n', 'c.py': 'import b\n'})
        result = W.explain(report)
        witness, = result['witnesses']
        self.assertEqual(witness['component'], ['a', 'b', 'c'])
        self.assertEqual(witness['import_path'], ['a', 'c', 'b', 'a'])
        self.assertEqual(witness['edges'][0]['sites'], [{'path': 'a.py', 'line': 1, 'target': 'c'}])

    def test_shortest_anchor_cycle_and_ties(self):
        graph = {'a': {'b', 'c', 'd'}, 'b': {'e'}, 'c': {'a'}, 'd': {'a'}, 'e': {'a'}}
        result = W.explain(graph_report(graph))
        self.assertEqual(result['witnesses'][0]['import_path'], ['a', 'c', 'a'])
        self.assertEqual(result, W.explain(graph_report(dict(reversed(list(graph.items()))))))

    def test_self_loop_disconnected_cycles_and_acyclic(self):
        graph = {'a': {'a', 'b'}, 'b': {'a'}, 'c': {'d'}, 'd': {'c'}, 'e': set()}
        witnesses = W.explain(graph_report(graph))['witnesses']
        self.assertEqual([w['import_path'] for w in witnesses], [['a', 'a'], ['c', 'd', 'c']])
        self.assertEqual(W.explain(graph_report({'a': {'b'}, 'b': set()}))['witnesses'], [])
        self.assertEqual(W.explain(mapped({}))['witnesses'], [])

    def test_relative_alias_and_duplicate_sites(self):
        report = mapped({'pkg/__init__.py': '', 'pkg/a.py': '# hi\nfrom . import b as bee\nfrom . import b\n',
                         'pkg/b.py': 'from .a import thing\n'})
        witness, = W.explain(report)['witnesses']
        self.assertEqual(witness['import_path'], ['pkg.a', 'pkg.b', 'pkg.a'])
        self.assertEqual([s['line'] for s in witness['edges'][0]['sites']], [2, 3])
        self.assertEqual(witness['edges'][1]['sites'][0]['target'], '.a import thing')

    def test_warnings_survive_without_cycles(self):
        report = mapped({'bad.py': '\x00', 'good.py': '__import__("plugin")\n'})
        result = W.explain(report)
        self.assertEqual(result['issues'], report['issues'])
        self.assertEqual(result['dynamic_imports'], [{'module': 'good', 'path': 'good.py', 'line': 1}])
        self.assertEqual(result['witnesses'], [])

    def test_long_cycle_is_iterative(self):
        names = [f'n{i:04}' for i in range(1600)]
        graph = {n: {names[(i+1) % len(names)]} for i, n in enumerate(names)}
        self.assertEqual(W.explain(graph_report(graph))['witnesses'][0]['import_path'], names + names[:1])

    def test_random_graphs_against_independent_forward_bfs(self):
        rng = random.Random(29)
        for _ in range(100):
            graph = {n: {m for m in 'abcdefg' if rng.random() < .22} for n in 'abcdefg'}
            report = graph_report(graph)
            result = W.explain(report)
            self.assertEqual(len(result['witnesses']), len(report['cycles']))
            for witness in result['witnesses']:
                path = witness['import_path']
                self.assertEqual(path[0], path[-1])
                self.assertEqual(len(set(path[:-1])), len(path)-1)
                for a, b in zip(path, path[1:]):
                    self.assertIn(b, graph[a])
                anchor = path[0]
                pending, seen, shortest = [(anchor, 0)], {anchor}, None
                for node, distance in pending:
                    if anchor in graph[node]:
                        shortest = distance + 1
                        break
                    for target in graph[node] - seen:
                        seen.add(target)
                        pending.append((target, distance + 1))
                self.assertEqual(len(path)-1, shortest)

    def test_cli_success_strict_refusal_and_no_execution(self):
        scratch = Path('test/scratch'); scratch.mkdir(parents=True, exist_ok=True)
        with tempfile.TemporaryDirectory(dir=scratch) as name:
            root = Path(name)
            marker = root / 'executed'
            (root / 'a.py').write_text('import b\n' + f'open({str(marker)!r}, "w").write("ran")\n')
            (root / 'b.py').write_text('import a\n')
            def cli(*args):
                out = io.StringIO()
                with contextlib.redirect_stdout(out):
                    code = W.main([str(root), '--json', *args])
                return code, json.loads(out.getvalue())
            code, result = cli()
            self.assertEqual(code, 0)
            self.assertEqual(result['inventory']['files'], 2)
            self.assertEqual(result['status'], 'complete')
            self.assertEqual(cli('--strict')[0], 1)
            code, refused = cli('--max-files', '1')
            self.assertEqual(code, 2)
            self.assertEqual(refused['status'], 'refused')
            self.assertNotIn('witnesses', refused)
            self.assertFalse(marker.exists())
            (root / 'a.py').write_text('')
            (root / 'b.py').write_text('')
            self.assertEqual(cli('--strict')[0], 0)

    def test_missing_evidence_is_refused(self):
        report = graph_report({'a': {'a'}})
        report['modules'][0]['imports'] = []
        with self.assertRaisesRegex(ValueError, 'missing source evidence'):
            W.explain(report)


if __name__ == '__main__':
    unittest.main()

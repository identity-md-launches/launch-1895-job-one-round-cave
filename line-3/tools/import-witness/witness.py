#!/usr/bin/env python3
"""Find one source-linked closed import walk per cyclic component, without execution."""
import argparse
from collections import deque
import importlib.util
import json
from pathlib import Path
import sys

SCOPE = ('One shortest cycle through the alphabetically first module of each cyclic '
         'component; not all cycles or a minimum set of edits. Static explicit local '
         'imports only. Conditional imports may never run; missing edges do not prove '
         'runtime isolation. Warnings and source hashes describe the admitted snapshot.')


def load_budget():
    path = Path(__file__).resolve().parents[1] / 'import-budget' / 'budget.py'
    spec = importlib.util.spec_from_file_location('line3_witness_budget', path)
    module = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(module)
    return module


def explain(report):
    """Iterative reverse BFS; deterministic shortest return path to each anchor."""
    records = {item['module']: item for item in report['modules']}
    graph = {name: set() for name in records}
    reverse = {name: set() for name in records}
    evidence = {}
    for edge in report['edges']:
        source, target = edge['from'], edge['to']
        graph[source].add(target)
        reverse[target].add(source)
    for name, record in records.items():
        for item in record['imports']:
            target = item.get('resolved')
            if target in graph[name]:
                evidence.setdefault((name, target), []).append({
                    'path': record['path'], 'line': item['line'], 'target': item['target']})
    witnesses = []
    for group in sorted(sorted(group) for group in report['cycles']):
        members = set(group)
        anchor = group[0]
        distance, toward = {anchor: 0}, {}
        queue = deque([anchor])
        while queue:
            node = queue.popleft()
            for parent in sorted(reverse[node] & members):
                if parent not in distance:
                    distance[parent] = distance[node] + 1
                    toward[parent] = node
                    queue.append(parent)
        first = min(graph[anchor] & members, key=lambda n: (distance[n], n))
        path = [anchor, first]
        while path[-1] != anchor:
            path.append(toward[path[-1]])
        edges = []
        for source, target in zip(path, path[1:]):
            sites = evidence.get((source, target), [])
            if not sites:
                raise ValueError('missing source evidence for ' + source + ' -> ' + target)
            edges.append({'from': source, 'to': target, 'sites': sorted(
                sites, key=lambda s: (s['path'], s['line'], s['target']))})
        witnesses.append({'component': group, 'anchor': anchor,
                          'import_path': path, 'edges': edges})
    return {'witnesses': witnesses, 'issues': report['issues'],
            'dynamic_imports': [{'module': m['module'], 'path': m['path'], 'line': line}
                                for m in report['modules'] for line in m['dynamic_import_lines']],
            'summary': dict(report['summary'], witness_count=len(witnesses)), 'scope': SCOPE}


def main(argv=None):
    budget = load_budget()
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument('root', type=Path, help='explicit import root inside the current workspace')
    parser.add_argument('--json', action='store_true')
    parser.add_argument('--strict', action='store_true', help='exit 1 for cycles, issues or dynamic imports')
    for name, value in budget.DEFAULTS.items():
        parser.add_argument('--max-' + name.replace('_', '-'), type=int, default=value, dest=name)
    args = parser.parse_args(argv)
    try:
        scan = budget.scan(args.root, {name: getattr(args, name) for name in budget.DEFAULTS})
        result = dict(explain(scan['map']), status='complete', limits=scan['limits'],
                      inventory=scan['inventory'], collection_scope=scan['scope'])
    except (OSError, ValueError, RuntimeError, RecursionError) as exc:
        error = exc.evidence if isinstance(exc, budget.BudgetExceeded) else {
            'type': 'scan_error', 'detail': str(exc)}
        if args.json:
            print(json.dumps({'status': 'refused', 'error': error}, indent=2))
        else:
            print('import-witness: ' + str(exc), file=sys.stderr)
        return 2
    if args.json:
        print(json.dumps(result, indent=2, ensure_ascii=False))
    else:
        print(f"Cyclic components: {len(result['witnesses'])}")
        for witness in result['witnesses']:
            print('Component: ' + ', '.join(witness['component']))
            print('Witness: ' + ' -> '.join(witness['import_path']))
            for edge in witness['edges']:
                for site in edge['sites']:
                    print(f"  {site['path']}:{site['line']}: {site['target']} ({edge['from']} -> {edge['to']})")
        print(f"Scan warnings: {len(result['issues'])} issues, {len(result['dynamic_imports'])} dynamic calls")
        print(SCOPE)
    return int(args.strict and bool(result['witnesses'] or result['issues'] or result['dynamic_imports']))


if __name__ == '__main__':
    sys.exit(main())

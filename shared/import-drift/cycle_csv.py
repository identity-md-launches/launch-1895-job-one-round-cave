#!/usr/bin/env python3
"""Review source-linked cycle witnesses with exact keyed CSV, entirely offline."""
import argparse
import csv
import io
import json
import sys

import budget
import import_map
import reconcile
import review
import witness

KEYS = ('anchor', 'from', 'to')
COLUMNS = (*KEYS, 'component', 'sites')


def compact(value):
    return json.dumps(value, ensure_ascii=True, sort_keys=True, separators=(',', ':'))


def snapshot(root, limits=None):
    scan = budget.scan(root, limits, mapper=import_map)
    report = scan['map']
    if any(issue['type'] == 'module_collision' for issue in report['issues']):
        raise ValueError('module collision prevents unambiguous cycle review')
    explanation = witness.explain(report)
    digests = {item['path']: item['sha256'] for item in scan['inventory']['manifest']}
    stream = io.StringIO(newline='')
    writer = csv.DictWriter(stream, fieldnames=COLUMNS, lineterminator='\n')
    writer.writeheader()
    for cycle in explanation['witnesses']:
        for edge in cycle['edges']:
            sites = [dict(site, source_sha256=digests[site['path']]) for site in edge['sites']]
            writer.writerow({'anchor': cycle['anchor'], 'from': edge['from'], 'to': edge['to'],
                             'component': compact(cycle['component']), 'sites': compact(sites)})
    evidence = dict(explanation, schema='cycle-csv/v1', status='complete',
                    inventory=scan['inventory'], limits=scan['limits'],
                    collection_scope=scan['scope'])
    return stream.getvalue(), evidence


def compare(before, after):
    for path in (before, after):
        header, groups, _ = reconcile.load_table(path, KEYS)
        if header != list(COLUMNS):
            raise ValueError('comparison requires cycle-csv/v1 columns in order')
        if any(any(not part for part in key) or len(rows) != 1 for key, rows in groups.items()):
            raise ValueError('cycle keys must be unique and nonempty')
    # A header-only export is a valid empty witness set, not missing input.
    return reconcile.reconcile(before, after, KEYS)


def main(argv=None):
    parser = argparse.ArgumentParser(description=__doc__, allow_abbrev=False)
    commands = parser.add_subparsers(dest='command', required=True)
    snap = commands.add_parser('snapshot', help='CSV stdout; complete evidence JSON stderr')
    snap.add_argument('root', help='explicit source directory inside the current workspace')
    for name, default in budget.DEFAULTS.items():
        snap.add_argument('--max-' + name.replace('_', '-'), type=int, default=default, dest=name)
    diff = commands.add_parser('compare', help='compare saved CSV witnesses; no source execution')
    diff.add_argument('before')
    diff.add_argument('after')
    diff.add_argument('--format', choices=('json', 'text', 'html'), default='json')
    args = parser.parse_args(argv)
    try:
        if args.command == 'snapshot':
            output, evidence = snapshot(args.root, {name: getattr(args, name) for name in budget.DEFAULTS})
            code = int(bool(evidence['witnesses'] or evidence['issues'] or evidence['dynamic_imports']))
            print(compact(evidence), file=sys.stderr)
        else:
            result = compare(args.before, args.after)
            if args.format == 'html':
                output = '\n'.join(review.iter_html(result)) + '\n'
            elif args.format == 'text':
                output = reconcile.render_text(result) + '\n'
            else:
                output = json.dumps(result, indent=2, ensure_ascii=True) + '\n'
            code = 0 if result['equal'] else 1
    except (OSError, ValueError, RuntimeError, RecursionError) as error:
        detail = error.evidence if isinstance(error, budget.BudgetExceeded) else {'type': 'review_error', 'detail': str(error)}
        print(compact({'schema': 'cycle-csv/v1', 'status': 'refused', 'error': detail}), file=sys.stderr)
        return 2
    sys.stdout.write(output)
    return code


if __name__ == '__main__':
    raise SystemExit(main())

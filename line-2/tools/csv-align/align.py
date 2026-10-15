#!/usr/bin/env python3
"""Reconcile keyed CSV exports with explicitly paired column names. Offline."""

import argparse
import json
from pathlib import Path
import sys

# Keep the same bounded, exact-string CSV reader as the original reconciler.
sys.path.insert(0, str(Path(__file__).resolve().parents[1] / 'csv-reconcile'))
from reconcile import InputError, load_table  # noqa: E402


def reconcile_aligned(before, after, keys, maps=()):
    """Compare two CSVs; all names in keys and map sources refer to `before`."""
    if not keys or any(not k for k in keys) or len(set(keys)) != len(keys):
        raise InputError('provide distinct, nonempty before-side key columns')
    explicit = {}
    targets = set()
    for source, target in maps:
        if not source or not target:
            raise InputError('mapped column names must be nonempty')
        if source in explicit or target in targets:
            raise InputError('each mapped source and target may occur only once')
        explicit[source] = target
        targets.add(target)

    before_header, before_groups, before_count = load_table(before, keys)
    absent_sources = sorted(set(explicit) - set(before_header))
    if absent_sources:
        raise InputError(f'mapped before columns do not exist: {absent_sources}')

    after_keys = [explicit.get(key, key) for key in keys]
    if len(set(after_keys)) != len(after_keys):
        raise InputError('key mappings collide on an after column')
    after_header, after_groups, after_count = load_table(after, after_keys)
    absent_targets = sorted(targets - set(after_header))
    if absent_targets:
        raise InputError(f'mapped after columns do not exist: {absent_targets}')

    # Explicit pairs take precedence. A target consumed by an explicit pair
    # cannot also be silently paired to a same-named before column.
    paired = []
    after_names = set(after_header)
    used_after = set(explicit.values())
    for source in before_header:
        if source in explicit:
            target = explicit[source]
            paired.append((source, target, True))
        elif source in after_names and source not in used_after:
            paired.append((source, source, False))
            used_after.add(source)
    pair_lookup = {source: target for source, target, _ in paired}
    if any(key not in pair_lookup or pair_lookup[key] != target
           for key, target in zip(keys, after_keys)):
        raise InputError('every key needs a distinct before/after column pair')

    removed_columns = [name for name in before_header if name not in pair_lookup]
    added_columns = [name for name in after_header if name not in used_after]
    compared = [(source, target) for source, target, _ in paired if source not in keys]
    added, removed, changed, ambiguous = [], [], [], []
    unchanged = 0
    for key in sorted(before_groups.keys() | after_groups.keys()):
        old = before_groups.get(key, [])
        new = after_groups.get(key, [])
        key_record = dict(zip(keys, key))
        if len(old) > 1 or len(new) > 1:
            ambiguous.append({'key': key_record, 'before': old, 'after': new})
        elif not old:
            added.append({'key': key_record, 'after_record': new[0]['record'],
                          'after_values': new[0]['values']})
        elif not new:
            removed.append({'key': key_record, 'before_record': old[0]['record'],
                            'before_values': old[0]['values']})
        else:
            fields = [
                {'before_column': source, 'after_column': target,
                 'before': old[0]['values'][source], 'after': new[0]['values'][target]}
                for source, target in compared
                if old[0]['values'][source] != new[0]['values'][target]
            ]
            if fields:
                changed.append({'key': key_record, 'before_record': old[0]['record'],
                                'after_record': new[0]['record'], 'fields': fields})
            else:
                unchanged += 1

    different = bool(added or removed or changed or ambiguous or
                     removed_columns or added_columns)
    return {
        'format': 'csv-align/v1', 'equal': not different, 'complete': not ambiguous,
        'keys': [{'before': key, 'after': pair_lookup[key]} for key in keys],
        'schema': {
            'paired_columns': [{'before': source, 'after': target, 'explicit': is_explicit}
                               for source, target, is_explicit in paired],
            'removed_before_columns': removed_columns,
            'added_after_columns': added_columns,
        },
        'summary': {'before_records': before_count, 'after_records': after_count,
                    'added': len(added), 'removed': len(removed),
                    'changed': len(changed), 'unchanged': unchanged,
                    'ambiguous_keys': len(ambiguous)},
        'added': added, 'removed': removed, 'changed': changed, 'ambiguous': ambiguous,
    }


def render_text(result):
    """Plain terminal text; JSON-quote every CSV-derived value and control."""
    def literal(value):
        return json.dumps(value, ensure_ascii=True)

    summary = result['summary']
    lines = ['CSV column alignment: ' + ('equal' if result['equal'] else 'different'),
             'Complete: ' + ('yes' if result['complete'] else 'no; duplicate keys remain unresolved'),
             'Row counts: ' + literal(summary),
             'Unchanged counts apply only to paired columns; inspect schema leftovers.',
             '', 'Key pairs (before -> after):']
    for pair in result['keys']:
        lines.append('  ' + literal(pair['before']) + ' -> ' + literal(pair['after']))
    lines.extend(['', 'Column pairs (before -> after):'])
    for pair in result['schema']['paired_columns']:
        mode = 'explicit' if pair['explicit'] else 'same name'
        lines.append('  ' + literal(pair['before']) + ' -> ' + literal(pair['after']) + ' (' + mode + ')')
    lines.extend([
        'Unpaired before columns: ' + literal(result['schema']['removed_before_columns']),
        'Unpaired after columns: ' + literal(result['schema']['added_after_columns']),
    ])
    for title, name in [('Added rows', 'added'), ('Removed rows', 'removed'),
                        ('Changed rows', 'changed'), ('Ambiguous keys (never paired)', 'ambiguous')]:
        lines.extend(['', title + ':'])
        if not result[name]:
            lines.append('  None.')
        for row in result[name]:
            lines.append('  Key ' + literal(row['key']))
            if name in ('added', 'removed'):
                side = 'after' if name == 'added' else 'before'
                lines.append('    ' + side + ' record ' + str(row[side + '_record']) + ': ' +
                             literal(row[side + '_values']))
            elif name == 'changed':
                lines.append('    Records: before ' + str(row['before_record']) +
                             ', after ' + str(row['after_record']))
                for field in row['fields']:
                    lines.append('    ' + literal(field['before_column']) + ' -> ' +
                                 literal(field['after_column']) + ': ' + literal(field['before']) +
                                 ' -> ' + literal(field['after']))
            else:
                lines.append('    Before: ' + literal(row['before']))
                lines.append('    After: ' + literal(row['after']))
    return '\n'.join(lines)


def main(argv=None):
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument('before', help='baseline CSV inside the current directory')
    parser.add_argument('after', help='candidate CSV inside the current directory')
    parser.add_argument('--key', action='append', required=True,
                        help='before-side key column; repeat for composite keys')
    parser.add_argument('--map', nargs=2, action='append', default=[],
                        metavar=('BEFORE', 'AFTER'),
                        help='explicitly pair differently named columns; repeat as needed')
    parser.add_argument('--format', choices=('json', 'text'), default='json',
                        help='JSON or a full, plain-text review with JSON-quoted values')
    args = parser.parse_args(argv)
    try:
        result = reconcile_aligned(args.before, args.after, args.key, args.map)
    except (InputError, OSError, ValueError, TypeError) as exc:
        print(json.dumps({'error': str(exc)}, ensure_ascii=False), file=sys.stderr)
        return 2
    print(render_text(result) if args.format == 'text' else
          json.dumps(result, ensure_ascii=False, indent=2))
    return 0 if result['equal'] else 1


if __name__ == '__main__':
    sys.exit(main())

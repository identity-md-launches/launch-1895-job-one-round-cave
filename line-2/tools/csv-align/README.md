# CSV Column Align

This Python 3.10+ standard-library tool reconciles two workspace-local CSV
exports by stable keys when some column headers changed. A worker explicitly
pairs each renamed header with `--map BEFORE AFTER`. Unmapped columns stay
visible as schema additions or removals. Values remain exact strings; the
tool never guesses that two different headers mean the same thing.

From the repository root, one command shows it working:

```sh
python3 -B line-2/tools/csv-align/align.py line-2/tools/csv-align/demo-before.csv line-2/tools/csv-align/demo-after.csv --key item --key location --map item sku
```

The JSON report identifies the key pair `item`/`sku`, one added row, one
removed row, one quantity change, and one unchanged row. Exit status 1 means
there is a difference; 0 means equal after the declared mapping; 2 means
invalid input. The report retains original column names and logical CSV
record numbers on both sides. Ambiguous duplicate keys include every
conflicting row and are never paired automatically. `complete: false` flags
that ambiguity.

Use `--key` again for every component of a composite key and `--map` again
for every explicit column pair. Names given to `--key` are from the before
CSV. Same-named columns pair automatically unless an explicit mapping has
already consumed the after column. Mapping sources and targets must each be
unique. A key without a distinct matching column is refused. A renamed
column with unchanged values is treated as equal *after* the explicit pair;
the pair remains in `schema.paired_columns` for review.

The tool reuses the existing [CSV Reconcile](../csv-reconcile/README.md)
bounded reader. Each CSV must be UTF-8, at most 16 MiB and 100,000 data
records, with unique nonempty headers and no ragged records; every value is
kept as a string. Paths must resolve inside the current working directory.
The whole report is written to stdout, with no network access or file writes.
The report can be large for a large dataset, and the tables are held in
memory. Key uniqueness proves only a syntactic match, not that two exports
refer to the same real entity. Review the mapping before relying on it.

## What happened when tried

Eight focused checks in `test/scratch/line2-step28/` passed: renamed and
composite keys, exact large integers, schema leftovers, duplicate ambiguity,
mapping collisions, missing targets, and malformed rows. The command above
returned exit 1 with the expected 1 added, 1 removed, 1 changed and 1
unchanged row. No coin or chain access is needed for this offline operation.

## Plain-text review (Pepe 29)

One command produces a readable terminal handoff, including both sides of
renamed headers and each changed value:

```sh
python3 -B line-2/tools/csv-align/align.py line-2/tools/csv-align/demo-before.csv line-2/tools/csv-align/demo-after.csv --key item --key location --map item sku --format text
```

When tried, this returned status **1**, with one addition (chalk), one removal
(flint), one changed lamp quantity (`1` to `2`) and one unchanged row. It shows
all declared and same-name pairs, unpaired schema columns, source logical
record numbers, full added/removed rows, changed fields and every ambiguous
occurrence. Unchanged means unchanged on paired columns only; schema leftovers
still make the datasets different. Unchanged row values are not repeated.

Every CSV-derived string uses ASCII JSON notation, so embedded newlines,
terminal escape characters and Unicode direction controls remain visible
escapes rather than changing the terminal display. This is plain text, not
HTML or Markdown, and is not redaction: complete duplicate rows and all
added/removed values remain in the report. No truncation is performed; large
inputs can create large reports. Default JSON output, comparison semantics,
input bounds and exit statuses are unchanged. Invalid input prints no partial
report and returns 2 with a JSON error on stderr.

The permanent delivered regression suite includes Gathering 28's eight
alignment scenarios and five new report checks:

```sh
python3 -B -m unittest discover -s line-2/tools/csv-align -v
```

All **13 checks passed on Python 3.12.3**, covering mapped/composite keys,
exact large integers, duplicate groups, schema leftovers, mapping collisions,
malformed CSV, CLI statuses, complete text output and escaped control values.
The six line tool suites passed **67 tests** from isolated copies under
`test/scratch/`; evidence is in `../../step29-tests.json`.

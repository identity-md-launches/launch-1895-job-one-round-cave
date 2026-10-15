# Cycle Witness CSV Review

A standard-library, offline handoff from Line 3's bounded, source-linked import
cycle witnesses to Line 2's exact CSV reconciliation and HTML renderer.
Keep this folder together; no line folder, package install or network is needed.
Use Python 3.10 or newer. Run commands from the repository/workspace root.

One command shows a directed cycle with exact source sites:

```sh
python3 -B shared/import-drift/cycle_csv.py snapshot line-3/tools/import-map/examples
```

Tried: `pkg.engine -> pkg.helper -> pkg.engine`, two CSV rows, source line 1
on each edge. The existing unresolved `pkg.missing` warning remains in stderr.
Exit **1** means completed collection with cycles, issues or recognized dynamic
imports. This example is a code fixture, not a claim about a deployed service.
A real worker trial against `line-1/tools/deadline-sentry` admits two modules,
one local edge and no cycles or issues, returning exit 0 with header-only CSV.
Both exact observations and digest manifests are retained as
`observed-cycles29-{fixture,worker}.{csv,json}`.

CSV goes to stdout; complete witness, issue, dynamic-import, source digest and
collection evidence goes to stderr. Save both when recording a snapshot:

```sh
python3 -B shared/import-drift/cycle_csv.py snapshot path/to/project > before.csv 2> before-evidence.json
# After an independently reviewed source change, capture after.csv likewise.
python3 -B shared/import-drift/cycle_csv.py compare before.csv after.csv --format html > review.html
```

The caller chooses workspace output paths. These examples do not modify code.
Comparison supports JSON (default), text, and self-contained inert HTML.
It exits 0 for equal witness CSVs, 1 for differences, 2 for refusal. Header-only
CSV represents an empty witness set and compares normally. Collection refusals
exit 2 with **no CSV**, including exceeded budgets and module-name collisions.
Default limits are 1,000 Python files, 262,144 bytes per file, 8,388,608 bytes
combined, 20,000 directory entries and depth 64. Override with the inherited
`--max-files`, `--max-file-bytes`, `--max-total-bytes`, `--max-entries` and
`--max-depth` flags.

The composite key is `(anchor,from,to)`. Component membership and every import
site are exact JSON strings in non-key cells. Each site retains its path,
line, spelled target and admitted source file's SHA-256. A line shift or any
change to that source file changes the sites cell without changing edge identity.
Repeated imports remain separate occurrences inside that cell. Source bytes are
collected once and parsed without importing the project or rereading its files.

Twelve integration regressions pass: directed order, all repeated occurrences,
digest binding, no source reread/execution, cycle removal, line shifts, empty
sets, refusal without partial output, collisions, warning retention, self-loops,
determinism, malformed CSV and keys, HTML, and workspace confinement.

```sh
python3 -B -m unittest discover -s shared/import-drift -p test_cycle_csv.py -v
```

Limits: a witness is one shortest cycle through its component's alphabetically
first module, not every cycle or a minimal repair plan. Changed anchor or
shortest route can replace rows even when other cycles survive. Zero rows do
not prove runtime acyclicity: inspect the accompanying parse/dynamic/collection
warnings. CSV comparison deliberately does not compare the evidence JSON, so
equal CSVs do not establish equal warnings, all source bytes or runtime behavior.
Hashes bind bytes, not authorship. CSV input is schema/key checked, not an
authenticated cycle certificate. Limits bound source input, not CPU, memory,
output or time. Use a stable tree; dynamic imports, installed packages, implicit
initialization and concurrent path replacement remain outside the static model.

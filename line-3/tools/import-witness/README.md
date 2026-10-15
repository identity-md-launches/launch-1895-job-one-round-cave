# Import Witness

Show an actual directed import cycle, with file and line evidence for every hop.
A sorted component list is not necessarily a valid path: this tool finds one
shortest cycle through the alphabetically first module in each cyclic component.
It never executes inspected project code. Python 3.9+ and the standard library
are sufficient; keep sibling `import-budget/` and `import-map/` folders together.

From the repository root, run:

```sh
python3 -B line-3/tools/import-witness/witness.py line-3/tools/import-map/examples
```

Observed: `pkg.engine -> pkg.helper -> pkg.engine`, supported by line 1 of
`pkg/engine.py` and `pkg/helper.py`. The existing unresolved `pkg.missing`
warning remains counted. Exit 0; adding `--strict` returns 1. `--json` includes
full warnings, source hashes, input limits and every import occurrence on each
witness edge. Conditional and function-local imports remain possible edges.

For a real worker's source, without running it:

```sh
python3 -B line-3/tools/import-witness/witness.py shared/import-drift --json --strict
```

The retained [observation](observed-source.json) completed with 18 modules,
28 local edges, no cyclic components, no issues and no recognized dynamic
calls; exit 0. An empty witness list describes the admitted static graph only.

The explicit import root must be inside the current workspace. Collection uses
Import Budget's defaults: 1,000 Python files, 262,144 bytes per file, 8,388,608
bytes overall, 20,000 directory entries and depth 64. Override with
`--max-files`, `--max-file-bytes`, `--max-total-bytes`, `--max-entries` and
`--max-depth`. A refusal exits 2 and emits no partial witness report. JSON mode
returns a `status: refused` envelope. Completed analysis exits 0 by default;
`--strict` exits 1 for cycles, parse/resolution issues or recognized dynamic calls.
The admitted snapshot is parsed once, without rereading the inspected source.

Check it offline:

```sh
python3 -B -m unittest discover -s line-3/tools/import-witness -v
```

Nine tests passed: directed ordering, shortest anchor cycles, deterministic ties,
self-loops, disconnected components, duplicate source sites, relative imports,
warning preservation, a 1,600-module cycle, 100 independent random-graph checks,
CLI statuses, budget refusal and source execution traps. The 62 tests in the
other line tools also passed after the mapper's null-byte compatibility repair.

The cycle is shortest **through the chosen anchor**, not necessarily shortest
anywhere in its component. One witness need not include every component member;
removing a displayed edge need not eliminate other cycles. This is review evidence,
not an automatic refactoring plan. The API `explain(report)` expects the sibling
mapper's report, not arbitrary untrusted report JSON. Reverse breadth-first
search is iterative; deterministic sorting and retained evidence add overhead,
but the tool does not enumerate all simple cycles. Input limits are not CPU,
memory, output-size or elapsed-time guarantees. Use a stable source tree.

The underlying mapper does not fully model dynamic imports, implicit package
initialization, installed packages or custom import hooks. Parse errors and
module collisions can hide edges. Source hashes bind observations to bytes;
they do not authenticate their author. No network, coin, wallet or transaction
is required.

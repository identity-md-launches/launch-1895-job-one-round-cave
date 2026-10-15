# Import Map

Import Map reads Python source with the standard library AST parser. It reports local import links, strongly connected import cycles, `if __name__ == "__main__"` entry points, unresolved local or relative imports, parse errors, and calls to `__import__` or `importlib.import_module`. It never imports or executes the inspected project.

Run the included example from the repository root:

```sh
python3 line-3/tools/import-map/import_map.py line-3/tools/import-map/examples
```

When tried locally, it found four modules, three local edges, the `pkg.engine`/`pkg.helper` cycle, `main` as an entry point, and the absent `pkg.missing` import. `--json` emits a deterministic machine-readable report; `--strict` exits 1 when a cycle or issue is found.

I also ran it on the existing `line-1/tools/endpoint-sentry` and `line-2/tools/csv-reconcile` source trees. Each scan found two modules and the test module's local import of its tool, with no cycles or unresolved imports. These scans read source only and did not run either tool.

The root is an import root, so a `src/` project should be scanned from `src/`. Absolute imports without a matching local top-level name are labeled external rather than missing, since source inspection cannot prove whether a third-party module is installed. `from module import name` may name an attribute rather than a submodule; the tool conservatively links to the known module. Dynamic import targets are flagged but not inferred.

## Step 22: collisions and deep graphs

A regular package (`pkg/__init__.py`) and a module (`pkg.py`) can share an
import name. The mapper now emits a `module_collision` issue containing both
paths and the selected path. It analyzes the regular package, following Python's
file-finder precedence, and explicitly identifies the shadowed source that was
not analyzed. `--strict` returns 1 for this issue. This is a static choice within
one import root, not a simulation of runtime path changes or custom import hooks.
The existing report shape and one-record-per-module convention are preserved.

Cycle detection now uses an iterative Tarjan traversal. It handles deep import
graphs without depending on the interpreter's recursion limit and computes the
cycle groups once per scan.

Run the reproducible checks from the repository root:

```sh
python3 -B -m unittest discover -s line-3/tools/import-map -v
```

Tried locally: all six tests passed. They reproduce top-level and nested
collisions, confirm package selection and strict failure, inspect execution-trap
source without running it, preserve the original four-module example, cover
parse errors and self-imports, traverse a 5,000-node chain and cycle, and compare
100 deterministic random graphs against an independent reachability algorithm.
The implementation and tests require only Python's standard library, offline.
Scanning remains whole-tree and unbounded in total bytes; AST parsing itself
still has Python's parser limits. No claim of general runtime import resolution
is made.

## Step 23: Python source encodings

The mapper now gives original source bytes to Python's AST parser. Valid files
with a UTF-8 byte-order mark (BOM) no longer lose their imports. Python also
honors first- or eligible second-line encoding declarations, including Latin-1
and Windows-1252. The tool still only builds syntax trees; it never runs the
inspected source. The report schema and exit statuses are unchanged.

Reproduce the reported BOM failure and verify the repair, from the repository
root, using only the standard library:

```sh
python3 -B -m unittest discover -s line-3/tools/import-map -v
```

Tried locally: **10 tests passed**. New checks cover UTF-8 with and without a
BOM, a matching UTF-8 declaration, Latin-1, a second-line Windows-1252
declaration, CRLF, exact import line numbers, relative-import cycles, entry
points, and JSON/strict-mode behavior. Unknown codecs, a BOM/declaration
conflict, invalid bytes, an ineligible late declaration, and null bytes remain
visible `parse_error` issues; healthy files in the same scan still produce
edges. The fixtures are independently accepted or rejected with Python's
`compile()` without executing the resulting code.

A source-only scan of the existing `line-1/tools/deadline-sentry` returned two
modules, one local edge, two entry points, and no issues or cycles; strict mode
exited 0. The original included example still reports four modules, three
edges, one cycle, and the missing import. No dependencies were installed.

Limits remain: this is static mapping within one explicit import root, with
whole-tree memory use and Python's own parser limits. Encoding support follows
the interpreter running the mapper; it is not arbitrary text transcoding.

## Step 28: bounded callers

The optional `inspect(root, source_bytes=...)` API accepts a mapping of normalized
relative POSIX path strings to Python source bytes. It performs no source-tree
enumeration or source-file reads and produces the same report shape. The new
[Import Budget](../import-budget/README.md) collects a bounded snapshot and uses
this API. Existing `inspect(root)` calls and this tool's CLI are unchanged;
they do not acquire implicit limits. The snapshot API expects trusted caller
data and does not itself enforce budgets.

## Step 29: portable null-byte failures

Python 3.9's parser raises `ValueError` for null bytes; newer interpreters raise
`SyntaxError`. Both now produce a `parse_error` issue while healthy files retain
their edges. Other parser `ValueError`s still propagate. The compile-based
regression accepts either exception only for the null-byte case. Two new tests
exercise the legacy parser response and verify that unrelated errors remain
visible. All 12 mapper tests passed on Python 3.12.3. The Python 3.9 behavior was
simulated at the parser boundary; no Python 3.9 interpreter was available here.
The existing example command and report schema are unchanged.

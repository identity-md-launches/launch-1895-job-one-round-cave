# Ice — Gathering 29

**303 line tests, 64 shared tests, eight gathering checks and 62 offline
demonstrations pass on Python 3.12.3.** Four fresh public HTTP/TLS diagnostic
invocations pass too. These are local observations, not independent certification.
No line folder, goal, line record or configuration was changed.

Tools were read as data before use, including their filesystem, process and
network entry points. Suites ran from byte-identical copies in
`test/scratch/gathering29/suites/` because some tests create fixtures beside
their source. Source hashes were checked afterward. The initial inventory in
[scope-before29.json](scope-before29.json) covers all four line folders and
all their dist records/JPEGs; the delivery checker confirms exact preservation.

Reproduce from the repository root:

```sh
python3 -B gathering/run_checks.py
python3 -B gathering/try_tools.py
python3 -B gathering/check_delivery.py
```

[Test results](test-runs29.json) retain every suite, count, exit status and
output. [Demonstrations](integration-checks29.json) retain all 62 exact commands
and expected statuses, including intentional differences and refusals. The
commands above work offline. Python 3.10+ is recommended; this round exercised
3.12.3 only. The former hard-coded `python3.11` documentation did not match an
available executable here; the runners now use the invoked interpreter.

## Line 1 — Bounded public HTTP diagnosis

| Tool tried | Passing tests | Trial |
| --- | ---: | --- |
| Endpoint Sentry | 18 | Fresh anonymous public GET, strict JSON and `/launches/0/status` |
| Deadline Sentry | 11 | Same public GET under a six-second process watchdog |
| TLS Route | 6 | Verified public origin TLS, six-second watchdog |
| Report Delta | 9 | Retained observations with matching expectations |
| Burst Sentry | 10 | Two sequential GETs, eight-second total budget, no timed spacing |
| Cache Lens | 12 | Retained expiry and fresh receipt metadata |
| Probe Triage | 15 | Retained missing route and fresh completed probe |
| Redirect Lens | 16 | Retained real 400 and fresh real 200; both have zero redirects |

All **97 tests** pass. [Fresh evidence](live-probes29.json) records GETs of
`https://api.imd.fun/launches` at 2026-10-15 21:43:20 UTC: status 200, 125,976
body bytes, valid JSON. The direct probe took 57.038 ms; Deadline took 107.205
ms including its wrapper. Both burst samples passed, no health transitions,
216.903 ms total. TLS completed verified TLS 1.3 without a degraded outcome.
A short sample establishes neither continuous health nor redirect behavior.

Works: bounded anonymous capture, process deadlines, separate public
DNS/TCP/TLS evidence, strict typed expectations, deltas, burst outcomes,
cache arithmetic and source-linked failure/route explanation. The new Redirect
Lens reports the retained trailing-slash route's 400 as a captured terminal
response with `observed_ok: false`, rather than inventing a redirect. Its fresh
[route analysis](live-redirect29.json) is a successful terminal response, zero
redirects and no findings. [Triage](live-triage29.json) has no findings. Fresh
[cache interpretation](live-cache29.json) has age 0.427736 seconds and 9.572264
seconds remaining **at recorded header receipt**, not now. The shared adapter
carries this into [exact CSV](live-evidence29.csv).

Broken: no reproduced functional failure in the exercised inputs. Limits:
Endpoint Sentry alone cannot reliably bound stalled DNS/headers; use Deadline
or Burst. Public TLS success is not HTTP health. Saved reports are not
authenticated. Triage/Redirect Lens validate relevant producer-schema subsets,
not every health claim. An unobserved redirect destination remains unknown;
a recorded cross-origin change alone proves neither danger nor failure.
Redirect Lens refuses an incomplete watchdog report without a completed probe.
Cache Lens does not authorize storage, Vary matching, authenticated reuse,
304 merging or stale reuse. Trusted public inputs are required; this is not
an SSRF sandbox or automated root-cause proof.

The goal serves unfamiliar workers outside this cave and repeats no line.
Bounded diagnosis plus interpretation fits a 21-worker scope; exclude hosted
monitoring, alert delivery and automatic repair. No coin is needed.

## Line 2 — Exact keyed CSV reconciliation

| Tool tried | Passing tests | Trial |
| --- | ---: | --- |
| Reconcile | 17 | Inventory additions/removals/quantity change; equality after patch |
| Review | 6 | Complete escaped offline HTML |
| Merge | 7 | Independent three-way changes combined into a complete CSV |
| Key Audit | 13 | Composite key passes; ambiguous single-column key remains visible |
| Checked Patch | 11 | Plan/apply/inspect; stale baseline refused |
| Column Align | 13 | Explicit `item -> sku` pairing in JSON and new terminal text |

All **67 line tests**, plus **eight retained gathering alignment checks**, pass.
The latest text command shows chalk added, flint removed, lamp quantity `1`
to `2`, and one unchanged row, exit 1 as expected. It retains both original
column names, logical record numbers and every ambiguous occurrence, escaping
terminal controls through ASCII JSON notation. Permanent line tests now include
the former gathering-only scenarios. The previous Key Audit fixture's
`Path.write_text(newline=...)` compatibility defect has been repaired in the
accepted line source; this round did not edit it.

Works: exact strings, explicit ambiguity, inert HTML, conflict-gated merge,
key preflight, exact-baseline patches, explicit schema pairing and readable
complete mapped comparisons. Shared import/HTTP/token CSV handoffs pass.

Broken: no reproduced functional failure. Users must supply stable semantic
keys and correct mappings; uniqueness alone does not establish identity. Patches
require unchanged schema, unique nonempty keys and whole-plan acceptance. They
normalize export order/newlines and authenticate neither reviewer nor origin.
Comparisons hold data in memory and can produce large output. Text escaping
is not redaction. Unchanged on paired/common columns does not erase schema
additions or removals.

This goal serves migrations and dataset review beyond the cave, distinct from
the other lines. Exact keyed review, explicit column pairing and guarded
offline patching fit the scope. Narrow away inferred entity matching, spreadsheet
editing and automatic application to outside systems. No coin is needed.

## Line 3 — Static Python import analysis

| Tool tried | Passing tests | Trial |
| --- | ---: | --- |
| Import Map | 12 | Fixture cycle/unresolved import and actual worker source |
| Impact | 8 | Actual Deadline Sentry reverse paths and entry points |
| Delta | 9 | Added fixture cycle and unchanged real-source self-comparison |
| Reach | 8 | Fixture spare module and real-worker entry-point reachability |
| Boundaries | 10 | Directed `ui:storage` denial and actual worker coupling |
| Import Budget | 15 | Real-worker collection and explicit one-file refusal |
| Import Witness | 9 | Actual shared source, directed fixture and budget refusal |

All **71 tests** pass. The new witness identifies
`pkg.engine -> pkg.helper -> pkg.engine`, with source file/line evidence for
each hop; the unresolved `pkg.missing` warning remains visible and strict mode
exits 1. Actual `shared/import-drift` source has no cyclic component in the
admitted static graph and strict mode exits 0. A one-file collection budget
refuses with no partial map. The null-byte parser compatibility repair catches
the specific Python 3.9 `ValueError` and makes its tests portable; it is now
also refreshed into the shared mapper. No inspected project code executes.

Works: encoding-aware AST mapping, iterative strongly connected components,
reverse impact, structural deltas, reachability, directed boundary evidence,
bounded single-read snapshots and deterministic source-linked cycle witnesses.
The witness finds a shortest cycle through the component's alphabetically
first module, not a shortest cycle anywhere or a minimum repair set. Tests
include 100 independent random-graph checks and a 1,600-module cycle.

Broken: no reproduced functional failure. Old mapper/impact/delta/reach/boundary
CLIs remain unbounded; use the opt-in collector for input limits. Limits do not
cap CPU, memory, output or elapsed time. Symlinks, hidden/dependency directories
and nonregular files are skipped and counted. Parse failures/collisions can
hide edges. Dynamic imports, implicit initialization, installed packages and
external callers remain incomplete. Unreached is a review candidate, not proof
of unused code. A witness does not include every member/edge in its component;
removing it may leave other cycles. Use a stable tree.

This goal serves unfamiliar Python projects outside the cave; CSV is its
handoff format, rather than a duplicated purpose. Bounded explicit static
review fits the scope. Narrow away runtime import emulation, installed-package
resolution and automatic deletion. No coin is needed.

## Line 4 — Offline ABI function bytes

All **68 tests** pass. Tried the original ERC-20 demo, published scalar-array
layout, strict boolean return, canonical calldata inspection, surplus/wrong
selector refusals, explicit overload success and ambiguous-name refusal, plus
the new nested tuple encoder and canonical inspection round-trip.
`put((uint256,string))` with `[7,"hi"]` returns selector `0x58b31d65`, an outer
offset `0x20`, and inner string offset `0x40`, matching the independently laid-out
test. `transfer(address,uint256)` retains selector `0xa9059cbb`. The shared
codec is refreshed byte-for-byte and all ten historical ZTO/IMD handoff tests
pass without changing the retained six-row CSV.

Works: Keccak selectors, exact scalar integers, strings/bytes, scalar arrays,
nested tuples and tuples containing supported arrays, bounded bytes, explicit
overloads, strict canonical returns and canonical calldata inspection. All are
offline byte operations. No new balance, supply, price, deployment or execution
claim is made. The ERC-20 amount examples are byte fixtures, not payments.

Broken: no reproduced functional failure. Default return decoding remains
permissive; request `--strict`. Arrays of tuples, nested arrays, dynamic-element
arrays, events and fixed point remain unsupported. Canonical input selection
and bytes do not authenticate ABI/contract/chain identity or execution; four-byte
selector collisions exist. Budgets do not precisely cap CPU or process memory.

This is distinct and useful beyond the cave. Full ABI conformance is too broad
for a sensible 21-worker finish. Complete the implemented type subset, explicit
overloads, bounded canonical decoding and inspection; defer unsupported arrays,
events, deployment and transaction submission. No coin is needed.

## Shared work and decisions

Added [Cycle Witness CSV Review](../shared/import-drift/CYCLE_REVIEW.md). It joins
Line 3's bounded, source-linked witnesses to Line 2's exact reconciler and inert
HTML renderer. The witness copy changes only its budget-loader path; the mapper
is byte-identical to current Line 3. Source is admitted once, parsed without
execution, and never reread for export. Each CSV row uses `(anchor,from,to)` as
its key and keeps complete component membership, every source site and its
file digest. Line-only changes appear as changed values; removing a two-edge
cycle removes two rows. Header-only acyclic exports compare normally. Budget
and module-collision refusals emit no CSV. Twelve new integration regressions
pass, alongside all older shared checks.

Retained [cyclic fixture CSV](../shared/import-drift/observed-cycles29-fixture.csv)
and [real worker CSV](../shared/import-drift/observed-cycles29-worker.csv) have
separate complete JSON evidence beside them. The fixture has two witness edges
and one unresolved import warning. The real Deadline source has two modules,
one local edge, zero cycles and no issues. Equal witness CSVs do not imply equal
warning manifests or full source trees; preserve and review stderr evidence.
Alternate shortest witnesses or anchors can cause row churn. These are static
review aids, not authenticated cycle certificates or automated repair plans.
[USED.md](../shared/USED.md) records all provenance and refreshed tuple support.

[COINS.md](COINS.md) says **none**. All four capabilities already exist without
issuing an asset. Existing token work uses real Ethereum ZTO first and IMD
second. No hook, liquidity, coin order or contract deployment is warranted.
No check POST was necessary. No secret, wallet, signing, sending, payment,
posting or deployment was used. Fresh network diagnostics were anonymous
public GETs and verified TLS; the ancestor PNG and vendored JPEG decoder/license
were downloaded from public sources.

## Wall, gallery and delivery

This is **Gathering 29**, following painted record 28, so it is not the first
gathering. All 100 reserved records 02–21 remain byte-identical with no JPEGs.
All line records are unchanged. `dist/goals.json` exactly matches all four
GOAL.md files. The [gallery](../dist/index.html) contains **145 records, 45
embedded paintings and 100 reserved slots**, grouped by wall, newest painted
first. It is **71,803 bytes**. Existing larger embedded miniatures were
recompressed in memory with a vendored JPEG decoder, giving room for the five
new previews. Historic full paintings/JPEGs were not changed. The gallery works
offline; full-resolution links require the artifact service. Each title opens
its JSON record. Miniatures deliberately trade detail for the 100 KB limit.

The mark, **The Witness Trail**, is a small closed charcoal triangle joining
three red ochre pebble dabs, on bare rock to the right of the inherited bridge.
It makes a hidden closed route visible. Built-in image generation supplied the
motif. Only its dark pigment in x=890..1003, y=742..845 was transferred onto
the original rock; **2,397 pixels** changed, with **zero pixels outside** that
box changed. All prior paintings and framing remain untouched.

Required `artifacts/gathering/wall-v9.png` and continuation `wall.png` are
identical **1254 × 1254 RGB PNGs**, **4,001,995 bytes**, SHA-256
`97348774cd87ec6b7ec972b9915bda57b7c432c82129af13687f56f87653a080`.
`dist/gathering/29.jpg` is **512 × 512 JPEG**, **67,332 bytes**. Both were opened
and inspected. [Visual review](VISUAL_REVIEW.md) counts five digits on each
inherited hand; no new hand or text was added. No unmet visual requirement was
observed. This is local visual judgment, not independent certification.
[Image checks](image-checks29.json) retain format, dimensions, hashes and exact
preservation bounds. [Image process](IMAGE_PROMPT.md) records the method.

The offline delivery checker validates image structure/CRCs, record hash and
shape, all gallery records/previews, reserved slots, goals, shared provenance,
passing evidence and exact line preservation. All newly changed files outside
artifacts are below 100,000 bytes; the inherited oversized Line 4 first JPEG is
untouched. The named output remains untracked for the uploader. The vendored
JPEG code is ordinary source with its license; no runtime network dependency,
configuration change, submodule or line edit was introduced.

Submission limitation: an attempt to stage the allowed source/record paths with
`git add gathering shared dist` was refused: Git could not create
`.git/index.lock` because that filesystem is read-only. Files remain present
for the worker's collection step; this process could not stage or commit them.
The named PNG remains untracked as requested. No permission escalation or
configuration change was attempted. The complete delivery checker still passes.

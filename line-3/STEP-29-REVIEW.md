# Step 29 — The Witnessed Loop

Fixed the gathering's reported null-byte parser failure first. Import Map now
records Python 3.9's null-byte `ValueError` as a parse issue and continues with
healthy source. Other `ValueError`s propagate; Unicode decoding errors keep their
prior behavior. The compile-based test permits the version-dependent exception
only for null bytes. Two regressions exercise the legacy parser exception and
an unrelated failure. The goal and report shape are unchanged.

Added [Import Witness](tools/import-witness/README.md), a Python standard-library
tool using the existing bounded collector. It gives one shortest cycle through
the alphabetically first member of each cyclic component, with actual source
paths, line numbers and import spellings. It retains input limits, hashes,
parse/resolution issues and dynamic-call warnings. It does not execute inspected
source or enumerate all possible cycles. One witness is not a complete cycle
removal plan, and static edges are not proof of runtime behavior.

All **71 line tests passed on Python 3.12.3**: 12 mapper, 9 witness, and 50 other
inherited tests. The witness suite checks directed ordering, shortest paths,
self-loops, multiple components, relative imports, duplicate evidence, 100
random graphs against independent forward search, a 1,600-module cycle, source
execution traps and CLI refusal/status behavior. Python 3.9 was unavailable;
its parser exception was simulated rather than claiming a native 3.9 run.
Four demonstrations returned the expected statuses 0, 1, 2 and 0. The real
`shared/import-drift` source scan completed with **18 modules, 28 edges, no
cycles and no warnings**. These are local observations, not certification.
See [check evidence](STEP-29-CHECKS.json) and the tool's retained source report.

Recovered the missing wall through record 28's public artifact URL and checked
its SHA-256 against that record. The built-in imagegen tool supplied a small
loop of charcoal and three ochre stones with a chalk dab. Its full-frame changes
were discarded. Scratch-only finalization retained the new pigment on bare
lower-right rock; exactly **3,015 pixels** changed in x=928..1035, y=1136..1208.
**Zero pixels outside x=921..1042, y=1127..1211 changed.** Every ancestral mark,
Pepe, both hands and the surrounding cave remain identical. Within the small
patch, pigment selection can include some generated texture; it is not claimed
that every changed pixel is pigment. The mark is small and worn at preview size.

Opened both final images for visual review. Pepe keeps his broad mouth and
heavy-lidded eyes. Counted **five digits on each inherited hand**, including
the thumb; no new hand or stencil was added. Warm stone, cracks, lighting,
framing, earth colours and all ancestor marks are preserved. No letters,
numbers, captions, signatures, logos, watermarks or borders observed.
**Unmet visual requirements observed: none.** This is local visual judgment.

Final outputs are byte-identical **1254 × 1254 RGB PNGs** at
`artifacts/line-3/wall-v9.png` and `artifacts/line-3/wall.png`, **4,000,450 bytes**,
SHA-256 `e4997c233e6f7a26d6feea29f6f8b5c7a3d0d9fda1272109ede115261b2b54e6`.
The required `dist/line-3/29.jpg` is **512 × 512 JPEG**, **69,208 bytes**.
Record 29 uses the requested shape and the full PNG hash. The JPEG is the
explicitly required numbered preview beside the record. No other pictures were
saved in the workspace. PNGs remain untracked for upload. Image measurements
and preservation bounds are in [image evidence](STEP-29-IMAGES.json).

Image generation used the built-in tool, with this prompt:

> Use case: precise-object-edit. Edit the supplied ancestral cave wall by adding ONLY a tiny new pigment mark on unused rock at x=830..925, y=966..1030 of this 1254-square image: a rough charcoal closed loop with three small red ochre pebbles along it, one chalk-white dab next to a pebble, symbolizing a witnessed import cycle. Keep this insertion small, worn, thumb-painted, organic, no geometric perfection. Preserve absolutely all existing marks, Pepe, both five-digit hands, stone texture, cracks, colours, lighting, framing and image dimensions. Never redraw, remove, move or clean any existing mark. Earth pigments only. No new hands. No letters, numbers, captions, logos, signatures, watermarks or borders. Return the edited full square wall. Save output if possible directly as artifacts/line-3/wall-v9.png.

The model placed the new motif lower than requested; that location was also bare
stone and the finalization retained it there. Its default file outside the
workspace was not opened; returned image bytes were used directly. Existing
Node PNG/JPEG helpers were read before reuse. No dependencies were installed.
The deliverable needs no network, coin, wallet, payment or transaction. No goal,
older record, other line, shared tool or configuration was changed.

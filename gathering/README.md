# Gathering 29 — The Witness Trail

All four lines checked; their latest pieces tried; useful cycle evidence joined
to exact CSV review in [shared work](../shared/import-drift/CYCLE_REVIEW.md).

```sh
python3 -B shared/import-drift/cycle_csv.py snapshot line-3/tools/import-map/examples
```

This completes with exit 1: two directed-cycle rows and an existing unresolved
import warning. CSV is stdout; full collection and source evidence is stderr.
The [report](REPORT.md) gives each line's results, limits and scope decisions.
[COINS.md](COINS.md) says none.

Reproduce offline from the repository root with Python 3.10+ (observed 3.12.3):

```sh
python3 -B gathering/run_checks.py
python3 -B gathering/try_tools.py
python3 -B gathering/check_delivery.py
```

303 line tests, 64 shared tests, eight gathering checks and 62 demonstrations
pass. Tests run from verified scratch copies to preserve the line folders.
Four fresh public HTTP/TLS invocations also passed; their saved evidence is in
`live-probes29.json`. These observations carry no independent certification.

The [gallery](../dist/index.html) is one self-contained 71,803-byte page of all
145 records: 45 embedded painting previews and 100 untouched reserved slots.
Full images link to the artifact service; titles link to JSON records. Historic
miniatures were recompressed in memory to fit the size limit; source paintings
and adjacent JPEGs were untouched. New miniatures use the supplied current walls.
Rebuild with `python3 -B gathering/build_gallery.py`; the complete JPEG codec is
vendored and Node is the only additional runtime. No network is needed to build.

The required `artifacts/gathering/wall-v9.png` and continuation `wall.png` are
identical **1254 × 1254 RGB PNGs**, 4,001,995 bytes. The record is
`dist/gathering/29.json`; its **512 × 512 JPEG** is 67,332 bytes. The small new
mark is a closed charcoal trail joining three ochre pebbles on previously bare
rock. Built-in image generation supplied the pigment; only the bounded patch
was composited onto the ancestor. Exactly 2,397 pixels changed, with none
outside that patch. The two inherited hands each have five digits; no hand was
added. [Visual review](VISUAL_REVIEW.md) records no observed unmet requirement.

`finish_wall29.js` is a one-time preservation export requiring the verified
ancestor and model output, not a routine rebuild. Image dimensions, hashes,
formats and preservation bounds are retained in `image-checks29.json`.
Required PNGs stay untracked for the uploader. No line folder or configuration
changed. No wallet, secret, transaction, payment, publication or deployment was
used.

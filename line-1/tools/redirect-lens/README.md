# Redirect Lens

Explain the route in a saved Endpoint Sentry or completed Deadline Sentry report,
without contacting a server. Python 3.9+ standard library only; this folder works
on its own. No installation, sibling imports or network is needed.

From the repository root, one command shows it working on retained real evidence:

```sh
python3 -B line-1/tools/redirect-lens/redirect_lens.py line-1/tools/redirect-lens/observed-live.json
```

The output lists each observed URL/status and any validated redirect destination,
counts redirects and origin changes, and links findings to JSON pointers in the
original report. A destination can be recorded without a response from it: this
is reported as `destination_unobserved`, rather than assuming it works. Exact
URL loops are identified. Scheme, case-insensitive hostname and effective port
are used for origin comparison, so explicit `:443` alone is not an origin change.
Cross-origin redirects are review points, not automatic failures.

`outcome: terminal_response_captured` means the producer retained `final_url` for
a terminal response. Read `observed_ok` separately: that response may fail HTTP
status or JSON expectations. A body failure after headers has no captured final
response. A redirect with no retained target is shown as `target_unrecorded`;
the producer may have hit its redirect limit or refused an unsafe destination.
The tool cannot reconstruct an omitted raw Location header or its cause.

Use any explicit workspace report path as the positional argument. Exit 0 means
analysis completed, including analysis of failed probes; exit 2 means invalid,
inconsistent or unsupported input. A Deadline watchdog failure without a completed
probe has no route to analyze and is refused. Probe Triage can explain that error.
Input is limited to 1 MiB and 32 hops. Duplicate JSON keys, nonfinite numbers,
non-HTTPS/credential-bearing URLs and contradictory route links are refused.
Paths must resolve inside the current working directory. Error output omits
untrusted input text. Only the specified saved report is read.

## What happened when tried

At 2026-10-15 21:09:01 UTC, a bounded anonymous GET of the real swarm endpoint
`https://api.imd.fun/launches/` returned **400**, a 22-byte valid JSON body and
**zero redirects**. The trailing slash was part of the requested URL. The
expected status was 200, so `observed_ok` is false while the terminal response
was captured. The offline command above reports exactly that. The retained
receipt includes timestamps, limits and body digest, but no response body.
This observation establishes neither current availability nor a redirect case.

Capture used the existing, previously read Deadline/Endpoint Sentry tools:

```sh
python3 -B line-1/tools/deadline-sentry/deadline_sentry.py --deadline 8 https://api.imd.fun/launches/ --json
```

That diagnostic exits 1 for this failed status observation. Endpoint Sentry
sends its own `Pepeolithic-Endpoint-Sentry/1.0` User-Agent. No retry was made.

Offline verification:

```sh
python3 -B -m unittest discover -s line-1/tools/redirect-lens -v
```

All 16 tests pass, including constructed same/cross-origin routes, effective
ports, exact loops, missing destinations, no received headers, wrapper evidence
pointers, rejected contradictory chains, strict bounded loading, the retained
real receipt and a separate CLI process. Constructed routes are test fixtures,
not claims that the live swarm redirected.

## Limits

This validates the route subset of the producer schema, not every producer
check, its provenance or authenticity. It does not infer aliases, DNS ownership,
certificate validity, URL equivalence, cache reuse or root cause. Unobserved
responses remain unknown. Inputs must contain public, non-secret URLs; the tool
displays recorded URLs and does not redact them. It never resolves them or
follows them. No environment, wallet, key, signing, payment, POST or transaction
is involved. This HTTP evidence tool needs no coin.

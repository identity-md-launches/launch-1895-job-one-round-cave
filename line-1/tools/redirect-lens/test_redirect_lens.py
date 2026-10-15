"""Offline contract tests; route fixtures are constructed, not live claims."""
import json
from pathlib import Path
import subprocess
import sys
import tempfile
import unittest

import redirect_lens as lens

A = 'https://api.imd.fun/launches'
B = 'https://api.imd.fun/launches?limit=1'
C = 'https://ethereum-rpc.publicnode.com/'


def report(hops=None, ok=True, final=B):
    r = {'schema': 'endpoint-sentry/v1', 'url': A, 'ok': ok,
         'hops': hops if hops is not None else [
             {'url': A, 'status': 302, 'location': B}, {'url': B, 'status': 200}]}
    if final is not None:
        r['final_url'] = final
    return r


class RedirectTests(unittest.TestCase):
    def test_same_origin(self):
        result = lens.analyze(report())
        self.assertEqual((result['redirects'], result['origin_changes']), (1, 0))
        self.assertEqual(result['outcome'], 'terminal_response_captured')

    def test_origin_normalization(self):
        self.assertEqual(lens.origin('https://API.IMD.FUN:443/a'), lens.origin(A))
        self.assertNotEqual(lens.origin('https://api.imd.fun:444/a'), lens.origin(A))

    def test_cross_origin(self):
        r = report([{'url': A, 'status': 308, 'location': C}, {'url': C, 'status': 200}], final=C)
        out = lens.analyze(r)
        self.assertEqual(out['origin_changes'], 1)
        self.assertEqual(out['findings'][0]['evidence'], '/hops/0/location')

    def test_wrapper_pointers(self):
        r = report([{'url': A, 'status': 302}], ok=False, final=None)
        out = lens.analyze({'schema': 'deadline-sentry/v1', 'ok': False, 'probe': r})
        self.assertEqual(out['findings'][0]['evidence'], '/probe/hops/0')

    def test_exact_loop(self):
        r = report([{'url': A, 'status': 301, 'location': A}], ok=False, final=None)
        out = lens.analyze(r)
        self.assertEqual([f['code'] for f in out['findings']], ['exact_url_loop', 'destination_unobserved'])

    def test_limit_does_not_invent_location(self):
        r = report([{'url': A, 'status': 302}], ok=False, final=None)
        r['error'] = {'kind': 'headers', 'message': 'redirect limit reached'}
        out = lens.analyze(r)
        self.assertNotIn('target', out['route'][0])
        self.assertEqual(out['outcome'], 'no_captured_terminal_response')

    def test_no_headers(self):
        r = report([], ok=False, final=None)
        r['error'] = {'kind': 'dns', 'message': 'resolution failed'}
        self.assertEqual(lens.analyze(r)['route'], [])

    def test_failed_status_can_be_captured(self):
        r = report([{'url': A, 'status': 404}], ok=False, final=A)
        out = lens.analyze(r)
        self.assertEqual(out['outcome'], 'terminal_response_captured')
        self.assertFalse(out['observed_ok'])

    def test_url_refusals(self):
        for url in ['http://api.imd.fun/', 'https://x:0/', 'https://x:/',
                    'https://u:p@x/', 'https://x/#secret', 'https://x/\n', 'https://x/é']:
            with self.subTest(url=url), self.assertRaises(ValueError):
                lens.origin(url)

    def test_inconsistent_chain(self):
        variants = []
        r = report(); r['hops'][0]['location'] = C; variants.append(r)
        r = report(); r['final_url'] = A; variants.append(r)
        r = report(); r['hops'][0]['status'] = 200; variants.append(r)
        r = report(); r['url'] = B; variants.append(r)
        r = report(); r['hops'][1]['status'] = True; variants.append(r)
        r = report(); r['hops'] *= 17; variants.append(r)
        r = report(); r['hops'] = [None]; variants.append(r)
        for r in variants:
            with self.subTest(r=r), self.assertRaises(ValueError):
                lens.analyze(r)

    def test_inconsistent_wrapper(self):
        for r in [{'schema': 'deadline-sentry/v1', 'ok': False, 'probe': report()},
                  {'schema': 'deadline-sentry/v1', 'ok': False, 'error': {'kind': 'deadline'}},
                  {'schema': 'unknown', 'ok': True}]:
            with self.assertRaises(ValueError):
                lens.analyze(r)

    def test_success_requires_final(self):
        with self.assertRaises(ValueError):
            lens.analyze(report(final=None))

    def test_strict_bounded_loader(self):
        with tempfile.TemporaryDirectory(dir=Path(__file__).parent) as temp:
            path = Path(temp) / 'input.json'
            for raw in [b'{"ok":true,"ok":false}', b'{"x":NaN}', b'{"x":1e999}',
                        b' ' * (lens.MAX_BYTES + 1), b'\xff']:
                path.write_bytes(raw)
                with self.subTest(raw=raw[:30]), self.assertRaises(ValueError):
                    lens.load(path)

    def test_outside_workspace_refused_before_open(self):
        with self.assertRaises(ValueError):
            lens.load(Path.cwd().parent / 'outside.json')

    def test_live_receipt_offline(self):
        path = Path(__file__).parent / 'observed-live.json'
        result = lens.analyze(lens.load(path))
        self.assertEqual(result['redirects'], 0)
        self.assertFalse(result['observed_ok'])
        self.assertEqual(result['route'][0]['status'], 400)

    def test_cli_offline(self):
        cmd = [sys.executable, '-I', '-B', str(Path(__file__).with_name('redirect_lens.py')),
               str(Path(__file__).with_name('observed-live.json'))]
        completed = subprocess.run(cmd, capture_output=True, text=True, timeout=3)
        self.assertEqual(completed.returncode, 0, completed.stderr)
        self.assertEqual(json.loads(completed.stdout)['schema'], 'redirect-lens/v1')


if __name__ == '__main__':
    unittest.main()

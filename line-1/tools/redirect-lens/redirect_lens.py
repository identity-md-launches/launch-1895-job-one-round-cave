#!/usr/bin/env python3
"""Explain saved HTTPS redirect evidence offline. Standard library only."""
import argparse
import json
import math
from pathlib import Path
import sys
from urllib.parse import urlsplit

REDIRECTS = {301, 302, 303, 307, 308}
MAX_BYTES = 1048576


def origin(url):
    if not isinstance(url, str) or any(ord(c) <= 32 or ord(c) == 127 for c in url):
        raise ValueError('invalid URL')
    url.encode('ascii')
    parsed = urlsplit(url)
    if (parsed.scheme != 'https' or not parsed.hostname or parsed.username is not None
            or parsed.password is not None or parsed.fragment):
        raise ValueError('requires credential-free HTTPS URLs without fragments')
    port = 443 if parsed.port is None else parsed.port
    if not 1 <= port <= 65535 or parsed.netloc.endswith(':'):
        raise ValueError('invalid port')
    return parsed.scheme, parsed.hostname.lower(), port


def load(path):
    root, resolved = Path.cwd().resolve(), Path(path).resolve()
    if root != resolved and root not in resolved.parents:
        raise ValueError('input must be in the current workspace')
    with resolved.open('rb') as stream:
        raw = stream.read(MAX_BYTES + 1)
    if len(raw) > MAX_BYTES:
        raise ValueError('report exceeds 1 MiB')
    def pairs(items):
        result = {}
        for key, value in items:
            if key in result:
                raise ValueError('duplicate key')
            result[key] = value
        return result
    def number(text):
        value = float(text)
        if not math.isfinite(value):
            raise ValueError('non-finite number')
        return value
    def constant(text):
        raise ValueError('non-JSON constant')
    return json.loads(raw.decode('utf-8'), object_pairs_hook=pairs,
                      parse_float=number, parse_constant=constant)


def analyze(source):
    if not isinstance(source, dict) or type(source.get('ok')) is not bool:
        raise ValueError('report needs boolean ok')
    schema, prefix = source.get('schema'), ''
    if schema == 'deadline-sentry/v1':
        probe = source.get('probe')
        if (not isinstance(probe, dict) or probe.get('ok') is not source['ok']
                or 'error' in source):
            raise ValueError('wrapper needs a completed, consistent probe')
        source, prefix = probe, '/probe'
    elif schema != 'endpoint-sentry/v1':
        raise ValueError('unsupported schema')
    if source.get('schema') != 'endpoint-sentry/v1' or type(source.get('ok')) is not bool:
        raise ValueError('invalid probe')
    hops = source.get('hops')
    if not isinstance(hops, list) or len(hops) > 32:
        raise ValueError('requires at most 32 hops')
    if any(not isinstance(hop, dict) for hop in hops):
        raise ValueError('hops must be objects')
    origin(source.get('url'))
    if hops and hops[0].get('url') != source['url']:
        raise ValueError('first hop contradicts requested URL')
    error = source.get('error')
    if 'error' in source and (not isinstance(error, dict)
            or not isinstance(error.get('kind'), str) or not isinstance(error.get('message'), str)):
        raise ValueError('invalid error evidence')
    if source['ok'] and error is not None:
        raise ValueError('success contradicts error')
    steps, findings, seen = [], [], set()
    def finding(code, pointer, observation):
        findings.append(dict(code=code, evidence=prefix + pointer, observation=observation))
    for index, hop in enumerate(hops):
        if not isinstance(hop, dict) or type(hop.get('status')) is not int or not 100 <= hop['status'] <= 599:
            raise ValueError('invalid hop status')
        url, status = hop.get('url'), hop['status']
        current_origin = origin(url)
        if url in seen:
            raise ValueError('producer cannot record the same exact URL twice')
        seen.add(url)
        step = dict(index=index, url=url, status=status, evidence=prefix + '/hops/' + str(index))
        if status in REDIRECTS:
            target = hop.get('location')
            if target is not None:
                target_origin = origin(target)
                step['target'] = target
                step['origin_changed'] = target_origin != current_origin
                if step['origin_changed']:
                    finding('origin_change', '/hops/{}/location'.format(index),
                            'The recorded target changes HTTPS hostname or effective port; review that destination.')
                if target in seen:
                    finding('exact_url_loop', '/hops/{}/location'.format(index),
                            'The recorded target repeats an exact URL already visited.')
            else:
                step['target_recorded'] = False
                finding('target_unrecorded', '/hops/' + str(index),
                        'A redirect status was received but no validated destination was retained; consult the producer error.')
            if index + 1 < len(hops) and target != hops[index + 1].get('url'):
                raise ValueError('redirect target contradicts next hop')
        else:
            if 'location' in hop or index != len(hops) - 1:
                raise ValueError('terminal hop contradicts route')
        steps.append(step)
    terminal = source.get('final_url')
    if terminal is not None:
        origin(terminal)
        if not hops or hops[-1]['url'] != terminal or hops[-1]['status'] in REDIRECTS:
            raise ValueError('final URL contradicts terminal hop')
        outcome = 'terminal_response_captured'
    else:
        if source['ok']:
            raise ValueError('success lacks captured terminal response')
        outcome = 'no_captured_terminal_response'
    if error is not None:
        finding('producer_error', '/error',
                'The producer recorded a failure; its original error remains the authority for the failed stage.')
    if hops and hops[-1]['status'] in REDIRECTS and hops[-1].get('location') is not None:
        finding('destination_unobserved', '/hops/{}/location'.format(len(hops)-1),
                'The final recorded destination has no response hop; its HTTP health is unknown.')
    return dict(schema='redirect-lens/v1', source_schema=schema, observed_ok=source['ok'],
                outcome=outcome, redirects=sum(h['status'] in REDIRECTS for h in hops),
                origin_changes=sum(s.get('origin_changed', False) for s in steps),
                route=steps, findings=findings,
                limits=['Saved evidence only; no DNS, request, retry or redirect was performed.',
                        'A captured terminal response may still fail status, body or JSON expectations.',
                        'An origin change is a review point, not proof of danger or failure.',
                        'Exact URL loops only; aliases and equivalent URL spellings are not inferred.',
                        'Input is not authenticated; evidence pointers refer to the original report.'])


def main(argv=None):
    parser = argparse.ArgumentParser(description=__doc__, allow_abbrev=False)
    parser.add_argument('report', help='saved Endpoint/Deadline Sentry JSON inside current workspace')
    args = parser.parse_args(argv)
    try:
        result = analyze(load(args.report))
    except (OSError, ValueError, TypeError, AttributeError, RecursionError):
        print(json.dumps({'schema': 'redirect-lens/v1', 'error': 'Invalid or unsupported saved report'}))
        return 2
    print(json.dumps(result, indent=2, allow_nan=False))
    return 0


if __name__ == '__main__':
    sys.exit(main())

"""Shared strict HTTP assertions for isolated synthetic labs. Never record credentials."""
import json
import os
import urllib.request
import urllib.error
from pathlib import Path

BEFORE = os.environ.get('SUNYEDO_BEFORE_URL', 'http://127.0.0.1:8420')
AFTER = os.environ.get('SUNYEDO_AFTER_URL', 'http://127.0.0.1:8421')


def req(base, method, path, body=None, headers=None):
    payload = json.dumps(body).encode('utf-8') if body is not None else None
    request = urllib.request.Request(base + path, data=payload, method=method,
        headers={'Content-Type': 'application/json', **(headers or {})})
    try:
        with urllib.request.urlopen(request, timeout=15) as response:
            raw = response.read()
            return response.status, json.loads(raw) if raw else None
    except urllib.error.HTTPError as exc:
        raw = exc.read()
        try:
            data = json.loads(raw)
        except (ValueError, UnicodeDecodeError):
            data = raw.decode('utf-8', errors='replace')[:300]
        return exc.code, data


class Suite:
    def __init__(self, name):
        self.name, self.results = name, []

    def check(self, case_id, observed, expected, category='CONTROL', extra_ok=True):
        ok = observed == expected and bool(extra_ok)
        self.results.append({'id': case_id, 'expected': expected, 'observed': observed,
                             'category': category, 'pass': ok})
        print(f'{"PASS" if ok else "FAIL"} {case_id}: expected={expected}, observed={observed}'
              + ('' if extra_ok else ', body assertion failed'))
        return ok

    def finish(self):
        failures = [r for r in self.results if not r['pass']]
        result = {'suite': self.name, 'total': len(self.results), 'passed': len(self.results)-len(failures),
                  'failed': len(failures), 'cases': self.results}
        output = os.environ.get('SUNYEDO_RESULTS_DIR')
        if output:
            p = Path(output); p.mkdir(parents=True, exist_ok=True)
            (p / (self.name + '.json')).write_text(json.dumps(result, indent=2, ensure_ascii=False) + '\n')
        print(f'{self.name}: {result["passed"]}/{result["total"]} passed')
        if failures:
            raise SystemExit(1)
        return result

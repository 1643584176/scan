# -*- coding: utf-8 -*-
"""Pull Matomo security advisories from GitHub Advisory DB + repo advisories."""
import json
import time
import urllib.request

def get(url):
    req = urllib.request.Request(url, headers={
        'User-Agent': 'h1kit/1.0',
        'Accept': 'application/vnd.github+json'})
    with urllib.request.urlopen(req, timeout=30) as r:
        return json.load(r)

try:
    advs = get('https://api.github.com/repos/matomo-org/matomo/security-advisories?per_page=50')
    print('== repo security advisories (%d) ==' % len(advs))
    for a in advs:
        print('-', a.get('ghsa_id'), a.get('cve_id'), '|', (a.get('severity') or ''),
              '|', (a.get('summary') or '')[:90])
        for v in (a.get('vulnerabilities') or []):
            print('    pkg:', (v.get('package') or {}).get('name'),
                  '| range:', (v.get('vulnerable_version_range') or ''),
                  '| patched:', (v.get('first_patched_version') or {}).get('identifier') or '-')
except Exception as e:
    print('repo advisories FAIL:', type(e).__name__, e)

time.sleep(2)
try:
    r = get('https://api.github.com/search/advisories?q=matomo&per_page=100')
    print()
    print('== advisory DB search "matomo" (%d total) ==' % (r.get('total_count') or 0))
    for a in r.get('items') or []:
        print('-', a.get('ghsa_id'), a.get('cve_id'), '|', a.get('severity'),
              '|', (a.get('summary') or '')[:80])
except Exception as e:
    print('advisory search FAIL:', type(e).__name__, e)

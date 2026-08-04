"""Fetch ops.wolt.com SPA and extract JS bundles / API endpoints."""
import requests, re

H = {
    'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36',
    'X-HackerOne-Research': 'pccp',
}

# 1. Fetch the ops SPA page
print("=== 1. FETCH OPS SPA ===")
r = requests.get('https://ops.wolt.com/', headers=H, timeout=15)
html = r.text
print(f"  Status: {r.status_code}, Size: {len(html)} bytes")

# 2. Extract external JS/CSS references
print("\n=== 2. STATIC ASSETS ===")
scripts = set(re.findall(r'src="([^"]+)"', html))
links = set(re.findall(r'href="([^"]+)"', html))
for s in sorted(scripts | links):
    print(f"  {s}")

# 3. Extract inline JS / __NEXT_DATA__ / window.__env
print("\n=== 3. INLINE DATA ===")
for pat in [r'window\.__env[^<]{0,500}', r'__NEXT_DATA__[^<]{0,500}',
            r'window\.__INITIAL_STATE__[^<]{0,500}', r'window\.__PREFETCHED_STATE__[^<]{0,500}',
            r'buildId["\']\s*:\s*["\'][^"\']+', r'"assetPrefix"\s*:\s*"[^"]*"']:
    for m in re.finditer(pat, html, re.I):
        print(f"  [{pat[:40]}] {m.group()[:300]}")

# 4. Extract API paths from HTML (inline scripts might contain them)
print("\n=== 4. API URLS IN HTML ===")
api_urls = set(re.findall(r'(?:https?://[^"\'\\s]{5,200}?(?:api|graphql|v\d)[^"\'\\s]*)', html, re.I))
for u in sorted(api_urls)[:30]:
    print(f"  {u}")

# 5. Also check common API paths with POST + JSON body to see if they respond differently
print("\n=== 5. API POST PROBES ===")
import json
api_probes = [
    '/api/v1/graphql', '/graphql', '/api/v1/query',
    '/api/login', '/api/auth', '/api/session',
    '/api/v1/orders', '/api/v1/venues', '/api/v1/merchants',
]
for path in api_probes:
    for ct in ['application/json', 'application/graphql']:
        try:
            r2 = requests.post(f'https://ops.wolt.com{path}',
                              headers={**H, 'Content-Type': ct},
                              json={'query': '{ __typename }'} if 'json' in ct else None,
                              data='{ __typename }' if 'graphql' in ct else None,
                              timeout=10)
            if r2.status_code not in [200, 404]:
                print(f"  POST {path} ({ct}) -> {r2.status_code} | {r2.text[:200]}")
            elif r2.status_code == 200 and 'ops-tools-backend' not in r2.text:
                print(f"  POST {path} ({ct}) -> 200 NON-SPA: {r2.text[:200]}")
        except Exception as e:
            pass

print("\n=== DONE ===")

"""Probe ops-related APIs from JS extraction."""
import requests

H = {
    'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36',
    'X-HackerOne-Research': 'pccp',
}

def probe(url, method='GET', **kwargs):
    try:
        r = requests.request(method, url, headers=H, timeout=10, **kwargs)
        ct = r.headers.get('content-type', '')[:40]
        body = r.text[:200].replace('\n', ' ')
        return f"{r.status_code:>4} | {ct} | {body}"
    except Exception as e:
        return f" ERR | {e}"

# Key API endpoints from ops JS
key_paths = [
    '/v1/token',
    '/v1/dvcrud/dynamic-values',
    '/v1/dvcrud/runtime/update',
    '/v1/dvcrud/healthchecks/',
    '/v1/curie/analyses',
    '/v1/dvedge/evaluation/evaluate',
    '/v1/usersync/users',
    '/v1/usersync/groups/search',
    '/v1/notificationhub/subscription/create',
    '/v1/dvcrud/sigma',
    '/v1/dvcrud/templates',
    '/v1/dvcrud/storage/download-url',
]

print("=== OPS.WOLT.COM API PATHS (from JS) ===\n")
for path in key_paths:
    # GET
    r = probe(f'https://ops.wolt.com{path}')
    if '404' not in r and 'Not Found' not in r:
        print(f"  GET  {path:45s} -> {r}")
    # POST
    r2 = probe(f'https://ops.wolt.com{path}', method='POST', json={})
    if '404' not in r2 and 'Not Found' not in r2 and '200' in r2:
        print(f"  POST {path:45s} -> {r2}")

# Also try DoorDash gateway
print("\n=== DOORDASH UNIFIED GATEWAY ===")
gateway_paths = ['/', '/v1/', '/health', '/v1/token', '/v1/dvcrud/']
for host in ['https://unified-gateway.doordash.com', 'https://unified-gateway.dashapi.com']:
    print(f"\n  {host}:")
    for path in gateway_paths:
        r = probe(f'{host}{path}')
        if 'ERR' not in r:
            print(f"    {path:20s} -> {r}")

# Try ops.doordash.com
print("\n=== OPS.DOORDASH.COM ===")
for path in ['/', '/login', '/api/', '/health']:
    r = probe(f'https://ops.doordash.com{path}')
    if 'ERR' not in r:
        print(f"  {path:20s} -> {r}")

# NEW VECTOR: Try Wolt's admin/management API
print("\n=== WOLT MANAGEMENT API ===")
for host in ['https://api.wolt.com', 'https://admin.wolt.com', 'https://management.wolt.com']:
    r = probe(f'{host}/')
    print(f"  {host:45s} -> {r}")

# NEW VECTOR: wolt.com legacy API paths
print("\n=== WOLT.COM LEGACY API ===")
legacy = ['/api/', '/api/v1/', '/api/v2/', '/graphql', '/rest/', '/.well-known/',
          '/api/health', '/api/status', '/api/config', '/api/env']
for path in legacy:
    r = probe(f'https://wolt.com{path}')
    if '404' not in r and '200' in r:
        print(f"  {path:25s} -> {r}")

print("\n=== DONE ===")

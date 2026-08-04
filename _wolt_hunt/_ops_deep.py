"""Deep probe of ops.wolt.com."""
import requests

H = {
    'User-Agent': 'Mozilla/5.0',
    'Origin': 'https://wolt.com',
    'X-HackerOne-Research': 'pccp',
}

def probe(url, method='GET', **kwargs):
    try:
        r = requests.request(method, url, headers=H, timeout=10, allow_redirects=False, **kwargs)
        ct = r.headers.get('content-type', '')[:50]
        body = r.text[:250]
        return f"{r.status_code} | {ct} | {body}"
    except Exception as e:
        return f"ERR: {e}"

BASE = 'https://ops.wolt.com'

print("=== OPS.WOLT.COM DEEP PROBE ===\n")

# 1. Known ops pages from domain assets
print("=== 1. KNOWN PAGES ===")
known_paths = [
    '/', '/login', '/api', '/graphql', '/admin',
    '/health', '/status', '/metrics', '/internal',
    '/swagger', '/docs', '/api-docs', '/openapi.json',
    '/.env', '/config', '/debug',
]
for p in known_paths:
    r = probe(BASE + p)
    if '404' not in r and 'ERR' not in r:
        print(f"  {p:25s} -> {r}")

# 2. API enumeration
print("\n=== 2. API PATHS ===")
api_paths = [
    '/api/', '/api/v1/', '/api/v2/',
    '/api/health', '/api/status', '/api/metrics',
    '/api/venues', '/api/orders', '/api/users',
    '/api/merchants', '/api/deliveries', '/api/analytics',
    '/api/internal/', '/api/admin/', '/api/ops/',
    '/v1/', '/v2/', '/v3/',
    '/graphql', '/playground',
]
for p in api_paths:
    r = probe(BASE + p)
    if '404' not in r and 'ERR' not in r:
        print(f"  {p:25s} -> {r}")

# 3. Ops-specific endpoints (from env config)
print("\n=== 3. OPS-SPECIFIC ===")
ops_endpoints = [
    '/api/v1/orders/search',
    '/api/v1/venues/manage',
    '/api/v1/merchants/list',
    '/api/v1/couriers/status',
    '/api/v1/support/tickets',
    '/api/v1/analytics/dashboard',
    '/api/v1/config',
    '/api/v1/feature-flags',
    '/_ah/health',
    '/readyz', '/livez',
]
for p in ops_endpoints:
    r = probe(BASE + p)
    if '404' not in r and 'ERR' not in r:
        print(f"  {p:35s} -> {r}")

# 4. Subdomain takeovers / CNAME
print("\n=== 4. HTTP METHODS ===")
for method in ['POST', 'PUT', 'DELETE', 'PATCH', 'OPTIONS']:
    r = probe(BASE + '/', method=method)
    print(f"  {method:8s} / -> {r}")

# 5. Check for open redirects
print("\n=== 5. OPEN REDIRECT ===")
import urllib.parse
redirect_payloads = [
    '?redirect=https://evil.com',
    '?next=https://evil.com',
    '?return=https://evil.com',
    '?return_to=https://evil.com',
    '?continue=https://evil.com',
    '?url=https://evil.com',
]
for pl in redirect_payloads:
    r = probe(BASE + '/' + pl)
    if 'evil.com' in r.lower():
        print(f"  {pl[:40]} -> REDIRECT FOUND: {r[:150]}")

print("\n=== DONE ===")

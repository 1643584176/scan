"""DoorDash recon v2: bypass WAF, probe API endpoints."""
import requests, re, json, os

# Try multiple UA to bypass WAF
H1 = {
    'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/131.0.0.0 Safari/537.36',
    'Accept-Language': 'en-US,en;q=0.9',
    'Accept': 'text/html,application/xhtml+xml,application/xml;q=0.9,*/*;q=0.8',
}
H2 = {**H1, 'User-Agent': 'Mozilla/5.0 (Linux; Android 14) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/131.0.6778.135 Mobile Safari/537.36'}
H3 = {
    'User-Agent': 'python-requests/2.31.0',
}

BASE = 'https://www.doordash.com'

# Try to fetch homepage with mobile UA
print("=== 1. HOMEPAGE WITH DIFFERENT UA ===")
for label, h in [('desktop', H1), ('mobile', H2), ('python', H3)]:
    r = requests.get(BASE + '/', headers=h, timeout=15)
    print(f"  {label:10s} -> {r.status_code} | {len(r.text)} bytes | {r.text[:80].replace(chr(10),' ')}")

# 2. Follow the API redirects
print("\n=== 2. API ENDPOINT PROBE ===")
api_paths = [
    '/v1/stores/', '/en-US/v1/stores/',
    '/v1/search/', '/en-US/v1/search/',
    '/v1/stores/search/', '/en-US/v1/stores/search/',
    '/v1/menus/', '/en-US/v1/menus/',
    '/v1/store/', '/en-US/v1/store/',
    '/v1/consumer/', '/en-US/v1/consumer/',
    '/v1/cart/', '/en-US/v1/cart/',
    '/v1/checkout/', '/en-US/v1/checkout/',
    '/v1/order/', '/en-US/v1/order/',
    '/v1/auth/', '/en-US/v1/auth/',
    '/v1/address/', '/en-US/v1/address/',
]

for path in api_paths:
    for h in [H1, H2]:
        try:
            r = requests.get(BASE + path, headers=h, timeout=10, allow_redirects=False)
            if r.status_code != 404:
                ct = r.headers.get('content-type', '')[:50]
                j = r.json() if 'json' in ct else None
                summary = str(j)[:200] if j else r.text[:120].replace('\n', ' ')
                print(f"  GET {path:35s} -> {r.status_code} | {summary}")
                break
        except:
            pass

# 3. Try POST to key endpoints
print("\n=== 3. POST TO ENDPOINTS ===")
post_tests = [
    ('/v1/stores/search/', {'lat': 37.7749, 'lng': -122.4194}),
    ('/en-US/v1/stores/search/', {'lat': 37.7749, 'lng': -122.4194}),
    ('/v1/search/', {'query': 'pizza'}),
    ('/en-US/v1/search/', {'query': 'pizza'}),
    ('/graphql', {'query': '{ __typename }'}),
    ('/en-US/graphql', {'query': '{ __typename }'}),
]
for path, body in post_tests:
    for h in [H1, H2]:
        try:
            r = requests.post(BASE + path, headers={**h, 'Content-Type': 'application/json'},
                            json=body, timeout=10, allow_redirects=False)
            if r.status_code != 404:
                ct = r.headers.get('content-type', '')[:40]
                summary = (r.json() if 'json' in ct else r.text[:150])
                print(f"  POST {path:40s} -> {r.status_code} | {str(summary)[:200]}")
                break
        except:
            pass

# 4. Check what /en-US/ redirect resolves to
print("\n=== 4. FOLLOW REDIRECTS ===")
for path in ['/v1/stores/', '/v1/search/', '/v1/stores/search/']:
    r = requests.get(BASE + path, headers=H1, timeout=10, allow_redirects=True)
    ct = r.headers.get('content-type', '')[:50]
    print(f"  GET {path} -> {r.status_code} | final URL: {r.url} | {r.text[:150].replace(chr(10),' ')}")

print("\n=== DONE ===")

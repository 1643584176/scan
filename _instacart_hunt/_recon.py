"""Instacart initial recon: fetch homepage, extract SSR/JS/API endpoints."""
import requests, re, json, os, base64

H = {
    'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/126.0.0.0 Safari/537.36',
    'Accept-Language': 'en-US,en;q=0.9',
}

os.makedirs('D:/scan/_instacart_hunt', exist_ok=True)
os.makedirs('D:/scan/_instacart_hunt/js', exist_ok=True)

TARGETS = {
    'www': 'https://www.instacart.com',
    'api': 'https://api.instacart.com',
    'shoppers': 'https://shoppers.instacart.com',
}

for label, base in TARGETS.items():
    print(f"\n{'='*60}")
    print(f"=== {label.upper()}: {base} ===")
    print(f"{'='*60}")
    
    # 1. Fetch homepage
    try:
        r = requests.get(base + '/', headers=H, timeout=30, allow_redirects=True)
        html = r.text
        print(f"  Status: {r.status_code}, Size: {len(html)} bytes, Final URL: {r.url}")
        
        if r.status_code == 200:
            with open(f'D:/scan/_instacart_hunt/{label}_homepage.html', 'w', encoding='utf-8') as f:
                f.write(html)
        else:
            print(f"  Body preview: {html[:200]}")
            continue
    except Exception as e:
        print(f"  ERR: {e}")
        continue

    # 2. Extract SSR data (Next.js, Apollo, etc.)
    print("\n  --- SSR / INLINE DATA ---")
    patterns = [
        ('__NEXT_DATA__', r'__NEXT_DATA__\s*=\s*({[^<]{200,50000}?})\s*<'),
        ('window.__NUXT__', r'window\.__NUXT__\s*=\s*({[^<]+?})'),
        ('window.__INITIAL_STATE__', r'window\.__INITIAL_STATE__\s*=\s*({[^<]+?})'),
        ('window.__PREFETCHED', r'window\.__PREFETCHED[^=]*=\s*({[^<]+?})'),
        ('window.__APOLLO', r'window\.__APOLLO[^=]*=\s*({[^<]+?})'),
        ('window.__REDUX', r'window\.__REDUX[^=]*=\s*({[^<]+?})'),
        ('window.__data', r'window\.__data\s*=\s*({[^<]+?})'),
        ('json_script', r'<script[^>]*type="application/json"[^>]*id="([^"]*)"[^>]*>([^<]{200,10000})</script>'),
        ('base64', r'atob\([\'"]([A-Za-z0-9+/=]{100,5000})[\'"]'),
    ]
    for pat_name, pat in patterns:
        for m in re.finditer(pat, html, re.I | re.DOTALL):
            if pat_name == 'json_script':
                val = m.group(2)[:2000]
                print(f"\n  [{pat_name}] id={m.group(1)} ({len(m.group(2))} chars)")
            else:
                val = m.group(1)[:2000]
                print(f"\n  [{pat_name}] ({len(m.group(1))} chars)")
            print(f"    {val[:500]}")
            if pat_name == 'base64':
                try:
                    decoded = base64.b64decode(m.group(1)).decode('utf-8', errors='replace')[:300]
                    print(f"    DECODED: {decoded}")
                except:
                    pass

    # 3. Extract JS bundle URLs
    print("\n  --- JS BUNDLES ---")
    js_urls = set()
    for m in re.finditer(r'<script[^>]*src="([^"]+)"', html, re.I):
        js_urls.add(m.group(1))
    for m in re.finditer(r'(/_next/static/[^"\'\s]+\.js)', html):
        js_urls.add(base + m.group(1))
    # Also find webpack chunks
    for m in re.finditer(r'(/static/(?:js|chunks)/[^"\'\s]+\.js)', html):
        js_urls.add(base + m.group(1))
    
    print(f"  Found {len(js_urls)} JS URLs")
    for u in sorted(js_urls)[:25]:
        print(f"    {u}")

    # 4. Extract hostnames
    print("\n  --- INTERESTING HOSTS ---")
    hosts = set()
    for m in re.finditer(r'https?://([a-zA-Z0-9][-a-zA-Z0-9]*(?:\.[a-zA-Z0-9][-a-zA-Z0-9]*)+)', html):
        hosts.add(m.group(1))
    for h in sorted(hosts):
        if any(kw in h.lower() for kw in ['instacart', 'api', 'graphql', 'cdn', 'static', 'assets']):
            print(f"    {h}")

    # 5. API endpoint extraction from HTML
    print("\n  --- API ENDPOINTS IN HTML ---")
    api_urls = set()
    for m in re.finditer(r'(/v\d+/[a-zA-Z0-9_/-]+|/api/[a-zA-Z0-9_/-]+|/graphql[a-zA-Z0-9_/-]*)', html):
        api_urls.add(m.group(1))
    for u in sorted(api_urls)[:30]:
        print(f"    {u}")

# 6. Direct API probing
print(f"\n{'='*60}")
print("=== DIRECT API PROBING ===")
api_probes = [
    # Instacart consumer API
    ('api.instacart.com', '/v1/', 'GET'),
    ('api.instacart.com', '/v2/', 'GET'),
    ('api.instacart.com', '/graphql', 'GET'),
    ('api.instacart.com', '/api/', 'GET'),
    ('api.instacart.com', '/v1/stores/', 'GET'),
    ('api.instacart.com', '/v1/search/', 'GET'),
    ('www.instacart.com', '/v1/', 'GET'),
    ('www.instacart.com', '/v2/', 'GET'),
    ('www.instacart.com', '/graphql', 'GET'),
    ('www.instacart.com', '/api/', 'GET'),
    ('www.instacart.com', '/api/v1/', 'GET'),
    ('www.instacart.com', '/api/v2/', 'GET'),
]

for host, path, method in api_probes:
    url = f'https://{host}{path}'
    try:
        if method == 'GET':
            r = requests.get(url, headers=H, timeout=10, allow_redirects=False)
        ct = r.headers.get('content-type', '')[:50]
        body_preview = r.text[:200].replace('\n', ' ')
        print(f"  {method:4s} {url:50s} -> {r.status_code:3d} | {body_preview[:150]}")
    except Exception as e:
        print(f"  {method:4s} {url:50s} -> ERR: {str(e)[:80]}")

# 7. Shoppers portal probe
print(f"\n{'='*60}")
print("=== SHOPPERS PORTAL ===")
for path in ['/', '/api/', '/graphql', '/login', '/v1/']:
    url = f'https://shoppers.instacart.com{path}'
    try:
        r = requests.get(url, headers=H, timeout=10, allow_redirects=False)
        print(f"  GET {url:50s} -> {r.status_code} | {r.text[:120].replace(chr(10),' ')}")
    except Exception as e:
        print(f"  GET {url:50s} -> ERR: {str(e)[:80]}")

# 8. instacart.tools probe
print(f"\n{'='*60}")
print("=== INSTACART.TOOLS ===")
for sub in ['api', 'admin', 'internal', 'dev', 'staging']:
    url = f'https://{sub}.instacart.tools/'
    try:
        r = requests.get(url, headers=H, timeout=8, allow_redirects=False)
        print(f"  {url:50s} -> {r.status_code} | {r.text[:100].replace(chr(10),' ')}")
    except Exception as e:
        print(f"  {url:50s} -> ERR: {str(e)[:60]}")

print("\n=== DONE ===")

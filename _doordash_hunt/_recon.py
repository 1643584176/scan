"""DoorDash initial recon: fetch homepage, extract SSR data and API endpoints."""
import requests, re, json, os, base64

H = {
    'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/126.0.0.0 Safari/537.36',
    'Accept-Language': 'en-US,en;q=0.9',
}

os.makedirs('D:/scan/_doordash_hunt', exist_ok=True)
os.makedirs('D:/scan/_doordash_hunt/js', exist_ok=True)

BASE = 'https://www.doordash.com'

# 1. Fetch homepage
print("=== 1. HOMEPAGE ===")
r = requests.get(BASE + '/', headers=H, timeout=30)
html = r.text
print(f"  Status: {r.status_code}, Size: {len(html)} bytes")
with open('D:/scan/_doordash_hunt/homepage.html', 'w', encoding='utf-8') as f:
    f.write(html)

# 2. Extract SSR data
print("\n=== 2. SSR / INLINE DATA ===")
for pat_name, pat in [
    ('__NEXT_DATA__', r'__NEXT_DATA__\s*=\s*({[^<]{100,2000}}?})\s*<'),
    ('window.__env', r'window\.__env\s*=\s*({[^<]+?})'),
    ('window.__INITIAL', r'window\.__INITIAL[^=]*=\s*({[^<]+?})'),
    ('window.__PREFETCHED', r'window\.__PREFETCHED[^=]*=\s*({[^<]+?})'),
    ('window.__APOLLO', r'window\.__APOLLO[^=]*=\s*({[^<]+?})'),
    ('base64 env', r'atob\([\'"]([A-Za-z0-9+/=]{100,2000})[\'"]'),
    ('json_script', r'<script[^>]*type="application/json"[^>]*>([^<]{200,3000})</script>'),
]:
    for m in re.finditer(pat, html, re.I | re.DOTALL):
        val = m.group(1)[:1500]
        try:
            decoded = base64.b64decode(val).decode('utf-8', errors='replace')[:500] if pat_name == 'base64 env' else None
        except:
            decoded = None
        print(f"\n  [{pat_name}] ({len(val)} chars)")
        print(f"    {val[:400]}")
        if decoded:
            print(f"    DECODED: {decoded[:300]}")

# 3. Extract JS bundle URLs
print("\n=== 3. JS BUNDLES ===")
js_urls = set()
for m in re.finditer(r'<script[^>]*src="([^"]+\.js[^"]*)"', html, re.I):
    js_urls.add(m.group(1))
for m in re.finditer(r'<link[^>]*href="([^"]+\.js[^"]*)"', html, re.I):
    js_urls.add(m.group(1))
# Also find _next/static chunks
for m in re.finditer(r'(/_next/static/[^"\'\s]+\.js)', html):
    js_urls.add('https://www.doordash.com' + m.group(1))

print(f"  Found {len(js_urls)} JS URLs")
for u in sorted(js_urls)[:30]:
    print(f"    {u}")

# 4. Extract all hostnames from HTML
print("\n=== 4. HOSTS IN HTML ===")
hosts = set()
for m in re.finditer(r'https?://([a-zA-Z0-9][-a-zA-Z0-9]*(?:\.[a-zA-Z0-9][-a-zA-Z0-9]*)+)', html):
    hosts.add(m.group(1))
for h in sorted(hosts)[:30]:
    if 'doordash' in h.lower() or 'dash' in h.lower():
        print(f"    {h}")

# 5. Quick API endpoint probe
print("\n=== 5. QUICK API PROBE ===")
api_probes = [
    '/api/', '/graphql', '/api/v1/', '/api/v2/',
    '/v1/stores/', '/v1/search/', '/v1/menus/',
    '/api/v1/stores', '/api/v1/search',
]
for path in api_probes:
    try:
        r2 = requests.get(BASE + path, headers=H, timeout=10, allow_redirects=False)
        ct = r2.headers.get('content-type', '')[:40]
        body = r2.text[:200]
        if r2.status_code != 200 or 'html' not in ct.lower():
            print(f"  GET {path:25s} -> {r2.status_code} | {ct} | {body[:120]}")
    except:
        pass

# 6. Also try common food ordering paths
print("\n=== 6. FOOD ORDERING PATHS ===")
food_paths = [
    '/store/', '/stores/', '/search', '/food/', 
    '/restaurant/', '/cuisine/', '/category/',
    '/menu/', '/checkout', '/cart', '/order/',
    '/en-US/store/', '/en-US/search/',
]
for path in food_paths:
    try:
        r2 = requests.get(BASE + path, headers=H, timeout=10, allow_redirects=False)
        if r2.status_code in [200, 301, 302, 307, 308]:
            loc = r2.headers.get('location', '')
            print(f"  GET {path:25s} -> {r2.status_code} | {loc[:80]}")
    except:
        pass

print("\n=== DONE ===")

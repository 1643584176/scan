"""Probe Foodpanda, Glovo, Delivery Hero consumer sites directly."""
import requests, re, json, os

H = {
    'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/126.0.0.0 Safari/537.36',
    'Accept-Language': 'en-US,en;q=0.9',
}

os.makedirs('D:/scan/_foodpanda_hunt', exist_ok=True)

TARGETS = [
    # Foodpanda - multiple country domains
    ('foodpanda.com', 'https://www.foodpanda.com'),
    ('foodpanda.de', 'https://www.foodpanda.de'),
    ('foodpanda.sg', 'https://www.foodpanda.sg'),
    ('foodpanda.tw', 'https://www.foodpanda.tw'),
    ('foodpanda.ph', 'https://www.foodpanda.ph'),
    ('foodpanda.bd', 'https://www.foodpanda.com.bd'),
    ('foodpanda.pk', 'https://www.foodpanda.pk'),
    # Glovo
    ('glovoapp.com', 'https://glovoapp.com'),
    # Delivery Hero corporate
    ('deliveryhero.com', 'https://www.deliveryhero.com'),
]

for label, base in TARGETS:
    print(f"\n{'='*60}")
    print(f"=== {label}: {base} ===")
    
    # 1. Homepage
    try:
        r = requests.get(base + '/', headers=H, timeout=15, allow_redirects=True)
        html = r.text
        print(f"  Status: {r.status_code}, Size: {len(html)} bytes, Final: {r.url}")
        
        if 'Just a moment' in html[:200] or 'cf-browser-verify' in html:
            print(f"  !! Cloudflare blocked!")
            continue
    except Exception as e:
        print(f"  ERR: {e}")
        continue

    # 2. SSR data
    for pat_name, pat in [
        ('__NEXT_DATA__', r'__NEXT_DATA__\s*=\s*({[^<]{200,10000}?})\s*<'),
        ('__NUXT__', r'window\.__NUXT__\s*=\s*({[^<]+?})'),
        ('__INITIAL__', r'window\.__INITIAL[^=]*=\s*({[^<]+?})'),
        ('window.__data', r'window\.__data\s*=\s*({[^<]+?})'),
        ('json_script', r'<script[^>]*type="application/json"[^>]*>([^<]{200,5000})</script>'),
    ]:
        for m in re.finditer(pat, html, re.I | re.DOTALL):
            val = m.group(1)[:600]
            print(f"  [{pat_name}] ({len(m.group(1))} chars): {val[:200]}")

    # 3. JS frameworks
    frameworks = []
    if 'next' in html.lower() or '__next' in html or '__NEXT_DATA__' in html:
        frameworks.append('Next.js')
    if 'nuxt' in html.lower() or '__NUXT__' in html:
        frameworks.append('Nuxt.js')
    if 'vue' in html.lower():
        frameworks.append('Vue.js')
    if 'react' in html.lower() or 'data-reactroot' in html:
        frameworks.append('React')
    if 'angular' in html.lower() or 'ng-version' in html:
        frameworks.append('Angular')
    if frameworks:
        print(f"  Frameworks: {', '.join(frameworks)}")

    # 4. JS bundles
    js_urls = set()
    for m in re.finditer(r'<script[^>]*src="([^"]+)"', html, re.I):
        js_urls.add(m.group(1))
    for m in re.finditer(r'(/_next/static/[^"\'\s]+\.js)', html):
        js_urls.add(base + m.group(1))
    print(f"  JS bundles: {len(js_urls)}")
    for u in sorted(js_urls)[:10]:
        print(f"    {u}")

    # 5. API endpoints in HTML
    api_paths = set()
    for m in re.finditer(r'(/[a-z0-9_-]+/[a-z0-9_/.-]{3,60})', html):
        path = m.group(1)
        if any(kw in path.lower() for kw in ['api', 'v1/', 'v2/', 'v3/', 'graphql', 'order', 'search', 'store', 'restaurant', 'checkout', 'menu']):
            api_paths.add(path)
    
    if api_paths:
        print(f"  API paths: {len(api_paths)}")
        for p in sorted(api_paths)[:20]:
            print(f"    {p}")

    # 6. Quick API probe
    for path in ['/api/', '/api/v1/', '/api/v2/', '/graphql', '/v1/', '/v2/', '/.well-known/']:
        try:
            r2 = requests.get(base + path, headers=H, timeout=8, allow_redirects=False)
            ct = r2.headers.get('content-type', '')[:40]
            if r2.status_code not in [404]:
                body = r2.text[:150].replace('\n', ' ')
                print(f"  GET {path:20s} -> {r2.status_code:3d} | {ct} | {body[:100]}")
        except:
            pass

# ===== Foodpanda API domain probe =====
print(f"\n{'='*60}")
print("=== FOODPANDA API DOMAINS ===")

api_domains = [
    'https://api.foodpanda.com/',
    'https://api.foodpanda.de/',
    'https://api.foodpanda.sg/',
    'https://disco-api.foodpanda.com/',
    'https://cw-api.foodpanda.com/',
    'https://glovoapp.com/api/',
    'https://api.glovoapp.com/',
]

for url in api_domains:
    try:
        r = requests.get(url, headers=H, timeout=8, allow_redirects=False)
        print(f"  {url:50s} -> {r.status_code:3d} | {r.text[:100].replace(chr(10),' ')}")
    except Exception as e:
        print(f"  {url:50s} -> ERR: {str(e)[:60]}")

print("\n=== DONE ===")

"""Deep recon: Rappi, Postmates, Gojek - JS extraction + API probing."""
import requests, re, json, os
from concurrent.futures import ThreadPoolExecutor, as_completed

H = {
    'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/126.0.0.0 Safari/537.36',
    'Accept-Language': 'en-US,en;q=0.9',
    'Accept': 'text/html,application/xhtml+xml,application/xml;q=0.9,*/*;q=0.8',
}

TARGETS = [
    ('rappi', 'https://www.rappi.com'),
    ('postmates', 'https://postmates.com'),
    ('gojek', 'https://www.gojek.com'),
    ('zomato', 'https://www.zomato.com'),
]

for label, base in TARGETS:
    out_dir = f'D:/scan/_new_targets/{label}'
    os.makedirs(out_dir, exist_ok=True)
    
    print(f"\n{'='*70}")
    print(f"=== {label.upper()}: {base} ===")
    
    # 1. Fetch homepage
    try:
        r = requests.get(base + '/', headers=H, timeout=20, allow_redirects=True)
        html = r.text
        final_url = r.url
        print(f"  Homepage: {r.status_code}, {len(html)} bytes -> {final_url}")
        with open(f'{out_dir}/homepage.html', 'w', encoding='utf-8') as f:
            f.write(html)
    except Exception as e:
        print(f"  Homepage ERR: {e}")
        continue
    
    # 2. SSR data
    print(f"\n  --- SSR DATA ---")
    for pat_name, pat in [
        ('__NEXT_DATA__', r'__NEXT_DATA__\s*=\s*({.+?});?\s*</script>'),
        ('__NUXT__', r'window\.__NUXT__\s*=\s*({.+?});'),
        ('window.__data', r'window\.__data\s*=\s*({.+?});'),
        ('window.__INITIAL_STATE__', r'window\.__INITIAL_STATE__\s*=\s*({.+?});'),
        ('window.__PRELOADED_STATE__', r'window\.__PRELOADED_STATE__\s*=\s*({.+?});'),
        ('json_script', r'<script[^>]*type="application/json"[^>]*id="([^"]*)"[^>]*>([^<]{100,})</script>'),
    ]:
        for m in re.finditer(pat, html, re.I | re.DOTALL):
            if pat_name == 'json_script':
                val = m.group(2)[:2000]
                print(f"  [{pat_name}] id={m.group(1)} ({len(m.group(2))} chars)")
            else:
                val = m.group(1)[:2000]
                print(f"  [{pat_name}] ({len(m.group(1))} chars)")
            
            # Try to parse JSON and extract keys
            try:
                data = json.loads(val if pat_name != 'json_script' else m.group(2))
                if isinstance(data, dict):
                    keys = list(data.keys())[:30]
                    print(f"    Top keys: {keys}")
            except:
                pass
    
    # 3. JS Bundle collection
    print(f"\n  --- JS BUNDLES ---")
    js_urls = set()
    for m in re.finditer(r'<script[^>]*src="([^"]+\.js[^"]*)"', html, re.I):
        js_urls.add(m.group(1))
    for m in re.finditer(r'(/_next/static/[^"\'\s]+\.js)', html):
        js_urls.add(base.rstrip('/') + m.group(1) if m.group(1).startswith('/') else m.group(1))
    
    # Also find webpack chunks in inline code
    for m in re.finditer(r'["\']([^"\']+\.js)["\']', html):
        url = m.group(1)
        if any(kw in url for kw in ['chunk', 'bundle', 'main', 'runtime', 'vendor']):
            if url.startswith('//'):
                url = 'https:' + url
            elif url.startswith('/'):
                url = base.rstrip('/') + url
            js_urls.add(url)
    
    print(f"  Total unique JS URLs: {len(js_urls)}")
    
    # Download key bundles (runtime, main, chunks with api/graphql related names)
    key_bundles = []
    for url in sorted(js_urls):
        fn = url.split('/')[-1].split('?')[0]
        # Prioritize runtime, main, vendor, or anything with api/gql keywords
        priority = 0
        if any(kw in fn.lower() for kw in ['runtime', 'webpack', 'main', 'vendor', 'framework']):
            priority = 3
        elif any(kw in fn.lower() for kw in ['app', 'pages', 'layout']):
            priority = 2
        elif any(kw in url.lower() for kw in ['chunk', 'bundle']):
            priority = 1
        key_bundles.append((priority, url, fn))
    
    key_bundles.sort(key=lambda x: -x[0])
    
    # Download top 20 bundles
    downloaded = 0
    for _, url, fn in key_bundles[:20]:
        if downloaded >= 15:
            break
        try:
            if not url.startswith('http'):
                url = base.rstrip('/') + url if url.startswith('/') else 'https:' + url
            r2 = requests.get(url, headers=H, timeout=15)
            if r2.status_code == 200 and len(r2.text) > 100:
                safe_fn = fn[:80]
                with open(f'{out_dir}/{safe_fn}', 'w', encoding='utf-8', errors='replace') as f:
                    f.write(r2.text)
                print(f"    DOWNLOADED: {safe_fn} ({len(r2.text)} chars)")
                downloaded += 1
        except Exception as e:
            pass
    
    # 4. API endpoint search in HTML
    print(f"\n  --- API ENDPOINTS IN HTML ---")
    api_endpoints = set()
    for m in re.finditer(r'https?://[a-zA-Z0-9][-a-zA-Z0-9]*(?:\.[a-zA-Z0-9][-a-zA-Z0-9]*)+/[a-zA-Z0-9_/.-]{3,80}', html):
        url = m.group(0)
        if any(kw in url.lower() for kw in ['api', 'graphql', 'v1/', 'v2/', 'v3/', 'v4/', 'gql', 'rest']):
            api_endpoints.add(url)
    
    # Also relative paths
    for m in re.finditer(r'["\'\`](/[a-zA-Z0-9_/.-]{4,80})["\'\`]', html):
        path = m.group(1)
        if any(kw in path.lower() for kw in ['api', 'graphql', 'v1/', 'v2/', 'v3/', 'v4/', 'gql']):
            api_endpoints.add(base.rstrip('/') + path)
    
    print(f"  Found {len(api_endpoints)} API endpoints")
    for ep in sorted(api_endpoints)[:20]:
        print(f"    {ep}")
    
    # 5. GraphQL probe
    print(f"\n  --- GRAPHQL PROBE ---")
    gql_paths = ['/graphql', '/api/graphql', '/gql', '/v1/graphql', '/v2/graphql', '/query']
    for path in gql_paths:
        try:
            r3 = requests.get(base + path, headers=H, timeout=8, allow_redirects=False)
            ct = str(r3.headers.get('content-type', ''))[:60]
            if r3.status_code in [200, 400, 405] or 'graphql' in ct.lower() or 'json' in ct.lower():
                body = r3.text[:300].replace('\n', ' ')
                print(f"  GET  {path:20s} -> {r3.status_code:3d} | {ct} | {body[:150]}")
        except:
            pass
    
    # 6. Common API paths probe
    print(f"\n  --- API PATH PROBE ---")
    api_paths = [
        '/api/', '/api/v1/', '/api/v2/', '/api/v3/', '/api/v4/',
        '/v1/', '/v2/', '/v3/', '/v4/',
        '/rest/', '/rest/v1/', '/rest/v2/',
        '/.well-known/', '/health', '/status', '/version',
        '/swagger', '/docs', '/openapi.json', '/api-docs',
    ]
    for path in api_paths:
        try:
            r4 = requests.get(base + path, headers=H, timeout=8, allow_redirects=False)
            ct = str(r4.headers.get('content-type', ''))[:50]
            if r4.status_code not in [404]:
                body = r4.text[:120].replace('\n', ' ').replace('\r', '')
                print(f"  GET  {path:20s} -> {r4.status_code:3d} | {ct} | {body[:100]}")
        except:
            pass
    
    # 7. For Rappi - try country subdomains
    if label == 'rappi':
        print(f"\n  --- RAPPI API DOMAINS ---")
        for domain in [
            'https://api.rappi.com/', 'https://api.rappi.com.mx/', 'https://api.rappi.com.ar/',
            'https://services.rappi.com/', 'https://www.rappi.com/api/',
            'https://restaurants.rappi.com/', 'https://gql.rappi.com/',
        ]:
            try:
                r5 = requests.get(domain, headers=H, timeout=8, allow_redirects=False)
                ct = str(r5.headers.get('content-type', ''))[:60]
                body = r5.text[:120].replace('\n', ' ').replace('\r', '')
                print(f"  {domain:45s} -> {r5.status_code:3d} | {ct} | {body[:100]}")
            except Exception as e:
                print(f"  {domain:45s} -> ERR: {str(e)[:60]}")
    
    # 8. For Postmates - try related domains
    if label == 'postmates':
        print(f"\n  --- POSTMATES API DOMAINS ---")
        for domain in [
            'https://api.postmates.com/', 'https://api.ubereats.com/',
            'https://www.ubereats.com/api/', 'https://www.ubereats.com/graphql',
        ]:
            try:
                r5 = requests.get(domain, headers=H, timeout=8, allow_redirects=False)
                ct = str(r5.headers.get('content-type', ''))[:60]
                body = r5.text[:120].replace('\n', ' ').replace('\r', '')
                print(f"  {domain:45s} -> {r5.status_code:3d} | {ct} | {body[:100]}")
            except Exception as e:
                print(f"  {domain:45s} -> ERR: {str(e)[:60]}")

print("\n\n=== ALL DONE ===")

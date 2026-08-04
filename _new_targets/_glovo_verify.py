"""Glovo vulnerability verification - JS analysis + API endpoint extraction."""
import requests, re, json, os
from urllib.parse import urljoin

H = {
    'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/126.0.0.0 Safari/537.36',
    'Accept-Language': 'en-US,en;q=0.9',
}

BASE = 'https://glovoapp.com'
OUT = 'D:/scan/_new_targets/glovo'
os.makedirs(OUT, exist_ok=True)

print("="*60)
print("=== GLOVO DEEP ANALYSIS ===")

# 1. Fetch homepage
r = requests.get(BASE + '/', headers=H, timeout=20, allow_redirects=True)
html = r.text
print(f"Homepage: {r.status_code}, {len(html)} bytes -> {r.url}")
with open(f'{OUT}/homepage.html', 'w', encoding='utf-8') as f:
    f.write(html)

# 2. SSR data (NEXT_DATA)
print(f"\n--- SSR DATA ---")
for pat_name, pat in [
    ('__NEXT_DATA__', r'__NEXT_DATA__\s*=\s*({.+?});?\s*</script>'),
    ('json_script', r'<script[^>]*type="application/json"[^>]*id="([^"]*)"[^>]*>([^<]{100,})</script>'),
]:
    for m in re.finditer(pat, html, re.I | re.DOTALL):
        if pat_name == 'json_script':
            val = m.group(2)
            print(f"  [{pat_name}] id={m.group(1)} ({len(val)} chars)")
        else:
            val = m.group(1)
            print(f"  [{pat_name}] ({len(val)} chars)")
        try:
            data = json.loads(val)
            if isinstance(data, dict):
                keys = list(data.keys())[:30]
                print(f"    Keys: {keys}")
                # Save
                with open(f'{OUT}/ssr_{pat_name}.json', 'w', encoding='utf-8') as f:
                    json.dump(data, f, indent=2, ensure_ascii=False)
        except:
            pass

# 3. Collect ALL JS bundles
print(f"\n--- JS BUNDLES ---")
js_urls = set()
for m in re.finditer(r'<script[^>]*src="([^"]+\.js[^"]*)"', html, re.I):
    url = m.group(1)
    if url.startswith('//'): url = 'https:' + url
    elif url.startswith('/'): url = BASE + url
    js_urls.add(url)
for m in re.finditer(r'(/_next/static/[^"\'\s]+\.js)', html):
    js_urls.add(BASE + m.group(1))
# Also find in inline chunks
for m in re.finditer(r'["\']([^"\']+\.js)["\']', html):
    url = m.group(1)
    if 'chunk' in url or 'static' in url:
        if url.startswith('//'): url = 'https:' + url
        elif url.startswith('/'): url = BASE + url
        js_urls.add(url)

print(f"  Total unique: {len(js_urls)}")

# Download ALL bundles (not just top N)
downloaded = 0
api_endpoints_found = set()
all_texts = []

for url in sorted(js_urls):
    fn = url.split('/')[-1].split('?')[0][:80]
    try:
        if not url.startswith('http'):
            url = urljoin(BASE, url)
        r2 = requests.get(url, headers=H, timeout=20)
        if r2.status_code == 200 and len(r2.text) > 100:
            with open(f'{OUT}/{fn}', 'w', encoding='utf-8', errors='replace') as f:
                f.write(r2.text)
            downloaded += 1
            all_texts.append(r2.text)
            
            # Search for API endpoints
            txt = r2.text
            # GraphQL operations
            for m in re.finditer(r'(?:query|mutation)\s+(\w+)', txt):
                api_endpoints_found.add(('gql_op', m.group(1)))
            # API URLs
            for m in re.finditer(r'https?://[a-zA-Z0-9][-a-zA-Z0-9]*(?:\.[a-zA-Z0-9][-a-zA-Z0-9]*)+/[a-zA-Z0-9_/.-]{3,80}', txt):
                url_found = m.group(0)
                if any(kw in url_found.lower() for kw in ['glovo', 'api', 'graphql', 'gql', 'v1/', 'v2/', 'v3/', 'v4/', 'auth']):
                    api_endpoints_found.add(('api_url', url_found))
            # Relative API paths
            for m in re.finditer(r'["\'\`](/[a-zA-Z0-9_/.-]{4,120})["\'\`]', txt):
                path = m.group(1)
                if any(kw in path.lower() for kw in ['api', 'graphql', 'gql', 'auth', 'order', 'basket', 'checkout']):
                    api_endpoints_found.add(('api_path', path))
    except:
        pass

print(f"  Downloaded: {downloaded} bundles")
print(f"  API endpoints found: {len(api_endpoints_found)}")
for typ, val in sorted(api_endpoints_found)[:40]:
    print(f"    [{typ}] {val}")

# 4. Combine all JS text and search for key patterns
print(f"\n--- CROSS-FILE SEARCH ---")
combined = '\n'.join(all_texts)

# Auth tokens / API keys
for pat_name, pat in [
    ('apiKey', r'apiKey["\s:=]+["\']([a-zA-Z0-9_-]+)["\']'),
    ('accessToken', r'(?:accessToken|access_token)["\s:=]+["\']([a-zA-Z0-9._-]+)["\']'),
    ('x-api-key', r'["\']x-api-key["\']'),
    ('authorization', r'["\']authorization["\']'),
    ('bearer', r'bearer\s+["\']([a-zA-Z0-9._-]+)["\']'),
    ('graphql_url', r'(https?://[^"\'\s]+graphql[^"\'\s]*)'),
    ('api_base', r'(?:apiBaseUrl|API_BASE|apiUrl|baseURL)["\s:=]+["\']([^"\']+)["\']'),
    ('apollo_client', r'(?:new ApolloClient|createHttpLink|ApolloClient)'),
]:
    matches = list(re.finditer(pat, combined, re.I))
    if matches:
        print(f"  [{pat_name}]: {len(matches)} matches")
        for m in matches[:5]:
            ctx = combined[max(0,m.start()-30):m.end()+50].replace('\n',' ')[:120]
            print(f"    {ctx}")

# 5. Probe API endpoints found
print(f"\n--- API PROBE ---")
# Follow redirects
for path in ['/api/', '/api/v1/', '/api/v2/', '/graphql', '/v1/', '/v2/']:
    try:
        r3 = requests.get(BASE + path, headers=H, timeout=10, allow_redirects=True)
        ct = str(r3.headers.get('content-type', ''))[:60]
        body = r3.text[:200].replace('\n', ' ')
        print(f"  GET  {path:20s} -> {r3.status_code:3d} | {r3.url[:60]} | {ct} | {body[:100]}")
    except Exception as e:
        print(f"  GET  {path:20s} -> ERR: {str(e)[:50]}")

# Try Glovo API domains
print(f"\n--- API DOMAINS ---")
for domain in [
    'https://api.glovoapp.com/', 'https://api.glovoapp.com/ping',
    'https://api.glovoapp.com/health',
    'https://glovoapp.com/api/', 'https://glovoapp.com/graphql',
    'https://orders.glovoapp.com/', 'https://couriers.glovoapp.com/',
]:
    try:
        r4 = requests.get(domain, headers=H, timeout=8, allow_redirects=False)
        ct = str(r4.headers.get('content-type', ''))[:60]
        body = r4.text[:120].replace('\n', ' ')
        print(f"  {domain:45s} -> {r4.status_code:3d} | {ct} | {body[:100]}")
    except Exception as e:
        print(f"  {domain:45s} -> ERR: {str(e)[:60]}")

# 6. CORS test on promising endpoints
print(f"\n--- CORS TEST ---")
for url in [
    'https://api.glovoapp.com/',
    'https://glovoapp.com/graphql',
]:
    try:
        r5 = requests.options(url, headers={
            **H, 'Origin': 'https://evil.com',
            'Access-Control-Request-Method': 'GET',
        }, timeout=8)
        acao = r5.headers.get('Access-Control-Allow-Origin', '')
        acac = r5.headers.get('Access-Control-Allow-Credentials', '')
        if acao:
            print(f"  OPTIONS {url:45s} -> ACAO={acao} | ACAC={acac}")
    except:
        pass

print(f"\n=== DONE ===")

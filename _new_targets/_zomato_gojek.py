"""Zomato API key hunting + Gojek deep recon."""
import requests, re, json, os

H = {
    'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/126.0.0.0 Safari/537.36',
    'Accept-Language': 'en-US,en;q=0.9',
}

os.makedirs('D:/scan/_new_targets/zomato', exist_ok=True)
os.makedirs('D:/scan/_new_targets/gojek', exist_ok=True)

# ===== ZOMATO =====
print("="*60)
print("=== ZOMATO ===")

# Fetch homepage
r = requests.get('https://www.zomato.com/', headers=H, timeout=20, allow_redirects=True)
html = r.text
print(f"Homepage: {r.status_code}, {len(html)} bytes -> {r.url}")

# Save HTML
with open('D:/scan/_new_targets/zomato/homepage.html', 'w', encoding='utf-8') as f:
    f.write(html)

# Search for API keys in HTML
print("\n--- API KEY SEARCH ---")
key_patterns = [
    r'api[_-]?key["\s:=]+["\']([a-zA-Z0-9_-]{10,80})["\']',
    r'["\']x-api-key["\'][^:]*:\s*["\']([a-zA-Z0-9_-]+)["\']',
    r'["\']zomato[^"\']{0,20}key[^"\']{0,10}["\']\s*:\s*["\']([^"\']+)["\']',
    r'user-key["\s:=]+["\']([a-zA-Z0-9]+)["\']',
    r'apiKey["\s:=]+["\']([a-zA-Z0-9_-]+)["\']',
    r'["\']apikey["\']\s*:\s*["\']([a-zA-Z0-9]+)["\']',
]

for pat in key_patterns:
    for m in re.finditer(pat, html, re.I):
        ctx = html[max(0,m.start()-50):m.end()+50].replace('\n',' ')
        print(f"  [{pat[:40]}]: {m.group(1)} | ctx: {ctx[:150]}")

# JS bundles
print("\n--- JS BUNDLES ---")
js_urls = set()
for m in re.finditer(r'<script[^>]*src="([^"]+)"', html, re.I):
    js_urls.add(m.group(1))
for m in re.finditer(r'(/_next/static/[^"\'\s]+\.js)', html):
    js_urls.add(m.group(1) if m.group(1).startswith('http') else 'https://www.zomato.com' + m.group(1))

print(f"  Total: {len(js_urls)}")
for u in sorted(js_urls)[:20]:
    print(f"    {u}")

# Download key bundles and search for API keys
downloaded = 0
for url in sorted(js_urls):
    if downloaded >= 8:
        break
    try:
        if not url.startswith('http'):
            url = 'https://www.zomato.com' + url if url.startswith('/') else url
        r2 = requests.get(url, headers=H, timeout=15)
        if r2.status_code == 200 and len(r2.text) > 500:
            fn = url.split('/')[-1].split('?')[0][:60]
            with open(f'D:/scan/_new_targets/zomato/{fn}', 'w', encoding='utf-8') as f:
                f.write(r2.text)
            
            # Search in JS
            js_text = r2.text
            for pat in key_patterns:
                for m in re.finditer(pat, js_text, re.I):
                    print(f"  [{fn}] KEY FOUND: {m.group(1)[:60]}")
            
            # Also find API endpoints
            api_urls = set(re.findall(r'https?://[a-zA-Z0-9][-a-zA-Z0-9]*(?:\.[a-zA-Z0-9][-a-zA-Z0-9]*)+/[a-zA-Z0-9_/.-]{3,80}', js_text))
            zomato_urls = [u for u in api_urls if 'zomato' in u.lower() and ('api' in u.lower() or 'v1' in u.lower() or 'v2' in u.lower())]
            if zomato_urls:
                print(f"  [{fn}] Zomato APIs ({len(zomato_urls)}):")
                for zu in sorted(zomato_urls)[:10]:
                    print(f"      {zu}")
            
            downloaded += 1
    except:
        pass

# Try Zomato API with common keys
print("\n--- ZOMATO API KEY BRUTE ---")
common_keys = [
    '7749b19667964b4f62cfe6e74d04c0b6',  # old Zomato API key format
    'zomato', 'zomato_api', 'test', 'dev',
    '1234567890', '0123456789abcdef',
]
for key in common_keys:
    try:
        r3 = requests.get('https://www.zomato.com/api/v1/', 
                         headers={**H, 'X-Zomato-API-Key': key, 'user-key': key, 'api-key': key},
                         timeout=8)
        if r3.status_code == 200:
            j = r3.json()
            if j.get('status') != 403:
                print(f"  KEY {key}: {r3.text[:200]}")
    except:
        pass

# ===== GOJEK =====
print(f"\n{'='*60}")
print("=== GOJEK ===")

r = requests.get('https://www.gojek.com/', headers=H, timeout=20, allow_redirects=True)
html = r.text
print(f"Homepage: {r.status_code}, {len(html)} bytes -> {r.url}")

with open('D:/scan/_new_targets/gojek/homepage.html', 'w', encoding='utf-8') as f:
    f.write(html)

# SSR data
print("\n--- SSR DATA ---")
for pat_name, pat in [
    ('__NEXT_DATA__', r'__NEXT_DATA__\s*=\s*({.+?});?\s*</script>'),
    ('__NUXT__', r'window\.__NUXT__\s*=\s*({.+?});'),
    ('window.__data', r'window\.__data\s*=\s*({.+?});'),
    ('json_script', r'<script[^>]*type="application/json"[^>]*id="([^"]*)"[^>]*>([^<]{100,})</script>'),
]:
    for m in re.finditer(pat, html, re.I | re.DOTALL):
        if pat_name == 'json_script':
            val = m.group(2)[:2000]
            print(f"  [{pat_name}] id={m.group(1)} ({len(m.group(2))} chars)")
        else:
            val = m.group(1)[:2000]
            print(f"  [{pat_name}] ({len(m.group(1))} chars)")
        try:
            data = json.loads(val if pat_name != 'json_script' else m.group(2))
            if isinstance(data, dict):
                print(f"    Top keys: {list(data.keys())[:25]}")
        except:
            pass

# JS bundles
print("\n--- JS BUNDLES ---")
js_urls = set()
for m in re.finditer(r'<script[^>]*src="([^"]+)"', html, re.I):
    js_urls.add(m.group(1))
for m in re.finditer(r'(/_next/static/[^"\'\s]+\.js)', html):
    js_urls.add(m.group(1) if m.group(1).startswith('http') else 'https://www.gojek.com' + m.group(1))

print(f"  Total: {len(js_urls)}")
for u in sorted(js_urls)[:15]:
    print(f"    {u}")

# Try following API redirects (Next.js pattern - follow 308 to actual API)
print("\n--- FOLLOW API REDIRECTS ---")
for path in ['/api/', '/api/v1/', '/api/v2/', '/graphql']:
    try:
        r4 = requests.get('https://www.gojek.com' + path, headers=H, timeout=10, allow_redirects=True)
        ct = str(r4.headers.get('content-type', ''))[:60]
        body = r4.text[:200].replace('\n', ' ')
        print(f"  GET  {path:20s} -> {r4.status_code:3d} | {r4.url[:80]} | {ct} | {body[:100]}")
    except Exception as e:
        print(f"  GET  {path:20s} -> ERR: {str(e)[:50]}")

# Try gojek API domains
print("\n--- GOJEK API DOMAINS ---")
for domain in [
    'https://api.gojek.com/', 'https://api.gojekapi.com/',
    'https://gofood.co.id/', 'https://gojek.com/api/',
    'https://www.gojek.com/graphql',
]:
    try:
        r5 = requests.get(domain, headers=H, timeout=8, allow_redirects=False)
        ct = str(r5.headers.get('content-type', ''))[:60]
        body = r5.text[:120].replace('\n', ' ')
        print(f"  {domain:40s} -> {r5.status_code:3d} | {ct} | {body[:100]}")
    except Exception as e:
        print(f"  {domain:40s} -> ERR: {str(e)[:60]}")

print("\n=== DONE ===")

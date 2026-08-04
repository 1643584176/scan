"""Fetch wolt.com venue page and extract API calls / inline data."""
import requests, re, json

H = {
    'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36',
    'Origin': 'https://wolt.com',
    'X-HackerOne-Research': 'pccp',
}

# Fetch the venue page HTML
url = 'https://wolt.com/en/fin/helsinki/venue/wolt-market-kamppi'
r = requests.get(url, headers=H)
html = r.text
print(f"[1] Page: {r.status_code}, {len(html)} bytes")

# Find all script tags with inline data
scripts = re.findall(r'<script[^>]*>(.*?)</script>', html, re.DOTALL)
print(f"\n[2] Inline scripts: {len(scripts)}")
for i, s in enumerate(scripts):
    s_stripped = s.strip()
    if s_stripped and len(s_stripped) > 50:
        print(f"\n  Script #{i} ({len(s_stripped)} chars):")
        print(f"  {s_stripped[:300]}...")

# Find window.__XXX__ assignments
for pattern in ['window\.__[A-Z_]+__', 'window\.__[A-Z_]+\s*=']:
    matches = re.findall(pattern, html)
    if matches:
        print(f"\n[3] Window assignments: {list(set(matches))}")

# Find __NEXT_DATA__ or similar SSR data
for pattern in ['__NEXT_DATA__', '__NUXT__', '__INITIAL_STATE__', '__DATA__', '__APP_DATA__']:
    m = re.search(pattern + r'[^>]*>\s*({.*?})\s*</script>', html, re.DOTALL)
    if m:
        print(f"\n[4] {pattern}: {m.group(1)[:500]}...")

# Find API URLs in JS
api_urls = re.findall(r'https?://[a-z][a-z0-9.-]*wolt[a-z0-9.-]*\.com/[^\s"\'<>]+', html)
unique_apis = list(set([u.rstrip('),;') for u in api_urls]))
print(f"\n[5] API URLs in HTML: {len(unique_apis)}")
for u in sorted(unique_apis)[:20]:
    print(f"    {u}")

# Extract all JS bundle URLs
js_urls = re.findall(r'(?:src|href)="([^"]+\.js[^"]*)"', html)
print(f"\n[6] JS bundles: {len(js_urls)}")
for j in js_urls[:10]:
    print(f"    {j}")

# Look for __EMOTION_*, __CSS*, styled-components data
for k in ['__EMOTION', '__CSS', '__STYLES', 'data-server-rendered']:
    if k in html:
        print(f"\n[7] Found: {k}")

# Look for relay/graphql persisted queries
pq = re.findall(r'"[a-f0-9]{32}"', html)
if pq:
    print(f"\n[8] Possible persisted query hashes: {len(set(pq))}")
    for h in list(set(pq))[:5]:
        print(f"    {h}")

# Specifically look for items/menu data in any format
for keyword in ['"items"', '"menu"', '"baseprice"', '"item_id"', '"product"']:
    if keyword in html:
        # Find context around it
        for m in re.finditer(keyword, html):
            start = max(0, m.start() - 50)
            end = min(len(html), m.end() + 100)
            print(f"\n[9] Found '{keyword}' at pos {m.start()}: ...{html[start:end]}...")
            break
        break

print("\nDONE")

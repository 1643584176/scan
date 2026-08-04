"""Batch probe new food delivery targets - Batch 1."""
import requests, re, json, os
from concurrent.futures import ThreadPoolExecutor, as_completed

H = {
    'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/126.0.0.0 Safari/537.36',
    'Accept-Language': 'en-US,en;q=0.9',
}

os.makedirs('D:/scan/_new_targets', exist_ok=True)

TARGETS = [
    # Just Eat Takeaway brands
    ('just-eat.co.uk', 'https://www.just-eat.co.uk'),
    ('takeaway.com', 'https://www.takeaway.com'),
    ('lieferando.de', 'https://www.lieferando.de'),
    # Deliveroo
    ('deliveroo.co.uk', 'https://deliveroo.co.uk'),
    ('deliveroo.fr', 'https://deliveroo.fr'),
    ('deliveroo.com.au', 'https://deliveroo.com.au'),
    # Grubhub
    ('grubhub.com', 'https://www.grubhub.com'),
    # Zomato
    ('zomato.com', 'https://www.zomato.com'),
    # Swiggy
    ('swiggy.com', 'https://www.swiggy.com'),
    # Rappi
    ('rappi.com', 'https://www.rappi.com'),
    ('rappi.com.ar', 'https://www.rappi.com.ar'),
    # SkipTheDishes
    ('skipthedishes.com', 'https://www.skipthedishes.com'),
    # iFood
    ('ifood.com.br', 'https://www.ifood.com.br'),
    # Postmates
    ('postmates.com', 'https://postmates.com'),
    # Grab
    ('grab.com', 'https://www.grab.com'),
    # Gojek
    ('gojek.com', 'https://www.gojek.com'),
]

def probe(label, base):
    try:
        r = requests.get(base + '/', headers=H, timeout=15, allow_redirects=True)
        html = r.text
        status = r.status_code
        final_url = r.url
        size = len(html)
        
        if 'Just a moment' in html[:300] or 'cf-browser-verify' in html or 'Checking your browser' in html[:300]:
            return (label, base, 'CF_BLOCKED', status, size, final_url, None, [], 0, [])
        
        # Detect frameworks
        frameworks = []
        if 'next' in html.lower() and ('__next' in html or '__NEXT_DATA__' in html):
            frameworks.append('Next.js')
        if 'nuxt' in html.lower() or '__NUXT__' in html:
            frameworks.append('Nuxt.js')
        if 'react' in html.lower() or 'data-reactroot' in html or 'react-root' in html:
            frameworks.append('React')
        if 'vue' in html.lower() and ('vue' in html[:5000] or 'v-' in html):
            frameworks.append('Vue.js')
        if 'angular' in html.lower() or 'ng-version' in html:
            frameworks.append('Angular')
        if 'wordpress' in html.lower() or 'wp-content' in html:
            frameworks.append('WordPress')
        
        # SSR data
        ssr = None
        for pat_name, pat in [
            ('__NEXT_DATA__', r'__NEXT_DATA__\s*=\s*({.+?});?\s*</script>'),
            ('__NUXT__', r'window\.__NUXT__\s*=\s*({.+?});'),
            ('window.__data', r'window\.__data\s*=\s*({.+?});'),
        ]:
            m = re.search(pat, html, re.I | re.DOTALL)
            if m:
                ssr = pat_name
                break
        
        # JS bundles
        js_count = len(re.findall(r'<script[^>]*src="([^"]+)"', html, re.I))
        
        # API paths in HTML
        api_paths = set()
        for m in re.finditer(r'(/[a-z0-9_-]+/[a-z0-9_/.-]{3,60})', html):
            path = m.group(1)
            if any(kw in path.lower() for kw in ['api', 'v1/', 'v2/', 'v3/', 'graphql', 'order', 'search', 'store', 'restaurant', 'checkout', 'menu', 'gql']):
                api_paths.add(path)
        
        return (label, base, 'OK', status, size, final_url, ssr, frameworks, js_count, list(api_paths)[:15])
    except Exception as e:
        return (label, base, f'ERR:{str(e)[:60]}', 0, 0, base, None, [], 0, [])

results = []
with ThreadPoolExecutor(max_workers=8) as ex:
    futs = {ex.submit(probe, l, b): l for l, b in TARGETS}
    for f in as_completed(futs):
        results.append(f.result())

# Sort: OK first, then CF blocked, then errors
results.sort(key=lambda x: (0 if x[2]=='OK' else (1 if 'CF' in str(x[2]) else 2), x[2]))

out_lines = []
for r in results:
    label, base, status, code, size, final, ssr, fws, js, apis = r
    out_lines.append(f'\n=== {label} === {base}')
    out_lines.append(f'  Status: {status} | HTTP {code} | {size} bytes | Final: {final}')
    if fws:
        out_lines.append(f'  Frameworks: {fws}')
    if ssr:
        out_lines.append(f'  SSR: {ssr}')
    out_lines.append(f'  JS bundles: {js}')
    if apis:
        out_lines.append(f'  API paths ({len(apis)}):')
        for p in sorted(apis)[:10]:
            out_lines.append(f'    {p}')

output = '\n'.join(out_lines)
print(output)

# Also save results
with open('D:/scan/_new_targets/_batch1_results.txt', 'w', encoding='utf-8') as f:
    f.write(output)

# ===== Quick API probe for OK targets =====
print(f"\n\n{'='*60}")
print("=== QUICK API PROBE FOR OK TARGETS ===")

ok_targets = [(r[0], r[1]) for r in results if r[2] == 'OK']
for label, base in ok_targets:
    print(f"\n--- {label}: {base} ---")
    for path in ['/graphql', '/api/', '/api/v1/', '/api/v2/', '/v1/', '/v2/']:
        try:
            r2 = requests.get(base + path, headers=H, timeout=8, allow_redirects=False)
            ct = r2.headers.get('content-type', '')[:40]
            if r2.status_code not in [404]:
                body = r2.text[:120].replace('\n', ' ')
                print(f"  GET {path:20s} -> {r2.status_code:3d} | {ct} | {body[:100]}")
        except:
            pass

print("\n=== DONE ===")

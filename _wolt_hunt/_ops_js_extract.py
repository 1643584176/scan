"""Download ops.wolt.com JS bundles and extract API endpoints."""
import requests, re, os

H = {
    'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36',
    'X-HackerOne-Research': 'pccp',
}

os.makedirs('D:/scan/_wolt_hunt/ops_js', exist_ok=True)

# Download shell JS files
js_files = [
    '/static/apps/shell/releases/75419df64a36cc110e3099f660ad406c6a4ec8cb/main.js',
    '/static/apps/shell/releases/75419df64a36cc110e3099f660ad406c6a4ec8cb/runtime.js',
]

print("=== DOWNLOADING OPS JS ===")
for js_path in js_files:
    url = f'https://ops.wolt.com{js_path}'
    r = requests.get(url, headers=H, timeout=15)
    fname = js_path.split('/')[-1]
    fpath = f'D:/scan/_wolt_hunt/ops_js/{fname}'
    with open(fpath, 'w', encoding='utf-8') as f:
        f.write(r.text)
    print(f"  {fname}: {len(r.text)} bytes -> {fpath}")

# Extract API URLs from the JS
print("\n=== EXTRACTING API URLS ===")
all_apis = set()
for js_path in js_files:
    fname = js_path.split('/')[-1]
    fpath = f'D:/scan/_wolt_hunt/ops_js/{fname}'
    if not os.path.exists(fpath):
        continue
    with open(fpath, encoding='utf-8') as f:
        txt = f.read()

    # Find URLs
    urls = set(re.findall(r'(?:https?://[a-zA-Z0-9._-]+\.wolt\.com[^"\'\\s)]{0,100})', txt, re.I))
    print(f"\n  --- {fname} ---")
    for u in sorted(urls)[:30]:
        print(f"    {u}")
        all_apis.add(u)

    # Also find API paths
    api_paths = set(re.findall(r"""["'](/api[^"']{3,80})["']""", txt))
    graphql = set(re.findall(r"""["'](/graphql[^"']{0,40})["']""", txt))
    vpaths = set(re.findall(r"""["'](/v\d/[^"']{3,80})["']""", txt))
    for p in sorted(api_paths | graphql | vpaths)[:30]:
        print(f"    PATH: {p}")
        all_apis.add(p)

# Also just grep for any domain pattern in main.js
print("\n=== ALL HOSTS IN MAIN.JS ===")
main_path = 'D:/scan/_wolt_hunt/ops_js/main.js'
if os.path.exists(main_path):
    with open(main_path, encoding='utf-8') as f:
        txt = f.read()
    hosts = set(re.findall(r'https?://([a-zA-Z0-9][-a-zA-Z0-9]*(?:\.[a-zA-Z0-9][-a-zA-Z0-9]*)+)', txt))
    for h in sorted(hosts):
        print(f"  {h}")

print(f"\n=== TOTAL UNIQUE APIs: {len(all_apis)} ===")
for u in sorted(all_apis)[:50]:
    print(f"  {u}")

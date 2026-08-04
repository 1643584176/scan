"""Full checkout + find place order endpoint."""
import requests, json

H = {
    'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64)',
    'Origin': 'https://wolt.com',
    'X-HackerOne-Research': 'pccp',
    'Content-Type': 'application/json',
}

VENUE_ID = '60ebeb71c6904c2caf035f71'
FAKE_ITEM_ID = '670fa3e9ead6e49d65cc3614'

item_obj = {
    'id': FAKE_ITEM_ID,
    'name': 'Test Item',
    'count': 1,
    'price': 1,
    'base_price': 1,
    'end_amount': 1,
    'options': [],
    'restrictions': [],
    'category_id': '',
    'exclude_from_discounts': False,
}

body = {
    'items': [item_obj],
    'base_price': 1,
    'end_amount': 1,
    'supplier_id': VENUE_ID,
    'selected_delivery_method': 'homedelivery',
    'delivery_location': {'lat': 60.168142, 'lon': 24.939986},
    'currency': 'EUR',
    'vendor': 'wolt',
    'discount': 0,
    'basket_id': 'test-basket-1',
    'pickup': False,
    'scheduled_time': None,
    'shipping_method': 'homedelivery',
    'discount_code': None,
    'purchase_plan': {
        'venue': {
            'id': VENUE_ID,
            'country': 'FIN',
            'currency': 'EUR'
        },
        'delivery_method': 'homedelivery',
        'menu_items': [item_obj]
    }
}

r = requests.post('https://consumer-api.wolt.com/order-xp/web/v2/pages/checkout',
                  headers=H, json=body)
d = r.json()
print(f"Status: {r.status_code}")
print(f"payable_amount: {d.get('payable_amount')}")
print(f"\nFull keys: {list(d.keys())}")
print(f"\n=== FULL RESPONSE ===")
print(json.dumps(d, indent=2)[:3000])

# Save for analysis
with open('_wolt_hunt/_checkout_response.json', 'w') as f:
    json.dump(d, f, indent=2)
print(f"\nSaved to _checkout_response.json")

# Step 2: Try order placement endpoints
print(f"\n=== TRYING ORDER PLACEMENT ===")
order_body = {
    'basket_id': body['basket_id'],
    'supplier_id': VENUE_ID,
    'delivery_location': body['delivery_location'],
    'selected_delivery_method': 'homedelivery',
    'currency': 'EUR',
}
order_endpoints = [
    ('POST', '/order-xp/web/v1/order/place'),
    ('POST', '/order-xp/web/v2/order/place'),
    ('POST', '/order-xp/web/v1/orders'),
    ('POST', '/order-xp/web/v2/orders'),
    ('POST', '/order-xp/web/v1/order/create'),
    ('POST', '/order-xp/web/v2/order/create'),
    ('POST', '/order-xp/web/v1/order'),
    ('POST', '/order-xp/web/v2/order'),
    ('POST', '/order-xp/web/v1/pages/order'),
    ('POST', '/order-xp/web/v2/pages/order'),
    ('PUT', '/order-xp/web/v1/order'),
    ('PUT', '/order-xp/web/v2/order'),
]
for method, ep in order_endpoints:
    try:
        if method == 'GET':
            r = requests.get(f'https://consumer-api.wolt.com{ep}', headers=H)
        else:
            r = requests.post(f'https://consumer-api.wolt.com{ep}', headers=H, json=order_body)
        if r.status_code not in (404, 405):
            print(f"  {method} {ep}: {r.status_code} | {r.text[:200]}")
    except Exception as e:
        print(f"  {method} {ep}: ERR {str(e)[:60]}")

print("\nDONE")

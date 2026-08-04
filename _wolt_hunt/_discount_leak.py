import requests, json

h = {'User-Agent': 'Mozilla/5.0', 'Origin': 'https://wolt.com', 'App-Language': 'en'}

r = requests.get('https://consumer-api.wolt.com/order-xp/web/v1/venue/slug/wolt-market-kamppi/dynamic/',
                params={'selected_delivery_method': 'homedelivery', 'lat': '60.168', 'lon': '24.940'},
                headers=h, timeout=15)
vd = r.json()

# 1. Full discount details
print("=== DISCOUNT CAMPAIGNS (FULL) ===")
discounts = vd.get('venue_raw', {}).get('discounts', [])
for i, d in enumerate(discounts):
    print(f'\n--- Discount #{i+1} ---')
    print(f'  id: {d.get("id")}')
    effects = d.get('effects', {})
    for ek, ev in effects.items():
        if ev:
            print(f'  {ek}: {json.dumps(ev)}')
    conds = d.get('conditions', {})
    if conds:
        print(f'  conditions keys: {list(conds.keys())}')
        for ck, cv in conds.items():
            if cv:
                print(f'    {ck}: {json.dumps(cv)[:200]}')

# 2. Delivery pricing details
print("\n\n=== DELIVERY PRICING ===")
ds = vd.get('venue_raw', {}).get('delivery_specs', {})
for k in ['original_delivery_price', 'order_minimum_no_surcharge', 'order_minimum_possible']:
    print(f'  {k}: {ds.get(k)}')

dp = ds.get('delivery_pricing', {})
print(f'  delivery_pricing keys: {list(dp.keys())}')
# Show pricing structure
for dk, dv in dp.items():
    if isinstance(dv, (int, float, str)):
        print(f'    {dk}: {dv}')
    elif isinstance(dv, dict):
        print(f'    {dk}: {json.dumps(dv)[:150]}')
    elif isinstance(dv, list):
        print(f'    {dk}: [{len(dv)} items] {json.dumps(dv[:2])[:150]}')

# 3. Subscription details
sub = ds.get('subscription', {})
if sub:
    print(f'\n  subscription: {json.dumps(sub)[:300]}')

# 4. Check if discount is auto-applied at checkout with specific conditions
print("\n\n=== CHECKOUT WITH DISCOUNT TRIGGER ===")
# Try with delivery_discount conditions
payload = {
    "purchase_plan": {
        "venue": {"id": "60ebeb71c6904c2caf035f71", "country": "FIN", "currency": "EUR"},
        "delivery_method": "homedelivery",
        "menu_items": [
            {"id": "60ebeb71c6904c2caf035f71", "name": "Test", "count": 1,
             "base_price": 2000, "price": 2000, "end_amount": 2000,
             "options": [], "category_id": "test", "exclude_from_discounts": False,
             "restrictions": []}
        ],
        # Try to trigger the campaign
        "campaign_id": "venue_campaign:6a4f437f001d9efc9c621570"
    }
}
r = requests.post('https://consumer-api.wolt.com/order-xp/web/v2/pages/checkout',
                 json=payload, headers={**h, 'Content-Type': 'application/json'}, timeout=15)
d = r.json() if r.status_code == 200 else {}
print(f'  campaign_id in payload: {r.status_code} | payable={d.get("payable_amount","?")}')

# Without campaign
payload2 = {
    "purchase_plan": {
        "venue": {"id": "60ebeb71c6904c2caf035f71", "country": "FIN", "currency": "EUR"},
        "delivery_method": "homedelivery",
        "menu_items": [
            {"id": "60ebeb71c6904c2caf035f71", "name": "Test", "count": 1,
             "base_price": 2000, "price": 2000, "end_amount": 2000,
             "options": [], "category_id": "test", "exclude_from_discounts": False,
             "restrictions": []}
        ]
    }
}
r2 = requests.post('https://consumer-api.wolt.com/order-xp/web/v2/pages/checkout',
                  json=payload2, headers={**h, 'Content-Type': 'application/json'}, timeout=15)
d2 = r2.json() if r2.status_code == 200 else {}
print(f'  no campaign: {r2.status_code} | payable={d2.get("payable_amount","?")}')

# 5. Check another venue for discount exposure
print("\n=== TEST OTHER VENUE ===")
r3 = requests.get('https://consumer-api.wolt.com/order-xp/web/v1/venue/slug/wolt-market-toolo/dynamic/',
                params={'selected_delivery_method': 'homedelivery'},
                headers=h, timeout=10)
if r3.status_code == 200:
    d3 = r3.json()
    discs = d3.get('venue_raw', {}).get('discounts', [])
    print(f'  wolt-market-toolo discounts: {len(discs)}')
    for d in discs[:2]:
        print(f'    {d.get("id")}: {json.dumps(d.get("effects",{}))[:150]}')
else:
    print(f'  wolt-market-toolo: {r3.status_code}')

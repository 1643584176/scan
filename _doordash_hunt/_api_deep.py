"""DoorDash API deep probe with known patterns."""
import requests, json

# DoorDash uses Cloudflare - need to match real browser headers
H = {
    'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/131.0.0.0 Safari/537.36',
    'Accept': 'application/json, text/plain, */*',
    'Accept-Language': 'en-US,en;q=0.9',
    'Accept-Encoding': 'gzip, deflate, br',
    'Cache-Control': 'no-cache',
}

BASE = 'https://www.doordash.com'

# 1. Try store search with proper query params
print("=== 1. STORE SEARCH ===")
search_params = [
    {'lat': '37.7749', 'lng': '-122.4194'},
    {'latitude': '37.7749', 'longitude': '-122.4194'},
    {'lat': '37.7749', 'lng': '-122.4194', 'limit': '10'},
]
for params in search_params:
    for method in ['GET']:
        url = BASE + '/en-US/v1/stores/search/'
        ps = '&'.join(f'{k}={v}' for k, v in params.items())
        full = f'{url}?{ps}'
        r = requests.get(full, headers=H, timeout=10, allow_redirects=False)
        print(f"  GET {full} -> {r.status_code} | {r.text[:200]}")

# 2. Try POST with different body formats
print("\n=== 2. POST BODY FORMATS ===")
post_bodies = [
    {'lat': 37.7749, 'lng': -122.4194},
    {'latitude': 37.7749, 'longitude': -122.4194},
    [37.7749, -122.4194],
    '{"lat":37.7749,"lng":-122.4194}',
]
for body in post_bodies:
    r = requests.post(BASE + '/v1/stores/search/', headers={**H, 'Content-Type': 'application/json'},
                      json=body if isinstance(body, (dict, list)) else None,
                      data=body if isinstance(body, str) else None,
                      timeout=10)
    print(f"  body={str(body)[:60]:60s} -> {r.status_code} | {r.text[:150]}")

# 3. Try with x-newrelic headers (from the 403 page)
print("\n=== 3. WITH DD-SPECIFIC HEADERS ===")
dd_headers = {**H, 'X-DD-Client': 'web', 'X-DD-Version': '1.0'}
r = requests.get(BASE + '/en-US/v1/stores/search/?lat=37.7749&lng=-122.4194',
                 headers=dd_headers, timeout=10, allow_redirects=False)
print(f"  {r.status_code} | {r.text[:200]}")

# 4. Try actual DoorDash food page URL patterns
print("\n=== 4. FOOD PAGES ===")
food_urls = [
    '/en-US/food/',
    '/en-US/search/store/?address=San+Francisco',
    '/en-US/store/',
    '/en-US/restaurant/',
]
for url in food_urls:
    r = requests.get(BASE + url, headers=H, timeout=10, allow_redirects=False)
    body = r.text[:150].replace('\n', ' ')
    print(f"  GET {url:40s} -> {r.status_code} | {body}")

# 5. Try subdomain API endpoints (not on www)
print("\n=== 5. OTHER DOORDASH HOSTS ===")
other_hosts = [
    'https://api.doordash.com/v1/stores/',
    'https://api.doordash.com/v2/stores/',
    'https://order.doordash.com/',
    'https://consumer.doordash.com/',
    'https://www.doordash.com/graphql/',
]
for url in other_hosts:
    try:
        r = requests.get(url, headers=H, timeout=10, allow_redirects=False)
        print(f"  {url:55s} -> {r.status_code} | {r.text[:120].replace(chr(10),' ')}")
    except Exception as e:
        print(f"  {url:55s} -> ERR: {str(e)[:80]}")

# 6. Cookie-based bypass attempt
print("\n=== 6. COOKIE BYPASS ===")
session = requests.Session()
session.headers.update(H)
# First visit to get cookies
r1 = session.get(BASE + '/', timeout=15)
cookies = dict(session.cookies)
print(f"  Initial cookies: {cookies}")
# Then try API
r2 = session.get(BASE + '/en-US/v1/stores/search/?lat=37.7749&lng=-122.4194', timeout=10, allow_redirects=False)
print(f"  API with cookies: {r2.status_code} | {r2.text[:200]}")

print("\n=== DONE ===")

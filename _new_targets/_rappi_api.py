"""Rappi API deep probe - api.rappi.com.mx is LIVE."""
import requests, re, json, os

H = {
    'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/126.0.0.0 Safari/537.36',
    'Accept': 'application/json, text/plain, */*',
    'Accept-Language': 'en-US,en;q=0.9',
    'Origin': 'https://www.rappi.com.mx',
    'Referer': 'https://www.rappi.com.mx/',
}

os.makedirs('D:/scan/_new_targets/rappi', exist_ok=True)

API_BASES = [
    'https://api.rappi.com.mx',
    'https://api.rappi.com.ar',
    'https://services.rappi.com',
]

# Common API paths to fuzz
API_PATHS = [
    # REST-like
    '/api/', '/api/v1/', '/api/v2/', '/api/v3/',
    '/v1/', '/v2/', '/v3/',
    # GraphQL
    '/graphql', '/api/graphql', '/query',
    # Common endpoints
    '/api/v1/restaurants', '/api/v1/stores', '/api/v1/search',
    '/api/v2/restaurants', '/api/v2/stores', '/api/v2/search',
    '/api/restaurants', '/api/stores', '/api/search',
    '/restaurants', '/stores', '/search',
    '/api/v1/cities', '/api/v1/countries', '/api/v1/categories',
    '/api/v1/menu', '/api/v1/products', '/api/v1/items',
    '/api/v1/orders', '/api/v1/checkout', '/api/v1/cart',
    '/api/v1/users', '/api/v1/auth', '/api/v1/login',
    '/api/v1/config', '/api/v1/health', '/api/v1/status',
    # More specific
    '/api/v1/public/restaurants', '/api/v1/public/stores',
    '/api/v1/consumer/restaurants', '/api/v1/consumer/stores',
    '/api/cp/v1/', '/api/cp/v1/restaurants',
    # Common microservice patterns
    '/api/restaurant/v1/', '/api/store/v1/', '/api/search/v1/',
    '/api/order/v1/', '/api/user/v1/',
]

for base_url in API_BASES:
    print(f"\n{'='*60}")
    print(f"=== {base_url} ===")
    
    # First, probe all paths
    for path in API_PATHS:
        url = base_url + path
        try:
            # GET first
            r = requests.get(url, headers=H, timeout=10, allow_redirects=False)
            ct = str(r.headers.get('content-type', ''))[:80]
            
            if r.status_code in [200, 201, 400, 401, 403, 405, 422, 429]:
                body = r.text[:300].replace('\n', ' ').replace('\r', '')
                print(f"  GET  {url:60s} -> {r.status_code:3d} | {ct[:50]}")
                if r.status_code in [200, 400, 401, 422]:
                    print(f"       Body: {body[:200]}")
            
            # POST for graphql
            if 'graphql' in path or 'query' in path:
                r2 = requests.post(url, headers={**H, 'Content-Type': 'application/json'},
                                  json={"query": "{ __typename }"}, timeout=10)
                if r2.status_code not in [404]:
                    print(f"  POST {url:60s} -> {r2.status_code:3d} | {r2.text[:200]}")
                    
        except Exception as e:
            pass  # Silently skip timeouts
    
    # Try common query params
    print(f"\n  --- QUERY PARAMS ---")
    for path in ['/api/v1/restaurants', '/api/restaurants', '/restaurants']:
        for params in [
            {'lat': '19.4326', 'lng': '-99.1332'},  # Mexico City
            {'latitude': '19.4326', 'longitude': '-99.1332'},
            {'city': 'ciudad-de-mexico', 'country': 'mx'},
            {'city_id': '1', 'country_id': '1'},
        ]:
            try:
                url = base_url + path
                r = requests.get(url, headers=H, params=params, timeout=10, allow_redirects=False)
                if r.status_code not in [404]:
                    ct = str(r.headers.get('content-type', ''))[:50]
                    body = r.text[:200].replace('\n', ' ')
                    print(f"  GET  {url}?{list(params.keys())[0]}=... -> {r.status_code} | {ct} | {body[:150]}")
            except:
                pass

print("\n=== DONE ===")

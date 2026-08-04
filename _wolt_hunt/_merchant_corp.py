"""Probe merchant.wolt.com and corporate.wolt.com."""
import requests, re

H = {
    'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36',
    'X-HackerOne-Research': 'pccp',
}

def probe(label, url, method='GET', **kwargs):
    try:
        r = requests.request(method, url, headers=H, timeout=10, allow_redirects=True, **kwargs)
        ct = r.headers.get('content-type', '')[:60]
        body = r.text[:300].replace('\n', ' ')
        redirect = f" -> {r.url}" if r.url != url else ""
        return f"{r.status_code} | {ct} | {body[:200]}{redirect}"
    except Exception as e:
        return f"ERR: {e}"

print("=== MERCHANT.WOLT.COM ===\n")
for path in ['/','/login','/api','/graphql','/api/v1/','/register','/signup',
             '/health','/metrics','/status','/docs','/swagger','/admin']:
    r = probe('merchant', f'https://merchant.wolt.com{path}')
    print(f"  {path:20s} -> {r[:200]}")

print("\n=== CORPORATE.WOLT.COM ===\n")
for path in ['/','/login','/api','/graphql','/api/v1/','/register','/signup',
             '/health','/metrics','/status','/docs','/swagger','/admin',
             '/orders','/invite','/dashboard']:
    r = probe('corporate', f'https://corporate.wolt.com{path}')
    print(f"  {path:20s} -> {r[:200]}")

# Also test POST to API paths
print("\n=== MERCHANT POST API ===")
for path in ['/api/v1/orders','/api/v1/venues','/graphql']:
    r = probe('merchant-post', f'https://merchant.wolt.com{path}', method='POST',
              json={'test': 1})
    print(f"  POST {path:25s} -> {r[:200]}")

print("\n=== CORPORATE POST API ===")
for path in ['/api/v1/orders','/api/v1/venues','/graphql']:
    r = probe('corp-post', f'https://corporate.wolt.com{path}', method='POST',
              json={'test': 1})
    print(f"  POST {path:25s} -> {r[:200]}")

print("\n=== DONE ===")

"""Quick sweep: newly discovered services from wolt.com env config."""
import requests

H = {
    'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64)',
    'X-HackerOne-Research': 'pccp',
}

# From wolt.com env + corporate.wolt.com env
services = [
    # New from wolt.com frontend env
    'https://consumer-api-experiment.wolt.com/',
    'https://gift-card-shop-http-api.wolt.com/',
    'https://agentic-shopping.wolt.com/',
    'https://payment-processor.wolt.com/',
    'https://payment-service.wolt.com/',
    'https://topup-service.wolt.com/',
    'https://tax-reporting-service.wolt.com/',
    'https://le-customer-interaction-service.wolt.com/',
    'https://payments-tips-service.wolt.com/',
    'https://plutos.wolt.com/public',
    'https://prodinfo.wolt.com/',
    # Previously discovered (corporate env)
    'https://corporate-service.wolt.com/',
    'https://legitimizer.wolt.com/',
    'https://merchant-payout-service.wolt.com/',
    'https://wolf.wolt.com/',
    'https://daas-public-api.wolt.com/',
    'https://daas-self-service-api.wolt.com/',
    # Other interesting
    'https://converse-static-resources.wolt.com/',
    'https://courier-api.wolt.com/workers-api',
]

# Also try common API paths on each
common_paths = ['', '/api/', '/api/v1/', '/health', '/status', '/v1/', '/graphql', '/.well-known/']

print("=== SERVICE SWEEP ===\n")
for svc in services:
    name = svc.split('//')[1].split('/')[0]
    results = []
    for path in common_paths:
        url = f"{svc.rstrip('/')}{path}" if path else svc
        try:
            r = requests.get(url, headers=H, timeout=6, allow_redirects=False)
            if r.status_code not in (404, 302, 301):
                ct = r.headers.get('content-type', '')[:40]
                results.append(f"{r.status_code}({ct})")
        except:
            results.append("ERR")
    
    interesting = [f"{p}:{r}" for p, r in zip(common_paths, results) if r != 'ERR' and not r.startswith('404')]
    if interesting:
        print(f"  {name:40s} {' | '.join(interesting)}")

# Special: prodinfo might have product info
print(f"\n=== PRODINFO ===")
for path in ['/', '/health', '/api/', '/v1/', '/products/', '/info/']:
    try:
        r = requests.get(f'https://prodinfo.wolt.com{path}', headers=H, timeout=8)
        if r.status_code != 404:
            print(f"  {path}: {r.status_code} | {r.text[:150]}")
    except Exception as e:
        print(f"  {path}: ERR {str(e)[:50]}")

# Try courier-api 
print(f"\n=== COURIER-API ===")
for path in ['/', '/workers-api/', '/workers-api/health', '/workers-api/v1/', '/v1/']:
    try:
        r = requests.get(f'https://courier-api.wolt.com{path}', headers=H, timeout=8)
        if r.status_code != 404:
            print(f"  {path}: {r.status_code} | {r.text[:150]}")
    except Exception as e:
        print(f"  {path}: ERR {str(e)[:50]}")

print("\nDONE")

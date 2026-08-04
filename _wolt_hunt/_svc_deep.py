"""Focused probe: legitimizer.wolt.com and other interesting services."""
import requests, json

H = {
    'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64)',
    'X-HackerOne-Research': 'pccp',
}

print("=== LEGITIMIZER.WOLT.COM ===")
paths = [
    '/', '/api/', '/api/v1/', '/v1/', '/v1/health', '/health', '/status',
    '/api/v1/legitimize', '/api/v1/verify', '/api/v1/validate',
    '/api/v1/check', '/api/v1/lookup',
    '/graphql', '/.well-known/', '/swagger', '/openapi.json',
]
for p in paths:
    try:
        r = requests.get(f'https://legitimizer.wolt.com{p}', headers=H, timeout=8)
        ct = r.headers.get('content-type', '')[:40]
        preview = r.text[:200] if 'json' in ct or 'text' in ct else f'[{len(r.content)}b]'
        if r.status_code != 404:
            print(f"  GET  {p:30s} {r.status_code} | {ct:30s} | {preview}")
    except Exception as e:
        print(f"  GET  {p:30s} ERR {str(e)[:50]}")

# Try with the gatekeeper API key as Bearer token
print(f"\n=== LEGITIMIZER with API Key ===")
key = 'Uyf4t2ie9Y1dWJDBjrmwmCdjsz9QFT21jU3WoAg1'
for p in ['/', '/api/', '/api/v1/', '/v1/']:
    for auth_type in [f'Bearer {key}', key]:
        try:
            r = requests.get(f'https://legitimizer.wolt.com{p}', 
                           headers={**H, 'Authorization': auth_type, 'x-api-key': key}, timeout=8)
            if r.status_code != 404:
                print(f"  {p}: {r.status_code} | {r.text[:150]}")
        except:
            pass

# prodinfo redirect follow
print(f"\n=== PRODINFO ===")
for p in ['/', '/health', '/api/', '/v1/']:
    try:
        r = requests.get(f'https://prodinfo.wolt.com{p}', headers=H, timeout=8, allow_redirects=True)
        if r.status_code != 404:
            print(f"  {p}: {r.status_code} → {r.url} | {r.text[:120]}")
    except Exception as e:
        print(f"  {p}: ERR {str(e)[:50]}")

# payment-service
print(f"\n=== PAYMENT-SERVICE ===")
for p in ['/', '/health', '/api/', '/v1/', '/status']:
    try:
        r = requests.get(f'https://payment-service.wolt.com{p}', headers=H, timeout=8)
        if r.status_code != 404:
            print(f"  {p}: {r.status_code} | {r.text[:120]}")
    except Exception as e:
        print(f"  {p}: ERR {str(e)[:50]}")

# plutos 
print(f"\n=== PLUTOS ===")
for p in ['/', '/public/', '/public/health', '/api/', '/v1/']:
    try:
        r = requests.get(f'https://plutos.wolt.com{p}', headers=H, timeout=8)
        if r.status_code != 404:
            print(f"  {p}: {r.status_code} | {r.text[:120]}")
    except Exception as e:
        print(f"  {p}: ERR {str(e)[:50]}")

print("\nDONE")

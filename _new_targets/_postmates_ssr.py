"""Postmates SSR data extraction - parse Redux state + Config for API endpoints."""
import requests, re, json, os

H = {
    'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/126.0.0.0 Safari/537.36',
    'Accept-Language': 'en-US,en;q=0.9',
}

os.makedirs('D:/scan/_new_targets/postmates', exist_ok=True)

# Fetch homepage again
r = requests.get('https://postmates.com/', headers=H, timeout=20, allow_redirects=True)
html = r.text
print(f"Homepage: {r.status_code}, {len(html)} bytes")

# Extract JSON script tags
for m in re.finditer(r'<script[^>]*type="application/json"[^>]*id="([^"]*)"[^>]*>([^<]+)</script>', html, re.I):
    script_id = m.group(1)
    json_str = m.group(2)
    try:
        data = json.loads(json_str)
        out_path = f'D:/scan/_new_targets/postmates/{script_id}.json'
        with open(out_path, 'w', encoding='utf-8') as f:
            json.dump(data, f, indent=2, ensure_ascii=False)
        print(f"\n[{script_id}]: {len(json_str)} chars -> saved")
        
        # Show top-level keys
        if isinstance(data, dict):
            print(f"  Keys: {list(data.keys())[:25]}")
            
            # Search for API URLs, endpoints
            data_str = json.dumps(data)
            api_urls = set(re.findall(r'https?://[a-zA-Z0-9][-a-zA-Z0-9]*(?:\.[a-zA-Z0-9][-a-zA-Z0-9]*)+/[a-zA-Z0-9_/.-]{3,80}', data_str))
            uber_urls = [u for u in api_urls if 'uber' in u.lower() or 'postmates' in u.lower() or 'eats' in u.lower()]
            if uber_urls:
                print(f"  Uber/Postmates URLs ({len(uber_urls)}):")
                for u in sorted(uber_urls)[:20]:
                    print(f"    {u}")
    except Exception as e:
        print(f"  [{script_id}]: PARSE ERR: {e}")

# Quick probe of found Uber APIs
print(f"\n{'='*50}")
print("=== UBER API PROBE ===")
uber_apis = [
    'https://auth.uber.com/v2/create-deferred-session',
    'https://www.ubereats.com/graphql',
    'https://www.ubereats.com/api/',
]
for url in uber_apis:
    for method in ['GET', 'POST']:
        try:
            if method == 'GET':
                r2 = requests.get(url, headers=H, timeout=8, allow_redirects=False)
            else:
                r2 = requests.post(url, headers={**H, 'Content-Type': 'application/json'},
                                  json={}, timeout=8, allow_redirects=False)
            ct = str(r2.headers.get('content-type', ''))[:60]
            body = r2.text[:200].replace('\n', ' ')
            print(f"  {method:4s} {url:50s} -> {r2.status_code:3d} | {ct} | {body[:120]}")
        except Exception as e:
            print(f"  {method:4s} {url:50s} -> ERR: {str(e)[:60]}")

print("\n=== DONE ===")

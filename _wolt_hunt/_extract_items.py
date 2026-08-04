"""Extract env config and item IDs from wolt.com venue page."""
import requests, re, json

H = {
    'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36',
    'Origin': 'https://wolt.com',
    'X-HackerOne-Research': 'pccp',
}

url = 'https://wolt.com/en/fin/helsinki/venue/wolt-market-kamppi'
r = requests.get(url, headers=H)
html = r.text

# Extract script #7 (env config) - the JSON after the <script> tag
scripts = re.findall(r'<script[^>]*>(.*?)</script>', html, re.DOTALL)
env_script = None
dehydrated_script = None
for i, s in enumerate(scripts):
    s_stripped = s.strip()
    if s_stripped.startswith('{"NODE_ENV"'):
        env_script = s_stripped
    if s_stripped.startswith('{"mutations":'):
        dehydrated_script = s_stripped

# Parse env
env = json.loads(env_script)
print("=== ENV CONFIG ===")
for k, v in env.items():
    if 'api' in k.lower() or 'endpoint' in k.lower() or 'uri' in k.lower() or 'url' in k.lower():
        print(f"  {k} = {v}")

# Parse dehydrated state for items
dq = json.loads(dehydrated_script)
print(f"\n=== DEHYDRATED STATE ===")
print(f"  mutations: {len(dq.get('mutations', []))}")
print(f"  queries: {len(dq.get('queries', []))}")

# Find queries with item data
item_ids_found = set()
for qi, q in enumerate(dq.get('queries', [])):
    state = q.get('state', {})
    data = state.get('data', None)
    if data is None:
        continue
    
    # Recursively search for item IDs
    def find_item_ids(obj, depth=0):
        if depth > 8:
            return
        if isinstance(obj, dict):
            for k, v in obj.items():
                if k in ('id', 'item_id', 'product_id') and isinstance(v, str) and len(v) > 10:
                    item_ids_found.add(v)
                find_item_ids(v, depth+1)
        elif isinstance(obj, list):
            for item in obj[:50]:
                find_item_ids(item, depth+1)
    
    find_item_ids(data)
    
    # Print query structure summary
    if isinstance(data, dict):
        keys = list(data.keys())[:10]
        print(f"  Query #{qi}: keys={keys}, size={len(json.dumps(data))}")
    elif isinstance(data, list):
        print(f"  Query #{qi}: list len={len(data)}")
        if data and isinstance(data[0], dict):
            print(f"    First item keys: {list(data[0].keys())[:10]}")

print(f"\n=== ITEM IDs FOUND: {len(item_ids_found)} ===")
for iid in list(item_ids_found)[:10]:
    print(f"  {iid}")

# Also look for venue items in dehydrated state - search for 'baseprice'
baseprice_positions = [m.start() for m in re.finditer(r'baseprice', dehydrated_script)]
print(f"\n  'baseprice' occurrences: {len(baseprice_positions)}")
for pos in baseprice_positions[:5]:
    print(f"  @{pos}: {dehydrated_script[pos:pos+150]}")

print("\nDONE")

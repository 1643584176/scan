"""Extract item data from query #5 (menu) in dehydrated state."""
import requests, re, json

H = {
    'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36',
    'Origin': 'https://wolt.com',
    'X-HackerOne-Research': 'pccp',
}

url = 'https://wolt.com/en/fin/helsinki/venue/wolt-market-kamppi'
r = requests.get(url, headers=H)
html = r.text
scripts = re.findall(r'<script[^>]*>(.*?)</script>', html, re.DOTALL)

for s in scripts:
    s_stripped = s.strip()
    if s_stripped.startswith('{"mutations":'):
        dq = json.loads(s_stripped)
        break

# Query #5 is the menu data
q5 = dq['queries'][5]
data = q5['state']['data']
print(f"Query #5 keys: {list(data.keys())}")
print(f"  items type: {type(data.get('items'))}")
items = data.get('items', [])
print(f"  items count: {len(items)}")
print(f"  categories count: {len(data.get('categories', []))}")
print(f"  variant_groups count: {len(data.get('variant_groups', []))}")

if items:
    first = items[0]
    print(f"\n  First item keys: {list(first.keys())}")
    print(f"  First item: {json.dumps(first, indent=2)[:500]}")
    
    # Show all items with id, name, price
    print(f"\n  All items with prices:")
    for item in items[:15]:
        iid = item.get('id', '?')
        name = item.get('name', '?')
        price = item.get('baseprice') or item.get('price', '?')
        print(f"    {iid} | {name[:50]} | {price}")
    
    # Save first complete item for reference
    with open('_wolt_hunt/_sample_item.json', 'w') as f:
        json.dump(first, f, indent=2)
    print(f"\n  Saved first item to _sample_item.json")
else:
    print("\n  Items is EMPTY! Checking categories for item_ids...")
    cats = data.get('categories', [])
    for cat in cats[:5]:
        print(f"  Category: {cat.get('name', cat.get('title', '?'))} | item_ids: {cat.get('item_ids', [])[:5]}")
    
    print("\n  Full data dump (first 2000 chars):")
    print(json.dumps(data, indent=2)[:2000])

print("\nDONE")

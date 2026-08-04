"""Instacart GraphQL deep probe + JS bundle analysis."""
import requests, re, json, os, base64, gzip

H = {
    'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/126.0.0.0 Safari/537.36',
    'Accept-Language': 'en-US,en;q=0.9',
    'Accept': 'application/json, */*',
}

BASE = 'https://www.instacart.com'
GQL = BASE + '/graphql'

# ===== 1. GRAPHQL INTROSPECTION =====
print("=" * 60)
print("=== 1. GRAPHQL INTROSPECTION ===")

introspection_query = """
query IntrospectionQuery {
  __schema {
    queryType { name }
    mutationType { name }
    subscriptionType { name }
    types {
      name
      kind
      description
      fields(includeDeprecated: true) { name description args { name type { name kind ofType { name kind } } } type { name kind ofType { name kind } } }
    }
  }
}
"""

# Try standard introspection
r = requests.post(GQL, headers={**H, 'Content-Type': 'application/json'},
                  json={'query': introspection_query}, timeout=15)
print(f"  Introspection: {r.status_code} | {len(r.text)} bytes")
print(f"  Response: {r.text[:800]}")

# Try Apollo-style GET introspection  
r2 = requests.get(GQL, headers={**H}, timeout=15)
print(f"\n  GET graphql: {r2.status_code} | {r2.text[:300]}")

# Try __type meta-field
r3 = requests.post(GQL, headers={**H, 'Content-Type': 'application/json'},
                   json={'query': '{ __typename }'}, timeout=10)
print(f"\n  __typename: {r3.status_code} | {r3.text[:300]}")

# Try schema via POST body
r4 = requests.post(GQL, headers={**H, 'Content-Type': 'application/json'},
                   json={'query': 'query { __schema { types { name } } }'}, timeout=10)
print(f"  __schema: {r4.status_code} | {r4.text[:500]}")

# ===== 2. GUESS COMMON QUERIES =====
print("\n" + "=" * 60)
print("=== 2. COMMON GRAPHQL QUERIES ===")

queries = [
    ('stores', '{ stores { id name } }'),
    ('store', '{ store(id: "1") { id name } }'),
    ('search', '{ search(query: "pizza") { id name } }'),
    ('me', '{ me { id email } }'),
    ('user', '{ user { id email } }'),
    ('viewer', '{ viewer { id } }'),
    ('products', '{ products { id name } }'),
    ('items', '{ items { id name } }'),
    ('categories', '{ categories { id name } }'),
    ('retailers', '{ retailers { id name } }'),
    ('delivery', '{ delivery { id } }'),
    ('cart', '{ cart { id } }'),
    ('orders', '{ orders { id } }'),
    ('shop', '{ shop { id name } }'),
    ('node', '{ node(id: "1") { id } }'),
]

for label, query in queries:
    try:
        r = requests.post(GQL, headers={**H, 'Content-Type': 'application/json'},
                         json={'query': query}, timeout=10)
        j = r.json()
        has_data = bool(j.get('data'))
        errs = j.get('errors', [])
        err_msg = errs[0].get('message', '')[:100] if errs else 'no error'
        print(f"  {label:15s} -> data={has_data} | {err_msg}")
    except Exception as e:
        print(f"  {label:15s} -> ERR: {str(e)[:80]}")

# ===== 3. API PATH PROBING =====
print("\n" + "=" * 60)
print("=== 3. DISCOVERED API PATHS ===")

api_paths = [
    '/v2/b',
    '/v8/store/hub',
    '/v1/', '/v2/', '/v3/', '/v4/', '/v5/', '/v6/', '/v7/', '/v8/',
    '/api/graphql', '/api/v3/', '/api/v4/',
    '/web/', '/web/v1/', '/web/v2/',
]

for path in api_paths:
    try:
        r = requests.get(BASE + path, headers=H, timeout=8, allow_redirects=False)
        ct = r.headers.get('content-type', '')[:40]
        j = None
        try: j = r.json()
        except: pass
        summary = str(j)[:200] if j else r.text[:150].replace('\n', ' ')
        if r.status_code not in [404, 403]:
            print(f"  GET {path:25s} -> {r.status_code} | {summary}")
        elif r.status_code != 404:
            print(f"  GET {path:25s} -> {r.status_code} | {ct} | {summary[:80]}")
    except Exception as e:
        pass

# ===== 4. JS BUNDLE DOWNLOAD + ANALYSIS =====
print("\n" + "=" * 60)
print("=== 4. JS BUNDLE ANALYSIS ===")

os.makedirs('D:/scan/_instacart_hunt/js', exist_ok=True)

# Read homepage to find JS bundles
html = requests.get(BASE + '/', headers=H, timeout=15).text

# Find all rspack bundles
bundles = set()
for m in re.finditer(r'https?://[^"]+?/assets/rspack/[^"]+\.js', html):
    bundles.add(m.group(0))
for m in re.finditer(r'(/assets/[^"\'\s]+\.js)', html):
    if 'cloudfront' in m.group(1) or 'rspack' in m.group(1):
        bundles.add(m.group(1) if m.group(1).startswith('http') else BASE + m.group(1))

print(f"  Found {len(bundles)} rspack bundles")

# Download a few key bundles and search for API patterns
key_terms = ['graphql', 'api/v', 'fetch(', 'axios', 'query', 'mutation', 'apollo', 'endpoint', 'baseURL', 'base_url', 'instacart.com', 'accessToken', 'apiKey', 'x-instacart']

downloaded = 0
all_findings = {}

for url in sorted(bundles)[:12]:
    try:
        r = requests.get(url, headers=H, timeout=20)
        filename = url.split('/')[-1].split('?')[0]
        filepath = f'D:/scan/_instacart_hunt/js/{filename}'
        with open(filepath, 'wb') as f:
            f.write(r.content)
        
        # Search for key terms
        text = r.text
        findings = {}
        for term in key_terms:
            matches = list(re.finditer(re.escape(term), text, re.I))
            if matches:
                findings[term] = len(matches)
                if term in ['graphql', 'api/v', 'endpoint', 'baseURL', 'base_url'] and matches:
                    for m_match in matches[:5]:
                        ctx = text[max(0, m_match.start()-80):m_match.end()+80]
                        findings[f'{term}_ctx'] = findings.get(f'{term}_ctx', []) + [ctx]
        
        if findings:
            all_findings[filename] = findings
            print(f"\n  [{filename}] ({len(text)} chars)")
            for k, v in findings.items():
                if not k.endswith('_ctx'):
                    print(f"    {k}: {v} occurrences")
                else:
                    for ctx in v[:3]:
                        print(f"    -> {ctx.strip()[:150]}")
        
        downloaded += 1
    except Exception as e:
        print(f"  SKIP {url.split('/')[-1][:40]}: {str(e)[:50]}")

# ===== 5. TRY POST TO DISCOVERED ENDPOINTS =====
print("\n" + "=" * 60)
print("=== 5. POST PROBES ===")

post_tests = [
    ('/v2/b', {'operationName': 'GetStores', 'variables': {}}),
    ('/v8/store/hub', {'store_id': '1'}),
    ('/graphql', {'operationName': 'GetStore', 'variables': {'id': '1'}, 'query': 'query GetStore($id: ID!) { store(id: $id) { id name } }'}),
]

for path, body in post_tests:
    try:
        r = requests.post(BASE + path, headers={**H, 'Content-Type': 'application/json'},
                         json=body, timeout=10)
        j = None
        try: j = r.json()
        except: pass
        print(f"  POST {path:25s} -> {r.status_code} | {str(j)[:300] if j else r.text[:150]}")
    except Exception as e:
        print(f"  POST {path:25s} -> ERR: {str(e)[:80]}")

print("\n=== DONE ===")

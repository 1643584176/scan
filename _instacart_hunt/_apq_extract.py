"""Instacart: Extract Apollo Persisted Queries from JS bundles."""
import requests, re, json, os, hashlib

H = {
    'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/126.0.0.0 Safari/537.36',
    'Accept': '*/*',
}

BASE = 'https://www.instacart.com'
GQL = BASE + '/graphql'
os.makedirs('D:/scan/_instacart_hunt/js', exist_ok=True)

# Download main bundle
MAIN_JS_URL = 'https://d2guulkeunn7d8.cloudfront.net/assets/rspack/4439.webpack_bundle-ab1e62a5de88a0fa-v3.js'
print(f"Downloading main bundle...")
r = requests.get(MAIN_JS_URL, headers=H, timeout=30)
main_js = r.text
print(f"  Size: {len(main_js)} chars")

with open('D:/scan/_instacart_hunt/js/4439_main.js', 'w', encoding='utf-8') as f:
    f.write(main_js)

# ===== 1. Find Apollo persisted query patterns =====
print("\n=== 1. PERSISTED QUERY PATTERNS ===")

# Pattern 1: sha256Hash literal
sha256_hashes = set()
for m in re.finditer(r'sha256Hash["\s:]+["\']([a-f0-9]{64})["\']', main_js, re.I):
    sha256_hashes.add(m.group(1))
print(f"  sha256Hash literals: {len(sha256_hashes)}")

# Pattern 2: persistedQuery objects
pq_objects = set()
for m in re.finditer(r'persistedQuery["\s:]*{[^}]+}', main_js, re.I):
    pq_objects.add(m.group(0)[:200])

# Pattern 3: Find gql`...` template literals (GraphQL queries)
gql_queries = []
for m in re.finditer(r'gql\s*`((?:[^`\\]|\\.)*)`', main_js):
    gql_queries.append(m.group(1))

# Pattern 4: Find GraphQL document strings (query/mutation definitions)
doc_strings = []
for m in re.finditer(r'["\']\s*(?:query|mutation|fragment)\s+\w+[^"\']{50,2000}?\s*["\']', main_js, re.I):
    doc_strings.append(m.group(0))

print(f"  gql template literals: {len(gql_queries)}")
print(f"  GraphQL doc strings: {len(doc_strings)}")

# ===== 2. Try to find query document -> hash mapping =====
print("\n=== 2. QUERY DOCUMENT EXTRACTION ===")

# Look for query strings with their operation names
query_blocks = []
for m in re.finditer(r'(?:query|mutation)\s+(\w+)[^}]*?(?:query|mutation)\s+\w+\s*(?:\([^)]*\))?\s*\{', main_js):
    start = m.start()
    # Try to find the matching closing brace context
    snippet = main_js[start:start+1000]
    query_blocks.append(snippet[:300])

print(f"  Query blocks: {len(query_blocks)}")
for qb in query_blocks[:5]:
    print(f"    {qb.strip()[:200]}")

# ===== 3. Try Persisted Query protocol =====
print("\n=== 3. APQ PROTOCOL TEST ===")

# Test with just hash (no full query) - this is the normal APQ flow
test_hashes = list(sha256_hashes)[:10]
for h in test_hashes[:5]:
    body = {
        "operationName": None,
        "variables": {},
        "extensions": {
            "persistedQuery": {
                "version": 1,
                "sha256Hash": h
            }
        }
    }
    r = requests.post(GQL, headers={**H, 'Content-Type': 'application/json'},
                     json=body, timeout=10)
    j = r.json()
    err = j.get('errors', [{}])[0].get('message', '')[:100]
    print(f"  {h[:20]}... -> {r.status_code} | {err[:120]}")

# ===== 4. Search for API endpoints and domains =====
print("\n=== 4. API ENDPOINT/URL EXTRACTION ===")

# Find all api URLs
api_urls = set()
for m in re.finditer(r'https?://[a-zA-Z0-9][-a-zA-Z0-9]*(?:\.[a-zA-Z0-9][-a-zA-Z0-9]*)+/[a-zA-Z0-9_/.-]{3,80}', main_js):
    url = m.group(0)
    if any(kw in url.lower() for kw in ['instacart', 'api', 'graphql', 'v1/', 'v2/', 'v3/', 'v4/', 'v5/', 'v6/', 'v7/', 'v8/']):
        api_urls.add(url)

# Find path patterns
path_patterns = set()
for m in re.finditer(r'["\'\`](/[a-zA-Z0-9_/.-]{5,100})["\'\`]', main_js):
    path = m.group(1)
    if any(kw in path for kw in ['api', 'graphql', 'v1/', 'v2/', 'v3/', 'v4/', '/v5/', '/v6/', '/v7/', '/v8/', 'store', 'search', 'order', 'checkout', 'cart']):
        path_patterns.add(path)

print(f"  API URLs: {len(api_urls)}")
for u in sorted(api_urls)[:30]:
    print(f"    {u}")
print(f"\n  API paths: {len(path_patterns)}")
for p in sorted(path_patterns)[:30]:
    print(f"    {p}")

# ===== 5. Try POST with APQ hash + full query =====
print("\n=== 5. APQ WITH FULL QUERY ===")

# Send hash + full query document together
for h in test_hashes[:3]:
    body = {
        "operationName": None,
        "variables": {},
        "query": "query { __typename }",
        "extensions": {
            "persistedQuery": {
                "version": 1,
                "sha256Hash": h
            }
        }
    }
    r = requests.post(GQL, headers={**H, 'Content-Type': 'application/json'},
                     json=body, timeout=10)
    j = r.json()
    print(f"  hash={h[:20]}... + query -> {r.status_code} | {str(j)[:200]}")

# ===== 6. Try without APQ, just query in extensions =====
print("\n=== 6. RAW QUERY (NO APQ) ===")
body = {
    "operationName": "IntrospectionQuery",
    "query": "query IntrospectionQuery { __schema { queryType { name } mutationType { name } } }",
    "variables": {}
}
r = requests.post(GQL, headers={**H, 'Content-Type': 'application/json'},
                 json=body, timeout=10)
print(f"  Raw query: {r.status_code} | {r.text[:300]}")

# ===== 7. Extract GraphQL operations with their operation names =====
print("\n=== 7. OPERATION NAME EXTRACTION ===")

op_names = set()
for m in re.finditer(r'operationName["\s:]+["\']([A-Za-z]\w*)["\']', main_js):
    op_names.add(m.group(1))
print(f"  Operation names: {len(op_names)}")
for n in sorted(op_names)[:30]:
    print(f"    {n}")

# ===== 8. Try operationName-based query =====
print("\n=== 8. OPERATION NAME QUERIES ===")
for op_name in sorted(op_names)[:10]:
    body = {
        "operationName": op_name,
        "variables": {},
        "extensions": {
            "persistedQuery": {
                "version": 1,
                "sha256Hash": "0000000000000000000000000000000000000000000000000000000000000000"
            }
        }
    }
    r = requests.post(GQL, headers={**H, 'Content-Type': 'application/json'},
                     json=body, timeout=10)
    j = r.json()
    err = j.get('errors', [{}])[0].get('message', '')[:120]
    if 'not found' not in err.lower():
        print(f"  {op_name:30s} -> {r.status_code} | {err[:120]}")

print("\n=== DONE ===")

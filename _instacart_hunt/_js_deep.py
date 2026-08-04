"""Instacart: Deep JS Chunk Analysis - look for persisted query config and operation documents."""
import requests, re, json, os

H = {'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36'}

# Key chunks to analyze (those with query/mutation/fetch references)
KEY_CHUNKS = [
    'https://d2guulkeunn7d8.cloudfront.net/assets/rspack/2377-f68887902e815b20-v3.webpack_chunk.js',
    'https://d2guulkeunn7d8.cloudfront.net/assets/rspack/3382-d1d7b0ab64135d85-v3.webpack_chunk.js',
    'https://d2guulkeunn7d8.cloudfront.net/assets/rspack/3721-45add71d55a706a2-v3.webpack_chunk.js',
    'https://d2guulkeunn7d8.cloudfront.net/assets/rspack/2771-e8fc872259d94acf-v3.webpack_chunk.js',
]

# Search patterns
PATTERNS = {
    'persistedQuery_config': [r'persistedQueries', r'createPersistedQueryLink', r'PersistedQueryLink',
                              r'persistedQuery', r'sha256', r'generateHash', r'createHash'],
    'apollo_config': [r'new ApolloClient', r'createHttpLink', r'HttpLink', r'ApolloLink',
                      r'InMemoryCache', r'ApolloProvider', r'useQuery', r'useMutation'],
    'graphql_operations': [r'gql`', r'graphql`', r'query\s+\w+\s*\(', r'mutation\s+\w+\s*\('],
    'api_urls': [r'https?://[a-z0-9.-]+\.instacart\.com', r'https?://[a-z0-9.-]+\.instacart\.', r'api\.instacart'],
    'endpoints': [r'"/[a-z0-9_-]+/[a-z0-9/_-]+"', r"'/[a-z0-9_-]+/[a-z0-9/_-]+'"],
    'auth': [r'accessToken', r'apiKey', r'x-api-key', r'Authorization', r'bearer', r'sessionToken'],
}

GQL = 'https://www.instacart.com/graphql'

for chunk_url in KEY_CHUNKS:
    filename = chunk_url.split('/')[-1]
    print(f"\n{'='*70}")
    print(f"=== {filename} ===")
    
    r = requests.get(chunk_url, headers=H, timeout=20)
    text = r.text
    print(f"  Size: {len(text)} chars")
    
    # Save
    with open(f'D:/scan/_instacart_hunt/js/{filename}', 'w', encoding='utf-8') as f:
        f.write(text)
    
    for category, patterns in PATTERNS.items():
        found = False
        for pat in patterns:
            matches = list(re.finditer(pat, text, re.I))
            if matches:
                if not found:
                    print(f"\n  [{category}]")
                    found = True
                for m in matches[:5]:
                    ctx = text[max(0,m.start()-100):m.end()+100]
                    ctx_clean = ctx.replace('\n', ' ')[:200]
                    print(f"    [{pat}] -> {ctx_clean}")

# Also try: find query hashes in all downloaded files
print(f"\n{'='*70}")
print("=== CROSS-FILE SHA256 HASH SEARCH ===")

for fn in os.listdir('D:/scan/_instacart_hunt/js/'):
    if not fn.endswith('.js'):
        continue
    text = open(f'D:/scan/_instacart_hunt/js/{fn}', encoding='utf-8', errors='replace').read()
    hashes = set(re.findall(r'[a-f0-9]{64}', text, re.I))
    if hashes and len(hashes) < 50:  # Skip if too many (false positives)
        print(f"  {fn}: {len(hashes)} potential sha256 hashes")
        for h in list(hashes)[:3]:
            print(f"    {h}")

# ===== Try Instacart's actual API pattern =====
print(f"\n{'='*70}")
print("=== INSTACART API FUZZING ===")

# Try different GraphQL paths
gql_urls = [
    'https://www.instacart.com/graphql',
    'https://www.instacart.com/api/graphql',
    'https://www.instacart.com/v3/graphql',
]

for url in gql_urls:
    # Try POST with just operationName + variables (standard persisted query)
    body = {"operationName": "GetStoreHomepage", "variables": {}}
    r = requests.post(url, headers={**H, 'Content-Type': 'application/json'}, json=body, timeout=10)
    print(f"  {url.split('/')[-3]}/graphql: {r.status_code} | {r.text[:200]}")

# Try v8/store/hub with different paths
store_paths = [
    'https://www.instacart.com/v8/store/hub',
    'https://www.instacart.com/v8/store',
    'https://www.instacart.com/v3/store',
]
for url in store_paths:
    r = requests.get(url, headers=H, timeout=8, allow_redirects=False)
    print(f"  GET {url}: {r.status_code} | {r.text[:120].replace(chr(10),' ')}")

print("\n=== DONE ===")

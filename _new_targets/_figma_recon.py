"""Figma HIGH-severity hunting - unauthenticated recon + api.figma.com fuzzing."""
import requests, re, json, os, urllib.parse

H = {
    'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36',
    'Accept': 'text/html,application/xhtml+xml,application/xml;q=0.9,*/*;q=0.8',
    'Accept-Language': 'en-US,en;q=0.9',
}
OUT = 'D:/scan/_new_targets/figma'
os.makedirs(OUT, exist_ok=True)

def get(url, **kw):
    return requests.get(url, headers=H, timeout=15, allow_redirects=False, **kw)

def post(url, body=None, json_body=None, extra_h=None):
    h = {**H}
    if extra_h: h.update(extra_h)
    if json_body is not None:
        r = requests.post(url, headers={**h, 'Content-Type': 'application/json'}, json=json_body, timeout=15, allow_redirects=False)
    elif body:
        r = requests.post(url, headers={**h, 'Content-Type': 'application/x-www-form-urlencoded'}, data=body, timeout=15, allow_redirects=False)
    else:
        r = requests.post(url, headers=h, timeout=15, allow_redirects=False)
    return r

print("="*60)
print("=== FIGMA HIGH-SEVERITY HUNT ===")

# ======== PHASE 1: Homepage Recon ========
print("\n--- PHASE 1: Homepage ---")
r = get('https://www.figma.com/')
html = r.text
print(f"Status: {r.status_code} | Size: {len(html)} | Final URL: {r.url}")
print(f"X-Frame-Options: {r.headers.get('x-frame-options','none')}")
print(f"CSP: {r.headers.get('content-security-policy','none')[:200]}")

with open(f'{OUT}/homepage.html', 'w', encoding='utf-8') as f: f.write(html)

# Extract all JS bundles
js_urls = set()
for m in re.finditer(r'<script[^>]*src="([^"]+)"', html):
    url = m.group(1)
    if url.startswith('//'): url = 'https:' + url
    elif url.startswith('/'): url = 'https://www.figma.com' + url
    js_urls.add(url)
# Also find webpack chunks
for m in re.finditer(r'["\'](/[^"\'\s]{5,}\.js[^"\'\s]*)["\']', html):
    url = 'https://www.figma.com' + m.group(1) if m.group(1).startswith('/') else m.group(1)
    js_urls.add(url)
print(f"JS bundles found: {len(js_urls)}")

# Download ALL JS bundles and search for API endpoints
all_js = []
api_urls = set()
for url in sorted(js_urls):
    try:
        r = get(url)
        if r.status_code == 200 and len(r.text) > 200:
            fn = urllib.parse.urlparse(url).path.split('/')[-1][:80]
            with open(f'{OUT}/{fn}', 'w', encoding='utf-8') as f: f.write(r.text)
            all_js.append(r.text)
            # Extract API URLs
            txt = r.text
            for m in re.finditer(r'(https?://(?:api|www)\.figma\.com/[^"\'\\s]{3,120})', txt):
                api_urls.add(m.group(1))
            for m in re.finditer(r'["\'`](/api/[^"\'`\\s]{3,120})["\'`]', txt):
                api_urls.add('https://www.figma.com' + m.group(1))
            for m in re.finditer(r'https?://[a-z][a-z0-9-]*\.figma\.com/[^"\'\\s]{2,80}', txt):
                api_urls.add(m.group(1))
    except: pass
print(f"Downloaded: {len(all_js)} bundles")
print(f"API URLs extracted: {len(api_urls)}")
for u in sorted(api_urls)[:30]:
    print(f"  {u}")

# ======== PHASE 2: api.figma.com Deep Probe ========
print("\n--- PHASE 2: api.figma.com Deep Probe ---")

# Paths that might leak data without auth
HIGH_VALUE_PATHS = [
    # Public/file access (BIG $$$ if unauthenticated)
    '/api/figma-oauth',
    '/v1/files/', '/v1/files/popular', '/v1/files/recent',
    '/v1/projects/', '/v1/teams/', '/v1/community/',
    '/v1/users/', '/v1/me',
    '/v1/search', '/v1/search/files',
    # OAuth (info disclosure)
    '/.well-known/openid-configuration',
    '/.well-known/oauth-authorization-server',
    # Health/info endpoints
    '/health', '/ping', '/status', '/version',
    '/api/status', '/api/health',
    # GraphQL
    '/graphql', '/api/graphql',
    '/v1/graphql', '/v2/graphql',
    # Common API paths
    '/v1/', '/v2/', '/v3/',
    '/api/v1/', '/api/v2/',
    '/api/rest/', '/api/public/',
    # FigJam
    '/api/figjam/', '/v1/figjam/',
    # File-related (potential info leak)
    '/v1/files/', '/v1/files/community',
    '/v1/community/files', '/v1/community/projects',
    '/api/community/',
    # Webhooks
    '/v1/webhooks/', '/api/webhooks/',
    # Plugin API
    '/v1/plugins/', '/v1/plugin/', '/api/plugins/',
    # Comments
    '/v1/comments/', '/api/comments/',
    # Internal
    '/internal/', '/debug/', '/admin/',
    '/api/internal/', '/api/debug/',
    '/swagger', '/openapi', '/docs',
    # Metrics
    '/metrics', '/api/metrics',
    # File export
    '/v1/images/', '/v1/exports/',
    # Teams/orgs
    '/v1/orgs/', '/v1/team/',
    # Library
    '/v1/library/', '/v1/styles/', '/v1/components/',
]

BASE_API = 'https://api.figma.com'
results = []

for path in HIGH_VALUE_PATHS:
    url = BASE_API + path
    try:
        r = get(url)
        ct = r.headers.get('content-type', '')[:50]
        body = r.text[:200].replace('\n', ' ')
        results.append((r.status_code, len(r.text), path, ct, body))
    except Exception as e:
        results.append((0, 0, path, 'ERR', str(e)[:50]))

# Print interesting results (non-404, non-403)
for code, size, path, ct, body in results:
    if code not in (404, 403) or size > 200:
        label = '🔴' if code in (200,301,302) else '🟡' if code in (400,401,405) else '⚪'
        print(f"  {label} {path:45s} -> {code:3d} | {size:5d}B | {ct[:40]} | {body[:100]}")

# ======== PHASE 3: www.figma.com API Probe ========
print("\n--- PHASE 3: www.figma.com API Probe ---")
BASE_WWW = 'https://www.figma.com'

www_paths = [
    '/api/', '/api/auth/', '/api/session/',
    '/api/user/', '/api/user/session',
    '/api/public/',
    '/graphql', '/api/graphql',
    '/api/files/', '/api/projects/',
    '/api/community/', '/api/teams/',
    '/api/search/',
    '/api/figjam/',
    '/file/', '/files/',
    '/@me', '/community',
]

for path in www_paths:
    try:
        r = get(BASE_WWW + path)
        code = r.status_code
        loc = r.headers.get('location', '')
        ct = r.headers.get('content-type', '')[:40]
        body = r.text[:120].replace('\n', ' ')
        if code not in (404,):
            print(f"  {code:3d} {path:30s} -> {ct} | loc={loc[:50]} | {body[:80]}")
    except Exception as e:
        print(f"  ERR {path:30s} -> {str(e)[:50]}")

# ======== PHASE 4: Subdomain Discovery ========
print("\n--- PHASE 4: Subdomain Probe ---")
subdomains = [
    'https://blog.figma.com/',
    'https://help.figma.com/',
    'https://status.figma.com/',
    'https://spectrum.figma.com/',
    'https://assets.figma.com/',
    'https://static.figma.com/',
    'https://cdn.figma.com/',
    'https://files.figma.com/',
    'https://uploads.figma.com/',
    'https://s3-alpha.figma.com/',
    'https://s3-alpha-sig.figma.com/',
    'https://www.figma.com/file/',
    'https://www.figma.com/community/',
    'https://www.figma.com/figjam/',
    'https://figma.com/',
]

for url in subdomains:
    try:
        r = get(url)
        ct = str(r.headers.get('content-type', ''))[:40]
        print(f"  {url:50s} -> {r.status_code:3d} | {ct} | {r.text[:80].replace(chr(10),' ')}")
    except Exception as e:
        print(f"  {url:50s} -> ERR: {str(e)[:50]}")

# ======== PHASE 5: JS Deep Analysis ========
print(f"\n--- PHASE 5: JS Deep Analysis ---")
combined = '\n'.join(all_js)

# Look for high-value patterns
patterns = {
    'graphql_queries': r'(?:query|mutation)\s+(\w+)',
    'api_keys': r'(?:apiKey|api_key|API_KEY)["\s:=]+["\']([^"\']{8,60})["\']',
    'auth_tokens': r'(?:accessToken|access_token|authToken)["\s:=]+["\']([^"\']{8,})["\']',
    'internal_endpoints': r'(?:figma\.com)?(/api/internal/[^"\'\s]{4,80})',
    'file_ids': r'(?:fileId|file_id|fileKey)["\s:=]+["\']([a-zA-Z0-9]{10,30})["\']',
    's3_buckets': r'(https?://[a-z0-9-]+\.s3[.-][^"\'\s]+)',
    'oauth_client_id': r'(?:clientId|CLIENT_ID|client_id)["\s:=]+["\']([^"\']{8,60})["\']',
    'ws_endpoints': r'(wss?://[^"\'\s]{6,80})',
    'graphql_endpoints': r'(https?://[^"\'\s]*graphql[^"\'\s]{0,30})',
    'redirect_uri': r'(?:redirectUri|redirect_uri|REDIRECT_URI)["\s:=]+["\']([^"\']{8,})["\']',
}

for name, pat in patterns.items():
    matches = list(re.finditer(pat, combined, re.I))
    if matches:
        values = set()
        for m in matches:
            val = m.group(1) if m.lastindex else m.group(0)
            values.add(val)
        print(f"  [{name}]: {len(matches)} matches, {len(values)} unique")
        for v in sorted(values)[:10]:
            print(f"    {v[:100]}")

# ======== PHASE 6: CORS/CSRF ========
print(f"\n--- PHASE 6: CORS Test ---")
for url in [BASE_API + '/', BASE_API + '/v1/', BASE_WWW + '/api/']:
    try:
        r = requests.options(url, headers={
            **H, 'Origin': 'https://evil.com',
            'Access-Control-Request-Method': 'GET',
        }, timeout=8)
        acao = r.headers.get('Access-Control-Allow-Origin', '')
        acac = r.headers.get('Access-Control-Allow-Credentials', '')
        if acao:
            print(f"  CORS: {url:50s} -> ACAO={acao} | ACAC={acac}")
    except: pass

print(f"\n=== RECON DONE ===")
print(f"Output saved to: {OUT}/")

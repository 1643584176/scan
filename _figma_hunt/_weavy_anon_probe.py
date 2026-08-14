import sys, io, json, urllib.request, urllib.error
sys.stdout.reconfigure(encoding="utf-8", errors="replace")
BASE = "https://api.weavy.ai/api"
ENDPOINTS = [
    ("GET", "/v1/community/categories"),
    ("GET", "/v1/figma-eligible-plans"),
    ("GET", "/v1/models/prices"),
    ("GET", "/v1/security/tier"),
    ("GET", "/v1/community/handle-availability?handle=test"),
    ("GET", "/v1/node-definitions/public"),
    ("GET", "/v1/credits/window-status"),
    ("GET", "/v1/analytics/members-report"),
    ("GET", "/v1/analytics/usage-report"),
    ("GET", "/v1/folders"),
    ("GET", "/v1/projects"),
    ("GET", "/v1/recipes"),
    ("POST", "/v1/accounts:lookup"),
    ("GET", "/v1/community/publisher-profiles"),
    ("GET", "/v1/figma-node/file-name"),
    ("GET", "/v1/figma-node/file-status"),
]
UA = "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/151.0.0.0 Safari/537.36"
for method, path in ENDPOINTS:
    req = urllib.request.Request(BASE + path, method=method,
                                 headers={"User-Agent": UA, "Origin": "https://app.weavy.ai",
                                          "Accept": "application/json"})
    try:
        r = urllib.request.urlopen(req, timeout=12)
        body = r.read(500).decode("utf-8", "replace")
        print(f"[{method} {path}] {r.status} len={r.headers.get('content-length','?')} :: {body[:180]}")
    except urllib.error.HTTPError as e:
        body = e.read(300).decode("utf-8", "replace")
        print(f"[{method} {path}] {e.code} :: {body[:180]}")
    except Exception as e:
        print(f"[{method} {path}] ❌ {type(e).__name__}: {str(e)[:80]}")

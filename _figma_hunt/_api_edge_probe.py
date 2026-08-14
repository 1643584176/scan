"""高价值端点认证边界探测:匿名 vs B 登录态
端点来源:js_editor/999 chunk(eZ/e3/e0 封装定义)
"""
import sys, io, json, urllib.request, urllib.parse
sys.stdout.reconfigure(encoding="utf-8", errors="replace")

CK_B = io.open('ws_cookie_B_new.txt', encoding='utf-8').read().strip()
UA = "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/151.0.0.0 Safari/537.36"

ENDPOINTS = [
    ("GET",  "/api/cortex/mcp/list_tools", None),
    ("GET",  "/api/cortex/mcp/check_auth", None),
    ("POST", "/api/cortex/shared/mcp_call_tool", {}),
    ("POST", "/api/cortex/foundry/fs-read-file", {}),
    ("POST", "/api/cortex/foundry/fs-snapshot", {}),
    ("GET",  "/api/cortex/foundry/files", None),
    ("POST", "/api/cortex/foundry/sandbox", {}),
    ("GET",  "/api/cortex/make/ai_gateway_token", None),
    ("POST", "/api/cortex/dev/request_response_logs/get_request_response_logs", {}),
    ("GET",  "/api/cortex/weave/inspect", None),
    ("GET",  "/api/figment-proxy", None),
    ("GET",  "/api/figment-proxy/monitor", None),
    ("GET",  "/api/integrations/supabase/authorize", None),
    ("GET",  "/api/cortex/foundry/debug-sandbox-status", None),
    ("GET",  "/api/cortex/foundry/fs-read-file", None),
]

def probe(label, cookie=None):
    print(f"\n===== {label} =====")
    for method, path, body in ENDPOINTS:
        hdrs = {"User-Agent": UA, "Accept": "application/json", "Origin": "https://www.figma.com",
                "Referer": "https://www.figma.com/"}
        data = None
        if body is not None:
            hdrs["Content-Type"] = "application/json"
            data = json.dumps(body).encode()
        if cookie:
            hdrs["Cookie"] = cookie
        req = urllib.request.Request("https://www.figma.com" + path, data=data, headers=hdrs, method=method)
        try:
            r = urllib.request.urlopen(req, timeout=12)
            resp = r.read().decode(errors='replace')
            print(f"  {method:4s} {path:70s} {r.status}  {len(resp)}B  {resp[:120]}")
        except urllib.error.HTTPError as e:
            resp = e.read().decode(errors='replace')
            print(f"  {method:4s} {path:70s} {e.code}  {resp[:140]}")
        except Exception as e:
            print(f"  {method:4s} {path:70s} !! {type(e).__name__} {str(e)[:60]}")

probe("匿名")
probe("B 登录态", CK_B)

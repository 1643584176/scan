"""MCP REST 端点权限契约探测
目标:POST /api/mcp/servers 创建服务器是否校验 plan 权限;mcpClients 读写契约
技巧:空 body → 400 typechecking 泄露必填参数;A/B 跨账号对比
"""
import sys, json, io, requests
sys.stdout.reconfigure(encoding="utf-8", errors="replace")

CK_A = io.open('ws_cookie_A_new.txt', encoding='utf-8').read().strip()
CK_B = io.open('ws_cookie_B_new.txt', encoding='utf-8').read().strip()
UA = "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/151.0.0.0 Safari/537.36"

def probe(label, method, path, cookie, body=None, extra=None):
    url = f"https://www.figma.com{path}"
    h = {"User-Agent": UA, "Accept": "application/json", "Origin": "https://www.figma.com",
         "Referer": "https://www.figma.com/", "Cookie": cookie}
    if body is not None:
        h["Content-Type"] = "application/json"
    try:
        r = requests.request(method, url, headers=h, json=body if body is not None else None,
                             timeout=20, allow_redirects=False)
        t = r.text
        print(f"[{label}] {method} {path} -> {r.status_code} ({len(t)}B)")
        print(f"    {t[:400]}")
    except Exception as e:
        print(f"[{label}] {method} {path} -> ERR {type(e).__name__}: {str(e)[:80]}")

if __name__ == "__main__":
    print("======== MCP REST 契约探测 ========")
    # 1. GET 基线
    probe("A", "GET", "/api/mcp/servers/", CK_A)
    # 2. POST 空 body 泄露参数契约
    probe("A", "POST", "/api/mcp/servers", CK_A, body={})
    # 3. PUT clients 契约
    probe("A", "PUT", "/api/mcp/clients/", CK_A, body={})
    # 4. B 重复对比
    probe("B", "POST", "/api/mcp/servers", CK_B, body={})
    probe("B", "PUT", "/api/mcp/clients/", CK_B, body={})

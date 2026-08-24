# -*- coding: utf-8 -*-
"""MCP server 读取接口访问控制 + 创建参数修正探测"""
import io, json, sys, urllib.error, urllib.request
sys.stdout.reconfigure(encoding='utf-8', errors='replace')

BASE = "https://www.figma.com"
A_UID = "1666382703778278399"
B_UID = "1667396392129259941"
UA = "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 Chrome/151.0.0.0 Safari/537.36"
PUB_SERVER = "322e5eb8-8034-4995-9d16-05bc2b54ee8b"   # Granola(public)
FAKE_SERVER = "ffffffff-ffff-4fff-9fff-ffffffffffff"


def load(path):
    return io.open(path, encoding='utf-8').read().strip().replace('\n', '; ')


AC = load('ws_cookie_A_new.txt')
BC = load('ws_cookie_B_new.txt')


def call(label, method, path, uid, ck, body=None):
    headers = {"User-Agent": UA, "Accept": "application/json", "Origin": BASE,
               "Referer": BASE + "/", "Cookie": ck, "X-Figma-User-ID": uid}
    data = None
    if body is not None:
        headers["Content-Type"] = "application/json"
        data = json.dumps(body).encode()
    req = urllib.request.Request(BASE + path, method=method, headers=headers, data=data)
    try:
        with urllib.request.urlopen(req, timeout=25) as r:
            raw = r.read().decode(errors='replace')
            print(f"[{label}] HTTP {r.status} {raw[:800]}")
            return r.status, raw
    except urllib.error.HTTPError as e:
        raw = e.read().decode(errors='replace')
        print(f"[{label}] HTTP {e.code} {raw[:800]}")
        return e.code, raw


print("======== 读取接口访问控制 ========")
call("anon read public server", "GET", f"/api/mcp/servers/{PUB_SERVER}")
call("B read public server", "GET", f"/api/mcp/servers/{PUB_SERVER}", B_UID, BC)
call("A read public server", "GET", f"/api/mcp/servers/{PUB_SERVER}", A_UID, AC)
call("B read fake server", "GET", f"/api/mcp/servers/{FAKE_SERVER}", B_UID, BC)

print()
print("======== 创建参数修正 ========")
for label, body in (
    ("A snake_case file_key", {"name": "h1-probe", "url": "https://example.com/mcp", "file_key": "5zb5YkoxMa09KpqOyuLcHD"}),
    ("A no headers", {"name": "h1-probe", "url": "https://example.com/mcp", "fileKey": "5zb5YkoxMa09KpqOyuLcHD"}),
):
    call(label, "POST", "/api/mcp/servers", A_UID, AC, body)

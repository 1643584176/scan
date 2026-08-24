# -*- coding: utf-8 -*-
"""MCP 细节面探针:B 登录,验证 plan 级资源与 token 交换的归属校验
- getMcpToolUsage: GET /api/plans/{planId}/mcp_usage (planId 为资源定位,测归属校验)
- sessionTokenExchange: POST /api/mcp/session_token_exchange (client 参数细节)
"""
import io, json, sys, urllib.error, urllib.request
sys.stdout.reconfigure(encoding='utf-8', errors='replace')

BASE = "https://www.figma.com"
A_UID = "1666382703778278399"
B_UID = "1667396392129259941"
UA = "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 Chrome/151.0.0.0 Safari/537.36"
A_PLAN = "cc6b6125-a07f-4d39-a54c-50ef65f33919"   # A 的 plan(来自 _lg_mcp_connectors_dbg_out)
PUB_PLAN = "3fc8b88e-5cb5-4f50-9034-2f341d43ed12"  # 公开文件1的 planRecordId(来自 _lg_mcp_scan_out)
RANDOM_PLAN = "00000000-0000-4000-8000-000000000000"


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
            return r.status, raw
    except urllib.error.HTTPError as e:
        raw = e.read().decode(errors='replace')
        return e.code, raw


print("======== getMcpToolUsage: /api/plans/{planId}/mcp_usage ========")
for plan in (A_PLAN, PUB_PLAN, RANDOM_PLAN):
    for label, uid, ck in (("B", B_UID, BC), ("A", A_UID, AC)):
        status, raw = call(f"{label}→plan:{plan[:8]}", "GET", f"/api/plans/{plan}/mcp_usage", uid, ck)
        print(f"[{label}→{plan[:8]}] HTTP {status} len={len(raw)} body={raw[:400]}")

print()
print("======== sessionTokenExchange: client 参数细节 ========")
for client in ("MCP_CLIENT_DESKTOP_PROXY", "MCP_CLIENT_WEB", "random_unknown_client", "attacker_controlled"):
    status, raw = call("B", "POST", "/api/mcp/session_token_exchange", B_UID, BC, {"client": client})
    body = raw[:500]
    # 脱敏打印 token
    try:
        parsed = json.loads(raw)
        meta = parsed.get("meta") or {}
        if meta.get("access_token"):
            body = json.dumps({k: (v[:12] + "…(redacted)" if k == "access_token" else v) for k, v in meta.items()}, ensure_ascii=False)
    except Exception:
        pass
    print(f"[B client={client}] HTTP {status} body={body}")

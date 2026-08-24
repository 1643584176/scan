# 实验J118: interactive token 跨沙箱复用 + 失效性 + 协议探测
# 动机: j117 确认 wss 认证存在(401); 核心问题=token 是否绑定 session(跨沙箱复用=任意沙箱接管)
import json, time, urllib.request, urllib.error, sys, ssl
try:
    sys.stdout.reconfigure(encoding='utf-8', errors='replace')
except Exception:
    pass

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

import websocket

def ws_try(url, payload=None, timeout=5, label=""):
    try:
        ws = websocket.create_connection(url, timeout=timeout,
                                         sslopt={"cert_reqs": ssl.CERT_NONE, "check_hostname": False})
        print(f"  [{label}] CONNECTED", flush=True)
        if payload is not None:
            ws.send(payload)
            print(f"  [{label}] sent {payload[:80]!r}", flush=True)
        msgs = []
        try:
            while True:
                m = ws.recv()
                msgs.append(m)
                print(f"  [{label}] recv: {m[:200]!r}", flush=True)
                if len(msgs) >= 3:
                    break
        except websocket.WebSocketTimeoutException:
            print(f"  [{label}] recv timeout ({len(msgs)} msgs)", flush=True)
        except Exception as e:
            print(f"  [{label}] recv end: {type(e).__name__}: {e}", flush=True)
        ws.close()
        return True, msgs
    except websocket.WebSocketBadStatusException as e:
        print(f"  [{label}] HTTP {e.status_code}", flush=True)
        return False, []
    except Exception as e:
        print(f"  [{label}] FAIL {type(e).__name__}: {e}", flush=True)
        return False, []

def make_sandbox(name):
    api("DELETE", f"/v2/sandboxes/{name}?teamId={TEAM}&projectId={PROJ}")
    c, r = api("POST", f"/v2/sandboxes?teamId={TEAM}",
               {"projectId": PROJ, "name": name,
                "networkPolicy": {"mode": "custom", "allowedDomains": ["httpbin.org"]}})
    if c != 200:
        print(f"create {name}: {c} {r[:200]}", flush=True)
        return None, None
    sid = json.loads(r)["sandbox"]["currentSessionId"]
    c, r = api("POST", f"/v2/sandboxes/sessions/{sid}/interactive?teamId={TEAM}", {})
    if c != 200:
        print(f"interactive {name}: {c} {r[:200]}", flush=True)
        return sid, None
    info = json.loads(r)
    return sid, (info["url"], info["token"])

print("== [A] 沙箱 A/B 创建 + interactive ==", flush=True)
sid_a, ia = make_sandbox("expj118a")
sid_b, ib = make_sandbox("expj118b")
print("A:", sid_a, ia, flush=True)
print("B:", sid_b, ib, flush=True)
if not ia or not ib:
    print("SETUP FAIL", flush=True)
    sys.exit(1)
url_a, token_a = ia
url_b, token_b = ib

print("\n== [1] tokenA + urlA (对照, 期望 CONNECTED) ==", flush=True)
ws_try(f"{url_a}?token={token_a}", label="A+A")

print("\n== [2] tokenA + urlB (跨沙箱, 期望 401=绑定) ==", flush=True)
ws_try(f"{url_b}?token={token_a}", label="A+B")

print("\n== [3] tokenB + urlA (跨沙箱反向) ==", flush=True)
ws_try(f"{url_a}?token={token_b}", label="B+A")

print("\n== [4] tokenB + urlB (对照) ==", flush=True)
ws_try(f"{url_b}?token={token_b}", label="B+B")

print("\n== [5] 删除 A 后 tokenA 失效性 ==", flush=True)
c, r = api("DELETE", f"/v2/sandboxes/expj118a?teamId={TEAM}&projectId={PROJ}")
print("  DELETE A:", c, flush=True)
time.sleep(3)
ws_try(f"{url_a}?token={token_a}", label="A-deleted+A-token")

print("\n== [6] 协议探测 (在 B 上, 各种消息格式) ==", flush=True)
probes = [
    ("raw-text", b"id"),
    ("json-input", b'{"type":"input","data":"id\\n"}'),
    ("json-cmd", b'{"command":"id"}'),
    ("json-op-resize", b'{"op":"resize","cols":80,"rows":24}'),
    ("json-type", b'{"type":"resize","cols":80,"rows":24}'),
    ("json-run", b'{"type":"run","cmd":"id"}'),
    ("json-exec", b'{"type":"exec","command":"id"}'),
    ("json-pty", b'{"type":"pty","command":"id"}'),
]
for label, payload in probes:
    ws_try(f"{url_b}?token={token_b}", payload=payload, label=f"proto-{label}")

# 清理
for name in ["expj118a", "expj118b"]:
    c, r = api("DELETE", f"/v2/sandboxes/{name}?teamId={TEAM}&projectId={PROJ}")
    print(f"cleanup {name}: {c}", flush=True)
print("\ncleanup done", flush=True)

# 实验J117: interactive WebSocket 认证验证 — wss 是否需要 token/能否无认证直连
# 动机: j116 发现 POST /v2/sandboxes/sessions/{sid}/interactive 返回公网 wss URL + token;
#       若 wss 服务不校验 token => 无认证接管任意沙箱 interactive shell
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

def ws_try(url, headers=None, payload=None, timeout=6, label=""):
    """返回 (连接结果, 收到的消息列表)"""
    msgs = []
    try:
        ws = websocket.create_connection(url, header=headers, timeout=timeout,
                                         sslopt={"cert_reqs": ssl.CERT_NONE, "check_hostname": False})
        print(f"  [{label}] CONNECTED", flush=True)
        if payload:
            ws.send(payload)
        # 收消息
        try:
            while True:
                m = ws.recv()
                msgs.append(m)
                print(f"  [{label}] recv: {m[:300]!r}", flush=True)
                if len(msgs) >= 5:
                    break
        except websocket.WebSocketTimeoutException:
            print(f"  [{label}] recv timeout after {len(msgs)} msgs", flush=True)
        except Exception as e:
            print(f"  [{label}] recv end: {type(e).__name__}: {e}", flush=True)
        ws.close()
        return True, msgs
    except websocket.WebSocketBadStatusException as e:
        print(f"  [{label}] HTTP {e.status_code}: {e.resp[:200] if hasattr(e,'resp') else ''}", flush=True)
        return False, msgs
    except Exception as e:
        print(f"  [{label}] FAIL {type(e).__name__}: {e}", flush=True)
        return False, msgs

NAME = "expj117"
api("DELETE", f"/v2/sandboxes/{NAME}?teamId={TEAM}&projectId={PROJ}")
c, r = api("POST", f"/v2/sandboxes?teamId={TEAM}",
           {"projectId": PROJ, "name": NAME,
            "networkPolicy": {"mode": "custom", "allowedDomains": ["httpbin.org"]}})
print("create:", c, flush=True)
if c != 200:
    print(r[:300], flush=True)
    sys.exit(1)
sid = json.loads(r)["sandbox"]["currentSessionId"]
print("sid:", sid, flush=True)

c, r = api("POST", f"/v2/sandboxes/sessions/{sid}/interactive?teamId={TEAM}", {})
print("interactive:", c, flush=True)
info = json.loads(r)
url = info["url"]
token = info["token"]
print("url:", url, flush=True)
print("token:", token, flush=True)

print("\n== [1] 无凭据直连 ==", flush=True)
ws_try(url, label="no-auth")

print("\n== [2] query token ==", flush=True)
ws_try(f"{url}?token={token}", label="query-token")

print("\n== [3] Authorization Bearer ==", flush=True)
ws_try(url, headers={"Authorization": f"Bearer {token}"}, label="auth-header")

print("\n== [4] 错误 token (query) ==", flush=True)
ws_try(f"{url}?token=WRONGTOKEN123", label="wrong-token")

print("\n== [5] 正确 token + 探测协议 (发消息) ==", flush=True)
ws_try(f"{url}?token={token}", payload="hello", label="token+msg")

print("\n== [6] 第二个 interactive 会话 (token 复用?) ==", flush=True)
c, r = api("POST", f"/v2/sandboxes/sessions/{sid}/interactive?teamId={TEAM}", {})
print("  second interactive:", c, r[:200], flush=True)
if c == 200:
    info2 = json.loads(r)
    print("  url2:", info2["url"], flush=True)
    print("  token2 same:", info2["token"] == token, flush=True)
    ws_try(f"{info2['url']}?token={token}", label="cross-token(url2+token1)")

api("DELETE", f"/v2/sandboxes/{NAME}?teamId={TEAM}&projectId={PROJ}")
print("\ncleanup done", flush=True)

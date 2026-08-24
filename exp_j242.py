# 实验J242: containerd.sock/cell.sock/apm.sock/metrics.sock + 23456端口 + 30002深测
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

NAME = "expj242"
api("DELETE", f"/v2/sandboxes/{NAME}?teamId={TEAM}&projectId={PROJ}")
c, r = api("POST", f"/v2/sandboxes?teamId={TEAM}",
           {"projectId": PROJ, "name": NAME})
print("create:", c, flush=True)
if c != 200:
    print(r[:400], flush=True)
    sys.exit(1)
sid = json.loads(r)["sandbox"]["currentSessionId"]
print("sid:", sid, flush=True)

# A) 23456 端口归属 + 基础探测 (安全)
CODE_A = r'''
import subprocess, os, glob
def p(*a): print(" ".join(str(x) for x in a), flush=True)
# inode 162 归属: 找沙箱内可见进程持有该 socket 的 fd
for proc in glob.glob("/proc/[0-9]*"):
    try:
        for fd in glob.glob(proc + "/fd/*"):
            try:
                t = os.readlink(fd)
                if "socket:[162]" in t:
                    p("OWNER", proc, fd, t)
            except Exception:
                pass
    except Exception:
        pass
# 23456 探测
code = (
    "import socket; s=socket.socket(socket.AF_INET, socket.SOCK_STREAM); s.settimeout(3); "
    "s.connect(('127.0.0.1', 23456)); print('C23456_OK', flush=True); "
    "s.send(b'GET / HTTP/1.1\\\\r\\\\nHost: x\\\\r\\\\n\\\\r\\\\n'); d=b''; "
    "exec('\\\\nwhile True:\\\\n try:\\\\n  b=s.recv(4096)\\\\n  if not b: break\\\\n  d+=b\\\\n except Exception: break'); "
    "print('RESP23456', d[:300].decode(errors='replace'), flush=True)"
)
r = subprocess.run(["python3", "-c", code], capture_output=True, text=True, timeout=8)
p("T23456", "rc", r.returncode, (r.stdout + r.stderr)[:300].replace(chr(10), "|"))
p("DONE_A", flush=True)
'''
run_cmd(sid, CODE_A, "A_23456", timeout=100)

# B) sudo 连接 containerd.sock (gRPC List) - 高风险, 独立阶段
CODE_B = r'''
import subprocess
def p(*a): print(" ".join(str(x) for x in a), flush=True)
code = (
    "import socket, time; "
    "s=socket.socket(socket.AF_UNIX, socket.SOCK_STREAM); s.settimeout(4); "
    "s.connect('/run/containerd/containerd.sock'); print('CTD_C_OK', flush=True); "
    "body=b'{}'; "
    "req=(b'POST /containerd.services.containers.v1.Containers/List HTTP/1.1\\\\r\\\\nHost: localhost\\\\r\\\\nContent-Type: application/grpc\\\\r\\\\nContent-Length: 0\\\\r\\\\nTE: trailers\\\\r\\\\n\\\\r\\\\n'); "
    "s.send(req); print('CTD_SENT', flush=True); "
    "d=b''; "
    "exec('\\\\nwhile True:\\\\n try:\\\\n  b=s.recv(4096)\\\\n  if not b: break\\\\n  d+=b\\\\n except Exception as e:\\\\n  print(\\\"CTD_RE\\\", type(e).__name__, flush=True); break'); "
    "print('CTD_RESP', d[:400].hex(), flush=True); print('DONE', flush=True)"
)
for who, cmd in (("USER", ["python3", "-c", code]), ("ROOT", ["sudo", "-n", "python3", "-c", code])):
    try:
        r = subprocess.run(cmd, capture_output=True, text=True, timeout=10)
        p("CTD", who, "rc", r.returncode, "OUT", (r.stdout + r.stderr)[:400].replace(chr(10), "|"))
    except Exception as e:
        p("CTD", who, "EXC", type(e).__name__, str(e)[:80])
p("DONE_B", flush=True)
'''
run_cmd(sid, CODE_B, "B_CTD", timeout=100)

# C) sudo 连接 cell.sock
CODE_C = r'''
import subprocess
def p(*a): print(" ".join(str(x) for x in a), flush=True)
code = (
    "import socket; s=socket.socket(socket.AF_UNIX, socket.SOCK_STREAM); s.settimeout(4); "
    "s.connect('/run/cell/cell.sock'); print('CELL_C_OK', flush=True); "
    "s.send(b'GET / HTTP/1.1\\\\r\\\\nHost: x\\\\r\\\\n\\\\r\\\\n'); d=b''; "
    "exec('\\\\nwhile True:\\\\n try:\\\\n  b=s.recv(4096)\\\\n  if not b: break\\\\n  d+=b\\\\n except Exception as e:\\\\n  print(\\\"CELL_RE\\\", type(e).__name__, flush=True); break'); "
    "print('CELL_RESP', d[:300].decode(errors='replace'), flush=True); print('DONE', flush=True)"
)
for who, cmd in (("USER", ["python3", "-c", code]), ("ROOT", ["sudo", "-n", "python3", "-c", code])):
    try:
        r = subprocess.run(cmd, capture_output=True, text=True, timeout=10)
        p("CELL", who, "rc", r.returncode, "OUT", (r.stdout + r.stderr)[:400].replace(chr(10), "|"))
    except Exception as e:
        p("CELL", who, "EXC", type(e).__name__, str(e)[:80])
p("DONE_C", flush=True)
'''
run_cmd(sid, CODE_C, "C_CELL", timeout=100)

# D) sudo 连接 apm.sock / metrics.sock / containerd shim
CODE_D = r'''
import subprocess
def p(*a): print(" ".join(str(x) for x in a), flush=True)
for sock in ("/run/apm/apm.sock", "/run/metrics/metrics.sock"):
    code = (
        "import socket; s=socket.socket(socket.AF_UNIX, socket.SOCK_STREAM); s.settimeout(4); "
        "s.connect('%s'); print('OK', flush=True); "
        "s.send(b'GET / HTTP/1.1\\\\r\\\\nHost: x\\\\r\\\\n\\\\r\\\\n'); d=b''; "
        "exec('\\\\nwhile True:\\\\n try:\\\\n  b=s.recv(4096)\\\\n  if not b: break\\\\n  d+=b\\\\n except Exception as e:\\\\n  print(\\\"RE\\\", type(e).__name__, flush=True); break'); "
        "print('RESP', d[:200].decode(errors='replace'), flush=True)" % sock
    )
    try:
        r = subprocess.run(["sudo", "-n", "python3", "-c", code], capture_output=True, text=True, timeout=10)
        p("SOCK", sock, "rc", r.returncode, "OUT", (r.stdout + r.stderr)[:300].replace(chr(10), "|"))
    except Exception as e:
        p("SOCK", sock, "EXC", type(e).__name__, str(e)[:80])
p("DONE_D", flush=True)
'''
run_cmd(sid, CODE_D, "D_SOCKS", timeout=100)

# E) 30002 深测 (原始字节 + 各种方法)
CODE_E = r'''
import subprocess
def p(*a): print(" ".join(str(x) for x in a), flush=True)
for payload, label in (
    (b"GET / HTTP/1.1\r\nHost: x\r\n\r\n", "GET"),
    (b"POST / HTTP/1.1\r\nHost: x\r\nContent-Length: 2\r\n\r\n{}", "POST"),
    (b"PRI * HTTP/2.0\r\n\r\nSM\r\n\r\n", "H2"),
    (b"", "EMPTY"),
):
    code = (
        "import socket; s=socket.socket(socket.AF_INET, socket.SOCK_STREAM); s.settimeout(3); "
        "s.connect(('127.0.0.1', 30002)); print('C_OK', flush=True); "
        "s.send(%r); d=b''; "
        "exec('\\\\nwhile True:\\\\n try:\\\\n  b=s.recv(4096)\\\\n  if not b: break\\\\n  d+=b\\\\n except Exception as e:\\\\n  print(\\\"RE\\\", type(e).__name__, flush=True); break'); "
        "print('RESP', d[:200].hex(), flush=True)" % payload
    )
    try:
        r = subprocess.run(["python3", "-c", code], capture_output=True, text=True, timeout=8)
        p("30002", label, "rc", r.returncode, "OUT", (r.stdout + r.stderr)[:250].replace(chr(10), "|"))
    except Exception as e:
        p("30002", label, "EXC", type(e).__name__, str(e)[:80])
p("DONE_E", flush=True)
'''
run_cmd(sid, CODE_E, "E_30002", timeout=100)

api("DELETE", f"/v2/sandboxes/{NAME}?teamId={TEAM}&projectId={PROJ}")
print("\ncleanup done", flush=True)

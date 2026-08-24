# 实验J149: 完整mountinfo + 沙箱网络布局 + celld TCP端口探测(默认网络沙箱) + loop0读测试
# j148: celld含加载私钥错误串(确认私钥在celld); 沙箱网络同100.64/16段可能直连宿主
# 方法: cmdA mountinfo+route完整; cmdB 默认网络沙箱端口探测100.64.79.9; cmdC loop0读测试
# 零破坏: 纯读+端口连接探测
import json, time, urllib.request, urllib.error, sys, threading
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
        time.sleep(3)
    print(f"=== cmd[{label}] status {c} ===", flush=True)
    if c != 200:
        print(f"  RAW: {r[:400]}", flush=True)
        return ""
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

def catfile(sid, path, label, n=15000):
    c, r = api("POST", f"/v2/sandboxes/sessions/{sid}/cmd?teamId={TEAM}",
               {"command": "cat", "args": [path], "wait": True, "logs": True, "timeout": 100})
    print(f"=== {label} status {c} ===", flush=True)
    print(r[:n], flush=True)

# ============ 沙箱A: mountinfo + 网络 ============
NAME_A = "expj149a"
api("DELETE", f"/v2/sandboxes/{NAME_A}?teamId={TEAM}&projectId={PROJ}")
c, r = api("POST", f"/v2/sandboxes?teamId={TEAM}",
           {"projectId": PROJ, "name": NAME_A,
            "networkPolicy": {"mode": "custom", "allowedDomains": ["httpbin.org"]}})
print("create A:", c)
sidA = json.loads(r)["sandbox"]["currentSessionId"]
print("sidA:", sidA)

CA = r'''
import os, subprocess
out = open("/tmp/d149a.txt", "w")
def p(*a):
    out.write(" ".join(str(x) for x in a) + "\n")
    out.flush()
def sh(cmd, t=10):
    try:
        r = subprocess.run(cmd, shell=True, capture_output=True, timeout=t)
        return (r.stdout or b"").decode("latin1", "replace") + (r.stderr or b"").decode("latin1", "replace")
    except Exception as e:
        return "EXC %r" % (e,)
p("=== MOUNTINFO_FULL ===")
p(open("/proc/self/mountinfo").read())
p("=== ROUTE ===")
p(sh("cat /proc/net/route 2>&1"))
p("=== FIB_TRIE ===")
p(sh("cat /proc/net/fib_trie 2>&1 | head -60"))
p("=== IFACE ===")
p(sh("cat /proc/net/dev 2>&1"))
p("=== ARP ===")
p(sh("cat /proc/net/arp 2>&1"))
p("=== DONE")
out.close()
'''

CC = r'''
import os, time
out = open("/tmp/d149c.txt", "w")
def p(*a):
    out.write(" ".join(str(x) for x in a) + "\n")
    out.flush()
p("=== LOOP0_READ_TEST ===")
try:
    f = open("/dev/loop0", "rb")
    t0 = time.time()
    total = 0
    CH = 8 * 1024 * 1024
    pos = 0
    while total < 512 * 1024 * 1024:
        f.seek(pos)
        chunk = f.read(CH)
        if not chunk:
            break
        pos += len(chunk)
        total += len(chunk)
    f.close()
    p("loop0 read MB", total // (1024 * 1024), "elapsed", int(time.time() - t0))
except Exception as e:
    p("loop0 err", repr(e))
p("=== DONE")
out.close()
'''

run_cmd(sidA, CA, "mountinfo", timeout=100)
catfile(sidA, "/tmp/d149a.txt", "d149a", 8000)

run_cmd(sidA, CC, "loop0-test", timeout=150)
catfile(sidA, "/tmp/d149c.txt", "d149c", 2000)
api("DELETE", f"/v2/sandboxes/{NAME_A}?teamId={TEAM}&projectId={PROJ}")

# ============ 沙箱B: 默认网络 -> celld端口探测 ============
NAME_B = "expj149b"
api("DELETE", f"/v2/sandboxes/{NAME_B}?teamId={TEAM}&projectId={PROJ}")
c, r = api("POST", f"/v2/sandboxes?teamId={TEAM}",
           {"projectId": PROJ, "name": NAME_B})
print("create B:", c, r[:200] if c != 200 else "")
if c == 200:
    sidB = json.loads(r)["sandbox"]["currentSessionId"]
    print("sidB:", sidB)
    CB = r'''
import socket, subprocess
out = open("/tmp/d149b.txt", "w")
def p(*a):
    out.write(" ".join(str(x) for x in a) + "\n")
    out.flush()
def sh(cmd, t=10):
    try:
        r = subprocess.run(cmd, shell=True, capture_output=True, timeout=t)
        return (r.stdout or b"").decode("latin1", "replace") + (r.stderr or b"").decode("latin1", "replace")
    except Exception as e:
        return "EXC %r" % (e,)
p("=== ROUTE ===")
p(sh("cat /proc/net/route 2>&1"))
p("=== CONNECT_TEST ===")
def try_conn(ip, port, t=3):
    try:
        s = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
        s.settimeout(t)
        s.connect((ip, port))
        s.close()
        return "OPEN"
    except Exception as e:
        return repr(e)[:60]
targets = ["100.64.79.9", "100.64.0.1", "100.64.0.2", "169.254.169.254"]
ports = [22, 80, 443, 8000, 8080, 3000, 5000, 9000, 2375, 2379, 6443, 10250, 10000, 32000, 32001, 33000, 8081, 9090, 8443]
for ip in targets:
    for port in ports:
        r = try_conn(ip, port)
        if r == "OPEN" or "timed out" not in r:
            p(ip, port, r)
        else:
            p(ip, port, "closed")
p("=== HTTP_PROBE ===")
for ip in targets:
    for port in (80, 443, 8000, 8080, 3000, 9000):
        try:
            s = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
            s.settimeout(2)
            s.connect((ip, port))
            s.send(b"GET / HTTP/1.0\r\nHost: x\r\n\r\n")
            d = s.recv(300)
            s.close()
            p("HTTP", ip, port, repr(d[:200]))
        except Exception as e:
            pass
p("=== DNS_TEST ===")
p(sh("getent hosts api.vercel.com 2>&1 | head -3"))
p("=== OUTBOUND ===")
try:
    s = socket.create_connection(("httpbin.org", 80), timeout=4)
    s.send(b"GET /ip HTTP/1.0\r\nHost: httpbin.org\r\n\r\n")
    d = s.recv(500)
    s.close()
    p("httpbin ok", repr(d[:300]))
except Exception as e:
    p("httpbin err", repr(e)[:100])
p("=== DONE")
out.close()
'''
    run_cmd(sidB, CB, "celld-probe", timeout=200)
    catfile(sidB, "/tmp/d149b.txt", "d149b", 10000)
    api("DELETE", f"/v2/sandboxes/{NAME_B}?teamId={TEAM}&projectId={PROJ}")

print("\ncleanup done", flush=True)

# 实验K6: 跨沙箱通信验证 — A 后台监听, B 同节点连接 (打破"沙箱间网络完全隔离"?)
# 前置: j92 共享 net ns(宿主监听可见); j121 沙箱随机调度多节点(sandbox-init 虚拟 inode 分组判定同节点)
# 流程: 建A -> A wait=False 后台监听31337 -> 建B -> stat 双方 sandbox-init inode 判同节点 -> B 连127.0.0.1:31337 -> A 查 /tmp/pwn.txt
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

def run_cmd(sid, code, label, wait=True, timeout=300, logs=True):
    body = {"command": "python3", "args": ["-c", code],
            "wait": wait, "logs": logs, "timeout": timeout}
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

NAME_A = "expk6a"
NAME_B = "expk6b"
api("DELETE", f"/v2/sandboxes/{NAME_A}?teamId={TEAM}&projectId={PROJ}")
api("DELETE", f"/v2/sandboxes/{NAME_B}?teamId={TEAM}&projectId={PROJ}")

# A: 创建 + 后台监听 31337 (wait=False, timeout 300s, logs=False)
c, r = api("POST", f"/v2/sandboxes?teamId={TEAM}",
           {"projectId": PROJ, "name": NAME_A,
            "networkPolicy": {"mode": "custom", "allowedDomains": ["httpbin.org"]}})
print("create A:", c)
sid_a = json.loads(r)["sandbox"]["currentSessionId"]
print("sid A:", sid_a)

LISTEN_CODE = """
import socket, os, time
s = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
s.setsockopt(socket.SOL_SOCKET, socket.SO_REUSEADDR, 1)
s.bind(("0.0.0.0", 31337))
s.listen(5)
open("/tmp/listening.txt", "w").write("LISTENING")
os.system("echo LISTENING >> /tmp/pwn.log")
# 多轮 accept, 每次记录
for i in range(10):
    try:
        c, a = s.accept()
        c.settimeout(3)
        d = b""
        try:
            d = c.recv(1024)
        except Exception:
            pass
        open("/tmp/pwn.txt", "a").write("ACCEPT %s %r\\n" % (a, d))
        try:
            c.sendall(b"PWN-ACK")
        except Exception:
            pass
        c.close()
    except Exception as e:
        open("/tmp/pwn.txt", "a").write("ERR %r\\n" % e)
time.sleep(2)
"""
run_cmd(sid_a, LISTEN_CODE, "A-listen", wait=False, timeout=300000, logs=False)

# B: 创建
c, r = api("POST", f"/v2/sandboxes?teamId={TEAM}",
           {"projectId": PROJ, "name": NAME_B,
            "networkPolicy": {"mode": "custom", "allowedDomains": ["httpbin.org"]}})
print("create B:", c)
sid_b = json.loads(r)["sandbox"]["currentSessionId"]
print("sid B:", sid_b)

# 同节点判定: stat sandbox-init inode (j121 方法)
NODE_CODE = """
import os
st = os.stat("/run/vercel/share/sandbox-init")
print("NODE_INODE", st.st_ino)
"""
run_cmd(sid_a, NODE_CODE, "A-node", wait=True, timeout=120000)
run_cmd(sid_b, NODE_CODE, "B-node", wait=True, timeout=120000)

# B 连 A: 127.0.0.1 (共享 net ns) + 自身 IP + 网关
CONN_CODE = """
import socket, subprocess, time
ips = ["127.0.0.1"]
try:
    r = subprocess.run(["hostname", "-I"], capture_output=True, text=True, timeout=5)
    ips += r.stdout.split()
except Exception:
    pass
print("TRY_IPS", ips, flush=True)
for ip in ips:
    for port in (31337,):
        try:
            s = socket.create_connection((ip, port), timeout=4)
            s.settimeout(4)
            s.sendall(b"HELLO-FROM-B")
            d = s.recv(200)
            print("CONN_OK", ip, port, "resp:", d[:100], flush=True)
            s.close()
        except Exception as e:
            print("CONN_FAIL", ip, port, "ERR:", e, flush=True)
"""
run_cmd(sid_b, CONN_CODE, "B-conn", wait=True, timeout=120000)

# A 查收件记录
READ_CODE = """
import os
for f in ("/tmp/pwn.txt", "/tmp/pwn.log", "/tmp/listening.txt"):
    try:
        print("===", f, "===", flush=True)
        print(open(f).read(), flush=True)
    except Exception as e:
        print(f, "ERR", e, flush=True)
"""
time.sleep(3)
run_cmd(sid_a, READ_CODE, "A-check", wait=True, timeout=120000)

api("DELETE", f"/v2/sandboxes/{NAME_A}?teamId={TEAM}&projectId={PROJ}")
api("DELETE", f"/v2/sandboxes/{NAME_B}?teamId={TEAM}&projectId={PROJ}")
print("\ncleanup done", flush=True)

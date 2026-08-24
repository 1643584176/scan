# 实验K6b: 跨沙箱通信 — 4沙箱同节点配对 (inode 分组) + 端口互连
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

def run_cmd(sid, code, label, wait=True, timeout=300, logs=True, quiet=False):
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
    out = []
    for line in r.splitlines():
        line = line.strip()
        if not line:
            continue
        try:
            d = json.loads(line)
            if d.get("stream") in ("stdout", "stderr"):
                out.append(d.get("data", ""))
            elif d.get("stream") == "command":
                out.append(f"\nEXIT: {d.get('command', {}).get('exitCode')}")
        except Exception:
            out.append(line[:400])
    joined = "".join(out)
    print(joined, flush=True)
    return joined

# 建 4 沙箱
NAMES = ["expk6b%d" % i for i in range(4)]
PORTS = [31337, 31338, 31339, 31340]
sids = []
for i, name in enumerate(NAMES):
    api("DELETE", f"/v2/sandboxes/{name}?teamId={TEAM}&projectId={PROJ}")
    c, r = api("POST", f"/v2/sandboxes?teamId={TEAM}",
               {"projectId": PROJ, "name": name,
                "networkPolicy": {"mode": "custom", "allowedDomains": ["httpbin.org"]}})
    sid = json.loads(r)["sandbox"]["currentSessionId"]
    sids.append(sid)
    print(f"create {name}: {c} sid={sid}", flush=True)

# 各沙箱后台监听唯一端口
for i, sid in enumerate(sids):
    port = PORTS[i]
    code = f"""
import socket, os
s = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
s.setsockopt(socket.SOL_SOCKET, socket.SO_REUSEADDR, 1)
s.bind(("0.0.0.0", {port}))
s.listen(5)
open("/tmp/pwn_{port}.txt", "w").write("LISTENING")
for _ in range(10):
    try:
        c, a = s.accept()
        c.settimeout(3)
        d = b""
        try:
            d = c.recv(1024)
        except Exception:
            pass
        open("/tmp/pwn_{port}.txt", "a").write("ACCEPT %s %r\\n" % (a, d))
        try:
            c.sendall(b"PWN-ACK")
        except Exception:
            pass
        c.close()
    except Exception as e:
        open("/tmp/pwn_{port}.txt", "a").write("ERR %r\\n" % e)
time.sleep(1)
"""
    run_cmd(sid, code, f"listen-{port}", wait=False, timeout=300000, logs=False, quiet=True)

# 同节点判定
inodes = []
NODE_CODE = 'import os; print("NODE_INODE", os.stat("/run/vercel/share/sandbox-init").st_ino)'
for i, sid in enumerate(sids):
    out = run_cmd(sid, NODE_CODE, f"node-{i}", wait=True, timeout=120000, quiet=True)
    ino = None
    for ln in out.splitlines():
        if "NODE_INODE" in ln:
            ino = ln.split()[-1]
    inodes.append(ino)
    print(f"sandbox[{i}] inode={ino}", flush=True)

# 找同节点对
pairs = []
for i in range(4):
    for j in range(i + 1, 4):
        if inodes[i] and inodes[i] == inodes[j]:
            pairs.append((i, j))
print("SAME_NODE_PAIRS:", pairs, flush=True)

if not pairs:
    print("NO SAME-NODE PAIR - 放弃", flush=True)
else:
    for (i, j) in pairs:
        print(f"\n########## PAIR ({i},{j}) 同节点 ##########", flush=True)
        # j 连 i 的端口 (127.0.0.1 共享 net ns)
        conn_code = f"""
import socket
for ip in ("127.0.0.1",):
    try:
        s = socket.create_connection((ip, {PORTS[i]}), timeout=5)
        s.settimeout(5)
        s.sendall(b"HELLO-FROM-SANDBOX-%d")
        d = s.recv(200)
        print("CONN_OK", ip, {PORTS[i]}, "resp:", d[:100], flush=True)
        s.close()
    except Exception as e:
        print("CONN_FAIL", ip, {PORTS[i]}, "ERR:", e, flush=True)
""" % j
        run_cmd(sids[j], conn_code, f"conn-{j}->{i}", wait=True, timeout=120000, quiet=True)
        time.sleep(2)
        read_code = f"""
for f in ("/tmp/pwn_{PORTS[i]}.txt",):
    try:
        print("===", f, "===", flush=True)
        print(open(f).read(), flush=True)
    except Exception as e:
        print(f, "ERR", e, flush=True)
"""
        run_cmd(sids[i], read_code, f"check-{i}", wait=True, timeout=120000, quiet=True)

for name in NAMES:
    api("DELETE", f"/v2/sandboxes/{name}?teamId={TEAM}&projectId={PROJ}")
print("\ncleanup done", flush=True)

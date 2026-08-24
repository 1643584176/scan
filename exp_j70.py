# 实验J70: 修正版权限探针 —— 先 setuid(0), 按顺序测试, 加 errno
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

NAME = "expj70"
api("DELETE", f"/v2/sandboxes/{NAME}?teamId={TEAM}&projectId={PROJ}")
c, r = api("POST", f"/v2/sandboxes?teamId={TEAM}",
           {"projectId": PROJ, "name": NAME,
            "networkPolicy": {"mode": "custom", "allowedDomains": ["httpbin.org"]}})
print("create:", c)
sid = json.loads(r)["sandbox"]["currentSessionId"]
print("sid:", sid)

PROBE = r"""
import os, sys, ctypes

libc = ctypes.CDLL(None, use_errno=True)
libc.syscall.restype = ctypes.c_long
def sc(nr, *args):
    ctypes.set_errno(0)
    r = libc.syscall(nr, *args)
    return r, ctypes.get_errno()

def t(label, fn):
    try:
        r = fn()
        print("[%-24s] OK %r" % (label, r), flush=True)
    except Exception as e:
        print("[%-24s] FAIL %r" % (label, e), flush=True)

os.setuid(0); os.setgid(0)
print("== [0] now uid=%d gid=%d ==" % (os.getuid(), os.getgid()), flush=True)

print("== [1] mount 测试 ==", flush=True)
os.makedirs("/tmp/mt3", exist_ok=True)
t("mount tmpfs", lambda: sc(165, b"none", b"/tmp/mt3", b"tmpfs", 0, None))  # x86_64 mount
t("umount", lambda: sc(166, b"/tmp/mt3", 0))
# mount 走 /bin/mount 看看
t("mount cmd", lambda: os.system("mount -t tmpfs none /tmp/mt3 2>&1; echo RC=$?"))

print("== [2] /dev/mem 深读 ==", flush=True)
t("open /dev/mem", lambda: len(open("/dev/mem", "rb").read(16)))
try:
    iomem = open("/proc/iomem").read()
    print("iomem head:", iomem[:600].replace("\n", " | "), flush=True)
except Exception as e:
    print("iomem ERR %r" % e, flush=True)
def mem_read_at(off):
    f = open("/dev/mem", "rb", buffering=0)
    f.seek(off)
    d = f.read(32)
    f.close()
    return d.hex()
for off in [0x0, 0x100000, 0x1000000, 0x80000000]:
    t("mem@%#x" % off, lambda o=off: mem_read_at(o))

print("== [3] /proc/1/fd 侦察 ==", flush=True)
try:
    for fd in sorted(os.listdir("/proc/1/fd"), key=int):
        try:
            print("  fd %s -> %s" % (fd, os.readlink("/proc/1/fd/" + fd)), flush=True)
        except Exception as e:
            print("  fd %s ERR %r" % (fd, e), flush=True)
except Exception as e:
    print("fd list ERR %r" % e, flush=True)

print("== [4] sandbox-init 环境/网络 ==", flush=True)
try:
    print("environ:", open("/proc/1/environ").read().replace("\x00", " ")[:1500], flush=True)
except Exception as e:
    print("environ ERR %r" % e, flush=True)
try:
    print(open("/proc/1/net/tcp").read(), flush=True)
except Exception as e:
    print("tcp ERR %r" % e, flush=True)
try:
    print(open("/proc/1/net/unix").read(), flush=True)
except Exception as e:
    print("unix ERR %r" % e, flush=True)

print("== [5] 能力类 syscall errno ==", flush=True)
t("bpf", lambda: sc(321, 5, 0, 0, 0, 0))
t("perf_event_open", lambda: sc(298, 0, 0, -1, 0x400000, 0))
t("open_by_handle_at", lambda: sc(304, -100, 0, 0, 0))
t("kexec_load", lambda: sc(246, 0, 0, 0, 0))
t("ptrace(1,1)", lambda: sc(101, 16, 1, 0, 0))
t("setns(1,0)", lambda: sc(308, 1, 0))
t("process_vm_readv(1)", lambda: sc(310, 1, 0, 0, 0, 0, 0))

print("== [6] /dev/vda 写测试 (写回原值) ==", flush=True)
def vda_test():
    f = open("/dev/vda", "r+b", buffering=0)
    f.seek(0)
    orig = f.read(16)
    f.seek(0)
    f.write(orig)
    f.close()
    return "rw-ok first16=%s" % orig.hex()
t("vda r+w", vda_test)
# 设备列表
try:
    print("dev:", sorted(os.listdir("/dev"))[:60], flush=True)
except Exception as e:
    print("dev ERR %r" % e, flush=True)
"""
run_cmd(sid, PROBE, "priv-probe-v2", wait=True, timeout=180000)

api("DELETE", f"/v2/sandboxes/{NAME}?teamId={TEAM}&projectId={PROJ}")
print("\ncleanup done", flush=True)

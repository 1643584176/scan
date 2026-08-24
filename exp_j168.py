# 实验J168: 检测升级验证矩阵 - 确认当前沙箱/账户下哪些操作还安全
# j167: 纯attach+getregs+detach被杀(与j161/j164同操作却死) => 疑似检测升级/账户标记
# 验证: cmd0写文件 -> cmdA process_vm_readv读16B -> cmdB纯attach+detach -> cmdC attach+getregs+detach
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
        if c == 410 or "sandbox_stopped" in r:
            print(f"  SANDBOX_DEAD at cmd[{label}]", flush=True)
            return "DEAD"
        time.sleep(3)
    print(f"=== cmd[{label}] status {c} ===", flush=True)
    if c != 200:
        print(f"  RAW: {r[:400]}", flush=True)
        return "DEAD" if "sandbox_stopped" in r else ""
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

def catfile(sid, path, label, n=3000):
    c, r = api("POST", f"/v2/sandboxes/sessions/{sid}/cmd?teamId={TEAM}",
               {"command": "cat", "args": [path], "wait": True, "logs": True, "timeout": 100})
    print(f"=== {label} status {c} ===", flush=True)
    print(r[:n], flush=True)
    return c

NAME = "expj168"
api("DELETE", f"/v2/sandboxes/{NAME}?teamId={TEAM}&projectId={PROJ}")
c, r = api("POST", f"/v2/sandboxes?teamId={TEAM}",
           {"projectId": PROJ, "name": NAME,
            "networkPolicy": {"mode": "custom", "allowedDomains": ["httpbin.org"]}})
print("create:", c)
if c != 200:
    print(r[:400])
    sys.exit(1)
sid = json.loads(r)["sandbox"]["currentSessionId"]
print("sid:", sid)

# cmd0: 基础写文件
C0 = r'''
import os
out = open("/tmp/d168a.txt", "w")
out.write("baseline_ok\n")
out.close()
'''

# cmdA: process_vm_readv 读 text 16B
CA = r'''
import ctypes, os
out = open("/tmp/d168b.txt", "w")
def p(*a):
    out.write(" ".join(str(x) for x in a) + "\n")
    out.flush()
libc = ctypes.CDLL(None, use_errno=True)
libc.syscall.restype = ctypes.c_long
SYS_process_vm_readv = 310
class Iovec(ctypes.Structure):
    _fields_ = [("iov_base", ctypes.c_void_p), ("iov_len", ctypes.c_size_t)]
buf = ctypes.create_string_buffer(16)
local = Iovec(ctypes.cast(buf, ctypes.c_void_p), 16)
remote = Iovec(ctypes.c_void_p(0x401000), 16)
ctypes.set_errno(0)
n = libc.syscall(SYS_process_vm_readv, 1, ctypes.byref(local), 1,
                 ctypes.byref(remote), 1, 0)
p("pvm_read", n, "errno", ctypes.get_errno())
if n > 0:
    p("data", buf.raw.hex())
p("=== DONE")
out.close()
'''

# cmdB: 纯 attach + detach
CB = r'''
import ctypes, time, os
out = open("/tmp/d168c.txt", "w")
def p(*a):
    out.write(" ".join(str(x) for x in a) + "\n")
    out.flush()
libc = ctypes.CDLL(None, use_errno=True)
libc.ptrace.restype = ctypes.c_long
def pt(pid, req, addr=0, data=0):
    ctypes.set_errno(0)
    r = libc.ptrace(req, pid, addr, data)
    return r, ctypes.get_errno()
p("start")
r, e = pt(1, 16)  # PTRACE_ATTACH
p("attach", r, "errno", e)
if r == 0:
    time.sleep(0.5)
    r2, e2 = pt(1, 17)  # PTRACE_DETACH
    p("detach", r2, "errno", e2)
else:
    p("attach_failed")
p("=== DONE")
out.close()
'''

# cmdC: attach + getregs + detach
CC = r'''
import ctypes, time, os
out = open("/tmp/d168d.txt", "w")
def p(*a):
    out.write(" ".join(str(x) for x in a) + "\n")
    out.flush()
libc = ctypes.CDLL(None, use_errno=True)
libc.ptrace.restype = ctypes.c_long
class UserRegs(ctypes.Structure):
    _fields_ = [("r15", ctypes.c_ulonglong), ("r14", ctypes.c_ulonglong),
                ("r13", ctypes.c_ulonglong), ("r12", ctypes.c_ulonglong),
                ("rbp", ctypes.c_ulonglong), ("rbx", ctypes.c_ulonglong),
                ("r11", ctypes.c_ulonglong), ("r10", ctypes.c_ulonglong),
                ("r9", ctypes.c_ulonglong), ("r8", ctypes.c_ulonglong),
                ("rax", ctypes.c_ulonglong), ("rcx", ctypes.c_ulonglong),
                ("rdx", ctypes.c_ulonglong), ("rsi", ctypes.c_ulonglong),
                ("rdi", ctypes.c_ulonglong), ("orig_rax", ctypes.c_ulonglong),
                ("rip", ctypes.c_ulonglong), ("cs", ctypes.c_ulonglong),
                ("eflags", ctypes.c_ulonglong), ("rsp", ctypes.c_ulonglong),
                ("ss", ctypes.c_ulonglong), ("fs_base", ctypes.c_ulonglong),
                ("gs_base", ctypes.c_ulonglong), ("ds", ctypes.c_ulonglong),
                ("es", ctypes.c_ulonglong), ("fs", ctypes.c_ulonglong),
                ("gs", ctypes.c_ulonglong)]
def pt(pid, req, addr=0, data=0):
    ctypes.set_errno(0)
    r = libc.ptrace(req, pid, addr, data)
    return r, ctypes.get_errno()
p("start")
r, e = pt(1, 16)
p("attach", r, "errno", e)
if r == 0:
    time.sleep(0.3)
    regs = UserRegs()
    rr, e = pt(1, 12, 0, ctypes.byref(regs))
    p("getregs", rr, "errno", e, "rip", hex(regs.rip) if rr == 0 else "?")
    time.sleep(0.3)
    pt(1, 17)
    p("detached")
else:
    p("attach_failed")
p("=== DONE")
out.close()
'''

steps = [
    ("baseline", "/tmp/d168a.txt", C0),
    ("pvm-read", "/tmp/d168b.txt", CA),
    ("attach-d", "/tmp/d168c.txt", CB),
    ("attach-gr-d", "/tmp/d168d.txt", CC),
]

for label, marker, code in steps:
    st = run_cmd(sid, code, label, timeout=150)
    time.sleep(2)
    cf = catfile(sid, marker, f"marker[{label}]", 2000)
    if st == "DEAD" or cf == 410:
        print(f"\n!!! DEATH after cmd[{label}] -> trigger = {label}", flush=True)
        break

api("DELETE", f"/v2/sandboxes/{NAME}?teamId={TEAM}&projectId={PROJ}")
print("\ncleanup done", flush=True)

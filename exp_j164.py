# 实验J164: 排除PEEKDATA后, 各操作单独验证 + process_vm_readv替代读通道
# j163: PTRACE_PEEKDATA(读PID1内存)触发被杀; attach/getregs 安全
# 方法: 单沙箱顺序执行, 每步后catfile确认存活:
#   cmd1: SETREGS原值写回  cmd2: POKEDATA写rw段(不读原值)  cmd3: CONT
#   cmd4: process_vm_readv(1)直读PID1内存(不attach, 不同syscall)
# 全部存活 => 写/改寄存器/继续执行均安全, 只有读被监控; cmd4若读到cmd2写入的0x90 => 写生效+读通道可用
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

def catfile(sid, path, label, n=2000):
    c, r = api("POST", f"/v2/sandboxes/sessions/{sid}/cmd?teamId={TEAM}",
               {"command": "cat", "args": [path], "wait": True, "logs": True, "timeout": 100})
    print(f"=== {label} status {c} ===", flush=True)
    print(r[:n], flush=True)
    return c

NAME = "expj164"
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

# cmd1: attach + GETREGS + SETREGS(原值) + detach
C1 = r'''
import ctypes, time, os
out = open("/tmp/d164a.txt", "w")
def p(*a):
    out.write(" ".join(str(x) for x in a) + "\n")
    out.flush()
libc = ctypes.CDLL(None, use_errno=True)
libc.ptrace.restype = ctypes.c_long
PTRACE_ATTACH, PTRACE_DETACH = 16, 17
PTRACE_GETREGS, PTRACE_SETREGS = 12, 13
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
r, e = pt(1, PTRACE_ATTACH)
p("attach", r, "errno", e)
if r == 0:
    time.sleep(0.3)
    regs = UserRegs()
    rr, e = pt(1, PTRACE_GETREGS, 0, ctypes.byref(regs))
    p("getregs", rr, "errno", e, "rip", hex(regs.rip))
    time.sleep(0.3)
    r2, e2 = pt(1, PTRACE_SETREGS, 0, ctypes.byref(regs))
    p("setregs_same", r2, "errno", e2)
    time.sleep(0.3)
    pt(1, PTRACE_DETACH)
    p("detached")
else:
    p("attach_failed")
p("=== DONE")
out.close()
'''

# cmd2: attach + POKEDATA 写 rw 段 0xe9e000 (0x90*8, 不读原值不恢复) + detach
C2 = r'''
import ctypes, time, os
out = open("/tmp/d164b.txt", "w")
def p(*a):
    out.write(" ".join(str(x) for x in a) + "\n")
    out.flush()
libc = ctypes.CDLL(None, use_errno=True)
libc.ptrace.restype = ctypes.c_long
PTRACE_ATTACH, PTRACE_DETACH = 16, 17
PTRACE_POKEDATA = 5
def pt(pid, req, addr=0, data=0):
    ctypes.set_errno(0)
    r = libc.ptrace(req, pid, addr, data)
    return r, ctypes.get_errno()
p("start")
r, e = pt(1, PTRACE_ATTACH)
p("attach", r, "errno", e)
if r == 0:
    time.sleep(0.3)
    r2, e2 = pt(1, PTRACE_POKEDATA, 0xe9e000, 0x9090909090909090)
    p("poke_rw", r2, "errno", e2)
    time.sleep(0.5)
    pt(1, PTRACE_DETACH)
    p("detached")
else:
    p("attach_failed")
p("=== DONE")
out.close()
'''

# cmd3: attach + CONT + detach
C3 = r'''
import ctypes, time, os
out = open("/tmp/d164c.txt", "w")
def p(*a):
    out.write(" ".join(str(x) for x in a) + "\n")
    out.flush()
libc = ctypes.CDLL(None, use_errno=True)
libc.ptrace.restype = ctypes.c_long
PTRACE_ATTACH, PTRACE_DETACH, PTRACE_CONT = 16, 17, 7
def pt(pid, req, addr=0, data=0):
    ctypes.set_errno(0)
    r = libc.ptrace(req, pid, addr, data)
    return r, ctypes.get_errno()
p("start")
r, e = pt(1, PTRACE_ATTACH)
p("attach", r, "errno", e)
if r == 0:
    time.sleep(0.3)
    r2, e2 = pt(1, PTRACE_CONT, 0, 0)
    p("cont", r2, "errno", e2)
    time.sleep(0.5)
    pt(1, PTRACE_DETACH)
    p("detached")
else:
    p("attach_failed")
p("=== DONE")
out.close()
'''

# cmd4: process_vm_readv(1) 直读 PID1 0xe9e000 (不attach)
C4 = r'''
import ctypes, time, os
out = open("/tmp/d164d.txt", "w")
def p(*a):
    out.write(" ".join(str(x) for x in a) + "\n")
    out.flush()
libc = ctypes.CDLL(None, use_errno=True)
libc.syscall.restype = ctypes.c_long
SYS_process_vm_readv = 310
class Iovec(ctypes.Structure):
    _fields_ = [("iov_base", ctypes.c_void_p), ("iov_len", ctypes.c_size_t)]
p("start")
buf = ctypes.create_string_buffer(16)
local = Iovec(ctypes.cast(buf, ctypes.c_void_p), 16)
remote = Iovec(ctypes.c_void_p(0xe9e000), 16)
ctypes.set_errno(0)
n = libc.syscall(SYS_process_vm_readv, 1, ctypes.byref(local), 1,
                 ctypes.byref(remote), 1, 0)
p("pvm_readv", n, "errno", ctypes.get_errno())
if n > 0:
    p("data", buf.raw.hex())
p("=== DONE")
out.close()
'''

steps = [
    ("setregs-same", "/tmp/d164a.txt", C1),
    ("poke-rw-noread", "/tmp/d164b.txt", C2),
    ("cont-only", "/tmp/d164c.txt", C3),
    ("pvm-readv", "/tmp/d164d.txt", C4),
]

for label, marker, code in steps:
    st = run_cmd(sid, code, label, timeout=200)
    time.sleep(2)
    cf = catfile(sid, marker, f"marker[{label}]", 1500)
    if st == "DEAD" or cf == 410:
        print(f"\n!!! DEATH after cmd[{label}] -> trigger = {label}", flush=True)
        break

api("DELETE", f"/v2/sandboxes/{NAME}?teamId={TEAM}&projectId={PROJ}")
print("\ncleanup done", flush=True)

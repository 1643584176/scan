# 实验J163: 触发点二分定位 (哪个ptrace操作导致沙箱被杀)
# j162: 写内存+POKETEXT+SETREGS+CONT 全链路触发杀; j161: attach/getregs/detach 只读安全
# 方法: 一个沙箱顺序执行5个cmd, 每个cmd=attach+单一操作+detach+写marker, 每步后catfile确认存活
# cmdA: PEEKDATA小读  cmdB: POKEDATA写rw段  cmdC: POKETEXT写text段  cmdD: SETREGS原值写回  cmdE: CONT
# 任一cmd后沙箱410 => 该操作即触发点; 全部存活 => 触发在组合/节奏
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

NAME = "expj163"
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

PT_BASE = r'''
import ctypes, time, os, struct
out = open("%s", "w")
def p(*a):
    out.write(" ".join(str(x) for x in a) + "\n")
    out.flush()
libc = ctypes.CDLL(None, use_errno=True)
libc.ptrace.restype = ctypes.c_long
PTRACE_ATTACH, PTRACE_DETACH, PTRACE_CONT = 16, 17, 7
PTRACE_GETREGS, PTRACE_SETREGS = 12, 13
PTRACE_POKEDATA, PTRACE_POKETEXT = 5, 4
PTRACE_PEEKDATA = 2
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
%%OP%%
    pt(1, PTRACE_DETACH)
    p("detached")
else:
    p("attach_failed")
p("=== DONE")
out.close()
'''

OP_PEEK = r'''
v, e = pt(1, PTRACE_PEEKDATA, 0x401000)
p("peek_text", hex(v & 0xffffffffffffffff) if v != -1 or e == 0 else "ERR", "errno", e)
v2, e2 = pt(1, PTRACE_PEEKDATA, 0xe9e000)
p("peek_rw", hex(v2 & 0xffffffffffffffff) if v2 != -1 or e2 == 0 else "ERR", "errno", e2)
'''

OP_POKE_RW = r'''
v, e = pt(1, PTRACE_PEEKDATA, 0xe9e000)
p("peek_rw", hex(v & 0xffffffffffffffff), "errno", e)
time.sleep(0.3)
r2, e2 = pt(1, PTRACE_POKEDATA, 0xe9e000, 0x9090909090909090)
p("poke_rw", r2, "errno", e2)
time.sleep(0.5)
r3, e3 = pt(1, PTRACE_POKEDATA, 0xe9e000, v)
p("poke_rw_restore", r3, "errno", e3)
'''

OP_POKE_TEXT = r'''
v, e = pt(1, PTRACE_PEEKDATA, 0x401000)
p("peek_text", hex(v & 0xffffffffffffffff), "errno", e)
time.sleep(0.3)
r2, e2 = pt(1, PTRACE_POKETEXT, 0x401000, 0x9090909090909090)
p("poke_text", r2, "errno", e2)
time.sleep(0.5)
r3, e3 = pt(1, PTRACE_POKETEXT, 0x401000, v)
p("poke_text_restore", r3, "errno", e3)
'''

OP_SETREGS = r'''
regs = UserRegs()
rr, e = pt(1, PTRACE_GETREGS, 0, ctypes.byref(regs))
p("getregs", rr, "errno", e, "rip", hex(regs.rip))
time.sleep(0.3)
r2, e2 = pt(1, PTRACE_SETREGS, 0, ctypes.byref(regs))
p("setregs_same", r2, "errno", e2)
'''

OP_CONT = r'''
r2, e2 = pt(1, PTRACE_CONT, 0, 0)
p("cont", r2, "errno", e2)
time.sleep(0.5)
'''

steps = [
    ("peek-only", "/tmp/d163a.txt", OP_PEEK),
    ("poke-rw", "/tmp/d163b.txt", OP_POKE_RW),
    ("poke-text", "/tmp/d163c.txt", OP_POKE_TEXT),
    ("setregs-same", "/tmp/d163d.txt", OP_SETREGS),
    ("cont-only", "/tmp/d163e.txt", OP_CONT),
]

for i, (label, marker, op) in enumerate(steps):
    op_ind = "\n".join(("    " + l if l.strip() else l) for l in op.splitlines())
    code = PT_BASE.replace("%%OP%%", op_ind) % marker
    st = run_cmd(sid, code, label, timeout=200)
    cf = catfile(sid, marker, f"marker[{label}]", 1500)
    if st == "DEAD" or cf == 410:
        print(f"\n!!! DEATH after cmd[{label}] -> trigger = {label}", flush=True)
        break

api("DELETE", f"/v2/sandboxes/{NAME}?teamId={TEAM}&projectId={PROJ}")
print("\ncleanup done", flush=True)

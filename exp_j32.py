# 实验J32: XFS 完整提取 - 短目录 inode(块131) → entries → inumber → inode → extent → 文件内容
# 依据: J31c 确认 536576 是 inode 块, 内含短目录 "celld.toml/xkernel.toml" (local format)
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

def run_cmd(sid, code, label, wait=True, timeout=200):
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

NAME = "expj32"
api("DELETE", f"/v2/sandboxes/{NAME}?teamId={TEAM}&projectId={PROJ}")
c, r = api("POST", f"/v2/sandboxes?teamId={TEAM}",
           {"projectId": PROJ, "name": NAME,
            "networkPolicy": {"mode": "custom", "allowedDomains": ["httpbin.org"]}})
print("create:", c)
sid = json.loads(r)["sandbox"]["currentSessionId"]
print("sid:", sid)

SCAN = r'''
import struct

def be16(d, o): return struct.unpack_from(">H", d, o)[0]
def be32(d, o): return struct.unpack_from(">I", d, o)[0]
def be64(d, o): return struct.unpack_from(">Q", d, o)[0]

f = open("/dev/vda", "rb", buffering=0)
f.seek(0)
sb = f.read(512)
bs = be32(sb, 0x04)
dblocks = be64(sb, 0x08)
rootino = be64(sb, 0x38)
agblocks = be32(sb, 0x54)
agcount = be32(sb, 0x58)
inodesize = be16(sb, 0x68)
inopblock = be16(sb, 0x6A)
inopblog = sb[0x7B]
agblklog = sb[0x7C]
shift = agblklog + inopblog
print("bs=%d agblocks=%d agcount=%d inodesize=%d inopblog=%d agblklog=%d" %
      (bs, agblocks, agcount, inodesize, inopblog, agblklog), flush=True)

# ---- 定位 inode 物理位置 ----
def inode_phys(ino):
    agno = ino >> shift
    agino = ino & ((1 << shift) - 1)
    agbno = agino >> inopblog
    inoff = (agino & (inopblock - 1)) * inodesize
    return agno * agblocks * bs + agbno * bs + inoff, agno, agino

def read_inode(ino):
    p, _, _ = inode_phys(ino)
    f.seek(p)
    return f.read(inodesize), p

def inode_info(ino):
    d, p = read_inode(ino)
    magic = d[:2]
    mode = be16(d, 2)
    ver = d[4]
    fmt = d[5]
    size = be64(d, 56)
    nxt = be32(d, 76)
    return d, p, magic, mode, ver, fmt, size, nxt

# ---- 解析块 131 (536576) 的 8 个 inode, 找短目录 ----
IBLK = 536576
base_agino = 1024 + (IBLK - 128 * bs) // bs * inopblock  # rootino=1024 在块128
print("block131 inodes:", base_agino, "..", base_agino + inopblock - 1, flush=True)

di = {}
for i in range(inopblock):
    ino = base_agino + i
    d, p, magic, mode, ver, fmt, size, nxt = inode_info(ino)
    print("ino=%d phys=%d magic=%r fmt=%d size=%d mode=%o" % (ino, p, magic, fmt, size, mode), flush=True)
    if fmt == 2:  # local
        data = d[160:160+min(size, inodesize-160)]
        print("  local[%d]: %r" % (len(data), data[:120]), flush=True)
    di[ino] = (d, fmt, size)

# ---- 找含 celld.toml 的短目录并解析 entries ----
target = None
for ino, (d, fmt, size) in di.items():
    if fmt == 2 and b"celld.toml" in d[160:160+size]:
        target = ino
        break
if target is None:
    raise SystemExit("shortform dir not found in block131")
data = di[target][0][160:160+di[target][2]]
print("SHORTFORM DIR ino=%d size=%d hex=%s" % (target, len(data), data[:64].hex()), flush=True)

# 短目录解析: count@0, i8count@1, parent(4或8), entries: namelen(1)+offset(2)+name+inumber(4或8)
count = data[0]
i8count = data[1]

def try_parse(data, psize, ino_size):
    out = []
    off = 2 + psize
    for _ in range(data[0]):
        if off + 3 > len(data):
            return None
        namelen = data[off]
        off += 3
        name = data[off:off+namelen].decode(errors="replace")
        off += namelen
        ino = struct.unpack_from(">Q", data, off)[0] if ino_size == 8 else data[off]
        if ino_size == 4:
            ino = struct.unpack_from(">I", data, off)[0]
        out.append((ino, name))
        off += ino_size
    return out

entries = None
for psize in (4, 8):
    e = try_parse(data, psize, 8 if i8count else 4)
    if e and all(0 < len(n) <= 255 for _, n in e):
        entries = e
        break
if entries is None:
    print("parse failed, raw:", data.hex(), flush=True)
    raise SystemExit("shortform parse fail")
print("DIR entries (%d, i8count=%d):" % (len(entries), i8count), flush=True)
for ino, name in entries:
    print("  ino=%d %r" % (ino, name), flush=True)

# ---- 提取每个文件 ----
def read_extents(fork, depth, limit):
    # fork: bmbt 数据 (extents format: rec 数组直接开始; btree: root block)
    if depth == 0:
        n = len(fork) // 16
        out = b""
        for i in range(n):
            rec = fork[i*16:i*16+16]
            l0 = be64(rec, 0)
            l1 = be64(rec, 8)
            startoff = l0 >> 12
            startblock = ((l0 & 0xFFF) << 43) | (l1 >> 21)
            blockcount = l1 & 0x1FFFFF
            agno = startblock >> agblklog
            agbno = startblock & ((1 << agblklog) - 1)
            base = agno * agblocks * bs + agbno * bs
            for b in range(blockcount):
                f.seek(base + b * bs)
                out += f.read(bs)
                if len(out) >= limit:
                    return out[:limit], startoff, blockcount
        return out, 0, 0
    # btree: 暂不支持 (配置文件不会大)
    return b"", 0, 0

for ino, name in entries:
    d, p, magic, mode, ver, fmt, size, nxt = inode_info(ino)
    if magic != b"IN":
        print("%s: bad inode" % name, flush=True)
        continue
    if fmt == 2:  # local
        content = d[160:160+size]
        print("===== FILE %s (local, %d B) =====" % (name, len(content)), flush=True)
        print(content.decode(errors="replace")[:8000], flush=True)
        print("===== END %s =====" % name, flush=True)
    elif fmt == 3:  # extents
        fork = d[160:160+inodesize-160]
        content, _, _ = read_extents(fork, 0, size)
        print("===== FILE %s (extents, %d B) =====" % (name, len(content)), flush=True)
        print(content[:8000].decode(errors="replace"), flush=True)
        print("===== END %s =====" % name, flush=True)
    else:
        print("%s: fmt=%d unsupported" % (name, fmt), flush=True)
'''
run_cmd(sid, SCAN, "xfs-extract", wait=True, timeout=120000)

api("DELETE", f"/v2/sandboxes/{NAME}?teamId={TEAM}&projectId={PROJ}")
print("\ncleanup done", flush=True)

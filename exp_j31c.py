# 实验J31c: XFS 大端解析 - superblock + 目录块(536576) entry 结构, 提取 inumber 映射
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

NAME = "expj31c"
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
print("magic:", sb[:4], flush=True)
bs = be32(sb, 0x04)
dblocks = be64(sb, 0x08)
uuid = sb[0x20:0x30].hex()
rootino = be64(sb, 0x38)
agblocks = be32(sb, 0x54)
agcount = be32(sb, 0x58)
inodesize = be16(sb, 0x68)
inopblock = be16(sb, 0x6A)
blocklog = sb[0x78]
inodelog = sb[0x7A]
inopblog = sb[0x7B]
agblklog = sb[0x7C]
print("bs=%d dblocks=%d (~%dMB) uuid=%s" % (bs, dblocks, dblocks*bs//1024//1024, uuid), flush=True)
print("rootino=%d agblocks=%d agcount=%d inodesize=%d inopblock=%d" %
      (rootino, agblocks, agcount, inodesize, inopblock), flush=True)
print("blocklog=%d inodelog=%d inopblog=%d agblklog=%d" %
      (blocklog, inodelog, inopblog, agblklog), flush=True)

# rootino 编码解码
shift = agblklog + inopblog
agno = rootino >> shift
agino = rootino & ((1 << shift) - 1)
print("rootino -> agno=%d agino=%d" % (agno, agino), flush=True)

# 目录块 536576
DIR = 538849
blk = DIR // bs
f.seek(blk * bs)
d = f.read(bs)
print("dirblk %d magic=%r hex64=%s" % (blk*bs, d[:4], d[:64].hex()), flush=True)

# 解析 dir2/dir3 data block entries
def parse_dir(blkdata, bs):
    magic = blkdata[:4]
    out = []
    if magic == b"XDB2":
        hdr = 28  # v2: magic4 + bestfree[3]*8
        ent_off = hdr
    elif magic == b"XDDB":
        hdr = 64  # v3
        ent_off = hdr
    else:
        return out
    while ent_off + 11 <= bs:
        ino = be64(blkdata, ent_off)
        if ino == 0:
            break
        namelen = blkdata[ent_off+8]
        name = blkdata[ent_off+9:ent_off+9+namelen].decode(errors="replace")
        out.append((ino, name))
        ent_off += 9 + namelen + 2
        if ent_off >= bs:
            break
    return out

entries = parse_dir(d, bs)
print("DIR entries (%d):" % len(entries), flush=True)
for ino, name in entries:
    print("  ino=%d %r" % (ino, name), flush=True)

# 验证 root inode: 解码 rootino 物理位置
# agino 物理: agbno = agino >> inopblog; inoff = (agino & (inopblock-1)) * inodesize
agbno = agino >> inopblog
inoff = (agino & (inopblock - 1)) * inodesize
phys = agno * agblocks * bs + agbno * bs + inoff
f.seek(phys)
inode = f.read(inodesize)
print("root inode phys=%d magic=%r" % (phys, inode[:2]), flush=True)
'''
run_cmd(sid, SCAN, "xfs-probe2", wait=True, timeout=90000)

api("DELETE", f"/v2/sandboxes/{NAME}?teamId={TEAM}&projectId={PROJ}")
print("\ncleanup done", flush=True)

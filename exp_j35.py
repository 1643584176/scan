# 实验J35: 完整解析 inode 1042/1043/1044 + 全盘搜 16B 头模式 + extent 指针解码
# 依据: J34 确认 di_ino=1042(目录)/1043(celld.toml)/1044(xkernel.toml), data fork 前16B固定
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

NAME = "expj35"
api("DELETE", f"/v2/sandboxes/{NAME}?teamId={TEAM}&projectId={PROJ}")
c, r = api("POST", f"/v2/sandboxes?teamId={TEAM}",
           {"projectId": PROJ, "name": NAME,
            "networkPolicy": {"mode": "custom", "allowedDomains": ["httpbin.org"]}})
print("create:", c)
sid = json.loads(r)["sandbox"]["currentSessionId"]
print("sid:", sid)

SCAN = r'''
import struct, re

def be16(d, o): return struct.unpack_from(">H", d, o)[0]
def be32(d, o): return struct.unpack_from(">I", d, o)[0]
def be64(d, o): return struct.unpack_from(">Q", d, o)[0]

f = open("/dev/vda", "rb", buffering=0)
sb = f.read(512)
bs = be32(sb, 0x04)
agblocks = be32(sb, 0x54)
inodesize = be16(sb, 0x68)
inopblock = be16(sb, 0x6A)
inopblog = sb[0x7B]
agblklog = sb[0x7C]
shift = agblklog + inopblog

def inode_phys(ino):
    agno = ino >> shift
    agino = ino & ((1 << shift) - 1)
    agbno = agino >> inopblog
    inoff = (agino & (inopblock - 1)) * inodesize
    return agno * agblocks * bs + agbno * bs + inoff

def dump_inode(ino, label):
    p = inode_phys(ino)
    f.seek(p)
    d = f.read(inodesize)
    print("===== inode %d @%d (%s) =====" % (ino, p, label), flush=True)
    print("magic=%r mode=%#06x ver=%d fmt=%d nlink=%d" %
          (d[:2], be16(d,2), d[4], d[5], be32(d,0x10)), flush=True)
    print("size=%d nblocks=%d nextents=%d anextents=%d" %
          (be64(d,0x38), be64(d,0x40), be32(d,0x4c), be16(d,0x50)), flush=True)
    print("forkoff=%d aformat=%d flags=%#x gen=%d crc=%#x" %
          (d[0x52], d[0x53], be16(d,0x5a), be32(d,0x5c), be32(d,0x64)), flush=True)
    print("flags2=%#x ino=%d" % (be64(d,0x78), be64(d,0x90)), flush=True)
    fork = d[160:160+32]
    print("fork32: %s" % fork.hex(), flush=True)
    # fork 内尝试解析 extent rec
    if len(fork) >= 16:
        l0 = be64(fork, 0); l1 = be64(fork, 8)
        startoff = l0 >> 12
        startblock = ((l0 & 0xFFF) << 43) | (l1 >> 21)
        blockcount = l1 & 0x1FFFFF
        print("bmbt(be): startoff=%d startblock=%d blockcount=%d" %
              (startoff, startblock, blockcount), flush=True)
    # attr fork 区域 (192 起) 前 64B
    print("attr64: %s" % d[192:256].hex(), flush=True)
    print("attr-ascii:", d[192:320], flush=True)
    return d

d1042 = dump_inode(1042, "DIR(celld.toml)")
d1043 = dump_inode(1043, "FILE celld.toml?")
d1044 = dump_inode(1044, "FILE xkernel.toml?")

# 全盘搜 16B 头模式分布 (0-100MB)
HDR = bytes.fromhex("cf913b1427c04adca9f65887fdbee93e")
print("===== HDR pattern search =====", flush=True)
t0 = time.time()
hits = []
CH = 4*1024*1024
off = 0
while off < 100*1024*1024:
    f.seek(off)
    d = f.read(CH)
    if not d:
        break
    for m in re.finditer(HDR, d):
        hits.append(off + m.start())
    off += len(d)
print("hdr hits: %d, %s (%.1fs)" % (len(hits), sorted(hits)[:40], time.time()-t0), flush=True)

# 11 a0 / 11 c0 模式搜
for pat, tag in [(bytes.fromhex("11a00001"), "11a00001"), (bytes.fromhex("11c00001"), "11c00001")]:
    hits2 = []
    off = 0
    while off < 100*1024*1024:
        f.seek(off)
        d = f.read(CH)
        if not d:
            break
        for m in re.finditer(pat, d):
            hits2.append(off + m.start())
        off += len(d)
    print("[%s] %d hits: %s" % (tag, len(hits2), sorted(hits2)[:20]), flush=True)
'''
run_cmd(sid, SCAN, "inode-deep", wait=True, timeout=400000)

api("DELETE", f"/v2/sandboxes/{NAME}?teamId={TEAM}&projectId={PROJ}")
print("\ncleanup done", flush=True)

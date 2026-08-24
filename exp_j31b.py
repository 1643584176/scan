# 实验J31b: XFS 探针 - 找 XFSB superblock, 解析目录块(536576)结构, 确认 dir2/dir3 布局
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

NAME = "expj31b"
api("DELETE", f"/v2/sandboxes/{NAME}?teamId={TEAM}&projectId={PROJ}")
c, r = api("POST", f"/v2/sandboxes?teamId={TEAM}",
           {"projectId": PROJ, "name": NAME,
            "networkPolicy": {"mode": "custom", "allowedDomains": ["httpbin.org"]}})
print("create:", c)
sid = json.loads(r)["sandbox"]["currentSessionId"]
print("sid:", sid)

SCAN = r'''
import struct

def u16(d, o): return struct.unpack_from("<H", d, o)[0]
def u32(d, o): return struct.unpack_from("<I", d, o)[0]
def u64(d, o): return struct.unpack_from("<Q", d, o)[0]

f = open("/dev/vda", "rb", buffering=0)

# 1. 扫前 8MB 找 XFSB
found = []
for off in range(0, 8*1024*1024, 512):
    f.seek(off)
    d = f.read(4)
    if d == b"XFSB":
        found.append(off)
print("XFSB offsets:", found[:10], flush=True)
if not found:
    raise SystemExit("no XFSB")

sb_off = found[0]
f.seek(sb_off)
sb = f.read(1024)
bs = u32(sb, 0x04)
dblocks = u64(sb, 0x08)
uuid = sb[32:48].hex()
rootino = u64(sb, 0x38)
agblocks = u32(sb, 0x54)
agcount = u32(sb, 0x58)
versionnum = u16(sb, 0x64)
sectsize = u16(sb, 0x66)
inodesize = u16(sb, 0x68)
inopblock = u16(sb, 0x6A)
fname = sb[0x6C:0x6C+12]
blocklog = sb[0x78]
sectlog = sb[0x79]
inodelog = sb[0x7A]
inopblog = sb[0x7B]
agblklog = sb[0x7C]
rextslog = sb[0x7D]
print("SB@%d bs=%d dblocks=%d uuid=%s rootino=%d" % (sb_off, bs, dblocks, uuid, rootino), flush=True)
print("agblocks=%d agcount=%d ver=%#x sectsize=%d inodesize=%d inopblock=%d" %
      (agblocks, agcount, versionnum, sectsize, inodesize, inopblock), flush=True)
print("fname=%r blocklog=%d sectlog=%d inodelog=%d inopblog=%d agblklog=%d" %
      (fname, blocklog, sectlog, inodelog, inopblog, agblklog), flush=True)
print("total size ~%d MB" % (dblocks*bs//1024//1024), flush=True)

# 2. 目录块 536576 对齐检查
DIR = 538849
blk = DIR // bs
off = blk * bs
f.seek(off)
blkdata = f.read(bs)
print("dirblk phys=%d hex=%s" % (off, blkdata[:64].hex()), flush=True)
print("dirblk ascii:", blkdata[:64], flush=True)

# 3. AGF/AGI 布局检查: AG0 block1=AGF, block2=AGI
f.seek(bs)
print("AG0 blk1:", f.read(4), flush=True)
f.seek(2*bs)
print("AG0 blk2:", f.read(4), flush=True)
f.seek(3*bs)
print("AG0 blk3:", f.read(4), flush=True)
'''
run_cmd(sid, SCAN, "xfs-probe", wait=True, timeout=90000)

api("DELETE", f"/v2/sandboxes/{NAME}?teamId={TEAM}&projectId={PROJ}")
print("\ncleanup done", flush=True)

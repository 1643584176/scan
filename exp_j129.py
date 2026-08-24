# 实验J129: 设备映射验证 — sandbox-init(ino=125832488) 实际所在设备定位
# 动机: j128 发现 vda XFS(33GB, agcount=16) 最大 inode 仅 69M < 125832488,
#       sandbox-init 不在 vda 上; 需确认 st_dev 映射 + vdb superblock + /dev 全设备
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

def run_cmd(sid, code, label, wait=True, timeout=120, args=None):
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

NAME = "expj129"
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

PROBE = r"""
import os, struct

# [1] /dev 全部设备 + partitions
print("== /proc/partitions ==", flush=True)
print(open("/proc/partitions").read(), flush=True)
print("== ls -la /dev ==", flush=True)
for f in sorted(os.listdir("/dev")):
    try:
        st = os.stat("/dev/" + f)
        print("%-16s dev=%d:%d rdev=%d:%d" % (f, os.major(st.st_dev), os.minor(st.st_dev),
                                               os.major(st.st_rdev), os.minor(st.st_rdev)), flush=True)
    except Exception as e:
        print("%-16s ERR %s" % (f, e), flush=True)

# [2] 关键路径 st_dev 映射
print("== stat st_dev ==", flush=True)
for p in ["/dev/vda", "/dev/vdb", "/run/vercel/share", "/run/vercel/share/sandbox-init",
          "/run/vercel/share/init.sock", "/etc/pki/ca-trust/source/anchors/vercel-proxy-ca.pem",
          "/vercel/sandbox", "/root", "/"]:
    try:
        st = os.stat(p)
        print("%-70s dev=%d:%d ino=%d" % (p, os.major(st.st_dev), os.minor(st.st_dev), st.st_ino), flush=True)
    except Exception as e:
        print("%-70s ERR %s" % (p, e), flush=True)

# [3] mount 全貌
print("== /proc/self/mounts ==", flush=True)
for line in open("/proc/self/mounts"):
    print(line.rstrip(), flush=True)

# [4] vdb superblock 解析
def be16(b, o): return struct.unpack_from(">H", b, o)[0]
def be32(b, o): return struct.unpack_from(">I", b, o)[0]
def be64(b, o): return struct.unpack_from(">Q", b, o)[0]
for dev, size in [("/dev/vda", 35433480192), ("/dev/vdb", 34359738368)]:
    try:
        f = open(dev, "rb", buffering=0)
        sb = f.read(512)
        f.close()
        if sb[:4] != b"XFSB":
            print(dev, "NOT XFS", sb[:16], flush=True)
            continue
        bs = be32(sb, 0x04)
        dblocks = be64(sb, 0x08)
        agblocks = be32(sb, 0x54)
        agcount = be32(sb, 0x58)
        inodesize = be16(sb, 0x68)
        inopblock = be16(sb, 0x6a)
        max_ino = agcount * agblocks * inopblock
        print("%s bs=%d dblocks=%d agblocks=%d agcount=%d inodesize=%d inopblock=%d max_ino=%d"
              % (dev, bs, dblocks, agblocks, agcount, inodesize, inopblock, max_ino), flush=True)
        print("  can_hold_125832488:", max_ino > 125832488, flush=True)
    except Exception as e:
        print(dev, "ERR", type(e).__name__, e, flush=True)

print("PROBE_DONE", flush=True)
"""
run_cmd(sid, PROBE, "dev-probe")

api("DELETE", f"/v2/sandboxes/{NAME}?teamId={TEAM}&projectId={PROJ}")
print("\ncleanup done", flush=True)

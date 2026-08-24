# 实验J226: 全内存搜真实pub (9cab29062e6d040002c3cbc8ad4be45e392ff7009cc1baa7645feed3b7105c7e)
# 只搜 rw-p 段 (pub在heap/argv区, 不在text) 避免 j216 被杀问题
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

NAME = "expj226"
api("DELETE", f"/v2/sandboxes/{NAME}?teamId={TEAM}&projectId={PROJ}")
c, r = api("POST", f"/v2/sandboxes?teamId={TEAM}",
           {"projectId": PROJ, "name": NAME})
print("create:", c, flush=True)
if c != 200:
    print(r[:400], flush=True)
    sys.exit(1)
sid = json.loads(r)["sandbox"]["currentSessionId"]
print("sid:", sid, flush=True)

CODE = r'''
import os, struct
out = open("/tmp/d226.txt", "w")
def p(*a):
    line = " ".join(str(x) for x in a)
    out.write(line + "\n"); out.flush()
    print(line, flush=True)

PUB = bytes.fromhex("9cab29062e6d040002c3cbc8ad4be45e392ff7009cc1baa7645feed3b7105c7e")
PUBB64 = b"nKspBi5tBAACw8vIrUvkXjkv9wCcwLqnZF/u07cQXH4="

fd = os.open("/proc/1/mem", os.O_RDWR)
def ra(a, n):
    os.lseek(fd, a, 0)
    return os.read(fd, n)

maps = open("/proc/1/maps").read()
rw = []
for ln in maps.splitlines():
    rng, perm, off, dev, ino, *rest = ln.split()
    if "rw" in perm:
        lo, hi = (int(x, 16) for x in rng.split("-"))
        if hi - lo >= 0x4000:
            rw.append((lo, hi))
p("RW_SEGS", [(hex(a), hex(b), b - a) for a, b in rw])

hits = 0
for lo, hi in rw:
    off = lo
    while off < hi:
        n = min(0x400000, hi - off)
        try:
            b = ra(off, n)
        except OSError:
            off += n
            continue
        for pat_name, pat in (("PUB32", PUB), ("PUBB64", PUBB64)):
            pos = 0
            while True:
                i = b.find(pat, pos)
                if i < 0:
                    break
                a = off + i
                hits += 1
                ctx = ra(max(lo, a - 0x20), min(0x80, hi - max(lo, a - 0x20)))
                p("HIT", pat_name, hex(a), ctx.hex())
                pos = i + 1
        off += n
p("HITS", hits)
p("done")
out.close()
os.close(fd)
'''
st = run_cmd(sid, CODE, "J226", timeout=280)
time.sleep(1)
bashfile(sid, "cat /tmp/d226.txt", "READOUT", 30000)

api("DELETE", f"/v2/sandboxes/{NAME}?teamId={TEAM}&projectId={PROJ}")
print("\ncleanup done", flush=True)

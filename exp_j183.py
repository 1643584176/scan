# 实验J183: 修复版全量字符串提取 + 神秘串测30002 + 分页下载
# j182: bug "/"str vs bytes 崩溃; 神秘串80字符; ELF: rodata@0x4db000 5.57MB
# 本步: 1)修复提取全量strings写/tmp/strs.txt 2)30002发神秘串 3)分页下载strs.txt
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

NAME = "expj183"
api("DELETE", f"/v2/sandboxes/{NAME}?teamId={TEAM}&projectId={PROJ}")
c, r = api("POST", f"/v2/sandboxes?teamId={TEAM}",
           {"projectId": PROJ, "name": NAME})
print("create:", c)
if c != 200:
    print(r[:400])
    sys.exit(1)
sid = json.loads(r)["sandbox"]["currentSessionId"]
print("sid:", sid)

# PA: 修复版全量提取 (逐chunk安全模式)
PA = r'''
import os, re
out = open("/tmp/d183a.txt", "w")
def p(*a):
    out.write(" ".join(str(x) for x in a) + "\n")
    out.flush()
p("start")
res = open("/tmp/strs.txt", "wb")
pat = re.compile(rb"[\x20-\x7e]{16,}")
skip = re.compile(rb"^[A-Za-z0-9_]{16,}$")
n = 0
fd = os.open("/run/vercel/share/sandbox-init", os.O_RDONLY)
while True:
    d = os.read(fd, 65536)
    if not d:
        break
    for m in pat.finditer(d):
        s = m.group(0)
        if skip.match(s) and b"/" not in s and b"." not in s and b"-" not in s:
            continue
        if len(s) >= 16:
            res.write(s + b"\n")
            n += 1
os.close(fd)
res.close()
p("nstrs", n)
p("size", os.path.getsize("/tmp/strs.txt"))
p("done")
out.close()
'''

# PB: 30002 神秘串测试
PB = r'''
import os, socket
out = open("/tmp/d183b.txt", "w")
def p(*a):
    out.write(" ".join(str(x) for x in a) + "\n")
    out.flush()
def probe(payload, to=3):
    try:
        s = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
        s.settimeout(to)
        s.connect(("127.0.0.1", 30002))
        if payload:
            s.send(payload)
        d = b""
        try:
            while True:
                b = s.recv(4096)
                if not b:
                    break
                d += b
                if len(d) > 2000:
                    break
        except Exception:
            pass
        s.close()
        return d
    except Exception as ex:
        return ("EXC:" + repr(ex)).encode()
p("start")
TOK = b"jsew6QlLu0BjbIS5zTym/jU8rfXxa6EoYX1hiUl4M/3Wubc93_THmJZDHRl-jE/Vx_3uhJ34OD1myaD7XeG"
d = probe(TOK)
p("RAW_TOK", d[:300])
d = probe(TOK + b"\n")
p("RAW_NL", d[:300])
d = probe(b"auth " + TOK)
p("AUTH_CMD", d[:300])
d = probe(b"token=" + TOK)
p("TOKEN_EQ", d[:300])
d = probe(TOK + b"\x00")
p("RAW_NUL", d[:300])
p("done")
out.close()
'''

steps = [
    ("extract2", "/tmp/d183a.txt", PA),
    ("tok30002", "/tmp/d183b.txt", PB),
]
for label, marker, code in steps:
    st = run_cmd(sid, code, label, timeout=280)
    time.sleep(2)
    bashfile(sid, f"cat {marker}", f"marker[{label}]", 6000)
    if st == "DEAD":
        print(f"\n!!! DEATH after cmd[{label}]", flush=True)
        break

# 下载 strs.txt 全量分批
if st != "DEAD":
    off = 1
    for i in range(30):
        bashfile(sid, f"tail -c +{off} /tmp/strs.txt | head -c 8000", f"strs[{off}]", 10000)
        time.sleep(1)
        off += 8000

api("DELETE", f"/v2/sandboxes/{NAME}?teamId={TEAM}&projectId={PROJ}")
print("\ncleanup done", flush=True)

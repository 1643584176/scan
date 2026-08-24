# 实验J184: rodata段定向提取(跳过text/pclntab) + 业务字符串过滤下载
# j183: 全量提取被杀在Go类型元数据(48KB); 发现 connect.Interceptor(connectrpc!); 30002不吃token
# 本步: 1)从rodata段(0x4db000)开始提取 2)过滤: 只留含/ . : 空格的业务串
#       3)输出到文件分批下载 4)统计识别 30002 服务名
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

NAME = "expj184"
api("DELETE", f"/v2/sandboxes/{NAME}?teamId={TEAM}&projectId={PROJ}")
c, r = api("POST", f"/v2/sandboxes?teamId={TEAM}",
           {"projectId": PROJ, "name": NAME})
print("create:", c)
if c != 200:
    print(r[:400])
    sys.exit(1)
sid = json.loads(r)["sandbox"]["currentSessionId"]
print("sid:", sid)

# PA: rodata段提取 + 业务串过滤 (逐chunk)
PA = r'''
import os, re
out = open("/tmp/d184a.txt", "w")
def p(*a):
    out.write(" ".join(str(x) for x in a) + "\n")
    out.flush()
p("start")
res = open("/tmp/biz.txt", "wb")
pat = re.compile(rb"[\x20-\x7e]{8,}")
# 业务串特征: 含 / . : 空格 = 2+, 且不是纯Go类型名
n = 0
RODATA_OFF = 0x4db000
RODATA_LEN = 0x554cb8
fd = os.open("/run/vercel/share/sandbox-init", os.O_RDONLY)
pos = 0
while pos < RODATA_LEN:
    os.lseek(fd, RODATA_OFF + pos, 0)
    d = os.read(fd, 65536)
    if not d:
        break
    for m in pat.finditer(d):
        s = m.group(0)
        # 过滤 Go 类型噪音
        if s.startswith(b"*") or s.startswith(b"func(") or s.startswith(b"type "):
            continue
        if b"/" in s or b"." in s or b" " in s or b":" in s or b"%" in s:
            res.write(s + b"\n")
            n += 1
    pos += len(d)
os.close(fd)
res.close()
p("nbiz", n)
p("size", os.path.getsize("/tmp/biz.txt"))
p("done")
out.close()
'''

# PB: biz.txt 分页统计 + 关键词命中
PB = r'''
import os, re
out = open("/tmp/d184b.txt", "w")
def p(*a):
    out.write(" ".join(str(x) for x in a) + "\n")
    out.flush()
p("start")
d = open("/tmp/biz.txt", "rb").read()
p("size", len(d))
keys = [b"vercel", b"30002", b"30001", b"23456", b"grpc", b"connect", b"route",
        b"rpc", b"service", b"command", b"exec", b"spawn", b"pty", b"socket",
        b"health", b"auth", b"token", b"error", b"failed", b"invalid", b"method",
        b"proto", b"handshake", b"control", b"agent", b"api", b"ws", b"stream"]
for k in keys:
    hits = [ln for ln in d.split(b"\n") if k in ln.lower()]
    if hits:
        p("KEY", k.decode(), "n", len(hits))
        for h in hits[:8]:
            p("  ", h[:200])
p("done")
out.close()
'''

steps = [
    ("rodata-extract", "/tmp/d184a.txt", PA),
    ("biz-stats", "/tmp/d184b.txt", PB),
]
for label, marker, code in steps:
    st = run_cmd(sid, code, label, timeout=280)
    time.sleep(2)
    bashfile(sid, f"cat {marker}", f"marker[{label}]", 8000)
    if st == "DEAD":
        print(f"\n!!! DEATH after cmd[{label}]", flush=True)
        break

# 下载 biz.txt 分批
if st != "DEAD":
    off = 1
    for i in range(40):
        bashfile(sid, f"tail -c +{off} /tmp/biz.txt | head -c 8000", f"biz[{off}]", 10000)
        time.sleep(1)
        off += 8000

api("DELETE", f"/v2/sandboxes/{NAME}?teamId={TEAM}&projectId={PROJ}")
print("\ncleanup done", flush=True)

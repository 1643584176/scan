# 实验J219: 触发verify后观察全局状态变化
# 关键: 发请求的python3进程会被杀, 但读内存的是独立进程不受影响
# bash: (python3 发请求 &) ; sleep; python3 读内存对比前后
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
               {"command": "bash", "args": ["-c", cmd], "wait": True, "logs": True, "timeout": 120})
    print(f"=== {label} status {c} ===", flush=True)
    print(r[:n], flush=True)
    return c

NAME = "expj219"
api("DELETE", f"/v2/sandboxes/{NAME}?teamId={TEAM}&projectId={PROJ}")
c, r = api("POST", f"/v2/sandboxes?teamId={TEAM}",
           {"projectId": PROJ, "name": NAME})
print("create:", c, flush=True)
if c != 200:
    print(r[:400], flush=True)
    sys.exit(1)
sid = json.loads(r)["sandbox"]["currentSessionId"]
print("sid:", sid, flush=True)

READER = r'''
import os, struct
fd = os.open("/proc/1/mem", os.O_RDWR)
def ra(a, n):
    os.lseek(fd, a, 0)
    return os.read(fd, n)
def dump(name, g):
    try:
        b = ra(g, 0x18)
        ptr, ln, cap = struct.unpack_from("<QQQ", b)
        print(name, hex(g), "ptr", hex(ptr), "len", ln, "cap", cap, flush=True)
        if ptr and 0x10000 < ptr < 0x800000000000 and 0 < ln <= 0x100:
            print(name, "OBJ", ra(ptr, ln).hex(), flush=True)
    except Exception as e:
        print(name, "ERR", repr(e), flush=True)
for g in (0xe9e010, 0xe9e610, 0xe9f060, 0xe9f140, 0xe9f1c0):
    dump("G", g)
os.close(fd)
print("READ_DONE", flush=True)
'''

# 阶段0: 请求前基线 (独立进程读内存)
bashfile(sid, "python3 -c '" + READER.replace("'", "'\\''") + "'", "BEFORE", 4000)

# 阶段1: 后台发请求(会被杀,无妨) + 独立进程读内存
REQ_BG = "(python3 -c 'import urllib.request; urllib.request.urlopen(\"http://127.0.0.1:30001/__exp\", timeout=5)' &) ; sleep 2 ; python3 -c '"
bashfile(sid, REQ_BG + READER.replace("'", "'\\''") + "'", "AFTER", 6000)

# 阶段2: 再等2秒, 再读一次 (看异步初始化)
bashfile(sid, "sleep 2 ; python3 -c '" + READER.replace("'", "'\\''") + "'", "AFTER2", 4000)

# 阶段3: 同时发多个不同请求变体 (不同path/body) 观察
MULTI = "(for i in 1 2 3; do python3 -c 'import urllib.request; urllib.request.urlopen(\"http://127.0.0.1:30001/a\"+str($i), timeout=5)' & done) ; sleep 3 ; python3 -c '"
bashfile(sid, MULTI + READER.replace("'", "'\\''") + "'", "AFTER3", 6000)

api("DELETE", f"/v2/sandboxes/{NAME}?teamId={TEAM}&projectId={PROJ}")
print("\ncleanup done", flush=True)

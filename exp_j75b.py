# 实验J75b: 最小化 pidfd_getfd 测试 —— 只读不写,逐步打印
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
    for attempt in range(6):
        c, r = api("POST", f"/v2/sandboxes/sessions/{sid}/cmd?teamId={TEAM}", body)
        if c == 200:
            break
        print(f"  retry[{attempt}] status {c}: {r[:150]}", flush=True)
        time.sleep(4)
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

NAME = "expj75b"
api("DELETE", f"/v2/sandboxes/{NAME}?teamId={TEAM}&projectId={PROJ}")
c, r = api("POST", f"/v2/sandboxes?teamId={TEAM}",
           {"projectId": PROJ, "name": NAME,
            "networkPolicy": {"mode": "custom", "allowedDomains": ["httpbin.org"]}})
print("create:", c)
sid = json.loads(r)["sandbox"]["currentSessionId"]
print("sid:", sid)

PROBE = r"""
import os, struct, ctypes, select, time

libc = ctypes.CDLL(None, use_errno=True)
libc.syscall.restype = ctypes.c_long
def sc(nr, *args):
    ctypes.set_errno(0)
    r = libc.syscall(nr, *args)
    return r, ctypes.get_errno()

print("STEP1 pidfd_open", flush=True)
pfd, e = sc(434, 1, 0)
print("pidfd_open: %d errno=%d" % (pfd, e), flush=True)

print("STEP2 getfd 7", flush=True)
newfd, e2 = sc(438, pfd, 7, 0)
print("getfd(7): fd=%d errno=%d" % (newfd, e2), flush=True)

print("STEP3 read loop 10s", flush=True)
deadline = time.time() + 10
n = 0
while time.time() < deadline:
    n += 1
    rl, _, _ = select.select([newfd], [], [], 0.5)
    if newfd in rl:
        try:
            d = os.read(newfd, 4096)
            print("LOOP%d got %d bytes: %r" % (n, len(d), d[:300]), flush=True)
            if len(d) == 0:
                print("EOF, break", flush=True)
                break
        except Exception as ex:
            print("LOOP%d read EXC %r" % (n, ex), flush=True)
    else:
        print("LOOP%d no data" % n, flush=True)
print("STEP4 done, close", flush=True)
os.close(newfd)
print("STEP5 all done", flush=True)
"""
run_cmd(sid, PROBE, "minimal-getfd", wait=True, timeout=120000)

api("DELETE", f"/v2/sandboxes/{NAME}?teamId={TEAM}&projectId={PROJ}")
print("\ncleanup done", flush=True)

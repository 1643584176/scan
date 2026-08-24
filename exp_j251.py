# 实验J251: 最小化诊断 - vda 最小读取是否触发杀 + 输出管道验证
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

NAME = "expj251"
api("DELETE", f"/v2/sandboxes/{NAME}?teamId={TEAM}&projectId={PROJ}")
c, r = api("POST", f"/v2/sandboxes?teamId={TEAM}",
           {"projectId": PROJ, "name": NAME})
print("create:", c, flush=True)
if c != 200:
    print(r[:400], flush=True)
    sys.exit(1)
sid = json.loads(r)["sandbox"]["currentSessionId"]
print("sid:", sid, flush=True)

CODE_A = r'''
import subprocess, os
print("HELLO_A_1", flush=True)
code = (
    "import os\n"
    "fd = os.open('/dev/vda', os.O_RDONLY)\n"
    "d = os.read(fd, 512)\n"
    "print('MIN_READ', len(d), d[:8].hex(), flush=True)\n"
    "os.close(fd)\n"
)
print("HELLO_A_2", flush=True)
try:
    r = subprocess.run(["sudo", "-n", "python3", "-c", code], capture_output=True, text=True, timeout=10)
    print("MIN_CMD rc", r.returncode, "OUT", (r.stdout + r.stderr)[:300].replace(chr(10), "|"), flush=True)
except Exception as e:
    print("MIN_CMD EXC", type(e).__name__, str(e)[:100], flush=True)
print("DONE_A", flush=True)
'''
run_cmd(sid, CODE_A, "A_MIN", timeout=100)

CODE_B = r'''
import subprocess, os
print("HELLO_B_1", flush=True)
code = (
    "import os\n"
    "fd = os.open('/dev/vda', os.O_RDONLY)\n"
    "os.lseek(fd, 0x100000, 0)\n"
    "d = os.read(fd, 65536)\n"
    "print('OFF1M', len(d), d[:16].hex(), flush=True)\n"
    "os.lseek(fd, 0x10000000, 0)\n"
    "d = os.read(fd, 4096)\n"
    "print('OFF256M', len(d), d[:16].hex(), flush=True)\n"
    "os.close(fd)\n"
)
try:
    r = subprocess.run(["sudo", "-n", "python3", "-c", code], capture_output=True, text=True, timeout=15)
    print("B_CMD rc", r.returncode, "OUT", (r.stdout + r.stderr)[:500].replace(chr(10), "|"), flush=True)
except Exception as e:
    print("B_CMD EXC", type(e).__name__, str(e)[:100], flush=True)
print("DONE_B", flush=True)
'''
run_cmd(sid, CODE_B, "B_OFF", timeout=100)

CODE_C = r'''
import subprocess
print("HELLO_C_1", flush=True)
code = (
    "import os\n"
    "fd = os.open('/dev/vda', os.O_RDONLY)\n"
    "os.lseek(fd, 0, 0)\n"
    "d = os.read(fd, 4096)\n"
    "print('SB', d[:4], flush=True)\n"
    "os.lseek(fd, 0x40000000, 0)\n"
    "d = os.read(fd, 4096)\n"
    "print('OFF1G', len(d), d[:16].hex(), flush=True)\n"
    "os.close(fd)\n"
)
try:
    r = subprocess.run(["sudo", "-n", "python3", "-c", code], capture_output=True, text=True, timeout=15)
    print("C_CMD rc", r.returncode, "OUT", (r.stdout + r.stderr)[:500].replace(chr(10), "|"), flush=True)
except Exception as e:
    print("C_CMD EXC", type(e).__name__, str(e)[:100], flush=True)
print("DONE_C", flush=True)
'''
run_cmd(sid, CODE_C, "C_1G", timeout=100)

api("DELETE", f"/v2/sandboxes/{NAME}?teamId={TEAM}&projectId={PROJ}")
print("\ncleanup done", flush=True)

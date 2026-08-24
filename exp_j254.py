# 实验J254: 最终确认 - vda 镜像与沙箱当前文件系统内容对比
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

NAME = "expj254"
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
import subprocess
code = (
    "import subprocess as sp, os\n"
    "def sh(c):\n"
    "    r = sp.run(c, shell=True, capture_output=True, text=True, timeout=8)\n"
    "    return (r.stdout + r.stderr)[:600]\n"
    "print('PARTITIONS', sh('cat /proc/partitions').replace(chr(10), '|'), flush=True)\n"
    "print('MOUNT', sh('findmnt -o SOURCE,TARGET,FSTYPE 2>/dev/null | head -20').replace(chr(10), '|'), flush=True)\n"
    "print('PYTHON_DIRS', sh('ls -d /usr/lib/python3* 2>/dev/null').replace(chr(10), '|'), flush=True)\n"
    "print('SYS_CONFIG', sh('ls /usr/lib/python3*/_sysconfigdata* 2>/dev/null').replace(chr(10), '|'), flush=True)\n"
    "print('AWS_DOCS', sh('find /usr -name \"list-roles.rst\" 2>/dev/null | head -3').replace(chr(10), '|'), flush=True)\n"
    "# vda 上同一文件名的内容与当前 fs 对比: 读 vda 0xa9000 块 与 当前 python 目录块\n"
    "fd = os.open('/dev/vda', os.O_RDONLY)\n"
    "os.lseek(fd, 0xa9000, 0)\n"
    "b = os.read(fd, 4096)\n"
    "print('VDA_BLK_HAS_ABC', b'abc.py' in b, b'ast.py' in b, flush=True)\n"
    "os.close(fd)\n"
    "# 当前 fs 对应文件\n"
    "r = sp.run('find /usr/lib/python3* -maxdepth 1 -name abc.py 2>/dev/null | head -2', shell=True, capture_output=True, text=True, timeout=8)\n"
    "print('CUR_ABC', r.stdout.strip(), flush=True)\n"
)
try:
    r = subprocess.run(["sudo", "-n", "python3", "-c", code], capture_output=True, text=True, timeout=25)
    print("A rc", r.returncode, (r.stdout + r.stderr)[:2500].replace(chr(10), "|"), flush=True)
except Exception as e:
    print("A EXC", type(e).__name__, str(e)[:100], flush=True)
print("DONE_A", flush=True)
'''
run_cmd(sid, CODE_A, "A_VERIFY", timeout=100)

api("DELETE", f"/v2/sandboxes/{NAME}?teamId={TEAM}&projectId={PROJ}")
print("\ncleanup done", flush=True)

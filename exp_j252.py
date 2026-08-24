# 实验J252: 分段小批量扫描 /dev/vda 找 XFS 目录块(XDD3) + rootino 解析
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

NAME = "expj252"
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
    "import os, struct\n"
    "fd = os.open('/dev/vda', os.O_RDONLY)\n"
    "sb = os.read(fd, 512)\n"
    "bsize = struct.unpack('>I', sb[4:8])[0]\n"
    "dblocks = struct.unpack('>Q', sb[8:16])[0]\n"
    "rootino = struct.unpack('>Q', sb[0x38:0x40])[0]\n"
    "agblocks = struct.unpack('>I', sb[0x54:0x58])[0]\n"
    "agcount = struct.unpack('>I', sb[0x58:0x5c])[0]\n"
    "print('SB bsize', bsize, 'dblocks', dblocks, 'rootino', rootino, 'agblocks', agblocks, 'agcount', agcount, flush=True)\n"
    "os.close(fd)\n"
)
try:
    r = subprocess.run(["sudo", "-n", "python3", "-c", code], capture_output=True, text=True, timeout=15)
    print("A rc", r.returncode, (r.stdout + r.stderr)[:800].replace(chr(10), "|"), flush=True)
except Exception as e:
    print("A EXC", type(e).__name__, str(e)[:100], flush=True)
print("DONE_A", flush=True)
'''
run_cmd(sid, CODE_A, "A_SB", timeout=100)

CODE_B = r'''
import subprocess
code = (
    "import os\n"
    "fd = os.open('/dev/vda', os.O_RDONLY)\n"
    "BS = 4096\n"
    "RANGE = 64 * 1024 * 1024\n"
    "hits = []\n"
    "off = 0\n"
    "bufsz = 4 * 1024 * 1024\n"
    "while off < RANGE:\n"
    "    os.lseek(fd, off, 0)\n"
    "    d = os.read(fd, bufsz)\n"
    "    if not d:\n"
    "        break\n"
    "    nb = len(d) // BS\n"
    "    for i in range(nb):\n"
    "        if d[i*BS:i*BS+4] == b'XDD3':\n"
    "            hits.append(off + i * BS)\n"
    "    off += len(d)\n"
    "print('HITS_0_64M', len(hits), flush=True)\n"
    "for h in hits[:30]:\n"
    "    print('DIR', hex(h), flush=True)\n"
    "os.close(fd)\n"
)
try:
    r = subprocess.run(["sudo", "-n", "python3", "-c", code], capture_output=True, text=True, timeout=60)
    print("B rc", r.returncode, (r.stdout + r.stderr)[:1500].replace(chr(10), "|"), flush=True)
except Exception as e:
    print("B EXC", type(e).__name__, str(e)[:100], flush=True)
print("DONE_B", flush=True)
'''
run_cmd(sid, CODE_B, "B_SCAN0", timeout=120)

CODE_C = r'''
import subprocess
code = (
    "import os\n"
    "fd = os.open('/dev/vda', os.O_RDONLY)\n"
    "BS = 4096\n"
    "START = 64 * 1024 * 1024\n"
    "RANGE = 192 * 1024 * 1024\n"
    "hits = []\n"
    "off = START\n"
    "bufsz = 4 * 1024 * 1024\n"
    "while off < START + RANGE:\n"
    "    os.lseek(fd, off, 0)\n"
    "    d = os.read(fd, bufsz)\n"
    "    if not d:\n"
    "        break\n"
    "    nb = len(d) // BS\n"
    "    for i in range(nb):\n"
    "        if d[i*BS:i*BS+4] == b'XDD3':\n"
    "            hits.append(off + i * BS)\n"
    "    off += len(d)\n"
    "print('HITS_64_256M', len(hits), flush=True)\n"
    "for h in hits[:30]:\n"
    "    print('DIR', hex(h), flush=True)\n"
    "os.close(fd)\n"
)
try:
    r = subprocess.run(["sudo", "-n", "python3", "-c", code], capture_output=True, text=True, timeout=60)
    print("C rc", r.returncode, (r.stdout + r.stderr)[:1500].replace(chr(10), "|"), flush=True)
except Exception as e:
    print("C EXC", type(e).__name__, str(e)[:100], flush=True)
print("DONE_C", flush=True)
'''
run_cmd(sid, CODE_C, "C_SCAN1", timeout=120)

api("DELETE", f"/v2/sandboxes/{NAME}?teamId={TEAM}&projectId={PROJ}")
print("\ncleanup done", flush=True)

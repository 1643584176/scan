# 实验K2: 报告2再检验 - 对照实验: 沙箱内已有能力 vs Spawn声称能力
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

NAME = "expk2"
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
def sh(c, timeout=10):
    try:
        r = subprocess.run(c, shell=True, capture_output=True, text=True, timeout=timeout)
        return f"rc={r.returncode} OUT={r.stdout[:400]} ERR={r.stderr[:200]}"
    except Exception as e:
        return f"EXC {type(e).__name__}: {e}"
# 1) 普通进程(无sudo)的 uid 与 caps
print("PLAIN_UID", sh("id"), flush=True)
print("PLAIN_CAP", sh("grep Cap /proc/self/status"), flush=True)
# 2) sudo 后
print("SUDO_ID", sh("sudo -n id"), flush=True)
print("SUDO_CAP", sh("sudo -n sh -c 'grep Cap /proc/self/status'"), flush=True)
# 3) setuid(0) 直接提权 (无 sudo)
print("SETEUID", sh("python3 -c 'import os; os.seteuid(0); print(\"ROOT_OK\", os.geteuid())'"), flush=True)
# 4) 读 /dev/vda (报告2声称能力)
print("VDA_READ", sh("sudo -n python3 -c 'import os; fd=os.open(\"/dev/vda\", os.O_RDONLY); d=os.read(fd, 512); print(len(d), d[:8].hex()); os.close(fd)'"), flush=True)
# 5) mount tmpfs (报告2声称: mount -t tmpfs OK)
print("MOUNT_TMPFS", sh("mkdir -p /tmp/tt && sudo -n mount -t tmpfs tmpfs /tmp/tt 2>&1; echo rc=$?; mountpoint /tmp/tt 2>&1"), flush=True)
# 6) 写入 /dev/vda 512B 测试 (报告2声称 O_RDWR)
print("VDA_WRITE", sh("sudo -n python3 -c 'import os; fd=os.open(\"/dev/vda\", os.O_RDWR); os.lseek(fd, 0x1000000, 0); n=os.write(fd, b\"K2TEST!\"*64); print(\"WROTE\", n); os.close(fd)'"), flush=True)
print("DONE_A", flush=True)
'''
run_cmd(sid, CODE_A, "A_CAP", timeout=100)

api("DELETE", f"/v2/sandboxes/{NAME}?teamId={TEAM}&projectId={PROJ}")
print("\ncleanup done", flush=True)

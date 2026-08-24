# 实验J108: runtime 镜像隔离差异对比 — seccomp/caps/mount/unshare/设备/穿透/metadata
import json, time, urllib.request, urllib.error, sys, base64
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
        return ""
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

RUNTIMES = ["node22", "python3.13", "cua-ubuntu-xfce", "sandbox-roocode-noble", "blackbox-playwright"]

PROBE = r"""
import os, subprocess, json, re

print(f"== PROBE runtime={os.environ.get('RT','?')} ==", flush=True)

def sh(cmd, timeout=8):
    try:
        r = subprocess.run(cmd, shell=True, capture_output=True, timeout=timeout)
        return (r.stdout + r.stderr).decode(errors="replace").strip()[:200]
    except Exception as e:
        return f"EXC({e})"

# 1. 身份
print("[1] id:", sh("id"), flush=True)
print("[2] uname:", sh("uname -a"), flush=True)
print("[3] os-release:", sh("grep PRETTY /etc/os-release"), flush=True)

# 2. seccomp / caps
print("[4] Seccomp:", sh("grep Seccomp /proc/self/status"), flush=True)
print("[5] CapEff:", sh("grep CapEff /proc/self/status"), flush=True)
print("[6] CapBnd:", sh("grep CapBnd /proc/self/status"), flush=True)

# 3. mount 测试 (tmpfs 探 seccomp)
print("[7] mount tmpfs:", sh("mkdir -p /tmp/mnt && mount -t tmpfs none /tmp/mnt 2>&1; echo rc=$?"), flush=True)

# 4. unshare user ns
print("[8] unshare:", sh("unshare -rm true 2>&1; echo rc=$?"), flush=True)

# 5. 设备
print("[9] block devs:", sh("ls -la /dev/vd* /dev/sd* 2>&1 | head -8"), flush=True)
print("[10] vda read:", sh("dd if=/dev/vda bs=512 count=1 2>/dev/null | head -c 8 | xxd -p"), flush=True)
print("[11] special devs:", sh("ls /dev/input /dev/kvm /dev/fuse /dev/shm 2>&1 | head -8"), flush=True)
print("[12] /proc/partitions:", sh("cat /proc/partitions"), flush=True)

# 6. /proc/1/root 穿透
print("[13] pid1 root:", sh("ls /proc/1/root/etc/shadow 2>&1"), flush=True)
print("[14] pid1 cmdline:", sh("tr '\\0' ' ' < /proc/1/cmdline | head -c 200"), flush=True)

# 7. metadata
print("[15] metadata:", sh("timeout 4 curl -sS -o /dev/null -w '%{http_code}' http://169.254.169.254/latest/meta-data/ 2>&1"), flush=True)

# 8. 网络策略外
print("[16] google:", sh("timeout 4 curl -sS -o /dev/null -w '%{http_code}' https://www.google.com 2>&1"), flush=True)

# 9. rootfs 设备号
print("[17] rootfs:", sh("df -T / | tail -1 | awk '{print $1, $2}'"), flush=True)
print("[18] sandbox-init:", sh("ls -la /run/vercel/share/ 2>&1 | head -6"), flush=True)
"""
for rt in RUNTIMES:
    NAME = f"expj108{rt[:6]}"
    api("DELETE", f"/v2/sandboxes/{NAME}?teamId={TEAM}&projectId={PROJ}")
    c, r = api("POST", f"/v2/sandboxes?teamId={TEAM}",
               {"projectId": PROJ, "name": NAME, "runtime": rt,
                "networkPolicy": {"mode": "custom", "allowedDomains": ["httpbin.org"]}})
    if c != 200:
        print(f"!! create {rt} FAIL: {r[:200]}", flush=True)
        continue
    sid = json.loads(r)["sandbox"]["currentSessionId"]
    print(f"\n########## runtime={rt} sid={sid} ##########", flush=True)
    run_cmd(sid, PROBE.replace("os.environ.get('RT','?')", f"'{rt}'"), rt, wait=True, timeout=300000)
    api("DELETE", f"/v2/sandboxes/{NAME}?teamId={TEAM}&projectId={PROJ}")
    time.sleep(1)

print("\nall done", flush=True)

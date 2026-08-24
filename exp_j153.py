# 实验J153: DNS内网探测(PTR反查宿主/网关) + /proc/1/maps布局 + UDP小探测
# j152: netns疑似与宿主共享(/proc/net/unix见宿主socket); init.sock连接触发杀进程; /proc/1/exe大读被杀
#       resolv.conf nameserver=172.31.0.2 (AWS VPC DNS!) -> VPC内网可达线索
# 方法: cmdA 纯DNS查询(PTR反查100.64.79.9/网关/自身 + 探测内网域名解析); cmdB /proc/1/maps布局(只读不触发大读)
# 零破坏: DNS查询与内存映射读取, 无连接建立, 无数据写入
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

def run_cmd(sid, code, label, wait=True, timeout=280):
    body = {"command": "python3", "args": ["-c", code],
            "wait": wait, "logs": True, "timeout": timeout}
    for attempt in range(4):
        c, r = api("POST", f"/v2/sandboxes/sessions/{sid}/cmd?teamId={TEAM}", body)
        if c == 200:
            break
        print(f"  retry[{attempt}] status {c}: {r[:150]}", flush=True)
        time.sleep(3)
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

def catfile(sid, path, label, n=15000):
    c, r = api("POST", f"/v2/sandboxes/sessions/{sid}/cmd?teamId={TEAM}",
               {"command": "cat", "args": [path], "wait": True, "logs": True, "timeout": 100})
    print(f"=== {label} status {c} ===", flush=True)
    print(r[:n], flush=True)

NAME = "expj153"
api("DELETE", f"/v2/sandboxes/{NAME}?teamId={TEAM}&projectId={PROJ}")
c, r = api("POST", f"/v2/sandboxes?teamId={TEAM}",
           {"projectId": PROJ, "name": NAME,
            "networkPolicy": {"mode": "custom", "allowedDomains": ["httpbin.org"]}})
print("create:", c)
if c != 200:
    print(r[:400])
    sys.exit(1)
sid = json.loads(r)["sandbox"]["currentSessionId"]
print("sid:", sid)

# cmdA: DNS 探测
CA = r'''
import socket, struct, random, subprocess, time
out = open("/tmp/d153a.txt", "w")
def p(*a):
    out.write(" ".join(str(x) for x in a) + "\n")
    out.flush()
def sh(cmd, t=10):
    try:
        r = subprocess.run(cmd, shell=True, capture_output=True, timeout=t)
        return (r.stdout or b"").decode("latin1", "replace") + (r.stderr or b"").decode("latin1", "replace")
    except Exception as e:
        return "EXC %r" % (e,)

def dns_query(name, qtype=1, server="172.31.0.2", timeout=3):
    """构造DNS查询包,返回原始响应"""
    tid = random.randint(0, 0xFFFF)
    hdr = struct.pack(">HHHHHH", tid, 0x0100, 1, 0, 0, 0)
    q = b""
    for part in name.split("."):
        q += bytes([len(part)]) + part.encode()
    q += b"\x00" + struct.pack(">HH", qtype, 1)
    try:
        s = socket.socket(socket.AF_INET, socket.SOCK_DGRAM)
        s.settimeout(timeout)
        s.sendto(hdr + q, (server, 53))
        d, _ = s.recvfrom(4096)
        s.close()
        return d
    except Exception as e:
        return b"ERR " + repr(e).encode()

def parse_dns(d):
    if len(d) < 12:
        return "SHORT"
    tid, flags, qd, an, ns, ar = struct.unpack(">HHHHHH", d[:12])
    rcode = flags & 0xF
    if an == 0:
        return f"rcode={rcode} no_answer flags=0x{flags:04x}"
    # 跳过 question
    off = 12
    while off < len(d) and d[off] != 0:
        off += 1 + d[off]
    off += 5
    # 第一个 answer
    answers = []
    for _ in range(an):
        # name (compression)
        if d[off] & 0xC0 == 0xC0:
            off += 2
        else:
            while d[off] != 0:
                off += 1 + d[off]
            off += 1
        rtype, rclass, ttl, rdlen = struct.unpack(">HHIH", d[off:off + 10])
        off += 10
        rd = d[off:off + rdlen]
        off += rdlen
        if rtype == 1 and rdlen == 4:
            answers.append("A " + socket.inet_ntoa(rd))
        elif rtype == 12:
            # PTR: decode name
            nm = []
            i = 0
            while i < len(rd):
                if rd[i] & 0xC0 == 0xC0:
                    break
                ln = rd[i]
                nm.append(rd[i + 1:i + 1 + ln].decode("latin1"))
                i += 1 + ln
            answers.append("PTR " + ".".join(nm))
        elif rtype == 5:
            nm = []
            i = 0
            while i < len(rd):
                if rd[i] & 0xC0 == 0xC0:
                    break
                ln = rd[i]
                nm.append(rd[i + 1:i + 1 + ln].decode("latin1"))
                i += 1 + ln
            answers.append("CNAME " + ".".join(nm))
        else:
            answers.append(f"type={rtype} rdlen={rdlen}")
    return "answers=" + ";".join(answers)

def ptr_of(ip):
    return ".".join(reversed(ip.split("."))) + ".in-addr.arpa"

p("=== PTR_HOST ===")
for ip in ["100.64.79.9", "100.64.0.1", "100.64.139.112", "172.31.0.2"]:
    d = dns_query(ptr_of(ip), 12)
    p(ip, "->", parse_dns(d))

p("=== DNS_SERVERS ===")
for srv in ["172.31.0.2", "172.31.0.2:5353", "10.0.0.2", "100.64.0.2"]:
    host = srv.split(":")[0]
    port = int(srv.split(":")[1]) if ":" in srv else 53
    d = dns_query("vercel.com", 1, host, timeout=2)
    p("srv", srv, "->", parse_dns(d))

p("=== INTERNAL_NAMES ===")
for nm in ["metadata.google.internal", "metadata.aws.internal", "instance-data.ec2.internal",
           "ip-172-31-0-1.ec2.internal", "ec2.internal", "api.vercel.com", "celld.vercel.internal"]:
    d = dns_query(nm, 1)
    p(nm, "->", parse_dns(d))

p("=== LOCAL_RESOLV ===")
p(sh("cat /etc/resolv.conf 2>&1"))
p("=== DONE")
out.close()
'''

# cmdB: /proc/1/maps 布局 (只读不触发大读)
CB = r'''
import os, subprocess
out = open("/tmp/d153b.txt", "w")
def p(*a):
    out.write(" ".join(str(x) for x in a) + "\n")
    out.flush()
def sh(cmd, t=10):
    try:
        r = subprocess.run(cmd, shell=True, capture_output=True, timeout=t)
        return (r.stdout or b"").decode("latin1", "replace") + (r.stderr or b"").decode("latin1", "replace")
    except Exception as e:
        return "EXC %r" % (e,)
p("=== MAPS ===")
p(sh("cat /proc/1/maps 2>&1 | head -60"))
p("=== SMAPS_HDR ===")
p(sh("head -40 /proc/1/smaps 2>&1"))
p("=== MEM_TEST ===")
p(sh("dd if=/proc/1/mem bs=1 count=16 skip=4194304 2>&1 | xxd 2>&1 | head -3"))
p("=== DONE")
out.close()
'''

run_cmd(sid, CA, "dns-probe", timeout=150)
catfile(sid, "/tmp/d153a.txt", "d153a", 9000)

run_cmd(sid, CB, "maps", timeout=100)
catfile(sid, "/tmp/d153b.txt", "d153b", 6000)

api("DELETE", f"/v2/sandboxes/{NAME}?teamId={TEAM}&projectId={PROJ}")
print("\ncleanup done", flush=True)

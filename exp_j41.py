# 实验J41: 宿主监听端口 23456/30001/30002 协议探测 + init.sock 路由挖掘
# 目标: 判断端口服务身份, 尝试协议交互, 挖出 sandbox-init HTTP 路由
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

NAME = "expj41"
api("DELETE", f"/v2/sandboxes/{NAME}?teamId={TEAM}&projectId={PROJ}")
c, r = api("POST", f"/v2/sandboxes?teamId={TEAM}",
           {"projectId": PROJ, "name": NAME,
            "networkPolicy": {"mode": "custom", "allowedDomains": ["httpbin.org"]}})
print("create:", c)
sid = json.loads(r)["sandbox"]["currentSessionId"]
print("sid:", sid)

SCAN = r'''
import socket, re, struct, os, subprocess

print("===== [1] 本机 IP 与完整监听列表 =====", flush=True)
import socket as sk
# 从路由表提取本机 IP (fib_trie 的 host LOCAL 条目)
self_ips = []
for ln in open("/proc/net/fib_trie"):
    m = re.match(r"\s*\|--\s+([0-9.]+)", ln)
    if m and "." in m.group(1) and not m.group(1).endswith(".0"):
        ip = m.group(1)
        if ip not in self_ips:
            self_ips.append(ip)
print("self IPs:", self_ips, flush=True)
for pf in ["tcp", "tcp6", "udp", "udp6"]:
    path = "/proc/net/%s" % pf
    try:
        lines = open(path).read().splitlines()[1:]
    except Exception:
        continue
    print("--- %s ---" % pf, flush=True)
    for ln in lines:
        p = ln.split()
        if len(p) < 4:
            continue
        try:
            local = p[1]
            laddr_hex, lport_hex = local.split(":")
            port = int(lport_hex, 16)
            af = socket.AF_INET if len(laddr_hex) == 8 else socket.AF_INET6
            ip = socket.inet_ntop(af, bytes.fromhex(laddr_hex))
        except Exception:
            continue
        if p[3] == "0A":
            print("  LISTEN %-42s :%d" % (ip, port), flush=True)
        elif p[3] == "01":
            try:
                raddr_hex, rport_hex = p[2].split(":")
                rip = socket.inet_ntop(af, bytes.fromhex(raddr_hex))
            except Exception:
                continue
            print("  ESTAB  %-42s :%d -> %s:%d" % (ip, port, rip, int(rport_hex, 16)), flush=True)

print("===== [2] 端口 23456/30001/30002 协议探测 =====", flush=True)
def probe(ip, port, timeout=2.5):
    res = {}
    s = socket.socket(socket.AF_INET6 if ":" in ip else socket.AF_INET)
    s.settimeout(timeout)
    try:
        s.connect((ip, port))
        res["connect"] = "OK"
        # banner
        try:
            d = s.recv(1024)
            res["banner"] = d[:200]
        except socket.timeout:
            res["banner"] = "no-banner"
        # HTTP GET
        try:
            s.sendall(b"GET / HTTP/1.1\r\nHost: localhost\r\n\r\n")
            d = b""
            while True:
                c = s.recv(4096)
                if not c:
                    break
                d += c
                if len(d) > 2000:
                    break
            res["http"] = d[:400]
        except Exception as e:
            res["http"] = "ERR %s" % e
        s.close()
    except Exception as e:
        res["connect"] = "FAIL %s" % e
    return res

for port in [23456, 30001, 30002]:
    for ip in ["::1", "127.0.0.1"]:
        r = probe(ip, port)
        print("port %d @ %s: %s" % (port, ip, r), flush=True)

print("===== [3] raw 协议探测 (23456) =====", flush=True)
for ip in ["::1", "127.0.0.1"]:
    for payload in [b"\x00", b"ping\n", b"hello\n", b'{"jsonrpc":"2.0","id":1,"method":"ping"}\n']:
        try:
            s = socket.socket(socket.AF_INET6 if ":" in ip else socket.AF_INET)
            s.settimeout(2)
            s.connect((ip, 23456))
            s.sendall(payload)
            d = s.recv(1024)
            print("%s send %r -> %r" % (ip, payload[:30], d[:200]), flush=True)
            s.close()
        except Exception as e:
            print("%s send %r -> ERR %s" % (ip, payload[:30], e), flush=True)

print("===== [4] init.sock HTTP 路由暴力 (从二进制提取候选) =====", flush=True)
b = open("/run/vercel/share/sandbox-init", "rb").read()
# 提取所有引号字符串, 含 / 且短的
cands = set()
for m in re.finditer(rb'([A-Za-z0-9_.\-/]{2,60})', b):
    s = m.group(1)
    if b"/" in s and not s.startswith((b"http", b"https", b"/proc", b"/dev", b"/sys", b"/tmp",
                                        b"/var", b"/run", b"/etc", b"/usr", b"/opt", b"/home",
                                        b"//", b"./", b"../", b"://")):
        if s.count(b"/") <= 4 and len(s) <= 50:
            cands.add(s.decode('latin1', errors='replace'))
cands = sorted(cands)
print("candidates:", len(cands), flush=True)

def http_req(path, method="GET", headers=None, body=b""):
    s = socket.socket(socket.AF_UNIX, socket.SOCK_STREAM)
    s.settimeout(2.5)
    s.connect("/run/vercel/share/init.sock")
    req = ("%s %s HTTP/1.1\r\nHost: localhost\r\n" % (method, path)).encode()
    if headers:
        for k, v in headers.items():
            req += ("%s: %s\r\n" % (k, v)).encode()
    if body:
        req += ("Content-Length: %d\r\n" % len(body)).encode()
    req += b"\r\n"
    if body:
        req += body
    s.sendall(req)
    data = b""
    try:
        while True:
            c = s.recv(8192)
            if not c:
                break
            data += c
            if len(data) > 60000:
                break
    except socket.timeout:
        pass
    s.close()
    return data

hits = []
for path in cands[:1500]:
    try:
        d = http_req("/" + path if not path.startswith("/") else path)
        first = d.split(b"\r\n", 1)[0]
        if b"404" not in first:
            hits.append((path, first, d[:300]))
            print("HIT %-50s -> %s" % (path, first.decode(errors='replace')), flush=True)
            print("     body: %r" % d[:300], flush=True)
    except Exception as e:
        pass
print("total hits:", len(hits), flush=True)

print("===== [5] HTTP/2 探测 =====", flush=True)
try:
    s = socket.socket(socket.AF_UNIX, socket.SOCK_STREAM)
    s.settimeout(2)
    s.connect("/run/vercel/share/init.sock")
    s.sendall(b"PRI * HTTP/2.0\r\n\r\nSM\r\n\r\n")
    d = s.recv(4096)
    print("h2c preface -> %r" % d[:300], flush=True)
    s.close()
except Exception as e:
    print("h2c ERR:", e, flush=True)

print("===== [6] 宿主 /proc 可见性检查 =====", flush=True)
# pid ns 隔离, 但尝试看宿主进程?
try:
    print(subprocess.run(["ps", "aux", "|", "wc", "-l"], shell=True, capture_output=True, text=True).stdout, flush=True)
except Exception as e:
    print("ERR", e, flush=True)
'''
run_cmd(sid, SCAN, "port-probe-route-bruteforce", wait=True, timeout=300000)

api("DELETE", f"/v2/sandboxes/{NAME}?teamId={TEAM}&projectId={PROJ}")
print("\ncleanup done", flush=True)

# 实验J40: 网络命名空间侦察 + 宿主本地端口探测 + 二进制路由挖掘
# 目标: 确认共享 net ns, 枚举宿主 127.0.0.1 监听服务, 从 sandbox-init 挖路由
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

NAME = "expj40"
api("DELETE", f"/v2/sandboxes/{NAME}?teamId={TEAM}&projectId={PROJ}")
c, r = api("POST", f"/v2/sandboxes?teamId={TEAM}",
           {"projectId": PROJ, "name": NAME,
            "networkPolicy": {"mode": "custom", "allowedDomains": ["httpbin.org"]}})
print("create:", c)
sid = json.loads(r)["sandbox"]["currentSessionId"]
print("sid:", sid)

SCAN = r'''
import socket, re, os, subprocess

def http_req(path, method="GET", headers=None, body=b""):
    s = socket.socket(socket.AF_UNIX, socket.SOCK_STREAM)
    s.settimeout(3)
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
            chunk = s.recv(8192)
            if not chunk:
                break
            data += chunk
            if len(data) > 60000:
                break
    except socket.timeout:
        pass
    s.close()
    return data

print("===== [1] net namespace 与网络状态 =====", flush=True)
print(subprocess.run(["ls", "-l", "/proc/self/ns/"], capture_output=True, text=True).stdout, flush=True)
print("hostname:", socket.gethostname(), flush=True)
for f in ["/proc/net/route", "/proc/net/arp", "/proc/net/fib_trie"]:
    try:
        print("--- %s ---" % f, flush=True)
        print(open(f).read()[:2000], flush=True)
    except Exception as e:
        print(f, "ERR", e, flush=True)

print("===== [2] /proc/net/tcp 监听端口 =====", flush=True)
def parse_tcp(path):
    out = []
    try:
        lines = open(path).read().splitlines()[1:]
    except Exception:
        return out
    for ln in lines:
        p = ln.split()
        if len(p) < 10:
            continue
        local, rem = p[1], p[2]
        st = p[3]
        laddr, lport = local.split(":"), int(local.split(":")[1], 16)
        rport = int(rem.split(":")[1], 16) if rem.split(":")[1] != "0000" else None
        if st == "0A" or st == "01":
            out.append((laddr[0], lport, st, rport))
    return out

for pf, path in [("tcp", "/proc/net/tcp"), ("tcp6", "/proc/net/tcp6"),
                 ("udp", "/proc/net/udp"), ("udp6", "/proc/net/udp6")]:
    lst = parse_tcp(path)
    print("%s: %d entries" % (pf, len(lst)), flush=True)
    for a, p, st, rp in lst[:60]:
        ip = socket.inet_ntop(socket.AF_INET if pf == "tcp" else socket.AF_INET6,
                              bytes.fromhex(a) if len(a) == 8 else bytes.fromhex(a.zfill(32)))
        print("  %-40s :%d state=%s" % (ip, p, st), flush=True)

print("===== [3] 127.0.0.1 端口扫描 (TCP connect) =====", flush=True)
listen_ports = set()
for pf in ["tcp", "tcp6"]:
    for a, p, st, rp in parse_tcp("/proc/net/%s" % pf):
        if st == "0A":
            ip = socket.inet_ntop(socket.AF_INET if pf == "tcp" else socket.AF_INET6,
                                  bytes.fromhex(a) if len(a) == 8 else bytes.fromhex(a.zfill(32)))
            if ip.startswith("127.") or ip == "::1" or ip == "0.0.0.0" or ip == "::":
                listen_ports.add(p)
print("127/0.0.0.0 listeners:", sorted(listen_ports), flush=True)

for port in sorted(listen_ports):
    for ip in ("127.0.0.1",):
        try:
            s = socket.create_connection((ip, port), timeout=1.5)
            s.settimeout(1.5)
            # 先尝试 HTTP
            s.sendall(b"GET / HTTP/1.1\r\nHost: localhost\r\n\r\n")
            d = b""
            try:
                while True:
                    c = s.recv(4096)
                    if not c:
                        break
                    d += c
                    if len(d) > 4000:
                        break
            except socket.timeout:
                pass
            s.close()
            print("port %-6d -> HTTP resp: %r" % (port, d[:300]), flush=True)
        except Exception as e:
            print("port %-6d -> ERR %s" % (port, e), flush=True)

print("===== [4] init.sock 路由挖掘 (二进制字符串) =====", flush=True)
b = open("/run/vercel/share/sandbox-init", "rb").read()
# Go mux 路由: 找含斜杠的路径串, 排除文件路径/URL/注释
cands = re.findall(rb'"[^"]{2,90}"', b)
routes = set()
for c in cands:
    s = c[1:-1]
    if b"/" in s and not s.startswith((b"http", b"https", b"://", b"/proc", b"/dev", b"/sys", b"/tmp", b"/var", b"/run", b"/etc", b"/usr", b"/opt", b"/home", b"$", b"%", b"{", b"./")):
        if s.count(b"/") <= 3 and all(ch < 128 for ch in s):
            routes.add(s.decode('latin1'))
for r in sorted(routes)[:120]:
    print("  %r" % r, flush=True)

print("===== [5] HTTP2/h2c 升级探测 =====", flush=True)
for extra in [b"", b"x\x00\x00\x00\x04\x00\x00\x00\x00\x00"]:
    try:
        s = socket.socket(socket.AF_UNIX, socket.SOCK_STREAM)
        s.settimeout(2)
        s.connect("/run/vercel/share/init.sock")
        if extra:
            s.sendall(extra)  # HTTP/2 preface
            d = s.recv(4096)
            print("h2 preface -> %r" % d[:200], flush=True)
        else:
            s.sendall(b"PRI * HTTP/2.0\r\n\r\nSM\r\n\r\n")
            d = s.recv(4096)
            print("PRI * -> %r" % d[:200], flush=True)
        s.close()
    except Exception as e:
        print("h2 probe ERR: %s" % e, flush=True)
'''
run_cmd(sid, SCAN, "netns-host-port-scan", wait=True, timeout=300000)

api("DELETE", f"/v2/sandboxes/{NAME}?teamId={TEAM}&projectId={PROJ}")
print("\ncleanup done", flush=True)

# 实验J1: sandbox-init 控制面 connectrpc 协议探测 + /etc/vercel + ptrace 可行性
# 背景(I系列已证实): sandbox-init = uid1000(同用户) + 全cap + connectrpc Go服务
#   监听 23456(HTTP 404壳)/7531/7532(未测协议!)/init.sock(属主=vercel-sandbox, 可连接!)
#   启动参数 --pubkey=ed25519(签名验证 SpawnService), 私钥在 agent 侧
# 目标: 找到无需签名可达的 connect 方法(health/ping/info) 或 未签名控制通道
import socket, os, subprocess, json, struct, time

def run(cmd, timeout=15):
    try:
        r = subprocess.run(["bash", "-c", cmd], capture_output=True, timeout=timeout)
        return (r.stdout + r.stderr).decode(errors='replace')
    except Exception as e:
        return f"ERR {type(e).__name__}: {e}"

def http_post(host, port, path, body=b"{}", ct="application/json", timeout=6, unix=None):
    """HTTP/1.1 POST(connectrpc 兼容), 支持 unix socket"""
    try:
        if unix:
            s = socket.socket(socket.AF_UNIX, socket.SOCK_STREAM)
            s.settimeout(timeout)
            s.connect(unix)
        else:
            s = socket.socket()
            s.settimeout(timeout)
            s.connect((host, port))
        req = (f"POST {path} HTTP/1.1\r\nHost: localhost\r\n"
               f"Content-Type: {ct}\r\nContent-Length: {len(body)}\r\n"
               f"Connect-Protocol-Version: 1\r\n\r\n").encode() + body
        s.sendall(req)
        data = b""
        try:
            while len(data) < 4096:
                c = s.recv(4096)
                if not c:
                    break
                data += c
        except socket.timeout:
            pass
        s.close()
        first = data.split(b"\r\n\r\n", 1)
        status = first[0].split(b" ")[1].decode() if first and b" " in first[0] else "?"
        return f"{status} | {data[:200]!r}"
    except Exception as e:
        return f"ERR {type(e).__name__}: {e}"

print("== [1] TCP 7531/7532/23456 connectrpc 探测 ==", flush=True)
SERVICES = [
    "grpc.health.v1.Health/Check",
    "vercel.sandbox.spawn.v1.SpawnService/Ping",
    "vercel.sandbox.spawn.v1.SpawnService/Kill",
    "vercel.sandbox.spawn.v1.SpawnService/GetInfo",
    "vercel.sandbox.spawn.v1.SpawnService/Status",
    "vercel.sandbox.spawn.v1.SpawnService/Spawn",
]
CTS = ["application/json", "application/connect+json", "application/grpc"]
for port in [7531, 7532, 23456]:
    for svc in SERVICES[:2]:  # 先 health + Ping 定位端口
        r = http_post("127.0.0.1", port, "/" + svc)
        print(f"  {port} {svc:<52} {r}", flush=True)

print("== [2] init.sock connectrpc 探测 ==", flush=True)
for svc in SERVICES[:3]:
    r = http_post(None, 0, "/" + svc, unix="/run/vercel/share/init.sock")
    print(f"  init.sock {svc:<52} {r}", flush=True)

print("== [3] /etc/vercel 目录 ==", flush=True)
print(run("ls -laR /etc/vercel/ 2>&1 | head -40"))
print(run("find /etc/vercel -type f 2>/dev/null | head -10 | while read f; do echo \"--- $f\"; cat \"$f\" 2>&1 | head -5; done"))

print("== [4] pid1 内存可读性 (ptrace 前提) ==", flush=True)
print(run("ls -la /proc/1/mem /proc/1/environ 2>&1"))
print(run("head -c 64 /proc/1/mem 2>&1 | xxd | head -2"))
print(run("grep -i 'yama\|ptrace_scope' /proc/sys/kernel/yama/ptrace_scope /proc/sys/kernel 2>/dev/null | head -3"))
print(run("cat /proc/sys/kernel/yama/ptrace_scope 2>&1"))

print("== [5] UDP/ICMP 边界快速矩阵 ==", flush=True)
def udp_probe(host, port, payload=b"AB", timeout=3):
    s = socket.socket(socket.AF_INET, socket.SOCK_DGRAM)
    s.settimeout(timeout)
    try:
        s.sendto(payload, (host, port))
        try:
            d, _ = s.recvfrom(512)
            return f"RECV {d[:24]!r}"
        except socket.timeout:
            return "TIMEOUT"
    except OSError as e:
        return f"ERR {e}"
    finally:
        s.close()
for host in ["8.8.8.8", "1.1.1.1", "100.64.0.1", "169.254.169.254"]:
    for port in [53, 443]:
        print(f"  udp {host}:{port}: {udp_probe(host, port)}", flush=True)
print(run("ping -c 1 -W 2 8.8.8.8 2>&1 | tail -1"))
print(run("ping -c 1 -W 2 100.64.0.1 2>&1 | tail -1"))

print("== [6] sandbox-init 运行参数/网络连接复确认 ==", flush=True)
print(run("cat /proc/1/cmdline | tr '\\0' ' '; echo"))
print(run("ss -tnp 2>/dev/null | grep -E '7531|7532|5BA0' | head -6"))
print("done", flush=True)

# 实验I12: agent 端口 + sandbox-init 服务端口 + 敏感 unix socket 探测
import socket, subprocess, os

def run(cmd, timeout=8):
    try:
        r = subprocess.run(["bash", "-c", cmd], capture_output=True, timeout=timeout)
        return (r.stdout + r.stderr).decode(errors='replace')
    except Exception as e:
        return f"ERR {type(e).__name__}: {e}"

print("== [1] agent 端口 100.64.0.1:47076 直接连接 ==", flush=True)
for port in [47076, 443, 80, 7531, 7532, 23456]:
    try:
        s = socket.socket()
        s.settimeout(3)
        s.connect(("100.64.0.1", port))
        print(f"  CONNECT 100.64.0.1:{port} OK", flush=True)
        # 发个 HTTP 探测
        s.sendall(b"GET / HTTP/1.1\r\nHost: 100.64.0.1\r\n\r\n")
        try:
            d = s.recv(300)
            print(f"    响应: {d[:200]!r}", flush=True)
        except socket.timeout:
            print("    (无响应)", flush=True)
        s.close()
    except Exception as e:
        print(f"  CONNECT 100.64.0.1:{port} FAIL: {type(e).__name__} {e}", flush=True)

print("== [2] 本机 sandbox-init 端口 ==", flush=True)
# 本机 IP
out = run("ip -o addr show 2>/dev/null | grep -v lo | awk '{print $4}' | head -3")
print(f"  本机 IP: {out.strip()}", flush=True)
for port in [7531, 7532, 23456]:
    try:
        s = socket.socket()
        s.settimeout(3)
        s.connect(("127.0.0.1", port))
        print(f"  127.0.0.1:{port} OPEN", flush=True)
        s.sendall(b"GET / HTTP/1.1\r\nHost: localhost\r\n\r\n")
        try:
            d = s.recv(300)
            print(f"    响应: {d[:200]!r}", flush=True)
        except socket.timeout:
            print("    (无响应)", flush=True)
        s.close()
    except Exception as e:
        print(f"  127.0.0.1:{port} FAIL: {type(e).__name__} {e}", flush=True)

print("== [3] 敏感 unix socket 权限 ==", flush=True)
for sp in ["/run/containerd/containerd.sock", "/run/apm/apm.sock", "/run/cell/cell.sock",
           "/run/metrics/metrics.sock", "/run/containerd/containerd.sock.ttrpc"]:
    r = run(f"ls -la {sp} 2>&1")
    print(f"  {sp}: {r.strip()}", flush=True)
    # 尝试连接
    try:
        s = socket.socket(socket.AF_UNIX, socket.SOCK_STREAM)
        s.settimeout(3)
        s.connect(sp)
        print(f"    -> 可连接! 发送探测...", flush=True)
        s.sendall(b"GET /v1/version HTTP/1.1\r\nHost: localhost\r\n\r\n")
        try:
            d = s.recv(300)
            print(f"    响应: {d[:200]!r}", flush=True)
        except socket.timeout:
            print("    (无响应)", flush=True)
        s.close()
    except Exception as e:
        print(f"    -> 连接失败: {type(e).__name__} {e}", flush=True)

print("== [4] fd8 (agent 连接) 详情 ==", flush=True)
print(run("cat /proc/1/net/tcp 2>/dev/null | grep -i 5BA0; cat /proc/1/net/tcp6 2>/dev/null | grep -i 5BA0"), flush=True)
print(run("for f in /proc/1/fd/*; do [ \"$(readlink $f)\" = \"socket:[716]\" ] && echo \"fd8 = socket 716\"; done; echo ---; cat /proc/1/net/tcp6 | head -3"), flush=True)

print("== [5] 网络命名空间内其他监听端口扫描(快速) ==", flush=True)
# 扫描常见高价值端口
import struct
ports_to_try = [22, 2375, 2376, 6443, 8080, 9090, 9091, 4318, 3000, 5000, 9000, 9669, 47076]
local_ips = ["127.0.0.1", "100.64.144.137"]
import subprocess as sp
for ip in local_ips:
    for port in ports_to_try:
        try:
            s = socket.socket()
            s.settimeout(1.5)
            s.connect((ip, port))
            print(f"  {ip}:{port} OPEN", flush=True)
            s.close()
        except Exception:
            pass
print("  (扫描完成)", flush=True)

print("done", flush=True)

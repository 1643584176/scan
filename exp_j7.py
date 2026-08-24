# 实验J7: 沙箱内 unix socket 可达性矩阵 - containerd/cell/apm/metrics
# J6 发现: /proc/1/net/unix 可见 containerd.sock + cell.sock + apm.sock + metrics.sock
# 目标: ① socket 权限与可连接性  ② gRPC/HTTP2 探测(containerd 若可连=逃逸通道)
#       ③ cell.sock 协议识别(可能是 vercel 沙箱控制面)
import os, re, subprocess, socket, struct

def run(cmd, timeout=15):
    try:
        r = subprocess.run(["bash", "-c", cmd], capture_output=True, timeout=timeout)
        return (r.stdout + r.stderr).decode(errors='replace')
    except Exception as e:
        return f"ERR {type(e).__name__}: {e}"

SOCKETS = [
    "/run/containerd/containerd.sock",
    "/run/containerd/containerd.sock.ttrpc",
    "/run/cell/cell.sock",
    "/run/apm/apm.sock",
    "/run/metrics/metrics.sock",
    "/run/vercel/share/init.sock",
]

print("== [1] socket 文件权限 ==", flush=True)
for s in SOCKETS:
    print(run(f"ls -la {s} 2>&1 | head -1"), end="", flush=True)

print("== [2] connect 可达性 ==", flush=True)
reachable = []
for s in SOCKETS:
    try:
        c = socket.socket(socket.AF_UNIX, socket.SOCK_STREAM)
        c.settimeout(3)
        c.connect(s)
        print(f"  CONNECT OK  {s}", flush=True)
        reachable.append(s)
        c.close()
    except Exception as e:
        print(f"  FAIL {type(e).__name__}: {s} ({e})", flush=True)

print("== [3] HTTP/2 + gRPC 探测(可连接 socket) ==", flush=True)
# HTTP/2 preface + SETTINGS + HEADERS(PRIORITY)
PREFACE = b"PRI * HTTP/2.0\r\n\r\nSM\r\n\r\n"
SETTINGS = b"\x00\x00\x00\x04\x00\x00\x00\x00\x00"
for s in reachable:
    try:
        c = socket.socket(socket.AF_UNIX, socket.SOCK_STREAM)
        c.settimeout(4)
        c.connect(s)
        c.sendall(PREFACE + SETTINGS)
        data = b""
        try:
            while len(data) < 512:
                chunk = c.recv(1024)
                if not chunk:
                    break
                data += chunk
        except socket.timeout:
            pass
        print(f"  {s}: resp={data[:128]!r}", flush=True)
        c.close()
    except Exception as e:
        print(f"  {s}: ERR {e}", flush=True)

print("== [4] cell.sock 协议嗅探(connectrpc 探测) ==", flush=True)
for s in ["/run/cell/cell.sock"]:
    try:
        c = socket.socket(socket.AF_UNIX, socket.SOCK_STREAM)
        c.settimeout(4)
        c.connect(s)
        # connectrpc 需要 POST + JSON/protobuf 头
        body = b"{}"
        req = (f"POST / HTTP/1.1\r\nHost: localhost\r\nContent-Type: application/json\r\n"
               f"Content-Length: {len(body)}\r\n\r\n").encode() + body
        c.sendall(req)
        data = b""
        try:
            while len(data) < 512:
                chunk = c.recv(1024)
                if not chunk:
                    break
                data += chunk
        except socket.timeout:
            pass
        print(f"  {s}: {data[:256]!r}", flush=True)
        c.close()
    except Exception as e:
        print(f"  {s}: ERR {e}", flush=True)

print("== [5] containerd.sock 精细探测(若可达) ==", flush=True)
if "/run/containerd/containerd.sock" in reachable:
    for path in ["/v1/containers", "/v1/namespaces", "/v1/version", "/v1/tasks"]:
        try:
            c = socket.socket(socket.AF_UNIX, socket.SOCK_STREAM)
            c.settimeout(4)
            c.connect("/run/containerd/containerd.sock")
            body = b"{}"
            req = (f"POST {path} HTTP/1.1\r\nHost: localhost\r\nContent-Type: application/json\r\n"
                   f"Content-Length: {len(body)}\r\n\r\n").encode() + body
            c.sendall(req)
            data = b""
            try:
                while len(data) < 512:
                    chunk = c.recv(1024)
                    if not chunk:
                        break
                    data += chunk
            except socket.timeout:
                pass
            print(f"  {path}: {data[:200]!r}", flush=True)
            c.close()
        except Exception as e:
            print(f"  {path}: ERR {e}", flush=True)
else:
    print("  containerd.sock 不可达, 跳过", flush=True)

print("done", flush=True)

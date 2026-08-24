# 实验I2: sandbox-init Unix socket 协议探测
# /run/vercel/share/init.sock 由 sandbox-init 监听, 同用户可访问
import socket, subprocess, os

def run(cmd, timeout=10):
    try:
        r = subprocess.run(["bash", "-c", cmd], capture_output=True, timeout=timeout)
        return (r.stdout + r.stderr).decode(errors='replace')
    except Exception as e:
        return f"ERR {e}"

print("== [1] share 目录 ==")
print(run("ls -la /run/vercel/share/; ls -la /run/vercel/"))
print(run("cat /run/vercel/share/sandbox-init 2>&1 | head -c 200"))

print("== [2] init 进程详情 ==")
print(run("cat /proc/1/cmdline 2>/dev/null | tr '\\0' ' '; echo; ls -la /proc/1/fd/ 2>/dev/null | head -20"))
print(run("ls -la /proc/1/root/ 2>/dev/null | head -10"))

print("== [3] socket 连接探测 ==")
def sock_probe(payload, timeout=3, label=""):
    try:
        s = socket.socket(socket.AF_UNIX, socket.SOCK_STREAM)
        s.settimeout(timeout)
        s.connect("/run/vercel/share/init.sock")
        if payload:
            s.sendall(payload)
        try:
            data = s.recv(512)
            print(f"  [{label}] recv: {data[:200]!r}")
        except socket.timeout:
            print(f"  [{label}] timeout (no response)")
        s.close()
    except Exception as e:
        print(f"  [{label}] ERR {type(e).__name__}: {e}")

sock_probe(b"", 3, "empty")
sock_probe(b"GET / HTTP/1.0\r\n\r\n", 3, "http")
sock_probe(b"SSH-2.0-probe\r\n", 3, "ssh-banner")
sock_probe(b"\x16\x03\x01\x00\x05\x01\x00\x00\x01", 3, "tls")

print("== [4] DGRAM socket ==")
try:
    s = socket.socket(socket.AF_UNIX, socket.SOCK_DGRAM)
    s.settimeout(3)
    s.sendto(b"hello", "/run/vercel/share/init.sock")
    try:
        print("  dgram recv:", s.recv(512)[:200])
    except socket.timeout:
        print("  dgram timeout")
    s.close()
except Exception as e:
    print("  dgram ERR:", e)

print("== [5] sandbox-init 二进制分析 ==")
print(run("file /run/vercel/share/sandbox-init 2>&1; strings /run/vercel/share/sandbox-init 2>/dev/null | grep -i -E 'vercel|token|api|http|socket|command|exec' | head -25"))

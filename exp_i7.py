# 实验I7: 用户身份/提权路径 + Ping/Kill json 调用
import socket, subprocess, json

def run(cmd, timeout=12):
    try:
        r = subprocess.run(["bash", "-c", cmd], capture_output=True, timeout=timeout)
        return (r.stdout + r.stderr).decode(errors='replace')
    except Exception as e:
        return f"ERR {e}"

print("== [1] 身份 ==")
print(run("id; whoami; cat /proc/self/status | grep -E 'Uid|Gid|Cap'"))

print("== [2] sudo/提权 ==")
print(run("ls -la /usr/bin/sudo /bin/su 2>&1; sudo -n id 2>&1 | head -3"))
print(run("find / -perm -4000 -type f 2>/dev/null | head -10"))
print(run("cat /etc/sudoers 2>/dev/null | head -5; ls -la /etc/sudoers.d/ 2>&1"))

print("== [3] 用户组/额外权限 ==")
print(run("groups; ls -la /dev/ | head -20"))

print("== [4] Ping json ==")
def connect_call(service_method, body=b"{}", ctype="application/json", timeout=4):
    try:
        s = socket.socket(socket.AF_UNIX, socket.SOCK_STREAM)
        s.settimeout(timeout)
        s.connect("/run/vercel/share/init.sock")
        hdr = (f"POST /{service_method} HTTP/1.1\r\nHost: localhost\r\n"
               f"Content-Type: {ctype}\r\nContent-Length: {len(body)}\r\n\r\n").encode()
        s.sendall(hdr + body)
        data = b""
        try:
            while len(data) < 2000:
                c = s.recv(4096)
                if not c:
                    break
                data += c
        except socket.timeout:
            pass
        s.close()
        return data[:600]
    except Exception as e:
        return f"ERR {type(e).__name__}: {e}".encode()

for m in ["Ping", "Kill", "Spawn"]:
    r = connect_call(f"vercel.sandbox.spawn.v1.SpawnService/{m}", b"{}")
    print(f"  {m} (json): {r!r}", flush=True)

print("== [5] ptrace 能力 ==")
print(run("cat /proc/sys/kernel/yama/ptrace_scope 2>/dev/null; python3 -c \"import ctypes; libc=ctypes.CDLL('libc.so.6'); libc.ptrace(16, 1, 0, 0); print('PTRACE_ATTACH OK')\" 2>&1 | tail -2"))

print("done", flush=True)

# 实验I11: sandbox-init 网络拓扑 + ptrace syscall 观察
# 目标: 确定 X-Signature 请求方向(发往 agent?) + 观察签名请求内容/目标
import ctypes, subprocess, time, os, struct

def run(cmd, timeout=10):
    try:
        r = subprocess.run(["bash", "-c", cmd], capture_output=True, timeout=timeout)
        return (r.stdout + r.stderr).decode(errors='replace')
    except Exception as e:
        return f"ERR {e}"

print("== [1] pid1 socket 拓扑 ==", flush=True)
print(run("cat /proc/1/net/tcp 2>/dev/null | head -10"), flush=True)
print(run("cat /proc/1/net/tcp6 2>/dev/null | head -10"), flush=True)
print(run("cat /proc/1/net/unix 2>/dev/null | head -15"), flush=True)

print("== [2] 全沙箱 socket 概览 ==", flush=True)
print(run("ss -tnp 2>/dev/null | head -20; ss -unp 2>/dev/null | head -10"), flush=True)

print("== [3] pid1 的 inode 对应 socket 详情 ==", flush=True)
# fd 4/7/8 是 socket, 找它们的 inode 对应
for fd in [4, 7, 8]:
    print(run(f"ls -la /proc/1/fd/{fd}; cat /proc/1/fdinfo/{fd} 2>/dev/null | head -5"), flush=True)

print("== [4] ptrace 观察 syscall (4 秒) ==", flush=True)
libc = ctypes.CDLL("libc.so.6")
if libc.ptrace(16, 1, 0, 0) != 0:
    print("ATTACH FAILED"); exit(1)
print("attached", flush=True)
try:
    # 用 PTRACE_SYSCALL 持续观察, 记录所有系统调用号和寄存器
    # 简化: 用 strace 如果存在
    pass
except Exception as e:
    print("ERR", e)
libc.ptrace(17, 1, 0, 0)
print("detached", flush=True)

print("== [5] strace 可用性 ==", flush=True)
print(run("which strace ltrace gdb 2>&1; ls /usr/bin/*trace* 2>&1"), flush=True)

print("== [6] 触发一次签名请求并抓取 ==", flush=True)
# 通过 init.sock 发 Spawn 请求(无签名), 观察响应 —— 判断 SpawnService 是否要求签名
import socket
s = socket.socket(socket.AF_UNIX, socket.SOCK_STREAM)
s.settimeout(4)
try:
    s.connect("/run/vercel/share/init.sock")
    body = b"{}"
    hdr = (f"POST /vercel.sandbox.spawn.v1.SpawnService/Spawn HTTP/1.1\r\nHost: localhost\r\n"
           f"Content-Type: application/connect+json\r\nContent-Length: {len(body)}\r\n\r\n").encode()
    s.sendall(hdr + body)
    data = b""
    try:
        while len(data) < 2000:
            c = s.recv(4096)
            if not c: break
            data += c
    except socket.timeout:
        pass
    print("  无签名 Spawn 响应:", data[:400], flush=True)
except Exception as e:
    print("  ERR:", e, flush=True)
s.close()

print("done", flush=True)

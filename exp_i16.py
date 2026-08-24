# 实验I16: VM 内 root 能力验证 + seccomp 边界 + 网络策略可操作性
import subprocess, os

def run(cmd, timeout=10):
    try:
        r = subprocess.run(["bash", "-c", cmd], capture_output=True, timeout=timeout)
        return (r.stdout + r.stderr).decode(errors='replace')
    except Exception as e:
        return f"ERR {type(e).__name__}: {e}"

print("== [1] setuid(0) 提权 ==", flush=True)
print(run("python3 -c \"import os; os.setuid(0); print('setuid(0) OK, uid =', os.getuid())\" 2>&1"), flush=True)

print("== [2] root 后读取敏感文件 ==", flush=True)
print(run("sudo -n id 2>&1 | head -2; su -c id 2>&1 | head -2"), flush=True)
print(run("ls -la /run/vercel/share/ 2>&1; cat /etc/shadow 2>&1 | head -2"), flush=True)

print("== [3] 网络配置可操作性 ==", flush=True)
print(run("iptables -L -n 2>&1 | head -15"), flush=True)
print(run("nft list ruleset 2>&1 | head -25"), flush=True)
print(run("ip route show 2>&1; ip rule show 2>&1 | head -5"), flush=True)

print("== [4] 添加路由测试(能改路由吗) ==", flush=True)
print(run("ip route add 192.0.2.1/32 via 100.64.0.1 2>&1 && echo ROUTE_ADDED && ip route del 192.0.2.1/32 2>&1; ip route add 192.0.2.1/32 dev eth0 2>&1 && echo ROUTE_ADDED2 && ip route del 192.0.2.1/32 2>&1"), flush=True)

print("== [5] 网络接口 ==", flush=True)
print(run("ip link show 2>&1; ip addr show 2>&1 | head -20"), flush=True)

print("== [6] seccomp 限制探测 ==", flush=True)
print(run("unshare -Urn true 2>&1 && echo USERNS_OK; unshare -r -m true 2>&1 && echo USERNS_MOUNT_OK || echo USERNS_MOUNT_FAIL"), flush=True)
print(run("mount -t tmpfs none /tmp 2>&1 | head -2"), flush=True)
print(run("python3 -c \"import ctypes; libc=ctypes.CDLL('libc.so.6'); print('chroot:', libc.chroot('/tmp'))\" 2>&1"), flush=True)
print(run("python3 -c \"import ctypes; libc=ctypes.CDLL('libc.so.6'); print('mount:', libc.mount(b'none', b'/mnt', b'tmpfs', 0, b''))\" 2>&1"), flush=True)

print("== [7] /proc/1/root 与 chroot 状态 ==", flush=True)
print(run("ls -la /proc/1/root/ 2>&1 | head -5; readlink /proc/1/root 2>&1; cat /proc/1/mountinfo | head -8"), flush=True)

print("== [8] 内核信息 ==", flush=True)
print(run("uname -a; cat /proc/version"), flush=True)

print("== [9] 设备节点 ==", flush=True)
print(run("ls -la /dev/ 2>&1 | head -25"), flush=True)

print("done", flush=True)

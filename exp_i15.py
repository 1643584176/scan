# 实验I15: 用户进程 vs sandbox-init 权限对比 + seccomp 检查
import subprocess, os

def run(cmd, timeout=10):
    try:
        r = subprocess.run(["bash", "-c", cmd], capture_output=True, timeout=timeout)
        return (r.stdout + r.stderr).decode(errors='replace')
    except Exception as e:
        return f"ERR {type(e).__name__}: {e}"

print("== [1] 当前进程(用户代码) 权限 ==", flush=True)
print(run("id; cat /proc/self/status | grep -E 'Uid|Gid|CapEff|CapBnd|NoNewPrivs|Seccomp'"), flush=True)
print(run("cat /proc/self/attr/current 2>/dev/null; echo; cat /proc/self/seccomp 2>/dev/null"), flush=True)

print("== [2] sandbox-init 权限对比 ==", flush=True)
print(run("cat /proc/1/status | grep -E 'Uid|Gid|CapEff|CapBnd|NoNewPrivs|Seccomp'"), flush=True)
print(run("cat /proc/1/attr/current 2>/dev/null; echo; cat /proc/1/seccomp 2>/dev/null"), flush=True)

print("== [3] 父进程链 ==", flush=True)
print(run("pstree -p 2>/dev/null | head -20 || ps -ef | head -20"), flush=True)

print("== [4] 用户代码能做的敏感操作(对照) ==", flush=True)
print(run("python3 -c \"import socket; s=socket.socket(socket.AF_INET, socket.SOCK_RAW, socket.IPPROTO_RAW); print('RAW SOCKET OK')\" 2>&1"), flush=True)
print(run("unshare -Urn true 2>&1 && echo 'USERNS OK' || echo 'USERNS FAIL'"), flush=True)
print(run("mount -t tmpfs none /tmp/mnt_test 2>&1 && echo 'MOUNT OK' && umount /tmp/mnt_test || echo 'MOUNT FAIL'"), flush=True)
print(run("cat /proc/sys/kernel/yama/ptrace_scope 2>/dev/null"), flush=True)

print("== [5] 当前用户代码能否读取 sandbox-init 的 agent 连接数据 ==", flush=True)
# 通过 /proc/1/fd/8 (socket) 无法直接读, 但确认对端信息
print(run("cat /proc/1/net/tcp6 | awk 'NR>1' | head -5"), flush=True)

print("== [6] 是否所有沙箱进程都是 uid 1000 + 无 cap ==", flush=True)
print(run("for p in /proc/[0-9]*; do pn=${p#/proc/}; [ \"$pn\" = \"1\" ] && continue; st=$(grep -E '^(Uid|CapEff)' $p/status 2>/dev/null | tr '\\n' ' '); echo \"pid $pn: $st\"; done 2>/dev/null | head -15"), flush=True)

print("== [7] sandbox-init spawn 的用户进程 caps(我们的 shell) ==", flush=True)
print(run("grep CapEff /proc/self/status; capsh --print 2>/dev/null | head -10 || echo 'no capsh'"), flush=True)

print("done", flush=True)

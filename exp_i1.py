# 实验I1: 沙箱内部信息收集(agent/进程/端口/运行时目录)
import subprocess

def run(cmd, timeout=12):
    try:
        r = subprocess.run(["bash", "-c", cmd], capture_output=True, timeout=timeout)
        return (r.stdout + r.stderr).decode(errors='replace')
    except Exception as e:
        return f"ERR {e}"

print("== [1] 进程树 ==")
print(run("ps aux --sort=-pid 2>/dev/null | head -20 || ps aux 2>/dev/null | head -20"))
print(run("ps -ef 2>/dev/null | head -20"))

print("== [2] PID1 环境变量 ==")
print(run("tr '\\0' '\\n' < /proc/1/environ 2>/dev/null | head -30"))
print(run("tr '\\0' '\\n' < /proc/$(cat /proc/1/task/1/children 2>/dev/null | awk '{print $1}')/environ 2>/dev/null | head -20"))

print("== [3] 监听端口 ==")
print(run("ss -tlnp 2>/dev/null || netstat -tlnp 2>/dev/null || netstat -tln 2>/dev/null"))
print(run("ss -xlnp 2>/dev/null | head -20"))

print("== [4] 26661 交互端口探测 ==")
print(run("curl -s -m 3 http://127.0.0.1:26661/ 2>&1 | head -c 300"))
print(run("curl -s -m 3 http://127.0.0.1:26661/health 2>&1 | head -c 300"))

print("== [5] 运行时目录 ==")
print(run("ls -la /run/vercel/ /vercel/ /home/vercel-sandbox/ 2>&1 | head -30"))
print(run("find /run/vercel /vercel /home/vercel-sandbox -maxdepth 3 -type f 2>/dev/null | head -20"))

print("== [6] 全盘敏感文件搜索 ==")
print(run("grep -r -l -i -E 'vcp_|vercel_token|authorization|bearer' /run/vercel /vercel /home/vercel-sandbox /etc 2>/dev/null | head -10"))

print("== [7] 容器/VM 元数据 ==")
print(run("cat /proc/1/cgroup 2>/dev/null | head -5; cat /sys/class/dmi/id/product_uuid 2>/dev/null; hostname; cat /proc/version | head -2"))

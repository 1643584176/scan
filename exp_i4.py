# 实验I4: sandbox-init 二进制字符串分析(快速)
import subprocess

def run(cmd, timeout=30):
    try:
        r = subprocess.run(["bash", "-c", cmd], capture_output=True, timeout=timeout)
        return (r.stdout + r.stderr).decode(errors='replace')
    except Exception as e:
        return f"ERR {e}"

print("== [1] 二进制大小/类型 ==")
print(run("ls -la /run/vercel/share/sandbox-init; head -c 20 /run/vercel/share/sandbox-init | xxd | head -2"))

print("== [2] HTTP 相关字符串 ==")
print(run("grep -a -o -E '([A-Za-z]+ )?(/[a-zA-Z0-9_.-]{1,40})' /run/vercel/share/sandbox-init 2>/dev/null | grep -v -E '^\\.|/lib|/usr|/etc|/proc|/sys|/dev|/var|/tmp|/bin|/include|/share|/home|/run|/vercel|/opt' | sort -u | head -40"))

print("== [3] vercel 相关 ==")
print(run("grep -a -o -E 'vercel[a-zA-Z0-9_.-]{0,40}' /run/vercel/share/sandbox-init 2>/dev/null | sort -u | head -30"))

print("== [4] http 方法/头 ==")
print(run("grep -a -o -E '(GET|POST|PUT|DELETE|PATCH|OPTIONS|Content-Type|Authorization|x-[a-z-]+)' /run/vercel/share/sandbox-init 2>/dev/null | sort -u | head -25"))

print("== [5] 可疑 URL ==")
print(run("grep -a -o -E 'https?://[a-zA-Z0-9./_-]{5,80}' /run/vercel/share/sandbox-init 2>/dev/null | sort -u | head -20"))

print("== [6] socket/通信 ==")
print(run("grep -a -o -E '(unix|socket|grpc|http2|quic|tcp|listen|dial)[a-zA-Z0-9_.-]{0,20}' /run/vercel/share/sandbox-init 2>/dev/null | sort -u | head -20"))

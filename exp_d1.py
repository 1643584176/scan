# 实验D1: DNS 解析归属判定 + 劫持实验
# 1) 查看沙箱 DNS 配置
# 2) 修改 /etc/resolv.conf 指向不可达 DNS -> 请求 example.com 判断防火墙是否用沙箱 DNS
# 3) 若沙箱 DNS 生效 -> 指向攻击者 DNS 可完全控制 SNI 域名解析(凭据窃取链)
import subprocess, socket, time

def run(cmd, timeout=15):
    try:
        r = subprocess.run(["bash", "-c", cmd], capture_output=True, timeout=timeout)
        return r.stdout.decode(errors='replace') + r.stderr.decode(errors='replace')
    except Exception as e:
        return f"ERR {e}"

print("== [1] resolv.conf ==")
print(run("cat /etc/resolv.conf 2>&1"))

print("== [2] 基线: 请求 example.com (原始 DNS) ==")
t0 = time.time()
try:
    s = socket.create_connection(("example.com", 443), timeout=10)
    print(f"   CONNECTED ({time.time()-t0:.2f}s)")
    s.close()
except Exception as e:
    print(f"   ERR {type(e).__name__}:{e}")

print("== [3] 修改 resolv.conf -> 192.0.2.1 (黑孔 DNS) ==")
print(run("cp /etc/resolv.conf /tmp/resolv.bak && echo 'nameserver 192.0.2.1' > /etc/resolv.conf && cat /etc/resolv.conf"))
t0 = time.time()
try:
    s = socket.create_connection(("example.com", 443), timeout=10)
    print(f"   CONNECTED ({time.time()-t0:.2f}s) -> 防火墙未用沙箱 DNS")
    s.close()
except Exception as e:
    print(f"   ERR {type(e).__name__}:{e} ({time.time()-t0:.2f}s) -> 防火墙可能用沙箱 DNS!")

print("== [4] 恢复 ==")
print(run("cp /tmp/resolv.bak /etc/resolv.conf"))

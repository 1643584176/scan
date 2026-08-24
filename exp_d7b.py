# 实验D7b: 100.64.0.0/10 网段快速并发扫描
import socket, threading, time

PORTS = [22, 80, 443, 2379, 26661, 3000, 5432, 6379, 8080, 9000, 3306, 9200]
LOCK = threading.Lock()
found = []
done = 0

def probe(host, port, timeout=1.2):
    s = socket.socket(); s.settimeout(timeout)
    try:
        s.connect((host, port))
        with LOCK:
            found.append((host, port))
            print(f"  *** FOUND {host}:{port}", flush=True)
    except Exception:
        pass
    finally:
        s.close()

def scan_range(prefix_list):
    """prefix_list: ['100.64.57', '100.64.0', ...]"""
    global done
    threads = []
    for prefix in prefix_list:
        for i in range(1, 255):
            host = f"{prefix}.{i}"
            for p in PORTS:
                t = threading.Thread(target=probe, args=(host, p))
                t.start()
                threads.append(t)
                while len(threads) >= 400:
                    threads[0].join(timeout=0.1)
                    if not threads[0].is_alive():
                        threads.pop(0)
    for t in threads:
        t.join(timeout=2)

print(f"开始扫描 (IP:{len(PORTS)}端口 x 并发)", flush=True)
t0 = time.time()

# 1. 自己 /24: 100.64.57.0/24
print("== 扫描 100.64.57.0/24 ==", flush=True)
scan_range(["100.64.57"])

# 2. 网关抽查
print("== 抽查其他段 ==", flush=True)
for third in [0, 1, 2, 16, 32, 64, 96, 128, 160, 192, 224]:
    scan_range([f"100.64.{third}"])
    print(f"  段 100.64.{third} 完成, 累计发现: {found}", flush=True)

print(f"\n扫描完成 {time.time()-t0:.1f}s, 发现: {found}")

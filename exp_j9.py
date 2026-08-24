# 实验J9: ptrace attach pid1 窃听 agent 签名请求(触发式)
# J8: /proc/1/fd 打开失败(ENXIO), 但 fd7/8=agent 连接确认
# 思路: 无YAMA+同uid+全cap -> strace attach pid1 -> 触发 cmd 让 agent 发 Spawn 签名请求
#       捕获 recvmsg/read 内容 = 签名头名+timestamp格式+消息格式 全解!
# 驱动配合: 本脚本启动后台 strace 后快速退出, 驱动再发第二个 cmd 触发 agent 请求
import os, re, subprocess, time, sys

def run(cmd, timeout=15):
    try:
        r = subprocess.run(["bash", "-c", cmd], capture_output=True, timeout=timeout)
        return (r.stdout + r.stderr).decode(errors='replace')
    except Exception as e:
        return f"ERR {type(e).__name__}: {e}"

mode = sys.argv[1] if len(sys.argv) > 1 else "capture"

if mode == "check":
    print("== 工具可用性 ==", flush=True)
    for t in ["strace", "gdb", "ltrace", "perf", "bpftrace"]:
        print(f"  {t}: {run(f'which {t}')}", flush=True)
    print("== ptrace 权限预检 ==", flush=True)
    # 尝试 attach 再 detach
    print(run("strace -p 1 -e trace=none -o /tmp/pt_test.log & sleep 1; kill %1 2>/dev/null; cat /tmp/pt_test.log 2>/dev/null | head -3"), flush=True)
    print("done", flush=True)

elif mode == "capture":
    print("[capture] 启动后台 strace", flush=True)
    # 清理旧日志
    run("rm -f /tmp/st.log /tmp/st.err")
    # attach pid1: 跟踪所有 fd 的 read/recvmsg, 保存完整数据
    cmd = ("strace -f -p 1 -e trace=read,recvfrom,recvmsg,write,sendto,sendmsg "
           "-s 8192 -o /tmp/st.log 2>/tmp/st.err & echo $! > /tmp/st.pid")
    print(run(cmd), flush=True)
    time.sleep(2)
    # 检查 strace 是否活着
    print(run("cat /tmp/st.err 2>/dev/null | head -3"), flush=True)
    print(run("ps aux | grep -v grep | grep strace | head -3"), flush=True)
    print("[capture] strace 已启动, 等待驱动触发 agent 请求", flush=True)
    # 保持短暂存活让驱动有时间发第二个 cmd(其实 strace 是后台的, 这里直接退出)
    time.sleep(3)
    print("done", flush=True)

elif mode == "dump":
    print("== strace 日志 ==", flush=True)
    print(run("wc -l /tmp/st.log 2>/dev/null"), flush=True)
    # 提取 read/recvmsg 调用内容, 找 HTTP 请求头(含 signature)
    log = run("grep -a -A3 'recvmsg\|read(' /tmp/st.log 2>/dev/null | head -200")
    print(log, flush=True)
    # 直接找 signature 头
    print("== signature 头搜索 ==", flush=True)
    print(run("grep -ai 'signature\\|timestamp\\|POST\\|HTTP/' /tmp/st.log 2>/dev/null | head -20"), flush=True)
    print("done", flush=True)

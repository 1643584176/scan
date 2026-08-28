# -*- coding: utf-8 -*-
"""exp_pidfd v13 驱动: 变体验证 trigger
v13 相对 v12:
  - trigger 改为 3 种可判别命令, 6 轮:
    cat /etc/hostname -> guest 注入 'out' (伪造 stdout=FAKEHOST-xxx)
    sleep 2; echo done -> guest 注入 'exit7' (伪造 exit code 7)
    ps aux -> guest 注入 'hang' (仅 started, 命令挂起)
  - guest 侧: accept 注入按请求内容选变体(auto) + 连接池注入线程(免竞速)"""
import json, base64, time, sys, os
from vercel_driver import api, TEAM, PROJ, fresh_sandbox, cmd

STOP_MARKER = 'ALLDONE'

ROUND = [
    ("bash", ["-c", "cat /etc/hostname"]),
    ("bash", ["-c", "sleep 2; echo done"]),
    ("bash", ["-c", "ps aux | head -3"]),
]


def run_pidfd_v13():
    sid = fresh_sandbox("exp_pidfd")
    print("sid:", sid)
    # 注入脚本
    here = os.path.dirname(os.path.abspath(__file__))
    code = open(os.path.join(here, "pidfd_guest.py"), "rb").read()
    payload = base64.b64encode(code).decode()
    inject = "import base64;open('/vercel/sandbox/pidfd_guest.py','wb').write(base64.b64decode('%s'))" % payload
    c, r = cmd(sid, "python3", ["-c", inject], timeout_ms=30000)
    print("inject:", c, r[:200])

    # 后台启动 guest(nohup, stderr 落盘)
    start = "nohup python3 /vercel/sandbox/pidfd_guest.py >/dev/null 2>/vercel/sandbox/pidfd.err & echo STARTED"
    c, r = cmd(sid, "bash", ["-c", start], timeout_ms=30000)
    print("start:", c, r[:200])

    # 等 PHASE1+2 完成
    time.sleep(25)
    c, r = cmd(sid, "cat", ["/vercel/sandbox/pidfd.out"], timeout_ms=30000)
    print("=== t+25s 中期检查 ===")
    print(r[:1500])
    c, r = cmd(sid, "cat", ["/vercel/sandbox/pidfd.err"], timeout_ms=30000)
    print("=== stderr ===")
    print(r[:800])

    # 6 轮 × 3 种 trigger(间隔 1s, 轮间 7s) => ~90s(观察期 85s 覆盖大部分)
    for rnd in range(6):
        for j in range(3):
            kind = ROUND[j]
            c, r = cmd(sid, kind[0], kind[1], timeout_ms=40000)
            print("trig %d.%d %s: %d %s" % (rnd, j, kind[0], c, r[:600]))
            time.sleep(1)
        time.sleep(7)

    # 等 guest 结束
    time.sleep(30)
    c, r = cmd(sid, "bash", ["-c", "ps aux | grep -v grep | grep pidfd_guest; echo PS_DONE"], timeout_ms=30000)
    print("=== ps ===")
    print(r[:400])
    c, r = cmd(sid, "cat", ["/vercel/sandbox/pidfd.err"], timeout_ms=30000)
    print("=== stderr2 ===")
    print(r[:800])

    # cat 结果(双通道 + 哨兵)
    for attempt in range(6):
        time.sleep(3)
        c, r = cmd(sid, "cat", ["/vercel/sandbox/pidfd.out"], timeout_ms=30000)
        if c == 200 and STOP_MARKER in r:
            print("=== 最终结果 ===")
            print(r)
            return r
        print("attempt %d: %s" % (attempt, r[:200]))
    c, r = cmd(sid, "cat", ["/vercel/sandbox/pidfd.out"], timeout_ms=30000)
    print("=== 最后结果 ===")
    print(r)
    return r


if __name__ == "__main__":
    run_pidfd_v13()

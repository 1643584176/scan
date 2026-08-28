# -*- coding: utf-8 -*-
"""exp_j330 收尾: 重建沙箱 -> 后台起监听 -> 制造流量 -> 前台等结果"""
import json, base64, time, sys, os, threading
from vercel_driver import api, TEAM, PROJ, fresh_sandbox, cmd

STOP_MARKER = 'SCAN_DONE'
HERE = os.path.dirname(os.path.abspath(__file__))


def run_full():
    sid = fresh_sandbox("exp330b")
    print("sid:", sid)

    code = open(os.path.join(HERE, "exp330b_guest.py"), "rb").read()
    payload = base64.b64encode(code).decode()
    inject = "import base64;open('/vercel/sandbox/exp330b.py','wb').write(base64.b64decode('%s'))" % payload
    c, r = cmd(sid, "python3", ["-c", inject], timeout_ms=30000)
    print("inject:", c)

    # 后台起监听(60s 超时, 让它跑满 35s)
    def run_listen():
        c, r = cmd(sid, "python3", ["/vercel/sandbox/exp330b.py"], timeout_ms=90000)
        print("run listen:", c, r[:300])

    t = threading.Thread(target=run_listen)
    t.start()

    # 等待 8s 让监听先启动, 然后制造流量
    time.sleep(8)
    print("--- 制造流量 ---")
    c, r = cmd(sid, "ping", ["-c", "2", "-W", "2", "100.64.0.1"], timeout_ms=15000)
    print("ping gw:", c, r[:200])
    c, r = cmd(sid, "curl", ["-m", "10", "-s", "https://httpbin.org/ip"], timeout_ms=20000)
    print("curl out:", c, r[:200])
    c, r = cmd(sid, "python3", ["-c",
        "import socket;s=socket.socket();s.settimeout(3);print(s.connect_ex(('100.64.0.1',443)))"],
        timeout_ms=15000)
    print("conn gw443:", c, r[:200])

    t.join(timeout=100)
    # cat 结果
    for attempt in range(4):
        time.sleep(2)
        c, r = cmd(sid, "cat", ["/vercel/sandbox/arp330b.out"], timeout_ms=30000)
        if c == 200 and STOP_MARKER in r:
            print("=== 监听结果 ===")
            print(r)
            return r
    c, r = cmd(sid, "cat", ["/vercel/sandbox/arp330b.out"], timeout_ms=30000)
    print("=== 最后结果 ===")
    print(r)
    return r


if __name__ == "__main__":
    run_full()

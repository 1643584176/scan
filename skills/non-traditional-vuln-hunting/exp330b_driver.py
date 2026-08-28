# -*- coding: utf-8 -*-
"""exp_j330b 驱动: 复用现有 sandbox 跑 promiscuous 监听"""
import json, base64, time, sys, os
from vercel_driver import api, TEAM, PROJ, cmd

STOP_MARKER = 'SCAN_DONE'


def run(sid):
    code = open(os.path.join(os.path.dirname(os.path.abspath(__file__)), "exp330b_guest.py"), "rb").read()
    payload = base64.b64encode(code).decode()
    inject = "import base64;open('/vercel/sandbox/exp330b.py','wb').write(base64.b64decode('%s'))" % payload
    c, r = cmd(sid, "python3", ["-c", inject], timeout_ms=30000)
    print("inject:", c, r[:150])
    c, r = cmd(sid, "python3", ["/vercel/sandbox/exp330b.py"], timeout_ms=60000)
    print("run:", c, r[:500])
    for attempt in range(4):
        time.sleep(2)
        c, r = cmd(sid, "cat", ["/vercel/sandbox/arp330b.out"], timeout_ms=30000)
        if c == 200 and STOP_MARKER in r:
            print("=== 结果 ===")
            print(r)
            return r
    c, r = cmd(sid, "cat", ["/vercel/sandbox/arp330b.out"], timeout_ms=30000)
    print("=== 最后结果 ===")
    print(r)
    return r


if __name__ == "__main__":
    sid = sys.argv[1]
    run(sid)

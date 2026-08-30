# -*- coding: utf-8 -*-
"""exp_j332 驱动"""
import base64, time, os, threading
from vercel_driver import cmd

HERE = os.path.dirname(os.path.abspath(__file__))
STOP_MARKER = 'SCAN_DONE'


def run(sid):
    cmd(sid, "sh", ["-c", "mkdir -p /vercel/sandbox"], timeout_ms=15000)
    code = open(os.path.join(HERE, "exp332_guest.py"), "rb").read()
    payload = base64.b64encode(code).decode()
    inject = "import base64;open('/vercel/sandbox/exp332.py','wb').write(base64.b64decode('%s'))" % payload
    c, r = cmd(sid, "python3", ["-c", inject], timeout_ms=30000)
    print("inject:", c)
    c, r = cmd(sid, "python3", ["/vercel/sandbox/exp332.py"], timeout_ms=120000)
    print("run:", c, r[:300])
    for attempt in range(4):
        time.sleep(2)
        c, r = cmd(sid, "cat", ["/vercel/sandbox/arp332.out"], timeout_ms=30000)
        if c == 200 and STOP_MARKER in r:
            print("=== 结果 ===")
            print(r)
            return r
        print("attempt", attempt, c)
    c, r = cmd(sid, "cat", ["/vercel/sandbox/arp332.out"], timeout_ms=30000)
    print("=== 最后结果 ===")
    print(r)
    return r


if __name__ == "__main__":
    import sys
    run(sys.argv[1])

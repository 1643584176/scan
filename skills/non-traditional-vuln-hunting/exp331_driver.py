# -*- coding: utf-8 -*-
"""exp_j331 驱动: 复用 exp330b 沙箱(sbx_ve9hIQazyGFZ92JEB30GyctbWJ2z 可能还在)"""
import json, base64, time, sys, os, threading
from vercel_driver import api, TEAM, PROJ, fresh_sandbox, cmd

STOP_MARKER = 'SCAN_DONE'
HERE = os.path.dirname(os.path.abspath(__file__))


def run_full():
    sid = fresh_sandbox("exp331")
    print("sid:", sid)

    code = open(os.path.join(HERE, "exp331_guest.py"), "rb").read()
    payload = base64.b64encode(code).decode()
    inject = "import base64;open('/vercel/sandbox/exp331.py','wb').write(base64.b64decode('%s'))" % payload
    c, r = cmd(sid, "python3", ["-c", inject], timeout_ms=30000)
    print("inject:", c)

    def run_listen():
        c, r = cmd(sid, "python3", ["/vercel/sandbox/exp331.py"], timeout_ms=120000)
        print("run:", c, r[:200])

    t = threading.Thread(target=run_listen)
    t.start()

    # 制造流量(多域 curl 让广播域活跃)
    time.sleep(10)
    for i, dom in enumerate(["https://httpbin.org/ip", "https://example.com/", "https://www.cloudflare.com/"]):
        c, r = cmd(sid, "curl", ["-m", "8", "-s", "-o", "/dev/null", "-w", "%{http_code}", dom],
                   timeout_ms=15000)
        print("curl %d:" % i, c, r[:100])
        time.sleep(2)

    t.join(timeout=130)
    for attempt in range(4):
        time.sleep(2)
        c, r = cmd(sid, "cat", ["/vercel/sandbox/arp331.out"], timeout_ms=30000)
        if c == 200 and STOP_MARKER in r:
            print("=== 结果 ===")
            print(r)
            return r
        print("attempt", attempt, c, r[:200])
    c, r = cmd(sid, "cat", ["/vercel/sandbox/arp331.out"], timeout_ms=30000)
    print("=== 最后结果 ===")
    print(r)
    return r


if __name__ == "__main__":
    run_full()

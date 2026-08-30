# -*- coding: utf-8 -*-
"""host_probe 驱动: 创建沙箱 -> 注入 host_probe_guest.py -> 执行 -> 拉取结果"""
import base64, json, os, sys, time
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
from vercel_driver import api, cmd, fresh_sandbox

HERE = os.path.dirname(os.path.abspath(__file__))
MARKER = 'HOSTPROBE_DONE'


def run(name="hostprobe1", network="allow-all"):
    sid = fresh_sandbox(name, network_mode=network)
    print("sid:", sid, flush=True)
    time.sleep(2)
    code = open(os.path.join(HERE, "host_probe_guest.py"), "rb").read()
    payload = base64.b64encode(code).decode()
    inject = "import base64;open('/vercel/sandbox/hp.py','wb').write(base64.b64decode('%s'))" % payload
    c, r = cmd(sid, "python3", ["-c", inject], timeout_ms=30000)
    print("inject:", c, r[:200], flush=True)
    c, r = cmd(sid, "python3", ["/vercel/sandbox/hp.py"], timeout_ms=180000)
    print("run:", c, flush=True)
    if c == 200:
        print(r[:600], flush=True)
    for attempt in range(6):
        time.sleep(2)
        c, r = cmd(sid, "cat", ["/vercel/sandbox/host_probe.out"], timeout_ms=30000)
        if c == 200 and MARKER in r:
            print("=== 结果 ===", flush=True)
            print(r, flush=True)
            return sid, r
        print("attempt %d status=%d" % (attempt, c), flush=True)
    c, r = cmd(sid, "cat", ["/vercel/sandbox/host_probe.out"], timeout_ms=30000)
    print("=== 最后结果 ===", flush=True)
    print(r, flush=True)
    return sid, r


if __name__ == "__main__":
    import sys as _s
    name = _s.argv[1] if len(_s.argv) > 1 else "hostprobe1"
    net = _s.argv[2] if len(_s.argv) > 2 else "allow-all"
    run(name, net)

# -*- coding: utf-8 -*-
"""批量 host 面扫描: 循环建沙箱跑 guest 脚本, 汇总关键信号
用法: python _batch_probe.py [数量] [前缀] [guest.py] [哨兵]
结果保存到 reports/_batch_host_scan.txt"""
import base64, json, os, sys, time
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
from vercel_driver import api, cmd, fresh_sandbox

N = int(sys.argv[1]) if len(sys.argv) > 1 else 4
PFX = sys.argv[2] if len(sys.argv) > 2 else "bscan"
HERE = os.path.dirname(os.path.abspath(__file__))
GUEST = sys.argv[3] if len(sys.argv) > 3 else "guest_fast.py"
MARKER = sys.argv[4] if len(sys.argv) > 4 else "FASTPROBE_DONE"
OUTNAME = sys.argv[5] if len(sys.argv) > 5 else "fast_probe.out"
REPORT = os.path.join(os.path.dirname(os.path.dirname(HERE)), "reports", "_batch_host_scan.txt")

code = open(os.path.join(HERE, GUEST), "rb").read()
payload = base64.b64encode(code).decode()
inject = "import base64;open('/vercel/sandbox/fp.py','wb').write(base64.b64decode('%s'))" % payload

results = []
for i in range(1, N + 1):
    name = "%s%d" % (PFX, i)
    print("=== %s (%d/%d) ===" % (name, i, N), flush=True)
    try:
        sid = fresh_sandbox(name)
        print("sid:", sid, flush=True)
        time.sleep(1)
        c, r = cmd(sid, "python3", ["-c", inject], timeout_ms=30000)
        print("inject:", c, flush=True)
        if c != 200:
            print("inject fail:", r[:200], flush=True)
            continue
        c, r = cmd(sid, "python3", ["/vercel/sandbox/fp.py"], timeout_ms=60000)
        print("run:", c, flush=True)
        got = None
        for attempt in range(5):
            time.sleep(2)
            c, r = cmd(sid, "cat", ["/vercel/sandbox/" + OUTNAME], timeout_ms=30000)
            if c == 200 and MARKER in r:
                got = r
                break
            print("attempt %d status=%d" % (attempt, c), flush=True)
        if not got:
            print("no result for %s" % name, flush=True)
            results.append("=== %s: NO RESULT ===" % name)
            continue
        # 提取信号
        hits = [l for l in got.split('\\n') if l.startswith('HIT') or l.startswith('nosig') or l.startswith('field')]
        key = []
        for sig in ["/run/cell/cell.sock", "/run/metrics/metrics.sock", "HIT", "nosig"]:
            if sig in got:
                key.append(sig)
        cell_ok = "cell.sock -> CONNECT_OK" in got
        metrics_ok = "metrics.sock -> CONNECT_OK" in got
        print("signals:", key, "cell_conn=%s metrics_conn=%s" % (cell_ok, metrics_ok), flush=True)
        for h in hits:
            print("  ", h[:180], flush=True)
        head = got[:3000]
        results.append("=== %s sid=%s cell_conn=%s metrics_conn=%s hits=%d ===" % (name, sid, cell_ok, metrics_ok, len(hits)))
        results.append(head)
    except Exception as e:
        print("ERR %s: %s" % (name, e), flush=True)
        results.append("=== %s: ERR %s ===" % (name, e))

open(REPORT, "w", encoding="utf-8").write("\n\n".join(results))
print("report saved:", REPORT, flush=True)

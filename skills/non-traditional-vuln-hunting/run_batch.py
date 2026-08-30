# -*- coding: utf-8 -*-
"""批量沙箱驱动: 创建沙箱 -> 注入 guest 脚本 -> 逐个运行 -> 拉回结果到 out/
用法: python run_batch.py <sandbox_name> <network_mode> <script:outfile:marker> [...]
例:   python run_batch.py exp332b allow-all exp332_guest.py:arp332.out:SCAN_DONE
"""
import base64, json, os, sys, time

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
from vercel_driver import api, cmd, fresh_sandbox

HERE = os.path.dirname(os.path.abspath(__file__))
OUTDIR = os.path.join(os.path.dirname(HERE), 'out')
os.makedirs(OUTDIR, exist_ok=True)


def inject_and_run(sid, guest_name, outfile, marker, run_timeout_ms=150000, wait_rounds=8):
    code = open(os.path.join(HERE, guest_name), 'rb').read()
    payload = base64.b64encode(code).decode()
    script_name = guest_name.replace('.py', '.py')
    inject = "import base64;open('/vercel/sandbox/%s','wb').write(base64.b64decode('%s'))" % (script_name, payload)
    c, r = cmd(sid, 'python3', ['-c', inject], timeout_ms=30000)
    print('  [inject %s] %d' % (script_name, c), flush=True)
    time.sleep(1)
    c, r = cmd(sid, 'python3', ['/vercel/sandbox/' + script_name], timeout_ms=run_timeout_ms)
    print('  [run %s] %d %s' % (script_name, c, r[:200].replace('\n', ' ')), flush=True)
    time.sleep(1)
    for attempt in range(wait_rounds):
        time.sleep(3)
        c, r = cmd(sid, 'cat', ['/vercel/sandbox/' + outfile], timeout_ms=30000)
        if c == 200 and marker in r:
            print('  [done %s] round=%d len=%d' % (script_name, attempt, len(r)), flush=True)
            return r
        print('  [wait %s] r%d status=%d' % (script_name, attempt, c), flush=True)
    c, r = cmd(sid, 'cat', ['/vercel/sandbox/' + outfile], timeout_ms=30000)
    print('  [final %s] status=%d' % (script_name, c), flush=True)
    return r if c == 200 else ('(no output) status=%d' % c)


def main():
    name = sys.argv[1]
    net = sys.argv[2]
    jobs = []
    for spec in sys.argv[3:]:
        parts = spec.split(':')
        jobs.append((parts[0], parts[1], parts[2]))
    sid = fresh_sandbox(name, network_mode=net)
    print('sid:', sid, flush=True)
    time.sleep(2)
    results = {}
    for guest, outfile, marker in jobs:
        try:
            res = inject_and_run(sid, guest, outfile, marker)
        except Exception as e:
            res = 'DRIVER_EXC: %s' % e
        results[guest] = res
        stamp = time.strftime('%Y%m%d_%H%M%S')
        fn = os.path.join(OUTDIR, '%s_%s_%s.txt' % (name, guest.replace('.py', ''), stamp))
        with open(fn, 'w', encoding='utf-8') as f:
            f.write(res)
        print('  saved ->', fn, flush=True)
        time.sleep(1)
    print('=== ALL DONE ===', flush=True)


if __name__ == '__main__':
    main()

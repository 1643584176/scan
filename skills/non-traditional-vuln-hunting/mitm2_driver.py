# -*- coding: utf-8 -*-
"""mitm2_driver: 容错版 MITM 驱动 (修复: 每步 try/except + 打印完整错误)
用法: python mitm2_driver.py <sandbox_name> [already_created]
"""
import base64, json, os, sys, time

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
from vercel_driver import api, cmd, fresh_sandbox

HERE = os.path.dirname(os.path.abspath(__file__))
OUTDIR = os.path.join(os.path.dirname(HERE), 'out')
name = sys.argv[1] if len(sys.argv) > 1 else 'mitme'


def step(label, fn):
    try:
        r = fn()
        print('[OK] %s -> %s' % (label, str(r)[:200]), flush=True)
        return r
    except Exception as e:
        print('[EXC] %s -> %s' % (label, e), flush=True)
        return None


def main():
    sid = step('create', lambda: fresh_sandbox(name, network_mode='allow-all'))
    if not sid:
        return
    time.sleep(2)
    code = open(os.path.join(HERE, 'mitm_init_proxy_guest.py'), 'rb').read()
    payload = base64.b64encode(code).decode()
    inject = "import base64;open('/vercel/sandbox/mitm.py','wb').write(base64.b64decode('%s'))" % payload
    step('inject', lambda: cmd(sid, 'python3', ['-c', inject], timeout_ms=30000))
    time.sleep(1)
    bg = 'cd /vercel/sandbox && nohup python3 mitm.py > mitm_nohup.txt 2>&1 & echo BG_OK'
    step('start_proxy', lambda: cmd(sid, 'bash', ['-c', bg], timeout_ms=30000))
    time.sleep(8)
    for i in range(8):
        step('traffic%d' % i, lambda i=i: cmd(sid, 'echo', ['mitm-traffic-%d' % i], timeout_ms=30000))
        time.sleep(5)
    time.sleep(20)
    for fname in ['mitm_cap.b64', 'mitm_resp.b64', 'mitm_heartbeat.txt', 'mitm_nohup.txt']:
        c, r = step('pull_%s' % fname, lambda fname=fname: cmd(sid, 'cat', ['/vercel/sandbox/' + fname], timeout_ms=30000))
        if c == 200:
            local = os.path.join(OUTDIR, '%s_%s' % (fname, name))
            with open(local, 'w', encoding='utf-8', errors='replace') as f:
                f.write(r)
            print('  saved -> %s (len=%d)' % (local, len(r)), flush=True)
        time.sleep(1)
    print('=== MITM2 DONE ===', flush=True)


if __name__ == '__main__':
    main()

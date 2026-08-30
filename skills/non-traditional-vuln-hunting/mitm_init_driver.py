# -*- coding: utf-8 -*-
"""mitm_init_driver: 驱动 MITM 重抓 (C 项)
1) 创建沙箱 -> 注入 mitm_init_proxy_guest.py -> 后台启动
2) 驱动侧发 8 次 cmd (制造 host->init 的 Spawn 流量)
3) 拉回 mitm_cap.b64 / mitm_resp.b64 / mitm_heartbeat.txt
4) base64 解码落盘本地供分析"""
import base64, json, os, sys, time

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
from vercel_driver import cmd, fresh_sandbox

HERE = os.path.dirname(os.path.abspath(__file__))
OUTDIR = os.path.join(os.path.dirname(HERE), 'out')
os.makedirs(OUTDIR, exist_ok=True)


def main():
    name = sys.argv[1] if len(sys.argv) > 1 else 'mitmb'
    sid = fresh_sandbox(name, network_mode='allow-all')
    print('sid:', sid, flush=True)
    time.sleep(2)
    code = open(os.path.join(HERE, 'mitm_init_proxy_guest.py'), 'rb').read()
    payload = base64.b64encode(code).decode()
    inject = "import base64;open('/vercel/sandbox/mitm.py','wb').write(base64.b64decode('%s'))" % payload
    c, r = cmd(sid, 'python3', ['-c', inject], timeout_ms=30000)
    print('inject:', c, r[:200], flush=True)
    time.sleep(1)
    # 后台启动代理
    c, r = cmd(sid, 'bash', ['-c', 'cd /vercel/sandbox && nohup python3 mitm.py > mitm_nohup.txt 2>&1 & echo BG_OK'],
               timeout_ms=30000)
    print('start proxy:', c, r[:300], flush=True)
    time.sleep(5)
    # 制造流量: 8 次 cmd
    for i in range(8):
        c, r = cmd(sid, 'echo', ['mitm-traffic-%d' % i], timeout_ms=30000)
        print('traffic %d: %d %s' % (i, c, r[:100].replace('\n', ' ')), flush=True)
        time.sleep(4)
    # 等待代理窗口结束
    time.sleep(15)
    for fname, local in [('mitm_cap.b64', 'mitm_cap_%s.b64' % name),
                         ('mitm_resp.b64', 'mitm_resp_%s.b64' % name),
                         ('mitm_heartbeat.txt', 'mitm_hb_%s.txt' % name),
                         ('mitm_nohup.txt', 'mitm_nohup_%s.txt' % name)]:
        c, r = cmd(sid, 'cat', ['/vercel/sandbox/' + fname], timeout_ms=30000)
        print('pull %s: %d len=%d' % (fname, c, len(r)), flush=True)
        if c == 200:
            with open(os.path.join(OUTDIR, local), 'w', encoding='utf-8', errors='replace') as f:
                f.write(r)
            print('  saved -> out/%s' % local, flush=True)
        time.sleep(1)
    # 本地解码 cap/resp
    for b64name in ['mitm_cap_%s.b64' % name, 'mitm_resp_%s.b64' % name]:
        p = os.path.join(OUTDIR, b64name)
        if not os.path.exists(p):
            continue
        lines = [l.strip() for l in open(p, encoding='utf-8', errors='replace').read().splitlines() if l.strip()]
        print('=== %s: %d frames ===' % (b64name, len(lines)), flush=True)
        out_dec = p.replace('.b64', '_dec.bin')
        with open(out_dec, 'wb') as f:
            for i, l in enumerate(lines):
                try:
                    raw = base64.b64decode(l)
                    f.write(b'\n----- frame %d (%dB) -----\n' % (i, len(raw)))
                    f.write(raw)
                    print('  frame %d: %dB head=%s' % (i, len(raw), raw[:120]), flush=True)
                except Exception as e:
                    print('  frame %d decode err %s' % (i, e), flush=True)
        print('  decoded -> %s' % out_dec, flush=True)
    print('=== MITM DONE ===', flush=True)


if __name__ == '__main__':
    main()

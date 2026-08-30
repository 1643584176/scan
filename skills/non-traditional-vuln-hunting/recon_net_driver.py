# -*- coding: utf-8 -*-
"""recon_net driver: 创建 allow-all 沙箱, 注入网络拓扑侦察脚本, 读取结果
用法: python recon_net_driver.py [sandbox_name]
"""
import sys, json, time, os
sys.path.insert(0, r'F:\scan\skills\non-traditional-vuln-hunting')
sys.stdout.reconfigure(encoding='utf-8')
from vercel_driver import fresh_sandbox, api, TEAM

name = sys.argv[1] if len(sys.argv) > 1 else 'recon1'

sid = fresh_sandbox(name, 'allow-all')
print('SID:', sid, flush=True)
time.sleep(3)

guest = open(os.path.join(os.path.dirname(__file__), 'recon_net_guest.py'), encoding='utf-8').read()
code = "cat > /tmp/recon_net.py <<'PYEOF'\n" + guest + "\nPYEOF\nnohup python3 /tmp/recon_net.py > /tmp/recon_run.log 2>&1 &\necho LAUNCHED"

c, r = api('POST', '/v2/sandboxes/sessions/%s/cmd?teamId=%s' % (sid, TEAM),
           {'command': 'bash', 'args': ['-lc', code], 'wait': False, 'timeout': 20000})
print('launch:', c, r[:200], flush=True)

# 轮询输出
for i in range(20):
    time.sleep(6)
    c, r = api('POST', '/v2/sandboxes/sessions/%s/cmd?teamId=%s' % (sid, TEAM),
               {'command': 'cat', 'args': ['/vercel/sandbox/recon_net.out'], 'wait': True, 'logs': True, 'timeout': 15000})
    if 'RECON_DONE' in r:
        print('=== OUTPUT (attempt %d) ===' % i, flush=True)
        # 提取 data 行
        for ln in r.splitlines():
            if ln.startswith('{"data"'):
                try:
                    d = json.loads(ln)
                    print(d.get('data', ''), flush=True)
                except Exception:
                    print(ln[:500], flush=True)
        break
    if i % 5 == 0:
        print('... waiting (%d)' % i, flush=True)

print('=== DONE ===', flush=True)

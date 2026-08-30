# -*- coding: utf-8 -*-
"""通用 guest 注入 driver: 创建/复用沙箱, 注入 guest 脚本, 轮询输出
用法: python run_guest_driver.py <sandbox_name> <guest_script> <mode> <sentinel>
mode: allow-all / custom / deny-all
"""
import sys, json, time, os
sys.path.insert(0, r'F:\scan\skills\non-traditional-vuln-hunting')
sys.stdout.reconfigure(encoding='utf-8')
from vercel_driver import fresh_sandbox, api, TEAM

name = sys.argv[1]
guest_file = sys.argv[2]
mode = sys.argv[3] if len(sys.argv) > 3 else 'allow-all'
sentinel = sys.argv[4] if len(sys.argv) > 4 else 'DONE'

sid = fresh_sandbox(name, mode)
print('SID:', sid, flush=True)
time.sleep(3)

guest = open(os.path.join(os.path.dirname(__file__), guest_file), encoding='utf-8').read()
code = ("cat > /tmp/g.py <<'PYEOF'\n" + guest + "\nPYEOF\n"
        "nohup python3 /tmp/g.py > /tmp/g_run.log 2>&1 &\necho LAUNCHED")

c, r = api('POST', '/v2/sandboxes/sessions/%s/cmd?teamId=%s' % (sid, TEAM),
           {'command': 'bash', 'args': ['-lc', code], 'wait': False, 'timeout': 20000})
print('launch:', c, r[:150], flush=True)

for i in range(60):
    time.sleep(8)
    c, r = api('POST', '/v2/sandboxes/sessions/%s/cmd?teamId=%s' % (sid, TEAM),
               {'command': 'cat', 'args': ['/vercel/sandbox/%s' % guest_file.replace('.py', '.out')],
                'wait': True, 'logs': True, 'timeout': 15000})
    if sentinel in r:
        print('=== OUTPUT (attempt %d) ===' % i, flush=True)
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

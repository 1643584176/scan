# -*- coding: utf-8 -*-
"""在指定 sid 上注入运行 guest 脚本 (不新建沙箱)
用法: python run_on_sid.py <sid> <guest.py> <outfile> <marker>
"""
import base64, os, sys, time
sys.path.insert(0, r'F:\scan\skills\non-traditional-vuln-hunting')
from vercel_driver import cmd

sid = sys.argv[1]
guest = sys.argv[2]
outfile = sys.argv[3]
marker = sys.argv[4]

HERE = r'F:\scan\skills\non-traditional-vuln-hunting'
code = open(os.path.join(HERE, guest), 'rb').read()
payload = base64.b64encode(code).decode()

inject = "import base64;open('/vercel/sandbox/%s','wb').write(base64.b64decode('%s'))" % (guest, payload)
c, r = cmd(sid, 'python3', ['-c', inject], timeout_ms=30000)
print('inject:', c, r[:100])
time.sleep(1)

c, r = cmd(sid, 'python3', ['/vercel/sandbox/' + guest], timeout_ms=120000)
print('run:', c, r[:200])

for attempt in range(10):
    time.sleep(3)
    c, r = cmd(sid, 'cat', ['/vercel/sandbox/' + outfile], timeout_ms=30000)
    if c == 200 and marker in r:
        print('done round=%d len=%d' % (attempt, len(r)))
        fn = os.path.join(r'F:\scan\skills\out', '%s_%s.txt' % (guest.replace('.py', ''), time.strftime('%Y%m%d_%H%M%S')))
        with open(fn, 'w', encoding='utf-8') as f:
            f.write(r)
        print('saved ->', fn)
        break
    print('wait r%d status=%d' % (attempt, c))

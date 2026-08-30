# -*- coding: utf-8 -*-
"""resume 指定沙箱后注入运行 guest 脚本
用法: python run_resumed.py <sbname> <guest.py> <outfile> <marker>
"""
import base64, json, os, sys, time
sys.path.insert(0, r'F:\scan\skills\non-traditional-vuln-hunting')
sys.stdout.reconfigure(encoding='utf-8')
from vercel_driver import api, cmd, TEAM, PROJ

name = sys.argv[1]
guest = sys.argv[2]
outfile = sys.argv[3]
marker = sys.argv[4]

HERE = r'F:\scan\skills\non-traditional-vuln-hunting'
OUTDIR = r'F:\scan\skills\out'

c, r = api('GET', '/v2/sandboxes/%s?teamId=%s&projectId=%s&resume=true' % (name, TEAM, PROJ))
print('resume %s:' % name, c, flush=True)
if c != 200:
    print('FAIL:', r[:300], flush=True)
    sys.exit(1)
sid = json.loads(r)['sandbox']['currentSessionId']
print('sid:', sid, flush=True)
time.sleep(2)

code = open(os.path.join(HERE, guest), 'rb').read()
payload = base64.b64encode(code).decode()
inject = "import base64;open('/vercel/sandbox/%s','wb').write(base64.b64decode('%s'))" % (guest, payload)
c, r = cmd(sid, 'python3', ['-c', inject], timeout_ms=30000)
print('inject:', c, r[:100], flush=True)
time.sleep(1)
c, r = cmd(sid, 'python3', ['/vercel/sandbox/' + guest], timeout_ms=180000)
print('run:', c, r[:150], flush=True)

for attempt in range(15):
    time.sleep(4)
    c, r = cmd(sid, 'cat', ['/vercel/sandbox/' + outfile], timeout_ms=30000)
    if c == 200 and marker in r:
        fn = os.path.join(OUTDIR, '%s_%s_%s.txt' % (name, guest.replace('.py', ''), time.strftime('%Y%m%d_%H%M%S')))
        open(fn, 'w', encoding='utf-8').write(r)
        print('saved ->', fn, flush=True)
        break
    print('wait r%d status=%d' % (attempt, c), flush=True)
print('=== DONE ===', flush=True)

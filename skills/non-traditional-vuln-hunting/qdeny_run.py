# -*- coding: utf-8 -*-
"""qdeny_run: 创建 deny-all 沙箱(创建时传参) -> 跑 udp_bypass 抓完整输出
输出: 本地控制台 + out/qdeny_full.txt
"""
import base64, json, os, sys, time

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
from vercel_driver import api, cmd, fresh_sandbox

HERE = os.path.dirname(os.path.abspath(__file__))
OUTDIR = os.path.join(os.path.dirname(HERE), 'out')
name = 'qdeny1'

sid = fresh_sandbox(name, network_mode='deny-all')
print('sid:', sid, flush=True)
time.sleep(2)

# 详情确认 policy
c, r = api("GET", "/v2/sandboxes/%s?teamId=%s&projectId=%s" % (name, "team_GIy1SZ444lspqeNbh4r8uAUg", "prj_iyw2xfjP3RKPT7n8b8c1tBIxxK5F"))
print('detail:', c, r[:500], flush=True)

code = open(os.path.join(HERE, 'udp_bypass_guest.py'), 'rb').read()
payload = base64.b64encode(code).decode()
inject = "import base64;open('/vercel/sandbox/udp_bypass_guest.py','wb').write(base64.b64decode('%s'))" % payload
c, r = cmd(sid, 'python3', ['-c', inject], timeout_ms=30000)
print('inject:', c, flush=True)
time.sleep(1)
c, r = cmd(sid, 'python3', ['/vercel/sandbox/udp_bypass_guest.py'], timeout_ms=180000)
print('run status:', c, flush=True)
out_txt = r
try:
    d2 = json.loads(r)
    parts = []
    for k in d2:
        if k == 'command':
            continue
        parts.append('--- %s ---\n%s' % (k, str(d2[k])))
    out_txt = '\n'.join(parts)
except Exception:
    pass
print(out_txt[:8000], flush=True)

with open(os.path.join(OUTDIR, 'qdeny1_full.txt'), 'w', encoding='utf-8') as f:
    f.write(out_txt)
print('saved -> skills/out/qdeny1_full.txt', flush=True)

time.sleep(2)
c, r = cmd(sid, 'cat', ['/vercel/sandbox/udp_bypass.out'], timeout_ms=30000)
print('cat out:', c, flush=True)
try:
    d3 = json.loads(r)
    cat_txt = str(d3.get('data', r))
except Exception:
    cat_txt = r
print(cat_txt[:8000], flush=True)
with open(os.path.join(OUTDIR, 'qdeny1_out.txt'), 'w', encoding='utf-8') as f:
    f.write(cat_txt)
print('saved -> skills/out/qdeny1_out.txt', flush=True)
print('=== QDENY DONE ===', flush=True)

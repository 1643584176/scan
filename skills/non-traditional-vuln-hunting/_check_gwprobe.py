# -*- coding: utf-8 -*-
"""检查 gwprobe1 沙箱的探测输出状态"""
import sys, json, time
sys.path.insert(0, r'F:\scan\skills\non-traditional-vuln-hunting')
sys.stdout.reconfigure(encoding='utf-8')
from vercel_driver import api, TEAM

# 1) 查看沙箱状态
c, r = api('GET', '/v2/sandboxes/gwprobe1?teamId=%s' % TEAM)
print('GET gwprobe1:', c, flush=True)
try:
    d = json.loads(r)
    sb = d.get('sandbox', {})
    print('status:', sb.get('status'), 'sid:', sb.get('currentSessionId'), flush=True)
    sid = sb.get('currentSessionId')
except Exception as e:
    print('parse err:', e, r[:300], flush=True)
    sid = None

# 2) 读输出文件
if sid:
    c, r = api('POST', '/v2/sandboxes/sessions/%s/cmd?teamId=%s' % (sid, TEAM),
               {'command': 'cat', 'args': ['/vercel/sandbox/gwprobe.out'],
                'wait': True, 'logs': True, 'timeout': 15000})
    print('read status:', c, flush=True)
    if 'GWPROBE_DONE' in r:
        for ln in r.splitlines():
            if ln.startswith('{"data"'):
                try:
                    d = json.loads(ln)
                    print(d.get('data', ''), flush=True)
                except Exception:
                    pass
    else:
        print('not done yet, tail:', flush=True)
        for ln in r.splitlines():
            if ln.startswith('{"data"'):
                try:
                    d = json.loads(ln)
                    print(d.get('data', '')[-1500:], flush=True)
                except Exception:
                    pass

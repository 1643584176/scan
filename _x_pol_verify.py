# -*- coding: utf-8 -*-
"""P 线实测: 修复 conn_test - 解析 cmd 响应 JSON 的 data 字段
对 ppol2 (resume 后) 与 ppol1 (resume 后) 做实测出网验证"""
import json, re, sys, time
sys.path.insert(0, r'F:\scan\skills\non-traditional-vuln-hunting')
sys.stdout.reconfigure(encoding='utf-8')
from vercel_driver import api, cmd, TEAM, PROJ

def conn_test(sid, tag):
    """实测: 1.1.1.1:443 与 httpbin.org:443; 解析 JSON data 字段"""
    def probe(ip, port):
        sc = 'python3 -c "import socket; s=socket.socket(); s.settimeout(4); rc=s.connect_ex((\'%s\',%d)); print(\'RC_\', rc)"' % (ip, port)
        c, r = cmd(sid, 'sh', ['-c', sc], timeout_ms=30000)
        rc = '?'
        try:
            for line in r.splitlines():
                if '"data"' in line:
                    d = json.loads(line).get('data', '')
                    m = re.search(r'RC_ (\d+)', d)
                    if m:
                        rc = m.group(1)
        except Exception as e:
            rc = 'ERR:%s' % e
        return rc
    pub = probe('1.1.1.1', 443)
    hb = probe('httpbin.org', 443)
    print('[%s] PUB_443=%s HTTPBIN_443=%s' % (tag, pub, hb), flush=True)
    return pub, hb

# ppol2 resume 后
c, r = api('GET', '/v2/sandboxes/ppol2?teamId=%s&projectId=%s' % (TEAM, PROJ))
d = json.loads(r)
sid2 = d['sandbox']['currentSessionId']
print('ppol2 sid:', sid2, 'status:', d['sandbox']['status'], flush=True)
conn_test(sid2, 'S2-resume-verified')

# ppol1 resume 后
c, r = api('GET', '/v2/sandboxes/ppol1?teamId=%s&projectId=%s' % (TEAM, PROJ))
d = json.loads(r)
sid1 = d['sandbox']['currentSessionId']
print('ppol1 sid:', sid1, 'status:', d['sandbox']['status'], flush=True)
conn_test(sid1, 'S1-resume-verified')

print('=== VERIFY DONE ===', flush=True)

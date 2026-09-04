# -*- coding: utf-8 -*-
"""③ branch diff/apply 桥探测(diff 只读;apply 仅探校验不真执行)
JS:POST /sites/{s}/database/branch/{id}/diff(无 body)
    POST /sites/{s}/database/branch/{id}/apply + body JSON(r 结构未知)
"""
import http.client, ssl, gzip, json, sys
sys.path.insert(0, r'D:\scan\netlify_report')
from _net_creds import TOKEN_B

SITE_B = 'd2977de0-d24d-4544-81cb-933e610cad7d'
BR_A1 = 'agent-6a98d5e6448c07a76d7babf3'   # B 的 agent 分支
ctx = ssl.create_default_context()


def api(method, path, body=None):
    conn = http.client.HTTPSConnection('api.netlify.com', context=ctx, timeout=40)
    h = {'User-Agent': 'Mozilla/5.0', 'Accept': 'application/json',
         'Content-Type': 'application/json', 'Authorization': 'Bearer ' + TOKEN_B}
    b = json.dumps(body).encode() if body is not None else None
    conn.request(method, path, body=b, headers=h)
    r = conn.getresponse()
    raw = r.read()
    st = r.status
    out = raw.decode('utf-8', 'ignore')
    conn.close()
    return st, out


base = '/api/v1/sites/%s/database/branch' % SITE_B
print('== diff(只读)==')
for label, bid in [('diff agent1', BR_A1), ('diff production', 'production'),
                   ('diff no-such', 'no-such-branch-xyz')]:
    st, out = api('POST', '%s/%s/diff' % (base, bid))
    print('%-16s [%d] %s' % (label, st, out[:600]))
    print()

print('== apply 校验探测(不真执行:用不存在的分支 id)==')
for body in [None, {}, {'queries': []}, {'sql': 'select 1'}, {'changes': []}, {'statements': []}]:
    st, out = api('POST', '%s/no-such-branch-xyz/apply' % base, body)
    print('apply no-such + %-28s [%d] %s' % (str(body), st, out[:250]))

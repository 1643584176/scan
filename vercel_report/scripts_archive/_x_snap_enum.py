# -*- coding: utf-8 -*-
"""快照创建/恢复端点枚举 + 快照 IDOR 前置 (v44s)
1) 建沙箱 snaptest
2) 枚举 POST 创建快照端点
3) 若有快照 id, 测试 GET 详情/恢复端点"""
import sys, json, time
sys.path.insert(0, r'F:\scan\skills\non-traditional-vuln-hunting')
sys.stdout.reconfigure(encoding='utf-8')
from vercel_driver import api, cmd, TEAM, PROJ

NAME = 'snaptest44'

def mk():
    api("DELETE", "/v2/sandboxes/%s?teamId=%s&projectId=%s" % (NAME, TEAM, PROJ))
    time.sleep(3)
    c, r = api("POST", "/v4/sandboxes?teamId=%s" % TEAM,
               {"projectId": PROJ, "name": NAME}, 60)
    print('[create] -> %s' % c, flush=True)
    if c != 200:
        sys.exit(1)
    return json.loads(r)['sandbox']['currentSessionId']

# POST 创建快照候选
CREATE_CANDS = [
    ('POST', '/v2/sandboxes/%s/snapshots' % NAME, {"name": NAME + "-s1"}),
    ('POST', '/v2/sandboxes/snapshots', {"name": NAME, "sandbox": NAME}),
    ('POST', '/v2/sandboxes/%s/snapshot' % NAME, {}),
    ('POST', '/v2/sandboxes/%s/snapshots' % NAME, {}),
    ('POST', '/v2/snapshots', {"name": NAME, "sandbox": NAME}),
    ('POST', '/v2/sandboxes/%s/snapshots' % NAME, {"description": "t"}),
]

if __name__ == '__main__':
    sid = mk()
    print('sid =', sid, flush=True)
    time.sleep(3)
    for m, p, b in CREATE_CANDS:
        c, r = api(m, p, b, timeout=90)
        print('%s %s body=%s -> %d %s' % (m, p, json.dumps(b)[:60], c, (r or '')[:300]), flush=True)
        time.sleep(1.5)
    # 列出快照确认
    c, r = api("GET", "/v2/sandboxes/snapshots?teamId=%s&project=%s&limit=20" % (TEAM, PROJ))
    print('list -> %d %s' % (c, (r or '')[:500]), flush=True)
    # 尝试从 sandbox GET 响应中找快照字段
    c, r = api('GET', '/v2/sandboxes/%s?teamId=%s&projectId=%s' % (NAME, TEAM, PROJ))
    print('get -> %d %s' % (c, (r or '')[:500]), flush=True)
    api("DELETE", "/v2/sandboxes/%s?teamId=%s&projectId=%s" % (NAME, TEAM, PROJ))
    print('CLEANED', flush=True)

# -*- coding: utf-8 -*-
"""生命周期端点枚举 (v44p): stop/pause/restart/start 等"""
import json, sys, time
sys.path.insert(0, r'F:\scan\skills\non-traditional-vuln-hunting')
sys.stdout.reconfigure(encoding='utf-8')
from vercel_driver import api, cmd, TEAM, PROJ

NAME = 'poltest44'

if __name__ == '__main__':
    # 先确认沙箱存在
    c, r = api('GET', '/v2/sandboxes/%s?teamId=%s&projectId=%s' % (NAME, TEAM, PROJ))
    print('get:', c, (r or '')[:150], flush=True)
    sid = None
    try:
        sid = json.loads(r)['sandbox']['currentSessionId']
    except Exception:
        print('no sandbox, create one', flush=True)
        api("DELETE", "/v2/sandboxes/%s?teamId=%s&projectId=%s" % (NAME, TEAM, PROJ))
        time.sleep(2)
        c, r = api("POST", "/v4/sandboxes?teamId=%s" % TEAM, {"projectId": PROJ, "name": NAME}, 60)
        sid = json.loads(r)['sandbox']['currentSessionId']
    print('sid =', sid, flush=True)
    for ep in ['/v2/sandboxes/%s/stop' % NAME,
               '/v2/sandboxes/%s/pause' % NAME,
               '/v2/sandboxes/%s/restart' % NAME,
               '/v2/sandboxes/%s/start' % NAME,
               '/v2/sandboxes/%s/resume' % NAME,
               '/v2/sandboxes/sessions/%s/stop' % sid,
               '/v2/sandboxes/sessions/%s/pause' % sid]:
        c, r = api('POST', ep + '?teamId=%s&projectId=%s' % (TEAM, PROJ), {}, timeout=90)
        print('%s -> %d %s' % (ep, c, (r or '')[:200]), flush=True)
        time.sleep(1)
    # 清理
    api("DELETE", "/v2/sandboxes/%s?teamId=%s&projectId=%s" % (NAME, TEAM, PROJ))
    print('CLEANED', flush=True)

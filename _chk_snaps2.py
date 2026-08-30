# -*- coding: utf-8 -*-
"""清理全部快照释放 Hobby Snapshots Storage 配额 (402 解锁)"""
import sys, json, time
sys.path.insert(0, r'F:\scan\skills\non-traditional-vuln-hunting')
sys.stdout.reconfigure(encoding='utf-8')
from vercel_driver import api, TEAM, PROJ

def ls():
    c, r = api('GET', '/v2/sandboxes/snapshots?teamId=%s&project=%s&limit=50' % (TEAM, PROJ), timeout=30)
    if c != 200:
        print('list fail', c, r[:200])
        return []
    try:
        return json.loads(r).get('snapshots', [])
    except Exception as e:
        print('parse fail', e, r[:200])
        return []

snaps = ls()
print('total snapshots:', len(snaps))
for s in snaps:
    print('  %s size=%d status=%s src=%s' % (s.get('id'), s.get('sizeBytes', 0), s.get('status'), s.get('sourceSandboxName', s.get('sourceSessionId', '?'))))

for s in snaps:
    sid = s.get('id')
    if not sid:
        continue
    for m, p in [
        ('DELETE', '/v2/sandboxes/snapshots/%s?teamId=%s&project=%s' % (sid, TEAM, PROJ)),
        ('DELETE', '/v2/snapshots/%s?teamId=%s&project=%s' % (sid, TEAM, PROJ)),
        ('DELETE', '/v2/snapshots/%s?teamId=%s' % (sid, TEAM)),
    ]:
        c, r = api(m, p, timeout=60)
        print('DEL %s -> %d %s' % (p[:70], c, (r or '')[:150]), flush=True)
        if c == 200:
            break
        time.sleep(1)

time.sleep(3)
print('--- after delete ---')
snaps2 = ls()
print('remaining:', len(snaps2))

# 验证创建恢复
c, r = api('POST', '/v4/sandboxes?teamId=%s' % TEAM, {'projectId': PROJ, 'name': 'quota_ok_probe'}, 30)
print('create probe:', c, (r or '')[:250])
if c == 200:
    try:
        sid = json.loads(r)['sandbox']['currentSessionId']
        print('OK sid:', sid)
        time.sleep(2)
        c2, r2 = api('DELETE', '/v2/sandboxes/quota_ok_probe?teamId=%s&projectId=%s' % (TEAM, PROJ))
        print('cleanup:', c2)
    except Exception as e:
        print('cleanup err', e)

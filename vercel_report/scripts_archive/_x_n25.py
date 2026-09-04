# -*- coding: utf-8 -*-
"""非传统面G: 并发 create 同名 — 竞态双实体/会话状态混淆"""
import json, sys, time, threading, requests
sys.path.insert(0, r'F:\scan\skills\non-traditional-vuln-hunting')
sys.stdout.reconfigure(encoding='utf-8')
from vercel_driver import api, TOKEN, TEAM, PROJ, BASE

def log(s): print(s, flush=True)

# 清场
api("DELETE", "/v2/sandboxes/race?teamId=%s&projectId=%s" % (TEAM, PROJ))
time.sleep(2)

results = {}
def create(tag):
    try:
        rr = requests.post('%s/v4/sandboxes?teamId=%s' % (BASE, TEAM),
                           headers={'Authorization': 'Bearer %s' % TOKEN,
                                    'Content-Type': 'application/json'},
                           data=json.dumps({"projectId": PROJ, "name": "race"}), timeout=60)
        results[tag] = (rr.status_code, rr.text[:300])
    except Exception as e:
        results[tag] = ('err', str(e))

# 并发 3 个同名 create
ths = [threading.Thread(target=create, args=('t%d' % i,)) for i in range(3)]
for t in ths: t.start()
for t in ths: t.join()
for k in sorted(results):
    log('[%s] -> %s | %s' % (k, results[k][0], results[k][1].replace(chr(10), ' ')))

# 现在 GET 该沙箱
c, r = api("GET", "/v2/sandboxes/race?teamId=%s&projectId=%s" % (TEAM, PROJ), None, 20)
log('GET race -> %s | %s' % (c, (r or '')[:500].replace(chr(10), ' ')))

# 列表看有多少个 race 实体
c, r = api("GET", "/v2/sandboxes?teamId=%s&project=%s&limit=50" % (TEAM, PROJ), None, 20)
if c == 200:
    try:
        sandboxes = json.loads(r).get('sandboxes', [])
        races = [s.get('name') for s in sandboxes if s.get('name') == 'race']
        log('list race count: %s' % len(races))
        for s in sandboxes:
            if s.get('name') == 'race':
                log('  race: sid=%s status=%s' % (s.get('currentSessionId'), s.get('status')))
    except Exception as e:
        log('list parse err %s' % e)

# 清理所有 race 实体
api("DELETE", "/v2/sandboxes/race?teamId=%s&projectId=%s" % (TEAM, PROJ))
log('DONE')

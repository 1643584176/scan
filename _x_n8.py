# -*- coding: utf-8 -*-
"""候选5b: interactive attach 通道深挖 — token 轮换/生命周期/authz/WS 握手与协议"""
import json, sys, time
sys.path.insert(0, r'F:\scan\skills\non-traditional-vuln-hunting')
sys.stdout.reconfigure(encoding='utf-8')
from vercel_driver import api, TEAM, PROJ

def log(s): print(s, flush=True)

c, r = api("POST", "/v2/sandboxes?teamId=%s" % TEAM, {"projectId": PROJ, "name": "n8"})
if c != 200:
    log('create fail %s' % r[:200]); sys.exit(1)
d = json.loads(r)['sandbox']
name, sid = d['name'], d['currentSessionId']
log('n8 sid=%s' % sid)
time.sleep(3)

I = "/v2/sandboxes/sessions/%s/interactive?teamId=%s" % (sid, TEAM)

def get_int(tag):
    c2, r2 = api("POST", I, {}, 20)
    log('[%s] http=%s | %s' % (tag, c2, (r2[:200] if r2 else '').replace(chr(10), ' ')))
    if c2 == 200:
        return json.loads(r2)
    return None

log('===== token 轮换 =====')
i1 = get_int('call-1')
time.sleep(1)
i2 = get_int('call-2')
if i1 and i2:
    log('token1 == token2: %s' % (i1.get('token') == i2.get('token')))
    log('url1 == url2: %s' % (i1.get('url') == i2.get('url')))

log('')
log('===== authz =====')
c2, r2 = api("POST", "/v2/sandboxes/sessions/%s/interactive?teamId=team_BAD" % sid, {}, 20)
log('bad team -> %s | %s' % (c2, (r2[:100] if r2 else '')))
c2, r2 = api("GET", "/v2/sandboxes/sessions/%s/interactive?teamId=%s" % (sid, TEAM), None, 20)
log('GET -> %s | %s' % (c2, (r2[:100] if r2 else '')))
c2, r2 = api("POST", "/v1/sandboxes/%s/interactive?teamId=%s" % (sid, TEAM), {}, 20)
log('v1 -> %s | %s' % (c2, (r2[:150] if r2 else '').replace(chr(10), ' ')))

log('')
log('===== schema (body 变体) =====')
for tag, body in [('empty', {}), ('cols', {"cols": 80, "rows": 24}), ('null', None)]:
    c2, r2 = api("POST", I, body, 20)
    log('[%s] http=%s | %s' % (tag, c2, (r2[:150] if r2 else '').replace(chr(10), ' ')))

log('')
log('===== WS 握手尝试 =====')
try:
    import websocket
    url = i1['url'] if i1 else None
    tok = i1['token'] if i1 else None
    if url:
        for tag, opts in [
            ('noauth', {}),
            ('q-token', {"header": {"Sec-WebSocket-Protocol": "chat"}}),
        ]:
            try:
                ws = websocket.create_connection(url + ('?token=%s' % tok if tag == 'q-token' else ''),
                                                 timeout=8,
                                                 header={"Authorization": "Bearer %s" % tok} if tag == 'q-token' else {})
                log('[ws-%s] CONNECTED' % tag)
                try:
                    data = ws.recv()
                    log('[ws-%s] recv %d bytes: %s' % (tag, len(data), repr(data[:200])))
                except Exception as e:
                    log('[ws-%s] recv err: %s' % (tag, e))
                ws.close()
            except Exception as e:
                log('[ws-%s] connect err: %s' % (tag, str(e)[:200]))
    else:
        log('no url to test')
except ImportError as e:
    log('websocket-client not available: %s' % e)

api("DELETE", "/v2/sandboxes/n8?teamId=%s&projectId=%s" % (TEAM, PROJ))
log('DONE')

# -*- coding: utf-8 -*-
"""候选5c: interactive WS — token 交叉绑定(跨沙箱)/删除后生命周期/协议帧探索
合规: 全部自有沙箱, 不枚举他人凭据"""
import json, sys, time, socket
sys.path.insert(0, r'F:\scan\skills\non-traditional-vuln-hunting')
sys.stdout.reconfigure(encoding='utf-8')
from vercel_driver import api, TEAM, PROJ
import websocket

def log(s): print(s, flush=True)

def new_sb(name):
    c, r = api("POST", "/v2/sandboxes?teamId=%s" % TEAM, {"projectId": PROJ, "name": name})
    if c != 200:
        log('create %s fail %s' % (name, r[:150])); return None, None
    d = json.loads(r)['sandbox']
    return d['name'], d['currentSessionId']

def get_ws(name, sid):
    c, r = api("POST", "/v2/sandboxes/sessions/%s/interactive?teamId=%s" % (sid, TEAM), {}, 20)
    if c != 200:
        log('interactive %s -> %s' % (name, c)); return None, None
    d = json.loads(r)
    return d['url'], d['token']

def try_ws(tag, url, tok, send=None, timeout=6):
    try:
        ws = websocket.create_connection(url + '?token=' + tok, timeout=timeout)
        log('[%s] CONNECTED' % tag)
        if send is not None:
            try:
                ws.send(send)
                log('[%s] sent %r' % (tag, send[:60]))
            except Exception as e:
                log('[%s] send err: %s' % (tag, e))
        try:
            data = ws.recv()
            log('[%s] recv %d B: %r' % (tag, len(data), data[:200]))
        except Exception as e:
            log('[%s] recv err: %s' % (tag, str(e)[:120]))
        ws.close()
        return True
    except Exception as e:
        log('[%s] connect err: %s' % (tag, str(e)[:160]))
        return False

nA, sA = new_sb('n8a')
nB, sB = new_sb('n8b')
time.sleep(4)
uA, tA = get_ws(nA, sA)
uB, tB = get_ws(nB, sB)
log('A: %s / %s' % (uA, tA))
log('B: %s / %s' % (uB, tB))

log('')
log('===== 1) 对照: A token + A url =====')
okA = try_ws('A-self', uA, tA)

log('')
log('===== 2) 交叉: A token + B url (跨沙箱) =====')
try_ws('A-tok-B-url', uB, tA, timeout=4)

log('')
log('===== 3) 交叉: B token + A url =====')
try_ws('B-tok-A-url', uA, tB, timeout=4)

log('')
log('===== 4) 协议帧探索 (A 会话) =====')
if okA:
    try_ws('frame-json', uA, tA, send=json.dumps({"cols": 80, "rows": 24}), timeout=5)
    try_ws('frame-id', uA, tA, send='id\n', timeout=5)
    try_ws('frame-cmd', uA, tA, send='echo HI_WS_2026\n', timeout=5)

log('')
log('===== 5) 删除 A 后: 旧 token+旧 url =====')
api("DELETE", "/v2/sandboxes/n8a?teamId=%s&projectId=%s" % (TEAM, PROJ))
time.sleep(3)
try_ws('deleted-A', uA, tA, timeout=5)

api("DELETE", "/v2/sandboxes/n8b?teamId=%s&projectId=%s" % (TEAM, PROJ))
log('DONE')

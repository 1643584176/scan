# -*- coding: utf-8 -*-
"""D 线闭环驱动 v2:
1) deny-all 沙箱内全通道测试 (udp_bypass_guest.py)
2) network-policy update 端点: 随机 sid / 已删 sid / 自己的 deny-all sid 改 allow-all
3) create 时 networkPolicy 校验: 非法 mode / 附加字段
"""
import base64, json, os, sys, time
sys.path.insert(0, r'F:\scan\skills\non-traditional-vuln-hunting')
sys.stdout.reconfigure(encoding='utf-8')
from vercel_driver import api, cmd, fresh_sandbox, TEAM, PROJ

HERE = r'F:\scan\skills\non-traditional-vuln-hunting'
OUTDIR = r'F:\scan\skills\out'
GUEST = 'udp_bypass_guest.py'
OUTF = 'udpbypass.out'
MARK = 'UDPBYPASS_DONE'


def save(fn, txt):
    p = os.path.join(OUTDIR, fn)
    open(p, 'w', encoding='utf-8').write(txt)
    print('saved ->', p, flush=True)


def inject_run(sid, tag):
    code = open(os.path.join(HERE, GUEST), 'rb').read()
    payload = base64.b64encode(code).decode()
    inject = "import base64;open('/vercel/sandbox/%s','wb').write(base64.b64decode('%s'))" % (GUEST, payload)
    c, r = cmd(sid, 'python3', ['-c', inject], timeout_ms=30000)
    print('[%s] inject %d' % (tag, c), flush=True)
    time.sleep(1)
    c, r = cmd(sid, 'python3', ['/vercel/sandbox/' + GUEST], timeout_ms=90000)
    print('[%s] run %d' % (tag, c), flush=True)
    for attempt in range(8):
        time.sleep(4)
        c, r = cmd(sid, 'cat', ['/vercel/sandbox/' + OUTF], timeout_ms=30000)
        if c == 200 and MARK in r:
            save('udp_bypass_%s.txt' % tag, r)
            return r
        print('[%s] wait r%d status=%d' % (tag, attempt, c), flush=True)
    return None


# ---- 1) deny-all 沙箱全通道 ----
print('===== 1) deny-all sandbox =====', flush=True)
try:
    sid = fresh_sandbox('denyall2', network_mode='deny-all')
    print('sid:', sid, flush=True)
    time.sleep(2)
    res = inject_run(sid, 'denyall2')
    print('res len:', len(res) if res else None, flush=True)
except Exception as e:
    print('EXC:', e, flush=True)

# ---- 2) network-policy update 端点权限 ----
print()
print('===== 2) network-policy update 权限 =====', flush=True)
RAND = 'sbx_zzz_nonexist_zzz'
DEL = 'sbx_b2TeTovZudMJHqzATCLk5iERq8qi'  # 已删 exp_idor
c, r = api('POST', '/v2/sandboxes/sessions/%s/network-policy?teamId=%s' % (RAND, TEAM), {'mode': 'deny-all'})
print('rand sid set-policy:', c, r[:250], flush=True)
c, r = api('POST', '/v2/sandboxes/sessions/%s/network-policy?teamId=%s' % (DEL, TEAM), {'mode': 'deny-all'})
print('deleted sid set-policy:', c, r[:250], flush=True)
c, r = api('GET', '/v2/sandboxes/sessions/%s/network-policy?teamId=%s' % (RAND, TEAM))
print('rand sid get-policy:', c, r[:250], flush=True)
c, r = api('GET', '/v2/sandboxes/sessions/%s/network-policy?teamId=%s' % (DEL, TEAM))
print('deleted sid get-policy:', c, r[:250], flush=True)

# ---- 3) create networkPolicy 校验 ----
print()
print('===== 3) create networkPolicy 校验 =====', flush=True)
for body in [{'projectId': PROJ, 'name': 'npc1', 'networkPolicy': {'mode': 'bogus-mode'}},
             {'projectId': PROJ, 'name': 'npc2', 'networkPolicy': {'mode': 'deny-all', 'allowedDomains': ['httpbin.org']}},
             {'projectId': PROJ, 'name': 'npc3', 'networkPolicy': {'mode': 'allow-all', 'extra': 1}}]:
    name = body['name']
    api('DELETE', '/v2/sandboxes/%s?teamId=%s&projectId=%s' % (name, TEAM, PROJ))
    time.sleep(1)
    c, r = api('POST', '/v2/sandboxes?teamId=%s' % TEAM, body)
    print('%s -> %d %s' % (name, c, r[:300]), flush=True)

print('=== D2 ALL DONE ===', flush=True)

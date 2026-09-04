# -*- coding: utf-8 -*-
"""v226: resume snapshotId 决定性验证 — 快照A(marker1) vs 快照B(marker2), 指定恢复 A
如果恢复出 marker1 -> snapshotId 参数生效 (潜在 IDOR: 可指定任意快照)
如果恢复出 marker2 -> 参数被忽略, 恢复最新"""
import json, sys, time
sys.path.insert(0, r'D:\scan\skills\non-traditional-vuln-hunting')
sys.stdout.reconfigure(encoding='utf-8')
from vercel_driver import api, TEAM, PROJ, cmd, fresh_sandbox

NAME = 'v226'


def log(s): print(s, flush=True)


def run(marker):
    code = "open('/vercel/sandbox/v226_m.txt','w').write('%s\\n')" % marker
    c, r = cmd(SID, 'python3', ['-c', code], 25000)
    return c


def snap(tag):
    c, r = api('POST', '/v2/sandboxes/sessions/%s/snapshot?teamId=%s' % (SID, TEAM), {}, 120)
    log('snap %s -> %s | %s' % (tag, c, (r or '')[:200]))
    if c == 201:
        return json.loads(r)['snapshot']['id']
    return None


def resume(tag, snapid=None):
    q = '/v2/sandboxes/%s?teamId=%s&projectId=%s&resume=true' % (NAME, TEAM, PROJ)
    if snapid:
        q += '&snapshotId=%s' % snapid
    c, r = api('GET', q, None, 90)
    log('resume %s -> %s | %s' % (tag, c, (r or '')[:150]))
    try:
        d = json.loads(r)
        return d.get('sandbox', {}).get('currentSessionId')
    except Exception:
        return None


def read_marker(tag):
    c, r = cmd(SID, 'python3', ['-c', "print(open('/vercel/sandbox/v226_m.txt').read())"], 25000)
    for line in (r or '').splitlines():
        if '"data"' in line:
            try:
                log('  read %s: %s' % (tag, json.loads(line).get('data')))
            except Exception:
                pass
    return r


if __name__ == '__main__':
    api('DELETE', '/v2/sandboxes/%s?teamId=%s&projectId=%s' % (NAME, TEAM, PROJ))
    SID = fresh_sandbox(NAME)
    log('sid=%s' % SID)
    time.sleep(4)

    run('MARKER_ONE_226')
    time.sleep(1)
    snap_a = snap('A')
    log('snap A=%s' % snap_a)
    time.sleep(3)

    # resume 恢复最新 (=A)
    SID = resume('afterA', None) or SID
    time.sleep(5)
    read_marker('afterA')  # 应 marker1

    run('MARKER_TWO_226')
    time.sleep(1)
    snap_b = snap('B')
    log('snap B=%s' % snap_b)
    time.sleep(3)

    # resume 指定 A
    SID = resume('specA', snap_a) or SID
    time.sleep(5)
    read_marker('specA')  # marker1 => 指定生效; marker2 => 忽略

    # 再 resume 最新 (=B)
    SID = resume('latest', None) or SID
    time.sleep(5)
    read_marker('latest')  # 应 marker2

    api('DELETE', '/v2/sandboxes/%s?teamId=%s&projectId=%s' % (NAME, TEAM, PROJ))
    log('DONE')

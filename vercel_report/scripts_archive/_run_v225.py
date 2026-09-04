# -*- coding: utf-8 -*-
"""v225: 快照数据面深挖 — 双快照恢复指定 snapshotId / 快照列表参数注入 / 下载端点 / fork 指定快照
流程: 建沙箱 -> 写 marker1 -> snapshot A -> 改 marker2 -> snapshot B ->
      测试恢复指定 A 是否生效 + 列表注入 + 下载 + fork 变体"""
import json, sys, time
sys.path.insert(0, r'D:\scan\skills\non-traditional-vuln-hunting')
sys.stdout.reconfigure(encoding='utf-8')
from vercel_driver import api, TEAM, PROJ, cmd

NAME = 'v225'


def log(s): print(s, flush=True)


def mk(marker):
    c, r = cmd(SID, 'bash', ['-c', 'echo %s > /vercel/sandbox/v225_m.txt' % marker], 20000)
    return c


if __name__ == '__main__':
    api('DELETE', '/v2/sandboxes/%s?teamId=%s&projectId=%s' % (NAME, TEAM, PROJ))
    c, r = api('POST', '/v4/sandboxes?teamId=%s' % TEAM, {'projectId': PROJ, 'name': NAME}, 60)
    d = json.loads(r)
    SID = d['sandbox']['currentSessionId']
    log('sid=%s' % SID)
    time.sleep(4)

    mk('MARKER_ONE_225')
    c, r = api('POST', '/v2/sandboxes/sessions/%s/snapshot?teamId=%s' % (SID, TEAM), {}, 90)
    snap_a = json.loads(r)['snapshot']['id']
    log('snap A=%s' % snap_a)
    time.sleep(2)
    mk('MARKER_TWO_225')
    time.sleep(1)
    c, r = api('POST', '/v2/sandboxes/sessions/%s/snapshot?teamId=%s' % (SID, TEAM), {}, 90)
    log('snap B raw -> %s | %s' % (c, (r or '')[:300]))
    try:
        snap_b = json.loads(r)['snapshot']['id']
    except Exception:
        # 重试一次 (可能是上一个大快照未释放)
        log('snap B retry...')
        time.sleep(5)
        c, r = api('POST', '/v2/sandboxes/sessions/%s/snapshot?teamId=%s' % (SID, TEAM), {}, 120)
        log('snap B retry -> %s | %s' % (c, (r or '')[:300]))
        try:
            snap_b = json.loads(r)['snapshot']['id']
        except Exception:
            log('snap B FAIL, use A for all tests')
            snap_b = snap_a
    log('snap B=%s' % snap_b)
    time.sleep(1)

    log('')
    log('===== 1) 恢复指定 snapshotId 变体 =====')
    for tag, m, p, b in [
        ('resume-q-snapA', 'GET', '/v2/sandboxes/%s?resume=true&snapshotId=%s' % (NAME, snap_a), None),
        ('restore-post', 'POST', '/v2/sandboxes/%s/restore' % NAME, {'snapshotId': snap_a}),
        ('snap-restore', 'POST', '/v2/sandboxes/snapshots/%s/restore' % snap_a, {}),
        ('snap-fork', 'POST', '/v2/sandboxes/snapshots/%s/fork' % snap_a, {'projectId': PROJ}),
        ('fork-snapid', 'POST', '/v2/sandboxes/%s/fork' % NAME, {'snapshotId': snap_a}),
    ]:
        c, r = api(m, p + ('?teamId=%s&projectId=%s' % (TEAM, PROJ) if '?' not in p else '&teamId=%s&projectId=%s' % (TEAM, PROJ)), b, 60)
        log('[%s] %-10s -> %s | %s' % (tag, m, c, (r[:250] if r else '').replace(chr(10), ' ')))

    log('')
    log('===== 2) 快照列表参数注入 =====')
    for q in ['?project=%s' % PROJ,
              '?project=',
              '?project=%s&teamId=%s' % (PROJ, TEAM),
              '?project=prj_zzzzzzzzzzzzzzzzzzzzzzzz',
              '?project=%s&limit=5' % PROJ]:
        c, r = api('GET', '/v2/sandboxes/snapshots' + q, None, 20)
        cnt = ''
        try:
            cnt = str(len(json.loads(r).get('snapshots', [])))
        except Exception:
            pass
        log('GET snapshots %-30s -> %s cnt=%s | %s' % (q, c, cnt, (r[:200] if r else '').replace(chr(10), ' ')))

    log('')
    log('===== 3) 快照下载/数据端点 =====')
    for p in ['/v2/sandboxes/snapshots/%s/download' % snap_a,
              '/v2/sandboxes/snapshots/%s/url' % snap_a,
              '/v2/sandboxes/snapshots/%s/file' % snap_a,
              '/v2/sandboxes/snapshots/%s/contents' % snap_a,
              '/v2/sandboxes/snapshots/%s' % snap_a]:
        c, r = api('GET', p + '?project=%s' % PROJ, None, 20)
        log('GET %-58s -> %s | %s' % (p, c, (r[:150] if r else '').replace(chr(10), ' ')))

    log('')
    log('===== 4) 快照删除 =====')
    c, r = api('DELETE', '/v2/sandboxes/snapshots/%s?project=%s' % (snap_a, PROJ), None, 20)
    log('DEL snapA -> %s | %s' % (c, (r[:200] if r else '').replace(chr(10), ' ')))

    api('DELETE', '/v2/sandboxes/%s?teamId=%s&projectId=%s' % (NAME, TEAM, PROJ))
    log('DONE')

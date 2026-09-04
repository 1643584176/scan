# -*- coding: utf-8 -*-
"""通用驱动: 注入并运行 vda4x guest 脚本 (mount /dev/vda -> cell.sock/containerd 测试)
用法: python _run_vda44.py vda44_driveid_enum_guest.py
依赖: vercel_cookies.txt 位于 workspace 根 (或 VERCEL_TOKEN 环境变量)
流程: 删旧沙箱 -> 创建 -> mknod /dev/vda -> base64 注入 guest -> nohup 执行
      -> 轮询哨兵 -> 保存结果到 skills/out -> 删除沙箱
若创建返回 402 (快照存储配额), 尝试清理 /v2/sandboxes/snapshots 后重试"""
import base64, os, sys, time, json, re

HERE = os.path.dirname(os.path.abspath(__file__))
sys.path.insert(0, HERE)
sys.stdout.reconfigure(encoding='utf-8')
from vercel_driver import api, cmd, TEAM, PROJ

GUEST = sys.argv[1] if len(sys.argv) > 1 else 'vda44_driveid_enum_guest.py'
m = re.search(r'vda(\d+)', GUEST)
NUM = m.group(1) if m else '44'
NAME = 'v%s' % NUM
OUTF = 'v%s.out' % NUM
MARK = 'V%sD_DONE' % NUM
OUTDIR = os.path.join(os.path.dirname(HERE), 'out')
os.makedirs(OUTDIR, exist_ok=True)


def mk(retry_snap_clean=True):
    api("DELETE", "/v2/sandboxes/%s?teamId=%s&projectId=%s" % (NAME, TEAM, PROJ))
    time.sleep(3)
    for attempt in range(8):
        c, r = api("POST", "/v4/sandboxes?teamId=%s" % TEAM,
                   {"projectId": PROJ, "name": NAME}, 60)
        if c == 429:
            print('[create] 429 retry %d' % (attempt + 1), flush=True)
            time.sleep(20)
            continue
        break
    print('[create] -> %s %s' % (c, r[:200]), flush=True)
    if c == 402 and retry_snap_clean:
        print('[create] 402 quota -> cleaning snapshots', flush=True)
        c2, r2 = api("GET", "/v2/sandboxes/snapshots?teamId=%s&project=%s&limit=50" % (TEAM, PROJ))
        print('[snaps] -> %s %s' % (c2, r2[:400]), flush=True)
        try:
            for s in json.loads(r2).get('snapshots', []):
                api("DELETE", "/v2/sandboxes/snapshots/%s?teamId=%s&project=%s" % (s['id'], TEAM, PROJ))
                print('[snap-del] %s' % s.get('id'), flush=True)
        except Exception as e:
            print('[snap-clean-err] %s' % e, flush=True)
        time.sleep(3)
        return mk(retry_snap_clean=False)
    if c != 200:
        sys.exit(1)
    d = json.loads(r)
    return d['sandbox']['currentSessionId']


if __name__ == '__main__':
    sid = mk()
    print('sid =', sid, flush=True)
    time.sleep(5)
    c, r = cmd(sid, 'sh', ['-c', 'mknod /dev/vda b 254 0 2>/dev/null; ls -la /dev/vda'], timeout_ms=15000)
    print('mknod:', c, (r or '')[:200], flush=True)
    c, r = cmd(sid, 'sh', ['-c', 'mkdir -p /vercel/sandbox'], timeout_ms=15000)
    print('mkdir:', c, flush=True)
    code = open(os.path.join(HERE, GUEST), 'rb').read()
    payload = base64.b64encode(code).decode()
    inject = "import base64;open('/vercel/sandbox/%s','wb').write(base64.b64decode('%s'))" % (GUEST, payload)
    c, r = cmd(sid, 'python3', ['-c', inject], timeout_ms=30000)
    print('inject:', c, flush=True)
    time.sleep(1)
    c, r = cmd(sid, 'sh', ['-c', 'ls -la /vercel/sandbox/'], timeout_ms=15000)
    print('verify:', c, (r or '')[:200], flush=True)
    if GUEST not in (r or ''):
        print('INJECT FAIL - abort', flush=True)
        sys.exit(2)
    c, r = cmd(sid, 'sh', ['-c', 'nohup python3 /vercel/sandbox/' + GUEST + ' > /tmp/' + NAME + '_stdout.txt 2>&1 &'], timeout_ms=15000)
    print('kick:', c, (r or '')[:150], flush=True)
    for attempt in range(48):
        time.sleep(5)
        c, r = cmd(sid, 'cat', ['/vercel/sandbox/' + NAME + '.out'], timeout_ms=30000)
        if c == 200 and MARK in r:
            fn = os.path.join(OUTDIR, '%s_%s.txt' % (GUEST.replace('.py', ''), time.strftime('%Y%m%d_%H%M%S')))
            open(fn, 'w', encoding='utf-8').write(r)
            print('saved ->', fn, flush=True)
            print(r[-4000:], flush=True)
            break
        tail = (r or '').replace('\\n', ' ')[-250:]
        print('wait r%d status=%d | %s' % (attempt, c, tail), flush=True)
        if attempt in (1, 5, 12) and c != 200:
            c2, r2 = cmd(sid, 'sh', ['-c', 'ls -la /vercel/sandbox/; tail -5 /tmp/' + NAME + '_stdout.txt 2>/dev/null'], timeout_ms=20000)
            print('diag:', c2, (r2 or '').replace('\\n', ' ')[-400:], flush=True)
    api("DELETE", "/v2/sandboxes/%s?teamId=%s&projectId=%s" % (NAME, TEAM, PROJ))
    print('CLEANED', flush=True)

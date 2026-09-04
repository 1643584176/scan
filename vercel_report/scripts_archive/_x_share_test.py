# -*- coding: utf-8 -*-
"""跨沙箱共享写测试 (v44t): /run/vercel/share 与 /run/cell 是否跨沙箱可见
A 沙箱写 marker -> B 沙箱读 (两个独立沙箱, 仅测试自有账号)
若可见 = 跨沙箱共享写原语 (新 host 写 / 跨租户面)"""
import base64, os, sys, time, json, random, string
sys.path.insert(0, r'F:\scan\skills\non-traditional-vuln-hunting')
sys.stdout.reconfigure(encoding='utf-8')
from vercel_driver import api, cmd, TEAM, PROJ

MARK = 'SHARE44_' + ''.join(random.choices(string.ascii_lowercase + string.digits, k=10))

def mk(name):
    api("DELETE", "/v2/sandboxes/%s?teamId=%s&projectId=%s" % (name, TEAM, PROJ))
    time.sleep(3)
    for attempt in range(8):
        c, r = api("POST", "/v4/sandboxes?teamId=%s" % TEAM,
                   {"projectId": PROJ, "name": name}, 60)
        if c == 429:
            print('[create %s] 429 retry %d' % (name, attempt + 1), flush=True)
            time.sleep(20)
            continue
        break
    print('[create %s] -> %s' % (name, c), flush=True)
    if c != 200:
        sys.exit(1)
    return json.loads(r)['sandbox']['currentSessionId']

if __name__ == '__main__':
    sida = mk('shareA44')
    sidb = mk('shareB44')
    time.sleep(4)
    # A: 写 marker 到 /run/vercel/share 和 /run/cell
    c, r = cmd(sida, 'sh', ['-c', 'echo %s > /run/vercel/share/.mark_%s 2>&1; echo %s > /run/cell/.mark_%s 2>&1; ls -la /run/vercel/share/ /run/cell/ 2>&1 | head -20' % (MARK, MARK, MARK, MARK)], timeout_ms=20000)
    print('A write:', c, (r or '').replace('\\n', ' ')[-400:], flush=True)
    # B: 读 marker (跨沙箱可见性)
    c, r = cmd(sidb, 'sh', ['-c', 'ls -la /run/vercel/share/ /run/cell/ 2>&1 | head -20; echo ===; cat /run/vercel/share/.mark_%s 2>&1; cat /run/cell/.mark_%s 2>&1' % (MARK, MARK)], timeout_ms=20000)
    print('B read:', c, (r or '').replace('\\n', ' ')[-500:], flush=True)
    # B: mountinfo 对照 (bind 源是否相同)
    c, r = cmd(sidb, 'sh', ['-c', 'grep -E "vercel/share|run/cell|/volumes" /proc/self/mountinfo'], timeout_ms=15000)
    print('B mountinfo:', c, (r or '').replace('\\n', ' ')[-400:], flush=True)
    c, r = cmd(sida, 'sh', ['-c', 'grep -E "vercel/share|run/cell|/volumes" /proc/self/mountinfo'], timeout_ms=15000)
    print('A mountinfo:', c, (r or '').replace('\\n', ' ')[-400:], flush=True)
    # 清理
    api("DELETE", "/v2/sandboxes/shareA44?teamId=%s&projectId=%s" % (TEAM, PROJ))
    api("DELETE", "/v2/sandboxes/shareB44?teamId=%s&projectId=%s" % (TEAM, PROJ))
    print('CLEANED, MARK=%s' % MARK, flush=True)

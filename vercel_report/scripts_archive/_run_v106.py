# -*- coding: utf-8 -*-
"""v98 驱动: 注入 exec_probe.sh + cell API drive 容器 Exec 侦察"""
import sys, os, time, json, base64
sys.path.insert(0, r'D:\scan\skills\non-traditional-vuln-hunting')
sys.stdout.reconfigure(encoding='utf-8')
from vercel_driver import api, TEAM, PROJ, fresh_sandbox, cmd

NAME = 'v106'
GUEST = r'D:\scan\skills\non-traditional-vuln-hunting\vda106_guest.py'
PAY = r'D:\scan\skills\non-traditional-vuln-hunting\vda106_probe_guest.py'

PROBE = r'''#!/bin/sh
{
echo ===ID===; id
echo ===HOSTNAME===; hostname
echo ===CWD===; pwd
echo ===ROOTLS===; ls -la /
echo ===PROC1===; tr '\0' ' ' < /proc/1/cmdline 2>&1; echo
echo ===SELF===; tr '\0' ' ' < /proc/self/cmdline 2>&1; echo
echo ===CGROUP===; cat /proc/self/cgroup 2>&1
echo ===MOUNT===; mount 2>&1 | head -40
echo ===PROCS===; ps -ef 2>&1 | head -40
echo ===RUN===; ls -la /run/ 2>&1 | head -20
echo ===CELL===; ls -la /run/cell/ 2>&1
echo ===VERCEL===; ls -la /run/vercel/ /run/vercel/share/ 2>&1
echo ===SANDBOX===; ls -la /vercel/sandbox/ 2>&1 | head -20
echo ===HOSTS===; cat /etc/hosts 2>&1
echo ===ENV===; env 2>&1 | head -30
echo ===PROC1_ENV===; tr '\0' '\n' < /proc/1/environ 2>&1 | head -20
echo ===DONE===
} > /run/vercel/share/exec_probe.out 2>&1; cp /run/vercel/share/exec_probe.out /vercel/sandbox/exec_probe.out 2>/dev/null
'''


def inject(sid, dst, content):
    b64 = base64.b64encode(content if isinstance(content, bytes) else content.encode()).decode()
    s = "import base64;open('%s','wb').write(base64.b64decode('%s'))" % (dst, b64)
    c, r = cmd(sid, 'python3', ['-c', s], 60000)
    print('[inject %s]' % dst, c)
    return c


def main():
    t0 = time.time()
    api('DELETE', '/v2/sandboxes/%s?teamId=%s&projectId=%s' % (NAME, TEAM, PROJ))
    sid = fresh_sandbox(NAME)
    print('[create ok] %.0fs' % (time.time() - t0))

    inject(sid, '/vercel/sandbox/exec_probe.sh', PROBE)
    inject(sid, '/vercel/sandbox/vda106_guest.py', open(GUEST, 'rb').read())
    inject(sid, '/vercel/sandbox/vda106_probe_guest.py', open(PAY, 'rb').read())
    
    c, r = cmd(sid, 'python3', ['/vercel/sandbox/vda106_guest.py'], 300000)
    print('[run guest]', c)
    print((r or '')[:30000])

    c, r = cmd(sid, 'sh', ['-c', 'tail -c 30000 /vercel/sandbox/v106m.out 2>&1'], 20000)
    print('[guest tail]', c)
    print((r or '')[:26000])

    c, r = cmd(sid, 'sh', ['-c', 'cat /vercel/sandbox/exec_probe.out 2>&1'], 20000)
    print('[probe out]', c)
    print((r or '')[:12000])

    c, r = cmd(sid, 'sh', ['-c', 'tail -c 90000 /vercel/sandbox/v106p3.out 2>&1'], 20000)
    print('[p3 file]', c)
    print((r or '')[:90000])

    api('DELETE', '/v2/sandboxes/%s?teamId=%s&projectId=%s' % (NAME, TEAM, PROJ))
    print('CLEANED total %.0fs' % (time.time() - t0))


if __name__ == '__main__':
    main()

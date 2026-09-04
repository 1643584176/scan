# -*- coding: utf-8 -*-
# 生成 v83 guest + 驱动 (基于 v82, 轮询改增量打印)
g = open(r'D:\scan\skills\non-traditional-vuln-hunting\vda82_guest.py', encoding='utf-8').read()

old_poll = """            if cur != seen:
                seen = cur
                log('--- COW v82c.out @%ds ---\\n%s' % (t_wait, cur[-4000:]))"""
new_poll = """            if cur != seen:
                new = cur[len(seen):] if cur.startswith(seen) else cur[-4000:]
                seen = cur
                log('--- COW v82c.out @%ds +%d ---\\n%s' % (t_wait, len(new), new[-3000:]))"""
assert old_poll in g, 'poll block not found'
g = g.replace(old_poll, new_poll)

g = g.replace('vda82', 'vda83').replace('v82', 'v83').replace('V82C_DONE', 'V83C_DONE')
open(r'D:\scan\skills\non-traditional-vuln-hunting\vda83_guest.py', 'w', encoding='utf-8').write(g)

d = open(r'D:\scan\_run_v82.py', encoding='utf-8').read()
d = d.replace('vda82', 'vda83').replace('v82', 'v83').replace('V82', 'V83')
open(r'D:\scan\_run_v83.py', 'w', encoding='utf-8').write(d)
print('done')

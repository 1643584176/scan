# -*- coding: utf-8 -*-
"""挖 JS 4: 模块 475210 的 C2 导出定义(N.C2 的实体)"""
import io

F = r'D:\scan\figma_report\_js\figma_app-main.js'
t = io.open(F, encoding='utf-8', errors='ignore').read()

m = t.find('475210(e,t,r)')
print('module 475210 at', m)
seg = t[m:m + 100000]
head_end = seg.find('});')
print('--- module head exports ---')
print(seg[:min(1200, head_end + 3)].replace('\n', ' '))
print()
k = seg.find('C2:()=>')
print('C2 export mapping at rel', k)
if k >= 0:
    print(seg[k:k + 150].replace('\n', ' '))
    # 提取目标变量名
    frag = seg[k + 6:k + 30]
    name = ''
    for ch in frag:
        if ch.isalnum() or ch in '_$':
            name += ch
        else:
            break
    print('target =', name)
    # 找定义
    import re
    for mm in re.finditer(r'[^A-Za-z0-9_$]' + re.escape(name) + r'\s*=', seg):
        s = mm.start()
        print('--- def @', s, ':', seg[s - 90:s + 380].replace('\n', ' '))
print('DONE4')

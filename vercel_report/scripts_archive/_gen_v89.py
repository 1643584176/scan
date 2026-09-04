# -*- coding: utf-8 -*-
# 生成 v89 guest + 驱动 (基于 v88), 删除 guest 的 celld 分析段
g = open(r'D:\scan\skills\non-traditional-vuln-hunting\vda88_guest.py', encoding='utf-8').read()
g = g.replace('vda88', 'vda89').replace('v88', 'v89').replace('V88C_DONE', 'V89C_DONE')
# 删除 celld 分析段 (guest main 末尾)
start = g.find('    # === celld proto 字段提取 ===')
end = g.find("    log('V66M_DONE')")
if start > 0 and end > start:
    g = g[:start] + g[end:]
open(r'D:\scan\skills\non-traditional-vuln-hunting\vda89_guest.py', 'w', encoding='utf-8').write(g)

d = open(r'D:\scan\_run_v88.py', encoding='utf-8').read()
d = d.replace('vda88', 'vda89').replace('v88', 'v89').replace('V88', 'V89')
open(r'D:\scan\_run_v89.py', 'w', encoding='utf-8').write(d)
print('done')

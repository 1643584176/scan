# -*- coding: utf-8 -*-
"""index-LpJ7SKi1.js: bat 的扩展链(class X extends bat / Object.assign / Le 混入)"""
import re, os

here = os.path.dirname(os.path.abspath(__file__))
p = os.path.join(here, '_js', 'prod_chunks', 'index-LpJ7SKi1.js')
src = open(p, encoding='utf-8', errors='replace').read()
out = []

out.append('class X extends bat: %s' % [m.group(0) for m in re.finditer(r'class\s+\w+\s+extends\s+bat', src)])
out.append('extends bat count: %d' % len(re.findall(r'extends\s+bat', src)))

# 搜另一个 client 类: openapi 生成类可能多个(class xxx extends yat 之外的)
for m in re.finditer(r'class\s+(\w+)\s+extends\s+yat', src):
    out.append('YAT-SUBCLASS: ' + m.group(1))

# Le 相关: Le= / new Le / Le.xxx= / Object.assign(Le
for m in re.finditer(r'Le\s*=', src):
    i = m.start()
    out.append('Le= @%d: %s' % (i, src[max(0, i - 120):i + 150].replace('\n', ' ')[:250]))
for m in re.finditer(r'Object\.assign\(\s*Le', src):
    i = m.start()
    out.append('OA-Le @%d: %s' % (i, src[i:i + 300].replace('\n', ' ')[:280]))

# bat 类定义结束位置: 找 "}const Kde" 或 "}" + 下一 token
i_bat = src.find('class bat extends yat')
i_kde = src.find('const Kde')
seg = src[i_bat:i_kde]
out.append('bat body len: %d' % len(seg))
# 方法名全部收集后分析前缀(找 lakebase 相关类的方法命名规律: 是否有其他 client 实例)
out.append('=== bat 内所有含 account/agentic/provision 的方法 ===')
for mm in re.finditer(r'([A-Za-z_$][\w$]*)=\(', seg):
    name = mm.group(1)
    if any(k in name.lower() for k in ['account', 'agent', 'provision', 'observ', 'workflow', 'ai']):
        out.append(name)

open(os.path.join(here, '_p77_out.txt'), 'w', encoding='utf-8').write('\n'.join(out))
print('done lines:', len(out), flush=True)

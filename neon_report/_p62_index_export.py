# -*- coding: utf-8 -*-
"""index-LpJ7SKi1.js: 找 ag 导出定义与 re-export 链
搜: getResolveRegions(so 方法) / export{ 语句含 ag / ag 作为对象 key
"""
import re, os

here = os.path.dirname(os.path.abspath(__file__))
p = os.path.join(here, '_js', 'prod_chunks', 'index-LpJ7SKi1.js')
src = open(p, encoding='utf-8', errors='replace').read()
out = []

for kw in ['getResolveRegions', 'listAutoscalingProjectBranchRoles', 'createDatabaseInstance',
           'getDatabaseInstanceDetails', 'deleteDatabaseInstance', 'updateDatabaseInstance',
           'listObservabilityConfigurations']:
    idxs = [m.start() for m in re.finditer(re.escape(kw), src)]
    out.append('KW %s -> %d' % (kw, len(idxs)))
    for i in idxs[:2]:
        seg = src[max(0, i - 200):i + 300].replace('\n', ' ')
        out.append('  ctx: ' + seg[:450])

# export 语句含 ag
for m in re.finditer(r'export\{[^}]{0,600}?\bag\b[^}]{0,100}\}', src):
    out.append('EXPORT-AG: ' + m.group(0)[:700])
for m in re.finditer(r'export\{[^}]{0,200}ag as[^}]{0,80}\}', src):
    out.append('EXPORT-AG-AS: ' + m.group(0)[:400])
# re-export: export{...}from
for m in re.finditer(r'export\{[^}]{0,300}\}from"[^"]+"', src[:50000]):
    s = m.group(0)
    if 'ag' in s:
        out.append('REEXPORT: ' + s[:400])

# 文件开头/结尾 1000 字符看结构
out.append('=== HEAD 800 ===')
out.append(src[:800])
out.append('=== TAIL 800 ===')
out.append(src[-800:])

open(os.path.join(here, '_p62_out.txt'), 'w', encoding='utf-8').write('\n'.join(out))
print('done lines:', len(out), flush=True)

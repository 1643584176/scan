# -*- coding: utf-8 -*-
"""index-LpJ7SKi1.js + prod_app.js: securityWorker 注入点 / setSecurityData 调用
+ extends yat 的 API 类列表(新功能面全部端点来源)
"""
import re, os

here = os.path.dirname(os.path.abspath(__file__))
out = []
for fn in ['prod_chunks/index-LpJ7SKi1.js', 'prod_app.js']:
    p = os.path.join(here, '_js', fn)
    src = open(p, encoding='utf-8', errors='replace').read()
    out.append('===== %s (len %d) =====' % (fn, len(src)))
    for kw in ['securityWorker', 'setSecurityData', 'extends yat', 'new yat', 'new bat']:
        idxs = [m.start() for m in re.finditer(re.escape(kw), src)]
        out.append('KW %s -> %d' % (kw, len(idxs)))
        for i in idxs[:4]:
            seg = src[max(0, i - 250):i + 350].replace('\n', ' ')
            out.append('  ctx: ' + seg[:550])
    # yat 子类类名收集(class X extends yat)
    for m in re.finditer(r'class\s+(\w+)\s+extends\s+yat', src):
        out.append('SUBCLASS: ' + m.group(1))
    # 实例化 export: new Xxx() 赋值导出变量
    for m in re.finditer(r'var\s+(\w+)\s*=\s*new\s+(\w+)\(\)', src):
        out.append('INST: %s = new %s()' % (m.group(1), m.group(2)))

open(os.path.join(here, '_p69_out.txt'), 'w', encoding='utf-8').write('\n'.join(out))
print('done lines:', len(out), flush=True)

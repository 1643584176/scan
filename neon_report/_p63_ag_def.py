# -*- coding: utf-8 -*-
"""index-LpJ7SKi1.js: 定位 axios/instance 创建与 API client 方法定义
方法名被 minify -> 搜 instance 属性定义/axios.create/baseURL
"""
import re, os

here = os.path.dirname(os.path.abspath(__file__))
p = os.path.join(here, '_js', 'prod_chunks', 'index-LpJ7SKi1.js')
src = open(p, encoding='utf-8', errors='replace').read()
out = []

# 1. 找 ag 定义赋值(export 变量): var ag= / const ag= / ag={ / ag= 独立
for m in re.finditer(r'(?:var|const|let)\s+ag\s*=', src):
    i = m.start()
    out.append('DEF ag @%d: %s' % (i, src[i:i + 500].replace('\n', ' ')[:480]))
# 2. instance 定义: .instance= 或 instance: 在对象里
for m in re.finditer(r'\.instance\s*=', src):
    i = m.start()
    out.append('INST= @%d: %s' % (i, src[max(0, i - 200):i + 300].replace('\n', ' ')[:480]))
# 3. axios.create / create({ 带 baseURL
for m in re.finditer(r'(?:axios|e|o|t)?\.?create\(\{[^}]{0,300}baseURL[^}]{0,200}\}', src):
    out.append('CREATE: ' + m.group(0)[:400])
# 4. 导出对象里 ag 对应的 key(export 语句)
m = re.search(r'export\{([^}]*)\}$', src)
if m:
    seg = m.group(1)
    out.append('=== export tail len %d ===' % len(seg))
    # 找 ag 在 export 中的位置
    parts = seg.split(',')
    for i, pt in enumerate(parts):
        if re.search(r'\bag\b', pt):
            out.append('export item: %s' % pt.strip()[:80])
            # 显示前后 5 个
            for j in range(max(0, i - 3), min(len(parts), i + 4)):
                out.append('   [%d] %s' % (j, parts[j].strip()[:60]))

open(os.path.join(here, '_p63_out.txt'), 'w', encoding='utf-8').write('\n'.join(out))
print('done lines:', len(out), flush=True)

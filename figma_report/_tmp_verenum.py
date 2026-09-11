# -*- coding: utf-8 -*-
"""清点 versions/{fk} 这条 SQL 的所有测试脚本 + 参数面"""
import os, io, re

DIR = r'D:/scan/figma_report'
out = []

for fn in sorted(os.listdir(DIR)):
    if not fn.endswith('.py') or not fn.startswith('_figma_r'):
        continue
    txt = io.open(os.path.join(DIR, fn), encoding='utf-8', errors='ignore').read()
    if '/api/versions' not in txt:
        continue
    # 找 URL 与参数字典
    urls = set(re.findall(r'/api/versions[^\s\'"]*', txt))
    params = set(re.findall(r"'((?:column|before|secondary_column|secondary_before|secondary_after|sort\w*|order\w*|cursor|page_size))'", txt))
    out.append((fn, sorted(urls), sorted(params)))

print('== scripts hitting /api/versions ==')
for fn, urls, params in out:
    print('%-38s %s' % (fn, ' '.join(urls)[:90]))
    if params:
        print('%-38s   params: %s' % ('', ','.join(params)))

print()
print('== 各脚本首行 docstring ==')
for fn, urls, params in out:
    txt = io.open(os.path.join(DIR, fn), encoding='utf-8', errors='ignore').read()
    m = re.search(r'"""(.*?)"""', txt, re.S)
    head = (m.group(1).strip().split('\n')[0] if m else '')[:100]
    print('%-38s %s' % (fn, head))

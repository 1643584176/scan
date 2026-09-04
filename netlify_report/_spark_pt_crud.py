# -*- coding: utf-8 -*-
"""定位 prompt-templates 写操作函数定义(92321 模块内 fetch 调用)"""
import re

data = open(r'D:\scan\netlify_report\_js\net_app.js', encoding='utf-8', errors='ignore').read()

# 找 f="/spark-proxy/api/prompt-templates" 附近 5000 字符内的 fetch 调用
i = data.find('"/spark-proxy/api/prompt-templates"')
seg = data[i:i + 9000]
# 打印所有 fetch( 附近 250 字符,去重
hits = [m.start() for m in re.finditer(r'fetch\(', seg)]
seen = set()
for j in hits[:25]:
    s = seg[max(0, j - 150):j + 350]
    key = s[100:250]
    if key in seen:
        continue
    seen.add(key)
    print('...%s...' % s.replace('\n', ' '))
    print('---')

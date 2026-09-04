# -*- coding: utf-8 -*-
"""从 HAR 分析输出提取 A 的所有文件 key"""
import re

for f in ['D:/scan/figma_report/_figma_har_analysis.txt',
          'D:/scan/figma_report/_lg_enum3.txt']:
    try:
        t = open(f, 'r', encoding='utf-8', errors='ignore').read()
    except Exception as e:
        print(f, 'ERR', e); continue
    keys = set(re.findall(r'[A-Za-z0-9_-]{22}', t))
    # 过滤像文件 key 的(22 字符混合大小写)
    fk = [k for k in keys if re.match(r'^[A-Za-z][A-Za-z0-9_-]{21}$', k)]
    print(f, ':', fk[:40])

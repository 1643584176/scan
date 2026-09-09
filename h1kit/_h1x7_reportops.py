# -*- coding: utf-8 -*-
"""h1x7: Report 相关 operation 名筛选 + 关键 query 调用处"""
import sys, io, re
sys.stdout = io.TextIOWrapper(sys.stdout.buffer, encoding='utf-8', errors='replace')

t_app = open(r'D:\scan\h1kit\_h1x4_app.js', encoding='utf-8', errors='ignore').read()

# operation 名清单(带上下文:query 定义处)
ops = {}
for m in re.finditer(r'\b(query|mutation)\s+([A-Za-z_][A-Za-z0-9_]*)', t_app):
    ops.setdefault(m.group(2), m.group(1))

report_ops = {k: v for k, v in ops.items() if 'eport' in k}
print('===== Report 相关 operation', len(report_ops), '=====')
for k, v in sorted(report_ops.items()):
    print(f'  [{v}] {k}')

# 找 ReportPage/ReportQuery 类似定义位置, 提取文档前后文本找变量
for target in ['ReportPageQuery', 'ReportQuery', 'ActivityPreviewReportQuery', 'ReportFragment', 'reportPage']:
    for m in list(re.finditer(re.escape(target), t_app))[:3]:
        i = m.start()
        seg = t_app[max(0, i-200):i+600]
        if 'kind:`Field`' in seg or 'query' in seg[:200].lower() or 'SelectionSet' in seg:
            print(f'===== {target} ctx =====')
            print(seg[:800].replace('\n', ' ')[:800])
            print()

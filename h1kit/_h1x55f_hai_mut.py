# -*- coding: utf-8 -*-
"""h1x55f: 提取 ExecuteHai* / HaiReport / ReportSummary 类 mutation 文档串"""
import io, sys, re
sys.stdout = io.TextIOWrapper(sys.stdout.buffer, encoding='utf-8', errors='replace')
data = open(r'D:\scan\h1kit\_h1x4_app.js', encoding='utf-8', errors='replace').read()
# 文档字符串里的 mutation 定义(带换行格式的 GraphQL)
for m in re.finditer(r'(mutation\s+(?:ExecuteHai|HaiReport|.*ReportSummary|.*ReportSimilarity|.*ReportStatistics|.*ReportAssessment|.*ReportFeature)[A-Za-z0-9_]*\s*\([^)]{0,800}?\)\s*\{[^}]{0,1200}?\})', data):
    s = m.group(1)
    print('========== @%d' % m.start())
    print(s[:1600])
    print()
# 兜底: AST 文档(ExecuteHaiReportSummary 等)
for kw in ['ExecuteHaiReportSummary', 'ExecuteHaiReportSimilarity', 'ExecuteHaiReportStatistics', 'ExecuteHaiReportAssessment', 'ExecuteHaiReportCompare', 'HaiReportQuery']:
    idx = 0
    n = 0
    while n < 4:
        i = data.find(kw, idx)
        if i < 0:
            break
        ctx = data[max(0, i - 200):i + 900]
        print('### CTX[%s] @%d:' % (kw, i))
        print(ctx.replace('\n', ' ')[:1100])
        print()
        idx = i + len(kw)
        n += 1

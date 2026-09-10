# -*- coding: utf-8 -*-
"""h1x55g: 找 executeHai* 字段名 + 其 mutation 定义"""
import io, sys, re
sys.stdout = io.TextIOWrapper(sys.stdout.buffer, encoding='utf-8', errors='replace')
data = open(r'D:\scan\h1kit\_h1x4_app.js', encoding='utf-8', errors='replace').read()
fields = ['executeHaiReportSummary', 'executeHaiReportStatistics', 'executeHaiReportAssessment', 'executeHaiReportCompare',
          'executeHaiReportSimilaritySearch', 'executeHaiReportSimilarityByEmbeddingSearch', 'executeHaiReportFeatureQuerySearch',
          'executeHaiReportComparisonTable', 'executeHaiRemediationAdvice', 'executeHaiBountyAmountSuggestion',
          'executeHaiInsightAgentExtractor', 'executeHaiMermaid', 'executeHaiBountyTableLookup']
for kw in fields:
    idx = 0
    n = 0
    while n < 6:
        i = data.find(kw, idx)
        if i < 0:
            break
        ctx = data[max(0, i - 400):i + 700]
        print('### [%s] @%d:' % (kw, i))
        print(ctx.replace('\n', ' ')[:1050])
        print()
        idx = i + len(kw)
        n += 1

# -*- coding: utf-8 -*-
"""h1x20: 提取 BetterReportDuplicates 完整 query(含返回字段)+ CompleteHacktivityReportIndex 字段"""
import re, sys, io
sys.stdout = io.TextIOWrapper(sys.stdout.buffer, encoding='utf-8', errors='replace')

t = open(r'D:\scan\h1kit\_h1x4_app.js', encoding='utf-8', errors='ignore').read()

for name in ['BetterReportDuplicates', 'HacktivitySearchQuery', 'BetterReportDuplicatesExactText']:
    # 字符串形式含完整 query(可能多个字符串片段拼 fragment,这里直接抓首次出现点前后)
    i = t.find('query ' + name)
    if i == -1:
        print(f'{name}: not found'); continue
    seg = t[max(0, i-300):i+6000]
    m = re.search(r'"(.*?query ' + name + r'.*?)"', seg, re.S)
    if m:
        s = m.group(1).replace('\\n', '\n')
        print(f'===== {name} (len {len(s)}) =====\n{s}\n')
    else:
        # AST 形式:找 op 对象的 selections 转字符串
        j = t.find('{kind:`OperationDefinition`', i-4000, i+100)
        if j != -1:
            jj = t.find('}', i, i+30000)
            print(f'===== {name} AST raw =====\n{t[j:jj+500]}\n')
        else:
            print(f'===== {name}: no string/AST near {i} =====\n')

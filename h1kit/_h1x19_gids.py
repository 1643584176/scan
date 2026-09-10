# -*- coding: utf-8 -*-
"""h1x19: 计算 report 全局 id + 提取 report(id:)/node(id:)/search 具体 query 形状"""
import re, sys, io, base64
sys.stdout = io.TextIOWrapper(sys.stdout.buffer, encoding='utf-8', errors='replace')

for rid in ['3732660', '3992341', '242816', '2487889']:
    g = base64.b64encode(f'gid://hackerone/Report/{rid}'.encode()).decode()
    print(f'Report {rid}: {g}')

t = open(r'D:\scan\h1kit\_h1x4_app.js', encoding='utf-8', errors='ignore').read()

# 找字符串 query:report(id: 使用示例 与 search 使用示例
for name in ['BetterReportDuplicates', 'HacktivitySearchQuery', 'DupeWindowReportsQuery', 'GetReportTitleQuery', 'ClaimableRetestForReport', 'ReporterCardQuery']:
    i = t.find('query ' + name)
    if i == -1:
        i = t.find(name)
    if i == -1:
        continue
    # 找字符串形式:往前往后找 " 边界
    seg = t[max(0, i-200):i+2500]
    # 尝试提取含 query name 的字符串字面量
    m = re.search(r'"(.*?query ' + name + r'.*?)"', seg, re.S)
    if m:
        s = m.group(1).replace('\\n', '\n')[:1500]
        print(f'\n===== {name} =====\n{s}')
    else:
        print(f'\n===== {name} (string not found near {i}) =====')

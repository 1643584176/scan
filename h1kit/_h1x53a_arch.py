# -*- coding: utf-8 -*-
"""h1x53a: bundle 考古 ①ReportDraft ②resource(url) 前端调用形态 ③HaiReportData/ExtractedReportData"""
import re, sys, io
sys.stdout = io.TextIOWrapper(sys.stdout.buffer, encoding='utf-8', errors='replace')
t = open(r'D:\scan\h1kit\_h1x4_app.js', encoding='utf-8', errors='ignore').read()

print('===== 1. ReportDraft =====')
hits = list(re.finditer(r'ReportDraft', t))
print('hits:', len(hits))
for m in hits[:6]:
    j = m.start()
    print('--- @', j)
    print(t[max(0, j-300):j+400].replace('\n', ' ')[:700])
    print()

print('===== 2. resource( url 调用 =====')
hits = list(re.finditer(r'resource\s*\(\s*url|query\s*Resource|resource\(url', t))
print('hits:', len(hits))
for m in hits[:6]:
    j = m.start()
    print('--- @', j)
    print(t[max(0, j-400):j+500].replace('\n', ' ')[:900])
    print()

print('===== 3. HaiReportData / extracted_report_data =====')
for pat in ['HaiReportData', 'extracted_report_data', 'hai_report_data', 'report_generated_content']:
    hits = list(re.finditer(pat, t))
    print(f'### {pat}: {len(hits)} hits')
    for m in hits[:3]:
        j = m.start()
        print('--- @', j)
        print(t[max(0, j-250):j+350].replace('\n', ' ')[:600])
        print()

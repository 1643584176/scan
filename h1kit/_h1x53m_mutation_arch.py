# -*- coding: utf-8 -*-
"""h1x53m: bundle 考古 resumeOrCreateReportIntent mutation 输入形态 + ReportIntentV2Query 参数"""
import re, sys, io
sys.stdout = io.TextIOWrapper(sys.stdout.buffer, encoding='utf-8', errors='replace')
t = open(r'D:\scan\h1kit\_h1x4_app.js', encoding='utf-8', errors='ignore').read()

for pat in ['resumeOrCreateReportIntent', 'ReportIntentV2Query', 'ReportAssistantConversation', 'Conversations::']:
    hits = list(re.finditer(re.escape(pat), t))
    print(f'### {pat}: {len(hits)} hits')
    for m in hits[:6]:
        j = m.start()
        print('--- @', j)
        print(t[max(0, j-350):j+450].replace('\n', ' ')[:800])
        print()

# -*- coding: utf-8 -*-
import io, sys, re
sys.stdout = io.TextIOWrapper(sys.stdout.buffer, encoding='utf-8', errors='replace')
data = open(r'D:\scan\h1kit\_h1x4_app.js', encoding='utf-8', errors='replace').read()
# 找 reportPdfExportTypes 常量定义
for m in re.finditer(r'reportPdfExportTypes[^;]{0,400}', data):
    print('===', m.start())
    print(m.group(0)[:400].replace('\n', ' '))
    print()
# 找 'reporter' 附近的 pdf 类型语境
for kw in ['pdf_type', 'pdfType', 'PDFExportType', 'pdfExportType']:
    idx = 0; n = 0
    while n < 5:
        i = data.find(kw, idx)
        if i < 0: break
        print('### [%s] @%d' % (kw, i))
        print(data[max(0, i-250):i+250].replace('\n', ' ')[:500])
        print()
        idx = i + len(kw); n += 1

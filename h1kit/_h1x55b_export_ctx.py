# -*- coding: utf-8 -*-
import io, sys, re
sys.stdout = io.TextIOWrapper(sys.stdout.buffer, encoding='utf-8', errors='replace')
data = open(r'D:\scan\h1kit\_h1x4_app.js', encoding='utf-8', errors='replace').read()
for kw in ['export/raw', 'export/zip', 'exportZippedReport', 'export_raw', 'exported_report', 'downloadExport', 'ExportReport', 'report_export', 'exportReport']:
    idx = 0; n = 0
    while n < 8:
        i = data.find(kw, idx)
        if i < 0: break
        ctx = data[max(0, i - 500):i + 500]
        print('=== [%s] @%d ===' % (kw, i))
        print(ctx.replace('\n', ' '))
        print()
        idx = i + len(kw); n += 1

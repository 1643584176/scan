# -*- coding: utf-8 -*-
import io, sys, re
sys.stdout = io.TextIOWrapper(sys.stdout.buffer, encoding='utf-8', errors='replace')
data = open(r'D:\scan\h1kit\_h1x4_app.js', encoding='utf-8', errors='replace').read()
# 找 constants 里 reportPdfExportTypes 定义:形如 reportPdfExportTypes:{...} 或 xxx={reporter:...}
for m in re.finditer(r'reportPdfExportTypes\s*[:=]\s*\{[^}]{0,300}\}', data):
    print('=== @%d' % m.start())
    print(m.group(0)[:350])
    print()
# 兜底:找 `reporter:` 与 `full:` 相邻的常量对象
for m in re.finditer(r'\{[^{}]{0,200}reporter:[^{}]{0,200}\}', data):
    s = m.group(0)
    if 'full' in s or 'triage' in s or 'pdf' in s.lower():
        print('CTX @%d:' % m.start(), s[:300])
        print()

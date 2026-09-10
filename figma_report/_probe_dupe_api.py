# -*- coding: utf-8 -*-
"""考古: duplicate 到 drafts 的后端端点 (duplicateFile 实现 / 菜单 payload)"""
import sys, io, re
sys.stdout = io.TextIOWrapper(sys.stdout.buffer, encoding='utf-8', errors='replace')

data = open(r'D:\scan\figma_report\_js\figma_app-main.js', encoding='utf-8', errors='replace').read()

# 1. duplicateFile 相关端点/函数定义
for kw in ['duplicateFile', 'duplicate_file', 'duplicateToDrafts', 'duplicate-to-drafts', 'duplicate_file_to',
           'createFileFromVersion', 'copy_file', 'copyFile', 'duplicate:']:
    ms = list(re.finditer(re.escape(kw), data))
    print(f'===== [{kw}] x{len(ms)} =====')
    for m in ms[:4]:
        s = max(0, m.start() - 200)
        e = min(len(data), m.end() + 260)
        print(f'@{m.start()}: {data[s:e].replace(chr(10)," ")[:480]}')
        print()
print('ALL DONE')

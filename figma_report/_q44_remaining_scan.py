# -*- coding: utf-8 -*-
import sys, io
sys.stdout = io.TextIOWrapper(sys.stdout.buffer, encoding='utf-8', errors='replace')

files = ['Figma-SQL注入总账-2026-09-10.md',
         'Figma-SQL注入-r212-213-盲区深打-结论-2026-09-11.md',
         'Figma-SQL注入-r214-218-极限深挖-结论-2026-09-11.md']
kws = ['候选', '剩余', '未打', '未测', '剩余方向', 'hub_files', 'code_connect', 'workshop', 'template']
for f in files:
    print('=' * 20, f)
    txt = open(f, encoding='utf-8', errors='replace').read()
    for i, line in enumerate(txt.splitlines(), 1):
        if any(k in line for k in kws):
            print(i, '|', line[:220])

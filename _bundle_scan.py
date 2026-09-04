# -*- coding: utf-8 -*-
import re, glob, os

targets = ['ai_chat/threads', 'tagged_file', 'libraries_by_library_keys', 'api/files/batch', 'api/files/create', 'multipart']
for f in glob.glob(r'D:\scan\figma_report\_js\*.min.js'):
    try:
        d = open(f, encoding='utf-8', errors='ignore').read()
    except Exception:
        continue
    for t in targets:
        if t in d:
            i = d.find(t)
            print(os.path.basename(f), '|', t, '->', d[max(0, i - 120): i + 200].replace('\n', ' ')[:320])
            print()

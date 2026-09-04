# -*- coding: utf-8 -*-
import re, glob, os
for f in glob.glob(r'D:\scan\figma_report\_js\*.min.js'):
    try:
        d = open(f, encoding='utf-8', errors='ignore').read()
    except Exception:
        continue
    for m in re.finditer(r'.{60}getTaggedUserFiles.{200}', d):
        print(os.path.basename(f), m.group(0).replace('\n', ' ')[:260])
        print('---')

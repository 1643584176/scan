# -*- coding: utf-8 -*-
import re, glob, os
# 找 FormData / multipart 上传点
for f in glob.glob(r'D:\scan\figma_report\_js\*.min.js'):
    try:
        d = open(f, encoding='utf-8', errors='ignore').read()
    except Exception:
        continue
    for m in re.finditer(r'FormData\(\)|multipart/form-data|FormData;', d):
        i = m.start()
        seg = d[max(0, i - 100): i + 150].replace('\n', ' ')
        if 'api/' in seg or 'upload' in seg.lower() or 'avatar' in seg.lower() or 'import' in seg.lower():
            print(os.path.basename(f), '->', seg[:280])
            print()

# -*- coding: utf-8 -*-
import re, glob, os
# 找文件属性更新:rename/update + api/files
for f in glob.glob(r'D:\scan\figma_report\_js\*.min.js'):
    try:
        d = open(f, encoding='utf-8', errors='ignore').read()
    except Exception:
        continue
    for kw in ['renameFile', 'updateFileProperties', 'setFileLinkAccess', 'FileProperties', 'updateFile(']:
        if kw in d:
            i = d.find(kw)
            print(os.path.basename(f), kw)
            print('  ', d[max(0, i - 150): i + 250].replace('\n', ' ')[:400])
            print()

# -*- coding: utf-8 -*-
"""找下载 _api_doc.md 的脚本与 URL"""
import os, re, glob

here = os.path.dirname(os.path.abspath(__file__))
for fn in glob.glob(os.path.join(here, '*.py')):
    try:
        s = open(fn, encoding='utf-8', errors='replace').read()
    except Exception:
        continue
    if 'api_doc' in s or ('openapi' in s and 'http' in s):
        print('###', os.path.basename(fn), flush=True)
        for m in re.finditer(r'[^ \n]{0,120}(?:api_doc|openapi|swagger|api-docs)[^ \n]{0,160}', s):
            seg = m.group(0)
            if 'http' in seg or 'json' in seg or 'write' in seg or 'open(' in seg:
                print('   ', seg[:240], flush=True)

# -*- coding: utf-8 -*-
"""检查 zip 内所有文件的中文残留"""
import zipfile, re

p = r'F:\scan\vercel_report\fw_vpc\fw_vpc_poc.zip'
z = zipfile.ZipFile(p)
for n in z.namelist():
    if not n.endswith(('.py', '.txt', '.md', '.README')):
        continue
    try:
        txt = z.read(n).decode('utf-8')
    except Exception:
        continue
    cjk = re.findall(r'[\u4e00-\u9fff]+', txt)
    if cjk:
        print('CJK in', n, ':', len(cjk))
        for m in cjk[:8]:
            print('   ', m)
print('CHECK DONE')

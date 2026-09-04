# -*- coding: utf-8 -*-
"""提取 e150 会话中 cell.sock/DrivesService/CreateSnapshot 的精确请求格式"""
import sys, re
sys.stdout.reconfigure(encoding='utf-8')

for path, name in [(r'F:\scan\skills\non-traditional-vuln-hunting\e1507845_text.txt', 'e150'),
                   (r'F:\scan\skills\non-traditional-vuln-hunting\494b74ea_text.txt', '494'),
                   (r'F:\scan\skills\non-traditional-vuln-hunting\a669521c_text.txt', 'a669')]:
    data = open(path, 'rb').read()
    txt = data.decode('gbk', errors='replace')
    lines = txt.splitlines()
    print('=' * 30, name, 'lines:', len(lines))
    for i, l in enumerate(lines):
        if re.search(r'cell\.sock|DrivesService|CreateSnapshot|drive_id|base_url|baseUrl', l, re.I):
            print('%4d: %s' % (i, l[:400]))

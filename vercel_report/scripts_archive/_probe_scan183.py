# -*- coding: utf-8 -*-
import re
data = open(r'D:\scan\skills\non-traditional-vuln-hunting\vda183_probe_guest.py',
            encoding='utf-8', errors='replace').read()
for i, line in enumerate(data.splitlines(), 1):
    s = line.strip()
    if (s.startswith('# ====') or s.startswith('log') or '26661' in s or 'tcp6' in s
            or 'listen' in s.lower() or 'netstat' in s or 'proc/net' in s
            or 'ss -' in s or 'LISTEN' in s):
        print(i, s[:140])

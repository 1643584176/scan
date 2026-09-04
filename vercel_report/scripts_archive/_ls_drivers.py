# -*- coding: utf-8 -*-
import os
d = r'D:/scan/skills/non-traditional-vuln-hunting'
for f in sorted(os.listdir(d)):
    if ('driver' in f.lower()) or ('drive' in f.lower()):
        print(f)

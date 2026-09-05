# -*- coding: utf-8 -*-
import re
f = r"F:\scan\neon_report\Neon-Auth与DataAPI技术面-20260904.md"
t = open(f, encoding="utf-8", errors="replace").read()
i = t.find("7.2")
if i >= 0:
    print(t[i:i + 1400])

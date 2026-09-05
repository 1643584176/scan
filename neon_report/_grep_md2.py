# -*- coding: utf-8 -*-
import re, io, sys
sys.stdout = io.TextIOWrapper(sys.stdout.buffer, encoding="utf-8", errors="replace")

f = r"F:\scan\neon_report\Neon-Auth与DataAPI技术面-20260904.md"
t = open(f, encoding="utf-8", errors="replace").read()
# print table of contents-ish: lines containing headers or key states
for i, line in enumerate(t.splitlines()):
    s = line.strip()
    if not s:
        continue
    if re.match(r"^#{1,4} ", s) or "闭合" in s or "结论" in s or "发现" in s or "候选" in s or "残留" in s:
        print("%4d %s" % (i + 1, s[:160]))

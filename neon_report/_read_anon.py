# -*- coding: utf-8 -*-
import io, sys, re
sys.stdout = io.TextIOWrapper(sys.stdout.buffer, encoding="utf-8", errors="replace")

f = r"F:\scan\neon_report\Neon-Anonymizer匿优化Beta面-20260904.md"
t = open(f, encoding="utf-8", errors="replace").read()
lines = t.splitlines()
for i, line in enumerate(lines):
    s = line.strip()
    if not s:
        continue
    print("%4d %s" % (i + 1, s[:200]))

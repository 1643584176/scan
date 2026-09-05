# -*- coding: utf-8 -*-
import io, sys
sys.stdout = io.TextIOWrapper(sys.stdout.buffer, encoding="utf-8", errors="replace")

f = r"F:\scan\neon_report\Neon-Auth与DataAPI技术面-20260904.md"
t = open(f, encoding="utf-8", errors="replace").read()
lines = t.splitlines()
start, end = 67, 107
for i in range(start - 1, min(end, len(lines))):
    print("%4d %s" % (i + 1, lines[i]))

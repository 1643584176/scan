# -*- coding: utf-8 -*-
import io, sys, re
sys.stdout = io.TextIOWrapper(sys.stdout.buffer, encoding="utf-8", errors="replace")


def re_match(s):
    return bool(re.match(r"^\|?\s*\d+\s*\|", s)) or s.startswith("#") or "版本" in s


f = r"F:\scan\neon_report\Neon-数据库机制面组合扫描-20260904.md"
t = open(f, encoding="utf-8", errors="replace").read()
for i, line in enumerate(t.splitlines()):
    s = line.strip()
    if not s:
        continue
    if re_match(s):
        print("%4d %s" % (i + 1, s[:170]))

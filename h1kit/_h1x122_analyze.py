# -*- coding: utf-8 -*-
"""分析审计输出:sink 分类统计 + URL 清单(2026-09-09)"""
import io, sys, re, collections

sys.stdout = io.TextIOWrapper(sys.stdout.buffer, encoding="utf-8", errors="replace")

text = open(r"D:\scan\h1kit\_h1x121_src_audit2.txt", encoding="utf-8").read()
urls_part = text.split("===== ALL ABSOLUTE URLS =====")[1]

print("===== ALL ABSOLUTE URLS =====")
for line in urls_part.strip().splitlines():
    print(line)

sec = text.split("===== SINK/LOC/MSG contexts =====")[1].split("===== ALL ABSOLUTE URLS =====")[0]
blocks = re.findall(r"\[(SINK|LOC|MSG|SRCDOC)\] (\S+)\n  (.*?)(?=\n\[|\Z)", sec, re.S)
print("\n===== counts =====")
print(collections.Counter(b[0] for b in blocks))
print("\n===== per-file sink density =====")
c = collections.Counter(b[1] for b in blocks)
for fn, n in c.most_common(40):
    print(f"{n:4d} {fn}")

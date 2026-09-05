# -*- coding: utf-8 -*-
"""List global experience files + find summary/state docs for neon/vercel"""
import os

for base, label in [(r"F:\scan\经验\全局经验", "经验/全局经验"),
                    (r"F:\scan\neon_report", "neon_report (md only)"),
                    (r"F:\scan", "workspace root summary-like")]:
    print("=" * 50, label)
    for f in sorted(os.listdir(base)):
        full = os.path.join(base, f)
        if not os.path.isfile(full):
            continue
        low = f.lower()
        if "经验学习" in f or "总结" in f or "summary" in low or "复盘" in f or "索引" in f:
            print("  %8d  %s" % (os.path.getsize(full), f))

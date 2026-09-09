# -*- coding: utf-8 -*-
"""读危险扫描完整输出——vendor 部分 + 凭据类(2026-09-09)"""
import re

with open(r"D:\scan\h1kit\_danger_scan_full.txt", "r", encoding="utf-8", errors="replace") as f:
    txt = f.read()

# 凭据模式(在原始 bundle 上再扫)
for fn in [r"D:\scan\h1kit\_h1x4_app.js", r"D:\scan\h1kit\_h1x4_vendor.js", r"D:\scan\h1kit\_h1x3_constants.js"]:
    with open(fn, "r", encoding="utf-8", errors="replace") as f:
        data = f.read()
    for pat, name in [(r"(sk|pk|rk)_(live|test)_[A-Za-z0-9]{16,}", "stripe"),
                      (r"AKIA[0-9A-Z]{16}", "aws"),
                      (r"gh[pousr]_[A-Za-z0-9]{20,}", "github"),
                      (r"-----BEGIN [A-Z ]*PRIVATE KEY-----", "pkey"),
                      (r"AIza[0-9A-Za-z\-_]{30,}", "gcp"),
                      (r"ya29\.[0-9A-Za-z\-_]{30,}", "g_oauth"),
                      (r"xox[baprs]-[0-9A-Za-z\-]{10,}", "slack"),
                      (r"eyJ[a-zA-Z0-9\-_]{20,}\.[a-zA-Z0-9\-_]{20,}\.[a-zA-Z0-9\-_]{20,}", "jwt")]:
        hits = set(m.group(0)[:60] for m in re.finditer(pat, data))
        if hits:
            print(f"{fn.split(chr(92))[-1]} {name}: {list(hits)[:3]}")

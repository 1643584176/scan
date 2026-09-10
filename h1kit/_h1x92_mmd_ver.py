# -*- coding: utf-8 -*-
"""找 mermaid 版本(2026-09-09)"""
import re

for fn in [r"D:\scan\h1kit\_h1x4_vendor.js", r"D:\scan\h1kit\_h1x4_app.js"]:
    with open(fn, "r", encoding="utf-8", errors="replace") as f:
        data = f.read()
    print("=====", fn)
    # version 字符串
    for pat in [r"mermaid[^\"']{0,60}version[^\"']{0,30}", r"\"version\"\s*:\s*\"(\d+\.\d+\.\d+)\"",
                r"version\s*=\s*\"(\d+\.\d+\.\d+)\"", r"@mermaid-js[^\"']{0,60}",
                r"mermaid@\d+\.\d+\.\d+"]:
        hits = set()
        for m in re.finditer(pat, data, re.I):
            hits.add(m.group(0)[:120])
        if hits:
            print(f"  [{pat[:30]}...]")
            for h in list(hits)[:8]:
                print("   ", h)

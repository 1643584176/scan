# -*- coding: utf-8 -*-
"""深挖 MCP resources/read + hackbot/genii + export/raw 上下文(2026-09-09)"""
import os, re, io, sys

sys.stdout = io.TextIOWrapper(sys.stdout.buffer, encoding="utf-8", errors="replace")

FILES = [
    r"D:\scan\h1kit\_h1x4_app.js",
    r"D:\scan\h1kit\_src_chunks\user_settings_router-DKsq46eC.js",
]

def find_all(text, needle, half=700):
    out = []
    start = 0
    while True:
        i = text.find(needle, start)
        if i < 0:
            break
        s = max(0, i - half)
        e = min(len(text), i + len(needle) + half)
        out.append(text[s:e])
        start = i + len(needle)
    return out

for f in FILES:
    if not os.path.exists(f):
        continue
    text = open(f, encoding="utf-8", errors="replace").read()
    name = os.path.basename(f)
    for needle in ["agentic_ui_mcp", "hackbot/genii", "export/raw", "resources/read"]:
        hits = find_all(text, needle)
        if hits:
            print(f"\n########## {name} :: {needle} ({len(hits)} hits) ##########")
            for h in hits[:3]:
                print(h)
                print("    ----")

# -*- coding: utf-8 -*-
"""找 rte 定义/import + sandbox 端点更多引用(2026-09-09)"""
import os, re, io, sys

sys.stdout = io.TextIOWrapper(sys.stdout.buffer, encoding="utf-8", errors="replace")

CHUNKS = r"D:\scan\h1kit\_src_chunks"
FILES = [r"D:\scan\h1kit\_h1x4_app.js"] + [os.path.join(CHUNKS, f) for f in os.listdir(CHUNKS) if f.endswith(".js")]
FILES += [r"D:\scan\h1kit\_h1x4_vendor.js", r"D:\scan\h1kit\_h1x3_constants.js"]

pats = {
    "sandbox_ep": re.compile(r'sandbox\?contentType|agentic_ui_mcp/sandbox'),
    "aui_renderer": re.compile(r'aui_renderer|renderer_uri|ui://'),
    "rte_def": re.compile(r'[,;(]rte=|\brte\s*=|rte:'),
    "iframe_sandbox": re.compile(r'iframe[^>]{0,120}sandbox'),
}

for f in FILES:
    if not os.path.exists(f):
        continue
    try:
        text = open(f, encoding="utf-8", errors="replace").read()
    except Exception:
        continue
    name = os.path.basename(f)
    for tag, pat in pats.items():
        ms = list(pat.finditer(text))
        if ms:
            print(f"\n### {name} :: {tag} ({len(ms)})")
            for m in ms[:4]:
                s = max(0, m.start() - 150)
                e = min(len(text), m.end() + 250)
                print("   ", text[s:e].replace("\n", " ")[:420])

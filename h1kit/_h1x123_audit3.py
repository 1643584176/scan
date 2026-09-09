# -*- coding: utf-8 -*-
"""pass3:修正则重扫 LOC/MSG/SRCDOC + 看非 vendor SINK(2026-09-09)"""
import os, re, io, sys

sys.stdout = io.TextIOWrapper(sys.stdout.buffer, encoding="utf-8", errors="replace")

SRC = r"D:\scan\h1kit\_src_chunks"
EXTRA = [r"D:\scan\h1kit\_h1x3_constants.js", r"D:\scan\h1kit\_h1x4_app.js"]

files = [os.path.join(SRC, f) for f in os.listdir(SRC) if f.endswith(".js")] + EXTRA

LOC_RE = re.compile(r'(?:location\.(?:href|assign|replace)|window\.open)\s*=\s*[^\s;]{0,160}')
MSG_RE = re.compile(r'addEventListener\(\s*["\']?message["\']?\s*,')
SRCDOC_RE = re.compile(r'srcdoc\s*=\s*["\'`]')
HREF_RE = re.compile(r'\.href\s*=\s*["\'`]')
OPEN_RE = re.compile(r'window\.open\s*\(\s*[^)]{0,120}\)')
ATTR_RE = re.compile(r'\.(setAttribute|setAttributeNS)\s*\(\s*["\'](?:src|href|srcdoc|action)["\']')

def ctx(text, m, half=200):
    s = max(0, m.start() - half)
    e = min(len(text), m.end() + half)
    return text[s:e].replace("\n", " ")

results = []
for i, f in enumerate(files):
    try:
        text = open(f, encoding="utf-8", errors="replace").read()
    except Exception:
        continue
    name = os.path.basename(f)
    if name.startswith(("vendor", "_h1x4_vendor")):
        continue  # 库代码跳过(已有结论)
    for pat, tag in [(LOC_RE, "LOC"), (MSG_RE, "MSG"), (SRCDOC_RE, "SRCDOC"), (HREF_RE, "HREF"), (OPEN_RE, "OPEN"), (ATTR_RE, "ATTR")]:
        for m in pat.finditer(text):
            results.append(f"[{tag}] {name}\n  {ctx(text, m)}\n")

out = "\n".join(results)
open(r"D:\scan\h1kit\_h1x123_audit3.txt", "w", encoding="utf-8").write(out)
print(f"hits: {len(results)}")
print(out[:6000])

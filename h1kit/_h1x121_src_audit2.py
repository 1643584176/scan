# -*- coding: utf-8 -*-
"""源码系统审计 pass2:URL 端点 + DOM sink + postMessage + 重定向(2026-09-09)"""
import os, re, io, sys

sys.stdout = io.TextIOWrapper(sys.stdout.buffer, encoding="utf-8", errors="replace")

SRC = [r"D:\scan\h1kit\_src_chunks"]
EXTRA = [
    r"D:\scan\h1kit\_h1x3_constants.js",
    r"D:\scan\h1kit\_h1x4_app.js",
    r"D:\scan\h1kit\_h1x4_vendor.js",
]
OUT = r"D:\scan\h1kit\_h1x121_src_audit2.txt"

files = []
for d in SRC:
    for fn in os.listdir(d):
        if fn.endswith(".js"):
            files.append(os.path.join(d, fn))
for f in EXTRA:
    if os.path.exists(f):
        files.append(f)

print(f"files: {len(files)}", flush=True)

URL_RE = re.compile(r'["\'](https?://[^"\']{4,120})["\']')
REL_RE = re.compile(r'["\'](/[a-zA-Z0-9_./?=&%:-]{3,120})["\']')
SINK_RE = re.compile(r'\.(insertAdjacentHTML|outerHTML|write|writeln)\s*[=(]')
LOC_RE = re.compile(r'(location\.(href|assign|replace)|window\.open)\s*[=(]')
MSG_RE = re.compile(r'addEventListener\(\s*["\']message["\']')
SRCDOC_RE = re.compile(r'srcdoc\s*=')

def ctx(text, m, half=160):
    s = max(0, m.start() - half)
    e = min(len(text), m.end() + half)
    return text[s:e].replace("\n", " ")

results = []
urls_all = set()
for i, f in enumerate(files):
    try:
        text = open(f, encoding="utf-8", errors="replace").read()
    except Exception:
        continue
    name = os.path.basename(f)
    for m in URL_RE.finditer(text):
        urls_all.add(m.group(1))
    # sinks 输出带上下文(限制每个文件 30 条)
    for m in SINK_RE.finditer(text):
        results.append(f"[SINK] {name}\n  {ctx(text, m)}\n")
    for m in LOC_RE.finditer(text):
        results.append(f"[LOC ] {name}\n  {ctx(text, m)}\n")
    for m in MSG_RE.finditer(text):
        results.append(f"[MSG ] {name}\n  {ctx(text, m)}\n")
    for m in SRCDOC_RE.finditer(text):
        results.append(f"[SRCDOC] {name}\n  {ctx(text, m)}\n")
    if i % 50 == 0:
        print(f"  scanned {i}/{len(files)}", flush=True)

with open(OUT, "w", encoding="utf-8") as f:
    f.write("===== SINK/LOC/MSG contexts =====\n")
    f.write("\n".join(results))
    f.write("\n\n===== ALL ABSOLUTE URLS =====\n")
    for u in sorted(urls_all):
        f.write(u + "\n")

print(f"done. sink hits: {len(results)}, urls: {len(urls_all)} -> {OUT}", flush=True)

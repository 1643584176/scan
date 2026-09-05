# -*- coding: utf-8 -*-
"""Round 4: NEW PRODUCT surfaces hidden in console JS:
agentic provisioning, warehouses, lakeview/lakewatch, notebook, spreadsheet
connector, data explorer, ingestion pipelines. Extract their API paths."""
import os
import re
import io
import sys

sys.stdout = io.TextIOWrapper(sys.stdout.buffer, encoding="utf-8", errors="replace")

JS_DIR = r"F:\scan\neon_report\_js"
blob = ""
for root, _, files in os.walk(JS_DIR):
    for fn in files:
        if fn.endswith(".js"):
            fp = os.path.join(root, fn)
            try:
                blob += open(fp, encoding="utf-8", errors="replace").read() + "\n"
            except Exception:
                pass

# Collect all api path templates: path:`...` and "/x/y" inside request({
PATHS = {}
for m in re.finditer(r"path:(?:`([^`]+)`|\"([^\"]+)\")", blob):
    p = m.group(1) or m.group(2)
    if p.startswith("/") and p.count("${") <= 3:
        PATHS.setdefault(p, 0)
        PATHS[p] += 1

KEYS = ["agentic", "provision", "warehouse", "warehouses", "lakeview", "lakewatch",
        "notebook", "spreadsheet", "explorer", "pipeline", "ingestion", "conversation",
        "assistant", "copilot", "ai_", "/ai", "data_explorer", "standalone"]
print("### interesting path templates from JS")
for p in sorted(PATHS):
    lp = p.lower()
    if any(k.lower() in lp for k in KEYS):
        print("  %-90s x%d" % (p, PATHS[p]))
print()
print("### context around 'agentic'")
for m in re.finditer(r"agentic", blob, re.I):
    seg = blob[max(0, m.start() - 500):m.start() + 500]
    seg = re.sub(r"\s+", " ", seg)
    print("  ...", seg[:1000])
    print()
    break
print("### context around 'spreadsheet' api")
for m in re.finditer(r"spreadsheet", blob, re.I):
    seg = blob[max(0, m.start() - 400):m.start() + 400]
    seg = re.sub(r"\s+", " ", seg)
    if "path:" in seg or "/" in seg[:200]:
        print("  ...", seg[:900])
        print()

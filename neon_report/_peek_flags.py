# -*- coding: utf-8 -*-
import json, io, sys
sys.stdout = io.TextIOWrapper(sys.stdout.buffer, encoding="utf-8", errors="replace")

for line in open(r"F:\scan\neon_report\_u1_out.jsonl", encoding="utf-8"):
    r = json.loads(line)
    if "feature_flags" in r["key"] or "agentic" in r["key"]:
        print("###", r["key"], "->", r["st"])
        print((r.get("body") or "")[:4000])
        print()

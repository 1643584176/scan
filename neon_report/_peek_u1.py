# -*- coding: utf-8 -*-
import json

for line in open(r"F:\scan\neon_report\_u1_out.jsonl", encoding="utf-8"):
    r = json.loads(line)
    if r["st"] == 200:
        print("###", r["key"], "->", r["st"])
        print((r.get("body") or "")[:700])
        print()

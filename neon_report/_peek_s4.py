# -*- coding: utf-8 -*-
import json

for line in open(r"F:\scan\neon_report\_s4_out.jsonl", encoding="utf-8"):
    r = json.loads(line)
    if r["st"] == 200 and (r["key"].startswith("ai_gateway") or
                           r["key"].startswith("storage") or
                           r["key"].startswith("logs fields") or
                           r["key"].startswith("creds list")):
        print("###", r["key"], "->", r["st"])
        print((r.get("body") or "")[:900])
        print()

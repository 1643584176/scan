# -*- coding: utf-8 -*-
import json

for line in open(r"F:\scan\neon_report\_s2_out.jsonl", encoding="utf-8"):
    r = json.loads(line)
    if r["key"].startswith("st5") or r["key"].startswith("st2 finalize"):
        print(r["key"], "->", r["st"], "| body:", (r.get("body") or "")[:500])

# -*- coding: utf-8 -*-
import json

for line in open(r"F:\scan\neon_report\_s3_out.jsonl", encoding="utf-8"):
    r = json.loads(line)
    if r["key"].startswith("A recon"):
        print("###", r["key"], "->", r["st"])
        print((r.get("body") or "")[:800])
        print()

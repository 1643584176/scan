# -*- coding: utf-8 -*-
"""Download HackerOne program metadata mirror (arkadiyt/bounty-targets-data)"""
import json
import urllib.request

URL = "https://raw.githubusercontent.com/arkadiyt/bounty-targets-data/main/data/hackerone_data.json"
OUT = r"F:\scan\h1_programs.json"

req = urllib.request.Request(URL, headers={"User-Agent": "Mozilla/5.0"})
with urllib.request.urlopen(req, timeout=60) as resp:
    data = json.loads(resp.read().decode("utf-8"))

print("total programs:", len(data))
# Inspect structure of first item
print(json.dumps(data[0], indent=1)[:600])
with open(OUT, "w", encoding="utf-8") as fh:
    json.dump(data, fh, ensure_ascii=False, indent=0)
print("saved to", OUT)

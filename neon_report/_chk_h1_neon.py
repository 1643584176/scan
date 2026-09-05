# -*- coding: utf-8 -*-
"""Find neon program entry inside h1_programs.json and print rules/criteria."""
import json

d = json.load(open(r"F:\scan\h1_programs.json", encoding="utf-8"))


def find_neon(o, path=""):
    if isinstance(o, dict):
        for k, v in o.items():
            find_neon(v, path + "." + k)
    elif isinstance(o, list):
        for i, v in enumerate(o):
            find_neon(v, path + "[%d]" % i)
    else:
        s = str(o)
        if "neon" in s.lower():
            print(path, "=", s[:300])


find_neon(d)

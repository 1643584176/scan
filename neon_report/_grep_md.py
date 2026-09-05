# -*- coding: utf-8 -*-
import glob, re, io, sys
sys.stdout = io.TextIOWrapper(sys.stdout.buffer, encoding="utf-8", errors="replace")

for f in sorted(glob.glob(r"F:\scan\neon_report\*.md")):
    try:
        t = open(f, encoding="utf-8").read()
    except Exception:
        continue
    hits = []
    for kw in ["add_default_grants", "jwks", "transfer_status", "owned_by",
               "settings", "auth/init", "permissions"]:
        for m in re.finditer(re.escape(kw), t):
            hits.append((kw, m.start()))
    if hits:
        print("##", f)
        seen = set()
        for kw, pos in hits[:10]:
            if pos in seen:
                continue
            seen.add(pos)
            print("  ", kw, ":", t[max(0, pos - 90):pos + 130].replace("\n", " "))
        print()

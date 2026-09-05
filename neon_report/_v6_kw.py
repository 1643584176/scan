# -*- coding: utf-8 -*-
import re
f = r"F:\scan\neon_report\Neon-Auth与DataAPI技术面-20260904.md"
t = open(f, encoding="utf-8", errors="replace").read()
for kw in ["mass", "Mass", "role", "impersonat", "sign-up", "signup", "admin"]:
    idxs = [m.start() for m in re.finditer(re.escape(kw), t)]
    print("### kw:", kw, "hits:", len(idxs))
    for i in idxs[:2]:
        print("   ...", t[max(0, i - 250):i + 250].replace("\n", " "))
    print()

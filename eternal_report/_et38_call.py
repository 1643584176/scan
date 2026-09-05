# -*- coding: utf-8 -*-
"""find call sites of searchapi.php var + how params are built"""
import re, glob

files = sorted(glob.glob("_js/z_*.js"))
for f in files:
    s = open(f, "r", encoding="utf-8", errors="replace").read()
    # locate the var definition to learn its name
    m = re.search(r'([A-Za-z_$][\w$]*)=("".concat\([^;]{0,80}searchapi\.php[^;]{0,40})', s)
    if not m:
        continue
    var = m.group(1)
    print("== %s var=%s ==" % (f, var))
    # find usages: var(...) or var+"?..." or .concat patterns
    for mm in list(re.finditer(re.escape(var) + r"\.concat\([^)]*\)", s))[:8]:
        i = mm.start()
        print("USE:", s[max(0, i - 120):i + 200].replace("\n", " ")[:320], "\n ---")
    for mm in list(re.finditer(r"[" + re.escape(var) + r"]\{1,3\}[+?]", s))[:20]:
        i = mm.start()
        ctx = s[max(0, i - 100):i + 180].replace("\n", " ")
        if "searchapi" in ctx or "entity" in ctx or "q=" in ctx or "category" in ctx.lower():
            print("CTX:", ctx[:280], "\n ---")
print("done", flush=True)

# -*- coding: utf-8 -*-
"""Extract console internal API surface: request() paths not under /api/v2.
1) find request() impl to learn prefixing
2) collect all `path:` template strings with ${} placeholders
3) collect telemetry/v1 usage
"""
import os
import re

JS_DIR = r"F:\scan\neon_report\_js"
DATA = {}
for root, _, files in os.walk(JS_DIR):
    for fn in files:
        if fn.endswith(".js"):
            fp = os.path.join(root, fn)
            try:
                DATA[fn] = open(fp, encoding="utf-8", errors="replace").read()
            except Exception:
                pass

blob = "\n".join(DATA.values())

# 1) find request impl inside the api class: look for "request=" or "request(" def
for m in re.finditer(r"request\s*[=:]\s*(?:async\s*)?\([^)]*\)\s*=>\s*\{", blob):
    seg = blob[m.start():m.start() + 900]
    print("### request impl candidate:", seg[:800].replace("\n", " "))
    print()

# 2) telemetry/v1 endpoints
print("==== telemetry/v1 usage ====")
for m in re.finditer(r'.{80}telemetry/v1.{200}', blob):
    print(m.group(0)[:280])
    print()

# 3) all path: templates with /projects/ or /organizations/ or /users/ etc
print("==== path: templates (unique, 300 max) ====")
paths = set()
for m in re.finditer(r'path\s*:\s*`([^`]+)`', blob):
    p = m.group(1)
    if "/api/" not in p and ("/projects/" in p or "/organizations/" in p or
                             "/users/" in p or "/branches/" in p or "/auth" in p):
        paths.add(p)
for p in sorted(paths):
    print("  ", p)

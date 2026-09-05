# -*- coding: utf-8 -*-
"""Check neon test environment availability (non-sensitive: file/key presence only)"""
import json
import os

base = r"F:\scan\neon_report"

# Check credential/context files exist without printing secrets
targets = ["_ctx.json", "_ctx_b.json", "_apikey.json", "_neon_creds.py",
           "_neon_creds_prod.py", "_neon_creds_stage.py", "_pguri.txt",
           "_auth_better_auth.json", "_apikey_path.py"]
for f in targets:
    full = os.path.join(base, f)
    if os.path.exists(full):
        size = os.path.getsize(full)
        try:
            with open(full, "r", encoding="utf-8") as fh:
                head = fh.read(200)
            print("OK  %-28s (%dB) %r..." % (f, size, head[:120]))
        except Exception as exc:
            print("OK  %-28s (%dB) read-err %s" % (f, size, exc))
    else:
        print("MISS %s" % f)

# Check for recent _p/_pg script naming to infer test stage
print("\n--- last-modified scripts in neon_report ---")
import time
files = []
for f in os.listdir(base):
    full = os.path.join(base, f)
    if f.startswith(("_p", "_pg", "_n", "_o", "_m", "_j", "_k")) and f.endswith(".py"):
        files.append((os.path.getmtime(full), f))
files.sort(reverse=True)
for mt, f in files[:15]:
    print(time.strftime("%m-%d %H:%M", time.localtime(mt)), f)

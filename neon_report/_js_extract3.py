# -*- coding: utf-8 -*-
"""Extract call sites (method+body) for hidden write endpoints from console JS."""
import os
import re

JS_DIR = r"F:\scan\neon_report\_js"
blob = ""
for root, _, files in os.walk(JS_DIR):
    for fn in files:
        if fn.endswith(".js"):
            fp = os.path.join(root, fn)
            try:
                blob += open(fp, encoding="utf-8", errors="replace").read() + "\n"
            except Exception:
                pass

KEYWORDS = ["passwordless_auth", "reset_to_parent", "branch_import", "auth/init",
            "features/enable", "early_access", "aigw_credits", "stats",
            "sync_keys_vercel", "integrations/monitoring/datadog", "applications/vercel",
            "transfer_ownership", "role_change_preview", "reset\"", "query/history",
            "saved_queries", "/recover", "deletion_checklist", "guests", "platform-served"]

for kw in KEYWORDS:
    print("=" * 20, kw, "=" * 20)
    cnt = 0
    for m in re.finditer(re.escape(kw), blob):
        seg = blob[max(0, m.start() - 260):m.start() + 260]
        seg = re.sub(r"\s+", " ", seg)
        print("  ...", seg)
        print()
        cnt += 1
        if cnt >= 3:
            break

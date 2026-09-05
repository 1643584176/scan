# -*- coding: utf-8 -*-
"""Round 3: passwordless template body, jwks POST body & SSRF candidate,
auth/init full flow (redirect_uri!), SQL editor execution channel,
project member role management context, hard_delete semantics.
"""
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


def show(title, regex, span=650, maxhits=4, flags=0):
    print("=" * 25, title, "=" * 25, flush=True)
    pat = re.compile(regex, flags)
    hits = 0
    for m in pat.finditer(blob):
        seg = blob[max(0, m.start() - span):m.start() + span]
        seg = re.sub(r"\s+", " ", seg)
        print("[%d] ...%s" % (hits, seg))
        print(flush=True)
        hits += 1
        if hits >= maxhits:
            break
    if not hits:
        print("  (no hits)", flush=True)


# 1. passwordless template BODY (wZ value)
show("psql_passwordless template", r"wZ=`[^`]{0,600}`")
# 2. jwks add body & callers
show("jwks url fetch", r"(jwks_url|jwksUrl|fetchJwks|validateJwks)[^;]{0,200}", maxhits=5)
# 3. auth/init flow: redirect params & callers
show("auth init callers", r"initializeNeonAuthProviderOAuth", maxhits=3, span=800)
show("auth init redirect", r"redirect[^;]{0,150}auth", maxhits=5, span=300)
# 4. SQL editor execution channel (websocket / proxy)
show("sql editor exec", r"(executeSql|runSql|sqlEditor|SqlEditor|/sql/|query_editor)", maxhits=5, span=300)
# 5. role_change_preview usage
show("role change preview use", r"role_change_preview", maxhits=2, span=900)
# 6. hard_delete callers
show("hard_delete callers", r"hard_delete[^;]{0,120}", maxhits=6, span=300)
print("== DONE", flush=True)

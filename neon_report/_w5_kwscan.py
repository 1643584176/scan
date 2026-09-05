# -*- coding: utf-8 -*-
import re
f = r"F:\scan\neon_report\Neon-Auth与DataAPI技术面-20260904.md"
t = open(f, encoding="utf-8", errors="replace").read()
for kw in ["transfer_ownership", "send_test_email", "email_provider/test", "auth/users",
           "auth/create", "auth/keys", "auth/user", "allow_localhost", "auth/config",
           "auth/domains", "email_server", "auth/integration", "transfer_status",
           "project_members", "permissions", "transfer_requests", "projects/shared"]:
    idxs = [m.start() for m in re.finditer(re.escape(kw), t)]
    print("### kw:", kw, "hits:", len(idxs))
    for i in idxs[:3]:
        seg = t[max(0, i - 200):i + 200].replace("\n", " ")
        print("   ...", seg)
    print()

# -*- coding: utf-8 -*-
# _sw_paths.py - dump path prefixes from netlify open-api swagger.yml
import yaml, collections

d = yaml.safe_load(open(r"D:/scan/netlify_report/_openapi/swagger.yml", encoding="utf-8"))
ps = list(d.get("paths", {}).keys())
print("total paths:", len(ps))
pre = collections.Counter()
for p in ps:
    seg = p.strip("/").split("/")
    pre["/".join(seg[:2])] += 1
for k, v in pre.most_common(80):
    print(v, k)
print()
print("== member/team-ish paths ==")
for p in ps:
    if any(s in p.lower() for s in ("member", "invite", "team", "account", "user", "role", "collaborator")):
        print(p)

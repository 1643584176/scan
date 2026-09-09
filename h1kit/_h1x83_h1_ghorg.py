# -*- coding: utf-8 -*-
"""拉 hacker0x01 repo 列表(2026-09-09)"""
import json
import urllib.request

out = []
for page in (1, 2):
    url = f"https://api.github.com/orgs/hacker0x01/repos?per_page=100&page={page}"
    req = urllib.request.Request(url, headers={"User-Agent": "Mozilla/5.0", "Accept": "application/vnd.github+json"})
    try:
        with urllib.request.urlopen(req, timeout=20) as r:
            repos = json.loads(r.read().decode())
        for repo in repos:
            out.append({
                "name": repo["name"],
                "desc": repo.get("description"),
                "lang": repo.get("language"),
                "archived": repo.get("archived"),
                "fork": repo.get("fork"),
                "updated": repo.get("pushed_at"),
            })
    except Exception as e:
        print("ERR page", page, e)
with open(r"D:\scan\h1kit\_hacker0x01_repos.json", "w") as f:
    json.dump(out, f, indent=1)
print("total:", len(out))
for r_ in sorted(out, key=lambda x: x["name"].lower()):
    if r_["desc"]:
        print(f'{r_["name"]} | {r_["lang"]} | {(r_["desc"] or "")[:100]}')

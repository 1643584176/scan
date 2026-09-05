# -*- coding: utf-8 -*-
"""Filter H1 programs related to databases (PG/MySQL/Redis/Mongo/cloud-db)"""
import json

DB_KW = [
    "database", "postgres", "postgre", "mysql", "maria", "redis", "mongo",
    "sql", "neon", "supabase", "cockroach", "clickhouse", "timescale",
    "planetscale", "dynamo", "cassandra", "neo4j", "elasticsearch",
    "serverless", "data", "snowflake", "bigquery", "warehouse", "vector",
]

with open(r"F:\scan\h1_programs.json", encoding="utf-8") as fh:
    data = json.load(fh)

rows = []
for p in data:
    if p.get("submission_state") != "open":
        continue
    name = (p.get("name") or "").lower()
    handle = (p.get("handle") or "").lower()
    targets = p.get("targets", {}).get("in_scope", [])
    ids = " ".join((t.get("asset_identifier") or "").lower() for t in targets)
    blob = name + " " + handle + " " + ids
    # strict: keyword must be in name/handle OR clearly db-ish scope
    hit = any(k in blob for k in DB_KW)
    if not hit:
        continue
    if not p.get("offers_bounties") and p.get("managed_program"):
        continue
    n_url = sum(1 for t in targets if t.get("asset_type") in ("URL", "WILDCARD"))
    rows.append({
        "name": p.get("name"), "handle": p.get("handle"),
        "url": p.get("url"), "n": len(targets), "n_url": n_url,
        "eff": p.get("response_efficiency_percentage"),
        "state": p.get("submission_state"), "bounty": p.get("offers_bounties"),
        "first": p.get("average_time_to_first_program_response"),
    })

rows.sort(key=lambda r: (r["n_url"], r["n"]))
print("db-related open programs:", len(rows))
for r in rows:
    print("- %-35s @%-22s url=%-3d all=%-3d bounty=%s eff=%s firstResp=%sh" % (
        r["name"], r["handle"], r["n_url"], r["n"], r["bounty"], r["eff"], r["first"]))

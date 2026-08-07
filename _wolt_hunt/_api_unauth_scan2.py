# -*- coding: utf-8 -*-
"""接口批量未授权扫描 v2（并发版）
- 会话复用 + 线程池并发 + 严格超时
- 每个请求记录 status/长度/特征词，输出全量 JSON + 汇总
- 关键：404 只说明该域无此路由；401/405/403 说明路由存在、权限边界待测
"""
import requests, json, sys, re, time
from concurrent.futures import ThreadPoolExecutor, as_completed
import urllib3
urllib3.disable_warnings()
sys.stdout.reconfigure(encoding="utf-8", errors="replace")

H = {
    "User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36",
    "Origin": "https://wolt.com",
    "Accept": "application/json",
    "X-HackerOne-Research": "pccp",
}

BASES = [
    ("consumer",  "https://consumer-api.wolt.com"),
    ("restaurant", "https://restaurant-api.wolt.com"),
    ("corporate", "https://corporate-service.wolt.com"),
]

paths = []
for line in open(r"D:\scan\_wolt_hunt\_api_inventory_out.txt", encoding="utf-8"):
    m = re.match(r"^\s*\d+\s+(/\S+)$", line.strip())
    if m:
        p = m.group(1)
        if p not in paths:
            paths.append(p)

ID_CANDIDATES = ["1", "0", "test"]

sess = requests.Session()
sess.headers.update(H)

def probe_one(job):
    base, p, m, params = job
    url = base + p
    try:
        r = sess.request(m, url, params=params, timeout=(3.05, 5), verify=False)
        body = r.text[:300].replace("\n", " ")
        feats = []
        for w in ["Unauthorized", "Forbidden", "not found", "access_token", "error", "token", "expired", "missing", "invalid"]:
            if re.search(w, body, re.I):
                feats.append(w)
        return {"base": base.split("//")[1], "m": m, "p": p, "params": params,
                "st": r.status_code, "len": len(r.text), "feats": feats, "snip": body}
    except Exception as e:
        return {"base": base.split("//")[1], "m": m, "p": p, "params": params,
                "st": None, "len": 0, "feats": [str(e)[:50]], "snip": ""}

# 构造任务：基础请求 + id 变体 + query 变体
jobs = []
for bname, base in BASES:
    for p in paths:
        m = "GET"
        if p.startswith(("/v1/wauth2/", "/v1/utils/send-email", "/v1/admin/", "/order-xp/v1/baskets/bulk/delete")):
            m = "POST"
        jobs.append((base, p, m, None))
        if "{id}" in p:
            for cid in ID_CANDIDATES:
                jobs.append((base, p.replace("{id}", cid), "GET", None))
        elif p.count("/") <= 3:
            for qv in [{"pagination": "false"}, {"include": "all"}]:
                jobs.append((base, p, "GET", qv))

print(f"TOTAL jobs: {len(jobs)}", flush=True)
results = []
t0 = time.time()
with ThreadPoolExecutor(max_workers=10) as ex:
    futs = [ex.submit(probe_one, j) for j in jobs]
    for i, f in enumerate(as_completed(futs)):
        r = f.result()
        results.append(r)
        if r["st"] is not None and (r["st"] != 404 or (r["st"] == 404 and len(r["feats"]) > 0)):
            line = f"[{r['base']:<10}] {r['m']:<4} {r['p'][:64]:<64} {str(r['params']):<26} {str(r['st']):<5} len={r['len']:<6} {','.join(r['feats'])[:50]}"
            print(line, flush=True)
        if (i + 1) % 50 == 0:
            print(f"... {i+1}/{len(jobs)} ({time.time()-t0:.0f}s)", flush=True)

json.dump(results, open(r"D:\scan\_wolt_hunt\_api_unauth_scan.json", "w", encoding="utf-8"), indent=1, ensure_ascii=False)

print("\n===== SUMMARY (by status) =====", flush=True)
from collections import Counter
c = Counter((r["base"], r["st"]) for r in results)
for k, v in sorted(c.items()):
    print(f"  {k[0]:<12} {str(k[1]):<6} x{v}", flush=True)

print("\n===== 非 404 响应（路由存在或异常）=====", flush=True)
seen = set()
for r in sorted(results, key=lambda x: (x["st"] is None, str(x["st"]))):
    if r["st"] != 404:
        k = (r["base"], r["m"], r["p"], str(r["params"]))
        if k in seen:
            continue
        seen.add(k)
        print(f"  [{r['base']}] {r['m']} {r['p']} {str(r['params'])} -> {r['st']} len={r['len']} | {r['snip'][:140]}", flush=True)
print("\nDONE", flush=True)

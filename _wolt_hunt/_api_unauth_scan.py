# -*- coding: utf-8 -*-
"""接口批量未授权扫描（L0/L1 证据收集）
策略：不只盯 200 —— 对每个接口族记录 status/响应头/body 特征，
并针对含 {id} 的接口尝试多种 id 形态与附加参数，供后续越权推演。
"""
import requests, json, sys, re, time, urllib3
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

# 从清单输出解析路径
paths = []
for line in open(r"D:\scan\_wolt_hunt\_api_inventory_out.txt", encoding="utf-8"):
    line = line.strip()
    m = re.match(r"^\s*\d+\s+(/\S+)$", line)
    if m:
        p = m.group(1)
        if p not in paths:
            paths.append(p)

# 含 {id} 的路径 → id 候选值（多种形态以区分 404 是"路由不存在"还是"id 格式不对"）
ID_CANDIDATES = ["1", "0", "123", "000000000000000000000000", "test", "abc"]

# 无 {id} 的路径 → 附加 query 变体（思考：有些接口 200 空返回，加参数才暴露数据）
QUERY_VARIANTS = [
    None,
    {"pagination": "false"},
    {"include": "all"},
    {"verbose": "true"},
]

def sig(r):
    """响应指纹：status + 内容类型 + 长度 + 特征词"""
    ct = r.headers.get("Content-Type", "")[:40]
    body = r.text[:2000]
    feats = []
    for w in ["Unauthorized", "Forbidden", "not found", "Not Found", "access_token",
              "error", "message", "token", "expired", "missing", "invalid"]:
        if re.search(w, body, re.I):
            feats.append(w)
    return ct, len(body), feats

def probe(base, m, p, params=None, body=None):
    url = base + p
    try:
        r = requests.request(m, url, headers=H, params=params, json=body, timeout=6, verify=False)
        ct, ln, feats = sig(r)
        return r.status_code, ct, ln, feats, r.text[:300].replace("\n", " ")
    except Exception as e:
        return None, "", 0, [str(e)[:60]], ""

results = []
print(f"{'#':<4}{'BASE':<11}{'METHOD':<6}{'PATH':<62}{'ST':<5}{'LEN':<7}FEATURES")
print("=" * 130)

for bi, (bname, base) in enumerate(BASES):
    for pi, p in enumerate(paths):
        # 1) 无参数 GET/POST 直连
        m = "GET"
        if p.startswith(("/v1/wauth2/", "/v1/utils/send-email", "/v1/admin/", "/order-xp/v1/baskets/bulk/delete")):
            m = "POST"
        st, ct, ln, feats, snippet = probe(base, m, p)
        line = f"{pi:<4}{bname:<11}{m:<6}{p[:60]:<62}{str(st):<5}{ln:<7}{','.join(feats)[:60]}"
        print(line)
        results.append({"base": bname, "m": m, "p": p, "params": None, "st": st, "ct": ct, "len": ln, "feats": feats, "snip": snippet})

        # 2) 含 {id} → 尝试多种 id 形态
        if "{id}" in p and st not in (401,):
            for cid in ID_CANDIDATES[:3]:
                url_p = p.replace("{id}", cid)
                st2, ct2, ln2, fe2, sn2 = probe(base, "GET", url_p)
                # 只在出现 200 或与无参不同状态时记录（有效信号）
                if st2 == 200 or (st2 not in (404, 401) and st2 != st):
                    line = f"{pi:<4}{bname:<11}{'GET':<6}{url_p[:60]:<62}{str(st2):<5}{ln2:<7}{','.join(fe2)[:60]}"
                    print("  └→", line)
                    results.append({"base": bname, "m": "GET", "p": url_p, "params": None, "st": st2, "ct": ct2, "len": ln2, "feats": fe2, "snip": sn2})

        # 3) 无 {id} → 附加 query 变体（防"200 空壳"漏判）
        if "{id}" not in p and st in (200, 404) and pi % 3 == 0:
            for qv in QUERY_VARIANTS:
                st3, ct3, ln3, fe3, sn3 = probe(base, "GET", p, params=qv)
                if st3 == 200 and (ln3 != ln or ln3 > 0):
                    line = f"{pi:<4}{bname:<11}{'GET':<6}{p[:40]}{str(qv):<22}{str(st3):<5}{ln3:<7}{','.join(fe3)[:50]}"
                    print("  └→", line)
                    results.append({"base": bname, "m": "GET", "p": p, "params": qv, "st": st3, "ct": ct3, "len": ln3, "feats": fe3, "snip": sn3})
        time.sleep(0.15)

json.dump(results, open(r"D:\scan\_wolt_hunt\_api_unauth_scan.json", "w", encoding="utf-8"), indent=1, ensure_ascii=False)

# ===== 汇总 =====
print("\n===== SUMMARY =====")
from collections import Counter
c = Counter((r["base"], r["st"]) for r in results)
for k, v in sorted(c.items()):
    print(f"  {k[0]:<12} {str(k[1]):<6} x{v}")

print("\n===== 200 / 非标准响应候选 =====")
for r in results:
    if r["st"] == 200 or r["st"] not in (401, 403, 404, 405, None):
        print(f"  [{r['base']}] {r['m']} {r['p']} {str(r['params'])} -> {r['st']} len={r['len']} | {r['snip'][:160]}")
print("\nDONE")

# -*- coding: utf-8 -*-
"""查 davensec 的全部 hacktivity 报告 + figma 披露报告（标题/CWE/金额可读）"""
import json, sys, time, urllib.request

API = "https://hackerone.com/graphql"
HEADERS = {
    "Content-Type": "application/json",
    "User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0 Safari/537.36",
    "Accept": "application/json",
    "Origin": "https://hackerone.com",
    "Referer": "https://hackerone.com/hacktivity/overview",
}

QUERY = """query HacktivitySearch($query_string: String, $first: Int, $after: String, $sort: SortInput) {
  search(index: CompleteHacktivityReportIndex, query_string: $query_string, first: $first, after: $after, sort: $sort) {
    total_count
    pageInfo { hasNextPage endCursor }
    nodes {
      ... on HacktivityDocument {
        id
        report { title id }
        team { handle name }
        reporter { username }
        severity_rating
        total_awarded_amount
        disclosed_at
        submitted_at
        cwe
      }
    }
  }
}"""

def fetch_page(query_string, first, after, sort):
    variables = {"query_string": query_string, "first": first}
    if after:
        variables["after"] = after
    if sort:
        variables["sort"] = sort
    payload = {"query": QUERY, "variables": variables, "operationName": "HacktivitySearch"}
    req = urllib.request.Request(API, data=json.dumps(payload).encode(), headers=HEADERS)
    with urllib.request.urlopen(req, timeout=30) as r:
        body = json.loads(r.read().decode())
    if "errors" in body:
        raise RuntimeError(json.dumps(body["errors"], ensure_ascii=False)[:800])
    return body["data"]["search"]

def fetch_all(query_string, pages=15, page_size=50):
    sort = {"field": "latest_disclosable_activity_at", "direction": "DESC"}
    all_nodes = []
    after = None
    total = None
    for p in range(pages):
        for attempt in range(3):
            try:
                res = fetch_page(query_string, page_size, after, sort)
                break
            except Exception as e:
                print(f"[{query_string}] page {p} attempt {attempt} err: {e}")
                time.sleep(5)
        else:
            break
        total = res["total_count"]
        nodes = res["nodes"]
        all_nodes.extend(nodes)
        print(f"[{query_string}] page {p}: {len(nodes)} items (累计 {len(all_nodes)} / total {total})")
        if len(nodes) < page_size:
            break
        after = res["pageInfo"]["endCursor"]
        time.sleep(1.5)
    return {"query": query_string, "total": total, "items": all_nodes}

def dump(items, outfile):
    with open(outfile, "w", encoding="utf-8") as f:
        json.dump(items, f, ensure_ascii=False, indent=1)
    print(f"-> {outfile}: {len(items)} 条")

if __name__ == "__main__":
    # 1) davensec 的所有报告（含其他项目，看研究模式）
    r1 = fetch_all("davensec", pages=15)
    dump(r1["items"], "D:/scan/_h1_toolkit/data/davensec_all.json")
    # 2) figma 披露的报告（标题可见！）
    r2 = fetch_all("figma disclosed:true", pages=15)
    dump(r2["items"], "D:/scan/_h1_toolkit/data/figma_disclosed.json")
    # 3) figma + davensec
    r3 = fetch_all("figma davensec", pages=5)
    dump(r3["items"], "D:/scan/_h1_toolkit/data/figma_davensec.json")

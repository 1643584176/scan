# -*- coding: utf-8 -*-
"""H1 hacktivity 抓取：disclosed:true / disclosed:false 各 10 页（每页 50 条，Relay cursor 分页）

用法:
    python hacktivity_fetch.py            # 抓全部并写 data/
    python hacktivity_fetch.py --pages 5  # 自定义页数
"""
import json
import sys
import time
import urllib.request

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
        report { title }
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


def fetch_all(query_string, pages=10, page_size=50, sort=None):
    # 注意: search 的 hasNextPage 恒为 false,endCursor 是 base64 编码的 offset
    # (如 "NTA" = base64("50")),分页需循环取 endCursor 作为下一次的 after,
    # 以"本次返回节点数 < page_size"作为结束条件。
    if sort is None:
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
            print(f"[{query_string}] page {p} FAILED")
            break
        total = res["total_count"]
        nodes = res["nodes"]
        all_nodes.extend(nodes)
        print(f"[{query_string}] page {p}: {len(nodes)} items (累计 {len(all_nodes)} / total {total})")
        if len(nodes) < page_size:
            print(f"[{query_string}] 已到末尾(返回 {len(nodes)} < {page_size})")
            break
        after = res["pageInfo"]["endCursor"]
        time.sleep(1.5)
    return {"query": query_string, "total": total, "items": all_nodes}


def main():
    pages = 10
    if len(sys.argv) > 1 and sys.argv[1] == "--pages":
        pages = int(sys.argv[2])
    for disclosed, outfile in [
        (True, "D:/scan/_h1_toolkit/data/hacktivity_disclosed.json"),
        (False, "D:/scan/_h1_toolkit/data/hacktivity_undisclosed.json"),
    ]:
        q = "disclosed:true" if disclosed else "disclosed:false"
        out = fetch_all(q, pages=pages)
        with open(outfile, "w", encoding="utf-8") as f:
            json.dump(out, f, ensure_ascii=False, indent=1)
        print(f"[{q}] 写入 {outfile}: {len(out['items'])} 条")
        time.sleep(2)


if __name__ == "__main__":
    main()

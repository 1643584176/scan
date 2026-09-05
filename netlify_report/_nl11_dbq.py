# -*- coding: utf-8 -*-
"""NL11: probe database-query function liveness (read-only SQL) - is the DB surface still reachable?"""
import http.client, ssl, json, sys
sys.path.insert(0, r'F:\scan\netlify_report')
from _net_creds import TOKEN_B, COOKIE_B

ctx = ssl.create_default_context()
SITE_B_ID = 'd2977de0-d24d-4544-81cb-933e610cad7d'


def q(site_id, sql, token=None, cookie=None):
    body = {"siteId": site_id, "action": "query", "sql": sql}
    conn = http.client.HTTPSConnection("app.netlify.com", timeout=40, context=ctx)
    h = {'User-Agent': 'Mozilla/5.0 Chrome/126.0', 'Content-Type': 'application/json', 'Origin': 'https://app.netlify.com'}
    if cookie:
        h['Cookie'] = cookie
    if token:
        h['Authorization'] = 'Bearer ' + token
    conn.request("POST", "/.netlify/functions/database-query", json.dumps(body).encode(), headers=h)
    r = conn.getresponse()
    raw = r.read().decode("utf-8", "replace")
    conn.close()
    return r.status, raw


def main():
    print("== NL11 ==", flush=True)
    for tag, kw in (("cookie", {"cookie": COOKIE_B}), ("token", {"token": TOKEN_B})):
        st, b = q(SITE_B_ID, "SELECT current_user, version()", **kw)
        print("%s: -> %d %s" % (tag, st, b[:300].replace("\n", " ")), flush=True)
    # try site A too (usage_exceeded site)
    st, b = q('04f08ff6-f274-47ac-b6d7-5fb1e055f3b4', "SELECT 1", token=TOKEN_B)
    print("A site via B token: -> %d %s" % (st, b[:200]), flush=True)
    print("done", flush=True)


if __name__ == "__main__":
    main()

# -*- coding: utf-8 -*-
"""NL23b: cleanup deploy key created during probe"""
import http.client, ssl, json, sys
sys.path.insert(0, r'F:\scan\netlify_report')
from _net_creds import TOKEN_A

ctx = ssl.create_default_context()
KEY_ID = '6a9bf977e8ea46367d4b6ffd'


def api(method, path, token=None):
    conn = http.client.HTTPSConnection("api.netlify.com", timeout=30, context=ctx)
    h = {'User-Agent': 'Mozilla/5.0 Chrome/126.0', 'Accept': 'application/json'}
    if token:
        h['Authorization'] = 'Bearer ' + token
    conn.request(method, path, headers=h)
    r = conn.getresponse()
    raw = r.read().decode("utf-8", "replace")
    conn.close()
    return r.status, raw


def main():
    print("== NL23b ==", flush=True)
    st, b = api("DELETE", "/api/v1/deploy_keys/%s" % KEY_ID, TOKEN_A)
    print("delete key [%d] %s" % (st, b[:200]), flush=True)
    st, b = api("GET", "/api/v1/deploy_keys", TOKEN_A)
    print("list after [%d] %s" % (st, b[:200]), flush=True)
    print("done", flush=True)


if __name__ == "__main__":
    main()

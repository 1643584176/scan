# -*- coding: utf-8 -*-
# _hk_cleanup2.py - delete matrix2 hooks
import sys, os, json, urllib.request, urllib.error

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
from _net_creds import TOKEN_B

API = "https://api.netlify.com/api/v1"

def req(method, url):
    r = urllib.request.Request(url, method=method)
    r.add_header("Authorization", "Bearer " + TOKEN_B)
    try:
        with urllib.request.urlopen(r, timeout=20) as resp:
            return resp.status
    except urllib.error.HTTPError as e:
        return e.code

ids = json.load(open(r"D:\scan\netlify_report\_hk_matrix2_ids.json"))
for k, hid in ids.items():
    print(k, req("DELETE", API + "/hooks/%s" % hid))

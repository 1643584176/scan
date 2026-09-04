# -*- coding: utf-8 -*-
# _ar_cleanup4.py - check individual run GET after delete
import sys, os, json, urllib.request, urllib.error

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
from _net_creds import TOKEN_B

API = "https://api.netlify.com/api/v1"

def req(method, url, tok=None, timeout=20):
    r = urllib.request.Request(url, method=method)
    if tok:
        r.add_header("Authorization", "Bearer " + tok)
    try:
        with urllib.request.urlopen(r, timeout=timeout) as resp:
            b = resp.read(20000)
            return resp.status, b[:300]
    except urllib.error.HTTPError as e:
        return e.code, e.read(2000)[:300]
    except Exception as ex:
        return -1, str(ex)[:200]

for rid in ["6a98d6d818790895d7d5ac00", "6a98d5e6448c07a76d7babf3", "6a98da92968b9a6f212f9775", "6a98db3f0041c71a1811ee8d"]:
    s, b = req("GET", API + "/agent_runners/%s" % rid, tok=TOKEN_B)
    print(rid, "->", s, b[:120])

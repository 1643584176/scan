# -*- coding: utf-8 -*-
# _hk_types2.py - full hook types dump (find url/email/events)
import sys, os, json, urllib.request, urllib.error

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
from _net_creds import TOKEN_B

API = "https://api.netlify.com/api/v1"

def req(method, url, tok=None, timeout=30):
    r = urllib.request.Request(url, method=method)
    r.add_header("Authorization", "Bearer " + tok)
    try:
        with urllib.request.urlopen(r, timeout=timeout) as resp:
            return resp.status, json.loads(resp.read().decode("utf-8", "replace"))
    except urllib.error.HTTPError as e:
        return e.code, None

s, b = req("GET", API + "/hooks/types", tok=TOKEN_B)
if isinstance(b, list):
    print("total types:", len(b))
    for t in b:
        nm = t.get("name", "")
        evs = t.get("events", [])
        fields = [f.get("name") for f in t.get("fields", [])]
        print("%-35s events=%s fields=%s" % (nm, evs, fields))

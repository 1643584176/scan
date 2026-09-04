# -*- coding: utf-8 -*-
# _st_probe.py - support-tickets fn: baseline + create + cross-account visibility
import sys, os, json, urllib.request, urllib.error

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
from _net_creds import COOKIE_A, COOKIE_B

FN = "https://app.netlify.com/.netlify/functions/support-tickets"
MARK = "qz-probe-9303"

def req(method, url, cookie=None, body=None, timeout=30):
    r = urllib.request.Request(url, method=method)
    if cookie:
        r.add_header("Cookie", cookie)
    data = json.dumps(body).encode() if body is not None else None
    if body is not None:
        r.add_header("Content-Type", "application/json")
    try:
        with urllib.request.urlopen(r, data=data, timeout=timeout) as resp:
            b = resp.read(60000)
            try:
                return resp.status, json.loads(b.decode("utf-8", "replace"))
            except Exception:
                return resp.status, b[:800]
    except urllib.error.HTTPError as e:
        b = e.read(8000)
        try:
            return e.code, json.loads(b.decode("utf-8", "replace"))
        except Exception:
            return e.code, b[:600]
    except Exception as ex:
        return -1, str(ex)[:200]

def show(tag, s, d):
    if isinstance(d, bytes):
        d = d.decode("utf-8", "replace")
    if isinstance(d, str):
        print("%-30s -> %s %s" % (tag, s, d[:500]))
    else:
        print("%-30s -> %s %s" % (tag, s, json.dumps(d, ensure_ascii=False)[:500]))

# baseline: B search + list-cc (should be empty-ish)
for tag, ck in (("anon", None), ("B", COOKIE_B), ("A", COOKIE_A)):
    s, d = req("GET", FN + "?action=search-tickets&q=" + MARK, cookie=ck)
    show("search baseline " + tag, s, d)
    s, d = req("GET", FN + "?action=list-cc-tickets", cookie=ck)
    show("list-cc " + tag, s, d)

# A creates one ticket
s, d = req("POST", FN + "?action=create-ticket", cookie=COOKIE_A,
           body={"subject": MARK, "body": "automated probe ticket for isolation check",
                 "collaborator_emails": [], "uploads": []})
show("create A", s, d)
tid = None
if isinstance(d, dict):
    tid = d.get("ticketId") or d.get("ticket_id") or (d.get("ticket") or {}).get("id")
print("ticket id:", tid)
json.dump({"tid": tid}, open(r"D:\scan\netlify_report\_st_tid.json", "w"))

# cross-account read/search
if tid:
    for tag, ck in (("B", COOKIE_B), ("A", COOKIE_A)):
        s, d = req("GET", FN + "?action=search-tickets&q=" + MARK, cookie=ck)
        show("search after create " + tag, s, d)

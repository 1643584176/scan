# -*- coding: utf-8 -*-
"""ET43b: o2_handler.php minimal param test"""
import http.client, ssl, time

ctx = ssl.create_default_context()
UA = "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/126.0.0.0 Safari/537.36"

def get(path):
    try:
        conn = http.client.HTTPSConnection("www.zomato.com", 443, timeout=10, context=ctx)
        conn.request("GET", path, headers={"User-Agent": UA, "Accept": "application/json"})
        r = conn.getresponse()
        raw = r.read(4000)
        conn.close()
        print("[%s] %d %s" % (path, r.status, raw.decode("utf-8", "replace")[:180].replace("\n", " ")), flush=True)
    except Exception as e:
        print("[%s] EXC %s" % (path, repr(e)[:70]), flush=True)

get("/php/o2_handler.php?res_id=1")
time.sleep(1.0)
get("/php/o2_handler.php?user_id=1")
time.sleep(1.0)
get("/php/o2_handler.php?res_id=1&user_id=1")
print("done", flush=True)

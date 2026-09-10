# -*- coding: utf-8 -*-
"""ET58: error-message-driven param discovery on search endpoints"""
import http.client, ssl, time, json

ctx = ssl.create_default_context()
UA = "Mozilla/5.0 (Windows NT 10.0; Win64; x64) Chrome/126.0.0.0 Safari/537.36"

def req(method, path, body=None, ctype=None, tag=""):
    try:
        hdr = {"User-Agent": UA, "Accept": "application/json,text/html,*/*", "X-Hackerone": "xxbo",
               "Referer": "https://www.zomato.com/ncr/restaurants?q=pizza"}
        if ctype:
            hdr["Content-Type"] = ctype
        conn = http.client.HTTPSConnection("www.zomato.com", 443, timeout=15, context=ctx)
        conn.request(method, path, body=body, headers=hdr)
        r = conn.getresponse()
        raw = r.read(20000)
        conn.close()
        print("== [%s] %s %s -> %d" % (tag, method, path[:90], r.status), flush=True)
        print("    " + raw.decode("utf-8", "replace")[:420].replace("\n", " "), flush=True)
    except Exception as e:
        print("== [%s] %s EXC %s" % (tag, path[:60], repr(e)[:100]), flush=True)

req("POST", "/webroutes/search/applyFilter", "", "application/x-www-form-urlencoded", "af-empty")
time.sleep(1)
req("POST", "/webroutes/search/applyFilter", "{}", "application/json", "af-json")
time.sleep(1)
req("GET", "/webapi/searchapi.php?q=pizza&zpwa=true", None, None, "zpwa")
time.sleep(1)
req("GET", "/webroutes/search/autoSuggest?q=pizza&city_id=1&lat=28.6&lon=77.2", None, None, "as-city")
print("done", flush=True)

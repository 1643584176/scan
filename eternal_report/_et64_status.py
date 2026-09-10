# -*- coding: utf-8 -*-
"""ET64: post-cooldown status - single normal-form request per host, stop on 403"""
import ssl, http.client, time

ctx = ssl.create_default_context()
UA = "Mozilla/5.0 (Windows NT 10.0; Win64; x64) Chrome/126.0.0.0 Safari/537.36"
HDR = {"User-Agent": UA, "Accept": "application/json,text/html,*/*",
       "X-Hackerone": "xxbo"}


def probe(tag, host, path, referer=None, read=4000):
    try:
        conn = http.client.HTTPSConnection(host, 443, timeout=15, context=ctx)
        h = dict(HDR)
        if referer:
            h["Referer"] = referer
        conn.request("GET", path, headers=h)
        r = conn.getresponse()
        raw = r.read(read)
        conn.close()
        body = raw.decode("utf-8", "replace")[:150].replace("\n", " ")
        print("[%s] %d len=%d %s" % (tag, r.status, len(raw), body), flush=True)
        return r.status
    except Exception as e:
        print("[%s][EXC] %s" % (tag, repr(e)[:110]), flush=True)
        return None


# step1: www baseline (was IP-banned)
s = probe("www", "www.zomato.com", "/webroutes/restaurant/info?res_id=3",
          "https://www.zomato.com/ncr/restaurants?q=pizza")
if s == 403:
    print("STILL BANNED - full stop", flush=True)
    raise SystemExit
if s == 200:
    print("UNBANNED - proceed slowly", flush=True)

time.sleep(20)

# step2: winecellar root (Tier1 cold domain)
probe("winecellar", "winecellar.zomato.com", "/")

time.sleep(20)

# step3: external.zomans.com root (new host from JS)
probe("zomans", "external.zomans.com", "/")

print("done", flush=True)

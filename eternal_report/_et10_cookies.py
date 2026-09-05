# -*- coding: utf-8 -*-
"""check Set-Cookie on district.in/ticketnew.com pages + cookie echo variants on /gw/auth/refresh_token"""
import http.client, ssl, json, uuid

ctx = ssl.create_default_context()
UA = "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/126.0.0.0 Safari/537.36"

def get_setcookies(h, path):
    try:
        conn = http.client.HTTPSConnection(h, 443, timeout=10, context=ctx)
        conn.request("GET", path, headers={"User-Agent": UA, "Accept": "text/html"})
        r = conn.getresponse()
        r.read(5000)
        conn.close()
        sc = r.headers.get_all("Set-Cookie") or []
        return [(s.split(";")[0], s) for s in sc]
    except Exception as e:
        return [("EXC", repr(e)[:100])]

print("== district.in / ==")
for c in get_setcookies("www.district.in", "/"):
    print("  ", c[1][:180])
print("== ticketnew.com /movies ==")
for c in get_setcookies("ticketnew.com", "/movies"):
    print("  ", c[1][:180])

# refresh_token with cookie name guesses
def rt(cookie):
    conn = http.client.HTTPSConnection("api.edition.in", 443, timeout=10, context=ctx)
    hdrs = {"User-Agent": UA, "Content-Type": "application/json",
            "Origin": "https://www.district.in", "x-device-id": str(uuid.uuid4()).upper(),
            "x-app-type": "ed_web", "x-app-version": "11.11.1"}
    if cookie:
        hdrs["Cookie"] = cookie
    conn.request("POST", "/gw/auth/refresh_token", body=json.dumps({}), headers=hdrs)
    r = conn.getresponse()
    raw = r.read(300)
    conn.close()
    print("rt cookie=%r -> [%d] %s" % ((cookie or "")[:60], r.status, raw.decode("utf-8", "replace")[:200]))

print("\n== refresh_token cookie-name guessing ==")
rt(None)
rt("refresh_token=abc")
rt("access_token=abc")
rt("ed_token=abc")
rt("userProfile=abc")
rt("token=abc")
print("done", flush=True)

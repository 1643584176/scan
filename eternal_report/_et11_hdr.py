# -*- coding: utf-8 -*-
"""ET11: refresh_token header/body variants to identify token source"""
import http.client, ssl, json, uuid

ctx = ssl.create_default_context()
UA = "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/126.0.0.0 Safari/537.36"


def call(extra_hdrs=None, body="{}", path="/gw/auth/refresh_token"):
    conn = http.client.HTTPSConnection("api.edition.in", 443, timeout=10, context=ctx)
    hdrs = {"User-Agent": UA, "Content-Type": "application/json",
            "Origin": "https://www.district.in", "x-device-id": str(uuid.uuid4()).upper(),
            "x-app-type": "ed_web", "x-app-version": "11.11.1"}
    if extra_hdrs:
        hdrs.update(extra_hdrs)
    conn.request("POST", path, body=body, headers=hdrs)
    r = conn.getresponse()
    raw = r.read(400)
    setc = r.headers.get_all("Set-Cookie") or []
    conn.close()
    print("[%d] %s %s" % (r.status, raw.decode("utf-8", "replace")[:220], ("SC=" + setc[0][:100]) if setc else ""), flush=True)


print("== refresh_token variants ==")
call({"Authorization": "Bearer abc"})
call({"Authorization": "abc"})
call({"x-refresh-token": "abc"})
call({"x-access-token": "abc"})
call(body=json.dumps({"refresh_token": "abc"}))
call(body=json.dumps({"token": "abc"}))
call(body=json.dumps({"refreshToken": "abc"}))
print("\n== movies endpoint with bearer ==")
call({"Authorization": "Bearer abc"}, path="/gw/consumer/movies/v3/cities")
print("\n== validate_otp shape (no real code) ==")
call(body=json.dumps({"phone_number": "abc", "otp": "123456"}), path="/gw/auth/validate_otp")
print("done", flush=True)

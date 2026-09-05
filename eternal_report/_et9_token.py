# -*- coding: utf-8 -*-
"""ET9: anonymous token acquisition attempt on api.edition.in/gw"""
import http.client, ssl, json, uuid

ctx = ssl.create_default_context()
UA = "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/126.0.0.0 Safari/537.36"
H = "api.edition.in"
DEVICE = str(uuid.uuid4()).upper()


def req(method, path, body=None, headers=None, read=20000):
    conn = http.client.HTTPSConnection(H, 443, timeout=10, context=ctx)
    hdrs = {
        "User-Agent": UA, "Accept": "application/json, text/plain, */*",
        "Content-Type": "application/json",
        "Origin": "https://www.district.in",
        "Referer": "https://www.district.in/",
        "x-device-id": DEVICE,
        "x-app-type": "ed_web",
        "x-app-version": "11.11.1",
        "x-is-events-supported": "true",
        "x-is-movies-supported": "true",
    }
    if headers:
        hdrs.update(headers)
    conn.request(method, path, body=body, headers=hdrs)
    r = conn.getresponse()
    raw = r.read(read)
    conn.close()
    return r.status, dict((k.lower(), v) for k, v in r.getheaders()), raw


def show(tag, st, hdrs, raw):
    print("%-46s [%d] %s" % (tag, st, raw[:600].decode("utf-8", "replace")), flush=True)
    return raw


def main():
    # 1. refresh_token with empty body (like frontend does)
    st, hdrs, raw = req("POST", "/gw/auth/refresh_token", json.dumps({}))
    show("refresh_token {}", st, hdrs, raw)
    # set-cookie?
    for k, v in hdrs.items():
        if k in ("set-cookie", "authorization"):
            print("   hdr %s=%s" % (k, v[:200]), flush=True)

    # 2. refresh_token with no body at all
    st, hdrs, raw = req("POST", "/gw/auth/refresh_token", None)
    show("refresh_token no-body", st, hdrs, raw)

    # 3. generate_otp with invalid phone (no SMS sent: format gate)
    for ph in ["", "abc", "+91"]:
        st, hdrs, raw = req("POST", "/gw/auth/generate_otp", json.dumps({"phone_number": ph, "country_code": "+91"}))
        print("generate_otp phone=%r -> [%d] %s" % (ph, st, raw[:200].decode("utf-8", "replace")), flush=True)
    print("done", flush=True)


if __name__ == "__main__":
    main()

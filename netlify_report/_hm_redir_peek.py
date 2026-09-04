# -*- coding: utf-8 -*-
# _hm_redir_peek.py - inspect real 302 Location headers for matrix redirect rules
import urllib.request, urllib.error

class NoRedir(urllib.request.HTTPRedirectHandler):
    def redirect_request(self, *a, **k):
        return None

op = urllib.request.build_opener(NoRedir)
for k in ("ctl", "meta", "pub", "r10", "hex"):
    url = "https://sec-b-08v4pk.netlify.app/hm_%s/x" % k
    try:
        rq = urllib.request.Request(url, method="GET")
        with op.open(rq, timeout=15) as resp:
            print("%-5s %s loc=%r" % (k, resp.status, resp.headers.get("Location")))
    except urllib.error.HTTPError as e:
        print("%-5s %s loc=%r" % (k, e.code, e.headers.get("Location")))
    except Exception as ex:
        print("%-5s ERR %s" % (k, str(ex)[:120]))

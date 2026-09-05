# -*- coding: utf-8 -*-
"""ET7: grep downloaded JS for API endpoints / hosts / keys"""
import os, re, glob

JS_DIR = os.path.join(os.path.dirname(os.path.abspath(__file__)), "_js")
files = glob.glob(os.path.join(JS_DIR, "*.js"))

endpoints = {}   # endpoint -> [files]
hosts = {}       # host -> [files]
apikeys = {}     # keyname -> [files]
patterns = [
    (r'(https?://[a-zA-Z0-9.\-]+\.[a-z]{2,}(?::\d+)?/[A-Za-z0-9_\-./?=&%${}]*)', "url"),
    (r'["\'](/[a-zA-Z0-9_\-./]{3,})["\']', "path"),
    (r'["\'](/api/[a-zA-Z0-9_\-./?=&${}]{3,})["\']', "apipath"),
]
key_re = re.compile(r'(x-?api-?key|api[-_]?key|token|secret|client[-_]?id|authorization|access[-_]?token)\s*[:=]\s*["\']([^"\']{8,100})["\']', re.I)
host_re = re.compile(r'https?://([a-zA-Z0-9.\-]+\.(?:zomato|district|ticketnew|tktnew|insider|blinkit|runnr|grofers|hyperpure|zomans|eternal|edition)\.(?:com|in|io|net))')

for fn in files:
    name = os.path.basename(fn)
    try:
        data = open(fn, "r", encoding="utf-8", errors="replace").read()
    except Exception:
        continue
    for pat, typ in patterns:
        for m in re.finditer(pat, data):
            s = m.group(1)
            if len(s) < 4 or s.startswith("/_next") or ".css" in s or s.startswith("//") or "w3.org" in s:
                continue
            if s.startswith("http"):
                endpoints.setdefault(s[:160], set()).add(name)
            else:
                endpoints.setdefault(s[:160], set()).add(name)
    for m in host_re.finditer(data):
        hosts.setdefault(m.group(1), set()).add(name)
    for m in key_re.finditer(data):
        apikeys.setdefault(m.group(1), set()).add(name)

print("==== HOSTS (scope-ish) ====")
for h in sorted(hosts):
    print("%-40s %s" % (h, ",".join(sorted(hosts[h])[:4])))

print("\n==== KEY-ish assignments ====")
for k in sorted(apikeys):
    print("%-20s %s" % (k, ",".join(sorted(apikeys[k])[:4])))

print("\n==== ENDPOINTS (filtered interesting) ====")
skip = lambda s: any(x in s for x in (".css", ".png", ".svg", ".woff", ".gif", "fonts.", "cloudflare", "googleapis", "gstatic", "hotjar", "mixpanel", "segment.", "amplitude", "sentry", "facebook", "twitter.com", "instagram", "wa.me", "whatsapp", "play.google", "apps.apple", "schema.org", "doubleclick", "google-analytics", "gtag", "cdn.district.in/", "cdnjs", "unpkg", "w3.org", "twitter", "youtube", "linkedin", "telegram", "razorpay", "payu", "amazon.", "aws.", "placehold"))
seen = set()
for ep in sorted(endpoints):
    if skip(ep):
        continue
    if ep in seen:
        continue
    seen.add(ep)
    # dedupe similar
    print("%-100s %s" % (ep[:100], ",".join(sorted(endpoints[ep])[:3])))

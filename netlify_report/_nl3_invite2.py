# -*- coding: utf-8 -*-
"""NL3: invite body refinement - add site_access; role enum discovery"""
import http.client, ssl, gzip, brotli, json, sys, time
sys.path.insert(0, r'F:\scan\netlify_report')
from _net_creds import TOKEN_A, TEAM_A

ctx = ssl.create_default_context()
B_EMAIL = "729488839@qq.com"


def req(method, path, body=None, token=TOKEN_A, timeout=25):
    conn = http.client.HTTPSConnection('api.netlify.com', context=ctx, timeout=timeout)
    h = {'User-Agent': 'Mozilla/5.0 Chrome/126.0', 'Accept-Encoding': 'br, gzip',
         'Accept': 'application/json', 'Content-Type': 'application/json'}
    if token:
        h['Authorization'] = 'Bearer ' + token
    b = json.dumps(body).encode() if isinstance(body, (dict, list)) else body
    conn.request(method, path, body=b, headers=h)
    r = conn.getresponse()
    raw = r.read()
    enc = r.getheader('Content-Encoding')
    if enc == 'br':
        raw = brotli.decompress(raw)
    elif enc == 'gzip':
        raw = gzip.decompress(raw)
    st = r.status
    txt = raw.decode('utf-8', 'ignore')
    conn.close()
    return st, txt


def show(tag, st, b, n=400):
    print("[%s] -> %d %s" % (tag, st, b[:n].replace("\n", " ")), flush=True)


def main():
    print("== NL3 ==", flush=True)
    # site_access + role combos
    combos = [
        {"email": B_EMAIL, "role": "Member", "site_access": "all"},
        {"email": B_EMAIL, "role": "Owner", "site_access": "all"},
        {"email": B_EMAIL, "role": "Guest", "site_access": "all"},
        {"email": B_EMAIL, "role": "Admin", "site_access": "all"},
        {"email": B_EMAIL, "role": "Owner", "site_access": "selected", "site_ids": ["04f08ff6-f274-47ac-b6d7-5fb1e055f3b4"]},
        {"email": B_EMAIL, "role": "Collaborator", "site_access": "all"},
    ]
    for body in combos:
        st, b = req("POST", "/api/v1/%s/members" % TEAM_A, body)
        show("POST %s" % json.dumps(body)[:110], st, b, 300)
        if st in (200, 201):
            print("  SUCCESS!")
            break
        time.sleep(0.4)
    # observe pending state
    st, b = req("GET", "/api/v1/%s/members" % TEAM_A)
    ms = json.loads(b)
    for m in ms:
        print("member:", m.get("email"), "role:", m.get("role"), "pending:", m.get("pending"),
              "invite_id:", m.get("invite_id"), "site_access:", m.get("site_access"))
    # cleanup if created
    for m in ms:
        if m.get("email") == B_EMAIL:
            st, b = req("DELETE", "/api/v1/%s/members/%s" % (TEAM_A, m.get("id")))
            show("cleanup delete", st, b, 200)


if __name__ == "__main__":
    main()

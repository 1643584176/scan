# -*- coding: utf-8 -*-
"""NL2: invite flow blackbox - POST /{slug}/members body variants -> observe pending member state
Then check role variants Owner/Member/Guest, duplicate invite, self-invite"""
import http.client, ssl, gzip, brotli, json, sys, time
sys.path.insert(0, r'F:\scan\netlify_report')
from _net_creds import TOKEN_A, TOKEN_B, TEAM_A, TEAM_B

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


def show(tag, st, b, n=500):
    print("[%s] -> %d %s" % (tag, st, b[:n].replace("\n", " ")), flush=True)


def members(token=TOKEN_A, slug=TEAM_A):
    st, b = req("GET", "/api/v1/%s/members" % slug, token=token)
    try:
        return json.loads(b)
    except Exception:
        return []


def main():
    print("== NL2 invite flow ==", flush=True)
    # baseline members
    for m in members():
        print("member:", m.get("email"), "role:", m.get("role"), "pending:", m.get("pending"), "invite_id:", m.get("invite_id"))
    # body variants
    bodies = [
        {"email": B_EMAIL, "role": "Member"},
        {"emails": [B_EMAIL], "role": "Member"},
        {"accountAddMemberSetup": {"email": B_EMAIL, "role": "Member"}},
        {"invitee_email": B_EMAIL, "role": "Member"},
    ]
    for i, body in enumerate(bodies):
        st, b = req("POST", "/api/v1/%s/members" % TEAM_A, body)
        show("POST members #%d %s" % (i, json.dumps(body)[:90]), st, b, 400)
        time.sleep(0.5)
        ms = members()
        for m in ms:
            if m.get("email") == B_EMAIL:
                print("  >> B state: role=%s pending=%s invite_id=%s" % (m.get("role"), m.get("pending"), m.get("invite_id")))
        if st == 200 or st == 201:
            break
    # try PUT update role of pending (if pending exists)
    for m in members():
        if m.get("email") == B_EMAIL and m.get("pending"):
            mid = m.get("id")
            for body in ({"role": "Owner"}, {"accountUpdateMemberSetup": {"role": "Owner"}}, {"role": "Guest"}):
                st, b = req("PUT", "/api/v1/%s/members/%s" % (TEAM_A, mid), body)
                show("PUT member role %s" % json.dumps(body)[:60], st, b, 300)
                time.sleep(0.3)
            break
    # cleanup: remove pending invite
    for m in members():
        if m.get("email") == B_EMAIL:
            mid = m.get("id")
            st, b = req("DELETE", "/api/v1/%s/members/%s" % (TEAM_A, mid))
            show("DELETE pending member", st, b, 200)
            break
    print("final members:")
    for m in members():
        print("  ", m.get("email"), m.get("role"), m.get("pending"))


if __name__ == "__main__":
    main()

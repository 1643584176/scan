# -*- coding: utf-8 -*-
"""V15: better-auth FULL route existence matrix on Neon staging.
Blind spots: 2FA plugin, webauthn plugin, admin plugin, account mgmt,
org plugin leftovers (cancel/reject-invitation, list-invitations).
GET first (no cookie) -> 404 = absent; anything else = present (deep-dive)."""
import json, ssl, time, http.client

NA_HOST = "ep-crimson-fog-w2gucld1.neonauth.us-east-2.aws.neon.build"
ctx = ssl.create_default_context()
PASS = "SecTest!2026pass"
U1 = "libobo1229+na_org1@gmail.com"


def out(s):
    print("[%s] %s" % (time.strftime("%H:%M:%S"), s), flush=True)


def na(method, path, body=None, cookie=None, origin="http://localhost:3000", timeout=20):
    try:
        conn = http.client.HTTPSConnection(NA_HOST, timeout=timeout, context=ctx)
        payload = json.dumps(body) if body is not None else None
        hdrs = {"Content-Type": "application/json",
                "User-Agent": "Mozilla/5.0", "Accept": "application/json",
                "X-Bug-Bounty": "xxbo"}
        if origin is not None:
            hdrs["Origin"] = origin
        if cookie:
            hdrs["Cookie"] = cookie
        conn.request(method, path, body=payload, headers=hdrs)
        resp = conn.getresponse()
        data = resp.read().decode("utf-8", "replace")
        ck = resp.getheader("Set-Cookie", "")
        conn.close()
        time.sleep(0.25)
        return resp.status, data, ck
    except Exception as e:
        time.sleep(0.25)
        return None, str(e)[:120], ""


def main():
    out("== V15 better-auth full route matrix ==")
    st, d, ck = na("POST", "/neondb/auth/sign-in/email",
                   {"email": U1, "password": PASS})
    cookie = ck.split(";")[0] if st in (200, 201) else None
    out("cookie: %s" % bool(cookie))
    if not cookie:
        return

    routes_anon = [
        # account / session mgmt
        ("POST", "/neondb/auth/change-password", {"currentPassword": PASS, "newPassword": PASS}),
        ("POST", "/neondb/auth/change-email", {"newEmail": "libobo1229+na_org1@gmail.com"}),
        ("POST", "/neondb/auth/delete-user", {}),
        ("POST", "/neondb/auth/revoke-sessions", {}),
        ("POST", "/neondb/auth/revoke-other-sessions", {}),
        ("POST", "/neondb/auth/migrate", {}),
        # 2FA plugin
        ("POST", "/neondb/auth/two-factor/enable", {}),
        ("POST", "/neondb/auth/two-factor/verify-otp", {"code": "000000"}),
        ("POST", "/neondb/auth/two-factor/send-otp", {}),
        ("POST", "/neondb/auth/two-factor/verify-totp", {"code": "000000"}),
        ("POST", "/neondb/auth/two-factor/disable", {}),
        ("POST", "/neondb/auth/two-factor/trust-device", {}),
        ("POST", "/neondb/auth/two-factor/send-otp-phone", {}),
        # webauthn plugin
        ("GET", "/neondb/auth/webauthn/register", None),
        ("POST", "/neondb/auth/webauthn/register/verify", {}),
        ("GET", "/neondb/auth/webauthn/authenticate", None),
        ("POST", "/neondb/auth/webauthn/authenticate/verify", {}),
        # admin plugin
        ("GET", "/neondb/auth/admin/list-users", None),
        ("POST", "/neondb/auth/admin/list-users", {}),
        ("POST", "/neondb/auth/admin/create-user", {}),
        ("POST", "/neondb/auth/admin/ban-user", {}),
        ("POST", "/neondb/auth/admin/remove-user", {}),
        ("POST", "/neondb/auth/admin/set-role", {}),
        ("POST", "/neondb/auth/admin/list-sessions", {}),
        ("POST", "/neondb/auth/admin/revoke-user-session", {}),
        # org plugin leftovers
        ("POST", "/neondb/auth/organization/cancel-invitation", {}),
        ("POST", "/neondb/auth/organization/reject-invitation", {}),
        ("GET", "/neondb/auth/organization/list-invitations", None),
        ("GET", "/neondb/auth/organization/get-members", None),
        ("POST", "/neondb/auth/organization/list-invitations", {}),
        ("GET", "/neondb/auth/organization/list", None),
        ("GET", "/neondb/auth/organization/list-organizations", None),
        ("GET", "/neondb/auth/organization/get-active", None),
        ("GET", "/neondb/auth/organization/active", None),
        # misc
        ("GET", "/neondb/auth/user", None),
        ("GET", "/neondb/auth/session", None),
        ("GET", "/neondb/auth/error", None),
        ("GET", "/neondb/auth/", None),
    ]
    # anon pass (no cookie): only care != 404/405
    out("--- anonymous (no cookie) ---")
    for m, p, b in routes_anon:
        st2, d2, _ = na(m, p, b)
        mark = " " if st2 in (404, 405) else "*"
        out("%s %-52s -> %d %s" % (mark, m + " " + p, st2, d2[:80]))
    # authed pass (skip state-destructive probes)
    out("--- authed (cookie) ---")
    skip_authed = {"/neondb/auth/delete-user", "/neondb/auth/revoke-sessions",
                   "/neondb/auth/revoke-other-sessions", "/neondb/auth/migrate"}
    for m, p, b in routes_anon:
        if p in skip_authed:
            continue
        st2, d2, _ = na(m, p, b, cookie=cookie)
        mark = " " if st2 in (404, 405) else "*"
        out("%s %-52s -> %d %s" % (mark, m + " " + p, st2, d2[:80]))
    out("done")


if __name__ == "__main__":
    main()

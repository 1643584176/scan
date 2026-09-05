# -*- coding: utf-8 -*-
"""V35: exhaustive auth-route presence scan (better-auth standard route list)
GET no-body: 400 param-validation = route EXISTS; 404 = absent
POST empty: 400 = route exists (POST-only routes caught here)"""
import ssl, http.client, json, time

ctx = ssl.create_default_context()
NA = "ep-crimson-fog-w2gucld1.neonauth.us-east-2.aws.neon.build"
BASE = "/neondb/auth"

routes = [
    "sign-in/email", "sign-up/email", "sign-in/social", "sign-in/social/callback",
    "callback/google", "callback/github", "sign-out", "forget-password", "reset-password",
    "verify-email", "email-verification", "request-email-verification", "change-email",
    "change-password", "revoke-sessions", "revoke-other-sessions", "revoke-session",
    "get-session", "update-user", "token", "list-sessions",
    "organization/create", "organization/list", "organization/get", "organization/update",
    "organization/delete", "organization/set-active", "organization/members",
    "organization/member/role", "organization/member/remove", "organization/member/leave",
    "organization/invite-accept", "organization/invite-cancel", "organization/invite-remove",
    "organization/invite-member", "organization/invitation/list", "organization/leave",
    "organization/join",
    "admin/create-user", "admin/list-users", "admin/user", "admin/ban-user", "admin/unban-user",
    "admin/impersonate-user", "admin/stop-impersonating", "admin/remove-user",
    "admin/set-user-password", "admin/update-user", "admin/delete-user", "admin/session/delete",
    "admin/session/list", "admin/verification/delete", "admin/verification/list",
    "two-factor/enable", "two-factor/disable", "two-factor/verify", "two-factor/send-otp",
    "phone-number/send-otp", "phone-number/verify", "magic-link/send", "magic-link/verify",
    "oauth2/authorize", "oauth2/callback", "unlink-account", "link-social", "list-accounts",
    "list-organization-invitations", "accept-invitation", "org/accept-invitation",
    "session", "sessions", "me", "user", "refresh-token", "logout",
    "sign-in", "sign-up", "invite-member", "members",
]


def req(method, p, body=None):
    conn = http.client.HTTPSConnection(NA, timeout=20, context=ctx)
    h = {"Content-Type": "application/json", "Origin": "http://localhost:3000", "User-Agent": "Mozilla/5.0"}
    conn.request(method, BASE + "/" + p, json.dumps(body).encode() if body is not None else None, headers=h)
    r = conn.getresponse()
    d = r.read().decode("utf-8", "replace")
    conn.close()
    return r.status, d


def main():
    print("== V35 route presence ==")
    found = {}
    for p in routes:
        st, d = req("GET", p)
        if st != 404:
            found[p] = ("GET", st, d[:80].replace("\n", " "))
        time.sleep(0.12)
    for p in routes:
        st, d = req("POST", p, {})
        if st != 404:
            if p in found:
                continue
            found[p] = ("POST", st, d[:80].replace("\n", " "))
        time.sleep(0.12)
    print("\n== routes present (non-404): %d ==" % len(found))
    for p, v in sorted(found.items()):
        print("%-40s %s %d %s" % (p, v[0], v[1], v[2]))
    json.dump({k: list(v) for k, v in found.items()},
              open(r"F:\scan\neon_report\_v35_routes.json", "w"), indent=1)
    print("done")


if __name__ == "__main__":
    main()

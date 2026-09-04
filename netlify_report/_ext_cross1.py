# -*- coding: utf-8 -*-
# _ext_cross1.py - cross-account extension write fns (harmless variants)
import sys, os, json, urllib.request, urllib.error

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
from _net_creds import COOKIE_A, COOKIE_B, SITE_A
import _net_creds as C

TEAM_A_ID = "6a979dd2ae93f47d55b62897"  # A account uuid
TEAM_B_ID = "6a97b6454fef0db964f75db6"  # B account uuid (from /accounts)
SITE_B = "d2977de0-d24d-4544-81cb-933e610cad7d"
APP = "https://app.netlify.com"

def req(method, url, cookie=None, body=None, headers=None, timeout=25):
    r = urllib.request.Request(url, method=method)
    if cookie:
        r.add_header("Cookie", cookie)
    if headers:
        for k, v in headers.items():
            r.add_header(k, v)
    data = None
    if body is not None:
        data = json.dumps(body).encode()
        r.add_header("Content-Type", "application/json")
    try:
        with urllib.request.urlopen(r, data=data, timeout=timeout) as resp:
            b = resp.read(30000)
            try:
                return resp.status, json.loads(b.decode("utf-8", "replace"))
            except Exception:
                return resp.status, b[:500]
    except urllib.error.HTTPError as e:
        b = e.read(4000)
        try:
            return e.code, json.loads(b.decode("utf-8", "replace"))
        except Exception:
            return e.code, b[:400]
    except Exception as ex:
        return -1, str(ex)[:200]

H2 = {"Api-Version": "2", "Content-Type": "application/json"}

def t(name, method, path, cookie, body=None, headers=None):
    s, b = req(method, APP + path, cookie=cookie, body=body, headers=headers or H2)
    msg = json.dumps(b, ensure_ascii=False)[:300] if isinstance(b, (dict, list)) else repr(b)[:200]
    print("%-55s -> %s %s" % (name, s, msg))

# control: A on own team (uninstall nonexistent slug)
print("== control group (A cookie on A team) ==")
t("A uninstall nonexistent", "POST", "/.netlify/functions/uninstall-extension",
  COOKIE_A, {"teamId": TEAM_A_ID, "slug": "no-such-ext-xyz", "hostSiteUrl": None, "v1Migrated": False})
t("A install nonexistent slug", "POST", "/.netlify/functions/install-extension",
  COOKIE_A, {"teamId": TEAM_A_ID, "slug": "no-such-ext-xyz", "hostSiteUrl": None, "metaDataHeaders": {}})
t("A delete-configs siteA", "DELETE", "/.netlify/functions/delete-configurations-for-site?teamId=%s&siteId=%s" % (TEAM_A_ID, SITE_A),
  COOKIE_A, {"teamId": TEAM_A_ID, "siteId": SITE_A})
t("A delete-all-installs", "DELETE", "/.netlify/functions/delete-all-team-installations-for-team",
  COOKIE_A, {"teamId": TEAM_A_ID})

print()
print("== cross-account (B cookie on A team) ==")
t("B->A uninstall nonexistent", "POST", "/.netlify/functions/uninstall-extension",
  COOKIE_B, {"teamId": TEAM_A_ID, "slug": "no-such-ext-xyz", "hostSiteUrl": None, "v1Migrated": False})
t("B->A install nonexistent slug", "POST", "/.netlify/functions/install-extension",
  COOKIE_B, {"teamId": TEAM_A_ID, "slug": "no-such-ext-xyz", "hostSiteUrl": None, "metaDataHeaders": {}})
t("B->A delete-configs siteA", "DELETE", "/.netlify/functions/delete-configurations-for-site?teamId=%s&siteId=%s" % (TEAM_A_ID, SITE_A),
  COOKIE_B, {"teamId": TEAM_A_ID, "siteId": SITE_A})
t("B->A delete-all-installs", "DELETE", "/.netlify/functions/delete-all-team-installations-for-team",
  COOKIE_B, {"teamId": TEAM_A_ID})
t("B->A fetch-site-configuration", "GET", "/.netlify/functions/fetch-site-configuration?siteId=%s&teamId=%s&integrationSlug=test" % (SITE_A, TEAM_A_ID),
  COOKIE_B)
t("B->A fetch-installed", "POST", "/.netlify/functions/fetch-installed-extensions-for-team?teamId=%s" % TEAM_A_ID,
  COOKIE_B, {})

print()
print("== also A->B for symmetry ==")
t("A->B uninstall nonexistent", "POST", "/.netlify/functions/uninstall-extension",
  COOKIE_A, {"teamId": TEAM_B_ID, "slug": "no-such-ext-xyz", "hostSiteUrl": None, "v1Migrated": False})

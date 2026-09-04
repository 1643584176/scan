# -*- coding: utf-8 -*-
# _ds_probe5.py - enable visual editor / preview server via PATCH site settings
import sys, os, json, urllib.request, urllib.error

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
from _net_creds import TOKEN_A, TOKEN_B, SITE_A
import _net_creds as C

API = "https://api.netlify.com/api/v1"

def req(method, url, tok=None, body=None, timeout=30):
    r = urllib.request.Request(url, method=method)
    if tok:
        r.add_header("Authorization", "Bearer " + tok)
    data = None
    if body is not None:
        data = json.dumps(body).encode()
        r.add_header("Content-Type", "application/json")
    try:
        with urllib.request.urlopen(r, data=data, timeout=timeout) as resp:
            b = resp.read(40000)
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

def keys_of(d, depth=0):
    if not isinstance(d, dict) or depth > 3:
        return []
    out = []
    for k, v in d.items():
        out.append(k)
        if isinstance(v, dict):
            out += [k + "." + x for x in keys_of(v, depth + 1)]
    return out

# current site settings related fields
print("== current visual_editor / repo fields on SITE_A ==")
s, b = req("GET", API + "/sites/" + SITE_A, tok=TOKEN_A)
if isinstance(b, dict):
    for k in b:
        if any(x in k.lower() for x in ("visual", "editor", "repo", "build", "container")):
            v = b[k]
            print(k, "=", json.dumps(v, ensure_ascii=False)[:250] if not isinstance(v, str) else v[:250])
else:
    print(s, repr(b)[:300])

# try PATCH variants to enable
print()
patches = [
    {"visual_editor_active": True},
    {"visual_editor_settings": {"enabled": True, "container_type": "devServer"}},
    {"visual_editor_settings": {"enabled": True, "containerType": "devServer"}},
    {"visual_editor_settings": {"enabled": True}},
]
for body in patches:
    s, b = req("PATCH", API + "/sites/" + SITE_A, tok=TOKEN_A, body=body)
    if isinstance(b, dict):
        resp_keys = keys_of(b)
        ve = b.get("visual_editor_active"), json.dumps(b.get("visual_editor_settings", {}), ensure_ascii=False)[:300]
        msg = "visual_editor_active=%r settings=%r" % ve
    else:
        msg = repr(b)[:300]
    print("PATCH %s -> %s %s" % (json.dumps(body)[:120], s, msg))
    if isinstance(b, dict):
        # check if dev server list changed
        s2, b2 = req("GET", API + "/sites/%s/dev_servers" % SITE_A, tok=TOKEN_A)
        print("   dev_servers now:", s2, json.dumps(b2, ensure_ascii=False)[:300] if isinstance(b2, (dict, list)) else repr(b2)[:200])

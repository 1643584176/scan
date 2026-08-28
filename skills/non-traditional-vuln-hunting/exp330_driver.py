# -*- coding: utf-8 -*-
"""exp_j330 驱动: 清理旧沙箱/快照 -> 建新沙箱 -> 注入 exp330_guest.py -> 运行 -> cat 结果"""
import json, base64, time, sys, os
from vercel_driver import api, TEAM, PROJ, fresh_sandbox, cmd

STOP_MARKER = 'SCAN_DONE'


def cleanup():
    """删除所有旧沙箱(双删: 沙箱 + 快照), 释放 Hobby 快照配额"""
    c, r = api("GET", "/v2/sandboxes?teamId=%s&project=%s&limit=50" % (TEAM, PROJ))
    if c == 200:
        for sb in json.loads(r).get("sandboxes", []):
            name = sb["name"]
            c2, r2 = api("DELETE", "/v2/sandboxes/%s?teamId=%s&projectId=%s" % (name, TEAM, PROJ))
            print("del sandbox %s: %d" % (name, c2))
    # 快照列表(端点试探: snapshots)
    c, r = api("GET", "/v2/sandboxes/snapshots?teamId=%s&project=%s&limit=50" % (TEAM, PROJ))
    print("list snapshots:", c, r[:200])
    if c == 200:
        snaps = json.loads(r).get("snapshots", [])
        print("snapshot count:", len(snaps))
        for sn in snaps:
            sid = sn.get("id") or sn.get("snapshotId") or sn.get("name")
            if sid:
                c2, r2 = api("DELETE", "/v2/sandboxes/snapshots/%s?teamId=%s&project=%s" % (sid, TEAM, PROJ))
                print("del snapshot %s: %d %s" % (sid, c2, r2[:120]))


def run_exp330():
    sid = fresh_sandbox("exp330")
    print("sid:", sid)
    # 注入脚本
    code = open(os.path.join(os.path.dirname(os.path.abspath(__file__)), "exp330_guest.py"), "rb").read()
    payload = base64.b64encode(code).decode()
    inject = "import base64;open('/vercel/sandbox/exp330.py','wb').write(base64.b64decode('%s'))" % payload
    c, r = cmd(sid, "python3", ["-c", inject], timeout_ms=30000)
    print("inject:", c, r[:200])
    # 运行(ARP 扫两个 /24 + 25s 监听约 3 分钟, timeout 给 280s)
    c, r = cmd(sid, "python3", ["/vercel/sandbox/exp330.py"], timeout_ms=280000)
    print("run:", c)
    print(r[:1000])
    # cat 结果(双通道)
    for attempt in range(5):
        time.sleep(3)
        c, r = cmd(sid, "cat", ["/vercel/sandbox/arp330.out"], timeout_ms=30000)
        if c == 200 and STOP_MARKER in r:
            print("=== 最终结果 ===")
            print(r)
            return r
        print("attempt %d: %s" % (attempt, r[:300]))
    # 最后再看一次
    c, r = cmd(sid, "cat", ["/vercel/sandbox/arp330.out"], timeout_ms=30000)
    print("=== 最后结果 ===")
    print(r)
    return r


if __name__ == "__main__":
    if len(sys.argv) > 1 and sys.argv[1] == "cleanup":
        cleanup()
    else:
        run_exp330()

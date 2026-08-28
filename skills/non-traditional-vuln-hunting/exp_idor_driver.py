# -*- coding: utf-8 -*-
"""承诺3验证: 对象删除后即失效? 删沙箱后旧 session ID 仍 exec?
流程: 建沙箱 -> 验证 cmd 可用 -> 删沙箱 -> 用旧 sid 发 cmd -> 观察 200/404/410
"""
import json, time, sys
from vercel_driver import api, TEAM, PROJ, fresh_sandbox, cmd

def main():
    sid = fresh_sandbox("exp_idor")
    print("sid:", sid)
    # 1) 正常 cmd
    c, r = cmd(sid, "echo", ["alive-1"], timeout_ms=30000)
    print("cmd before delete:", c, r[:150])
    # 2) 删除沙箱
    c, r = api("DELETE", "/v2/sandboxes/exp_idor?teamId=%s&projectId=%s" % (TEAM, PROJ))
    print("delete sandbox:", c, r[:200])
    time.sleep(3)
    # 3) 用旧 sid 发 cmd
    for i in range(3):
        c, r = cmd(sid, "echo", ["ghost-%d" % i], timeout_ms=30000)
        print("cmd after delete #%d:" % i, c, r[:250])
        time.sleep(2)
    # 4) 沙箱列表确认
    c, r = api("GET", "/v2/sandboxes?teamId=%s&project=%s&limit=50" % (TEAM, PROJ))
    print("list after delete:", c, r[:400])

if __name__ == "__main__":
    main()

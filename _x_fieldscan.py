# -*- coding: utf-8 -*-
"""控制面字段枚举: 沙箱创建 body + network-policy body 的未知/潜在字段
策略: 每个字段单独测, 用 API 错误信息反推 schema; 测完即删沙箱
候选面: image/fsId/region(创建) + dns/ports/rules(策略) -> 若接受则行为可能为新攻击面
"""
import json, os, sys, time
sys.path.insert(0, r'F:\scan\skills\non-traditional-vuln-hunting')
sys.stdout.reconfigure(encoding='utf-8')
from vercel_driver import api, TEAM, PROJ

OUT = r'F:\scan\skills\out\_fieldscan.txt'
buf = []

def log(s):
    print(s, flush=True)
    buf.append(s)

def try_create(name, extra, tag):
    """带 extra 字段创建沙箱, 返回 (code, body 摘要)"""
    body = {"projectId": PROJ, "name": name}
    body.update(extra)
    c, r = api("POST", "/v2/sandboxes?teamId=%s" % TEAM, body)
    log('[create:%s] %s | %s' % (tag, c, r[:600].replace('\n', ' ')))
    # 清理
    if c == 200:
        time.sleep(1)
        api("DELETE", "/v2/sandboxes/%s?teamId=%s&projectId=%s" % (name, TEAM, PROJ))
        time.sleep(1)
    return c, r

def try_policy(sid, body, tag):
    c, r = api("POST", "/v2/sandboxes/sessions/%s/network-policy?teamId=%s" % (sid, TEAM), body)
    log('[policy:%s] %s | %s' % (tag, c, r[:250].replace('\n', ' ')))
    return c, r

def main():
    # ===== 1) 创建 body 字段枚举 =====
    log('===== 1) CREATE body unknown fields =====')
    # 基线: 空 extra
    try_create('fs_base', {}, 'baseline')
    # 潜在注入面: 镜像/文件系统/区域/特权
    try_create('fs_img', {"image": "node:20"}, 'image-node20')
    try_create('fs_img2', {"image": "vercel/sandbox:latest"}, 'image-custom')
    try_create('fs_fsid', {"fsId": "fs_abc123"}, 'fsId')
    try_create('fs_region', {"region": "sfo1"}, 'region')
    try_create('fs_priv', {"privileged": True}, 'privileged')
    try_create('fs_caps', {"capabilities": ["CAP_SYS_ADMIN"]}, 'capabilities')
    try_create('fs_mount', {"mounts": [{"hostPath": "/etc", "guestPath": "/mnt/etc"}]}, 'mounts')
    try_create('fs_net', {"networkMode": "host"}, 'networkMode-host')
    try_create('fs_env', {"env": {"FOO": "bar"}}, 'env')
    try_create('fs_meta', {"metadata": {"k": "v"}}, 'metadata')
    try_create('fs_labels', {"labels": {"k": "v"}}, 'labels')
    try_create('fs_ttl', {"ttl": 3600}, 'ttl')
    try_create('fs_tmpl', {"templateId": "tpl_x"}, 'templateId')
    try_create('fs_runtime', {"runtime": "go1.22"}, 'runtime')
    try_create('fs_runtime2', {"runtime": "cua-ubuntu-xfce"}, 'runtime-xfce')
    try_create('fs_runtime3', {"runtime": "blackbox-playwright"}, 'runtime-playwright')
    try_create('fs_runtime4', {"runtime": "sandbox-roocode"}, 'runtime-roocode')
    try_create('fs_runtime5', {"runtime": "walleye-python"}, 'runtime-walleye')
    try_create('fs_mount2', {"mounts": {}}, 'mounts-empty')
    try_create('fs_mount3', {"mounts": {"host": "/etc", "guest": "/mnt"}}, 'mounts-obj')
    try_create('fs_mount4', {"mounts": {"/etc": "/mnt/etc"}}, 'mounts-map')

    # ===== 2) network-policy 未知字段枚举 =====
    log('===== 2) network-policy unknown fields =====')
    # 先建一个沙箱用于策略测试
    c, r = api("POST", "/v2/sandboxes?teamId=%s" % TEAM, {"projectId": PROJ, "name": "fs_pol"})
    if c != 200:
        log('create fs_pol failed: %s' % r[:200])
        return
    sid = json.loads(r)["sandbox"]["currentSessionId"]
    log('fs_pol sid: %s' % sid)

    base = {"mode": "custom", "allowedDomains": ["httpbin.org"]}
    fields = [
        ("dns", {"dns": {"mode": "block"}}),
        ("dns2", {"dns": {"allow": ["vercel.internal"]}}),
        ("allowedPorts", {"allowedPorts": [53, 443]}),
        ("deniedPorts", {"deniedPorts": [5432]}),
        ("protocols", {"protocols": ["tcp"]}),
        ("rules", {"rules": [{"action": "deny", "dst": "172.31.0.0/16"}]}),
        ("outbound", {"outbound": {"mode": "allow"}}),
        ("http", {"http": {"mode": "allow"}}),
        ("tls", {"tls": {"mode": "allow"}}),
        ("log", {"log": True}),
        ("dnsMode", {"dnsMode": "proxy"}),
        ("allowPrivate", {"allowPrivate": False}),
        ("privateNetworks", {"privateNetworks": []}),
        ("allowedHosts", {"allowedHosts": ["*"]}),
        ("egressRules", {"egressRules": []}),
        ("sniffing", {"sniffing": "on"}),
        ("wildcardDomains", {"wildcardDomains": ["*.vercel.app"]}),
        ("allowedIps", {"allowedIps": ["172.31.0.0/16"]}),
    ]
    for tag, extra in fields:
        body = dict(base)
        body.update(extra)
        try_policy(sid, body, tag)
        time.sleep(1)

    api("DELETE", "/v2/sandboxes/fs_pol?teamId=%s&projectId=%s" % (TEAM, PROJ))
    log('DONE')

    open(OUT, 'w', encoding='utf-8').write('\n'.join(buf))
    log('saved -> %s' % OUT)

if __name__ == '__main__':
    main()

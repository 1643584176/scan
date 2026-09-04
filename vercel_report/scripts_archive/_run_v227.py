# -*- coding: utf-8 -*-
"""v227: 公网 wss 代理面 — sb-xxx.vercel.run 域名解析 + 公网 26661/health/ws 探测
+ guest 完整 LISTEN 端口枚举 (沙箱内 payload)"""
import json, sys, time, socket, base64, urllib.request, ssl
sys.path.insert(0, r'D:\scan\skills\non-traditional-vuln-hunting')
sys.stdout.reconfigure(encoding='utf-8')
from vercel_driver import api, TEAM, PROJ, fresh_sandbox, cmd

NAME = 'v227'
PAY = r'D:\scan\skills\non-traditional-vuln-hunting\vda227_listen_guest.py'


def log(s): print(s, flush=True)


def http_probe(url, timeout=8):
    ctx = ssl.create_default_context()
    req = urllib.request.Request(url, headers={'User-Agent': 'Mozilla/5.0'})
    try:
        with urllib.request.urlopen(req, timeout=timeout, context=ctx) as r:
            return r.status, r.read()[:200]
    except urllib.error.HTTPError as e:
        return e.code, e.read()[:200]
    except Exception as e:
        return -1, str(e)[:150].encode()


if __name__ == '__main__':
    api('DELETE', '/v2/sandboxes/%s?teamId=%s&projectId=%s' % (NAME, TEAM, PROJ))
    sid = fresh_sandbox(NAME)
    log('sid=%s' % sid)

    # interactive 拿 URL
    c, r = api('POST', '/v2/sandboxes/sessions/%s/interactive?teamId=%s' % (sid, TEAM), {}, 60)
    log('interactive -> %s' % c)
    wurl = ''
    try:
        d = json.loads(r)
        wurl = d.get('url', '')
        log('wss url=%s' % wurl)
    except Exception:
        log('interactive resp: %s' % (r or '')[:200])

    # 域名解析
    if wurl:
        host = wurl.split('://')[1].split('/')[0]
        log('host=%s' % host)
        try:
            ips = socket.getaddrinfo(host, 443)
            for ip in ips[:6]:
                log('  DNS -> %s' % ip[4])
        except Exception as e:
            log('  DNS err %s' % e)
        base = 'https://%s' % host
        for p in ['/health', '/ws/interactive', '/', '/healthz']:
            c2, b2 = http_probe(base + p)
            log('pub GET %-18s -> %s %r' % (p, c2, b2[:100]))
        # 公网 26661 端口直连
        try:
            s = socket.create_connection((host, 26661), timeout=6)
            s.settimeout(3)
            s.sendall(b'GET /health HTTP/1.1\r\nHost: x\r\nConnection: close\r\n\r\n')
            buf = b''
            try:
                while True:
                    d = s.recv(4096)
                    if not d:
                        break
                    buf += d
            except socket.timeout:
                pass
            s.close()
            log('pub :26661 /health -> %r' % buf[:200])
        except Exception as e:
            log('pub :26661 conn err %s' % e)

    # guest 完整端口枚举 (注入 payload)
    b64 = base64.b64encode(open(PAY, 'rb').read()).decode()
    c, r = cmd(sid, 'python3', ['-c', "import base64;open('/vercel/sandbox/vda227.py','wb').write(base64.b64decode('%s'))" % b64], 60000)
    log('inject -> %s' % c)
    c, r = cmd(sid, 'python3', ['/vercel/sandbox/vda227.py'], 60000)
    log('run -> %s' % c)
    for line in (r or '').splitlines():
        if '"data"' in line:
            try:
                log('  guest: %s' % json.loads(line).get('data'))
            except Exception:
                pass

    api('DELETE', '/v2/sandboxes/%s?teamId=%s&projectId=%s' % (NAME, TEAM, PROJ))
    log('DONE')

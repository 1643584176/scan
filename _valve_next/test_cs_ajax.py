# -*- coding: utf-8 -*-
"""cs2: counter-strike.net ajax 端点未登录行为 + 参数测试"""
import re
import sys
import ssl
import time
import urllib.parse
import urllib.request

sys.stdout.reconfigure(encoding='utf-8', errors='replace')

CTX = ssl.create_default_context()
CTX.check_hostname = False
CTX.verify_mode = ssl.CERT_NONE
UA = ("Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 "
      "(KHTML, like Gecko) Chrome/126.0.0.0 Safari/537.36")
BASE = "https://www.counter-strike.net"


def get(url, timeout=20, referer=None):
    h = {'User-Agent': UA, 'Accept-Language': 'en-US,en;q=0.9'}
    if referer:
        h['Referer'] = referer
    r = urllib.request.Request(url, headers=h)
    try:
        resp = urllib.request.urlopen(r, context=CTX, timeout=timeout)
        return resp.status, resp.read(), dict(resp.headers), resp.geturl()
    except urllib.error.HTTPError as e:
        return e.code, e.read(), dict(e.headers), e.geturl()
    except Exception as e:
        return 0, str(e).encode(), {}, ''


def post(url, data, timeout=20, referer=None):
    h = {'User-Agent': UA, 'Accept-Language': 'en-US,en;q=0.9',
         'Content-Type': 'application/x-www-form-urlencoded'}
    if referer:
        h['Referer'] = referer
    r = urllib.request.Request(url, data=data.encode(), headers=h)
    try:
        resp = urllib.request.urlopen(r, context=CTX, timeout=timeout)
        return resp.status, resp.read(), dict(resp.headers), resp.geturl()
    except urllib.error.HTTPError as e:
        return e.code, e.read(), dict(e.headers), e.geturl()
    except Exception as e:
        return 0, str(e).encode(), {}, ''


def main():
    eps = [
        '/ajaxgetcreatorhomeinfo',
        '/ajaxgetvanityandclanid/',
        '/announcements/ajaxgetlocalization/',
        '/announcements/ajaxgetmyvote/',
        '/events/ajaxgetdynamiceventmetadata',
        '/ajaxcreateupdatedeletepartnerevents/',
        '/ajaxgetpartnereventpermissions/',
    ]
    print("=" * 70)
    print("[1] ajax 端点未登录 GET/POST 行为")
    print("=" * 70)
    for ep in eps:
        s, body, h, final = get(BASE + ep)
        txt = body.decode('utf-8', 'replace')[:160].replace('\n', ' ')
        print(f"GET  {ep:48s} -> {s} ct={h.get('Content-Type','')[:30]} {txt[:120]!r}")
        s, body, h, final = post(BASE + ep, 'appid=730&eventid=1&gid=1&steamid=76561197960434622')
        txt = body.decode('utf-8', 'replace')[:160].replace('\n', ' ')
        print(f"POST {ep:48s} -> {s} ct={h.get('Content-Type','')[:30]} {txt[:120]!r}")
        time.sleep(0.8)

    # main.js 里找这些端点的调用上下文(参数、请求方法)
    print()
    print("=" * 70)
    print("[2] main.js 中端点调用上下文")
    print("=" * 70)
    import os
    jsdir = r'D:\scan\_valve_next'
    for f in os.listdir(jsdir):
        if not f.startswith('cs_') or not f.endswith('.js'):
            continue
        txt = open(os.path.join(jsdir, f), encoding='utf-8', errors='replace').read()
        for ep in eps:
            if ep in txt:
                for m in re.finditer(re.escape(ep), txt):
                    i = m.start()
                    ctx = txt[max(0, i - 250):i + 250].replace('\n', ' ')
                    print(f"[{f}] {ep}:")
                    print(f"   ...{ctx[:500]}...")
                    print()

    # 事件/公告页参数反射
    print()
    print("=" * 70)
    print("[3] 事件/公告页参数反射")
    print("=" * 70)
    for path in ['/news/updates/', '/news/', '/cs2/']:
        for q in ['?id=XVXZTOKEN', '?event=XVXZTOKEN', '?gid=XVXZTOKEN',
                  '?appid=XVXZTOKEN', '?lang=XVXZTOKEN']:
            s, body, h, final = get(BASE + path + q)
            txt = body.decode('utf-8', 'replace')
            n = txt.count('XVXZTOKEN')
            if n:
                print(f"{path}{q:30s} -> {s} 反射={n}")
        time.sleep(0.8)


if __name__ == '__main__':
    main()

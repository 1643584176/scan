# -*- coding: utf-8 -*-
"""partner.steamgames.com:goto 参数 open redirect 测试 + 后台 JS 下载分析"""
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
BASE = "https://partner.steamgames.com"


def get(url, timeout=20):
    h = {'User-Agent': UA, 'Accept-Language': 'en-US,en;q=0.9'}
    r = urllib.request.Request(url, headers=h)
    try:
        resp = urllib.request.urlopen(r, context=CTX, timeout=timeout)
        return resp.status, resp.read(), dict(resp.headers), resp.geturl()
    except urllib.error.HTTPError as e:
        return e.code, e.read(), dict(e.headers), e.geturl()
    except Exception as e:
        return 0, str(e).encode(), {}, ''


def main():
    print("=" * 70)
    print("[A] partner ?goto= 参数行为")
    print("=" * 70)
    gotos = [
        '/home/',
        'https://evil.com/steal',
        '//evil.com/steal',
        'https://evil.com@partner.steamgames.com',
        'https://partner.steamgames.com.evil.com',
        'javascript:alert(1)',
        '/\\evil.com',
        '%2F%2Fevil.com',
        'https://partner.steamgames.com/home/',
    ]
    for g in gotos:
        s, body, h, final = get(BASE + "/?goto=" + urllib.parse.quote(g, safe=''))
        loc = h.get('Location')
        # 页面中 goto 反射
        txt = body.decode('utf-8', 'replace')
        hits = [m.start() for m in re.finditer(re.escape(g), txt)]
        print(f"goto={g!r:55s} -> {s} loc={loc} final={final[:70]} 反射{len(hits)}处")
        for i in hits[:2]:
            print(f"   @{i}: ...{txt[max(0,i-80):i+100]}...")
        time.sleep(0.5)

    print()
    print("=" * 70)
    print("[B] goto 在页面中如何被消费 (JS/表单)")
    print("=" * 70)
    s, body, h, final = get(BASE + "/?goto=%2Fhome%2F")
    txt = body.decode('utf-8', 'replace')
    open(r'D:\scan\_valve_next\partner_home.html', 'w', encoding='utf-8').write(txt)
    for kw in ['goto', 'redirect', 'return_to', 'login_redirect']:
        for m in re.finditer(re.escape(kw), txt):
            i = m.start()
            ctx = txt[max(0, i - 90):i + 130].replace('\n', ' ')
            print(f"   [{kw}] @{i}: ...{ctx[:220]}...")
            break
    # 表单
    for m in list(re.finditer(r'<form[^>]*>', txt))[:5]:
        print("   form:", m.group(0)[:200])
    for m in list(re.finditer(r'<input[^>]*>', txt))[:15]:
        print("   input:", m.group(0)[:150])

    print()
    print("=" * 70)
    print("[C] 下载后台 JS")
    print("=" * 70)
    js_names = ['marketing.js', 'storeadmin.js', 'admin.js', 'newsadmin.js', 'webtoolkit.aim.js',
                'prototype-1.7.js']
    # 从首页提取带版本号的 URL
    s, body, h, final = get(BASE + "/")
    txt = body.decode('utf-8', 'replace')
    for m in list(re.finditer(r'<script[^>]*src="([^"]+)"', txt)):
        url = m.group(1)
        for jn in js_names:
            if jn in url:
                name = 'partner_' + jn
                try:
                    s2, b2, h2, f2 = get(url)
                    open(rf'D:\scan\_valve_next\{name}', 'wb').write(b2)
                    print(f"   {name}: {len(b2)//1024} KB ({s2})")
                except Exception as e:
                    print(f"   {name}: ERROR {e}")
                time.sleep(0.5)


if __name__ == '__main__':
    main()

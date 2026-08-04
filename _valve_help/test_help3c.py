# -*- coding: utf-8 -*-
"""help3 第三批:redirect 字段字符集测试 + HelpWithLoginInfoReset 页面反射 + search_text 消费"""
import re
import sys
import json
import ssl
import http.cookiejar
import urllib.parse
import urllib.request

sys.stdout.reconfigure(encoding='utf-8', errors='replace')

CTX = ssl.create_default_context()
CTX.check_hostname = False
CTX.verify_mode = ssl.CERT_NONE
UA = ("Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 "
      "(KHTML, like Gecko) Chrome/126.0.0.0 Safari/537.36")
BASE = "https://help.steampowered.com"


def make_opener():
    cj = http.cookiejar.CookieJar()
    op = urllib.request.build_opener(
        urllib.request.HTTPSHandler(context=CTX),
        urllib.request.HTTPCookieProcessor(cj))
    op.addheaders = [('User-Agent', UA)]
    op.open(BASE + "/en/", timeout=15).read()
    sid = [c.value for c in cj if c.name == 'sessionid'][0]
    return op, sid


def post(op, path, params, ck):
    data = urllib.parse.urlencode(params).encode()
    r = urllib.request.Request(BASE + path, data=data, method="POST",
                               headers={'User-Agent': UA, 'Cookie': ck,
                                        'Content-Type': 'application/x-www-form-urlencoded'})
    try:
        resp = op.open(r, timeout=20)
        return resp.status, resp.read().decode('utf-8', 'replace'), dict(resp.headers)
    except urllib.error.HTTPError as e:
        return e.code, e.read().decode('utf-8', 'replace'), dict(e.headers)
    except Exception as e:
        return 0, str(e), {}


def get(op, path, ck):
    r = urllib.request.Request(BASE + path, headers={'User-Agent': UA, 'Cookie': ck})
    try:
        resp = op.open(r, timeout=20)
        return resp.status, resp.read().decode('utf-8', 'replace'), dict(resp.headers)
    except urllib.error.HTTPError as e:
        return e.code, e.read().decode('utf-8', 'replace'), dict(e.headers)
    except Exception as e:
        return 0, str(e), {}


def main():
    op, sid = make_opener()
    ck = f'sessionid={sid}'

    print("=" * 70)
    print("[I3] redirect 字段字符集测试 (account/issueid)")
    print("=" * 70)
    chars = ['999', '999.1', '9-9', '9_9', '999,1', '999 1', '999/1', '999\\1',
             '999?1', '999#1', '999:1', '999@1', '999%1', "999'1", '999"1',
             '999<1', '999>1', '999&1', '999=1', '999;1', '999+1', '999!1',
             '999~1', '999(1)', '999[1]', '999{1}']
    for v in chars:
        s, b, h = post(op, "/en/wizard/AjaxAccountRecoveryGetNextStep",
                       {'s': 'AAAA', 'account': v, 'reset': '0', 'issueid': '0', 'lost': '0', 'sessionid': sid}, ck)
        m = re.search(r'"redirect":"([^"]*)"', b)
        if m:
            rd = m.group(1).replace('\\/', '/')
            print(f"account={v!r:12s} -> {s} redirect={rd}")
        else:
            print(f"account={v!r:12s} -> {s} {b[:80]!r}")

    print()
    print("=" * 70)
    print("[I4] issueid 字符集测试")
    print("=" * 70)
    for v in ['999/1', '999\\1', '999?x=1', '999#x', '999@1', '999%00', '999"1', '999&a=1', '999;1']:
        s, b, h = post(op, "/en/wizard/AjaxAccountRecoveryGetNextStep",
                       {'s': 'AAAA', 'account': '0', 'reset': '0', 'issueid': v, 'lost': '0', 'sessionid': sid}, ck)
        m = re.search(r'"redirect":"([^"]*)"', b)
        if m:
            rd = m.group(1).replace('\\/', '/')
            print(f"issueid={v!r:12s} -> {s} redirect={rd}")
        else:
            print(f"issueid={v!r:12s} -> {s} {b[:80]!r}")

    print()
    print("=" * 70)
    print("[M] HelpWithLoginInfoReset?account= 页面反射")
    print("=" * 70)
    for v in ['999999999', 'XV"><script>alert(1)</script>', '999" onmouseover=alert(1)']:
        s, b, h = get(op, "/en/wizard/HelpWithLoginInfoReset/?account=" + urllib.parse.quote(v), ck)
        title = re.search(r'<title>([^<]*)</title>', b)
        hits = [m.start() for m in re.finditer(re.escape(v), b)]
        print(f"account={v!r:38s} -> {s} title={title.group(1) if title else None!r} 反射{len(hits)}处")
        for i in hits[:2]:
            print(f"   @{i}: ...{b[max(0,i-90):i+90]}...")

    print()
    print("=" * 70)
    print("[N] search_text 消费点 (help.js)")
    print("=" * 70)
    js = open(r'D:\scan\_valve_help\js\help.js', encoding='utf-8', errors='replace').read()
    for m in re.finditer(r'search_text', js):
        i = m.start()
        print(f"@{i}: ...{js[max(0,i-150):i+200].replace(chr(10),' ')}...")
        print()

    print()
    print("=" * 70)
    print("[O] AjaxSearchResults 参数变体")
    print("=" * 70)
    # appid + text 组合、空 text
    for params in [
        {'text': 'csgo', 'appid': '570', 'sessionid': sid},
        {'text': 'csgo', 'count': '100', 'sessionid': sid},
        {'text': '', 'sessionid': sid},
        {'text': 'a"&<>', 'sessionid': sid},
    ]:
        s, b, h = post(op, "/en/wizard/AjaxSearchResults/", params, ck)
        print(f"{params} -> {s} len={len(b)} {b[:150]!r}")


if __name__ == '__main__':
    main()

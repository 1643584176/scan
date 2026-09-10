# -*- coding: utf-8 -*-
"""h1x53t: 全类型字段名扫描 - 找引用报告/original/duplicate/related 的字段(跨 Report/Activity/Notification 系)"""
import json, sys, io, urllib.request, re
sys.stdout = io.TextIOWrapper(sys.stdout.buffer, encoding='utf-8', errors='replace')

def gql(q):
    req = urllib.request.Request('https://hackerone.com/graphql',
        data=json.dumps({'query': q}).encode(),
        headers={'Content-Type': 'application/json', 'User-Agent': 'Mozilla/5.0'})
    try:
        with urllib.request.urlopen(req, timeout=25) as r:
            return json.loads(r.read().decode())
    except Exception as e:
        return {'__err': str(e)}

def type_fields(tn, depth=0):
    """返回类型字段名->返回类型名映射"""
    q = f'query{{ __type(name: "{tn}") {{ kind fields {{ name type {{ kind name ofType {{ kind name ofType {{ name }} }} }} }} }} }}'
    r = gql(q)
    if 'data' not in r or not r['data']['__type'] or not r['data']['__type'].get('fields'):
        return {}
    out = {}
    for f in r['data']['__type']['fields']:
        t = f['type']
        nm = t.get('name') or (t.get('ofType') or {}).get('name') or (((t.get('ofType') or {}).get('ofType') or {}).get('name'))
        out[f['name']] = nm
    return out

# 敏感关键词:引用其它报告或 dup/original 语义
KEYS = re.compile(r'(original|duplicate|dup|related|source|reference|referenc|origin|link|merged|merge|supersed|parent|child|cross|collab)', re.I)

targets = {
    'Report': None,
    'ReportActivityInterface': None,
    'ActivityInterface': None,
}
# 已知 Activity/Report 相关类型名(从 bundle union 记忆)
known = ['Activity', 'ActivitiesBugClosed', 'ActivitiesBugDuplicate', 'ActivitiesBugStateChange',
         'ActivitiesBugAssignedToTeam', 'ActivitiesBountyAwarded', 'ActivitiesBountySuggested',
         'ActivitiesCommentPosted', 'ActivitiesCustomUserUpdated', 'ActivitiesExternalUserMentioned',
         'ActivitiesGroupAssigned', 'ActivitiesInvitationAccepted', 'ActivitiesMediationRequested',
         'ActivitiesReportRetestStarted', 'ActivitiesReportRetestPassed', 'ActivitiesReportRetestFailed',
         'ActivitiesTeamChange', 'ActivitiesUserBanned', 'ReportIntent', 'Notification',
         'ReportDuplicateInformation', 'ReportRetest', 'ReportMediationRequest', 'ReportCollaborator',
         'ActivitiesReportTriaged', 'ActivitiesReportNeedsMoreInfo', 'ActivitiesReportDisclosureScheduled']
# 补 introspection 发现 union 成员
for uname in ['ActivityUnion', 'ReportActivityUnion']:
    r = gql(f'query{{ __type(name: "{uname}") {{ possibleTypes {{ name }} }} }}')
    if r.get('data', {}).get('__type'):
        for pt in r['data']['__type']['possibleTypes']:
            known.append(pt['name'])
known = list(dict.fromkeys(known))

print('=== 类型字段扫描(敏感字段名) ===')
found = {}
for tn in known:
    flds = type_fields(tn)
    if not flds:
        continue
    hits = [(f, t) for f, t in flds.items() if KEYS.search(f) or KEYS.search(t or '')]
    if hits:
        print(f'\n## {tn}')
        for f, t in hits:
            print(f'   {f}: {t}')
        found[tn] = hits

print('\n=== 汇总(去重) ===')
allf = {}
for tn, hits in found.items():
    for f, t in hits:
        allf.setdefault(f, set()).add(tn)
for f in sorted(allf):
    print(f'{f}: {sorted(allf[f])}')

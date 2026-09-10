# -*- coding: utf-8 -*-
"""h1x53v: introspection ReportMetadata + 相关新类型全字段(ReportMetadata/ExtractedReportData/HaiReportData/ReportGeneratedContent/AveAgentCheck)"""
import json, sys, io, urllib.request
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

def dump(tn):
    q = ('query{ __type(name: "%s") { kind fields { name type { kind name ofType { kind name ofType { name } } } } } }' % tn)
    r = gql(q)
    t = r.get('data', {}).get('__type')
    print('=== %s (%s)' % (tn, t.get('kind') if t else 'NULL'))
    if not t or not t.get('fields'):
        print('   (no fields / not found)')
        return
    for f in t['fields']:
        ty = f['type']
        nm = ty.get('name') or (ty.get('ofType') or {}).get('name') or (((ty.get('ofType') or {}).get('ofType') or {}).get('name'))
        print('   %s: %s' % (f['name'], nm))

for tn in ['ReportMetadata', 'ExtractedReportData', 'HaiReportData', 'ReportGeneratedContent', 'AveAgentCheck', 'DeduplicationActionRecommendation', 'DeduplicationRecommendation', 'DupeWindow']:
    dump(tn)

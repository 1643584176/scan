# -*- coding: utf-8 -*-
"""下载关键 chunk 并提取 API 端点:
- ProvisionedInstances* (新资源类型)
- OrgPeople / OrgSettings (org 成员管理)
- CreateObservabilityConfigPage / useObservabilityDefaultConfig / useWorkspaceInsightsSummary
- ProjectSettingsTabbed / ProjectDataAPI / AddJWKSModal
- OrgIntegrations / UserIntegrations
"""
import http.client, ssl, re, os, sys, json

ctx = ssl.create_default_context()
here = os.path.dirname(os.path.abspath(__file__))
outdir = os.path.join(here, '_js', 'prod_chunks')
os.makedirs(outdir, exist_ok=True)

FILES = [
    'ProvisionedInstancesList-CTp5c_4X.js', 'ProvisionedInstancesItem-B_EULg7j.js',
    'ProvisionedInstancesItemRoles-BFeEbS-M.js', 'ProvisionedInstancesItemPermissions-D0kxYUw1.js',
    'ProvisionedInstancesItemCatalogs-0DPn8ML0.js', 'ProvisionedInstancesItemMonitoring-SlFXV9A7.js',
    'CreateOrEditProvisionedInstanceModal-RFT4nmPC.js', 'useCurrentProvisionedInstance-BkyxKEkQ.js',
    'OrgPeople-AJkGkV8O.js', 'OrgSettings-D_4JnzeS.js',
    'CreateObservabilityConfigPage-BapbJ9q3.js', 'useObservabilityDefaultConfig-BYYLakXu.js',
    'useWorkspaceInsightsSummary-DPC8cJpd.js', 'WorkspaceInsightItemPage-BoEXbhuA.js',
    'ProjectSettingsTabbed-ECm22iEn.js', 'ProjectDataAPI-Drs23Zcc.js', 'AddJWKSModal-BlsLOnmF.js',
    'OrgIntegrations-T3EVEqI6.js', 'UserIntegrations-t2w54Wbb.js', 'ProjectGeniePage-Le_jcnkx.js',
    'useAIGatewayAccess-DRMEumu5.js', 'ProjectInsightsTab-Tbbvi_xZ.js', 'useInsightTelemetry-PbOQ0ibW.js',
    'TransferProjectSelectOrgModal-DiCQ8KKy.js', 'TransferProjectsSelectOrgModal-6k6IVRo5.js',
    'InsightsExplorer-13R9AnEe.js', 'Insights-mknIqQ3B.js', 'ProjectAdvisorsTab-CODzdtcK.js',
]
conn_pool = {}
def fetch(name):
    try:
        conn = http.client.HTTPSConnection('dfv3qgd2ykmrx.cloudfront.net', context=ctx, timeout=30)
        conn.request('GET', '/assets/' + name, headers={'User-Agent': 'Mozilla/5.0'})
        r = conn.getresponse()
        raw = r.read()
        conn.close()
        return r.status, raw
    except Exception as e:
        return -1, str(e).encode()

allsrc = {}
for f in FILES:
    st, raw = fetch(f)
    if st == 200:
        p = os.path.join(outdir, f)
        open(p, 'wb').write(raw)
        allsrc[f] = raw.decode('utf-8', 'replace')
        print('OK %s (%d)' % (f, len(raw)), flush=True)
    else:
        print('FAIL %s -> %d' % (f, st), flush=True)

# 端点提取(全部源合并)
merged = '\n'.join(allsrc.values())
print('\nmerged size:', len(merged), flush=True)
urls = set()
for m in re.finditer(r'["\'`]((?:/api|/ajax-api)[A-Za-z0-9_.${}/-]{2,150})["\'`]', merged):
    urls.add(m.group(1))
print('\n=== /api 端点 ===', flush=True)
for s in sorted(urls):
    print(s[:170], flush=True)

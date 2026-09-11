# -*- coding: utf-8 -*-
# q75: 差集端点「词级核对」——特征词在历史脚本里的真实出现情况
import sys, io, glob, os, re
sys.stdout = io.TextIOWrapper(sys.stdout.buffer, encoding='utf-8', errors='replace')

D = r'D:\scan\figma_report'
files = glob.glob(os.path.join(D, '_*.py'))
texts = {}
for f in files:
    try:
        texts[os.path.basename(f)] = open(f, encoding='utf-8', errors='replace').read()
    except Exception:
        pass
print(f'扫描脚本: {len(texts)} 个')

# 差集端点的特征词（排除 auth/session 登录面）
words = [
    'audios', 'videos', 'thumbnails', 'last_interaction', 'page_thumbnails',
    'realtime_token', 'reference_id', 'source_file_updated_info',
    'ancestor_folders', 'can_move', 'can_move_files', 'contributors',
    'inheritance', 'deletion_file_count', 'num_backfilled_team_user',
    'has_published_site', 'subscription_status', 'team_name', 'segments',
    'deletion_impact', 'scim_provisioned_status', 'figment-proxy',
    'org_saml_config_required', 'statsig', 'folders/rename',
    'folders/restore', 'folders/trash', 'redeem_magic_link',
]
print('\n=== 词级核对（脚本内出现次数）===')
for w in words:
    cnt = 0
    sample = ''
    for fn, t in texts.items():
        c = t.count(w)
        if c:
            cnt += c
            if not sample:
                i = t.find(w)
                sample = f'{fn}: ...{t[max(0,i-60):i+60]}...'.replace('\n', ' ')
    flag = '**真空白**' if cnt == 0 else ''
    print(f'{w:32s} {cnt:5d}  {flag}')
    if sample and cnt < 400:
        print(f'    {sample[:170]}')
print('DONE q75')

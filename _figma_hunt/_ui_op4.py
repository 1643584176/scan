# -*- coding: utf-8 -*-
import io, sys, json
import urllib.request
sys.stdout.reconfigure(encoding='utf-8', errors='replace')
raw=io.open('ws_cookie_A_new.txt',encoding='utf-8').read().strip().replace('\n','; ')
url='https://www.figma.com/api/design_systems/library/bv2nMIdFf4u3dESGail4sm/published_components?include_thumbnail=false&include_realtime=false'
req=urllib.request.Request(url, headers={'Cookie':raw, 'User-Agent':'Mozilla/5.0'})
try:
    data=json.loads(urllib.request.urlopen(req, timeout=20).read())
    f=data.get('meta',{}).get('file',{})
    print('file key:', f.get('key'))
    print('creator_id:', f.get('creator_id'))
    print('team_id:', f.get('team_id'))
    print('parent_org_id:', f.get('parent_org_id'))
    print('link_access:', f.get('link_access'))
    print('editable:', f.get('editable'))
    print('components:', len(data.get('meta',{}).get('components',[])))
except Exception as e:
    print('ERR:', str(e)[:200])
# 用户身份
try:
    req2=urllib.request.Request('https://www.figma.com/api/users/me', headers={'Cookie':raw, 'User-Agent':'Mozilla/5.0'})
    me=json.loads(urllib.request.urlopen(req2, timeout=20).read())
    m=me.get('meta',{})
    print('me:', m.get('id'), m.get('handle'), m.get('email'))
except Exception as e:
    print('me ERR:', str(e)[:150])

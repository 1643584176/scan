# -*- coding: utf-8 -*-
import io, sys, json
import urllib.request
sys.stdout.reconfigure(encoding='utf-8', errors='replace')
raw=io.open('ws_cookie_A_new.txt',encoding='utf-8').read().strip().replace('\n','; ')
def get(url):
    req=urllib.request.Request(url, headers={'Cookie':raw,'User-Agent':'Mozilla/5.0'})
    return json.loads(urllib.request.urlopen(req, timeout=30).read())
# 1) 文件节点树(截断)
try:
    d=get('https://www.figma.com/api/files/bv2nMIdFf4u3dESGail4sm')
    print('FILES keys:', list(d.keys())[:10])
    doc=d.get('meta',{}).get('document',{})
    def walk(n, depth, out):
        if depth>3: return
        t=n.get('type',''); nm=n.get('name','')[:40]
        if t in ('COMPONENT','COMPONENT_SET'):
            out.append({'id':n.get('id'),'type':t,'name':nm})
        for c in n.get('children',[]):
            walk(c, depth+1, out)
    comps=[]; walk(doc,0,comps)
    print('COMPONENTS found:', len(comps))
    for c in comps[:10]: print(' ', c)
    # 顶层页面
    pages=[{'id':p.get('id'),'name':p.get('name')} for p in doc.get('children',[])]
    print('PAGES:', pages[:8])
except Exception as e:
    print('files ERR:', str(e)[:200])
# 2) library key 确认
try:
    d2=get('https://www.figma.com/api/design_systems/library/bv2nMIdFf4u3dESGail4sm/published_components?include_thumbnail=false&include_realtime=false')
    meta=d2.get('meta',{})
    print('library:', {k:meta.get(k) for k in ('library_key','library_name','team_id') if k in meta})
except Exception as e:
    print('lib ERR:', str(e)[:150])

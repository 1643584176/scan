# -*- coding: utf-8 -*-
import io, sys, json
import urllib.request
sys.stdout.reconfigure(encoding='utf-8', errors='replace')
raw=io.open('ws_cookie_A_new.txt',encoding='utf-8').read().strip().replace('\n','; ')
def get(url):
    req=urllib.request.Request(url, headers={'Cookie':raw,'User-Agent':'Mozilla/5.0'})
    return json.loads(urllib.request.urlopen(req, timeout=30).read())
try:
    d=get('https://www.figma.com/api/files/bv2nMIdFf4u3dESGail4sm')
    print('ERROR resp:', json.dumps(d)[:300])
except Exception as e:
    print('files ERR:', str(e)[:200])
try:
    d2=get('https://www.figma.com/api/design_systems/library/bv2nMIdFf4u3dESGail4sm/published_components?include_thumbnail=false&include_realtime=false')
    print('FULL:', json.dumps(d2)[:600])
except Exception as e:
    print('lib ERR:', str(e)[:150])

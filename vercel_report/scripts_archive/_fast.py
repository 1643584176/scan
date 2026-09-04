# -*- coding: utf-8 -*-
p = r'D:\scan\_run_v57.py'
s = open(p, encoding='utf-8').read()
s = s.replace("    time.sleep(5)\n    c, r = cmdsh('mkdir", "    time.sleep(2)\n    c, r = cmdsh('mkdir")
s = s.replace("    t0 = time.time()\n    state = None\n    while time.time() - t0 < 90:\n        time.sleep(3)",
              "    t0 = time.time()\n    state = None\n    while time.time() - t0 < 40:\n        time.sleep(1)")
s = s.replace("    time.sleep(3)\n    c, r = api('GET', '/v2/sandboxes/%s?teamId=%s&projectId=%s&resume=true'",
              "    time.sleep(1)\n    c, r = api('GET', '/v2/sandboxes/%s?teamId=%s&projectId=%s&resume=true'")
s = s.replace("    time.sleep(3)\n\n    c, r = api('POST', '/v2/sandboxes/sessions/%s/cmd?teamId=%s' % (sid, TEAM),",
              "    time.sleep(1)\n\n    c, r = api('POST', '/v2/sandboxes/sessions/%s/cmd?teamId=%s' % (sid, TEAM),")
open(p, 'w', encoding='utf-8').write(s)
print('patched fast mode')

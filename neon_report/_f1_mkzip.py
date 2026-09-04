# -*- coding: utf-8 -*-
"""生成 kf1.zip(根目录 index.mjs dump env names)供 curl 上传"""
import io, zipfile
code = r'''export default {
  async fetch(request) {
    const names = Object.keys(process.env).sort();
    return new Response(JSON.stringify({ env_names: names }, null, 1), {
      headers: { 'content-type': 'application/json' },
    });
  }
};
'''
with zipfile.ZipFile(r'D:\scan\neon_report\_f1.zip', 'w', zipfile.ZIP_DEFLATED) as z:
    z.writestr('index.mjs', code)
print('written')

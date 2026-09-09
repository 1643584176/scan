# -*- coding: utf-8 -*-
"""浏览器块 AP:email 防护覆盖面测试"""
print('''
(async () => {
  const sleep = ms => new Promise(r => setTimeout(r, ms));
  const csrf = document.querySelector('meta[name="csrf-token"]').content;
  const out = [];

  const gql = async (label, q) => {
    const r = await fetch('/graphql', {
      method: 'POST',
      headers: { 'Content-Type': 'application/json', 'X-CSRF-Token': csrf },
      body: JSON.stringify({ query: q })
    });
    out.push('===== ' + label + '\\n' + JSON.stringify(await r.json()).slice(0, 2000));
  };

  // AP1: User 类型所有 email/contact/token 类字段名
  await gql('AP1 user fields', `{
    a: __type(name: "User") { fields { name } }
  }`);

  const ta = document.createElement('textarea');
  ta.style.cssText = 'position:fixed;top:0;left:0;width:97%;height:92%;z-index:999999;font:10px monospace;white-space:pre;';
  ta.value = out.join('\\n\\n');
  document.body.appendChild(ta);
  ta.focus(); ta.select();
})();
''')

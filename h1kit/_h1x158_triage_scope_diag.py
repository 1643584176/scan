# -*- coding: utf-8 -*-
"""浏览器块 x158:triage_scope 固定集合身份判别 + 慢路径稳定性"""
print('''
(async () => {
  const sleep = ms => new Promise(r => setTimeout(r, ms));
  const csrf = document.querySelector('meta[name="csrf-token"]').content;
  const out = [];
  const gql = async (label, q) => {
    const t0 = Date.now();
    const r = await fetch('/graphql', {
      method: 'POST',
      headers: { 'Content-Type': 'application/json', 'X-CSRF-Token': csrf },
      body: JSON.stringify({ query: q })
    });
    const ms = Date.now() - t0;
    out.push('===== ' + label + ' (' + ms + 'ms)\\n' + JSON.stringify(await r.json()).slice(0, 3500));
    await sleep(400);
  };
  // U1: User 全字段(找 system/employee 定性字段)
  await gql('U1 User fields', `{ __type(name: "User") { fields { name } } }`);
  // U2: triage_scope 固定集前20 + system 标记
  await gql('U2 triage_scope full', `{ users(first: 20, where: { triage_scope: "zzz" }) { edges { node { username system } } } }`);
  // U3: 空串对照(是否也走慢路径)
  await gql('U3 triage_scope empty-str', `{ users(first: 5, where: { triage_scope: "" }) { edges { node { username } } } }`);
  // U4: 换值复测计时(确认稳定慢)
  await gql('U4 triage_scope abc', `{ users(first: 5, where: { triage_scope: "abc" }) { edges { node { username } } } }`);
  const ta = document.createElement("textarea");
  ta.style.cssText = 'position:fixed;top:0;left:0;width:97%;height:92%;z-index:999999;font:10px monospace;white-space:pre;';
  ta.value = out.join('\\n\\n');
  document.body.appendChild(ta); ta.focus(); ta.select();
})();
''')

# -*- coding: utf-8 -*-
"""浏览器块:conversation 面探索"""
print("paste block:")
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

  // AA1: ConversationUnion 成员 + conversation 参数类型
  await gql('AA1 conv types', `{
    a: __type(name: "ConversationUnion") { possibleTypes { name } }
    b: __type(name: "Query") { fields { name args { name type { kind name ofType { kind name } } } } }
  }`);
  await sleep(400);

  // AA2: conversation(id: 1) 数字小 id
  await gql('AA2 conv id 1', `{ conversation(id: 1) { __typename } }`);
  await sleep(400);

  // AA3: report_retest_user 用自己活动 id
  await gql('AA3 retest', `{ report_retest_user(activity_id: 44070787) { __typename } }`);

  const ta = document.createElement('textarea');
  ta.style.cssText = 'position:fixed;top:0;left:0;width:97%;height:92%;z-index:999999;font:10px monospace;white-space:pre;';
  ta.value = out.join('\\n\\n');
  document.body.appendChild(ta);
  ta.focus(); ta.select();
})();
''')

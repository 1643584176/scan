# -*- coding: utf-8 -*-
"""浏览器块 AN:claim credential 面探索"""
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
    out.push('===== ' + label + '\\n' + JSON.stringify(await r.json()).slice(0, 1800));
  };

  // AN1: Vercel Sandbox team 的 structured scopes(读)
  await gql('AN1 vercel scopes', `{
    team(handle: "vercel_sandbox") {
      id handle
      structured_scopes(first: 10) { edges { node { id asset_identifier eligibility } } }
    }
  }`);
  await sleep(400);

  // AN2: 匿名接受邀请-假 token(看错误差异)
  await gql('AN2 accept fake', `mutation {
    anonymouslyAcceptForwardedEmailInvitation(input: { token: "fake_token_abc", email: "1643584176@qq.com" }) { was_successful errors { edges { node { message field } } } }
  }`);
  await sleep(400);

  // AN3: SendMarkdownEmail 发自己邮箱(权限试探,零第三方影响)
  await gql('AN3 send mail self', `mutation {
    sendMarkdownEmail(input: { markdown_content: "test", subject: "test", email: "1643584176@qq.com" }) { was_successful errors { edges { node { message field } } } }
  }`);

  const ta = document.createElement('textarea');
  ta.style.cssText = 'position:fixed;top:0;left:0;width:97%;height:92%;z-index:999999;font:10px monospace;white-space:pre;';
  ta.value = out.join('\\n\\n');
  document.body.appendChild(ta);
  ta.focus(); ta.select();
})();
''')

# -*- coding: utf-8 -*-
"""x149: 判别性凭证扫描块生成器
对 447 handles 扫 scope: counts + claimed_credential(user 身份)
输出: 命中行(avail/claimed/revoked>0 或 claimed_credential 非 null) + StructuredScope 字段表"""
import json

hs = json.load(open('D:/scan/h1kit/_h1x148_handles.json', encoding='utf-8'))
chunks = [hs[i:i + 3] for i in range(0, len(hs), 3)]

L = []
L.append('(async () => {')
L.append('  const sleep = ms => new Promise(r => setTimeout(r, ms));')
L.append("  const csrf = document.querySelector('meta[name=\"csrf-token\"]').content;")
L.append('  const out = [];')
L.append('  const gql = async (label, q) => {')
L.append('    const r = await fetch("/graphql", {')
L.append("      method: 'POST', headers: { 'Content-Type': 'application/json', 'X-CSRF-Token': csrf },")
L.append('      body: JSON.stringify({ query: q })')
L.append('    });')
L.append('    out.push("===== " + label + "\\n" + JSON.stringify(await r.json()).slice(0, 3000));')
L.append('  };')
# 0. StructuredScope 全字段(含 deprecated) — 自包含,免贴 BF1
L.append("  await gql('SCOPE FIELDS', `{ __type(name: \"StructuredScope\") { fields { name isDeprecated } } }`);")
L.append('  await sleep(300);')
# 1. 判别扫描
L.append('  const hits = [];')
L.append('  const q = async (handle) => {')
L.append('    const r = await fetch("/graphql", {')
L.append("      method: 'POST', headers: { 'Content-Type': 'application/json', 'X-CSRF-Token': csrf },")
L.append('      body: JSON.stringify({ query: `{ team(handle: "${handle}") { structured_scopes { edges { node {')
L.append('        id asset_identifier credentials_available_count credentials_claimed_count credentials_revoked_count')
L.append('        claimed_credential { id revoked claimed_at user { username } }')
L.append('      } } } } }` })')
L.append('    });')
L.append('    const j = await r.json();')
L.append('    const sc = j?.data?.team?.structured_scopes?.edges || [];')
L.append('    for (const e of sc) {')
L.append('      const n = e.node;')
L.append('      const cc = n.claimed_credential;')
L.append('      if (n.credentials_available_count > 0 || n.credentials_claimed_count > 0 || n.credentials_revoked_count > 0 || cc)')
L.append('        hits.push(handle + " | " + n.asset_identifier + " | avail=" + n.credentials_available_count')
L.append('          + " claimed=" + n.credentials_claimed_count + " revoked=" + n.credentials_revoked_count')
L.append('          + " | claimUser=" + (cc ? (cc.user ? cc.user.username : "null-user") + " id=" + cc.id + " revoked=" + cc.revoked + " at=" + cc.claimed_at : "null"));')
L.append('    }')
L.append('  };')
for i, c in enumerate(chunks):
    parts = []
    for h in c:
        parts.append('await q(%r)' % h)
    L.append('  try { ' + '; '.join(parts) + '; } catch (e) {}')
    L.append('  await sleep(160);')
L.append('  const ta = document.createElement("textarea");')
L.append("  ta.style.cssText = 'position:fixed;top:0;left:0;width:97%;height:92%;z-index:999999;font:10px monospace;white-space:pre;';")
L.append("  ta.value = out.join('\\n\\n') + '\\n\\n##### HITS (' + hits.length + '):\\n' + hits.join('\\n') + '\\n\\n(empty = no scope has credentials/claims)';")
L.append('  document.body.appendChild(ta); ta.focus(); ta.select();')
L.append('})();')

block = '\n'.join(L)
open('D:/scan/h1kit/_h1x149_scan_block.txt', 'w', encoding='utf-8').write(block)
print('block lines:', len(L), '| chunk count:', len(chunks))
print(block[:400])

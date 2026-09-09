import{o as e}from"./rolldown-runtime-DAXXjFlN.js";import{Fw as t,Kx as n,Lr as r,Rw as i,qx as a,zx as o}from"./vendor-_WdvpBLr.js";import{Ah as s,Gn as c,T as l,Th as u,_h as d,ba as f,fm as p,k as m,lh as h,qr as g,sm as _,vh as v,vm as y,ym as b}from"./app-5pKgUmmm.js";var x=e(i()),S=e(o());a();var C=t(),w=n`
  query TeamGenii($handle: String!) {
    team(handle: $handle) {
      id
      remediation_guidance_enabled
      team_genii {
        edges {
          node {
            id
            name
            description
            muted
          }
        }
      }
    }
  }
`,T=n`
  mutation UpdateTeamGenius($team_genius_id: ID!, $muted: Boolean!) {
    updateTeamGenius(
      input: { team_genius_id: $team_genius_id, muted: $muted }
    ) {
      was_successful
      team_genius {
        id
        muted
      }
    }
  }
`,E=n`
  mutation UpdateRemediationGuidance($team_id: ID!, $disabled: Boolean!) {
    updateRemediationGuidance(
      input: { team_id: $team_id, disabled: $disabled }
    ) {
      was_successful
      team {
        id
        remediation_guidance_enabled
      }
    }
  }
`,D=e=>{let t=e.match.params.handle,{data:n,loading:i}=v(w,{variables:{handle:t}}),[a]=d(T,{onCompleted:e=>e.updateTeamGenius.was_successful?b():y()}),[o]=d(E,{onCompleted:e=>e.updateRemediationGuidance.was_successful?b():y()}),S=(e,t)=>a({variables:{team_genius_id:e.id,muted:t},optimisticResponse:{updateTeamGenius:{__typename:`UpdateTeamGeniusPayload`,was_successful:!0,team_genius:{__typename:`TeamGenius`,id:e.id,muted:t}}}}),D=(e,t)=>o({variables:{team_id:e.id,disabled:t},optimisticResponse:{updateRemediationGuidance:{__typename:`UpdateRemediationGuidancePayload`,was_successful:!0,team:{__typename:`Team`,id:e.id,remediation_guidance_enabled:!t}}}});if(i)return(0,C.jsx)(u,{});let{team_genii:O}=n.team;return(0,C.jsx)(g,{children:(0,C.jsx)(l,{header:(0,C.jsx)(m,{...e}),content:(0,C.jsxs)(`div`,{children:[(0,C.jsx)(r,{children:(0,C.jsx)(`title`,{children:f(`Hackbot settings`)})}),(0,C.jsxs)(`div`,{children:[(0,C.jsxs)(`div`,{className:`settings-title-container`,children:[(0,C.jsx)(`h3`,{className:`daisy-h3`,children:`Hackbot`}),(0,C.jsx)(`p`,{className:`daisy-text`,children:`Enable or disable actions done/suggested by HackerOne Hackbot`})]}),(0,C.jsxs)(`div`,{children:[O.edges.map(e=>(0,C.jsxs)(x.default.Fragment,{children:[(0,C.jsxs)(h,{flexDirection:`row`,justifyContent:`space-between`,alignItems:`center`,children:[(0,C.jsxs)(`div`,{children:[e.node.name,(0,C.jsx)(p,{className:`margin-8--right`,children:e.node.description})]}),(0,C.jsx)(`div`,{children:(0,C.jsx)(c,{checked:!e.node.muted,onChange:t=>S(e.node,!t.target.checked)})})]}),(0,C.jsx)(_,{size:`extra-small`})]},e.node.id)),(0,C.jsxs)(C.Fragment,{children:[(0,C.jsxs)(h,{flexDirection:`row`,justifyContent:`space-between`,alignItems:`center`,children:[(0,C.jsxs)(`div`,{children:[`Suggest remediation`,(0,C.jsx)(p,{className:`margin-8--right`,children:`Hackbot will suggest remediation guidance from MITRE based on the report weakness`})]}),(0,C.jsx)(`div`,{children:(0,C.jsx)(c,{className:`spec-toggle-remediation-guidance`,checked:n.team.remediation_guidance_enabled,onChange:e=>D(n.team,!e.target.checked)})})]}),(0,C.jsx)(_,{size:`extra-small`})]})]})]})]}),footer:(0,C.jsx)(s,{})})})};D.propTypes={match:S.default.shape({params:S.default.shape({handle:S.default.string.isRequired}).isRequired}).isRequired};export{D as default};
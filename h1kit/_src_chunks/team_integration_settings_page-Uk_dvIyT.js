import{o as e}from"./rolldown-runtime-DAXXjFlN.js";import{Fw as t,Kx as n,Lr as r,Px as i,Rw as a,Vf as o,gw as s,qx as c,zx as l}from"./vendor-_WdvpBLr.js";import{Ah as u,Nn as d,Pn as f,Sd as p,Sm as m,T as h,Th as g,ba as _,dh as v,ff as y,k as b,lh as x,qr as S,rp as C,vh as w,x as T}from"./app-5pKgUmmm.js";import{t as E}from"./integration_images-SAmnRkzI.js";var D=e(a()),O=e(s()),k=e(o()),A=e(l()),j=t(),M=({name:e,integration_key:t,teamHandle:n,link:r,className:i})=>(0,j.jsxs)(p.Row,{className:`spec-static-integration`,children:[(0,j.jsxs)(p.Cell,{children:[(0,j.jsx)(`img`,{className:`integration__image`,src:E[t]}),(0,j.jsx)(`h2`,{className:`integration__name`,children:e})]}),(0,j.jsx)(p.Cell,{children:(0,j.jsx)(d.Context,{name:constants.gates.all.url_issue_tracker,teamHandle:n,children:(0,j.jsx)(d.Open,{children:r?(0,j.jsx)(x,{justifyContent:`flex-end`,className:i,children:(0,j.jsx)(v,{to:r,className:`spec-contact-link`,children:`View Documentation`})}):(0,j.jsx)(x,{justifyContent:`flex-end`,className:i,children:(0,j.jsx)(v,{to:window.constants.notification.support_link,className:`spec-contact-link`,children:`Contact Us`})})})})})]});M.propTypes={name:A.default.string.isRequired,integration_key:A.default.string.isRequired,teamHandle:A.default.string,link:A.default.string,className:A.default.string},c();var N=n`
  query BiDirectionalJiraIntegration($handle: String!) {
    team(handle: $handle) {
      id
      handle
      jira_webhook {
        id
        has_received_events
      }
      jira_integration {
        id
      }
      jira_team_integration {
        id
        _id
        active
        has_authentication
        legacy_integration
      }
    }
  }
`,P=({match:e,name:t,integration_key:n,link:r})=>{let{handle:i}=e.params,[a,o]=(0,D.useState)(!1),{data:s,loading:c}=w(N,{variables:{handle:i}});if(c)return(0,j.jsx)(p.Row,{children:(0,j.jsx)(p.Cell,{children:(0,j.jsx)(g,{})})});let{team:l}=s;if((0,O.default)(l,`jira_team_integration.legacy_integration`))return null;let{hasSomeConfiguration:u,hasBiDirectionalJiraConfigured:f}=T(l,null);if(!u)return(0,j.jsx)(M,{name:t,integration_key:n,teamHandle:l.handle,link:r,className:`spec-jira-integration`});let m=e=>{e.preventDefault(),o(!a)};return(0,j.jsxs)(p.Row,{className:`spec-hackerone-to-jira-integration`,children:[(0,j.jsxs)(p.Cell,{children:[(0,j.jsx)(`img`,{className:`integration__image`,src:E.jira}),(0,j.jsx)(`h2`,{className:`integration__name`,children:`Jira`})]}),(0,j.jsx)(p.Cell,{children:(0,j.jsx)(d.Context,{name:constants.gates.all.url_issue_tracker,teamHandle:l.handle,children:(0,j.jsxs)(d.Open,{children:[(0,j.jsx)(x,{justifyContent:`flex-end`,children:u&&f?(0,j.jsx)(v,{to:`/${l.handle}/bi_directional_jira_integrations`,children:`Edit`}):(0,j.jsx)(v,{to:`#`,onClick:m,children:`Connect with Jira`})}),a&&(0,j.jsxs)(C,{size:`medium`,onCloseModal:m,children:[(0,j.jsx)(`h2`,{className:`text-aligned-center`,children:`Which version of Jira are you using?`}),(0,j.jsxs)(`div`,{className:`integration__jira`,children:[(0,j.jsx)(v,{to:`https://marketplace.atlassian.com/1217001`,className:`integration__jira__version`,external:!0,children:`Jira Cloud`}),(0,j.jsx)(v,{className:`integration__jira__version`,to:`/${l.handle}/bi_directional_jira_integrations`,external:!0,children:`Jira Server`}),(0,j.jsx)(`div`,{className:`clearfix`})]})]})]})})})]})};P.propTypes={match:A.default.shape({params:A.default.shape({handle:A.default.string.isRequired})}).isRequired,name:A.default.string.isRequired,integration_key:A.default.string.isRequired,link:A.default.string.isRequired},c();var F=n`
  query SlackIntegrationQuery($handle: String!) {
    team(handle: $handle) {
      id
      handle
      slack_integration {
        id
      }
    }
  }
`,I=e=>{let{handle:t}=e.match.params,{data:n,loading:r}=w(F,{variables:{handle:t}});if(r)return(0,j.jsx)(p.Row,{children:(0,j.jsx)(p.Cell,{children:(0,j.jsx)(g,{})})});let{team:i}=n,a=i.slack_integration&&i.slack_integration.id;return(0,j.jsxs)(p.Row,{className:`spec-self-integration`,children:[(0,j.jsxs)(p.Cell,{children:[(0,j.jsx)(`img`,{className:`integration__image`,src:E.slack}),(0,j.jsx)(`h2`,{className:`integration__name`,children:`Slack`})]}),(0,j.jsx)(p.Cell,{children:(0,j.jsx)(d.Context,{name:constants.gates.all.url_issue_tracker,teamHandle:i.handle,children:(0,j.jsx)(d.Open,{children:(0,j.jsx)(x,{justifyContent:`flex-end`,children:(0,j.jsx)(v,{to:`/${i.handle}/slack_integration`,className:`spec-slack-integration-link`,children:a?`Edit`:`Connect with Slack`})})})})})]})};I.propTypes={match:A.default.shape({params:A.default.shape({handle:A.default.string.isRequired})}).isRequired},c();var L=n`
  query SfdcAgileAcceleratorIntegrationQuery($handle: String!) {
    team(handle: $handle) {
      id
      handle
      agile_accelerator_integration {
        id
      }
      agile_accelerator_integration_enabled
    }
  }
`,R=e=>{let{handle:t}=e.match.params,{data:n,loading:r}=w(L,{variables:{handle:t}});if(r)return(0,j.jsx)(p.Row,{children:(0,j.jsx)(p.Cell,{children:(0,j.jsx)(g,{})})});let{team:i}=n;if(!i.agile_accelerator_integration_enabled)return null;let a=i.agile_accelerator_integration&&i.agile_accelerator_integration.id;return(0,j.jsxs)(p.Row,{className:`spec-agile-accelerator-integration`,children:[(0,j.jsxs)(p.Cell,{width:`280px`,children:[(0,j.jsx)(`img`,{className:`integration__image`,src:E.agile_accelerator}),(0,j.jsx)(`h2`,{className:`integration__name`,children:`Agile Accelerator`})]}),(0,j.jsx)(p.Cell,{className:`text-aligned-right`,children:(0,j.jsx)(v,{to:`/${i.handle}/sfdc_agile_accelerator_settings`,children:a?`Edit`:`Connect with Agile Accelerator`})})]})};R.propTypes={match:A.default.shape({params:A.default.shape({handle:A.default.string.isRequired})}).isRequired};var z=({handle:e,solution_id:t,name:n,active:r})=>(0,j.jsx)(v,{to:`/${e}/integrations/${encodeURIComponent(t)}`,children:r?`Edit`:`Connect with ${n}`});z.propTypes={handle:A.default.string.isRequired,solution_id:A.default.string.isRequired,name:A.default.string.isRequired,active:A.default.bool.isRequired},c();var B=n`
  query SlackIntegrationQuery($handle: String!) {
    team(handle: $handle) {
      id
      handle
      slack_integration {
        id
      }
    }
  }
`,V=({handle:e,solution_id:t,name:n,active:r})=>{let{SLACK_MIGRATION:i}=window.constants.featureToggles||{},{enabled:a}=y(i,e),{data:o,loading:s}=w(B,{variables:{handle:e},skip:!a}),c=a&&o?.team?.slack_integration?.id;return a?s?(0,j.jsx)(g,{size:`small`}):c?(0,j.jsxs)(j.Fragment,{children:[(0,j.jsx)(v,{to:`/${e}/slack_integration`,className:`spec-slack-integration-legacy-link margin-4--right`,children:`Edit Legacy Slack`}),(0,j.jsx)(`span`,{className:`mx-2`,children:`|`}),(0,j.jsx)(v,{to:`/${e}/integrations/${encodeURIComponent(t)}`,className:`spec-slack-integration-new-link margin-4--left`,children:r?`Edit`:`Connect with Slack`})]}):(0,j.jsx)(v,{to:`/${e}/integrations/${encodeURIComponent(t)}`,className:`spec-slack-integration-new-link`,children:r?`Edit`:`Connect with Slack`}):(0,j.jsx)(v,{to:`/${e}/integrations/${encodeURIComponent(t)}`,children:r?`Edit`:`Connect with ${n}`})};V.propTypes={handle:A.default.string.isRequired,solution_id:A.default.string.isRequired,name:A.default.string.isRequired,active:A.default.bool.isRequired};var H={slack:V},U=e=>H[e]||z,W=({match:e,solution_id:t,name:n,integration_key:r,active:i})=>{let{handle:a}=e.params,o=U(r);return(0,j.jsxs)(p.Row,{className:`spec-service-now-integration`,children:[(0,j.jsxs)(p.Cell,{children:[(0,j.jsx)(`img`,{className:`integration__image`,src:E[r]}),(0,j.jsx)(`h2`,{className:`integration__name`,children:n})]}),(0,j.jsx)(p.Cell,{children:(0,j.jsx)(d.Context,{name:constants.gates.all.url_issue_tracker,teamHandle:a,children:(0,j.jsx)(d.Open,{children:(0,j.jsx)(x,{justifyContent:`flex-end`,children:(0,j.jsx)(o,{handle:a,solution_id:t,name:n,active:i})})})})})]})};W.propTypes={match:A.default.shape({params:A.default.shape({handle:A.default.string.isRequired})}).isRequired,history:A.default.object.isRequired,solution_id:A.default.string.isRequired,name:A.default.string.isRequired,integration_key:A.default.string.isRequired,active:A.default.bool.isRequired};var G=i(W);c();var K=`Something went wrong while fetching the integrations.
  Please contact ${window.constants.notification.support_link} if the problem persists.`,q=n`
  query IntegrationsQuery($handle: String!) {
    team(handle: $handle) {
      id
      available_integrations
    }
  }
`,J={agile_accelerator:R,bi_directional_jira:P,generic:M,slack:I,tray:G},Y=({props:e,handle:t,integration:n})=>{let r=J[n.type];return(0,j.jsx)(r,{...e,name:n.name,integration_key:n.key,teamHandle:t,link:n.link,solution_id:n.solution_id,active:n.active})};Y.propTypes={props:A.default.any,handle:A.default.string,integration:A.default.shape({type:A.default.string.isRequired,name:A.default.string.isRequired,key:A.default.string.isRequired,link:A.default.string.isRequired,solution_id:A.default.string,active:A.default.bool}).isRequired};var X=e=>{let{handle:t}=e.match.params,{data:n,loading:r,error:i}=w(q,{variables:{handle:t}});return r?(0,j.jsx)(g,{}):i?m(`error`,K):(0,j.jsxs)(`div`,{children:[(0,j.jsx)(`h3`,{className:`daisy-h3`,children:`Integrations`}),(0,j.jsx)(d.Context,{name:constants.gates.all.url_issue_tracker,teamHandle:t,children:(0,j.jsx)(d.Closed,{children:(0,j.jsx)(f,{})})}),(0,j.jsxs)(`p`,{className:`daisy-text`,children:[`HackerOne integrates with these third party services to streamline your workflow.`,` `,(0,j.jsx)(v,{to:`https://docs.hackerone.com/organizations/supported-integrations.html`,children:`How integration works.`})]}),(0,j.jsx)(`h3`,{className:`daisy-h3`,children:`Issue tracking`}),(0,j.jsx)(p,{fixed:!1,children:(0,j.jsx)(p.Body,{children:(0,k.default)(n.team.available_integrations.issue_tracking,n=>(0,j.jsx)(Y,{props:e,handle:t,integration:n},n.name))})}),(0,j.jsx)(`br`,{}),(0,j.jsx)(`h3`,{className:`daisy-h3`,children:`Notification`}),(0,j.jsx)(p,{fixed:!1,children:(0,j.jsx)(p.Body,{children:(0,k.default)(n.team.available_integrations.notification,n=>(0,j.jsx)(Y,{props:e,handle:t,integration:n},n.name))})}),(0,j.jsx)(`br`,{}),(0,j.jsx)(`h3`,{className:`daisy-h3`,children:`Data Aggregation`}),(0,j.jsx)(p,{fixed:!1,children:(0,j.jsx)(p.Body,{children:(0,k.default)(n.team.available_integrations.data_aggregation,n=>(0,j.jsx)(Y,{props:e,handle:t,integration:n},n.name))})}),(0,j.jsx)(`br`,{}),(0,j.jsx)(`h3`,{className:`daisy-h3`,children:`Vulnerability Management`}),(0,j.jsx)(p,{fixed:!1,children:(0,j.jsx)(p.Body,{children:(0,k.default)(n.team.available_integrations.vulnerability_management,n=>(0,j.jsx)(Y,{props:e,handle:t,integration:n},n.name))})})]})};X.propTypes={match:A.default.shape({params:A.default.shape({handle:A.default.string.isRequired})}).isRequired};var Z=e=>(0,j.jsx)(S,{children:(0,j.jsx)(h,{header:(0,j.jsx)(b,{...e}),content:(0,j.jsxs)(`div`,{children:[(0,j.jsx)(r,{children:(0,j.jsx)(`title`,{children:_(`Integrations`)})}),(0,j.jsx)(X,{...e})]}),footer:(0,j.jsx)(u,{})})});export{Z as default};
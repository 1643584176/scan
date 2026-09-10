import{o as e}from"./rolldown-runtime-DAXXjFlN.js";import{$y as t,Fw as n,Iw as r,Kx as i,Lr as a,Pb as o,Px as s,Qy as c,Rw as l,Vu as u,Vw as d,db as f,ov as p,qx as m,zx as h}from"./vendor-_WdvpBLr.js";import{Ah as g,Bn as _,Dh as v,Gn as y,In as b,Jc as x,Sm as S,T as C,Th as w,_h as T,ba as E,cr as D,dh as O,dr as k,k as ee,qr as te,rp as ne,vh as A,ym as j}from"./app-5pKgUmmm.js";var re=e(d()),M=e(h()),N=e(l()),P=n(),F=`/sample_report_templates.json`,I=({label:e,onSelect:t,focus:n=!0})=>{let[r,i]=(0,N.useState)([]),[a,o]=(0,N.useState)(!0),[s,c]=(0,N.useState)(!1);return(0,N.useEffect)(()=>{let e=!0;return(async()=>{try{let t=await fetch(F,{headers:{Accept:`application/json`}});if(!t.ok)throw Error(`HTTP ${t.status}`);let n=await t.json();if(!e)return;i(Array.isArray(n)?n.map(({title:e,message:t})=>({id:e,title:e,message:t})):[])}catch{e&&c(!0)}finally{e&&o(!1)}})(),()=>{e=!1}},[]),(0,P.jsx)(_,{items:r,label:e,onSelect:t,focus:n,loading:a,emptyMessage:s?`Could not load the sample templates. Please reload the page.`:`No sample templates found.`})},L=({templateText:e,onChange:t,handle:n,history:r})=>(0,P.jsxs)(`div`,{children:[(0,P.jsxs)(`p`,{children:[`You can pre-fill hacker reports with template text of your choosing to ensure that certain information is captured in every report - find out more in the`,` `,(0,P.jsx)(O,{to:`https://docs.hackerone.com/organizations/report-templates.html`,newTab:!0,children:`Document Center`}),`. You can also`,` `,(0,P.jsx)(O,{to:`/${n}/custom_fields`,children:`add hacker facing custom fields`}),` `,`to get more specific insights on this report`]}),(0,P.jsx)(`div`,{className:`input-wrapper`,children:(0,P.jsx)(x,{value:e,name:`report_template_textarea`,textareaId:`report_template_textarea`,minimumHeight:148,onChange:t,maxLength:4e3,helperText:`Limited to 4,000 characters`,renderCommonResponses:({onSelect:e,focus:t,label:n})=>(0,P.jsx)(I,{label:n,onSelect:e,focus:t}),commonResponsesLabel:`Sample Templates`,commonResponseWriteMode:`overwrite`})}),(0,P.jsx)(`div`,{className:`clearfix`})]});L.propTypes={templateText:M.default.string,onChange:M.default.func.isRequired,handle:M.default.string.isRequired,history:M.default.object.isRequired};var ie=s(L),ae=`OWASP Top 10 2013 A`,oe=`OWASP Top 10 Mobile 2016 M`;function R(e){return e.includes(ae)?`- ${e.substring(18)}`:e.includes(oe)?`- ${e.substring(25)}`:e}m();var z=({cluster:e})=>(0,P.jsx)(`div`,{className:`weaknesses__heading`,children:(0,P.jsx)(`div`,{className:`text-truncate`,children:R(e.name)})});z.propTypes={cluster:M.default.shape({name:M.default.string.isRequired}).isRequired},z.fragments={cluster:i`
    fragment Heading on Cluster {
      id
      name
    }
  `};var B=e(r());m();var V=({active:e=!1,cluster:t,onClick:n})=>(0,P.jsxs)(`div`,{className:(0,B.default)(`cluster__item`,`spec-cluster-item`,{"cluster__item--active":e}),children:[(0,P.jsx)(`span`,{className:`cluster__title spec-cluster-title`,onClick:n,children:R(t.name)}),(0,P.jsx)(`span`,{className:`cluster__count meta-text`,children:t.weaknesses.total_count})]});V.propTypes={active:M.default.bool.isRequired,cluster:M.default.object.isRequired,onClick:M.default.func.isRequired},V.fragments={cluster:i`
    fragment Cluster on Cluster {
      id
      name
      weaknesses {
        total_count
      }
    }
  `};var H=e(o());m();var U=i`
  mutation UpdateTeamWeakness(
    $team_weakness_id: ID!
    $state: TeamWeaknessStates!
    $instruction: String!
  ) {
    updateTeamWeakness(
      input: {
        team_weakness_id: $team_weakness_id
        state: $state
        instruction: $instruction
      }
    ) {
      was_successful
      query {
        id
        clusters {
          edges {
            node {
              id
              weaknesses {
                total_count
              }
            }
          }
        }
      }

      team_weakness {
        id
        state
        instruction
      }
    }
  }
`,W=({teamWeakness:e,closeModal:t})=>{let[n,r]=(0,N.useState)(null),[i,a]=(0,N.useState)(e.instruction||``),o=n||e.state,s=o===`disabled`&&(H.default.null(i)||H.default.empty(i)),[c,{loading:l}]=T(U,{onCompleted:()=>{S(`notice`,`Updated team weakness successfully`),t()}}),u=l,d=()=>{c({variables:{team_weakness_id:e.id,state:o,instruction:i||``}})},f=e=>{r(e.target.value)},p=e=>{a(e)},m=(e,t)=>(0,P.jsx)(x,{value:i,name:`weakness_instruction`,textareaId:`weakness_instruction`,label:e,required:t,minimumHeight:70,onChange:p});return(0,P.jsxs)(ne,{onCloseModal:t,children:[(0,P.jsx)(`h2`,{children:`Visibility configuration`}),(0,P.jsxs)(`p`,{children:[e.weakness.name,` `,e.weakness.external_id&&(0,P.jsxs)(P.Fragment,{children:[`(`,e.weakness.external_id.toUpperCase(),`)`]})]}),(0,P.jsx)(b,{checked:o===`enabled`,id:`spec-enable-weakness`,value:`enabled`,helperText:`Shown to hackers and selectable on the submit report page.`,onChange:f,label:`Show`}),(0,P.jsx)(`div`,{className:`help-block help-block--radio-button margin-20--bottom`,children:o===`enabled`?m(`Message to hackers`,!1):null}),(0,P.jsx)(b,{checked:o===`hidden`,value:`hidden`,id:`spec-hide-weakness`,onChange:f,helperText:`Not shown on the submission form.`,label:`Hide`}),(0,P.jsx)(b,{checked:o===`disabled`,value:`disabled`,id:`spec-disable-weakness`,onChange:f,helperText:`Shown to hackers with a contextual message and not selectable on the submit
            report page.`,label:`Disable`}),(0,P.jsx)(b,{checked:o===`unused`,value:`unused`,id:`spec-unused-weakness`,onChange:f,helperText:`No one will be able to tag submissions with this weakness.`,label:`Unused`}),(0,P.jsx)(`div`,{className:`help-block help-block--radio-button`,children:o===`disabled`?m(`Special instruction to hackers`,!0):null}),(0,P.jsxs)(`div`,{className:`modal-footer`,children:[(0,P.jsx)(`a`,{href:``,className:`pull-left`,onClick:t,children:`Cancel`}),u?(0,P.jsx)(`div`,{className:`pull-right`,children:(0,P.jsx)(`button`,{disabled:!0,className:`button button--success`,children:`Saving...`})}):(0,P.jsx)(`div`,{className:`pull-right`,children:(0,P.jsx)(`button`,{disabled:s,className:`button button--success`,onClick:d,children:`Save`})})]})]})};W.propTypes={closeModal:M.default.func.isRequired,teamWeakness:M.default.shape({id:M.default.string.isRequired,instruction:M.default.string,state:M.default.oneOf([`disabled`,`hidden`,`enabled`,`unused`]),weakness:M.default.object.isRequired}).isRequired},W.fragments={teamWeakness:i`
    fragment AdvancedOptionModalTeamWeakness on TeamWeakness {
      id
      state
      instruction
    }
  `},m();var G=({teamWeakness:e})=>{let[t,n]=(0,N.useState)(!1),r=e=>{e&&e.preventDefault(),n(!t)};return(0,P.jsxs)(`ul`,{className:`list list--inline weaknesses__options`,children:[(0,P.jsx)(`li`,{children:(0,P.jsxs)(`span`,{className:(0,B.default)(`spec-weakness-state`,{"text-red":e.state===`disabled`,"text-muted":[`hidden`,`unused`].includes(e.state),"text-green":e.state===`enabled`}),children:[{disabled:`Disabled`,hidden:`Hidden`,enabled:`Shown`,unused:`Unused`}[e.state],H.default.not.existy(e.instruction)||H.default.empty(e.instruction)?null:(0,P.jsx)(`i`,{className:`margin-5--left weakness__icon-message icon-message`})]})}),(0,P.jsx)(`a`,{href:``,onClick:r,children:`Edit`}),t?(0,P.jsx)(W,{closeModal:r,teamWeakness:e}):null]})};G.propTypes={teamWeakness:M.default.shape({state:M.default.oneOf([`disabled`,`hidden`,`enabled`,`unused`]),instruction:M.default.string}).isRequired},G.fragments={teamWeakness:i`
    fragment OptionsTeamWeakness on TeamWeakness {
      id
      state
      instruction
      ...AdvancedOptionModalTeamWeakness
    }
    ${W.fragments.teamWeakness}
  `},m();var K=({teamWeakness:{weakness:e},teamWeakness:t})=>(0,P.jsxs)(`div`,{className:`weaknesses__item`,children:[(0,P.jsx)(G,{teamWeakness:t}),(0,P.jsxs)(`div`,{className:`weaknesses__label`,children:[(0,P.jsx)(`span`,{title:e.name,children:e.name}),e.external_id?(0,P.jsxs)(`span`,{className:`text-muted no-wrap`,children:[` `,`(`,e.external_id.toUpperCase(),`)`]}):null]}),(0,P.jsx)(`div`,{className:`clearfix`})]});K.propTypes={teamWeakness:M.default.shape({weakness:M.default.shape({external_id:M.default.string,name:M.default.string.isRequired}).isRequired}).isRequired},K.fragments={teamWeakness:i`
    fragment WeaknessTeamWeakness on TeamWeakness {
      id
      state
      instruction
      weakness {
        id
        name
        external_id
      }
      ...OptionsTeamWeakness
    }
    ${G.fragments.teamWeakness}
  `};var se=e(u());m();var ce=i`
  query WeaknessesSearch($handle: String!, $searchQuery: String) {
    team(handle: $handle) {
      id
      weaknesses(first: 10, search: $searchQuery) {
        edges {
          node {
            id
            name
            external_id
            clusters(first: 2) {
              edges {
                node {
                  id
                  name
                }
              }
            }
          }
        }
      }
    }
  }
`,q=({onSelect:e,teamHandle:t})=>{let[n,r]=(0,N.useState)(``),[i,a]=(0,N.useState)(``),{data:o,loading:s}=A(ce,{variables:{handle:t,searchQuery:i}}),c=(0,se.default)(e=>{a(e)},250),l=e=>{r(e),c(e)},u=e=>(0,P.jsxs)(`div`,{className:`spec-weakness-suggestion weakness-selector__search__suggestion`,children:[e.node.name,` `,e.node.external_id&&(0,P.jsxs)(P.Fragment,{children:[`(`,e.node.external_id.toUpperCase(),`)`]}),e.node.clusters.edges.map(e=>(0,P.jsxs)(`span`,{children:[` `,(0,P.jsx)(`span`,{className:`label`,children:e.node.name})]},e.node.id))]});if(s&&!o)return(0,P.jsx)(w,{centered:`inContainer`});let{weaknesses:d}=o.team;return(0,P.jsx)(`div`,{className:`weakness-selector__search`,children:(0,P.jsx)(D,{onSelectSuggestion:t=>e(t),placeHolder:`Search`,disabled:!1,renderSuggestion:u,isLoading:s,suggestions:d.edges,onQueryChange:l,query:n,className:`spec-weaknesses-search`,displayOnFocus:!1,searchIcon:!0})})};q.propTypes={onSelect:M.default.func.isRequired,teamHandle:M.default.string.isRequired},m();var le=i`
  query WeaknessClusters($handle: String!) {
    clusters(first: 100) {
      edges {
        node {
          id
          ...Cluster
          ...Heading

          weaknesses {
            edges {
              node {
                id
              }
            }
          }
        }
      }
    }

    teams(where: { handle: { _eq: $handle } }) {
      edges {
        node {
          id
          team_weaknesses(first: 2000) {
            edges {
              node {
                id
                ...WeaknessTeamWeakness
              }
            }
          }
        }
      }
    }
  }

  ${z.fragments.cluster}
  ${V.fragments.cluster}
  ${K.fragments.teamWeakness}
`,J=({teamHandle:e})=>{let[t,n]=(0,N.useState)(null),{data:r,loading:i}=A(le,{variables:{handle:e}}),[a,o]=(0,N.useState)(null),s=e=>{e&&e.preventDefault(),o(null)},c=e=>{n(e)};if(i&&!r)return(0,P.jsx)(w,{});let{clusters:l}=r,u=l.edges.filter(e=>e.node.id===t).map(e=>e.node),d=u.map(e=>e.id),f=i;return(0,P.jsxs)(`div`,{className:`weakness-selector spec-weaknesses`,children:[(0,P.jsx)(q,{onSelect:e=>{o(r.teams.edges[0].node.team_weaknesses.edges.filter(t=>t.node.weakness.id===e.node.id)[0].node)},teamHandle:e}),a&&(0,P.jsx)(W,{closeModal:s,teamWeakness:a}),(0,P.jsxs)(`div`,{className:`weakness-selector__wrapper`,children:[(0,P.jsx)(k,{className:`weakness-selector__clusters`,children:l.edges.map(t=>(0,P.jsx)(V,{active:d.indexOf(t.node.id)!==-1,onClick:()=>c(t.node.id),cluster:t.node,teamHandle:e},t.node.id))}),u.map(t=>(0,P.jsxs)(`div`,{className:`weakness-selector__weaknesses`,children:[(0,P.jsx)(z,{cluster:t,teamHandle:e}),(0,P.jsx)(k,{className:`weaknesses__wrapper`,children:t.weaknesses.edges.map(e=>{let t=r.teams.edges[0].node.team_weaknesses.edges.find(t=>t.node.weakness.id===e.node.id);return t?(0,P.jsx)(K,{teamWeakness:t.node},e.node.id):null})}),f?(0,P.jsx)(w,{overlay:!0}):null]},t.id))]})]})};J.propTypes={teamHandle:M.default.string.isRequired},m();var ue=i`
  mutation UpdateTeamSubmissionState(
    $handle: String!
    $submission_state: SubmissionStateEnum!
  ) {
    updateTeamSubmissionState(
      input: { handle: $handle, submission_state: $submission_state }
    ) {
      was_successful
      team {
        id
        submission_state
      }
    }
  }
`,Y=({team:e})=>{let[t]=T(ue,{onCompleted:j}),{open:n,paused:r}=constants.team.submissionStates,{submission_state:i,is_submission_state_locked:a,is_delinquent:o}=e,s=a=>{a.preventDefault();let o=i===n?r:n;t({variables:{handle:e.handle,submission_state:o},optimisticResponse:{updateTeamSubmissionState:{__typename:`Mutation`,was_successful:!0,team:{...e,submission_state:o}}}})},c=()=>o?`New submissions are currently blocked. Please contact your HackerOne customer representative.`:`Submissions cannot be resumed when reports are failing response SLAs.`,l=i===n;return(0,P.jsxs)(`div`,{className:`spec-submission-state-switch`,children:[(0,P.jsxs)(`div`,{className:`pull-left`,children:[`Accepting new `,(0,P.jsx)(`strong`,{children:`report submissions`})]}),(0,P.jsx)(`div`,{className:`pull-right`,children:a?(0,P.jsx)(f,{text:c(),children:(0,P.jsx)(y,{checked:l,disabled:!0,onChange:s,onLabel:`YES`,offLabel:`NO`})}):(0,P.jsx)(y,{checked:l,onChange:s,onLabel:`YES`,offLabel:`NO`})}),(0,P.jsx)(`div`,{className:`clearfix`})]})};Y.propTypes={team:M.default.object.isRequired},Y.fragments={team:i`
    fragment SubmissionStateSwitchTeam on Team {
      handle
      submission_state
      is_delinquent
      is_submission_state_locked
      id
    }
  `},m();var de=i`
  mutation UpdateTeamCriticialSubmissionState(
    $handle: String!
    $critical_submissions_enabled: Boolean!
  ) {
    updateTeamCriticalSubmissionState(
      input: {
        handle: $handle
        critical_submissions_enabled: $critical_submissions_enabled
      }
    ) {
      was_successful
      team {
        id
        critical_submissions_enabled
      }
    }
  }
`,X=({team:e})=>{let[t]=T(de,{onCompleted:j}),{critical_submissions_enabled:n,i_can_view_critical_submissions_enabled:r}=e;return r?(0,P.jsxs)(`div`,{className:`spec-critical-submission-state-switch`,children:[(0,P.jsxs)(`div`,{className:`pull-left`,children:[`Accepting `,(0,P.jsx)(`strong`,{children:`critical report submissions`}),` even when not accepting new reports`]}),(0,P.jsx)(`div`,{className:`pull-right`,children:(0,P.jsx)(y,{checked:n,onChange:r=>{r.preventDefault();let i=!n;t({variables:{handle:e.handle,critical_submissions_enabled:i},optimisticResponse:{updateTeamCriticalSubmissionState:{__typename:`Mutation`,was_successful:!0,team:{...e,critical_submissions_enabled:i}}}})},onLabel:`YES`,offLabel:`NO`})}),(0,P.jsx)(`div`,{className:`clearfix`})]}):null};X.propTypes={team:M.default.object.isRequired},X.fragments={team:i`
    fragment CriticalSubmissionStateSwitchTeam on Team {
      critical_submissions_enabled
      i_can_view_critical_submissions_enabled
      id
      handle
    }
  `},m();var fe=({impact_template:e})=>e??`## Summary:
`,Z=({query:e})=>{let{team:n}=e,[r,i]=(0,N.useState)(!1),[a,o]=(0,N.useState)(n.report_submission_form_intro),[s,l]=(0,N.useState)(n.report_template),[u,d]=(0,N.useState)(fe(n)),f=r,m=n.type===`Engagements::Assessment`;return(0,P.jsxs)(`div`,{children:[(0,P.jsx)(`div`,{className:`page-title-container mb-md`,children:(0,P.jsx)(p,{children:`Submit Report Form`})}),(0,P.jsx)(`div`,{className:`settings-section`,children:!m&&(0,P.jsx)(Y,{team:n})}),(0,P.jsx)(`div`,{className:`settings-section`,children:!m&&(0,P.jsx)(X,{team:n})}),(0,P.jsxs)(`div`,{className:`settings-section`,children:[(0,P.jsx)(`h3`,{className:`daisy-h3`,children:`Introduction Text`}),(0,P.jsxs)(`div`,{children:[(0,P.jsx)(`div`,{className:`input-wrapper`,children:(0,P.jsx)(x,{value:a,name:`intro_textarea`,textareaId:`intro_textarea`,minimumHeight:74,onChange:o,maxLength:1e4,helperText:`Limited to 10,000 characters`})}),(0,P.jsx)(`div`,{className:`clearfix`})]})]}),(0,P.jsxs)(`div`,{className:`settings-section`,children:[(0,P.jsx)(`h3`,{className:`daisy-h3`,children:`Report Template`}),(0,P.jsx)(ie,{templateText:s,onChange:e=>l(e),handle:n.handle})]}),(0,P.jsxs)(`div`,{className:`settings-section`,children:[(0,P.jsx)(`h3`,{className:`daisy-h3`,children:`Impact Template`}),(0,P.jsxs)(`div`,{children:[(0,P.jsx)(`p`,{children:`You can pre-fill the Impact field visible to hackers when submitting a report.`}),(0,P.jsx)(`div`,{className:`input-wrapper`,children:(0,P.jsx)(x,{value:u,name:`impact_template_textarea`,textareaId:`impact_template_textarea`,minimumHeight:148,onChange:d,maxLength:4e3,helperText:`Limited to 4,000 characters`})}),(0,P.jsx)(`div`,{className:`clearfix`})]})]}),(0,P.jsx)(`div`,{className:`pull-right`,children:(0,P.jsxs)(c,{type:t.SUCCESS,onClick:()=>{i(!0),re.default.ajax({url:`/${n.handle}/submission_form`,type:`PUT`,data:{report_submission_form_intro:a,report_template:s,impact_template:u}}).then(()=>i(!1)).then(()=>S(`notice`,`Submission form settings updated.`)).catch(()=>S(`error`,`Something went wrong while updating submission form settings.Please contact ${window.constants.notification.support_link} if the problem persists.`))},disabled:f,children:[`Update introduction and templates`,` `]})}),(0,P.jsx)(`div`,{className:`clearfix`}),(0,P.jsx)(`div`,{className:`separator separator--muted`}),(0,P.jsxs)(`div`,{className:`settings-section`,children:[(0,P.jsx)(`h3`,{className:`daisy-h3`,children:`Weakness Configuration`}),(0,P.jsxs)(`div`,{children:[(0,P.jsxs)(`p`,{children:[`All weaknesses are shown by default. A weakness may belong to more than one cluster. Hiding, disabling or showing a weakness in one cluster will also change how this weakness acts in other clusters.`,` `,(0,P.jsx)(`a`,{href:`https://docs.hackerone.com/hackers/weakness.html`,target:`_blank`,rel:`noopener noreferrer`,children:`Learn more about Weaknesses and Clusters`}),`.`]}),(0,P.jsxs)(`p`,{children:[`As an example: `,(0,P.jsx)(`em`,{children:`Information Disclosure`}),`, a weakness, belongs to two clusters called `,(0,P.jsx)(`em`,{children:`Access Control`}),` and`,` `,(0,P.jsx)(`em`,{children:`Secure Design`}),`. Hiding `,(0,P.jsx)(`em`,{children:`Information Disclosure`}),` in`,` `,(0,P.jsx)(`em`,{children:`Access Control`}),` will also hide the weakness in`,` `,(0,P.jsx)(`em`,{children:`Secure Design`}),`.`]})]}),(0,P.jsx)(J,{teamHandle:n.handle})]})]})};Z.propTypes={query:M.default.object.isRequired};var pe=i`
  query SubmissionForm($handle: String!) {
    team(handle: $handle) {
      id
      handle
      type
      i_can_view_weaknesses
      report_submission_form_intro
      report_template
      impact_template
      ...SubmissionStateSwitchTeam
      ...CriticalSubmissionStateSwitchTeam
    }
  }
  ${Y.fragments.team}
  ${X.fragments.team}
`,Q=({match:{params:{handle:e}}})=>{let{data:t,loading:n}=A(pe,{variables:{handle:e}});return n||!t?(0,P.jsx)(v,{}):(0,P.jsx)(Z,{query:t})};Q.propTypes={match:M.default.shape({params:M.default.shape({handle:M.default.string.isRequired}).isRequired}).isRequired};var $=e=>(0,P.jsx)(te,{children:(0,P.jsx)(C,{header:(0,P.jsx)(ee,{...e}),content:(0,P.jsxs)(`div`,{children:[(0,P.jsx)(a,{children:(0,P.jsx)(`title`,{children:E(`Submission Form`)})}),(0,P.jsx)(Q,{...e})]}),footer:(0,P.jsx)(g,{})})});$.propTypes={match:M.default.shape({params:M.default.shape({handle:M.default.string.isRequired}).isRequired}).isRequired};export{$ as default};
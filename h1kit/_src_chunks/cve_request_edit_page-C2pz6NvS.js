import{o as e}from"./rolldown-runtime-DAXXjFlN.js";import{Fw as t,Kx as n,Lr as r,qx as i,yf as a,zx as o}from"./vendor-_WdvpBLr.js";import{Sm as s,T as c,Th as l,Tm as u,_h as d,_i as f,ap as p,ba as m,dh as h,fm as g,k as _,qr as v,tp as y,uh as b,vh as x,vm as S,wm as C}from"./app-5pKgUmmm.js";import{_ as w,b as T}from"./form_components-BUnCA1ee.js";import{t as E}from"./form-BPL2WRC6.js";var D=e(a()),O=e(o());i();var k=t(),A=n`
  query CveRequestEditPage($handle: String!, $cveRequestId: Int) {
    team(handle: $handle) {
      id
      _id
      handle
      cveRequest: cve_requests(first: 1, database_id: $cveRequestId) {
        edges {
          node {
            id
            cveIdentifier: cve_identifier
            state
            latestStateChangeReason: latest_state_change_reason
            autoSubmitOnPubliclyDisclosingReport: auto_submit_on_publicly_disclosing_report
            report {
              id
              databaseId: _id
            }
            ...CveRequestFormCveRequest
          }
        }
      }
    }
  }
  ${E.fragments.cveRequest}
`,j=n`
  mutation UpdateCveRequest(
    $cve_request_id: ID!
    $versions: JSON
    $metrics: JSON
    $credits: JSON
    $report_id: Int
    $weakness_id: ID
    $description: String
    $workaround: String
    $references: [String]
    $vulnerability_discovered_at: String
    $auto_submit_on_publicly_disclosing_report: Boolean
    $event: String
    $event_reason: String
  ) {
    updateCveRequest(
      input: {
        cve_request_id: $cve_request_id
        versions: $versions
        metrics: $metrics
        credits: $credits
        report_id: $report_id
        weakness_id: $weakness_id
        description: $description
        workaround: $workaround
        references: $references
        vulnerability_discovered_at: $vulnerability_discovered_at
        auto_submit_on_publicly_disclosing_report: $auto_submit_on_publicly_disclosing_report
        event: $event
        event_reason: $event_reason
      }
    ) {
      was_successful
      errors {
        nodes {
          field
          type
          message
        }
      }
    }
  }
`,M=({match:e})=>{let{params:{handle:t,id:n}}=e,{data:i,loading:a}=x(A,{variables:{handle:t,cveRequestId:parseInt(n,10)}}),[o]=d(j,{onError:S,onCompleted:({updateCveRequest:e})=>{if(e.was_successful)s(`notice`,`CVE request was successfully updated`),setTimeout(()=>{p(`/${t}/cve_requests`)},2e3);else{let t=e.errors?.nodes||[];if(t.length>0){let e=t.map(e=>e.field===`base`||e.field===`version_config`?e.message:`${e.field}: ${e.message}`);s(`error`,e.length===1?`Unable to save: ${e[0]}`:`Unable to save. Please fix these ${e.length} issues: ${e.join(`, `)}`)}else S()}}});if(a)return(0,k.jsx)(l,{overlay:!0});let O=e=>{let{report:t,vulnerabilityDiscoveredAt:n,weakness:r,versions:a,metrics:s,credits:c,description:l,workaround:u,references:d,autoSubmitOnPubliclyDisclosingReport:f}=e,p={cve_request_id:w(i.team.cveRequest).id,report_id:t.value?parseInt(t.value.databaseId,10):null,vulnerability_discovered_at:n.value,weakness_id:r.value,versions:a.value,metrics:s.value,credits:c.value,description:l.value,workaround:u.value,references:d.value.split(`
`),auto_submit_on_publicly_disclosing_report:f.value};o({variables:(0,D.default)(p,e=>e===``)})},{state:M,latestStateChangeReason:N,cveIdentifier:P,autoSubmitOnPubliclyDisclosingReport:F,report:I}=w(i.team.cveRequest);return(0,k.jsx)(v,{children:(0,k.jsx)(c,{header:(0,k.jsx)(_,{match:e}),hasBackground:!1,content:(0,k.jsxs)(`div`,{children:[(0,k.jsxs)(f,{children:[(0,k.jsx)(r,{children:(0,k.jsx)(`title`,{children:m(`Request a CVE ID`)})}),(0,k.jsx)(`div`,{className:`settings-title-container--daisy`,children:(0,k.jsx)(h,{to:`/${t}/cve_requests`,className:`daisy-link spec-back-to-triggers`,children:`← back to overview`})}),(0,k.jsx)(C,{className:`pull-right`,variation:`green`,children:T(M,F,I?.databaseId)}),(0,k.jsx)(f.Title,{children:`Request a CVE ID`}),(0,k.jsxs)(f.Description,{children:[M===constants.enums.CveRequestState.Draft&&(0,k.jsx)(b,{children:(0,k.jsx)(g,{children:`Please fill out the form below`})}),P&&(0,k.jsxs)(b,{children:[(0,k.jsx)(`strong`,{children:`Assigned CVE ID:`}),` `,(0,k.jsx)(`a`,{href:`https://www.cve.org/CVERecord?id=${P}`,className:`daisy-link`,rel:`noopener noreferrer`,target:`_blank`,children:P})]})]})]}),(0,k.jsx)(u,{children:(0,k.jsxs)(u.Content,{children:[M===constants.enums.CveRequestState.Draft&&N&&(0,k.jsx)(b,{children:(0,k.jsx)(y,{variation:`yellow`,children:N})}),(0,k.jsx)(E,{handle:t,cveRequest:w(i.team.cveRequest),handleSubmit:O})]})})]})})})};M.propTypes={match:O.default.shape({params:O.default.shape({handle:O.default.string.isRequired,id:O.default.string.isRequired}).isRequired}).isRequired};export{M as default};
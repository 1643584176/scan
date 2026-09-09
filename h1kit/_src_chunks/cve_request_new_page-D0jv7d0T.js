import{o as e}from"./rolldown-runtime-DAXXjFlN.js";import{Fw as t,Kx as n,Lr as r,Rd as i,qx as a,yf as o,zx as s}from"./vendor-_WdvpBLr.js";import{Sm as c,T as l,Tm as u,_h as d,_i as f,ap as p,ba as m,dh as h,k as g,qr as _,vm as v}from"./app-5pKgUmmm.js";import{t as y}from"./form-BPL2WRC6.js";var b=e(o()),x=e(s()),S=e(i());a();var C=t(),w=n`
  mutation CreateCveRequest(
    $team_handle: String!
    $versions: JSON!
    $metrics: JSON!
    $credits: JSON
    $report_id: Int
    $weakness_id: ID!
    $description: String!
    $workaround: String
    $references: [String]
    $vulnerability_discovered_at: String!
    $auto_submit_on_publicly_disclosing_report: Boolean
    $cve_entry_identifier: String
  ) {
    createCveRequest(
      input: {
        team_handle: $team_handle
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
        cve_entry_identifier: $cve_entry_identifier
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
`,T=({match:e,location:t})=>{let{params:{handle:n}}=e,[i]=d(w,{onError:v,onCompleted:({createCveRequest:e})=>{if(e.was_successful)c(`notice`,`CVE request was successfully created`),setTimeout(()=>{p(`/${n}/cve_requests`)},1e3);else{let t=e.errors?.nodes||[];if(t.length>0){let e=t.map(e=>e.field===`base`||e.field===`version_config`?e.message:`${e.field}: ${e.message}`);c(`error`,e.length===1?`Unable to create: ${e[0]}`:`Unable to create. Please fix these ${e.length} issues: ${e.join(`, `)}`)}else v()}}}),a=e=>{let{report:t,vulnerabilityDiscoveredAt:r,weakness:a,versions:o,metrics:s,credits:c,description:l,workaround:u,references:d,autoSubmitOnPubliclyDisclosingReport:f,cveIdentifier:p}=e,m={report_id:t.value?parseInt(t.value.databaseId,10):null,vulnerability_discovered_at:r.value,weakness_id:a.value,versions:o.value,metrics:s.value,credits:c.value,description:l.value,workaround:u.value,references:d.value.split(`
`),team_handle:n,auto_submit_on_publicly_disclosing_report:f.value,cve_entry_identifier:p.value};i({variables:(0,b.default)(m,e=>e===``)})},{report_id:o,request_type:s}=(0,S.parse)(t.search),x=parseInt(o,10),T=isNaN(x)?null:x;return(0,C.jsx)(_,{children:(0,C.jsx)(l,{header:(0,C.jsx)(g,{match:e}),hasBackground:!1,content:(0,C.jsxs)(`div`,{children:[(0,C.jsxs)(f,{children:[(0,C.jsx)(r,{children:(0,C.jsx)(`title`,{children:m(`CVE ID Request`)})}),(0,C.jsx)(`div`,{className:`settings-title-container--daisy`,children:(0,C.jsx)(h,{to:`/${n}/cve_requests`,className:`daisy-link spec-back-to-triggers`,children:`← back to overview`})}),(0,C.jsx)(f.Title,{children:`CVE ID Request`}),(0,C.jsx)(f.Description,{children:`Please fill out the form below`})]}),(0,C.jsx)(u,{children:(0,C.jsx)(u.Content,{children:(0,C.jsx)(y,{handle:n,cveRequestType:s,selectedReportId:T,handleSubmit:a})})})]})})})};T.propTypes={match:x.default.shape({params:x.default.shape({handle:x.default.string.isRequired}).isRequired}).isRequired,location:x.default.object.isRequired};export{T as default};
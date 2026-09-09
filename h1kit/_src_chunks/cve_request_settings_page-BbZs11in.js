import{o as e}from"./rolldown-runtime-DAXXjFlN.js";import{Fw as t,Kx as n,Lr as r,Rw as i,qx as a,zx as o}from"./vendor-_WdvpBLr.js";import{Sd as s,Sm as c,T as l,Th as u,Tm as d,_h as f,_i as p,ap as m,ba as h,dh as g,dl as _,hc as v,k as y,op as b,qr as x,uh as S,vh as C,vm as w,vp as T}from"./app-5pKgUmmm.js";import{b as E}from"./form_components-BUnCA1ee.js";var D=e(i());a();var O=e(o()),k=t(),A=20,j=n`
  query CveRequestSettingsPage(
    $handle: String!
    $pageSize: Int!
    $cursor: String
  ) {
    team(handle: $handle) {
      id
      cveRequests: cve_requests(first: $pageSize, after: $cursor)
        @connection(key: "teamCveRequests") {
        edges {
          node {
            id
            databaseId: _id
            cve_identifier
            state
            request_type
            products
            latest_state_change_reason
            auto_submit_on_publicly_disclosing_report
            report {
              id
              databaseId: _id
            }
          }
        }
        pageInfo {
          endCursor
          hasNextPage
        }
      }
    }
  }
`,M=n`
  mutation FireEventForCveRequestMutation(
    $cve_request_id: ID!
    $event: String
    $event_reason: String
  ) {
    updateCveRequest(
      input: {
        cve_request_id: $cve_request_id
        event: $event
        event_reason: $event_reason
      }
    ) {
      was_successful
      errors {
        edges {
          node {
            field
            type
            message
          }
        }
      }

      cve_request {
        id
        state
        request_type
        cve_identifier
      }
    }
  }
`,N=({match:e})=>{let{params:{handle:t}}=e,{data:n,loading:i,fetchMore:a}=C(j,{variables:{handle:t,pageSize:A}}),[o]=f(M,{onError(){w()},onCompleted(e){if(e.updateCveRequest.was_successful)c(`notice`,`CVE request was submitted for publication.`);else{let t=e.updateCveRequest.errors.edges.map(e=>e.node.field===`base`?v(e.node.message):e.node.message);c(`error`,t.length===1?`Unable to submit: ${t[0]}`:`Unable to submit. Please fix these ${t.length} issues: ${t.join(`, `)}`)}}}),[O]=f(M,{onError(){w()},onCompleted(e){e.updateCveRequest.was_successful?c(`notice`,`CVE request was cancelled.`):w()}}),N=_(n,`team.cveRequests`,a);return i&&!n?(0,k.jsx)(u,{renderInBody:!0,children:`Loading...`}):(0,k.jsx)(x,{children:(0,k.jsx)(l,{header:(0,k.jsx)(y,{match:e}),hasBackground:!1,content:(0,k.jsxs)(`div`,{children:[(0,k.jsxs)(S,{children:[(0,k.jsx)(r,{children:(0,k.jsx)(`title`,{children:h(`CVE ID Requests`)})}),(0,k.jsxs)(p,{children:[(0,k.jsx)(b,{onClick:()=>m(`/${t}/cve_requests/new?request_type=update`),className:`pull-right`,size:`small`,variation:`secondary`,children:`Update CVE ID`}),(0,k.jsx)(b,{onClick:()=>m(`/${t}/cve_requests/new`),className:`pull-right margin-5--right`,size:`small`,children:`New CVE ID`}),(0,k.jsx)(p.Title,{children:`CVE ID Requests`}),(0,k.jsx)(p.Description,{children:`Request or update a CVE ID for your vulnerability using HackerOne.`})]}),(0,k.jsx)(d,{children:(0,k.jsx)(d.Content,{children:(0,k.jsxs)(`p`,{children:[`CVE IDs reference publicly known cybersecurity vulnerabilities. You can request to have CVE IDs associated with your program's vulnerabilities to easily identify them. Upon request, HackerOne a`,` `,(0,k.jsx)(`a`,{href:`https://www.cve.org/ResourcesSupport/Glossary?activeTerm=glossaryCNA`,target:`_blank`,rel:`noopener noreferrer`,children:`CNA`}),` `,`will review the CVE record and process it for public disclosure. The entire process takes about 7 business days after request.`]})})})]}),(0,k.jsx)(S,{children:(0,k.jsx)(d,{children:(0,k.jsxs)(s,{children:[(0,k.jsx)(s.Head,{children:(0,k.jsxs)(s.Row,{children:[(0,k.jsx)(s.CellHeader,{children:`ID`}),(0,k.jsx)(s.CellHeader,{children:`CVE ID`}),(0,k.jsx)(s.CellHeader,{children:`Request Type`}),(0,k.jsx)(s.CellHeader,{children:`Status`}),(0,k.jsx)(s.CellHeader,{children:`Product(s)`}),(0,k.jsx)(s.CellHeader,{children:`Action`})]})}),(0,k.jsxs)(s.Body,{children:[n.team.cveRequests.edges.length===0&&(0,k.jsx)(s.Row,{children:(0,k.jsx)(s.Cell,{colSpan:6,className:`text-aligned-center`,children:`No CVEs have been requested yet.`})}),n.team.cveRequests.edges.map(e=>(0,k.jsxs)(s.Row,{className:`spec-cve-request-${e.node.databaseId}`,children:[(0,k.jsxs)(s.Cell,{children:[`#`,e.node.databaseId]}),(0,k.jsx)(s.Cell,{children:e.node.cve_identifier?(0,k.jsx)(`a`,{href:`https://www.cve.org/CVERecord?id=${e.node.cve_identifier}`,className:`daisy-link`,target:`_blank`,rel:`noopener noreferrer`,children:e.node.cve_identifier}):`Not assigned`}),(0,k.jsx)(s.Cell,{children:e.node.request_type===`new`?`Publication`:`Update`}),(0,k.jsx)(s.Cell,{children:e.node.state===constants.enums.CveRequestState.Draft&&e.node.latest_state_change_reason?(0,k.jsx)(T,{className:`inline-help`,tooltipText:e.node.latest_state_change_reason,children:E(e.node.state,e.node.auto_submit_on_publicly_disclosing_report,e.node.report?.databaseId)}):E(e.node.state,e.node.auto_submit_on_publicly_disclosing_report,e.node.report?.databaseId)}),(0,k.jsx)(s.Cell,{children:(e.node.products||[]).join(`, `)}),(0,k.jsx)(s.Cell,{children:e.node.state===constants.enums.CveRequestState.Draft?(0,k.jsxs)(D.default.Fragment,{children:[(0,k.jsx)(`div`,{children:(0,k.jsx)(g,{to:`/${t}/cve_requests/${e.node.databaseId}/edit`,className:`daisy-link`,children:`Edit`})}),(0,k.jsx)(`div`,{children:!e.node.auto_submit_on_publicly_disclosing_report&&(0,k.jsx)(`a`,{href:``,onClick:t=>{t.preventDefault(),o({variables:{cve_request_id:e.node.id,event:constants.enums.CveRequestEvent.SubmitForHackeroneApproval,event_reason:`Requesting approval for publication.`},optimisticResponse:{updateCveRequest:{__typename:`UpdateCveRequestPayload`,was_successful:!0,cve_request:{__typename:`CveRequest`,id:e.node.id,state:constants.enums.CveRequestState.PendingHackeroneApproval}}}})},className:`daisy-link`,children:`Request publication`})}),(0,k.jsx)(`div`,{children:(0,k.jsx)(`a`,{href:``,onClick:t=>{t.preventDefault(),O({variables:{cve_request_id:e.node.id,event:constants.enums.CveRequestEvent.Cancel,event_reason:`Draft cancelled by user.`},optimisticResponse:{updateCveRequest:{__typename:`UpdateCveRequestPayload`,was_successful:!0,cve_request:{__typename:`CveRequest`,id:e.node.id,state:constants.enums.CveRequestState.Cancelled,cve_identifier:null}}}})},className:`daisy-link`,children:`Cancel`})})]}):(0,k.jsx)(g,{to:`/${t}/cve_requests/${e.node.databaseId}/edit`,className:`daisy-link`,children:`View`})})]},e.node.id)),n.team.cveRequests.pageInfo.hasNextPage&&(0,k.jsx)(s.Row,{children:(0,k.jsx)(s.Cell,{colSpan:4,className:`text-aligned-center`,children:(0,k.jsx)(b,{onClick:N,variation:`secondary`,size:`small`,children:`Load more...`})})})]})]})})})]})})})};N.propTypes={match:O.default.shape({params:O.default.shape({handle:O.default.string.isRequired})}).isRequired};export{N as default};
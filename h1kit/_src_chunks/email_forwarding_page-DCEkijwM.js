import{o as e}from"./rolldown-runtime-DAXXjFlN.js";import{Fw as t,Kx as n,Rw as r,jn as i,qx as a,zx as o}from"./vendor-_WdvpBLr.js";import{Eh as s,Jf as c,Ju as l,Sd as u,Tm as d,Uf as f,dl as p,gh as m,lh as h,qf as g,uh as _,v,vh as y,wm as b}from"./app-5pKgUmmm.js";var x=e(r()),S=e(o());a();var C=t(),w=25,T=n`
  query ForwardedEmailsQuery(
    $cursor: String
    $handle: String!
    $forwardedEmailsPerPage: Int!
  ) {
    team(handle: $handle) {
      id
      forwarded_emails(
        first: $forwardedEmailsPerPage
        after: $cursor
        order_by: { field: created_at, direction: DESC }
      ) {
        pageInfo {
          endCursor
          hasNextPage
        }
        total_count
        edges {
          node {
            id
            subject
            body
            headers
            dkim_passed
            spf_passed
            is_nonce
            email_signature_valid
            created_at
          }
        }
      }
    }
  }
`,E=({match:e})=>{let t=e.params.handle,[n,r]=(0,x.useState)(void 0),{data:a,loading:o,fetchMore:S}=y(T,{variables:{handle:t,cursor:null,forwardedEmailsPerPage:w}});if(o)return null;let E=a?.team?.forwarded_emails?.edges?.map(e=>e.node)||[],D=E.find(({id:e})=>e===n),O=p(a,`team.forwarded_emails`,S),k={};return D&&D.headers&&(k=JSON.parse(D.headers)),(0,C.jsx)(C.Fragment,{children:E&&E.length>0?(0,C.jsx)(m,{hasOutsideGutter:!0,isFluid:!0,children:(0,C.jsxs)(m.Row,{children:[(0,C.jsx)(m.Column,{size:`one-third`,style:{overflowY:`scroll`,height:`calc(100vh - 58px)`},children:(0,C.jsx)(i,{dataLength:E.length,next:()=>O(),hasMore:a.team.forwarded_emails.pageInfo.hasNextPage,loader:(0,C.jsx)(s,{}),scrollableTarget:`main-content`,children:E.map(({id:e,subject:t,created_at:n,is_nonce:i,email_signature_valid:a})=>(0,C.jsx)(_,{top:!0,children:(0,C.jsx)(d,{onClick:()=>r(e),children:(0,C.jsx)(d.Content,{children:(0,C.jsxs)(h,{justifyContent:`space-between`,children:[(0,C.jsxs)(h,{flexDirection:`column`,children:[(0,C.jsx)(`strong`,{children:t}),(0,C.jsxs)(`div`,{children:[i?(0,C.jsx)(b,{variation:`grey`,size:`smaller`,rounded:!0,children:`nonce`}):null,` `,a?null:(0,C.jsx)(b,{variation:`red`,size:`smaller`,rounded:!0,children:`not processed`})]})]}),(0,C.jsxs)(h,{flexDirection:`column`,style:{minWidth:100,textAlign:`right`},children:[(0,C.jsx)(`span`,{children:f({date:n})}),(0,C.jsx)(`div`,{style:{fontSize:`14px`},children:c({date:n})})]})]})})})},e))})}),(0,C.jsx)(m.Column,{size:`two-thirds`,style:{overflowY:`scroll`,height:`calc(100vh - 58px)`},children:D?(0,C.jsxs)(C.Fragment,{children:[(0,C.jsx)(_,{top:!0,children:(0,C.jsxs)(d,{children:[(0,C.jsx)(d.SubHeading,{className:`card__subheading--top_and_bottom_border`,children:(0,C.jsxs)(h,{justifyContent:`space-between`,alignItems:`center`,children:[(0,C.jsx)(`h4`,{className:`daisy-h4 no-margin`,children:(0,C.jsx)(`strong`,{children:D.subject})}),(0,C.jsx)(`span`,{children:g({date:D.created_at})})]})}),(0,C.jsx)(d.Content,{children:(0,C.jsx)(l,{className:`markdownable`,markdown:D.body})})]})}),(0,C.jsx)(_,{top:!0,children:(0,C.jsxs)(d,{children:[(0,C.jsx)(d.SubHeading,{className:`card__subheading--top_and_bottom_border`,children:(0,C.jsxs)(h,{justifyContent:`space-between`,alignItems:`center`,children:[(0,C.jsx)(`h4`,{className:`daisy-h4 no-margin`,children:(0,C.jsx)(`strong`,{children:`Debugging`})}),(0,C.jsxs)(`span`,{children:[D.is_nonce?(0,C.jsxs)(`div`,{children:[(0,C.jsx)(b,{variation:`grey`,size:`smaller`,rounded:!0,children:`NONCE email`}),` `]}):null,(0,C.jsx)(b,{variation:`grey`,size:`smaller`,rounded:!0,children:D.dkim_passed?`DKIM pass`:`DKIM fail`}),` `,(0,C.jsx)(b,{variation:`grey`,size:`smaller`,rounded:!0,children:D.spf_passed?`SPF pass`:`SPF fail`}),` `]})]})}),(0,C.jsx)(d.Content,{children:(0,C.jsxs)(u,{fixed:!0,children:[(0,C.jsx)(u.Head,{children:(0,C.jsxs)(u.Row,{children:[(0,C.jsx)(u.CellHeader,{width:`150px`,children:`Header`}),(0,C.jsx)(u.CellHeader,{width:`20%`,children:`Value`})]})}),(0,C.jsx)(u.Body,{children:k&&Object.keys(k).map(e=>(0,C.jsxs)(u.Row,{children:[(0,C.jsx)(u.Cell,{style:{verticalAlign:`top`},children:e}),(0,C.jsx)(u.Cell,{className:`break-all`,children:k[e]})]},e))})]})})]})})]}):null})]})}):(0,C.jsxs)(v,{children:[(0,C.jsx)(`h3`,{className:`daisy-h3 no-margin`,children:`No email to show`}),(0,C.jsx)(`p`,{children:`This program hasn't received any emails yet`})]})})};E.propTypes={match:S.default.shape({params:S.default.shape({handle:S.default.string.isRequired}).isRequired}).isRequired};export{E as default};
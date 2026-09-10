import{o as e}from"./rolldown-runtime-DAXXjFlN.js";import{Fw as t,Kx as n,Lr as r,Nb as i,ov as a,qx as o,rv as s,zx as c}from"./vendor-_WdvpBLr.js";import{Ah as l,Gn as u,T as d,Th as f,Tm as p,_h as m,ba as h,k as g,qr as _,vh as v,vm as y,ym as b}from"./app-5pKgUmmm.js";o();var x=e(c()),S=t(),C=window.constants.notification.support_link,w=n`
  mutation UpdateTeamAllowsPrivateDisclosure(
    $handle: String!
    $allows_private_disclosure: Boolean!
  ) {
    updateTeamAllowsPrivateDisclosure(
      input: {
        handle: $handle
        allows_private_disclosure: $allows_private_disclosure
      }
    ) {
      was_successful
      team {
        id
        allows_private_disclosure
        handle
        disclosed_reports: reports(
          where: { disclosed_at: { _is_null: false } }
        ) {
          total_count
        }
      }
    }
  }
`,T=n`
  query TeamDisclosureQuery($handle: String!) {
    team(handle: $handle) {
      id
      handle
      allows_private_disclosure
      disclosed_reports: reports(where: { disclosed_at: { _is_null: false } }) {
        total_count
      }
    }
  }
`,E=({team:e})=>{let[t,{loading:n}]=m(w,{onCompleted:({updateTeamAllowsPrivateDisclosure:e})=>{e.was_successful?b():y()}});return n?(0,S.jsx)(f,{}):(0,S.jsx)(S.Fragment,{children:(0,S.jsx)(p,{children:(0,S.jsxs)(p.Content,{children:[(0,S.jsx)(`div`,{children:`Upon disclosure, contents of the report will only be visible to participants in your program. This will enable hackers to see what vulnerabilities have already been found and drive more engagement to your program.`}),(0,S.jsx)(`br`,{}),(0,S.jsxs)(`div`,{children:[`In order to opt out of this feature, please contact`,` `,(0,S.jsx)(`a`,{className:`daisy-link`,href:C,children:C})]}),(0,S.jsx)(`br`,{}),(0,S.jsxs)(`div`,{children:[(0,S.jsx)(u,{onLabel:`YES`,offLabel:`NO`,disabled:e.disclosed_reports.total_count>0&&e.allows_private_disclosure,checked:e.allows_private_disclosure,onChange:n=>{n.preventDefault(),t({variables:{handle:e.handle,allows_private_disclosure:!e.allows_private_disclosure}})},className:`pull-right spec-private-disclosure-required-at-switch`}),`Allow hackers to disclose reports in your private program`]})]})})})};E.propTypes={team:x.default.object.isRequired};var D=({handle:e})=>{let{data:t,loading:n}=v(T,{variables:{handle:e}});if(n)return(0,S.jsx)(f,{});let{team:r}=t;return(0,S.jsxs)(S.Fragment,{children:[(0,S.jsxs)(`div`,{className:`mb-md`,children:[(0,S.jsx)(a,{children:`Disclosure`}),(0,S.jsx)(i,{top:`16`}),(0,S.jsx)(s,{children:`Enable hackers to disclose reports in your private program.`})]}),(0,S.jsx)(i,{bottom:`32`,children:(0,S.jsx)(E,{team:r})})]})};D.propTypes={handle:x.default.string.isRequired};var O=e=>{let{handle:t}=e.match.params;return(0,S.jsx)(_,{children:(0,S.jsx)(d,{header:(0,S.jsx)(g,{match:e.match}),hasBackground:!1,content:(0,S.jsxs)(`div`,{children:[(0,S.jsx)(r,{children:(0,S.jsx)(`title`,{children:h(`Disclosure`)})}),(0,S.jsx)(D,{handle:t})]}),footer:(0,S.jsx)(l,{})})})};O.propTypes={match:x.default.shape({params:x.default.shape({handle:x.default.string}).isRequired}).isRequired};export{O as default};
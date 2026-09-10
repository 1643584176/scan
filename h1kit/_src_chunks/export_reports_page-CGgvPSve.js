import{o as e}from"./rolldown-runtime-DAXXjFlN.js";import{Fw as t,Kx as n,Rw as r,qx as i,zx as a}from"./vendor-_WdvpBLr.js";import{Ah as o,Sm as s,T as c,Th as l,Tm as u,_h as d,fm as f,gc as p,k as m,op as h,qr as g,rc as _,vh as v}from"./app-5pKgUmmm.js";var y=e(r()),b=e(a());i();var x=t(),S=n`
  query ExportLifetimeReportsQuery {
    me {
      id
      email
    }
  }
`,C=n`
  mutation ExportLifetimeReports($handle: String!, $email: String!) {
    exportLifetimeReports(input: { handle: $handle, email: $email }) {
      was_successful
      errors(first: 100) {
        edges {
          node {
            id
            field
            message
            type
          }
        }
      }
    }
  }
`,w=({handle:e,userEmail:t})=>{let[n,r]=(0,y.useState)(!1),[i,a]=(0,y.useState)(t),[o]=d(C,{onCompleted:({exportLifetimeReports:e})=>{e.was_successful?r(!0):s(`error`,p(e.errors).team_id)}});return(0,x.jsxs)(u,{children:[(0,x.jsxs)(u.Heading,{children:[(0,x.jsx)(`h3`,{className:`daisy-h3`,children:`Export Reports`}),(0,x.jsxs)(f,{children:[`Enter your email address to receive a link to download all reports for this program and any child programs.`,(0,x.jsx)(`br`,{}),`Note: It may take some time to export all reports depending on the number of submissions.`]})]}),(0,x.jsxs)(u.Content,{children:[n?(0,x.jsx)(`div`,{children:`We've successfully received your request. You'll receive an email shortly!`}):(0,x.jsxs)(`form`,{onSubmit:t=>{t.preventDefault(),o({variables:{handle:e,email:i}})},children:[(0,x.jsx)(_,{id:`email_address`,name:`email_address`,value:i,type:`email`,onChange:e=>a(e.target.value),required:!0}),(0,x.jsx)(`div`,{className:`pull-right`,style:{marginTop:10},children:(0,x.jsx)(h,{children:`Send`})})]}),(0,x.jsx)(`div`,{className:`clearfix`})]})]})};w.propTypes={handle:b.default.string.isRequired,userEmail:b.default.string.isRequired};var T=({handle:e})=>{let{data:t,loading:n}=v(S);return n?(0,x.jsx)(l,{}):(0,x.jsx)(w,{handle:e,userEmail:t.me.email})};T.propTypes={handle:b.default.string.isRequired};var E=class extends y.Component{static propTypes={match:b.default.shape({params:b.default.shape({handle:b.default.string.isRequired}).isRequired}).isRequired};render(){let e=this.props.match.params.handle;return(0,x.jsx)(g,{children:(0,x.jsx)(c,{header:(0,x.jsx)(m,{...this.props}),content:(0,x.jsx)(`div`,{children:(0,x.jsx)(T,{handle:e})}),footer:(0,x.jsx)(o,{}),hasBackground:!1})})}};export{E as default};
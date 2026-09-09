import{o as e}from"./rolldown-runtime-DAXXjFlN.js";import{Fw as t,Kx as n,Rw as r,qx as i,zx as a}from"./vendor-_WdvpBLr.js";import{Tm as o,_h as s,_i as c,gh as l,mr as u,op as d,rc as f,uh as p}from"./app-5pKgUmmm.js";var m=e(r()),h=e(a());i();var g=t(),_=n`
  mutation RegisterUserDevice($token: String!, $name: String) {
    registerUserDevice(input: { token: $token, name: $name }) {
      was_successful
      errors {
        nodes {
          id
          field
          message
        }
      }
    }
  }
`,v=({location:{search:e}})=>{let t=new URLSearchParams(e).get(`token`),[n,r]=(0,m.useState)([]),[i,a]=(0,m.useState)(``),[h,{loading:v,called:y}]=s(_,{onCompleted:({registerUserDevice:e})=>{e.was_successful||r(e.errors.nodes.map(e=>`${e.field} ${e.message}`))}});return(0,g.jsx)(u,{content:(0,g.jsx)(l,{hasOutsideGutter:!0,maxWidth:440,children:(0,g.jsxs)(p,{top:!0,size:`extra-large`,children:[(0,g.jsx)(p,{size:`large`,children:(0,g.jsx)(c,{children:(0,g.jsx)(c.Title,{className:`text-aligned-center`,children:`Register a new device`})})}),(0,g.jsx)(l.Column,{size:`one-whole`,children:(0,g.jsx)(o,{children:(0,g.jsxs)(o.Content,{children:[y&&!v&&n.length===0?(0,g.jsxs)(g.Fragment,{children:[(0,g.jsxs)(`p`,{children:[(0,g.jsx)(`strong`,{children:`Device registered successfully!`}),` This device can now be used to authenticate to your HackerOne account.`]}),(0,g.jsx)(`p`,{children:(0,g.jsx)(d,{componentTag:`a`,href:`/users/sign_in`,children:`Sign in`})})]}):(0,g.jsxs)(`form`,{onSubmit:e=>{e.preventDefault(),h({variables:{token:t,name:i}})},children:[(0,g.jsx)(`p`,{children:`You're about to authorize a new device to authenticate to your HackerOne account. In order to make a device easier to identify, you can provide an optional device name for future reference.`}),(0,g.jsxs)(p,{children:[(0,g.jsx)(`label`,{children:(0,g.jsx)(`strong`,{children:`Device name`})}),(0,g.jsx)(f,{value:i,onChange:e=>a(e.target.value),maxLength:constants.deviceRegistration.nameMaxLength,autoFocus:!0})]}),(0,g.jsx)(p,{children:(0,g.jsx)(d,{type:`submit`,disabled:v,children:v?`Registering...`:`Register`})})]}),n.length>0&&(0,g.jsxs)(g.Fragment,{children:[(0,g.jsx)(`p`,{children:`The following errors occurred when registering the new device:`}),(0,g.jsx)(`ul`,{children:n.map((e,t)=>(0,g.jsx)(`li`,{children:e},t))})]})]})})})]})})})};v.propTypes={location:h.default.shape({search:h.default.string.isRequired}).isRequired};export{v as default};
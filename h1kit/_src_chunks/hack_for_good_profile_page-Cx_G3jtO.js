import{o as e}from"./rolldown-runtime-DAXXjFlN.js";import{Fw as t,Kx as n,Rw as r,qx as i,zx as a}from"./vendor-_WdvpBLr.js";import{Ah as o,Ju as s,Th as c,Tm as l,gh as u,uh as d,vh as f}from"./app-5pKgUmmm.js";import{t as p}from"./user_profile_card-mjpCqC7A.js";var m=e(r());i();var h=e(a()),g=t(),_=({user:e})=>e.intro&&(0,g.jsx)(d,{children:(0,g.jsxs)(l,{children:[(0,g.jsxs)(l.Heading,{children:[`About `,e.name]}),(0,g.jsx)(l.Content,{children:(0,g.jsx)(s,{markdown:e.intro,className:`break-all`})})]})});_.propTypes={user:h.default.shape({intro:h.default.string,name:h.default.string}).isRequired};var v=n`
  query HackForGoodProfilePageQuery($resourceIdentifier: String!) {
    me {
      id
      username
      ...UserProfileCardMe
    }
    user(username: $resourceIdentifier) {
      id
      username
      name
      intro
      ...UserProfileCardUser
    }
  }
  ${p.fragments.user}
  ${p.fragments.me}
`,y=()=>{let{data:e,loading:t}=f(v,{variables:{resourceIdentifier:`hackforgood`}});return t?(0,g.jsx)(c,{}):(0,g.jsx)(m.default.Fragment,{children:(0,g.jsx)(d,{top:!0,size:`large`,children:(0,g.jsxs)(u,{hasOutsideGutter:!0,children:[(0,g.jsxs)(u.Row,{children:[(0,g.jsx)(u.Column,{size:`one-quarter`,children:(0,g.jsx)(p,{user:e.user,me:e.me})}),(0,g.jsx)(u.Column,{children:(0,g.jsx)(_,{user:e.user})})]}),(0,g.jsx)(u.Row,{children:(0,g.jsx)(u.Column,{children:(0,g.jsx)(o,{})})})]})})})};export{y as default};
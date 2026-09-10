import{o as e}from"./rolldown-runtime-DAXXjFlN.js";import{Fw as t,Kx as n,Lr as r,qx as i,zx as a}from"./vendor-_WdvpBLr.js";import{Th as o,ba as s,mr as c,vh as l}from"./app-5pKgUmmm.js";var u=e(a()),d=`/assets/static/dashboard_overview_demo-B5JGZ_UI.png`;i();var f=t(),p=n`
  query DashboardOverviewDemo($handle: String!) {
    team(handle: $handle) {
      id
      handle
      state
    }
  }
`,m=({match:{params:{handle:e}},history:t})=>{let{loading:n}=l(p,{variables:{handle:e}});return n?(0,f.jsx)(o,{overlay:!0}):(0,f.jsx)(c,{content:(0,f.jsxs)(`div`,{children:[(0,f.jsx)(r,{children:(0,f.jsx)(`title`,{children:s(`DashboardOverviewDemoPage`)})}),(0,f.jsx)(`div`,{className:`full-width-inner-container`,children:(0,f.jsx)(`div`,{className:`content-wrapper`,children:(0,f.jsx)(`img`,{src:d})})})]})})};m.propTypes={match:u.default.object.isRequired,history:u.default.object.isRequired};export{m as default};
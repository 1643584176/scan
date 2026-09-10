import{o as e}from"./rolldown-runtime-DAXXjFlN.js";import{Bx as t,By as n,Fw as r,Ly as i,Rw as a,Vx as o,cp as s}from"./vendor-_WdvpBLr.js";import{Cp as c,mr as l}from"./app-5pKgUmmm.js";var u=e(a()),d=r(),f=c(`
  subscription CatFactSubscription {
    cat_fact {
      fact
    }
  }
`),p=c(`
  mutation PublishCatFactMutation {
    publishCatFact(input: {}) {
      was_successful
    }
  }
`),m=()=>{let[e,r]=(0,u.useState)(null);t(f,{onSubscriptionData:({subscriptionData:e})=>{e?.data&&r(e.data.cat_fact.fact)}});let[a]=o(p);return(0,d.jsx)(l,{content:(0,d.jsxs)(`div`,{className:`m-lg`,children:[(0,d.jsx)(s,{fill:!0,children:e?(0,d.jsx)(i,{variation:n.Information,contentPrimary:e}):(0,d.jsx)(`div`,{className:`m-md`,children:(0,d.jsx)(`center`,{children:`Sadly, there are no cat facts yet.`})})}),(0,d.jsx)(`div`,{className:`m-md`,children:(0,d.jsx)(`center`,{children:(0,d.jsx)(`a`,{onClick:()=>{a()},children:`Publish your own cat fact.`})})})]})})};export{f as CAT_FACT_SUBSCRIPTION,p as PUBLISH_CAT_FACT_MUTATION,m as default};
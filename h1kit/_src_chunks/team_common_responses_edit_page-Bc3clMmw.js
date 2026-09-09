import{o as e}from"./rolldown-runtime-DAXXjFlN.js";import{Fw as t,Kx as n,Lr as r,Rw as i,qx as a,zx as o}from"./vendor-_WdvpBLr.js";import{Ah as s,T as c,_h as l,ba as u,gc as d,k as f,qr as p,vh as m}from"./app-5pKgUmmm.js";import{t as h}from"./form-DqrcV2O9.js";var g=e(i()),_=e(o());a();var v=t(),y=n`
  mutation UpdateCommonResponse(
    $common_response_id: ID!
    $title: String!
    $message: String!
  ) {
    updateCommonResponse(
      input: {
        common_response_id: $common_response_id
        title: $title
        message: $message
      }
    ) {
      was_successful
      errors {
        edges {
          node {
            id
            field
            message
          }
        }
      }
    }
  }
`,b=n`
  query CommonResponse($database_id: Int!, $handle: String!) {
    teams(where: { handle: { _eq: $handle } }) {
      nodes {
        id
        common_responses(where: { id: { _eq: $database_id } }) {
          nodes {
            id
            title
            message
          }
        }
      }
    }
  }
`,x=({handle:e,history:t,id:n,initialTitle:r,initialMessage:i})=>{let[a,o]=(0,g.useState)({}),[s,{loading:c}]=l(y,{onCompleted:({updateCommonResponse:{was_successful:n,errors:r}})=>{n?t.push(`/${e}/common_responses`):o(d(r))}}),[u,f]=(0,g.useState)(r),[p,m]=(0,g.useState)(i);return(0,v.jsx)(h,{handleSubmit:e=>{e.preventDefault(),s({variables:{common_response_id:n,title:u,message:p}})},handle:e,errors:a,loading:c,title:u,setTitle:f,message:p,setMessage:m,heading:`Edit Common Response`})};x.propTypes={handle:_.default.string.isRequired,history:_.default.object.isRequired,id:_.default.string.isRequired,initialTitle:_.default.string.isRequired,initialMessage:_.default.string.isRequired};var S=e=>{let{match:{params:{handle:t,id:n}},history:i}=e,{data:a,loading:o,error:l}=m(b,{variables:{database_id:parseInt(n,10),handle:t}}),d=a?.teams?.nodes?.[0]?.common_responses?.nodes?.[0];return(0,v.jsx)(p,{children:(0,v.jsx)(c,{header:(0,v.jsx)(f,{...e}),tertiaryHeader:`Common Responses`,content:(0,v.jsxs)(`div`,{children:[(0,v.jsx)(r,{children:(0,v.jsx)(`title`,{children:u(`Common Responses`)})}),(0,v.jsxs)(`div`,{children:[o&&(0,v.jsx)(`span`,{children:`Loading...`}),l&&(0,v.jsx)(`span`,{children:`An error occurred`}),!o&&!l&&!d&&(0,v.jsx)(`span`,{children:`Common response not found`}),!o&&!l&&d&&(0,v.jsx)(x,{id:d.id,initialTitle:d.title,initialMessage:d.message,handle:t,history:i})]})]}),footer:(0,v.jsx)(s,{})})})};S.propTypes={match:_.default.shape({params:_.default.shape({handle:_.default.string.isRequired,id:_.default.string.isRequired}).isRequired}).isRequired,history:_.default.object.isRequired};export{S as default};
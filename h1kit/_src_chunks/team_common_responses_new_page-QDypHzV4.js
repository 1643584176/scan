import{o as e}from"./rolldown-runtime-DAXXjFlN.js";import{Fw as t,Kx as n,Lr as r,Rw as i,qx as a,zx as o}from"./vendor-_WdvpBLr.js";import{Ah as s,T as c,_h as l,ba as u,gc as d,k as f,qr as p}from"./app-5pKgUmmm.js";import{t as m}from"./form-DqrcV2O9.js";var h=e(i()),g=e(o());a();var _=t(),v=n`
  mutation CreateCommonResponse(
    $team_id: ID!
    $title: String!
    $message: String!
  ) {
    createCommonResponse(
      input: { team_id: $team_id, title: $title, message: $message }
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
`,y=({handle:e,team:t,history:n})=>{let[r,i]=(0,h.useState)({}),[a,{loading:o}]=l(v,{onCompleted:({createCommonResponse:{was_successful:t,errors:r}})=>{t?n.push(`/${e}/common_responses`):i(d(r))}}),[s,c]=(0,h.useState)(``),[u,f]=(0,h.useState)(``);return(0,_.jsx)(m,{handleSubmit:e=>{e.preventDefault(),a({variables:{team_id:btoa(`gid://hackerone/Team/${t.id}`),title:s,message:u}})},handle:e,errors:r,loading:o,title:s,setTitle:c,message:u,setMessage:f,heading:`Add Common Response`})};y.propTypes={handle:g.default.string.isRequired,history:g.default.object.isRequired,team:g.default.object.isRequired};var b=e=>{let{match:{params:{handle:t}},history:n}=e,i=TeamStore.byHandle(t);return(0,_.jsx)(p,{children:(0,_.jsx)(c,{header:(0,_.jsx)(f,{...e}),tertiaryHeader:`Common Responses`,content:(0,_.jsxs)(`div`,{children:[(0,_.jsx)(r,{children:(0,_.jsx)(`title`,{children:u(`Common Responses`)})}),(0,_.jsx)(`div`,{children:(0,_.jsx)(y,{handle:t,team:i,history:n})})]}),footer:(0,_.jsx)(s,{})})})};b.propTypes={match:g.default.shape({params:g.default.shape({handle:g.default.string.isRequired}).isRequired}).isRequired,history:g.default.object.isRequired};export{b as default};
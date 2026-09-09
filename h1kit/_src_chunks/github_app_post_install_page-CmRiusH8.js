import{o as e}from"./rolldown-runtime-DAXXjFlN.js";import{Fw as t,Hx as n,Kx as r,Li as i,Pb as a,Xi as o,qx as s,zx as c}from"./vendor-_WdvpBLr.js";import{Cm as l,Gs as u,Js as d,Ks as f,Sm as p,Th as m,Tm as h,Ws as g,ap as _,qs as v,uh as y,vh as b}from"./app-5pKgUmmm.js";var x=e(c());s();var S=e(a()),C=e(o()),w=t(),T=r`
  query GithubPostInstallQuery {
    me {
      id
      name
      teams(
        first: 100
        permissions: [program_management]
        secure_order_by: { name: { _direction: ASC } }
      ) {
        edges {
          node {
            id
            databaseId: _id
            name
            handle
            tray_integration_enabled
          }
        }
      }
    }
  }
`,E=r`
  query TeamGithubIntegrationQuery($handle: String!) {
    team(handle: $handle) {
      id
      databaseId: _id
      name
      handle
      githubIntegration: available_integrations(key: "github")
    }
  }
`,D=()=>{let{data:e,loading:t}=b(T),[r,{loading:a}]=n(E,{onCompleted:({team:e})=>{if(S.default.empty(e.githubIntegration)||S.default.null(e.githubIntegration.solution_id)){p(`error`,`Sorry, you cannot connect ${e.name} to GitHub. GitHub integration is not enabled for this program.`);return}_(`/${e.handle}/integrations/${e.githubIntegration.solution_id}`)}});if(t)return(0,w.jsx)(m,{});let{me:{teams:{edges:o}}}=e,s=o.filter(({node:e})=>e.tray_integration_enabled);if(S.default.empty(s))return(0,w.jsx)(`div`,{className:`narrow-wrapper`,children:(0,w.jsx)(y,{top:!0,children:(0,w.jsxs)(h,{children:[(0,w.jsx)(h.Heading,{className:`text-aligned-center`,children:(0,w.jsx)(`h2`,{className:`text-aligned-center margin-0--bottom`,children:`Connect with HackerOne`})}),(0,w.jsxs)(h.Content,{children:[(0,w.jsx)(`p`,{children:`Thank you for installing HackerOne for GitHub.`}),(0,w.jsx)(`p`,{children:`Unfortunately, you do not manage any program to link your GitHub repository.`})]})]})})});let c=new i(new C.default({teamHandle:{type:String,allowedValues:s.map(({node:e})=>e.handle),label:`Program`,uniforms:{transform:e=>s.find(({node:t})=>t.handle===e).node.name,placeholder:`Select a program...`,searchable:!0}}}));return(0,w.jsx)(`div`,{className:`narrow-wrapper`,children:(0,w.jsx)(y,{top:!0,children:(0,w.jsxs)(h,{children:[(0,w.jsx)(h.Heading,{children:(0,w.jsx)(`h2`,{className:`text-aligned-center margin-0--bottom`,children:`Connect with HackerOne`})}),(0,w.jsxs)(h.Content,{children:[(0,w.jsx)(`p`,{children:`Thank you for installing HackerOne for GitHub.`}),(0,w.jsx)(`p`,{children:`You are about to connect a GitHub repository to one of your HackerOne programs.`}),(0,w.jsx)(`p`,{children:`Select the program you want to link your GitHub repository:`}),(0,w.jsxs)(g,{label:!1,placeholder:!0,schema:c,showInlineError:!0,onSubmit:({teamHandle:e})=>{l(),r({variables:{handle:e}})},children:[(0,w.jsx)(d,{}),(0,w.jsx)(v,{}),(0,w.jsx)(f,{disabled:a,color:`blue`,value:`${a?`Loading...`:`Link GitHub repository to program`}`,className:`is-full-width`}),(0,w.jsx)(u,{})]})]})]})})})};D.propTypes={history:x.default.shape({replace:x.default.func.isRequired}),location:x.default.object.isRequired};export{D as default};
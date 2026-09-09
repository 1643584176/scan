const __vite__mapDeps=(i,m=__vite__mapDeps,d=(m.f||(m.f=["static/code_editor-g2DJ2JRb.js","static/rolldown-runtime-DAXXjFlN.js","static/vendor-_WdvpBLr.js","static/vendor-B9d8IRD6.css","static/app-5pKgUmmm.js","static/app-DKLdaBkR.css","static/editor.api-0I2BIQE3.js","static/editor-D8jrZz3P.css","static/monaco.contribution-BWWB7wFD.js","static/code_editor-D9Xoe3D9.css"])))=>i.map(i=>d[i]);
import{o as e}from"./rolldown-runtime-DAXXjFlN.js";import{$_ as t,$u as n,Ax as r,Bl as i,By as a,Ca as o,Dx as s,Fl as c,Fw as l,I_ as u,Iw as d,Li as f,Ll as p,Lr as m,Ly as h,Mf as ee,Mx as te,Nb as g,Nf as ne,Pf as _,Pl as v,Pv as re,Qy as y,Rw as ie,St as ae,Tx as oe,Ux as b,Vx as x,Wi as se,Wn as ce,Xa as le,Xd as S,Xi as ue,Yl as C,Zd as w,av as T,br as de,cp as E,db as fe,eb as D,i_ as pe,iv as O,jx as me,lp as k,nb as he,nv as A,od as j,ov as M,pu as ge,rb as _e,rv as N,sv as P,tb as F,tr as ve,tv as I,zx as ye}from"./vendor-_WdvpBLr.js";import{Cp as L,Gp as R,Gs as be,Js as xe,Ju as Se,Kf as Ce,Ks as we,Nm as Te,Ps as Ee,Rs as De,Sh as z,Sm as B,Th as V,Uf as Oe,_m as ke,ap as H,ba as Ae,dh as U,ep as je,fl as Me,gc as Ne,hc as W,kf as G,pf as Pe,qs as Fe,vm as K,xp as q,yh as J,ym as Y}from"./app-5pKgUmmm.js";import{t as Ie}from"./format_bytes-CNxcX6FD.js";import{j as Le}from"./constants-KKBS4o7v.js";var X=e(ie()),Re=e(ye()),ze=e(ue()),Z=function(e){return e.WorkspaceCreated=`workspace created`,e.WorkspaceDescriptionUpdated=`workspace description updated`,e.WorkspaceDeleted=`workspace deleted`,e.WorkspaceArtifactCreated=`workspace artifact created`,e.WorkspaceArtifactPinned=`workspace artifact pinned`,e.WorkspaceArtifactUnPinned=`workspace artifact unpinned`,e.WorkspaceArtifactUpdated=`workspace artifact updated`,e.WorkspaceArtifactDownloaded=`workspace artifact downloaded`,e.WorkspaceArtifactPreviewed=`workspace artifact previewed`,e.WorkspaceArtifactDeleted=`workspace artifact deleted`,e.WorkspaceArtifactSearched=`workspace artifact searched`,e}({}),Be=L(`
  query ReconContextList {
    reconContextList: recon_contexts {
      pageInfo {
        hasNextPage
        hasPreviousPage
      }
      total_count
      nodes {
        ...ReconContextListNode
      }
    }
  }
`),Ve=L(`
  fragment ReconContextListNode on ReconWorkspaceContext {
    id
    databaseId: _id
    name
    lastUpdatedAt: updated_at
    description
    owner {
      ...ReconContextParticipantNode
    }
    target {
      id
      name
      handle
      profile_picture(size: small)
      type
    }
    collaborators {
      ...ReconContextParticipantNode
    }
  }
`),He=L(`
  fragment ReconArtifactNode on ReconWorkspaceArtifact {
    id
    _id
    name
    pinned
    description
    information_type
    tool_source
    state
    content_type
    byte_size
    contributed_by {
      id
      username
      profile_picture(size: small)
    }
    url
    created_at
  }
`),Ue=L(`
  query ReconContextPage($id: Int!) {
    reconContext: recon_context(id: $id) {
      ...ReconContextNode
    }
  }
`),We=L(`
  query ReconArtifactPage($id: Int!, $search_query: String) {
    reconContext: recon_context(id: $id) {
      ...ReconContextSearchNode
    }
  }
`),Ge=L(`
  fragment ReconArtifactSearchResultNode on ReconWorkspaceArtifactSearchResult {
    id
    artifact_name
    artifact_id
    content
    start_index
    end_index
    start_line_number
    end_line_number
    artifact {
      ...ReconArtifactNode
    }
  }
`),Ke=L(`
  fragment ReconContextSearchNode on ReconWorkspaceContext {
    id
    search(search_query: $search_query) {
      nodes {
        ...ReconArtifactSearchResultNode
      }
    }
  }
`),qe=L(`
  fragment ReconContextNode on ReconWorkspaceContext {
    id
    _id
    name
    description
    owner {
      ...ReconContextParticipantNode
    }
    collaborators {
      ...ReconContextParticipantNode
    }
    artifacts {
      nodes {
        ...ReconArtifactNode
      }
    }
    target {
      id
      handle
      name
      type
    }
    options {
      id
      delete_enabled
    }
  }
`),Q=L(`
  fragment ReconContextParticipantNode on User {
    __typename
    id
    username
    profile_picture(size: small)
  }
`),Je=L(`
  mutation createReconContext($name: String!, $description: String) {
    createReconContext(input: { name: $name, description: $description }) {
      was_successful
      errors(first: 100) {
        edges {
          node {
            id
            type
            field
            message
          }
        }
      }
    }
  }
`),Ye=L(`
  mutation CreateReconArtifact($files: [Upload!]!, $recon_context_id: Int!) {
    createReconArtifact(
      input: { files: $files, recon_context_id: $recon_context_id }
    ) {
      was_successful
      errors {
        edges {
          node {
            id
            type
            message
          }
        }
      }
      recon_context {
        id
        name
        artifacts {
          nodes {
            ...ReconArtifactNode
          }
        }
      }
    }
  }
`),Xe=L(`
  mutation PinReconArtifact($recon_artifact_id: Int!, $pinned: Boolean!) {
    updateReconArtifact(
      input: { recon_artifact_id: $recon_artifact_id, pinned: $pinned }
    ) {
      was_successful
      errors {
        edges {
          node {
            id
            type
            message
          }
        }
      }
      recon_artifact {
        ...ReconArtifactNode
      }
    }
  }
`),Ze=L(`
  mutation UpdateReconArtifact(
    $recon_artifact_id: Int!
    $name: String
    $description: String
  ) {
    updateReconArtifact(
      input: {
        recon_artifact_id: $recon_artifact_id
        name: $name
        description: $description
      }
    ) {
      was_successful
      errors {
        edges {
          node {
            id
            type
            message
          }
        }
      }
      recon_artifact {
        ...ReconArtifactNode
      }
    }
  }
`),Qe=L(`
  mutation updateReconContext(
    $recon_context_id: Int!
    $name: String
    $description: String
  ) {
    updateReconContext(
      input: {
        recon_context_id: $recon_context_id
        name: $name
        description: $description
      }
    ) {
      was_successful
      recon_context {
        ...ReconContextNode
      }
      errors(first: 100) {
        edges {
          node {
            id
            type
            field
            message
          }
        }
      }
    }
  }
`),$e=L(`
  mutation DeleteReconArtifact($recon_artifact_id: Int!) {
    deleteReconArtifact(input: { recon_artifact_id: $recon_artifact_id }) {
      was_successful
      errors {
        edges {
          node {
            id
            message
            type
          }
        }
      }
      recon_context {
        id
        name
        artifacts {
          nodes {
            ...ReconArtifactNode
          }
        }
      }
    }
  }
`),et=L(`
  mutation DeleteReconContext($recon_context_id: Int!) {
    deleteReconContext(input: { recon_context_id: $recon_context_id }) {
      was_successful
      errors {
        edges {
          node {
            id
            type
            message
          }
        }
      }
    }
  }
`),$=l(),tt=new f(new ze.default({name:{type:String,optional:!1,uniforms:{helperText:`Give your project a memorable name`,placeholder:`Acme Corp Target, XSS Investigation, Web Pentest, etc.`}},description:{type:String,label:`Scope and Goal`,optional:!0,uniforms:{component:De,helperText:`Set the focus of the recon project`,maxLength:1024,lengthIndicator:1024,placeholder:`## Goal

## Scope

## Limitations

## References

## Notes

`}}})),nt=({open:e,onClose:t,onAdd:n})=>{let r=(0,X.useRef)(null),[i,{loading:a}]=x(Je,{onCompleted({createReconContext:{was_successful:e,errors:t}}){e?(z.track(Z.WorkspaceCreated),n(),r.current&&r.current.reset()):ke(`Something went wrong:`,Ne(t))}});return(0,$.jsx)(S,{open:e,title:`Create new Workspace`,onClose:t,accessibilityLabel:`Create a new Workspace`,children:(0,$.jsxs)(se,{ref:r,schema:tt,placeholder:!0,onSubmit:e=>{i({variables:{name:e.name,description:e.description??null}}).catch(e=>{B(`error`,e)})},children:[(0,$.jsx)(Fe,{}),(0,$.jsx)(xe,{fields:void 0}),(0,$.jsx)(we,{disabled:a,color:`blue`,size:`small`,inputRef:null,position:`right`,testId:`create-workspace-button`,value:a?`Loading...`:`Create`,className:`is-full-width`}),(0,$.jsx)(be,{})]})})},rt=({owner:e,collaborators:t})=>{let n=(0,X.useContext)(q).me?.gql_id;return(0,$.jsxs)(`div`,{className:`flex mt-md mb-md gap-xs`,children:[e&&(0,$.jsx)(fe,{text:`${e.username} (Owner)${e.id===n?` - you!`:``}`,children:(0,$.jsx)(U,{to:`/${e.username}`,children:(0,$.jsx)(`img`,{alt:`${e.username}'s profile picture`,className:`rounded-full h-lg`,src:e.profile_picture})})}),t.map(e=>(0,$.jsx)(fe,{text:`${e.username} (Collaborator${e.id===n?` - you!`:``})`,children:(0,$.jsx)(U,{to:`/${e.username}`,children:(0,$.jsx)(`img`,{alt:`${e.username}'s profile picture`,className:`rounded-full h-lg`,src:e.profile_picture})})},e.id))]})},it=({reconContext:e})=>{let t=G(Q,e?.owner),n=(G(Q,e?.collaborators)??[]).flatMap(e=>e?[e]:[]);return(0,$.jsxs)(C.Container,{children:[(0,$.jsx)(C.Header,{children:(0,$.jsxs)(`div`,{className:`flex justify-between`,children:[e.target?(0,$.jsx)(`img`,{alt:`Target profile picture`,className:`rounded-full h-lg`,src:e.target.profile_picture}):(0,$.jsx)(he,{size:_e.Large,src:ce}),(0,$.jsx)(`span`,{className:`flex items-center gap-2xs`,children:(0,$.jsx)(`span`,{className:`text-sm`,children:e.lastUpdatedAt?Oe({date:e.lastUpdatedAt}):null})})]})}),(0,$.jsxs)(C.Body,{heading:(0,$.jsx)(U,{to:`/workspaces/${e.databaseId}`,children:e.name}),children:[(0,$.jsx)(Se,{className:`line-clamp-4`,markdown:e.description,disableContextMenu:!0}),e.target&&(0,$.jsx)(`div`,{className:`mt-md`,children:(0,$.jsxs)(N,{children:[`Target:`,` `,(0,$.jsx)(U,{newTab:!0,to:`/${e.target.handle}/`,children:e.target.name}),e.target.type&&(0,$.jsx)(`span`,{className:`ml-xs`,children:(0,$.jsx)(_,{children:Le[e.target.type]})})]})})]}),(0,$.jsx)(C.Footer,{children:t&&(0,$.jsx)(rt,{owner:t,collaborators:n})})]},e.id)},at=()=>(0,$.jsx)(`div`,{className:`mb-md`,children:(0,$.jsx)(h,{variation:a.Information,contentPrimary:`Welcome to the Workspace Beta!`,contentSecondary:`This is an experimental feature to help you collaborate and take notes on the reconnaissance process. It may be a little rough around the edges. Please direct any feedback through the #pentester-feedback channel on Slack.`})}),{RECON_WORKSPACE:ot,RECON_WORKSPACE_CREATE:st}=window.constants.featureToggles,ct=()=>(0,$.jsx)(g,{top:`1l`,bottom:`2xl`,children:(0,$.jsx)(E,{fill:!0,children:(0,$.jsx)(k,{children:`You do not have access to this feature.`})})}),lt=()=>(0,$.jsx)(g,{top:`1l`,bottom:`2xl`,children:(0,$.jsx)(E,{fill:!0,children:(0,$.jsx)(k,{children:`Something went wrong!`})})}),ut=({createEnabled:e,onCreateNew:t})=>(0,$.jsx)(g,{top:`1l`,bottom:`2xl`,children:(0,$.jsx)(E,{fill:!0,children:(0,$.jsx)(k,{children:(0,$.jsxs)(`div`,{className:`flex flex-col text-center justify-center items-center`,children:[(0,$.jsx)(u,{illustration:`nothing_here_2`}),e?(0,$.jsxs)(N,{renderAs:I.Paragraph,children:[`There are no entries`,` `,(0,$.jsx)(`a`,{className:`daisy-link`,onClick:t,children:`click here`}),` `,`to create a new one.`]}):(0,$.jsx)(N,{renderAs:I.Paragraph,children:`Nothing here yet! Wait until someone adds you to a Recon Workspace.`})]})})})}),dt=()=>{let{data:e,refetch:t,loading:n,error:r}=b(Be),{enabled:i,loading:a}=Pe(ot),{enabled:o,loading:s}=Pe(st),[c,l]=(0,X.useState)(!1),u=G(Ve,e?.reconContextList?.nodes?.flatMap(e=>e?[e]:[]))??[];return(0,$.jsx)(`div`,{children:n||a||s?(0,$.jsx)(V,{}):(0,$.jsxs)(j,{children:[(0,$.jsx)(m,{title:Ae(`Workspace`),children:(0,$.jsx)(`meta`,{name:`description`,content:`Workspace`})}),(0,$.jsxs)(`div`,{className:`flex flex-col`,children:[(0,$.jsxs)(`div`,{className:`flex justify-between`,children:[(0,$.jsx)(M,{size:P.Scale500,renderAs:T.H2,children:`Workspaces`}),o&&(0,$.jsx)(y,{variation:F.Primary,onClick:()=>{l(!0)},children:`Create`})]}),(0,$.jsx)(`p`,{className:`mt-sm mb-sm`,children:(0,$.jsx)(N,{variation:O.Subtle,children:`Workspaces are places to collaborate and take notes on the reconnaissance process.`})}),(0,$.jsx)(at,{}),!i&&u.length===0?(0,$.jsx)(ct,{}):r?(0,$.jsx)(lt,{}):u.length===0?i?(0,$.jsx)(ut,{createEnabled:o,onCreateNew:()=>{l(!0)}}):(0,$.jsx)(ct,{}):(0,$.jsx)(`div`,{className:`grid grid-cols-1 gap-md md:grid-cols-2 lg:grid-cols-3 xl:grid-cols-4`,children:u.map(e=>(0,$.jsx)(it,{reconContext:e},e.id))}),(0,$.jsx)(nt,{open:c,onClose:()=>{l(!1)},onAdd:()=>{t().then(()=>{l(!1),Y()})}})]})]})})},ft=({reconContext:e,setSelectedReconArtifact:t})=>{let n=(G(He,e?.artifacts?.nodes?.flatMap(e=>e?[e]:[]))??[]).filter(e=>e?.pinned).flatMap(e=>e?[e]:[]);return(0,$.jsx)(E,{fill:!0,children:(0,$.jsxs)(k,{children:[(0,$.jsx)(M,{renderAs:T.H3,size:P.Scale300,children:`Pinned Artifacts`}),(0,$.jsx)(N,{size:A.Scale300,variation:O.Subtle,children:`Artifacts pinned by collaborators`}),(0,$.jsx)(N,{children:(0,$.jsx)(`ul`,{className:`list-disc p-md`,children:n.length>0?n.map(e=>(0,$.jsx)(`li`,{children:(0,$.jsx)(U,{to:`#`,className:`daisy-link`,onClick:()=>{t(e)},children:e.name})},e.id)):(0,$.jsx)(`li`,{children:`No pinned artifacts`})})})]})})},pt=({reconArtifact:e,onDelete:t})=>{let[n,{loading:r}]=x($e,{onCompleted:({deleteReconArtifact:{was_successful:e,errors:n}})=>{if(e)B(`notice`,`Artifact deleted successfully`),z.track(Z.WorkspaceArtifactDeleted),t();else throw new Ee(n)}}),[i,a]=(0,X.useState)(!1),o=parseInt(e._id,10);return(0,$.jsxs)($.Fragment,{children:[(0,$.jsx)(je,{showModal:i,shouldCloseOnOverlayClick:!0,shouldCloseOnEsc:!0,handleCloseModal:()=>{a(!1)},buttonText:`Delete`,handleButtonClick:()=>{n({variables:{recon_artifact_id:o}}).catch(K)},cancelLinkText:`Cancel`,buttonDisabled:r,cancelLinkDisabled:r,buttonColor:`danger`,title:(0,$.jsx)(`span`,{className:`leading-normal`,children:`Are you sure?`}),overlayClassName:`z-modal`,children:(0,$.jsx)(N,{children:`This will delete this artifact from the workspace.`})}),(0,$.jsx)(y,{testId:`delete-artifact-button-${o}`,variation:F.DangerSecondary,to:`#`,onClick:()=>{a(!0)},disabled:r,iconOnly:!0,icons:{center:{accessibilityLabel:`Delete`,src:de}}})]})},mt=({artifact:e,variation:t=F.Secondary,renderAs:n=D.Button,small:r=!1,disabled:i=!1})=>(0,$.jsx)(y,{testId:`download-artifact-button-${e._id}`,variation:t,onClick:()=>{z.track(Z.WorkspaceArtifactDownloaded,{tool_information_type:e.information_type,tool_source:e.tool_source}),e.url&&H(e.url)},renderAs:n,disabled:i,small:r,iconOnly:!0,icons:{center:{accessibilityLabel:`Download`,src:le}},external:!0}),ht=({reconContext:e,artifact:n,onClose:r,onDelete:i})=>{let a=(0,X.useContext)(q).me?.gql_id,s=parseInt(n._id,10),[c,{loading:l}]=x(Ze,{onCompleted:({updateReconArtifact:{was_successful:e,errors:t}})=>{if(e)z.track(Z.WorkspaceArtifactUpdated,{tool_information_type:n.information_type,tool_source:n.tool_source}),B(`notice`,`Artifact updated successfully`),r();else throw new Ee(t)}}),[u,d]=(0,X.useState)(n.description??``),[f,p]=(0,X.useState)(n.name??``),m=l,h=e?.owner,ee=[n.information_type,n.tool_source].filter(e=>e!==`unknown`);return(0,$.jsxs)(S,{open:!0,title:`Edit artifact`,subtitle:`${n.name} (${Ie(n.byte_size)})`,onClose:r,footer:(0,$.jsxs)(`div`,{className:`flex gap-sm`,children:[n.url&&(0,$.jsx)(mt,{artifact:n,disabled:m}),(n?.contributed_by?.id===a||h?.id===a)&&(0,$.jsx)(pt,{reconArtifact:n,onDelete:i}),(0,$.jsx)(`div`,{className:`grow`}),(0,$.jsx)(y,{testId:`save-artifact-button`,variation:F.Primary,disabled:m||f===``||u===(n.description??``)&&f===n.name,onClick:()=>{c({variables:{recon_artifact_id:s,name:f,description:u}}).catch(K)},children:m?`Saving...`:`Save`})]}),accessibilityLabel:`Artifact details for ${n.name}`,children:[(0,$.jsx)(g,{bottom:`md`,children:(0,$.jsx)(o,{id:`artifact-sheet-name`,name:`artifact-sheet-name`,value:f,onBlur:e=>{e.target.value.length===0&&p(n.name??``)},onChange:e=>{p(e.target.value)},labelText:`Name *`,required:!0})}),(0,$.jsxs)(g,{bottom:`sm`,children:[(0,$.jsx)(t,{text:`Details`,htmlFor:`artifact-sheet-description`}),(0,$.jsx)(g,{bottom:`xs`,children:(0,$.jsx)(N,{size:A.Scale300,variation:O.Subtle,renderAs:I.Paragraph,children:`Changes made to this artifact will be visible to everyone`})}),(0,$.jsx)(Me,{id:`artifact-sheet-description`,name:`artifact-sheet-description`,value:u,onChange:e=>{d(e.target.value)}})]}),ee.map(e=>(0,$.jsx)(_,{children:W(e)},e))]})},gt=()=>(0,$.jsxs)(j,{children:[(0,$.jsx)(g,{bottom:`sm`,children:(0,$.jsx)(M,{size:P.Scale500,renderAs:T.H2,children:`Workspace`})}),(0,$.jsx)(g,{bottom:`md`,children:(0,$.jsx)(N,{variation:O.Subtle,children:`Workspace is a place to collaborate and take notes on the reconnaissance process.`})}),(0,$.jsx)(g,{top:`1l`,bottom:`2xl`,children:(0,$.jsx)(E,{fill:!0,children:(0,$.jsx)(k,{children:`This Workspace is not available or you may not have access to it.`})})})]}),_t=`data:image/svg+xml,%3csvg%20xmlns='http://www.w3.org/2000/svg'%20width='24'%20height='24'%20viewBox='0%200%2024%2024'%3e%3cpath%20d='M12%2017.27L18.18%2021l-1.64-7.03L22%209.24l-7.19-.61L12%202L9.19%208.63L2%209.24l5.46%204.73L5.82%2021z'/%3e%3c/svg%3e`,vt=({reconContextId:e,onDelete:t})=>{let[n,{loading:r}]=x(et,{onCompleted:e=>{e.deleteReconContext.was_successful?(B(`notice`,`Workspace deleted successfully`),z.track(Z.WorkspaceDeleted),t()):K()}}),[i,a]=(0,X.useState)(!1);return(0,$.jsxs)($.Fragment,{children:[(0,$.jsx)(je,{showModal:i,shouldCloseOnOverlayClick:!0,shouldCloseOnEsc:!0,handleCloseModal:()=>{a(!1)},buttonText:`Delete`,handleButtonClick:()=>{n({variables:{recon_context_id:e}}).catch(K)},cancelLinkText:`Cancel`,buttonDisabled:r,cancelLinkDisabled:r,buttonColor:`danger`,title:(0,$.jsx)(`span`,{className:`leading-normal`,children:`Are you sure?`}),children:(0,$.jsx)(N,{children:`This will delete this workspace and all associated data.`})}),(0,$.jsx)(y,{testId:`remove-workspace-button`,onClick:()=>{a(!0)},variation:F.DangerSecondary,iconOnly:!0,icons:{center:{accessibilityLabel:`Delete`,src:de}}})]})},yt=[{label:`Overview`,path:e=>`/workspaces/${e}`},{label:`Artifacts`,path:e=>`/workspaces/${e}/artifacts`}],bt=({reconContext:e})=>{let t=r(),i=(0,X.useContext)(q).me?.gql_id===G(Q,e?.owner)?.id,a=i&&!!e?.options?.delete_enabled;return(0,$.jsxs)($.Fragment,{children:[(0,$.jsx)(m,{title:Ae(`${e.name} | Workspace`),children:(0,$.jsx)(`meta`,{name:`description`,content:`${e.name} | Workspace #${e._id}`})}),(0,$.jsxs)(`div`,{className:`flex justify-between`,children:[(0,$.jsxs)(M,{size:P.Scale500,renderAs:T.H2,children:[e.name,i&&(0,$.jsx)(`div`,{className:`absolute right-0 z-10 opacity-0 group-hover:opacity-100 mt-[-25px]`,children:(0,$.jsx)(y,{testId:`spec-recon-context-name-edit-button`,variation:F.Secondary,renderAs:D.Link,onClick:()=>{},iconOnly:!0,icons:{center:{accessibilityLabel:`edit`,src:`data:image/svg+xml,%3csvg%20xmlns='http://www.w3.org/2000/svg'%20width='24'%20height='24'%20viewBox='0%200%2024%2024'%3e%3cpath%20d='M14.06%209.02l.92.92L5.92%2019H5v-.92l9.06-9.06M17.66%203c-.25%200-.51.1-.7.29l-1.83%201.83l3.75%203.75l1.83-1.83a.996.996%200%200%200%200-1.41l-2.34-2.34c-.2-.2-.45-.29-.71-.29zm-3.6%203.19L3%2017.25V21h3.75L17.81%209.94l-3.75-3.75z'/%3e%3c/svg%3e`}}})})]}),a&&(0,$.jsx)(vt,{reconContextId:parseInt(e._id,10),onDelete:()=>{t.push(`/workspaces`)}})]}),(0,$.jsx)(g,{vertical:`sm`,children:(0,$.jsxs)(N,{variation:O.Subtle,children:[`Workspace`,(0,$.jsx)(`sup`,{children:(0,$.jsx)(_,{icons:{left:{accessibilityLabel:`star`,src:_t},right:{accessibilityLabel:`star`,src:_t}},size:ne.ExtraSmall,color:ee.Blue,children:`Beta`})}),` `,`is a place to collaborate and take notes on the reconnaissance process.`]})}),(0,$.jsx)(`div`,{className:`flex h-spacing-48 items-center content-center gap-lg mb-sm`,children:yt.map(({label:t,path:r})=>(0,$.jsx)(n,{exact:!0,label:t,to:r(e._id)},t))})]})},xt=new f(new ze.default({description:{type:String,label:``,optional:!1,uniforms:{component:De,helperText:`Set the focus of the recon project`,maxLength:6e3,lengthIndicator:6e3,placeholder:`## Goal

## Scope

## Limitations

## References

## Notes

`}}})),St=({reconContextId:e,description:t,onSave:n,onCancel:r})=>{let i=(0,X.useRef)(null),a={description:t},[o,{loading:s}]=x(Qe,{onCompleted({updateReconContext:{was_successful:e,errors:t}}){e?(n(),z.track(Z.WorkspaceDescriptionUpdated),Y(),i.current&&i.current.reset()):ke(`Something went wrong:`,Ne(t))}});return(0,$.jsxs)(se,{ref:i,schema:xt,model:a,placeholder:!0,onSubmit:t=>{o({variables:{recon_context_id:e,description:t.description??null}}).catch(e=>{B(`error`,e)})},children:[(0,$.jsx)(Fe,{}),(0,$.jsx)(xe,{fields:void 0}),(0,$.jsxs)(`div`,{className:`flex justify-end gap-xs align-baseline`,children:[(0,$.jsx)(`div`,{className:`mt-md`,children:(0,$.jsx)(y,{to:`#`,onClick:r,variation:F.Ghost,children:`Cancel`})}),(0,$.jsx)(we,{disabled:s,color:`blue`,size:`small`,inputRef:null,position:`right`,value:s?`Loading...`:`Save`})]}),(0,$.jsx)(be,{})]})},Ct=()=>{let e=(0,X.useContext)(q),{id:t}=te(),{data:n,loading:r,refetch:i}=b(Ue,{variables:{id:parseInt(t,10)}}),a=G(qe,n?.reconContext),o=G(Q,a?.owner),s=(G(Q,a?.collaborators)??[]).flatMap(e=>e?[e]:[]),[c,l]=(0,X.useState)(null),[u,d]=(0,X.useState)(!1),f=e.me?.gql_id,p=o?.id===f;return(0,$.jsx)(`div`,{children:r?(0,$.jsx)(V,{}):a?(0,$.jsxs)(j,{children:[(0,$.jsx)(bt,{reconContext:a}),(0,$.jsxs)(`div`,{className:`grid grid-cols-1 gap-md sm:grid-cols-1 lg:grid-cols-4 xl:grid-cols-6`,children:[(0,$.jsx)(`div`,{className:`row-span-4 col-span-4 group flex`,children:(0,$.jsx)(E,{fill:!0,children:(0,$.jsxs)(k,{children:[(0,$.jsx)(M,{renderAs:T.H2,size:P.Scale400,children:`Scope and Goal`}),(0,$.jsx)(`div`,{className:`mt-md`,children:u?(0,$.jsx)(St,{reconContextId:parseInt(a._id,10),description:a.description??``,onCancel:()=>{d(!1)},onSave:()=>{d(!1)}}):(0,$.jsxs)(`div`,{className:`full relative h-full`,children:[p&&(0,$.jsx)(`div`,{className:`absolute right-0 z-10 opacity-0 group-hover:opacity-100 mt-[-25px]`,children:(0,$.jsx)(y,{testId:`edit-workspace-context-button`,variation:F.Secondary,renderAs:D.Link,onClick:()=>{d(!0)},iconOnly:!0,icons:{center:{accessibilityLabel:`edit`,src:`data:image/svg+xml,%3csvg%20xmlns='http://www.w3.org/2000/svg'%20width='24'%20height='24'%20viewBox='0%200%2024%2024'%3e%3cpath%20d='M14.06%209.02l.92.92L5.92%2019H5v-.92l9.06-9.06M17.66%203c-.25%200-.51.1-.7.29l-1.83%201.83l3.75%203.75l1.83-1.83a.996.996%200%200%200%200-1.41l-2.34-2.34c-.2-.2-.45-.29-.71-.29zm-3.6%203.19L3%2017.25V21h3.75L17.81%209.94l-3.75-3.75z'/%3e%3c/svg%3e`}}})}),(0,$.jsx)(Se,{className:`flex flex-col flex-grow spec-description-markdown`,markdown:a.description,disableContextMenu:!0})]})})]})})}),a.target&&(0,$.jsx)(`div`,{className:`col-span-2 flex`,children:(0,$.jsx)(E,{fill:!0,children:(0,$.jsxs)(k,{children:[(0,$.jsxs)(M,{renderAs:T.H3,size:P.Scale300,children:[`Target: `,a.target.name]}),(0,$.jsx)(N,{size:A.Scale300,variation:O.Subtle,children:`A program that is the target for reconnaissance`}),(0,$.jsxs)(`div`,{className:`flex gap-xs mt-md`,children:[(0,$.jsx)(y,{small:!0,variation:F.Tertiary,onClick:()=>{H(`/${a?.target?.handle}/`)},children:`View Program`}),(0,$.jsx)(y,{small:!0,variation:F.Tertiary,onClick:()=>{H(`/${a?.target?.handle}/reports/new`)},children:`Submit Report`})]})]})})}),(0,$.jsx)(`div`,{className:`col-span-2 flex`,children:(0,$.jsx)(ft,{reconContext:a,setSelectedReconArtifact:l})}),(0,$.jsx)(`div`,{className:`col-span-2 flex`,children:(0,$.jsx)(E,{fill:!0,children:(0,$.jsxs)(k,{children:[(0,$.jsx)(M,{renderAs:T.H3,size:P.Scale300,children:`Collaborators`}),(0,$.jsx)(N,{size:A.Scale300,variation:O.Subtle,children:`Collaborators working with you on the goal`}),o&&(0,$.jsx)(rt,{owner:o,collaborators:s})]})})}),c&&(0,$.jsx)(ht,{reconContext:a,artifact:c,onClose:()=>{l(null)},onDelete:()=>{l(null),i()}})]})]}):(0,$.jsx)(gt,{})})},wt=`data:image/svg+xml,%3csvg%20xmlns='http://www.w3.org/2000/svg'%20width='24'%20height='24'%20viewBox='0%200%2024%2024'%3e%3cpath%20d='M14%204v5c0%201.12.37%202.16%201%203H9c.65-.86%201-1.9%201-3V4h4m3-2H7c-.55%200-1%20.45-1%201s.45%201%201%201h1v5c0%201.66-1.34%203-3%203v2h5.97v7l1%201l1-1v-7H19v-2c-1.66%200-3-1.34-3-3V4h1c.55%200%201-.45%201-1s-.45-1-1-1z'/%3e%3c/svg%3e`,Tt=`data:image/svg+xml,%3csvg%20xmlns='http://www.w3.org/2000/svg'%20width='24'%20height='24'%20viewBox='0%200%2024%2024'%3e%3cpath%20d='M16%209V4h1c.55%200%201-.45%201-1s-.45-1-1-1H7c-.55%200-1%20.45-1%201s.45%201%201%201h1v5c0%201.66-1.34%203-3%203v2h5.97v7l1%201l1-1v-7H19v-2c-1.66%200-3-1.34-3-3z'%20fill-rule='evenodd'/%3e%3c/svg%3e`,Et=({artifacts:e,setSelectedReconArtifact:t,setViewingReconArtifact:n,refetch:r})=>{let[a]=x(Xe,{onCompleted:({updateReconArtifact:e})=>{let{was_successful:t,recon_artifact:n}=e;if(t&&n){let e=n;e.pinned?z.track(Z.WorkspaceArtifactPinned,{tool_information_type:e.information_type,tool_source:e.tool_source}):z.track(Z.WorkspaceArtifactUnPinned,{tool_information_type:e.information_type,tool_source:e.tool_source})}r()}}),o=[new v().setLabel(`Name`).setAccessorKey(`name`).setWidth(`300px`).setCellComponent(e=>(0,$.jsxs)(`div`,{className:`flex gap-xs`,children:[(0,$.jsx)(y,{small:!0,testId:`${e.pinned?`unpin`:`pin`}-artifact-button-${e._id}`,variation:e.pinned?F.Ghost:F.GhostSecondary,renderAs:D.Link,iconOnly:!0,icons:{center:e.pinned?{src:Tt,accessibilityLabel:`Unpin Artifact`}:{src:wt,accessibilityLabel:`Pin Artifact`}},onClick:()=>{a({variables:{recon_artifact_id:parseInt(e._id),pinned:!e.pinned}}).catch(K)}}),(0,$.jsx)(U,{to:`#`,className:`cursor-pointer`,onClick:()=>{n(e)},children:e.name})]})).create(),new v().setLabel(`Tags`).setAccessorKey(`information_type`).setCellComponent(({information_type:e,tool_source:t})=>(0,$.jsxs)(`div`,{className:`flex gap-xs`,children:[e&&e!==`unknown`&&(0,$.jsx)(_,{children:W(e)}),t&&t!==`unknown`&&(0,$.jsx)(_,{children:W(t)})]})).create(),new v().setLabel(`Contributed By`).setCellComponent(e=>e.contributed_by?.username?(0,$.jsx)(`a`,{href:`/${e.contributed_by?.username}`,children:(0,$.jsx)(`img`,{alt:`Contributor profile picture`,className:`rounded-full h-lg mx-spacing-8`,src:e.contributed_by.profile_picture})}):(0,$.jsx)($.Fragment,{children:`N/A`})).create(),new v().setLabel(`Uploaded At`).setAccessorKey(`created_at`).setCellComponent(({created_at:e})=>(0,$.jsx)($.Fragment,{children:Ce({date:re(e)})})).create(),new v().setLabel(`Actions`).setPinned(c.Right).setWidth(`120px`).setCellComponent(e=>(0,$.jsxs)(`div`,{className:`flex items-center gap-xs`,children:[(0,$.jsx)(y,{small:!0,variation:F.Tertiary,renderAs:D.Link,iconOnly:!0,icons:{center:{src:Te,accessibilityLabel:`Edit Artifact`}},onClick:()=>{t(e)},testId:`edit-artifact-button-${e._id}`}),(0,$.jsx)(mt,{small:!0,artifact:e,variation:F.Tertiary,renderAs:D.Link})]})).create()];return(0,$.jsx)(p,{verticalAlignment:i.Center,columns:o,data:e,testId:`recon-artifacts-table`})},Dt=e(d()),Ot=`application/octet-stream`,kt=(e,t)=>{fetch(e,{mode:`cors`}).then(e=>{if(e.ok)e.blob().then(e=>{let n=new FileReader;n.onload=()=>{t(n.result)},n.readAsDataURL(e)}).catch(e=>{throw e});else throw Error(`Failed to fetch artifact contents`)}).catch(e=>{throw e})},At=({artifact:e})=>{let[t,n]=(0,X.useState)(void 0),r=e.content_type??Ot,i=r===`application/pdf`;return(0,X.useEffect)(()=>{e.url&&e.url&&kt(e.url??``,n)},[]),t?(0,$.jsx)(`div`,{className:`media-preview flex flex-row size-full place-content-center`,children:(0,$.jsx)(`object`,{data:i?t+`#view=FitH&toolbar=0&navpanes=0&scrollbar=0`:t,type:r,className:(0,Dt.default)(`place-self-center`,{"size-full":i,"size-fit":!i}),title:`Preview of ${e.name??`artifact`}`,children:(0,$.jsx)(`p`,{children:`Preview not supported for this file type`})})}):(0,$.jsx)(`p`,{children:`Loading...`})},jt=(0,X.lazy)(async()=>await pe(()=>import(`./code_editor-g2DJ2JRb.js`),__vite__mapDeps([0,1,2,3,4,5,6,7,8,9]))),Mt=[`application/xml`,`application/json`,`application/octet-stream`],Nt=[R.Configuration,R.GraphqlSchema,R.IntrusionAlerts,R.NetworkInformation,R.NetworkTrafficData,R.Sbom,R.SourceCode,R.VulnerabilityScanReport,R.WebApplicationVulnerabilities,R.WebServerVulnerabilities,R.WirelessNetworkData],Pt=e=>!!e.information_type&&Nt.includes(e.information_type)||!!e.content_type&&(e.content_type.startsWith(`text/`)||Mt.includes(e.content_type)),Ft=({artifact:e,onClose:t})=>{let[n,r]=(0,X.useState)(!1),i;return i=Pt(e)?(0,$.jsx)(jt,{testId:`text-artifact-preview-editor`,content:e.url?{uri:e.url}:void 0,fullscreen:n,setFullscreen:r,options:{readOnly:!0,wordWrap:`on`}}):(0,$.jsx)(At,{artifact:e}),(0,$.jsx)(S,{open:!0,title:e.name??`Preview`,onClose:t,size:n?{default:w.full}:{default:w.full,sm:w.full,md:w.full,lg:w[`10/12`],xl:w[`8/12`],"2xl":w[`6/12`]},footer:(0,$.jsxs)(`div`,{className:`flex gap-sm`,children:[(0,$.jsx)(`div`,{className:`grow`}),(0,$.jsx)(y,{testId:`download-artifact-button`,variation:F.Primary,onClick:()=>{z.track(Z.WorkspaceArtifactDownloaded,{tool_information_type:e.information_type,tool_source:e.tool_source}),e.url&&H(e.url)},children:`Download`})]}),accessibilityLabel:`Artifact details for ${e.name}`,children:i})},It=({onClose:e})=>(0,$.jsxs)(S,{open:!0,title:`Search Help`,onClose:e,children:[(0,$.jsx)(`p`,{className:`mb-sm`,children:`Search query supports a variety of operators and filters to help you find the artifacts with the contents you are looking for.`}),(0,$.jsxs)(`p`,{className:`mb-sm`,children:[`Here are some examples of search queries you can use:`,(0,$.jsxs)(`ul`,{className:`list`,children:[(0,$.jsx)(`li`,{children:(0,$.jsx)(U,{to:`?${new URLSearchParams({q:`content:/([0-9]{2,3}\\.){3}[0-9]{1,3}/`}).toString()}`,children:`Search for IPv4 and IPv6 addresses`})}),(0,$.jsx)(`li`,{children:(0,$.jsx)(U,{to:`?${new URLSearchParams({q:`content:\\:/80|8080|443/`}).toString()}`,children:`Find Common Web Ports`})}),(0,$.jsx)(`li`,{children:(0,$.jsx)(U,{to:`?${new URLSearchParams({q:`technologies OR tech`}).toString()}`,children:`Find references to tech`})}),(0,$.jsx)(`li`,{children:(0,$.jsx)(U,{to:`?${new URLSearchParams({q:`tool_source:nmap`}).toString()}`,children:`Find data from a specific tool, like Nmap`})})]})]}),(0,$.jsxs)(`p`,{className:`mb-sm`,children:[`For more details on using Lucene’s query syntax, refer to the official`,` `,(0,$.jsx)(U,{external:!0,to:`https://lucene.apache.org/core/2_9_4/queryparsersyntax.html`,children:`Lucene documentation`}),`.`]}),(0,$.jsx)(M,{size:P.Scale400,children:`Syntax`}),(0,$.jsx)(`p`,{className:`mb-sm`,children:`The query string is parsed into a series of terms and operators. A term can be a single word or a phrase, surrounded by double quotes which searches for all the words in the phrase, in the same order.`}),(0,$.jsx)(`p`,{className:`mb-sm`,children:`Operators allow you to customize the search the available options are explained below.`}),(0,$.jsx)(M,{size:P.Scale400,children:`Fields`}),(0,$.jsxs)(`p`,{className:`mb-sm`,children:[`You can specify a field name to search for contents specifically in that field. For example, to find a specific file you can search for`,(0,$.jsx)(`code`,{children:`name:my_filename.json`}),(0,$.jsxs)(`ul`,{className:`list mt-sm`,children:[(0,$.jsxs)(`li`,{children:[(0,$.jsx)(`em`,{children:`name`}),` - the filename you are looking form`]}),(0,$.jsxs)(`li`,{children:[(0,$.jsx)(`em`,{children:`tool_source`}),` - the name of the tool tagged for the artifact`]}),(0,$.jsxs)(`li`,{children:[(0,$.jsx)(`em`,{children:`information_type`}),` - the type of information tagged for the artifact`]}),(0,$.jsxs)(`li`,{children:[(0,$.jsx)(`em`,{children:`content`}),` - the content of the artifact`]})]})]}),(0,$.jsx)(M,{size:P.Scale400,children:`Grouping`}),(0,$.jsxs)(`p`,{className:`mb-sm`,children:[`You can group terms using parentheses to control the order of the boolean operators. For example, to find all the json files that contain the word "password" you can search for`,` `,(0,$.jsx)(`code`,{children:`name:password_files.json AND (password)`}),`. The default grouping is AND, but you can use OR to find artifacts where the term may not exist in all, `,(0,$.jsx)(`code`,{children:`80 OR 8080 OR 443`})]}),(0,$.jsx)(M,{size:P.Scale400,children:`Wildcards`}),(0,$.jsxs)(`p`,{className:`mb-sm`,children:[`Wildcard searches can be run on individual terms, using ? to replace a single character, and * to replace zero or more characters. For example, to find all the json files you can search for `,(0,$.jsx)(`code`,{children:`name:*.json`})]}),(0,$.jsx)(M,{size:P.Scale400,children:`Results`}),(0,$.jsx)(`p`,{className:`mb-sm`,children:`Searching will return all the artifacts that match the search query. When content matches the query, an artifact can be listed more than one time with the relevant content highlighted in the Snippet column.`})]}),Lt=e=>e.split(/(<em>.*?<\/em>)/).filter(Boolean).map((e,t)=>e.startsWith(`<em>`)&&e.endsWith(`</em>`)?(0,$.jsx)(_,{color:ee.Yellow,rounded:!1,size:ne.Medium,children:e.slice(4,-5)},t):(0,$.jsx)(`span`,{children:e},t)),Rt=({setSelectedReconArtifact:e,artifactSearchResults:t,isLoading:n})=>{let r=[new v().setLabel(`Name`).setAccessorKey(`artifact_name`).setWidth(`300px`).setCellComponent(t=>(0,$.jsxs)(U,{to:`#`,className:`cursor-pointer`,onClick:n=>{n.preventDefault(),e&&t?.artifact&&e(t.artifact)},children:[t.artifact_name,`:`,t.start_line_number,`:`,t.end_line_number]})).create(),new v().setLabel(`Snippet`).setAccessorKey(`content`).setCellComponent(e=>(0,$.jsx)(`div`,{style:{whiteSpace:`pre-line`,height:`150px`,overflow:`scroll`,width:`100%`},children:e.content?Lt(e.content):`No preview available`})).create(),new v().setLabel(`Actions`).setPinned(c.Right).setWidth(`120px`).setCellComponent(t=>t.artifact?(0,$.jsxs)(`div`,{className:`flex items-center gap-xs`,children:[(0,$.jsx)(y,{small:!0,variation:F.Tertiary,renderAs:D.Link,iconOnly:!0,icons:{center:{src:Te,accessibilityLabel:`Edit Artifact`}},onClick:()=>{e&&e(t.artifact)},testId:`edit-artifact-button-${t.artifact_id}`}),(0,$.jsx)(mt,{small:!0,artifact:t.artifact,variation:F.Tertiary,renderAs:D.Link})]}):(0,$.jsx)($.Fragment,{})).create()];return(0,$.jsx)(p,{verticalAlignment:i.Center,columns:r,data:t??[],testId:`recon-artifacts-table`,isLoading:n})},zt=({error:e})=>(0,$.jsx)(h,{contentPrimary:`Search Failed`,contentSecondary:`Encountered the following error: ${e.message}`,variation:a.Error}),Bt=()=>(0,$.jsx)(h,{contentPrimary:`No Results`,contentSecondary:`Try searching for something else`,variation:a.Information}),Vt=({reconContextId:e,searchQuery:t,setSelectedReconArtifact:n})=>{let{data:r,error:i,loading:a}=b(We,{variables:{id:e,search_query:t}}),o=G(Ge,G(Ke,r?.reconContext)?.search?.nodes?.flatMap(e=>e?[e]:[])),s=o?[...o]:[];return(0,$.jsx)(g,{top:`1l`,children:(0,$.jsx)(E,{fill:!0,children:a?(0,$.jsx)(Rt,{isLoading:!0}):i?(0,$.jsx)(zt,{error:i}):s.length>0?(0,$.jsx)(Rt,{isLoading:!1,setSelectedReconArtifact:n,artifactSearchResults:s}):(0,$.jsx)(Bt,{})})})},Ht=({reconContextId:e,handleSearchInvoked:t,handleSearchCleared:n,setSelectedReconArtifact:i})=>{let a=r(),s=me(),c=new URLSearchParams(s.search).get(`q`)??``,[l,u]=(0,X.useState)(c),[d,f]=(0,X.useState)(!1),p=()=>{l===``?a.push({pathname:s.pathname}):a.push({pathname:s.pathname,search:new URLSearchParams({q:l}).toString()})};return(0,X.useEffect)(()=>{c===``?n():(f(!1),u(c),t(),z.track(Z.WorkspaceArtifactSearched))},[c,n,t,u]),(0,$.jsxs)($.Fragment,{children:[(0,$.jsx)(g,{top:`1l`,bottom:`xl`,children:(0,$.jsx)(E,{fill:!0,children:(0,$.jsx)(k,{children:(0,$.jsxs)(`div`,{className:`flex justify-between`,children:[(0,$.jsx)(`div`,{className:`flex flex-col grow`,children:(0,$.jsx)(o,{value:l,onEnter:p,labelText:`Search artifacts`,onChange:e=>{u(e.target.value)}})}),(0,$.jsx)(`div`,{className:`flex flex-col ml-sm mt-spacing-28`,children:(0,$.jsx)(y,{variation:F.Tertiary,onClick:()=>{f(!0)},iconOnly:!0,icons:{center:{src:ve,accessibilityLabel:`Filter`}}})}),(0,$.jsx)(`div`,{className:`flex flex-col ml-sm mt-spacing-28`,children:(0,$.jsx)(y,{variation:F.Tertiary,onClick:p,iconOnly:!0,icons:{center:{accessibilityLabel:`search`,src:ge}}})})]})})})}),c&&(0,$.jsx)(Vt,{searchQuery:c,reconContextId:e,setSelectedReconArtifact:i}),d&&(0,$.jsx)(It,{onClose:()=>{f(!1)}})]})},Ut=()=>{let{id:e}=te(),t=parseInt(e,10),{data:n,loading:r,refetch:i}=b(Ue,{variables:{id:t}}),a=G(qe,n?.reconContext),[o,s]=(0,X.useState)(!0),[c,l]=(0,X.useState)(null),[u,d]=(0,X.useState)(null),f=G(He,a?.artifacts?.nodes?.flatMap(e=>e?[e]:[])),p=f?[...f]:[],[m,{loading:h}]=x(Ye,{onCompleted:e=>{e.createReconArtifact.was_successful?(z.track(Z.WorkspaceArtifactCreated),Y()):K()},refetchQueries:[Ue,`ReconContextPage`]});return(0,$.jsx)(`div`,{children:r?(0,$.jsx)(V,{}):a?(0,$.jsxs)(j,{children:[(0,$.jsx)(bt,{reconContext:a}),(0,$.jsx)(Ht,{handleSearchInvoked:()=>{s(!1)},handleSearchCleared:()=>{i(),s(!0)},setSelectedReconArtifact:d,reconContextId:t}),(0,$.jsx)(g,{top:`1l`,children:o&&(0,$.jsx)(E,{fill:!0,children:p.length>0?(0,$.jsxs)($.Fragment,{children:[(0,$.jsx)(Et,{artifacts:p,setSelectedReconArtifact:l,setViewingReconArtifact:d,refetch:()=>{i()}}),(0,$.jsx)(ae,{onDrop:e=>{m({variables:{recon_context_id:parseInt(a._id,10),files:e}})},children:({getRootProps:e,getInputProps:t,isDragActive:n})=>(0,$.jsx)(`section`,{children:(0,$.jsxs)(`div`,{...e(),children:[(0,$.jsx)(`input`,{...t()}),(0,$.jsx)(`div`,{className:(0,Dt.default)(`h-64 p-xl text-center`,{"bg-blue-900":n}),children:(0,$.jsx)(N,{renderAs:I.Paragraph,children:h?(0,$.jsxs)($.Fragment,{children:[(0,$.jsx)(V,{}),`Uploading artifacts, standby!`]}):`Drag and drop (or click) to add more files to collaborate on. We recommend sharing Nmap scans, Burp suite reports, Nessus scans, and other recon related artifacts.`})})]})})})]}):(0,$.jsx)($.Fragment,{children:(0,$.jsx)(ae,{onDrop:e=>{m({variables:{recon_context_id:parseInt(a._id,10),files:e}})},children:({getRootProps:e,getInputProps:t,isDragActive:n})=>(0,$.jsx)(`section`,{children:(0,$.jsxs)(`div`,{...e({className:`dropzone`}),children:[(0,$.jsx)(`input`,{...t()}),(0,$.jsx)(`div`,{className:(0,Dt.default)(`flex flex-col text-center items-center justify-center p-xl`,{"bg-blue-900":n}),children:(0,$.jsx)(N,{renderAs:I.Paragraph,children:`Drag and drop (or click) to add files you want to collaborate on. We recommend sharing Nmap scans, Burp suite reports, Nessus scans, and other recon related artifacts.`})})]})})})})})}),c&&(0,$.jsx)(ht,{reconContext:a,artifact:c,onDelete:()=>{l(null),i()},onClose:()=>{l(null)}}),u&&(0,$.jsx)(Ft,{artifact:u,onClose:()=>{d(null)}})]}):(0,$.jsx)(gt,{})})},Wt=({match:{path:e}})=>(0,$.jsxs)(s,{children:[(0,$.jsx)(J,{exact:!0,path:`${e}`,component:dt,area:`workspaces`,feature:`list`}),(0,$.jsx)(J,{exact:!0,path:`${e}/new`,component:dt,area:`workspaces`,feature:`new`}),(0,$.jsx)(J,{exact:!0,path:`${e}/:id`,component:Ct,area:`workspaces`,feature:`show`}),(0,$.jsx)(J,{exact:!0,path:`${e}/:id/artifacts`,component:Ut,area:`workspaces`,feature:`artifacts`}),(0,$.jsx)(J,{exact:!0,path:`${e}/documents`,render:()=>(0,$.jsx)(oe,{to:`${e}/artifacts`})})]});Wt.propTypes={match:Re.default.object.isRequired};export{Wt as ReconWorkspaceRouter,Wt as default};
import{o as e}from"./rolldown-runtime-DAXXjFlN.js";import{Fw as t,Kx as n,Ly as r,Nb as i,Qd as a,Qy as o,Rw as s,cp as c,lp as l,qx as u,zx as d}from"./vendor-_WdvpBLr.js";import{Ah as f,Nf as p,Rf as m,Sm as h,T as g,Th as _,Uf as v,_h as y,dh as b,ep as x,k as S,qr as C,vh as w,ym as T}from"./app-5pKgUmmm.js";import{n as E,t as D}from"./beta-lightmode-CsXkRd9t.js";var O=e(s()),k=e(d()),A=t(),j=({onConfirm:e,loading:t,title:n,children:r})=>{let[i,s]=(0,O.useState)(!1);return(0,A.jsxs)(A.Fragment,{children:[(0,A.jsx)(x,{showModal:i,shouldCloseOnOverlayClick:!0,shouldCloseOnEsc:!0,handleCloseModal:()=>s(!1),buttonText:`Enable feature`,handleButtonClick:e,cancelLinkText:`Cancel`,buttonDisabled:t,cancelLinkDisabled:t,buttonColor:`blue`,title:(0,A.jsx)(`span`,{className:`leading-normal`,children:n}),children:(0,A.jsx)(a,{children:r})}),(0,A.jsx)(o,{variation:`secondary`,onClick:()=>s(!0),children:`I'm ready`})]})};j.propTypes={onConfirm:k.default.func,loading:k.default.bool,title:k.default.string,children:k.default.node},u();var M=n`
  fragment LegacyFeatureTeamFragment on Team {
    legacy_features {
      id
      key
      title
      description
      deadline
      migration_guide_url
    }
  }
`,N=n`
  query TeamLegacyFeatureTogglesQuery($handle: String!) {
    teams(first: 1, where: { handle: { _eq: $handle } }) {
      nodes {
        id
        name
        ...LegacyFeatureTeamFragment
      }
    }
  }
  ${M}
`,P=n`
  mutation enableLegacyTeamFeatureMutation(
    $feature_key: String!
    $team_id: ID!
  ) {
    enableLegacyTeamFeatureMutation(
      input: { feature_key: $feature_key, team_id: $team_id }
    ) {
      was_successful
      team {
        id
        name
        ...LegacyFeatureTeamFragment
      }
      errors {
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
  ${M}
`,F=({teamHandle:e})=>{let{isDarkModeEnabled:t}=p(),{data:n,loading:o}=w(N,{variables:{handle:e},fetchPolicy:`cache-and-network`}),[s,{loading:u}]=y(P,{onCompleted:({enableLegacyTeamFeatureMutation:{was_successful:e,errors:t}})=>{let n=t?.edges?.[0]?.node?.message;e?T():h(`error`,n)}});if(o||!n)return(0,A.jsx)(_,{});let d=n.teams.nodes[0],f=d.legacy_features;return(0,A.jsxs)(A.Fragment,{children:[(0,A.jsx)(`h3`,{className:`daisy-h3`,children:`Legacy Features`}),(0,A.jsx)(l,{edgeToEdge:!0,children:f.length>0?f.map(e=>(0,A.jsxs)(`div`,{children:[(0,A.jsxs)(c,{fill:`true`,orientation:`horizontal`,padding:`md`,children:[(0,A.jsx)(l,{flexBasis:`100%`,children:(0,A.jsxs)(a,{children:[(0,A.jsx)(`h4`,{className:`text-base mb-2xs font-bold`,children:e.title}),(0,A.jsx)(`p`,{className:`text-sm mb-md`,children:e.description||`No description provided.`}),(0,A.jsx)(`p`,{className:`text-sm`,children:(0,A.jsxs)(`span`,{className:m({end:e.deadline})<=0?`text-red-300`:``,children:[`Migration required before`,` `,v({date:e.deadline})]})}),(0,A.jsx)(`p`,{className:`text-sm`,children:(0,A.jsx)(b,{to:e.migration_guide_url,children:`Migration Guide`})})]})}),(0,A.jsx)(l,{children:(0,A.jsx)(`div`,{className:`flex h-full flex-col w-[120px] text-center items-center justify-center`,children:(0,A.jsxs)(j,{loading:u,title:`Enabling feature "${e.title}"`,onConfirm:()=>s({variables:{feature_key:e.key,team_id:d.id}}),children:[(0,A.jsxs)(`p`,{children:[`Are you sure you want to enable this feature for the`,` `,d.name,` program?`]}),(0,A.jsxs)(`p`,{className:`mb-spacing-20`,children:[`Please make sure you've read the`,` `,(0,A.jsx)(b,{to:e.migration_guide_url,children:`migration guide.`})]}),(0,A.jsx)(r,{variation:`warning`,contentPrimary:`Warning: This action cannot be undone!`})]})})})]}),(0,A.jsx)(i,{bottom:`16`})]},e.key)):(0,A.jsxs)(`div`,{className:`flex flex-col justify-center text-center`,children:[(0,A.jsx)(`img`,{src:t?E:D,className:`max-h-[406px]`,alt:`legacy feature illustration`}),(0,A.jsx)(a,{children:(0,A.jsx)(`p`,{className:`mt-spacing-20 text-neutral-300 dark:text-neutral-800`,children:`No legacy features right now.`})})]})})]})};F.propTypes={teamHandle:k.default.string.isRequired},F.displayName=`TeamLegacyFeatureToggles`;var I=({match:e,match:{params:{handle:t}}})=>(0,A.jsx)(C,{children:(0,A.jsx)(g,{header:(0,A.jsx)(S,{match:e}),content:(0,A.jsx)(A.Fragment,{children:(0,A.jsx)(F,{teamHandle:t})}),footer:(0,A.jsx)(f,{}),hasBackground:!1})});I.propTypes={match:k.default.shape({params:k.default.shape({handle:k.default.string.isRequired}).isRequired}).isRequired};export{I as default};
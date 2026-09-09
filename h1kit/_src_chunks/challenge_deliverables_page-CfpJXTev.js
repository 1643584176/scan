import{o as e}from"./rolldown-runtime-DAXXjFlN.js";import{Fw as t,Kx as n,Ll as r,Mx as i,Nb as a,Pl as o,Qy as s,Rw as c,Xa as l,cp as u,db as d,ov as f,qx as p,rv as m,sv as h,zx as g}from"./vendor-_WdvpBLr.js";import{Kf as _,T as v,Wf as y,of as b,qr as x,vh as S}from"./app-5pKgUmmm.js";var C=e(g());p();var w=e(c()),T=t(),{challengeSummaryReport:E}=window.constants.engagementDeliverables,D={[E]:`challenge-summary-report`},O=n`
  query EngagementDeliverableDownloadTableQuery($handle: String!) {
    team(handle: $handle) {
      id
      is_team_member
      summary_report_delivery_date
      engagement_deliverables {
        nodes {
          id
          name
          created_at
          source
          uploaded_by {
            id
            name
          }
          deliverable_type
          attachment {
            id
            expiring_url
          }
        }
      }
      challenge_setting {
        id
        stops_at
      }
    }
  }
`,k=({is_team_member:e})=>[new o().setLabel(`Name`).setAccessorKey(`name`).setCellComponent(({name:e,id:t})=>j(t,e)).create(),new o().setLabel(`Creator`).setAccessorKey(`creator`).setCellComponent(({creator:e,id:t})=>e?j(t,e):`--`).create(),new o().setLabel(`Type`).setAccessorKey(`type`).setCellComponent(({type:e,id:t})=>j(t,`Summary Report`)).create(),new o().setLabel(`Date generated`).setAccessorKey(`date_generated`).setCellComponent(({date_generated:e,id:t})=>j(t,_({date:e,options:{monthAndYear:!1}}),`date_generated`)).create(),new o().setLabel(``).setAccessorKey(`download`).setWidth(`max-content`).setCellComponent(({download:t,type:n})=>(0,T.jsx)(A,{download:t,downloadable:e,type:n})).create()],A=({download:e,downloadable:t,type:n})=>{let[r,i]=(0,w.useState)(!1),{trackWithOrganizationGroup:a}=b();return e==null?null:(0,T.jsx)(N,{condition:r,message:`Download started!`,children:(0,T.jsx)(s,{testId:`spec-download-report-button-${D[n]}`,small:!0,disabled:!t,variation:`tertiary`,onClick:t=>{e.attachment&&(a(`engagement deliverable download clicked`,{feature:`engagement-deliverables`,path:window.location.pathname,deliverable_type:n,deliverable_id:e.id}),i(!0),window.open(e.attachment.expiring_url,`_blank`),setTimeout(()=>i(!1),3e3))},external:!0,iconOnly:!0,icons:{center:{src:l,accessibilityLabel:`Download challenge report`}}})})};A.propTypes={download:C.default.object,downloadable:C.default.bool,type:C.default.string};var j=(e,t,n)=>e===`placeholder-summary-report`?(0,T.jsxs)(`span`,{className:`text-neutral-400 dark:text-neutral-950`,children:[n===`date_generated`&&`ETA `,t]}):t,M=e=>{let t=(e.team.engagement_deliverables?.nodes).map((e,t)=>({id:e.name+t,name:e.name,creator:e.uploaded_by?.name,type:e.deliverable_type,date_generated:e.created_at,download:e,source:e.source})),n=y()<e.team.challenge_setting.stops_at;return t.length===0&&n&&t.unshift({id:`placeholder-summary-report`,name:`Final Summary Report`,creator:`--`,type:E,date_generated:e.team.summary_report_delivery_date,download:null}),t},N=({condition:e,message:t,children:n})=>e?(0,T.jsx)(d,{text:t,testId:`download-report-info-tooltip`,children:n}):n;N.propTypes={condition:C.default.bool,message:C.default.string,children:C.default.node};var P=({teamHandle:e})=>{let{data:t,isLoading:n}=S(O,{variables:{handle:e}});if(!t?.team?.is_team_member)return null;let i=n?[]:M(t);return(0,T.jsx)(T.Fragment,{children:(0,T.jsx)(a,{bottom:`2xl`,children:(0,T.jsx)(u,{fill:!0,children:(0,T.jsx)(r,{isLoading:n,isPaginated:!0,pageSize:10,columns:k(t.team),data:i,testId:`engagement-deliverables-table`})})})})};P.propTypes={teamHandle:C.default.string.isRequired};var F=()=>{let{handle:e}=i();return(0,T.jsx)(x,{children:(0,T.jsx)(v,{content:(0,T.jsxs)(a,{bottom:`48`,children:[(0,T.jsx)(a,{bottom:`sm`,children:(0,T.jsx)(f,{size:h.Scale500,renderAs:`h2`,children:`Deliverables`})}),(0,T.jsx)(a,{bottom:`md`,children:(0,T.jsx)(m,{variation:`subtle`,children:`These are the deliverables available during your challenge.`})}),(0,T.jsx)(P,{teamHandle:e})]}),hasBackground:!1})})};export{F as default};
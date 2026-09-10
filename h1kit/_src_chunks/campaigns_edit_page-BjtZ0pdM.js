import{o as e}from"./rolldown-runtime-DAXXjFlN.js";import{Ax as t,Fw as n,Kx as r,Rw as i,qx as a}from"./vendor-_WdvpBLr.js";import{Sm as o,Yf as s,_h as c,bi as l,hf as u,yi as d,ym as f}from"./app-5pKgUmmm.js";import{t as p}from"./campaign_form_wrapper-C3k9mv8l.js";var m=e(i());a();var h=n(),g=r`
  mutation UpdateCampaign($input: UpdateCampaignInput!) {
    updateCampaign(input: $input) {
      was_successful
      errors {
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
`,{statuses:_}=constants.campaigns,v=()=>{let{store:e,dispatch:n}=(0,m.useContext)(l),{organization:r}=(0,m.useContext)(u),i=t(),[a,{loading:v}]=c(g,{onCompleted:({updateCampaign:{was_successful:e,errors:t}})=>{e?(n({type:d.RESET,value:null}),f(),i.push(`/organizations/${r.handle}/campaigns`)):o(`error`,`Something went wrong: ${t.edges[0].node.field?t.edges[0].node.field:``} ${t.edges[0].node.message}`)}});return(0,h.jsx)(p,{isEdit:!0,isActiveEdit:e.status===_.active,onSave:()=>a({variables:{input:{campaign_id:e.id,bounty_table_row_id:e.bounty_table_row?e.bounty_table_row.id:null,start_date:s(e.start_date,`01:00:00`,`UTC`).toISOString(),end_date:s(e.end_date,`23:00:00`,`UTC`).toISOString(),critical:parseFloat(e.critical),high:parseFloat(e.high),medium:parseFloat(e.medium),low:parseFloat(e.low),structured_scope_ids:e.structured_scope_ids,researchers_information:e.researchers_information}}}),isLoading:v,onBack:()=>{n({type:d.RESET,value:null}),i.push(`/organizations/${r.handle}/campaigns`)}})};export{v as default};
import{o as e}from"./rolldown-runtime-DAXXjFlN.js";import{Ax as t,Fw as n,Kx as r,Rw as i,qx as a}from"./vendor-_WdvpBLr.js";import{Sh as o,Sm as s,Yf as c,_h as l,bi as u,hf as d,wi as f,yi as p,ym as m}from"./app-5pKgUmmm.js";import{t as h}from"./campaign_form_wrapper-C3k9mv8l.js";import{r as g}from"./bounty_competitiveness-Byys0NW5.js";var _=e(i());a();var v=n(),y=r`
  mutation CreateCampaign($input: CreateCampaignInput!) {
    createCampaign(input: $input) {
      campaign {
        id
      }
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
`,b=()=>{let{store:e,dispatch:n}=(0,_.useContext)(u),{organization:r}=(0,_.useContext)(d),i=t(),[a,{loading:b}]=l(y,{onCompleted:({createCampaign:{campaign:t,was_successful:n,errors:a}})=>{n?(o.track(f,{team_id:e.team?.id,team_handle:e.team?.handle,organization_id:r.id,organization_handle:r.handle,campaign_id:t.id,critical_multiplier:e.critical,high_multiplier:e.high,offer_percentile_position_critical:e.bounty_multiplier_recommendation?.critical[g[e.critical]],offer_percentile_position_high:e.bounty_multiplier_recommendation?.high[g[e.high]]}),window.Intercom?.(`trackEvent`,`campaign-created`),m(),i.push(`/organizations/${r.handle}/campaigns`)):s(`error`,`Something went wrong: ${a.edges[0].node.field?a.edges[0].node.field:``} ${a.edges[0].node.message}`)}});return(0,_.useEffect)(()=>{e.id&&n({type:p.RESET})},[]),(0,v.jsx)(h,{isEdit:!1,onSave:()=>a({variables:{input:{team_id:e.team.id,bounty_table_row_id:e.bounty_table_row?e.bounty_table_row.id:null,campaign_objective_id:e.campaign_objective.id,start_date:c(e.start_date,`01:00:00`,`UTC`).toISOString(),end_date:c(e.end_date,`23:00:00`,`UTC`).toISOString(),campaign_type:e.campaign_type,critical:parseFloat(e.critical),high:parseFloat(e.high),medium:parseFloat(e.medium),low:parseFloat(e.low),structured_scope_ids:e.structured_scope_ids,researchers_information:e.researchers_information}}}),isLoading:b,onBack:()=>{let t=e.campaign_objective.category;n({type:p.RESET_FOR_NAVIGATION,value:null}),i.push(`/organizations/${r.handle}/campaigns/${t}/select_objective`)}})};export{b as default};
import{o as e}from"./rolldown-runtime-DAXXjFlN.js";import{$y as t,Fw as n,Kx as r,Lr as i,Nb as a,Q_ as o,Qy as s,Rw as c,Y_ as l,cp as u,df as d,ov as f,qx as p,rv as m,zx as h}from"./vendor-_WdvpBLr.js";import{Ah as g,Sm as _,T as v,Th as y,_h as b,ba as x,ff as S,k as C,pr as w,qr as T,vh as E,ym as D}from"./app-5pKgUmmm.js";var O=e(h()),k=e(c());p();var A=n(),{ENABLE_METRIC_DISPLAY_CONFIGURATION:j}=constants.featureToggles,M=`Something went wrong while updating display options.
  Please contact ${window.constants.notification.support_link} if the problem persists.`,N=r`
  mutation UpdateTeamDisplayOptionsSettings(
    $team_id: ID!
    $show_minimum_bounty: Boolean
    $show_reports_resolved: Boolean
    $show_mean_first_response_time: Boolean
    $show_mean_report_triage_time: Boolean
    $show_mean_resolution_time: Boolean
    $show_total_bounties_paid: Boolean
    $show_average_bounty: Boolean
    $show_mean_bounty_time: Boolean
    $show_top_bounties: Boolean
    $show_total_reports_per_asset: Boolean
    $show_total_reports_per_severity: Boolean
  ) {
    updateTeamDisplayOptions(
      input: {
        team_id: $team_id
        show_minimum_bounty: $show_minimum_bounty
        show_reports_resolved: $show_reports_resolved
        show_mean_first_response_time: $show_mean_first_response_time
        show_mean_report_triage_time: $show_mean_report_triage_time
        show_mean_resolution_time: $show_mean_resolution_time
        show_mean_bounty_time: $show_mean_bounty_time
        show_total_bounties_paid: $show_total_bounties_paid
        show_average_bounty: $show_average_bounty
        show_top_bounties: $show_top_bounties
        show_total_reports_per_asset: $show_total_reports_per_asset
        show_total_reports_per_severity: $show_total_reports_per_severity
      }
    ) {
      was_successful
      errors(first: 100) {
        edges {
          node {
            id
            field
            message
            type
          }
        }
      }
      team_display_options {
        id
        show_minimum_bounty
        show_reports_resolved
        show_mean_first_response_time
        show_mean_report_triage_time
        show_mean_resolution_time
        show_mean_bounty_time
        show_total_bounties_paid
        show_average_bounty
        show_top_bounties
        show_total_reports_per_asset
        show_total_reports_per_severity
      }
    }
  }
`,P={TOGGLE_SHOW_MINIMUM_BOUNTY:`TOGGLE_SHOW_MINIMUM_BOUNTY`,TOGGLE_SHOW_REPORTS_RESOLVED:`TOGGLE_SHOW_REPORTS_RESOLVED`,TOGGLE_SHOW_MEAN_FIRST_RESPONSE_TIME:`TOGGLE_SHOW_MEAN_FIRST_RESPONSE_TIME`,TOGGLE_SHOW_MEAN_REPORT_TRIAGE_TIME:`TOGGLE_SHOW_MEAN_REPORT_TRIAGE_TIME`,TOGGLE_SHOW_MEAN_RESOLUTION_TIME:`TOGGLE_SHOW_MEAN_RESOLUTION_TIME`,TOGGLE_SHOW_MEAN_BOUNTY_TIME:`TOGGLE_SHOW_MEAN_BOUNTY_TIME`,TOGGLE_SHOW_TOTAL_BOUNTIES_PAID:`TOGGLE_SHOW_TOTAL_BOUNTIES_PAID`,TOGGLE_SHOW_AVERAGE_BOUNTY:`TOGGLE_SHOW_AVERAGE_BOUNTY`,TOGGLE_SHOW_TOP_BOUNTIES:`TOGGLE_SHOW_TOP_BOUNTIES`,TOGGLE_SHOW_TOTAL_REPORTS_PER_ASSET:`TOGGLE_SHOW_TOTAL_REPORTS_PER_ASSET`,TOGGLE_SHOW_TOTAL_REPORTS_PER_SEVERITY:`TOGGLE_SHOW_TOTAL_REPORTS_PER_SEVERITY`},F=(e,t={})=>{switch(t.type){case P.TOGGLE_SHOW_MINIMUM_BOUNTY:return{...e,show_minimum_bounty:!e.show_minimum_bounty};case P.TOGGLE_SHOW_REPORTS_RESOLVED:return{...e,show_reports_resolved:!e.show_reports_resolved};case P.TOGGLE_SHOW_MEAN_FIRST_RESPONSE_TIME:return{...e,show_mean_first_response_time:!e.show_mean_first_response_time};case P.TOGGLE_SHOW_MEAN_REPORT_TRIAGE_TIME:return{...e,show_mean_report_triage_time:!e.show_mean_report_triage_time};case P.TOGGLE_SHOW_MEAN_RESOLUTION_TIME:return{...e,show_mean_resolution_time:!e.show_mean_resolution_time};case P.TOGGLE_SHOW_MEAN_BOUNTY_TIME:return{...e,show_mean_bounty_time:!e.show_mean_bounty_time};case P.TOGGLE_SHOW_TOTAL_BOUNTIES_PAID:return{...e,show_total_bounties_paid:!e.show_total_bounties_paid};case P.TOGGLE_SHOW_AVERAGE_BOUNTY:return{...e,show_average_bounty:!e.show_average_bounty};case P.TOGGLE_SHOW_TOP_BOUNTIES:return{...e,show_top_bounties:!e.show_top_bounties};case P.TOGGLE_SHOW_TOTAL_REPORTS_PER_ASSET:return{...e,show_total_reports_per_asset:!e.show_total_reports_per_asset};case P.TOGGLE_SHOW_TOTAL_REPORTS_PER_SEVERITY:return{...e,show_total_reports_per_severity:!e.show_total_reports_per_severity};default:return e}},I=({team:e})=>{let{team_display_options:n,handle:r}=e,{enabled:i,global:c}=S(j,r),[p,h]=(0,k.useReducer)(F,{show_minimum_bounty:n.show_minimum_bounty,show_reports_resolved:n.show_reports_resolved,show_mean_first_response_time:n.show_mean_first_response_time,show_mean_report_triage_time:n.show_mean_report_triage_time,show_mean_resolution_time:n.show_mean_resolution_time,show_mean_bounty_time:n.show_mean_bounty_time,show_total_bounties_paid:n.show_total_bounties_paid,show_average_bounty:n.show_average_bounty,show_top_bounties:n.show_top_bounties,show_total_reports_per_severity:n.show_total_reports_per_severity,show_total_reports_per_asset:n.show_total_reports_per_asset}),[g,{loading:v}]=b(N,{onCompleted:({updateTeamDisplayOptions:e})=>{e.was_successful?D():_(`error`,M)}});return v?(0,A.jsx)(y,{}):(0,A.jsxs)(A.Fragment,{children:[(0,A.jsxs)(`div`,{className:`mb-md`,children:[(0,A.jsx)(f,{children:`Metrics Display`}),(0,A.jsx)(a,{top:`16`}),(0,A.jsxs)(m,{children:[`These statistics can attract the best hackers to your program. Select the ones you want to display on your program's page.`,!i&&!c&&` Greyed
            out fields are mandatory and cannot be turned off.`]})]}),(0,A.jsxs)(u,{fill:!0,children:[(0,A.jsxs)(a,{horizontal:`24`,top:`24`,children:[(0,A.jsx)(f,{renderAs:`h5`,size:200,children:`Program information`}),(0,A.jsx)(a,{vertical:`sm`}),e.offers_bounties&&(0,A.jsxs)(A.Fragment,{children:[(0,A.jsx)(l,{name:`show_minimum_bounty`,label:` Minimum bounty`,testId:`spec-show-minimum-bounty`,checked:p.show_minimum_bounty,onChange:()=>h({type:P.TOGGLE_SHOW_MINIMUM_BOUNTY}),disabled:!i&&!c}),(0,A.jsx)(a,{vertical:`2xs`})]}),(0,A.jsx)(l,{name:`show_reports_resolved`,label:`Reports resolved`,testId:`spec-show-reports-resolved`,checked:p.show_reports_resolved,onChange:()=>h({type:P.TOGGLE_SHOW_REPORTS_RESOLVED})})]}),(0,A.jsx)(a,{vertical:`24`,children:(0,A.jsx)(d,{variation:`light`})}),(0,A.jsxs)(a,{horizontal:`24`,children:[(0,A.jsx)(f,{renderAs:`h5`,size:200,children:`Response efficiency`}),(0,A.jsx)(a,{vertical:`sm`}),(0,A.jsx)(l,{name:`show_mean_first_response_time`,label:`Average time to first response`,testId:`spec-show-mean-first-response-time`,checked:p.show_mean_first_response_time,onChange:()=>h({type:P.TOGGLE_SHOW_MEAN_FIRST_RESPONSE_TIME})}),(0,A.jsx)(a,{vertical:`2xs`}),(0,A.jsx)(l,{name:`show_mean_report_triage_time`,label:`Average time to triage`,testId:`spec-show-mean-report-triage-time`,checked:p.show_mean_report_triage_time,onChange:()=>h({type:P.TOGGLE_SHOW_MEAN_REPORT_TRIAGE_TIME})}),(0,A.jsx)(a,{vertical:`2xs`}),(0,A.jsx)(l,{name:`show_mean_resolution_time`,label:`Average time to resolution`,testId:`spec-show-mean-resolution-time`,checked:p.show_mean_resolution_time,onChange:()=>h({type:P.TOGGLE_SHOW_MEAN_RESOLUTION_TIME})}),e.offers_bounties&&(0,A.jsxs)(A.Fragment,{children:[(0,A.jsx)(a,{vertical:`2xs`}),(0,A.jsx)(l,{name:`show_mean_bounty_time`,label:`Average time to bounty`,testId:`spec-show-mean-bounty-time`,checked:p.show_mean_bounty_time,onChange:()=>h({type:P.TOGGLE_SHOW_MEAN_BOUNTY_TIME}),disabled:!i&&!c})]})]}),(0,A.jsx)(a,{vertical:`24`,children:(0,A.jsx)(d,{variation:`light`})}),(0,A.jsxs)(a,{horizontal:`24`,children:[(0,A.jsx)(f,{renderAs:`h5`,size:200,children:`Report volume statistics`}),(0,A.jsx)(a,{vertical:`sm`}),(0,A.jsx)(l,{name:`show_total_reports_per_severity`,label:`Show total reports per severity`,testId:`spec-total-reports-per-severity`,checked:p.show_total_reports_per_severity,onChange:()=>h({type:P.TOGGLE_SHOW_TOTAL_REPORTS_PER_SEVERITY})}),(0,A.jsx)(a,{vertical:`2xs`}),(0,A.jsx)(l,{name:`show_total_reports_per_asset`,label:`Show total reports per asset`,testId:`spec-show-total-reports-per-asset`,checked:p.show_total_reports_per_asset,onChange:()=>h({type:P.TOGGLE_SHOW_TOTAL_REPORTS_PER_ASSET})})]}),e.offers_bounties&&(0,A.jsxs)(`div`,{children:[(0,A.jsx)(a,{vertical:`24`,children:(0,A.jsx)(d,{variation:`light`})}),(0,A.jsxs)(a,{horizontal:`24`,children:[(0,A.jsx)(f,{renderAs:`h5`,size:200,children:`Bounty statistics`}),(0,A.jsx)(a,{vertical:`sm`}),(0,A.jsxs)(A.Fragment,{children:[(0,A.jsx)(l,{name:`show_total_bounties_paid`,label:`Total bounties paid`,testId:`spec-show-total-bounties-paid`,checked:p.show_total_bounties_paid,onChange:()=>h({type:P.TOGGLE_SHOW_TOTAL_BOUNTIES_PAID}),disabled:!i&&!c}),(0,A.jsx)(a,{vertical:`2xs`})]}),(0,A.jsx)(l,{name:`show_average_bounty`,label:`Average bounty`,testId:`spec-show-average-bounty`,checked:p.show_average_bounty,onChange:()=>h({type:P.TOGGLE_SHOW_AVERAGE_BOUNTY}),disabled:!i&&!c}),(0,A.jsx)(a,{left:`xs`,children:(0,A.jsx)(o,{text:`Displayed as a range from the 45th to 55th percentile.`})}),(0,A.jsx)(a,{vertical:`2xs`}),(0,A.jsx)(l,{name:`show_top_bounties`,testId:`spec-show-top-bounties`,label:`Top bounty`,checked:p.show_top_bounties,onChange:()=>h({type:P.TOGGLE_SHOW_TOP_BOUNTIES}),disabled:!i&&!c}),(0,A.jsx)(a,{left:`xs`,children:(0,A.jsx)(o,{text:`Displayed as a range from the 90th to 100th percentile.`})})]})]}),(0,A.jsx)(`div`,{className:`m-lg flex justify-end`,children:(0,A.jsx)(s,{disabled:v,onClick:()=>{g({variables:{team_id:e.id,show_minimum_bounty:p.show_minimum_bounty,show_reports_resolved:p.show_reports_resolved,show_mean_first_response_time:p.show_mean_first_response_time,show_mean_report_triage_time:p.show_mean_report_triage_time,show_mean_resolution_time:p.show_mean_resolution_time,show_mean_bounty_time:p.show_mean_bounty_time,show_total_bounties_paid:p.show_total_bounties_paid,show_average_bounty:p.show_average_bounty,show_top_bounties:p.show_top_bounties,show_total_reports_per_severity:p.show_total_reports_per_severity,show_total_reports_per_asset:p.show_total_reports_per_asset}})},type:t.Submit,children:`Update`})})]})]})};I.propTypes={team:O.default.object.isRequired},I.fragments={team:r`
    fragment DisplayOptionsLayout on Team {
      id
      offers_bounties
      team_display_options {
        id
        show_minimum_bounty
        show_reports_resolved
        show_mean_first_response_time
        show_mean_report_triage_time
        show_mean_resolution_time
        show_mean_bounty_time
        show_total_bounties_paid
        show_average_bounty
        show_top_bounties
        show_total_reports_per_asset
        show_total_reports_per_severity
      }
    }
  `},p();var L=r`
  query TeamDisplayOptionsSettings($handle: String!) {
    team(handle: $handle) {
      id
      handle
      i_can_manage_program
      ...DisplayOptionsLayout
    }
  }
  ${I.fragments.team}
`,R=e=>{let{handle:t}=e.match.params,{data:n,loading:r}=E(L,{variables:{handle:t}});if(r)return(0,A.jsx)(y,{});let{team:a}=n;return a.i_can_manage_program?(0,A.jsx)(T,{children:(0,A.jsx)(v,{header:(0,A.jsx)(C,{match:e.match}),content:(0,A.jsxs)(`div`,{children:[(0,A.jsx)(i,{children:(0,A.jsx)(`title`,{children:x(`Metrics Display`)})}),(0,A.jsx)(I,{team:a})]}),footer:(0,A.jsx)(g,{}),hasBackground:!1})}):(0,A.jsx)(w,{})};R.propTypes={match:O.default.shape({params:O.default.shape({handle:O.default.string.isRequired})}).isRequired};export{R as default};
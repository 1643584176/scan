import{o as e}from"./rolldown-runtime-DAXXjFlN.js";import{$y as t,Fw as n,Kx as r,Lr as i,Nb as a,Pb as o,Qy as s,Rw as c,jw as l,ov as u,qx as d,rv as f,zx as p}from"./vendor-_WdvpBLr.js";import{Ah as m,Sd as h,Sm as g,T as _,Th as v,Tm as y,_h as b,ba as x,cc as S,fm as C,gc as w,k as T,lh as E,pc as D,qr as O,rc as k,sc as A,uh as j,vh as M,vm as N,yl as P,ym as F}from"./app-5pKgUmmm.js";var I=e(l()),L=e(p()),R=e(c());d();var z=e(o()),B=n(),V=()=>(0,B.jsxs)(`p`,{children:[`Your targets can't be set to exceed HackerOne's response standards. Reports that miss either response standards or targets will be marked with colored labels in your inbox. For more details on response standards and targets see our`,`  `,(0,B.jsx)(`a`,{className:`daisy-text--blue`,target:`_blank`,rel:`noreferrer`,href:`https://docs.hackerone.com/organizations/response-target-metrics.html`,children:`doc site article`}),`.`]}),H=({name:e,onChange:t,value:n,errors:r})=>(0,B.jsxs)(E,{alignItems:`center`,children:[(0,B.jsx)(`div`,{"data-intercom-target":`Input ${e.replace(/_/g,` `)}`,children:(0,B.jsx)(k,{name:`${e}_input`,className:`spec_${e}_input`,value:z.default.existy(n)?S(n):``,onChange:t,errors:r,type:`number`})}),(0,B.jsx)(`div`,{className:`sla_input__label margin-8--left`,children:`days`})]});H.propTypes={name:L.default.string.isRequired,onChange:L.default.func.isRequired,value:L.default.number,errors:L.default.array};var U=({checked:e,onChange:t})=>(0,B.jsxs)(D,{className:`daisy-text--blue`,children:[(0,B.jsx)(`input`,{className:`margin-5--right spec-severity-based-sla-setting-toggle`,type:`checkbox`,checked:e,onChange:t}),`Advanced Settings`]});U.propTypes={checked:L.default.bool.isRequired,onChange:L.default.func.isRequired};var W=({metric:e})=>{let t=t=>`${t}_severity_${e}`,n=[...constants.report.severity.all].reverse();return(0,B.jsx)(h.Cell,{className:`align-top`,children:n.map(e=>(0,B.jsx)(j,{size:`small`,children:(0,B.jsx)(E,{height:`42px`,alignItems:`center`,children:(0,B.jsx)(P,{rating:e,showScore:!1})})},t(e)))})};W.propTypes={metric:L.default.string.isRequired};var G=class extends R.Component{static propTypes={team:L.default.object.isRequired,updateTeamResponseSlaMutation:L.default.func.isRequired};constructor(e,t){super(e,t),this.state={errors:{},...this.fetchSlaThresholds(e.team)}}fetchSlaThresholds(e){let{sla_setting:t,...n}=e,r=t||{none_severity_resolved_staleness_threshold:e.resolved_staleness_threshold,low_severity_resolved_staleness_threshold:e.resolved_staleness_threshold,medium_severity_resolved_staleness_threshold:e.resolved_staleness_threshold,high_severity_resolved_staleness_threshold:e.resolved_staleness_threshold,critical_severity_resolved_staleness_threshold:e.resolved_staleness_threshold,use_advanced_settings:!1};return{...n,...r}}hasErrorsForThreshold=e=>z.default.not.empty(this.getErrorsForThreshold(e));getErrorsForThreshold=e=>{let{errors:t}=this.state,n=t[e];return n&&(0,I.default)(n)?n.slice(0,1):[]};durationChangeHandler=e=>t=>{let n=t.target.value;z.default.empty(n)?this.setState({[e]:null}):this.setState({[e]:A(n)})};handleSubmit=e=>{e.preventDefault(),this.setState({errors:{}});let t=({data:{updateTeamResponseSla:{was_successful:e,errors:t,team:n}}})=>{e?(F(),this.setState({...this.fetchSlaThresholds(n)})):(this.setState({errors:w(t)}),g(`error`,`Changes could not be saved. Response targets cannot exceed HackerOne response standards. See details below.`))};this.props.updateTeamResponseSlaMutation({variables:{team_handle:this.props.team.handle,...this.state}}).then(e=>t(e),()=>N())};renderSeverityBasedSlaForm(e){let{use_advanced_settings:t}=this.state;if(!t)return null;let n=t=>`${t}_severity_${e}`;return[...constants.report.severity.all].reverse().map(e=>(0,B.jsx)(j,{size:`small`,children:(0,B.jsx)(E,{height:`42px`,children:(0,B.jsx)(H,{name:n(e),onChange:this.durationChangeHandler(n(e)),value:this.state[n(e)],errors:this.getErrorsForThreshold(n(e))})})},n(e)))}render(){let{use_advanced_settings:e}=this.state,{team:n}=this.props;return(0,B.jsxs)(`div`,{children:[(0,B.jsxs)(h,{fixed:!0,children:[(0,B.jsx)(h.Head,{children:(0,B.jsxs)(h.Row,{children:[(0,B.jsx)(h.CellHeader,{width:`33%`}),(0,B.jsx)(h.CellHeader,{children:`Standard`}),(0,B.jsx)(h.CellHeader,{}),(0,B.jsx)(h.CellHeader,{width:`25%`,children:`Target`})]})}),(0,B.jsxs)(h.Body,{children:[(0,B.jsxs)(h.Row,{children:[(0,B.jsx)(h.Cell,{children:(0,B.jsx)(D,{className:`no-margin`,hasErrors:this.hasErrorsForThreshold(`new_staleness_threshold`),children:`Time to first response`})}),(0,B.jsxs)(h.Cell,{colSpan:2,children:[S(n.new_staleness_threshold_limit),` days`]}),(0,B.jsx)(h.Cell,{children:(0,B.jsx)(H,{name:`new_staleness_threshold`,onChange:this.durationChangeHandler(`new_staleness_threshold`),value:this.state.new_staleness_threshold,errors:this.getErrorsForThreshold(`new_staleness_threshold`)})})]}),(0,B.jsxs)(h.Row,{children:[(0,B.jsx)(h.Cell,{children:(0,B.jsx)(D,{className:`no-margin`,hasErrors:this.hasErrorsForThreshold(`triaged_staleness_threshold`),children:`Time to triage`})}),(0,B.jsxs)(h.Cell,{colSpan:2,children:[S(n.triaged_staleness_threshold_limit),` days`]}),(0,B.jsx)(h.Cell,{children:(0,B.jsx)(H,{name:`triaged_staleness_threshold`,onChange:this.durationChangeHandler(`triaged_staleness_threshold`),value:this.state.triaged_staleness_threshold,errors:this.getErrorsForThreshold(`triaged_staleness_threshold`)})})]}),n.offers_bounties?(0,B.jsxs)(h.Row,{children:[(0,B.jsx)(h.Cell,{children:(0,B.jsx)(D,{className:`no-margin`,children:`Time to bounty`})}),(0,B.jsx)(h.Cell,{colSpan:2,children:`N/A`}),(0,B.jsx)(h.Cell,{children:(0,B.jsx)(H,{name:`bounty_awarded_staleness_threshold`,onChange:this.durationChangeHandler(`bounty_awarded_staleness_threshold`),value:this.state.bounty_awarded_staleness_threshold,errors:this.getErrorsForThreshold(`bounty_awarded_staleness_threshold`)})})]}):null,(0,B.jsxs)(h.Row,{children:[(0,B.jsxs)(h.Cell,{className:`align-top`,children:[(0,B.jsx)(E,{height:`42px`,alignItems:`center`,children:(0,B.jsx)(D,{className:`no-margin`,hasErrors:this.hasErrorsForThreshold(`resolved_staleness_threshold`),children:`Time to resolution`})}),(0,B.jsx)(U,{checked:this.state.use_advanced_settings,onChange:()=>this.setState({use_advanced_settings:!e})})]}),(0,B.jsx)(h.Cell,{className:`align-top`,children:(0,B.jsx)(E,{height:`42px`,alignItems:`center`,children:`N/A`})}),e?(0,B.jsx)(W,{metric:`resolved_staleness_threshold`}):(0,B.jsx)(h.Cell,{}),(0,B.jsx)(h.Cell,{className:`align-top`,children:e?this.renderSeverityBasedSlaForm(`resolved_staleness_threshold`):(0,B.jsx)(H,{name:`resolved_staleness_threshold`,onChange:this.durationChangeHandler(`resolved_staleness_threshold`),value:this.state.resolved_staleness_threshold,errors:this.getErrorsForThreshold(`resolved_staleness_threshold`)})})]})]})]}),(0,B.jsxs)(j,{top:!0,children:[(0,B.jsx)(C,{className:`pull-left`,children:`Note: All days above are in business days.`}),(0,B.jsx)(`div`,{className:`save-custom-staleness-thresholds-spec inline-block pull-right`,"data-intercom-target":`Save response targets`,children:(0,B.jsx)(s,{type:t.Submit,onClick:this.handleSubmit,children:`Save`})}),(0,B.jsx)(`div`,{className:`clearfix`})]})]})}},K=r`
  mutation updateTeamResponseSlaMutation(
    $team_handle: String!
    $new_staleness_threshold: Int
    $triaged_staleness_threshold: Int
    $resolved_staleness_threshold: Int
    $bounty_awarded_staleness_threshold: Int
    $use_advanced_settings: Boolean
    $none_severity_resolved_staleness_threshold: Int
    $low_severity_resolved_staleness_threshold: Int
    $medium_severity_resolved_staleness_threshold: Int
    $high_severity_resolved_staleness_threshold: Int
    $critical_severity_resolved_staleness_threshold: Int
  ) {
    updateTeamResponseSla(
      input: {
        team_handle: $team_handle
        new_staleness_threshold: $new_staleness_threshold
        triaged_staleness_threshold: $triaged_staleness_threshold
        resolved_staleness_threshold: $resolved_staleness_threshold
        bounty_awarded_staleness_threshold: $bounty_awarded_staleness_threshold
        use_advanced_settings: $use_advanced_settings
        none_severity_resolved_staleness_threshold: $none_severity_resolved_staleness_threshold
        low_severity_resolved_staleness_threshold: $low_severity_resolved_staleness_threshold
        medium_severity_resolved_staleness_threshold: $medium_severity_resolved_staleness_threshold
        high_severity_resolved_staleness_threshold: $high_severity_resolved_staleness_threshold
        critical_severity_resolved_staleness_threshold: $critical_severity_resolved_staleness_threshold
      }
    ) {
      team {
        id
        new_staleness_threshold
        triaged_staleness_threshold
        resolved_staleness_threshold
        bounty_awarded_staleness_threshold
        new_staleness_threshold_limit
        triaged_staleness_threshold_limit
        sla_setting {
          id
          none_severity_resolved_staleness_threshold
          low_severity_resolved_staleness_threshold
          medium_severity_resolved_staleness_threshold
          high_severity_resolved_staleness_threshold
          critical_severity_resolved_staleness_threshold
          use_advanced_settings
        }
      }
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
`,q=r`
  query TeamResponseSlaSettingsQuery($handle: String!) {
    team(handle: $handle) {
      id
      handle
      offers_bounties

      new_staleness_threshold
      triaged_staleness_threshold
      resolved_staleness_threshold
      bounty_awarded_staleness_threshold

      new_staleness_threshold_limit
      triaged_staleness_threshold_limit

      sla_setting {
        id
        none_severity_resolved_staleness_threshold
        low_severity_resolved_staleness_threshold
        medium_severity_resolved_staleness_threshold
        high_severity_resolved_staleness_threshold
        critical_severity_resolved_staleness_threshold

        use_advanced_settings
      }
    }
  }
`,J=({handle:e})=>{let{data:t,loading:n,error:r}=M(q,{variables:{handle:e}}),[i]=b(K);return n?(0,B.jsx)(v,{size:`small`}):r?(0,B.jsx)(`div`,{children:`Some error occurred`}):(0,B.jsxs)(B.Fragment,{children:[(0,B.jsxs)(`div`,{className:`mb-md`,children:[(0,B.jsx)(u,{children:`Response Targets`}),(0,B.jsx)(a,{top:`16`}),(0,B.jsx)(f,{children:`Set your program's custom response targets by configuring the number of business days that can elapse on a report.`})]}),(0,B.jsx)(y,{children:(0,B.jsxs)(y.Content,{children:[(0,B.jsx)(V,{}),(0,B.jsx)(a,{top:`24`}),(0,B.jsx)(G,{team:t.team,updateTeamResponseSlaMutation:i})]})})]})};J.propTypes={handle:L.default.string.isRequired};var Y=({match:{params:{handle:e}}})=>(0,B.jsx)(O,{children:(0,B.jsx)(_,{header:(0,B.jsx)(T,{match:{params:{handle:e}}}),hasBackground:!1,content:(0,B.jsxs)(`div`,{children:[(0,B.jsx)(i,{children:(0,B.jsx)(`title`,{children:x(`Response Targets`)})}),(0,B.jsx)(J,{handle:e})]}),footer:(0,B.jsx)(m,{})})});Y.propTypes={match:L.default.object.isRequired};export{Y as default};
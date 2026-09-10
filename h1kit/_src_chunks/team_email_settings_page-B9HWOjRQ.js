import{o as e}from"./rolldown-runtime-DAXXjFlN.js";import{Fw as t,Kx as n,Lr as r,Nb as i,ov as a,qx as o,rv as s,zx as c}from"./vendor-_WdvpBLr.js";import{Ah as l,In as u,T as d,Th as f,_h as p,ba as m,k as h,qr as g,vh as _,vm as v,ym as y}from"./app-5pKgUmmm.js";var b=e(c());o();var x=t(),S=n`
  query TeamEmailSetting($handle: String!) {
    team(handle: $handle) {
      id
      email_setting
    }
  }
`,C=n`
  mutation UpdateTeamEmailSetting($team_id: ID!, $email_setting: Int!) {
    updateTeamEmailSetting(
      input: { team_id: $team_id, email_setting: $email_setting }
    ) {
      was_successful
      team {
        id
        email_setting
      }
    }
  }
`,w=e=>{let t=e.match.params.handle,{data:n,loading:o}=_(S,{variables:{handle:t}}),[c]=p(C,{onCompleted:e=>e.updateTeamEmailSetting.was_successful?y():v()});if(o)return(0,x.jsx)(f,{});let{id:b,email_setting:w}=n.team,T=e=>c({variables:{team_id:b,email_setting:e},optimisticResponse:{updateTeamEmailSetting:{__typename:`UpdateTeamEmailSettingPayload`,was_successful:!0,team:{__typename:`Team`,id:b,email_setting:e}}}});return(0,x.jsx)(g,{children:(0,x.jsx)(d,{header:(0,x.jsx)(h,{...e}),content:(0,x.jsxs)(`div`,{children:[(0,x.jsx)(r,{children:(0,x.jsx)(`title`,{children:m(`Email Settings`)})}),(0,x.jsxs)(`div`,{className:`mb-md`,children:[(0,x.jsx)(a,{children:`Email Settings`}),(0,x.jsx)(i,{top:`16`}),(0,x.jsx)(s,{children:`Report activity triggers email notifications. Configure what content they include.`})]}),(0,x.jsxs)(`div`,{children:[(0,x.jsxs)(`div`,{className:`input-wrapper`,children:[(0,x.jsx)(u,{id:`spec-no-content`,name:`email-setting`,value:`no-content`,label:`No content`,className:`spec-no-content`,helperText:`Include only a notification that new activity has occurred.`,checked:w===3,onChange:()=>T(3)}),(0,x.jsx)(u,{id:`spec-minimal-content`,name:`email-setting`,value:`minimal-content`,label:`Minimal content (Default)`,helperText:`Include report title and activity, but exclude report details.`,checked:w===1,onChange:()=>T(1)}),(0,x.jsx)(u,{id:`spec-full-content`,name:`email-setting`,value:`full-content`,label:`Full content`,className:`spec-full-content`,helperText:`Include all activity and report details.`,checked:w===2,onChange:()=>T(2)})]}),(0,x.jsxs)(`div`,{className:`inline-banner inline-banner--notice`,children:[`Tip: Configure if you want to receive emails by default in your`,` `,(0,x.jsx)(`a`,{href:`/settings/notification_preferences`,children:`notification preferences`}),`.`]})]})]}),footer:(0,x.jsx)(l,{})})})};w.propTypes={match:b.default.shape({params:b.default.shape({handle:b.default.string.isRequired}).isRequired}).isRequired};export{w as default};
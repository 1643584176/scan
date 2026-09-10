import{o as e}from"./rolldown-runtime-DAXXjFlN.js";import{By as t,Fw as n,Kx as r,Lr as i,Ly as a,Nb as o,Qy as s,Rw as c,Ry as l,Y_ as u,df as d,ff as f,ov as p,qx as m,zx as h}from"./vendor-_WdvpBLr.js";import{Ah as g,Gn as _,In as v,T as y,Th as b,Tm as x,_h as S,ba as C,dh as w,fm as T,k as E,pr as D,qr as O,uh as k,vh as A,vm as j,ym as M}from"./app-5pKgUmmm.js";var N=e(h());m();var P=n(),F=r`
  mutation UpdateTeamTargetSignal($team_id: ID!, $target_signal: Float!) {
    updateTeamTargetSignal(
      input: { team_id: $team_id, target_signal: $target_signal }
    ) {
      was_successful
      team {
        id
        signal_requirements_setting {
          id
          target_signal
        }
      }
    }
  }
`,I=e=>{switch(e){case`strict`:return 1;case`standard`:return 0;case`lenient`:return-1;default:return-10}},L=({team:e})=>{let[t]=S(F,{onCompleted:({updateTeamTargetSignal:e})=>{e.was_successful?M():j()}}),n=n=>{t({variables:{team_id:e.id,target_signal:I(n.target.value)}})},r=e.signal_requirements_setting?.target_signal;return(0,P.jsx)(`div`,{children:e.signal_requirements_setting&&(0,P.jsx)(k,{children:(0,P.jsxs)(x,{children:[(0,P.jsx)(x.Heading,{children:(0,P.jsx)(`strong`,{children:`Signal Requirements`})}),(0,P.jsxs)(x.Content,{children:[(0,P.jsxs)(`p`,{children:[`Select a Signal Requirement for your team. Any hacker with a past-year Signal lower than your threshold will have a restricted number of reports they can submit to your program.`,` `,(0,P.jsx)(w,{to:`https://www.hackerone.com/blog/signal-requirements`,target:`_blank`,children:`Learn more...`})]}),(0,P.jsxs)(`div`,{className:`input-wrapper`,children:[(0,P.jsx)(v,{id:`spec-strict`,name:`signal-setting`,value:`strict`,label:`Strict (>= 1.0 Signal)`,className:`spec-strict`,helperText:`Hackers with a proven record are unrestricted, while hackers who do not
              meet this requirement will have a limited number of allowed submissions to your
              program. Recommended for new programs.`,checked:r===1,onChange:n}),(0,P.jsx)(v,{id:`spec-standard`,name:`signal-setting`,value:`standard`,label:`Standard (>= 0.0 Signal)`,className:`spec-standard`,helperText:`Recommended for most programs.`,checked:r===0,onChange:n}),(0,P.jsx)(v,{id:`spec-lenient`,name:`signal-setting`,value:`lenient`,label:`Lenient (>= -1.0 Signal)`,className:`spec-lenient`,helperText:`Recommended for experienced programs that want to maximize hacker breadth.`,checked:r===-1,onChange:n}),(0,P.jsx)(v,{id:`spec-disabled`,name:`signal-setting`,value:`disabled`,label:`Turn off Signal Requirements`,className:`spec-disabled`,helperText:`This will disable the rate limiter entirely. Recommended for veteran programs only.`,checked:r===-10,onChange:n})]})]})]})})})};L.propTypes={team:N.default.shape({id:N.default.string.isRequired,type:N.default.string.isRequired,save:N.default.func,set:N.default.func,previousAttributes:N.default.object,changedAttributes:N.default.object,signal_requirements_setting:N.default.shape({target_signal:N.default.number})}).isRequired},L.fragments={team:r`
    fragment SignalSettingsLayoutTeam on Team {
      id
      type
      signal_requirements_setting {
        id
        target_signal
      }
    }
  `};var R=e(c());m();var z=Object.values(window.constants.report.severityCalculationMethods),{MANUAL:B,CVSS_3_0_HACKERONE:V,CVSS_3_1:H,CVSS_4_0:U}=window.constants.report.severityCalculationMethods,W=r`
  query TeamSubmissionRequirementsSeverityMethods($handle: String!) {
    team(handle: $handle) {
      id
      handle
      submissionRequirements: submission_requirements {
        id
        severityCalculationMethods: severity_calculation_methods
        severityRequiredAt: severity_required_at
      }
    }
  }
`,G=r`
  mutation UpdateSubmissionRequirementsSeverity(
    $team_id: ID!
    $severity_calculation_methods: [SeverityCalculationMethodEnum!]
    $severity_required_at: String
  ) {
    updateSubmissionRequirements(
      input: {
        team_id: $team_id
        severity_calculation_methods: $severity_calculation_methods
        severity_required_at: $severity_required_at
      }
    ) {
      was_successful
      errors {
        edges {
          node {
            id
            message
            field
            type
          }
        }
      }
      team {
        id
        submission_requirements {
          id
          severityCalculationMethods: severity_calculation_methods
          severityRequiredAt: severity_required_at
        }
      }
    }
  }
`,K=({team_handle:e,addingSeverityRequirementDisabled:n})=>{let[r,i]=(0,R.useState)([]),[c,p]=(0,R.useState)(!1),[m,h]=(0,R.useState)(null),{data:g,loading:_}=A(W,{variables:{handle:e}});(0,R.useEffect)(()=>{let e=g?.team.submissionRequirements?.severityCalculationMethods;e?.length>0&&i([...e]),p(g?.team.submissionRequirements?.severityRequiredAt||!1)},[g]);let[v]=S(G,{onCompleted:({updateSubmissionRequirements:e})=>{e.was_successful?M():j()}}),y=(0,R.useCallback)(e=>{z.includes(e)&&(r.includes(e)?i([...r].filter(t=>t!==e)):i([...r,e]))},[r]);if(_)return(0,P.jsx)(b,{overlay:!0});let{team:C}=g,E=()=>{if(!r.length){h(`You have to select at least 1 severity calculation method.`);return}v({variables:{team_id:g?.team.id,severity_calculation_methods:r,severity_required_at:c||null}})},D=()=>{p(c?!1:C.submissionRequirements?.severityRequiredAt||new Date().toISOString())};return(0,P.jsxs)(x,{children:[(0,P.jsxs)(x.Heading,{children:[(0,P.jsx)(`strong`,{children:`Severity Calculation Methods`}),(0,P.jsx)(T,{children:`Select what severity calculation methods are available to hackers when submitting reports.`})]}),(0,P.jsx)(x.Content,{children:(0,P.jsxs)(`div`,{className:`flex flex-col`,children:[m&&(0,P.jsxs)(P.Fragment,{children:[(0,P.jsx)(a,{contentPrimary:m,variation:t.Error,dismissable:!0,dismissAccessibilityLabel:`close`}),(0,P.jsx)(o,{vertical:`24`})]}),(0,P.jsxs)(`div`,{className:`flex flex-col`,children:[(0,P.jsxs)(`div`,{className:`flex`,children:[(0,P.jsx)(u,{checked:r.includes(U),accessibilityLabel:`CVSS 4.0`,onChange:()=>{y(U)},testId:`severity-calculation-methods-cvss-4-0-hackerone`}),`CVSS 4.0`]}),(0,P.jsxs)(T,{children:[`Provides the option to use CVSS 4.0.`,` `,(0,P.jsx)(`a`,{href:`https://www.first.org/cvss/v4.0/specification-document`,children:`Check out`}),` `,`the official documentation for more information.`]})]}),(0,P.jsx)(o,{vertical:`24`}),(0,P.jsxs)(`div`,{className:`flex flex-col`,children:[(0,P.jsxs)(`div`,{className:`flex`,children:[(0,P.jsx)(u,{checked:r.includes(H),accessibilityLabel:`CVSS 3.1`,onChange:()=>{y(H)},testId:`severity-calculation-methods-cvss-3-1-hackerone`}),`CVSS 3.1`]}),(0,P.jsxs)(T,{children:[`Provides the option to use CVSS 3.1.`,` `,(0,P.jsx)(`a`,{href:`https://www.first.org/cvss/v3.1/specification-document`,children:`Check out`}),` `,`the official documentation for more information.`]})]}),(0,P.jsx)(o,{vertical:`24`}),(0,P.jsxs)(`div`,{className:`flex flex-col`,children:[(0,P.jsxs)(`div`,{className:`flex`,children:[(0,P.jsx)(u,{checked:r.includes(V),accessibilityLabel:`CVSS 3.0 HackerOne`,onChange:()=>{y(V)},testId:`severity-calculation-methods-cvss-3-0-hackerone`}),`CVSS 3.0 HackerOne`]}),(0,P.jsxs)(T,{children:[`Provides the option to use HackerOne`,`’`,`s implementation of CVSS 3.0. This custom version of CVSS includes an additional environmental metric value: none. This can be used to indicate that loss of [Confidentiality | Integrity | Availability] will not have adverse affect on the organization or individuals associated with the organization (e.g., employees, customers). This custom environmental metric value `,(0,P.jsx)(`em`,{children:`None`}),` will be treated as`,` `,(0,P.jsx)(`em`,{children:`Low`}),` in CVSS version 3.1 and higher.`]})]}),(0,P.jsx)(o,{vertical:`24`}),(0,P.jsxs)(`div`,{className:`flex flex-col`,children:[(0,P.jsxs)(`div`,{className:`flex flex-row`,children:[(0,P.jsx)(u,{checked:r.includes(B),accessibilityLabel:`Manual selection`,onChange:()=>{y(B)},testId:`severity-calculation-methods-manual`}),`Manual selection`]}),(0,P.jsx)(T,{children:`Provides the option to manually select a severity level without using a severity calculator.`})]}),(0,P.jsx)(o,{vertical:`24`}),(0,P.jsx)(d,{variation:f.Light}),(0,P.jsx)(o,{vertical:`24`}),(0,P.jsxs)(`div`,{className:`flex flex-col`,children:[(0,P.jsxs)(`div`,{className:`flex`,children:[(0,P.jsx)(u,{checked:c,accessibilityLabel:`Make setting severity mandatory`,onChange:()=>{D()},testId:`severity-required-at`,disabled:!c&&n}),`Make selecting a severity mandatory when submitting a report`]}),!c&&n&&(0,P.jsx)(l,{contentPrimary:`You can't turn this on right now`,contentSecondary:(0,P.jsxs)(P.Fragment,{children:[`In order to make severity a mandatory field when submitting reports, you will need to disable`,` `,(0,P.jsx)(w,{to:`/${e}/security_email_forwarding`,children:`email forwarding`})]}),variation:t.Information})]}),(0,P.jsx)(o,{vertical:`24`}),(0,P.jsx)(`div`,{className:`flex flex-row-reverse`,children:(0,P.jsx)(s,{onClick:E,loading:_,testId:`severity-calculation-methods-update-button`,children:`Update calculation methods`})})]})})]})};K.propTypes={team_handle:N.default.string.isRequired,addingSeverityRequirementDisabled:N.default.bool};var q=({assetRequired:e,weaknessRequired:n,requiringNewFieldsDisabled:r,teamHandle:i,onChange:a})=>(0,P.jsxs)(x,{children:[(0,P.jsxs)(x.Heading,{children:[(0,P.jsx)(`strong`,{children:`Required Fields`}),(0,P.jsx)(T,{children:`Select which fields hackers must complete when submitting a report.`})]}),(0,P.jsxs)(x.Content,{className:`flex flex-col`,children:[r&&(0,P.jsx)(l,{contentPrimary:`You can't turn this on right now`,contentSecondary:(0,P.jsxs)(P.Fragment,{children:[`In order to add required fields when submitting reports, you will need to disable`,` `,(0,P.jsx)(w,{to:`/${i}/security_email_forwarding`,children:`email forwarding`})]}),variation:t.Information}),(0,P.jsx)(u,{label:`Asset`,testId:`asset-checkbox`,checked:e,onChange:()=>{a(!e,n)},disabled:!e&&r}),(0,P.jsx)(u,{label:`Weakness`,testId:`weakness-checkbox`,checked:n,onChange:()=>{a(e,!n)},disabled:!n&&r})]})]});m();var J=r`
  query TeamSubmissionRequirements($handle: String!) {
    team(handle: $handle) {
      id
      type
      handle
      state
      submissionRequirements: submission_requirements {
        id
        severityCalculationMethods: severity_calculation_methods
        severityRequiredAt: severity_required_at
        assetRequired: asset_required
        weaknessRequired: weakness_required
      }
      allows_bounty_splitting
      allows_collaboration_with_non_whitelisted_hackers
      is_team_member
      can_toggle_bounty_splitting
      email_forwarding_setting {
        security_email_forwarding_enabled
      }
      ...SignalSettingsLayoutTeam
    }
  }
  ${L.fragments.team}
`,Y=r`
  mutation UpdateSubmissionRequirementsPage(
    $team_id: ID!
    $severity_required_at: String
    $asset_required: Boolean
    $weakness_required: Boolean
  ) {
    updateSubmissionRequirements(
      input: {
        team_id: $team_id
        severity_required_at: $severity_required_at
        asset_required: $asset_required
        weakness_required: $weakness_required
      }
    ) {
      was_successful
      team {
        id
        submission_requirements {
          id
          severityCalculationMethods: severity_calculation_methods
          severityRequiredAt: severity_required_at
          assetRequired: asset_required
          weaknessRequired: weakness_required
        }
      }
    }
  }
`,X=r`
  mutation UpdateTeamBountySplittingSetting($team_id: ID!) {
    updateTeamBountySplittingSetting(input: { team_id: $team_id }) {
      was_successful
      team {
        id
        allows_bounty_splitting
      }
    }
  }
`,Z=r`
  mutation ToggleCollaborationWithNonWhitelistedHackers($team_id: ID!) {
    toggleCollaborationWithNonWhitelistedHackers(input: { team_id: $team_id }) {
      was_successful
      team {
        id
        allows_collaboration_with_non_whitelisted_hackers
      }
    }
  }
`,Q=(e,t)=>n=>{n.preventDefault(),t({variables:{team_id:e.id}})},$=({match:e})=>{let{data:t,loading:n}=A(J,{variables:{handle:e.params.handle}}),[r]=S(Y,{onCompleted:({updateSubmissionRequirements:e})=>{e.was_successful?M():j()}}),[a]=S(X,{onCompleted:({updateTeamBountySplittingSetting:e})=>{e.was_successful?M():j()}}),[o]=S(Z,{onCompleted:({toggleCollaborationWithNonWhitelistedHackers:e})=>{e.was_successful?M():j()}});if(n)return(0,P.jsx)(b,{overlay:!0});let{team:s}=t,c=s.type===`Engagements::Assessment`,l=s.type===`Engagements::VulnerabilityDisclosureProgram`,u=s.email_forwarding_setting?.security_email_forwarding_enabled;return(0,P.jsx)(O,{children:s&&s.is_team_member?(0,P.jsx)(y,{pageLayout:!0,header:(0,P.jsx)(E,{match:{params:{handle:s.handle}},pageLayout:!0}),hasBackground:!1,content:(0,P.jsxs)(`div`,{children:[(0,P.jsx)(i,{children:(0,P.jsx)(`title`,{children:C(`Submission Requirements`)})}),(0,P.jsx)(`div`,{className:`spec-scopes-title mb-md`,children:(0,P.jsx)(p,{children:`Submission Requirements`})}),(0,P.jsx)(L,{team:s}),(0,P.jsx)(k,{children:(0,P.jsx)(x,{children:(0,P.jsxs)(x.Content,{children:[!c&&!l&&(0,P.jsxs)(`div`,{className:`row input-wrapper`,children:[(0,P.jsx)(_,{onLabel:`YES`,offLabel:`NO`,disabled:!s.can_toggle_bounty_splitting,checked:s.allows_bounty_splitting,onChange:Q(s,a),className:`pull-right spec-enable-bounty-splitting-switch`}),`Enable collaboration`,(0,P.jsx)(T,{children:`Collaboration allows hackers to work together on a report and share the bounty.`}),!s.can_toggle_bounty_splitting&&(0,P.jsxs)(T,{children:[`To enable collaboration, you must first enable prepayment under`,` `,(0,P.jsx)(`strong`,{children:`Program Settings > General > Billing > Prepayment`}),`.`]})]}),s.allows_bounty_splitting&&s.state===`soft_launched`&&(0,P.jsxs)(`div`,{className:`row input-wrapper`,children:[(0,P.jsx)(_,{onLabel:`YES`,offLabel:`NO`,disabled:!s.can_toggle_bounty_splitting,checked:s.allows_collaboration_with_non_whitelisted_hackers,onChange:Q(s,o),className:`pull-right spec-enable-collab-outside-switch`}),`Enable collaboration with hackers outside of your program`,(0,P.jsx)(T,{children:`Turning on this setting will allow hackers to invite other hackers that have not been invited to your program to collaborate on a report.`})]})]})})}),(0,P.jsx)(k,{children:(0,P.jsx)(K,{team_handle:e.params.handle,addingSeverityRequirementDisabled:u})}),(0,P.jsx)(k,{children:(0,P.jsx)(q,{assetRequired:s.submissionRequirements?.assetRequired??!1,weaknessRequired:s.submissionRequirements?.weaknessRequired??!1,requiringNewFieldsDisabled:u,teamHandle:s.handle,onChange:(e,t)=>r({variables:{team_id:s.id,asset_required:e,weakness_required:t,severity_required_at:s.submissionRequirements?.severityRequiredAt},optimisticResponse:{updateSubmissionRequirements:{was_successful:!0,team:{id:s.id,submission_requirements:{id:s.submissionRequirements?.id,severityCalculationMethods:s.submissionRequirements?.severityCalculationMethods,severityRequiredAt:s.submissionRequirements?.severityRequiredAt,assetRequired:e,weaknessRequired:t,__typename:`SubmissionRequirements`},__typename:`Team`}}}})})})]}),footer:(0,P.jsx)(g,{})}):(0,P.jsx)(D,{})})};$.propTypes={match:N.default.object.isRequired};export{$ as default};
import{o as e}from"./rolldown-runtime-DAXXjFlN.js";import{Fw as t,Iw as n,Kx as r,Lr as i,Nb as a,Qy as o,Rw as s,ov as c,qx as l,rv as u,tb as d,zx as f}from"./vendor-_WdvpBLr.js";import{Sd as p,T as m,Th as h,Tm as g,_h as _,ba as v,bm as y,dh as b,ep as x,fc as S,fm as C,gc as w,k as T,lh as E,pc as D,qr as O,rc as k,tp as A,uc as j,uh as M,v as N,vh as P,vm as F,vp as ee}from"./app-5pKgUmmm.js";var I=e(n()),L=e(s());l();var R=e(f()),z=t(),B=r`
  fragment SecurityEmailForwardingFragment on Team {
    id
    handle
    i_can_view_email_forwarding_overview
    email_forwarding_setting {
      id
      email_forwarding_address
      security_email_forwardings {
        total_count
        edges {
          node {
            id
            _id
            security_email
            status
          }
        }
      }
    }
    submission_requirements {
      id
      severity_required_at
      asset_required
      weakness_required
    }
  }
`,V=r`
  mutation CreateOrUpdateSecurityEmailForwardingMutation(
    $team_id: ID!
    $security_email: String!
    $security_email_forwarding_id: ID
  ) {
    createOrUpdateSecurityEmailForwarding(
      input: {
        team_id: $team_id
        security_email: $security_email
        security_email_forwarding_id: $security_email_forwarding_id
      }
    ) {
      security_email_forwarding {
        id
        _id
        security_email
      }
      team {
        id
        ...SecurityEmailForwardingFragment
      }
      was_successful
      errors(first: 100) {
        edges {
          node {
            id
            field
            type
            message
          }
        }
      }
    }
  }
  ${B}
`,H=r`
  mutation TestEmailForwarding($team_id: ID!, $forwarding_id: Int!) {
    testEmailForwarding(
      input: { team_id: $team_id, forwarding_id: $forwarding_id }
    ) {
      was_successful
      team {
        id
        ...SecurityEmailForwardingFragment
      }
      errors(first: 100) {
        edges {
          node {
            id
            field
            type
            message
          }
        }
      }
    }
  }
  ${B}
`,U={EMAIL_ADDRESS:`email_address`,INSTRUCTIONS:`instructions`,TEST_RUNNING:`test_running`},W=({setCurrentStep:e,securityEmailForwarding:t,setSecurityEmailForwarding:n,team:r})=>{let[i,a]=(0,L.useState)(t?t.security_email:``),[o,s]=(0,L.useState)([]),[c,{loading:l}]=_(V,{variables:{team_id:r.id,security_email:i,security_email_forwarding_id:t?parseInt(t._id,10):null},onCompleted:({createOrUpdateSecurityEmailForwarding:t})=>{t.was_successful?(n(t.security_email_forwarding),e(U.INSTRUCTIONS)):s(w(t.errors).security_email)},onError:()=>{F()}}),u=()=>{l||c()};return(0,z.jsxs)(x,{title:`Email forwarding address`,showModal:!0,cancelLinkText:`Cancel`,buttonText:`Continue`,intercomTarget:`Continue Adding Email Forwarding`,buttonDisabled:i===``||l,handleButtonClick:()=>u(),shouldCloseOnOverlayClick:!0,shouldCloseOnEsc:!0,handleCloseModal:()=>e(null),size:`medium`,children:[l?(0,z.jsx)(h,{centered:!0,size:`large`}):null,(0,z.jsx)(`p`,{children:`Enter the email address where you want to receive vulnerability reports.`}),(0,z.jsx)(`form`,{onSubmit:e=>{e.preventDefault(),u()},children:(0,z.jsx)(M,{children:(0,z.jsxs)(S,{hasErrors:o.length>0,children:[(0,z.jsx)(D,{children:`Email`}),(0,z.jsx)(C,{children:`For example: security@example.com or hackerone@example.com`}),(0,z.jsx)(k,{id:`spec-security-email`,value:i,onChange:e=>a(e.target.value)}),(0,z.jsx)(C,{errors:o,children:`Hint: it could be "Shine"`})]})})})]})};W.propTypes={setCurrentStep:R.default.func.isRequired,setSecurityEmailForwarding:R.default.func.isRequired,securityEmailForwarding:R.default.object,team:R.default.object.isRequired};var G=({setCurrentStep:e,emailForwardingAddress:t,securityEmailForwarding:n,team:r})=>{let[i,a]=(0,L.useState)(!1),[o,{loading:s}]=_(H,{variables:{team_id:r.id,forwarding_id:parseInt(n._id,10)},onCompleted:({testEmailForwarding:t})=>{t.was_successful?e(U.TEST_RUNNING):y(t.errors)},onError:()=>{F()}}),c=(0,L.useCallback)(()=>{s||o()},[o,s]);return(0,z.jsxs)(x,{title:`Instructions`,showModal:!0,cancelLinkText:`Close`,buttonText:`Run Test`,intercomTarget:`Run Test Email Forwarding`,buttonDisabled:!i||s,handleButtonClick:c,shouldCloseOnOverlayClick:!1,shouldCloseOnEsc:!1,handleCloseModal:()=>e(null),size:`medium`,children:[s?(0,z.jsx)(h,{centered:!0,size:`large`}):null,(0,z.jsx)(M,{children:(0,z.jsx)(A,{variation:`green`,size:`medium`,children:`Forwarding address successfully added!`})}),(0,z.jsxs)(`p`,{children:[`Configure `,(0,z.jsxs)(`strong`,{children:[`"`,n.security_email,`"`]}),` to forward to the following address:`]}),(0,z.jsx)(M,{children:(0,z.jsx)(`pre`,{className:`monospace`,children:(0,z.jsx)(`code`,{style:{background:`inherit`,border:`none`},children:t})})}),(0,z.jsx)(`p`,{children:(0,z.jsx)(`a`,{className:`daisy-link`,target:`_blank`,href:`https://docs.hackerone.com/organizations/email-forwarding.html`,rel:`noreferrer`,children:`Click here for detailed setup instructions.`})}),(0,z.jsxs)(`p`,{children:[`Some providers (e.g., Google) require you to verify the forwarding address via a confirmation email, you can find this email in`,` `,(0,z.jsx)(`a`,{className:`daisy-link`,target:`_blank`,rel:`noreferrer`,href:`/${r.handle}/email_forwarding`,children:`Incoming Emails.`})]}),(0,z.jsxs)(`p`,{children:[`Once the setup is complete, click the "Run Test" button below. If successful, email forwarding will begin immediately.`,` `]}),(0,z.jsx)(`p`,{children:(0,z.jsx)(j,{checked:i,id:`spec-confirm-checkbox`,name:`Test Performed`,helperText:``,onChange:()=>a(!i),children:`I have performed the email configuration above.`})})]})};G.propTypes={setCurrentStep:R.default.func.isRequired,emailForwardingAddress:R.default.string.isRequired,securityEmailForwarding:R.default.shape({_id:R.default.string.isRequired,id:R.default.string.isRequired,security_email:R.default.string.isRequired}).isRequired,team:R.default.object.isRequired};var K=({setCurrentStep:e,securityEmailForwarding:t})=>(0,z.jsx)(x,{title:`Test in progress`,showModal:!0,buttonText:`Close`,handleButtonClick:()=>e(null),shouldCloseOnOverlayClick:!0,shouldCloseOnEsc:!0,handleCloseModal:()=>e(null),size:`medium`,children:(0,z.jsxs)(M,{children:[`Email forwarding test for`,` `,(0,z.jsxs)(`strong`,{children:[`"`,t.security_email,`"`]}),` is in progress.`,(0,z.jsx)(`br`,{}),`Please come back in 10 minutes to see the results.`]})});K.propTypes={setCurrentStep:R.default.func.isRequired,securityEmailForwarding:R.default.shape({_id:R.default.string.isRequired,id:R.default.string.isRequired,security_email:R.default.string.isRequired}).isRequired},l();var q=window.constants.notification.support_link,J={verified:{label:`Verified`,class:`daisy-text--green`,tooltip:`Emails are currently forwarded to HackerOne.`},pending:{label:`Pending`,class:`daisy-text--light-grey`,tooltip:`Verification in progress, we will email you upon completion.`},unverified:{label:`Failed`,class:`daisy-text--red`,tooltip:`Forwarding failed.
       Please check your forwarding setup or contact ${q}.`},disabled:{label:`Disabled`,class:`daisy-text--light-grey`,tooltip:`Contact ${q} to enable forwarding.`}},Y=r`
  query EmailForwardingSettings($handle: String!) {
    team(handle: $handle) {
      id
      ...SecurityEmailForwardingFragment
    }
  }
  ${B}
`,X=({status:e})=>{let t=J[e];if(!t)return null;let n=(0,I.default)(`daisy-text`,t.class);return(0,z.jsx)(ee,{className:`inline-help`,eventType:`hover`,tooltipText:t.tooltip,light:!1,children:(0,z.jsx)(`span`,{className:n,children:t.label})})};X.propTypes={status:R.default.string.isRequired};var Z=({setSecurityEmailForwarding:e,setCurrentStep:t,disabled:n})=>(0,z.jsx)(`div`,{"data-intercom-target":`Add email address`,children:(0,z.jsx)(o,{onClick:()=>{e(null),t(U.EMAIL_ADDRESS)},testId:`add-email-forwarding-button`,disabled:n,children:`Add email address`})});Z.propTypes={setSecurityEmailForwarding:R.default.func.isRequired,setCurrentStep:R.default.func.isRequired,disabled:R.default.bool.isRequired};var Q=({handle:e})=>{let{data:t,loading:n}=P(Y,{variables:{handle:e}}),[r,i]=(0,L.useState)(null),[s,l]=(0,L.useState)(null);if(n)return(0,z.jsx)(h,{overlay:!0});let f=t.team.email_forwarding_setting&&t.team.email_forwarding_setting.security_email_forwardings,m=t.team.email_forwarding_setting&&t.team.email_forwarding_setting.email_forwarding_address,_=t.team.submission_requirements,v=_?.severity_required_at||_?.asset_required||_?.vulnerability_type_required;return(0,z.jsxs)(z.Fragment,{children:[s===U.EMAIL_ADDRESS?(0,z.jsx)(W,{setCurrentStep:l,securityEmailForwarding:r,setSecurityEmailForwarding:i,team:t.team}):null,s===U.INSTRUCTIONS&&r!==null?(0,z.jsx)(G,{setCurrentStep:l,emailForwardingAddress:m,securityEmailForwarding:r,team:t.team}):null,s===U.TEST_RUNNING?(0,z.jsx)(K,{setCurrentStep:l,securityEmailForwarding:r}):null,(0,z.jsxs)(`div`,{className:`spec-scopes-title mb-md`,children:[(0,z.jsx)(c,{children:`Email Forwarding`}),(0,z.jsx)(a,{top:`16`}),(0,z.jsxs)(u,{children:[`Have emails (i.e. "security@example.com") forwarded to your HackerOne inbox. Anyone who discovers this email address will be able to submit reports to your program.`,` `,(0,z.jsx)(`a`,{target:`_blank`,rel:`noreferrer`,href:`https://docs.hackerone.com/organizations/email-forwarding.html`,tabIndex:`-1`,className:`daisy-link`,children:`Learn more.`})]})]}),(0,z.jsxs)(M,{top:!0,children:[v&&(0,z.jsx)(M,{children:(0,z.jsxs)(A,{variation:`yellow`,children:[`Email forwarding cannot be enabled because your`,` `,(0,z.jsx)(b,{to:`/${e}/submission_requirements`,children:`submission requirements`}),` `,`include fields that are required for all reports, and emailed reports can't specify fields. Disable these field requirements if you wish to enable email forwarding.`]})}),(0,z.jsx)(M,{children:(0,z.jsxs)(A,{variation:`blue`,children:[`Are you having trouble with your email forwarding setup? Visit our`,` `,(0,z.jsx)(`a`,{target:`_blank`,rel:`noreferrer`,href:`https://docs.hackerone.com/organizations/email-forwarding.html#setup-issues`,tabIndex:`-1`,className:`daisy-link`,children:`documentation`}),` `,`to find help with common setup issues.`]})}),(0,z.jsx)(g,{children:(0,z.jsx)(g.Content,{children:f?.total_count>0?(0,z.jsxs)(z.Fragment,{children:[(0,z.jsxs)(M,{className:`daisy-text`,children:[(0,z.jsx)(`strong`,{children:`Forwarding to: `}),` `,m]}),(0,z.jsxs)(p,{className:`spec-email-forwarding-table`,children:[(0,z.jsx)(p.Head,{children:(0,z.jsxs)(p.Row,{children:[(0,z.jsx)(p.CellHeader,{children:`Email address`}),(0,z.jsx)(p.CellHeader,{children:`Forwarding Status`}),(0,z.jsx)(p.CellHeader,{})]})}),(0,z.jsx)(p.Body,{children:f&&f.edges.map(({node:e})=>(0,z.jsxs)(p.Row,{className:`spec-forwarding-entry`,children:[(0,z.jsx)(p.Cell,{children:e.security_email}),(0,z.jsx)(p.Cell,{children:(0,z.jsx)(X,{status:e.status})}),(0,z.jsx)(p.Cell,{children:v?(0,z.jsx)(z.Fragment,{}):(0,z.jsx)(`a`,{className:`daisy-link`,onClick:()=>{i(e),l(U.EMAIL_ADDRESS)},children:e.status===`unverified`?`Start Over`:`Edit`})})]},e.id))})]})]}):(0,z.jsxs)(N,{children:[(0,z.jsx)(`h3`,{className:`daisy-h3 no-margin`,children:`Email forwarding has not been set up yet.`}),(0,z.jsx)(M,{top:!0,children:(0,z.jsx)(Z,{setSecurityEmailForwarding:i,setCurrentStep:l,disabled:v})})]})})})]}),f&&f.total_count>0?(0,z.jsx)(M,{top:!0,children:(0,z.jsxs)(E,{justifyContent:`flex-end`,children:[t.team.i_can_view_email_forwarding_overview&&(0,z.jsx)(`div`,{className:`margin-10--right`,children:(0,z.jsx)(o,{variation:d.Secondary,renderAs:`link`,to:`/${e}/email_forwarding`,children:`View incoming emails`})}),(0,z.jsx)(Z,{setSecurityEmailForwarding:i,setCurrentStep:l,disabled:v})]})}):null]})};Q.propTypes={handle:R.default.string.isRequired};var $=e=>{let{handle:t}=e.match.params;return(0,z.jsx)(O,{children:(0,z.jsx)(m,{header:(0,z.jsx)(T,{match:e.match}),content:(0,z.jsxs)(M,{size:`large`,children:[(0,z.jsx)(i,{children:(0,z.jsx)(`title`,{children:v(`Email Forwarding`)})}),(0,z.jsx)(Q,{handle:t})]}),hasBackground:!1})})};$.propTypes={match:R.default.shape({params:R.default.shape({handle:R.default.string.isRequired}).isRequired}).isRequired};export{$ as default};
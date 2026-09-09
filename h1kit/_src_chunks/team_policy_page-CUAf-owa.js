import{o as e}from"./rolldown-runtime-DAXXjFlN.js";import{$y as t,Ax as n,Fw as r,Kx as i,Lr as a,Nb as o,Pb as s,Qy as c,Rw as l,Ux as u,Vw as d,Vx as f,ov as p,qx as m,rv as h,zx as g}from"./vendor-_WdvpBLr.js";import{Af as _,Ah as v,Cp as y,Dh as ee,Jc as b,Sm as x,T as S,Th as C,Tm as w,Tn as te,Wt as T,Zc as ne,_h as E,ap as D,ba as O,cl as k,er as A,fl as j,fm as M,gc as N,k as P,ll as F,op as I,qr as L,uc as re,uh as R,vh as z,vm as B,vn as ie,wn as ae,ym as V}from"./app-5pKgUmmm.js";import{t as oe}from"./custom_message_dialog-CrE8EryV.js";var H=e(l()),U=e(g()),W=y(`
  query TeamPolicySettings($teamHandle: String!) {
    team(handle: $teamHandle) {
      id
      _id
      policy
      name
      external_program {
        id
      }
      state
      type
      declarative_policy {
        has_open_scope
        pays_within_one_month
        protected_by_gold_standard_safe_harbor
        protected_by_ai_safe_harbor
        disclosure_declaration
        introduction
        platform_standards_exclusions {
          id
          justification
          platform_standard
        }
        exemplary_standards_exclusions
        contact_email
        scope_exclusions {
          id
          _id
          category
          details
          created_at
        }
      }
    }
  }
`),G=y(`
  mutation UpdateTeamPolicy(
    $teamId: ID!
    $policy: String
    $notifySubscribersOfPolicyChange: Boolean
    $customMessageForPolicyChange: String
    $hasOpenScope: Boolean
    $paysWithinOneMonth: Boolean
    $protectedByGoldStandardSafeHarbor: Boolean
    $protectedByAiSafeHarbor: Boolean
    $disclosureDeclaration: String
    $introduction: String
    $platformStandardsExclusions: [PlatformStandardsExclusionInput!]
    $exemplaryStandardsExclusions: [String!]
    $contactEmail: String
    $scopeExclusions: [ScopeExclusionInput!]
  ) {
    updateTeamPolicy(
      input: {
        team_id: $teamId
        policy: $policy
        notify_subscribers_of_policy_change: $notifySubscribersOfPolicyChange
        custom_message_for_policy_change: $customMessageForPolicyChange
        has_open_scope: $hasOpenScope
        pays_within_one_month: $paysWithinOneMonth
        protected_by_gold_standard_safe_harbor: $protectedByGoldStandardSafeHarbor
        protected_by_ai_safe_harbor: $protectedByAiSafeHarbor
        disclosure_declaration: $disclosureDeclaration
        introduction: $introduction
        platform_standards_exclusions: $platformStandardsExclusions
        exemplary_standards_exclusions: $exemplaryStandardsExclusions
        contact_email: $contactEmail
        scope_exclusions: $scopeExclusions
      }
    ) {
      was_successful
    }
  }
`),K=async({teamHandle:e,teamId:t,formData:n,policy:r,notifySubscribersOfPolicyChange:i,customMessageForPolicyChange:a,declarativePolicy:o,mutation:s,setSubmitting:c,showAlert:l})=>{c(!0);try{await fetch(`/${e}`,{method:`PUT`,body:n,headers:{...T()}});let{data:c}=await s({variables:{teamId:t,policy:r,notifySubscribersOfPolicyChange:i,customMessageForPolicyChange:a,introduction:o?.introduction,hasOpenScope:o?.has_open_scope,paysWithinOneMonth:o?.pays_within_one_month,protectedByGoldStandardSafeHarbor:o?.protected_by_gold_standard_safe_harbor,protectedByAiSafeHarbor:o?.protected_by_ai_safe_harbor,disclosureDeclaration:o?.disclosure_declaration,contactEmail:o?.contact_email,platformStandardsExclusions:o?.platform_standards_exclusions?.map(e=>({platform_standard:e.platform_standard,justification:e.justification})),exemplaryStandardsExclusions:o?.exemplary_standards_exclusions,scopeExclusions:o?.scope_exclusions,...Y,product_feature:J.Update},refetchQueries:[`TeamPolicySettings`]});if(!(c?.updateTeamPolicy?.was_successful??!1))throw Error(`Policy update failed.`);l(`notice`,`Changes saved successfully.`)}catch{l(`error`,`Could not save changes. Please retry and if this problem persists, contact us via ${window.constants.notification.support_link}.`)}c(!1)},q=r(),J=function(e){return e.Show=`show`,e.Update=`update`,e}({}),Y={product_area:_.DeclarativePolicies,product_feature:`show`},se=b,X=({teamHandle:e,attachments:r})=>{let i=n(),[a,s]=(0,H.useState)(!1),[l,d]=(0,H.useState)(void 0),[m,g]=(0,H.useState)(!1),[_,v]=(0,H.useState)(!1),[y,b]=(0,H.useState)(!1),[S,C]=(0,H.useState)(``),[w,T]=(0,H.useState)(!1),[E,D]=(0,H.useState)(!1),[O,k]=(0,H.useState)(!1),[j,M]=(0,H.useState)(),{data:N,loading:P,refetch:I}=u(W,{variables:{teamHandle:e,...Y}}),[L]=f(G);if((0,H.useEffect)(()=>{let e=N?.team?.policy;e&&d(e),M(N?.team?.declarative_policy??{})},[N]),(0,H.useEffect)(()=>{document.referrer.replace(/^[^:]+:\/\/[^/]+/,``).replace(/#.*/,``)===`/${e}/setup`&&(T(!0),D(!0))},[e]),(0,H.useEffect)(()=>{v(!1)},[JSON.stringify(r.toJSON())]),(0,H.useEffect)(()=>{let e=i.block(()=>{if(a)return`You have unsaved changes. Are you sure you want to leave?`}),t=e=>{a&&(e.preventDefault(),e.returnValue=!0)};return window.addEventListener(`beforeunload`,t),()=>{e(),window.removeEventListener(`beforeunload`,t)}},[a,i]),P)return(0,q.jsx)(ee,{});if(!N?.team)return(0,q.jsx)(q.Fragment,{});let R=N?.team?.id,z=N?.team?._id,B=N?.team?.name,V=N?.team?.external_program?.id,U=N?.team?.state,J=N?.team?.type===`Engagements::VulnerabilityDisclosureProgram`,X=!!V&&![`inactive`,`public_mode`].some(e=>U===e);return(0,q.jsxs)(`div`,{className:`settings-section spec-legacy-policy-layout`,children:[w&&(0,q.jsx)(te,{}),E&&(0,q.jsx)(ae,{}),(0,q.jsxs)(`form`,{method:`post`,encType:`multipart/form-data`,onSubmit:t=>{t.preventDefault();let n=new FormData(t.currentTarget),r=new FormData;n.has(`team[attachment_ids][]`)?n.getAll(`team[attachment_ids][]`).forEach(e=>{r.append(`team[attachment_ids][]`,e)}):r.append(`team[attachment_ids][]`,``);let i=j?.scope_exclusions?.filter(e=>!e.transient||!e.delete).map(e=>({id:e.transient?null:e.id,category:e.category,details:e.details,delete:e.delete}));K({teamHandle:e,teamId:R,formData:r,policy:l,notifySubscribersOfPolicyChange:n.get(`team[notify_subscribers_of_policy_change]`)===`on`,customMessageForPolicyChange:S,declarativePolicy:{...j,scope_exclusions:i??[]},mutation:L,setSubmitting:k,showAlert:x}).then(async()=>(s(!1),await I()))},children:[(0,q.jsxs)(`div`,{className:`spec-policy-title mb-md`,children:[(0,q.jsx)(p,{children:X?`Private Program Overview`:`Overview`}),(0,q.jsx)(o,{top:`16`}),(0,q.jsxs)(h,{children:[`Organizations typically publish vulnerability disclosure guidance for how they want to receive information related to potential vulnerabilities in their products or online services (see ISO 29147, or`,` `,(0,q.jsx)(A,{url:window.constants.notification.support_link,children:`contact us`}),` `,`for help with a draft).`]})]}),(0,q.jsxs)(`div`,{children:[(0,q.jsx)(ie,{declarativePolicy:j,setDeclarativePolicy:e=>{s(!0),M(e)},vdp:J,teamHandle:e}),(0,q.jsx)(o,{top:`24`}),X&&(0,q.jsx)(`p`,{children:`This policy is only visible to hackers that you invite to your program.`}),(0,q.jsx)(`div`,{className:`input-wrapper`,children:(0,q.jsx)(se,{textareaId:`spec-text-area`,name:`team[policy]`,minimumHeight:100,attachments:r.map(e=>({_id:e.id,file_name:e.get(`name`),file_size:e.get(`size`),content_type:e.get(`type`),expiring_url:e.get(`expiring_url`)??``})),value:l,onChange:e=>{e!==void 0&&l!==void 0&&e!==l&&s(!0),e!==void 0&&d(e)},markdownOptions:{enableUnderline:!0}})}),(0,q.jsx)(`div`,{className:`input-wrapper`,children:(0,q.jsx)(ne,{attachments:r,displayAttachmentIds:!0,contextType:`Team`,contextId:z?Number(z):void 0,onAdd:e=>{let t=new F({id:`${e.id}`,name:e.name,size:e.size,type:e.type,expiring_url:e.dataURL});r.add(t)},onRemove:e=>{r.remove(e),v(!0)},onUploadInProgressChange:e=>{g(e)}})}),r.map(e=>(0,q.jsx)(`input`,{type:`hidden`,name:`team[attachment_ids][]`,value:e.get(`id`)},e.get(`id`))),(0,q.jsxs)(`div`,{children:[(0,q.jsx)(`div`,{className:`pull-left`,children:(0,q.jsx)(o,{top:`8`,children:(0,q.jsxs)(re,{defaultChecked:!0,id:`notify_subscribers_of_policy_change`,name:`team[notify_subscribers_of_policy_change]`,children:[`Notify subscribers of changes. \xA0`,(0,q.jsx)(oe,{teamName:B,showModal:y,customMessage:S,onShowModal:()=>{b(!0)},onCancel:()=>{b(!1),C(``)},onChange:e=>{C(e)},onSave:()=>{b(!1)}})]})})}),(0,q.jsx)(`div`,{className:`pull-right`,children:(0,q.jsx)(c,{testId:`button-success`,type:t.Submit,disabled:!l||m||_||O,children:m&&`Uploading attachment...`||O&&`Updating...`||`Update`})}),(0,q.jsx)(`div`,{className:`clearfix`})]})]})]})]})};X.defaultProps={attachments:new k([],{})},m();var ce=e(s()),le=i`
  mutation UpdateStructuredPolicy(
    $team_handle: String!
    $brand_promise: String
    $scope: String
    $process: String
    $safe_harbor: String
    $preferences: String
  ) {
    updateStructuredPolicy(
      input: {
        team_handle: $team_handle
        brand_promise: $brand_promise
        scope: $scope
        process: $process
        safe_harbor: $safe_harbor
        preferences: $preferences
      }
    ) {
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
      team {
        id
        handle
        state
        external_program {
          id
        }
        policy_setting {
          id
          structured_policy {
            id
            brand_promise
            scope
            process
            safe_harbor
            preferences
          }
        }
      }
    }
  }
`,Z=({team:e})=>{let[t,n]=(0,H.useState)({}),[r,i]=(0,H.useState)(e.policy_setting?.structured_policy.brand_promise),[a,o]=(0,H.useState)(e.policy_setting?.structured_policy.scope),[s,c]=(0,H.useState)(e.policy_setting?.structured_policy.process),[l,u]=(0,H.useState)(e.policy_setting?.structured_policy.safe_harbor),[d,f]=(0,H.useState)(e.policy_setting?.structured_policy.preferences),[p,{loading:m}]=E(le,{onCompleted:({updateStructuredPolicy:e})=>{if(e.was_successful)V();else{B();let t=N(e.errors);n(t)}}}),h=()=>ce.default.not.empty(t),g=t=>{t.preventDefault(),n({}),p({variables:{team_handle:e.handle,brand_promise:r,scope:a,process:s,safe_harbor:l,preferences:d}})},_=()=>e.external_program&&(e.state!==`inactive`||e.state!==`public_mode`);return(0,q.jsxs)(`div`,{className:`settings-section spec-structured-policy-layout`,children:[(0,q.jsx)(`h2`,{className:`daisy-h2`,children:_()?`Private Policy`:`Policy`}),_()&&(0,q.jsx)(`p`,{children:`This policy is only visible to hackers that you invite to your program.`}),(0,q.jsxs)(R,{size:`medium`,children:[(0,q.jsx)(R,{size:`extra-large`,children:(0,q.jsxs)(w,{children:[(0,q.jsxs)(w.Heading,{children:[(0,q.jsx)(`strong`,{children:`Brand Promise`}),(0,q.jsx)(M,{children:`Demonstrate a clear commitment to customers and stakeholders potentially impacted by security vulnerabilities.`})]}),(0,q.jsx)(w.Content,{children:(0,q.jsx)(j,{id:`brand_promise`,name:`brand_promise`,value:r,onChange:e=>{i(e.target.value)},hasErrors:h()})})]})}),(0,q.jsx)(R,{size:`extra-large`,children:(0,q.jsxs)(w,{children:[(0,q.jsxs)(w.Heading,{children:[(0,q.jsx)(`strong`,{children:`Scope`}),(0,q.jsx)(M,{children:`Include websites or assets which should be covered by this policy.`})]}),(0,q.jsx)(w.Content,{children:(0,q.jsx)(j,{id:`scope`,name:`scope`,value:a,onChange:e=>o(e.target.value),hasErrors:h()})})]})}),(0,q.jsx)(R,{size:`extra-large`,children:(0,q.jsxs)(w,{children:[(0,q.jsxs)(w.Heading,{children:[(0,q.jsx)(`strong`,{children:`Process`}),(0,q.jsx)(M,{children:`Define a mechanism for submission and reporting.`})]}),(0,q.jsx)(w.Content,{children:(0,q.jsx)(j,{id:`process`,name:`process`,value:s,onChange:e=>c(e.target.value),hasErrors:h()})})]})}),(0,q.jsx)(R,{size:`extra-large`,children:(0,q.jsxs)(w,{children:[(0,q.jsxs)(w.Heading,{children:[(0,q.jsx)(`strong`,{children:`Safe harbor`}),(0,q.jsx)(M,{children:`We will not take legal action if... (you follow these very simple, non-legalese terms).`})]}),(0,q.jsx)(w.Content,{children:(0,q.jsx)(j,{id:`safe_harbor`,name:`safe_harbor`,value:l,onChange:e=>u(e.target.value),hasErrors:h()})})]})}),(0,q.jsx)(R,{size:`extra-large`,children:(0,q.jsxs)(w,{children:[(0,q.jsxs)(w.Heading,{children:[(0,q.jsx)(`strong`,{children:`Preferences`}),(0,q.jsx)(M,{children:`Set expectations based on priorities and submission volume (e.g. responsiveness, severity).`})]}),(0,q.jsx)(w.Content,{children:(0,q.jsx)(j,{id:`preferences`,name:`preferences`,value:d,onChange:e=>f(e.target.value),hasErrors:h()})})]})}),(0,q.jsxs)(`div`,{children:[(0,q.jsx)(I,{onClick:g,className:`pull-right`,disabled:m,children:m?`Updating policy...`:`Update policy`}),(0,q.jsx)(`div`,{className:`clearfix`})]})]})]})};Z.propTypes={team:U.default.object.required},Z.fragments={team:i`
    fragment StructuredPolicyLayout on Team {
      id
      handle
      state
      external_program {
        id
      }
      policy_setting {
        id
        structured_policy {
          id
          brand_promise
          preferences
          process
          safe_harbor
          scope
        }
      }
    }
  `};var ue=e(d()),de=class extends H.Component{static displayName=`ProgramSettingsUpsell`;static propTypes={teamHandle:U.default.string.isRequired};state={loading:!1};handleSubmit=e=>{e.preventDefault(),this.promoteFromInactive()};promoteFromInactive=()=>{this.setState({loading:!0}),ue.default.ajax({url:`/${this.props.teamHandle}/learn_more/promote`,type:`POST`,dataType:`json`,contentType:`application/json`,success(e){document.location.href=`/bugs?subject=${e.handle}`},error(){this.setState({loading:!1}),x(`error`,`Something went wrong. Please retry and if this problem persists, contact us via ${window.constants.notification.support_link}`)}})};renderBullet=e=>(0,q.jsxs)(`li`,{children:[(0,q.jsx)(`i`,{className:`text-green icon-checkmark-alt`}),` ${e}`]});renderLoadingIndicator=()=>{if(this.state.loading)return(0,q.jsx)(C,{overlay:!0})};render(){return(0,q.jsxs)(`div`,{className:`settings-section`,children:[this.renderLoadingIndicator(),(0,q.jsx)(`h2`,{children:`Try running your program on HackerOne`}),(0,q.jsxs)(`ul`,{children:[this.renderBullet(`Define an invitation-only policy for security hackers.`),this.renderBullet(`Receive vulnerability reports confidentially.`),this.renderBullet(`Reward and communicate with hackers.`)]}),(0,q.jsx)(`br`,{}),(0,q.jsx)(`p`,{children:`Try the free, private demo now with sample reports.`}),(0,q.jsx)(`div`,{className:`content-footer`,children:(0,q.jsx)(`div`,{className:`content-footer-wrapper`,children:(0,q.jsxs)(`div`,{className:`content-footer-left`,children:[(0,q.jsx)(`button`,{className:`button button--success`,onClick:this.handleSubmit,children:`Start Demo`}),` `,(0,q.jsx)(`a`,{href:window.constants.notification.support_link,children:`Contact us`})]})})})]})}},fe=e=>e?.vdp_launch_configuration&&e?.state===`sandboxed`,pe=e=>e?.bbp_launch_configuration&&e?.state===`sandboxed`,me=e=>fe(e)||pe(e);m();var he=i`
  query TeamPolicyPage($handle: String!) {
    team(handle: $handle) {
      id
      handle
      policy_setting {
        id
        has_structured_policy
      }
      vdp_launch_configuration {
        id
      }
      bbp_launch_configuration {
        id
      }
      state
      attachments {
        id
        _id
        file_name
        file_size
        content_type
        expiring_url
      }
      ...StructuredPolicyLayout
    }
  }
  ${Z.fragments.team}
`,Q=({handle:e,setHasBackground:t})=>{let{data:n,loading:r}=z(he,{variables:{handle:e}});if(r)return(0,q.jsx)(C,{});if(!n||!n.team)return null;let{team:i}=n;if(me(i))return D(`/programs/settings`);t(!i.policy_setting?.has_structured_policy||i.state===`inactive`);let o=i.attachments.map(e=>new F({id:e._id,name:e.file_name,size:e.file_size,type:e.content_type,expiring_url:e.expiring_url,moderated:e.moderated}));return(0,q.jsxs)(`div`,{children:[(0,q.jsx)(a,{children:(0,q.jsx)(`title`,{children:O(`Policy`)})}),i.state===`inactive`?(0,q.jsx)(de,{teamHandle:i.handle}):(0,q.jsx)(q.Fragment,{children:i.policy_setting?.has_structured_policy?(0,q.jsx)(Z,{team:i}):(0,q.jsx)(X,{teamHandle:i.handle,attachments:new k(o,{})})})]})};Q.propTypes={handle:U.default.string.isRequired,setHasBackground:U.default.func.isRequired};var $=e=>{let{handle:t}=e.match.params,[n,r]=(0,H.useState)(!0);return(0,q.jsx)(L,{children:(0,q.jsx)(S,{header:(0,q.jsx)(P,{match:e.match}),content:(0,q.jsx)(Q,{handle:t,setHasBackground:r}),footer:(0,q.jsx)(v,{}),hasBackground:n})})};$.propTypes={match:U.default.shape({params:U.default.shape({handle:U.default.string.isRequired}).isRequired}).isRequired};export{$ as default};
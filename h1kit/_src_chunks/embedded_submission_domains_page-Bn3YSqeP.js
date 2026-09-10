import{o as e}from"./rolldown-runtime-DAXXjFlN.js";import{$d as t,Fw as n,Kx as r,Lw as i,Pb as a,Qy as o,Rw as s,Vf as c,Vw as l,a as u,gw as d,na as f,ov as p,qx as m,sd as h,tb as g,ux as _,zx as v}from"./vendor-_WdvpBLr.js";import{Ah as y,Dh as b,Nn as x,Rn as S,T as C,Tm as w,_h as ee,df as te,dh as T,fm as E,gc as D,ic as O,ih as k,k as A,lh as j,op as ne,pc as M,qr as N,rc as P,tp as F,uh as I,vh as L,vl as re,vm as ie,ym as R}from"./app-5pKgUmmm.js";import{t as ae}from"./minus-BVDvkpHi.js";import{t as oe}from"./encode_query_string-BBfVzn6J.js";import{n as se}from"./better_report_form-BzuBw8Pn.js";var ce=e(d()),le=e(_()),z=e(c()),ue=e(f()),B=e(v()),V=e(s()),H=e(i()),U=e(l()),W=e(a()),G=n(),K=class extends V.Component{static displayName=`ColorPicker`;static propTypes={id:B.default.string.isRequired,name:B.default.string.isRequired,initialValue:B.default.string,onChange:B.default.func.isRequired};state={value:this.props.initialValue||``,color:`#fff`,showPopover:!1};componentDidMount(){(0,U.default)(document).on(`click`,this.handleDocumentClick)}componentDidUpdate(){(0,U.default)(`.profile-header`).css(`background-color`,this.state.value)}componentWillUnmount(){(0,U.default)(document).off(`click`,this.handleDocumentClick)}handleDocumentClick=e=>{if((0,U.default)(e.target).closest(H.findDOMNode(this)).length)return;let t;H.findDOMNode(this.refs.colorpicker)&&(t=H.findDOMNode(this.refs.colorpicker).parentNode),!(0,U.default)(e.target).closest(t).length&&this.setState({showPopover:!1})};toggletooltipVisibilityFactory=e=>()=>this.setState({showPopover:e});setValue=e=>{let t;t=/^#/.test(e)?e:`#${e}`,/^#[0-9a-fA-F]{0,6}$/.test(t)&&(this.setState({value:t}),this.props.onChange(t))};handleChange=e=>this.setValue(e.target.value);onDrag=e=>this.setValue(e.hex);renderPopover=()=>{if(this.state.showPopover)return(0,G.jsx)(re,{size:`medium`,children:(0,G.jsx)(u,{ref:`colorpicker`,color:this.state.value,onChange:this.onDrag,onChangeComplete:this.onDrag})})};render(){return(0,G.jsx)(P,{id:this.props.id,name:this.props.name,onChange:this.handleChange,onFocus:this.toggletooltipVisibilityFactory(!0),placeholder:`e.g. #123456`,value:this.state.value,hasErrors:W.default.existy(this.state.value)&&!W.default.empty(this.state.value)&&!/^#[0-9a-fA-F]{3}([0-9a-fA-F]{3})?$/.test(this.state.value),prefix:(0,G.jsx)(`div`,{className:`input__color-indicator--daisy`,onClick:this.toggletooltipVisibilityFactory(!this.state.showPopover),style:{backgroundColor:this.state.value},children:this.renderPopover()})})}};m();var{EMBEDDED_FORM_VERSION_2:de}=window.constants.featureToggles,fe=(0,ce.default)(window,`constants.websafeFonts`,[]),q=r`
  fragment EmbeddedSubmissionsFragment on Team {
    id
    handle
    state
    entry_vdp
    organization {
      id
      handle
      gate_i18n_embedded_submission_forms_opened
    }
    embedded_submission_forms(first: 1) {
      edges {
        node {
          id
          uuid
          promotion_enabled
          typeface
          accent_color
          accent_text_color
          link_color
          button_color
          button_text_color
          version
          locales
          supports_dark_mode
        }
      }
    }
    embedded_submission_domains(first: 100) {
      edges {
        node {
          id
          _id
          domain
        }
      }
    }
  }
`,pe=r`
  mutation UpdateEmbeddedSubmissionDomains(
    $team_id: ID!
    $embedded_submission_domains: [String]!
  ) {
    updateEmbeddedSubmissionDomains(
      input: {
        team_id: $team_id
        embedded_submission_domains: $embedded_submission_domains
      }
    ) {
      was_successful
      errors(types: ARGUMENT, first: 100) {
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
        ...EmbeddedSubmissionsFragment
      }
    }
  }
  ${q}
`,me=r`
  mutation UpdateEmbeddedSubmissionForm(
    $team_id: ID!
    $promotion_enabled: Boolean!
    $typeface: String
    $accent_color: String
    $accent_text_color: String
    $link_color: String
    $button_color: String
    $button_text_color: String
    $version: Int
    $locales: [String!]
    $supports_dark_mode: Boolean
  ) {
    updateEmbeddedSubmissionForm(
      input: {
        team_id: $team_id
        promotion_enabled: $promotion_enabled
        typeface: $typeface
        accent_color: $accent_color
        accent_text_color: $accent_text_color
        link_color: $link_color
        button_color: $button_color
        button_text_color: $button_text_color
        version: $version
        locales: $locales
        supports_dark_mode: $supports_dark_mode
      }
    ) {
      was_successful
      errors(types: ARGUMENT, first: 100) {
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
        ...EmbeddedSubmissionsFragment
      }
    }
  }
  ${q}
`,he=r`
  query EmbeddedSubmissionDomains($handle: String!) {
    team(handle: $handle) {
      id
      ...EmbeddedSubmissionsFragment
    }
  }
  ${q}
`,J={ADD_DOMAIN:`ADD_DOMAIN`,UPDATE_DOMAIN:`UPDATE_DOMAIN`,DESTROY_DOMAIN:`DESTROY_DOMAIN`,ADD_ERRORS:`ADD_ERRORS`,UPDATE_FORM:`UPDATE_FORM`},ge=e=>{let t=(0,z.default)(e.embedded_submission_domains.edges,e=>({url:e.node.domain}));return W.default.empty(t)?[{url:``}]:t},Y=e=>W.default.not.empty(e?.embedded_submission_forms?.edges)?e.embedded_submission_forms.edges[0].node:{promotion_enabled:!0},_e=e=>({form:{domains:{value:ge(e)},errors:{}}}),ve=(e,t={})=>{switch(t.type){case J.ADD_DOMAIN:{let t={...e};return t.form.domains.value=t.form.domains.value.concat({url:``}),t}case J.UPDATE_DOMAIN:{let n={...e},r=e.form.domains.value[t.index],i=(0,le.default)(r,{url:t.value});return n.form.domains.value[t.index]=i,n}case J.DESTROY_DOMAIN:{let n={...e},r=(0,ue.default)(n.form.domains.value);return r.splice(t.index,1),n.form.domains.value=W.default.empty(r)?[{url:``}]:r,n}case J.ADD_ERRORS:{let n={...e};return n.form.errors=t.value,n}default:return e}},ye=(e,t={})=>ve(e,t),X=({store:e,dispatch:t})=>(0,G.jsxs)(`div`,{children:[(0,z.default)(e.form.domains.value,(n,r)=>{let i=W.default.empty(n.url)?null:e.form.errors[`domain.${n.url}`];return(0,G.jsxs)(I,{children:[(0,G.jsxs)(j,{flexShrink:1,flexBasis:`100%`,children:[(0,G.jsx)(P,{onChange:e=>{t({value:e.target.value,index:r,domainObject:n,type:J.UPDATE_DOMAIN})},onFocus:e=>{e.target.value||t({value:`https://`,index:r,domainObject:n,type:J.UPDATE_DOMAIN})},placeholder:`https://www.example.com`,name:`domain-${r+1}`,value:n.url,hasErrors:W.default.existy(i)}),(0,G.jsx)(`div`,{className:`pull-right margin-16--left`,children:(0,G.jsx)(`a`,{className:`remove-link-${r+1}`,onClick:e=>{e.preventDefault(),t({index:r,domainObject:n,type:J.DESTROY_DOMAIN})},children:(0,G.jsx)(k,{glyph:ae,size:`small`,className:`margin-12--top margin-12--bottom`,color:`grey`})})})]}),(0,G.jsx)(E,{errors:i})]},`domain-textfield-${r}`)}),(0,G.jsx)(I,{children:(0,G.jsx)(`a`,{href:`#`,onClick:()=>t({type:J.ADD_DOMAIN}),children:`+ add another domain`})})]});X.propTypes={store:B.default.object.isRequired,dispatch:B.default.func.isRequired};var Z=[{value:1,label:`English`},{value:2,label:`Multi-lingual`}],Q=Object.keys(window.constants.embedded_submission_forms.locales).map(e=>({value:e,label:window.constants.embedded_submission_forms.locales[e]})),$=({selected:e,onChange:n})=>(0,G.jsx)(t,{items:[{id:null,label:`Auto`},{id:`#000000`,label:`Black`},{id:`#FFFFFF`,label:`White`}],selectedId:e,onClick:e=>n(e)});$.propTypes={selected:B.default.string,onChange:B.default.func.isRequired};var be=({team:e})=>{let[t,{loading:n}]=ee(me,{onQueryUpdated:()=>!1,onCompleted:({updateEmbeddedSubmissionForm:e})=>{e.was_successful?R():ie()}}),[r,i]=(0,V.useState)(Y(e).promotion_enabled),[a,s]=(0,V.useState)(Y(e).typeface),[c,l]=(0,V.useState)(Y(e).accent_color),[u,d]=(0,V.useState)(Y(e).accent_text_color),[f,p]=(0,V.useState)(Y(e).link_color),[m,_]=(0,V.useState)(Y(e).button_color),[v,y]=(0,V.useState)(Y(e).button_text_color),[b,C]=(0,V.useState)(Y(e).version),[E,D]=(0,V.useState)(Y(e).locales),[k,A]=(0,V.useState)(Y(e).supports_dark_mode??!0),N=se({buttonColor:m,buttonTextColor:v,accentColor:c,accentTextColor:u,linkColor:f,typeFace:a}),P=e=>`/${e}/embedded_submissions/preview?${oe({button_color:m||void 0,button_text_color:v||void 0,link_color:f||void 0,typeface:a||void 0,accent_color:c||void 0,accent_text_color:u||void 0})}`,F=()=>{t({variables:{team_id:e.id,promotion_enabled:r}}).then(({data:{updateEmbeddedSubmissionForm:e}})=>{let t=e.team.embedded_submission_forms.edges[0].node.uuid,n=window.open(P(t),`_blank`);n!==null&&n.focus()})},{enabled:L}=te(de,e.organization.handle);return(0,G.jsx)(I,{children:(0,G.jsxs)(w,{className:`spec-customization`,children:[(0,G.jsx)(w.Heading,{children:(0,G.jsx)(`div`,{children:`Customization`})}),(0,G.jsx)(w.Content,{children:(0,G.jsxs)(x.Context,{name:constants.gates.all.embedded_submission_customization,teamHandle:e.handle,children:[(0,G.jsxs)(x.Open,{children:[(0,G.jsx)(I,{children:(0,G.jsxs)(`label`,{style:{display:`flex`},children:[(0,G.jsx)(S,{name:`promotion_enabled`,className:`spec-promotion-enabled`,checked:r,onChange:e=>i(e.target.checked)}),`Show "Powered by HackerOne" on the submission form`]})}),(0,G.jsx)(I,{children:(0,G.jsxs)(`label`,{style:{display:`flex`},children:[(0,G.jsx)(S,{name:`supports_dark_mode`,className:`spec-supports-dark-mode`,checked:k,onChange:e=>A(e.target.checked)}),`Match visitor theme (light/dark)`]})}),L&&e.organization.gate_i18n_embedded_submission_forms_opened&&(0,G.jsxs)(G.Fragment,{children:[(0,G.jsx)(I,{children:(0,G.jsx)(j,{alignItems:`flex-end`,children:(0,G.jsx)(j,{flexBasis:`50%`,children:(0,G.jsxs)(`div`,{style:{width:`70%`},children:[(0,G.jsx)(M,{children:`Select Form Version`}),(0,G.jsx)(h,{defaultValue:Z.find(e=>e.value===b),onChange:e=>C(e.value),options:Z})]})})})}),b===2&&(0,G.jsx)(I,{children:(0,G.jsx)(j,{alignItems:`flex-end`,children:(0,G.jsx)(j,{flexBasis:`50%`,children:(0,G.jsxs)(`div`,{style:{width:`70%`},children:[(0,G.jsx)(M,{children:`Select Locales`}),(0,G.jsx)(h,{defaultValue:Q.filter(({value:e})=>E.includes(e)),onChange:e=>D(e.map(({value:e})=>e)),options:Q,isMulti:!0})]})})})})]}),(0,G.jsx)(I,{children:(0,G.jsx)(j,{alignItems:`flex-end`,children:(0,G.jsx)(j,{flexBasis:`50%`,children:(0,G.jsxs)(`div`,{style:{width:`70%`},children:[(0,G.jsx)(M,{children:`Select Typeface`}),(0,G.jsx)(h,{placeholder:`Default`,testId:`typeface-dropdown`,defaultValue:a,onChange:e=>s(e.value),options:fe.map(e=>({value:e,label:e,style:{fontFamily:e}}))})]})})})}),(0,G.jsxs)(I,{children:[(0,G.jsx)(M,{children:`Select Link Color`}),(0,G.jsxs)(j,{alignItems:`center`,children:[(0,G.jsx)(j,{flexBasis:`50%`,children:(0,G.jsx)(`div`,{style:{width:`70%`},children:(0,G.jsx)(`div`,{className:`input-wrapper`,name:`link_color`,children:(0,G.jsx)(K,{id:`link_color`,name:`link_color`,label:`Select Link Color`,initialValue:f,onChange:e=>p(e)})})})}),(0,G.jsx)(`strong`,{className:`daisy-text daisy-text--small daisy-text--grey`,children:`Preview`}),(0,G.jsx)(`div`,{className:`spec-preview-link margin-24--left`,style:N,children:(0,G.jsx)(T,{className:`daisy-link`,to:`#`,children:`I'm a link`})})]})]}),(0,G.jsxs)(I,{children:[(0,G.jsx)(M,{children:`Select Accent Color`}),(0,G.jsxs)(j,{alignItems:`center`,children:[(0,G.jsx)(j,{flexBasis:`50%`,children:(0,G.jsxs)(`div`,{style:{width:`70%`},children:[(0,G.jsx)(`div`,{className:`input-wrapper`,name:`accent_color`,children:(0,G.jsx)(K,{id:`accent_color`,name:`accent_color`,label:`Select Accent Color`,initialValue:c,onChange:e=>l(e)})}),(0,G.jsxs)(`div`,{className:`flex flex-col input-wrapper accent_text_color`,children:[(0,G.jsx)(M,{children:`Select Accent Text Color`}),(0,G.jsx)($,{selected:u,onChange:d})]})]})}),(0,G.jsx)(`strong`,{className:`daisy-text daisy-text--small daisy-text--grey`,children:`Preview`}),(0,G.jsx)(`div`,{className:`spec-preview-timeline embedded-submission-form margin-24--left daisy-text`,style:N,children:(0,G.jsx)(O.Entry,{children:(0,G.jsx)(O.Indicator,{children:(0,G.jsx)(O.Step,{step:1})})})})]})]}),(0,G.jsxs)(I,{size:`extra-large`,children:[(0,G.jsx)(M,{children:`Select Button Color`}),(0,G.jsxs)(j,{alignItems:`center`,children:[(0,G.jsx)(j,{flexBasis:`50%`,children:(0,G.jsxs)(`div`,{style:{width:`70%`},children:[(0,G.jsx)(`div`,{className:`input-wrapper`,name:`button_color`,children:(0,G.jsx)(K,{id:`button_color`,name:`button_color`,label:`Select Button Color`,initialValue:m,onChange:e=>_(e)})}),(0,G.jsxs)(`div`,{className:`flex flex-col input-wrapper button_text_color`,children:[(0,G.jsx)(M,{children:`Select Button Text Color`}),(0,G.jsx)($,{selected:v,onChange:y})]})]})}),(0,G.jsx)(`strong`,{className:`daisy-text daisy-text--small daisy-text--grey`,children:`Preview`}),(0,G.jsx)(`div`,{className:`margin-24--left`,style:N,children:(0,G.jsx)(ne,{className:`spec-submit-report-preview`,children:`Submit report`})})]})]}),(0,G.jsxs)(`div`,{className:`flex space-x-md pull-right`,children:[Y(e).uuid?(0,G.jsx)(o,{variation:g.Secondary,renderAs:`link`,to:P(Y(e).uuid),onClick:t=>{t.preventDefault(),window.open(P(Y(e).uuid),`_blank`,`noreferrer`)},children:`Preview form`}):(0,G.jsx)(o,{disabled:n,variation:g.Secondary,onClick:F,children:`Preview form`}),(0,G.jsx)(o,{disabled:n,variation:g.Primary,onClick:()=>t({variables:{team_id:e.id,promotion_enabled:!!r,typeface:a,accent_color:c===`#`?null:c,accent_text_color:u,link_color:f===`#`?null:f,button_color:m===`#`?null:m,button_text_color:v,version:b,locales:E,supports_dark_mode:k}}),children:n?`Saving...`:`Save changes`})]}),(0,G.jsx)(`div`,{className:`clearfix`})]}),(0,G.jsx)(x.Closed,{children:(0,G.jsx)(`div`,{className:`spec-gate-notice`,children:(0,G.jsxs)(`div`,{className:`inline-banner inline-banner--notice`,children:[(0,G.jsx)(`h3`,{children:`Upgrade to use this feature`}),`To customize your embedded submission form, you need to upgrade your product edition. Learn more about customization`,` `,(0,G.jsx)(T,{to:`https://docs.hackerone.com/en/articles/8541571-embedded-submission-form`,children:`here`}),`, or `,(0,G.jsx)(T,{to:`mailto:sales@hackerone.com`,children:`contact us`}),` `,`for more information.`]})})})]})})]})})};be.propTypes={team:B.default.object.isRequired};var xe=()=>(0,G.jsx)(`div`,{className:`row pull-right`,children:(0,G.jsx)(o,{children:`Save configuration`})}),Se=({team:e,refetch:t})=>{let[n,r]=(0,V.useReducer)(ye,_e(e)),[i]=ee(pe,{onQueryUpdated:()=>!1,onCompleted:({updateEmbeddedSubmissionDomains:e})=>{if(e.was_successful)R(),t();else{let t=D(e.errors);r({value:t,type:J.ADD_ERRORS})}}}),a=({event:t})=>{t.preventDefault(),i({variables:(()=>{let t=(0,z.default)(n.form.domains.value,e=>e.url).filter(e=>e.length);return{team_id:e.id,embedded_submission_domains:t}})()})};return(0,G.jsxs)(`div`,{children:[(0,G.jsx)(`div`,{className:`spec-scopes-title mb-md`,children:(0,G.jsx)(p,{children:`Embedded Submission Configuration`})}),(0,G.jsx)(I,{children:(0,G.jsxs)(w,{children:[(0,G.jsxs)(w.Heading,{children:[(0,G.jsxs)(I,{size:`extra-large`,children:[(0,G.jsx)(`div`,{children:`Configure Domain Allowlist`}),(0,G.jsxs)(E,{children:[`Specify the domains you want to include an iframe on here to configure the security settings. Please be sure to fill in a Fully Qualified Domain Name (FQDN), such as`,` `,(0,G.jsx)(`a`,{href:`https://www.hackerone.com`,children:`https://www.hackerone.com`}),`. You can add up to 100 domains.`]})]}),e.state===`soft_launched`&&!e.entry_vdp&&(0,G.jsx)(I,{children:(0,G.jsx)(F,{variation:`yellow`,children:`You're about to configure embedded submissions for your private program. This means that hackers will be able to submit vulnerabilities to your program as long as they have access to the embedded submission form, even if they’re not explicitly invited to your program. Your program will no longer be strictly private when you integrate this form on your website.`})})]}),(0,G.jsx)(w.Content,{children:(0,G.jsxs)(`form`,{onSubmit:e=>a({event:e}),children:[(0,G.jsx)(X,{store:n,dispatch:r}),(0,G.jsx)(xe,{}),(0,G.jsx)(`div`,{className:`clearfix`})]})})]})}),(0,G.jsx)(be,{team:e,store:n,dispatch:r}),Y(e).uuid&&(0,G.jsxs)(G.Fragment,{children:[(0,G.jsx)(I,{children:(0,G.jsxs)(w,{children:[(0,G.jsxs)(w.Heading,{children:[(0,G.jsx)(`div`,{children:`Embedded Script`}),(0,G.jsx)(E,{children:`Copy and paste the following code on your website to embed a submission form.`})]}),(0,G.jsx)(w.Content,{children:(0,G.jsx)(`div`,{className:`inline-banner monospace`,children:(e=>`<script async src="${window.location.origin}/${e}/embedded_submissions/script" data-url="${window.location.origin}/${e}/embedded_submissions/new?locale=en" data-name="h1-embedded-submission" type="text/javascript"><\/script>`)(Y(e).uuid)})})]})}),(0,G.jsx)(I,{children:(0,G.jsxs)(w,{children:[(0,G.jsxs)(w.Heading,{children:[(0,G.jsxs)(`div`,{children:[(0,G.jsx)(`strong`,{children:`Alternative`}),`: Direct`,` `,(0,G.jsx)(`code`,{children:`<iframe />`}),` element`]}),(0,G.jsx)(E,{children:`Copy and paste the following HTML on your website to embed a frame directly onto your page without including dynamic JavaScript.`})]}),(0,G.jsx)(w.Content,{children:(0,G.jsx)(`div`,{className:`inline-banner monospace`,children:(e=>`<iframe src="${window.location.origin}/${e}/embedded_submissions/new?locale=en"  frameborder="0" title="Submit Vulnerability Report" style="border: none; width: 100%; height: 1000px;" />`)(Y(e).uuid)})})]})})]})]})};Se.propTypes={team:B.default.object.isRequired,refetch:B.default.func};var Ce=({handle:e})=>{let{data:t,loading:n,refetch:r}=L(he,{variables:{handle:e}});return n?(0,G.jsx)(b,{}):(0,G.jsx)(Se,{team:t.team,refetch:r})};Ce.propTypes={handle:B.default.string.isRequired};var we=class extends V.Component{static propTypes={match:B.default.shape({params:B.default.shape({handle:B.default.string.isRequired}).isRequired}).isRequired};render(){let e=this.props.match.params.handle;return(0,G.jsx)(N,{children:(0,G.jsx)(C,{pageLayout:!0,header:(0,G.jsx)(A,{...this.props,pageLayout:!0}),content:(0,G.jsx)(`div`,{children:(0,G.jsx)(Ce,{handle:e})}),footer:(0,G.jsx)(y,{}),hasBackground:!1})})}};export{we as default};
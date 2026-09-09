import{o as e}from"./rolldown-runtime-DAXXjFlN.js";import{$_ as t,Ar as n,Ax as r,By as i,Ca as a,Ci as o,Cp as s,Ct as c,Fw as l,Gd as u,Iw as d,Kx as f,Li as p,Ln as m,Lr as h,Ly as g,Ma as _,Mf as v,Mr as y,Na as b,Nb as x,Pb as S,Pf as C,Qd as w,Qy as T,Rn as ee,Rw as te,Ry as E,Ux as ne,Vb as D,Vf as O,Vu as re,Vx as k,Vy as A,Wd as j,Wl as ie,Wx as ae,Wy as oe,Xd as se,Xi as ce,Y_ as le,Yf as ue,Yn as de,bb as fe,br as pe,cd as me,ci as he,cp as ge,cv as M,db as N,dv as _e,eb as ve,gu as ye,jr as be,ki as xe,kn as Se,lp as Ce,nb as P,pu as we,qx as F,rb as Te,sb as Ee,sd as De,tb as Oe,tf as ke,tp as Ae,uw as je,vb as Me,wp as Ne,yb as Pe,yf as Fe,yv as Ie,zd as Le,zx as Re}from"./vendor-_WdvpBLr.js";import{$m as ze,Ah as Be,Ao as Ve,Fs as He,Gs as Ue,Ju as We,Kl as Ge,Lm as Ke,Ls as qe,Oo as Je,Pf as Ye,Ps as Xe,Qm as Ze,Ri as Qe,Sd as I,Sh as $e,Sm as L,Th as et,Uc as tt,V as nt,Wi as rt,Ws as it,Yr as at,Ys as R,_h as z,df as B,dh as ot,ec as st,ep as V,fl as ct,fm as lt,gc as ut,ih as dt,jo as ft,kh as pt,ko as mt,lh as H,mf as ht,mr as gt,op as _t,pf as vt,qf as yt,ql as bt,qs as xt,uh as St,ui as Ct,vh as U,vm as W,wo as wt,wt as Tt,ym as G,yp as Et}from"./app-5pKgUmmm.js";import{t as Dt}from"./tabs-D04eFuSP.js";import{t as Ot}from"./format_bytes-CNxcX6FD.js";import{t as kt}from"./startCase-CDmOTtbv.js";import"./outline-B91AlHOq.js";import{t as At}from"./asset_filter_sheet-C0Bo-W68.js";import{t as jt}from"./outline-e3IpHVjE.js";import{t as Mt}from"./baseline-C1o43icd.js";import{t as Nt}from"./max_groups_banner-BoCFAucO.js";import{t as Pt}from"./outline-DtcHKA3V.js";import{t as Ft}from"./tabs-CK50rHQ_.js";var It=`data:image/svg+xml,%3csvg%20width='18'%20height='22'%20viewBox='0%200%2018%2022'%20fill='none'%20xmlns='http://www.w3.org/2000/svg'%3e%3cpath%20d='M9%200L0%204V10C0%2015.55%203.84%2020.74%209%2022C14.16%2020.74%2018%2015.55%2018%2010V4L9%200ZM16%2010C16%2011.85%2015.49%2013.65%2014.62%2015.21L13.17%2013.76C14.46%2011.82%2014.24%209.18%2012.53%207.47C10.58%205.52%207.41%205.52%205.46%207.47C3.51%209.42%203.51%2012.59%205.46%2014.54C7.17%2016.25%209.81%2016.46%2011.75%2015.18L13.47%2016.9C12.28%2018.32%2010.74%2019.41%209%2019.94C4.98%2018.69%202%2014.52%202%2010V5.3L9%202.19L16%205.3V10ZM9%2014C7.34%2014%206%2012.66%206%2011C6%209.34%207.34%208%209%208C10.66%208%2012%209.34%2012%2011C12%2012.66%2010.66%2014%209%2014Z'%20fill='currentcolor'/%3e%3c/svg%3e`,K=e(Re()),q=l(),Lt={A:`green`,B:`yellow`,C:`orange`,D:`orange`,E:`pink`,F:`red`,U:`gray`},Rt=({riskRating:e})=>(0,q.jsx)(`span`,{className:`align-middle spec-risk-rating-label`,children:(0,q.jsx)(C,{color:Lt[e],children:e})});Rt.propTypes={riskRating:K.default.string};var J=e(te()),zt=({risk:e})=>{let[t,n]=(0,J.useState)(!1),r=Et()!==pt.LIGHT;return(0,q.jsxs)(q.Fragment,{children:[(0,q.jsxs)(I.Row,{className:`spec-asset-risks-row cursor-pointer`,onClick:()=>n(!t),children:[(0,q.jsx)(I.Cell,{width:`60`,children:(0,q.jsx)(Rt,{riskRating:e.rating})}),(0,q.jsx)(I.Cell,{children:(0,q.jsx)(`span`,{className:`text-sm font-bold align-middle`,children:e.title})}),(0,q.jsx)(I.Cell,{width:`60`,children:(0,q.jsx)(H,{justifyContent:`flex-end`,children:(0,q.jsx)(`button`,{"data-testid":`spec-risk-collapse-button`,children:(0,q.jsx)(dt,{glyph:t?Ze:ze,size:`medium`,color:r?`white`:`black`,className:`margin-8--left`})})})})]},`tags-group-${e.id}`),t&&(0,q.jsx)(I.Row,{className:`spec-risk-row tag-risk`,children:(0,q.jsxs)(I.Cell,{colSpan:2,className:`h-spacing-48 `,children:[(0,q.jsx)(`div`,{className:`text-sm font-bold mb-spacing-8`,children:`Type`}),(0,q.jsx)(`p`,{className:`text-sm text-neutral-300 dark:text-neutral-600 mb-spacing-8`,children:e.readable_type}),e.description&&(0,q.jsxs)(q.Fragment,{children:[(0,q.jsx)(`div`,{className:`text-sm font-bold mb-spacing-8`,children:`Description`}),(0,q.jsx)(We,{className:`markdownable text-sm text-neutral-300 dark:text-neutral-600 mb-spacing-8`,markdown:e.description})]}),e.evidence&&(0,q.jsxs)(q.Fragment,{children:[(0,q.jsx)(`div`,{className:`text-sm font-bold mb-spacing-8`,children:`Evidence`}),(0,q.jsx)(We,{className:`markdownable text-sm text-neutral-300 dark:text-neutral-600 mb-spacing-8`,markdown:e.evidence})]}),e.proposed_action&&(0,q.jsxs)(q.Fragment,{children:[(0,q.jsx)(`div`,{className:`text-sm font-bold mb-spacing-8`,children:`Proposed action`}),(0,q.jsx)(We,{className:`markdownable text-sm text-neutral-300 dark:text-neutral-600 mb-spacing-8`,markdown:e.proposed_action})]})]})},`tag-${e.id}`)]})};zt.propTypes={risk:K.default.object.isRequired};var Bt=({risks:e,loading:t})=>(0,q.jsx)(q.Fragment,{children:(0,q.jsx)(w,{children:(0,q.jsxs)(`div`,{className:`spec-asset-risks-tab`,children:[t&&(0,q.jsx)(et,{}),!t&&(0,q.jsx)(q.Fragment,{children:(0,q.jsx)(I,{fixed:!0,children:(0,q.jsx)(I.Body,{children:e.map(e=>(0,q.jsx)(zt,{risk:e},`asset-risk-group-${e.id}`))})})})]})})});Bt.propTypes={risks:K.default.array.isRequired,loading:K.default.bool.isRequired};var Vt=`data:image/svg+xml,%3csvg%20xmlns='http://www.w3.org/2000/svg'%20width='24'%20height='24'%20viewBox='0%200%2024%2024'%3e%3cpath%20d='M21%2012l-4.37%206.16c-.37.52-.98.84-1.63.84h-3v-2h3l3.55-5L15%207H5v3H3V7c0-1.1.9-2%202-2h10c.65%200%201.26.31%201.63.84L21%2012zm-11%203H7v-3H5v3H2v2h3v3h2v-3h3v-2z'/%3e%3c/svg%3e`,Y=e(ce());F();var Ht=f`
  mutation updateAssetDescription($assetId: ID!, $description: String!) {
    updateAssetDescription(
      input: { asset_id: $assetId, description: $description }
    ) {
      was_successful
      asset {
        id
        description
      }
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
`,Ut=({assetId:e,initialValue:t,onSuccess:n,onCancel:r})=>{let i={description:t},a=new p(new Y.default({description:{type:String,label:null,uniforms:{id:`spec-edit-asset-description`,component:qe,placeholder:`Add an asset description`},optional:!0}})),[o,{loading:s}]=z(Ht,{onCompleted:({updateAssetDescription:{was_successful:e,errors:t,asset:r}})=>{e?(G(),n(r.description)):W()}}),c=({description:t})=>{o({variables:{assetId:e,description:t}})},l=(0,J.createRef)();return(0,q.jsxs)(`div`,{children:[(0,q.jsx)(it,{schema:a,model:i,onSubmit:c,showInlineError:!0,ref:l,className:`flex grow shrink flex-col`,children:(0,q.jsx)(`div`,{style:{maxWidth:`100%`},children:(0,q.jsx)(R,{name:`description`,disabled:s})})}),(0,q.jsxs)(`div`,{className:`flex justify-end gap-md`,children:[(0,q.jsx)(T,{iconOnly:!0,icons:{center:{accessibilityLabel:`Cancel`,src:A}},onClick:()=>{r?.()},variation:`ghost-secondary`,testId:`cancel-description`}),(0,q.jsx)(T,{iconOnly:!0,icons:{center:{accessibilityLabel:`Confirm`,src:ye}},onClick:()=>{l.current?.submit()},variation:`ghost-secondary`,testId:`submit-description`})]})]})};Ut.propTypes={assetId:K.default.string.isRequired,initialValue:K.default.string,onSuccess:K.default.func,onCancel:K.default.func};var Wt={organization_manager:`You must have Asset Manager permissions to perform this action`},Gt=({disabled:e,messageKey:t,children:n,testId:r})=>{let i=Wt[t];return e?(0,q.jsx)(`span`,{"data-testid":r,children:(0,q.jsx)(N,{testId:`unauthorized-tooltip`,text:i,children:n})}):(0,q.jsx)(`span`,{"data-testid":r,children:n})};Gt.propTypes={disabled:K.default.bool.isRequired,messageKey:K.default.string.isRequired,children:K.default.node.isRequired,testId:K.default.string};var Kt=({canManage:e,asset:t})=>{let[n,r]=(0,J.useState)(!1),i=t.description?.length>300?(0,q.jsx)(`div`,{"data-testid":`spec-asset-description-expandable`,children:(0,q.jsx)(tt,{content:t.description,truncateHeight:72,enableMarkdown:!0,disableContextMenu:!0})}):(0,q.jsx)(`div`,{"data-testid":`spec-asset-description-interactive`,children:(0,q.jsx)(We,{className:`markdownable`,markdown:t.description,disableContextMenu:!0})});return(0,q.jsx)(q.Fragment,{children:n?(0,q.jsx)(Ut,{assetId:t.id,initialValue:t.description,onSuccess:()=>r(!1),onCancel:()=>r(!1)}):(0,q.jsxs)(`div`,{className:`flex justify-between items-center`,children:[i,(0,q.jsx)(Gt,{testId:`edit-button-wrapper`,messageKey:`organization_manager`,disabled:!e,children:(0,q.jsx)(T,{iconOnly:!0,disabled:!e,icons:{center:{accessibilityLabel:`Edit`,src:Ie}},onClick:()=>{r(!0)},variation:`ghost-secondary`,small:!0,testId:`edit-description-button`})})]})})};Kt.propTypes={canManage:K.default.bool.isRequired,asset:K.default.shape({id:K.default.string.isRequired,description:K.default.string})},F();var qt=f`
  mutation RemoveTagFromAsset($assetId: ID!, $tagId: ID!) {
    removeTagFromAsset(input: { asset_id: $assetId, tag_id: $tagId }) {
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
    }
  }
`,Jt=({asset:e,tag:t,canManage:n})=>{let[r]=z(qt,{variables:{assetId:e.id,tagId:t.id},refetchQueries:[`AssetSidebarQuery`,`AssetGroupAssetsQuery`,`AssetGroupSearchQuery`,`AssetGroupCountsQuery`,`ProgramSettingsScopeManagement`],onCompleted:e=>{e.removeTagFromAsset.was_successful?L(`notice`,`Tag removed!`):W()}});return(0,q.jsx)(`div`,{className:`inline-block m-spacing-4 spec-asset-tag`,children:n?(0,q.jsx)(C,{dismissable:!0,onDismiss:()=>{r()},rounded:!1,children:t.name_with_category}):(0,q.jsx)(C,{rounded:!1,children:t.name_with_category})},t.id)};Jt.propTypes={asset:K.default.object.isRequired,tag:K.default.object.isRequired,canManage:K.default.bool.isRequired},F();var Yt=f`
  mutation updateAssetIdentifyMutation($assetId: ID!, $identifier: String!) {
    updateAssetIdentifier(
      input: { asset_id: $assetId, identifier: $identifier }
    ) {
      was_successful
      asset {
        id
        identifier
      }
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
`,Xt=({initialValue:e,assetId:t,onSuccess:n,onCancel:r})=>{let i={identifier:e},a=new p(new Y.default({identifier:{type:String,label:null,required:!0,uniforms:{id:`spec-edit-asset-identifier`}}})),[o,{loading:s}]=z(Yt,{onCompleted:({updateAssetIdentifier:{was_successful:e,errors:t,asset:r}})=>{e?(G(),n(r.identifier)):W()}}),c=({identifier:e})=>{o({variables:{assetId:t,identifier:e}})},l=(0,J.createRef)();return(0,q.jsxs)(`div`,{className:`flex justify-between`,children:[(0,q.jsx)(it,{schema:a,model:i,onSubmit:c,showInlineError:!0,ref:l,children:(0,q.jsx)(R,{name:`identifier`,wrapperClassName:`edit-identifier-input m-spacing-0`,disabled:s})}),(0,q.jsxs)(`div`,{className:`flex justify-end gap-md`,children:[(0,q.jsx)(T,{iconOnly:!0,icons:{center:{accessibilityLabel:`Confirm`,src:ye}},onClick:()=>{l.current?.submit()},variation:`ghost-secondary`,small:!0,testId:`submit-identifier`}),(0,q.jsx)(T,{iconOnly:!0,icons:{center:{accessibilityLabel:`Cancel`,src:A}},onClick:()=>{r?.()},variation:`ghost-secondary`,small:!0,testId:`cancel-identifier`})]})]})};Xt.propTypes={assetId:K.default.string.isRequired,initialValue:K.default.string,onSuccess:K.default.func,onCancel:K.default.func};var Zt=({asset:e})=>{let t=e.display_name===`Domain`?`https://${e.identifier}`:e.identifier;return(0,q.jsx)(q.Fragment,{children:e.display_name===`Domain`||e.display_name===`URL`?(0,q.jsx)(`a`,{className:`spec-asset-link`,href:t,target:`_blank`,rel:`noreferrer`,children:e.identifier}):e.identifier})};Zt.propTypes={asset:K.default.shape({identifier:K.default.string,display_name:K.default.string})};var Qt=({canManage:e,asset:t})=>{let[n,r]=(0,J.useState)(!1);return(0,q.jsx)(q.Fragment,{children:e&&t.display_name===`Other Asset`?n?(0,q.jsx)(Xt,{assetId:t.id,initialValue:t.identifier,onSuccess:()=>r(!1),onCancel:()=>r(!1)}):(0,q.jsxs)(`div`,{className:`flex gap-sm`,children:[t.identifier,(0,q.jsx)(T,{iconOnly:!0,icons:{center:{accessibilityLabel:`Edit`,src:Ie}},onClick:()=>{r(!0)},variation:`ghost-secondary`,small:!0,testId:`edit-identifier-button`})]}):(0,q.jsx)(Zt,{asset:t})})};Qt.propTypes={canManage:K.default.bool.isRequired,asset:K.default.shape({id:K.default.string.isRequired,identifier:K.default.string,display_name:K.default.string})};var $t=({attachment:e,onClick:t})=>(0,q.jsx)(q.Fragment,{children:(0,q.jsx)(`a`,{className:`spec-attachment-link attachment-link`,href:e.expiring_url,target:`_blank`,rel:`noreferrer`,onClick:t,children:e.file_name})});$t.propTypes={attachment:K.default.object.isRequired,onClick:K.default.func.isRequired},F();var en=f`
  mutation updateAssetReference($assetId: ID!, $reference: String!) {
    updateAssetReference(input: { asset_id: $assetId, reference: $reference }) {
      was_successful
      asset {
        id
        reference
      }
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
`,tn=({assetId:e,initialValue:t,onSuccess:n,onCancel:r})=>{let i={reference:t},a=new p(new Y.default({reference:{type:String,label:null,required:!1,uniforms:{id:`spec-asset-reference`}}})),[o,{loading:s}]=z(en,{onCompleted:({updateAssetReference:{was_successful:e,errors:t,asset:r}})=>{e?(G(),n(r.reference)):W()}}),c=({reference:t})=>{o({variables:{assetId:e,reference:t}})},l=(0,J.createRef)();return(0,q.jsxs)(`div`,{className:`flex justify-between`,children:[(0,q.jsx)(it,{schema:a,model:i,onSubmit:c,showInlineError:!0,ref:l,children:(0,q.jsx)(R,{name:`reference`,wrapperClassName:`m-spacing-0`,disabled:s})}),(0,q.jsxs)(`div`,{className:`flex`,children:[(0,q.jsx)(T,{iconOnly:!0,icons:{center:{accessibilityLabel:`Cancel`,src:A}},onClick:()=>{r?.()},variation:`ghost-secondary`,testId:`cancel-reference`,small:!0}),(0,q.jsx)(T,{iconOnly:!0,icons:{center:{accessibilityLabel:`Confirm`,src:ye}},onClick:()=>{l.current?.submit()},variation:`ghost-secondary`,testId:`submit-reference`,small:!0})]})]})};tn.propTypes={assetId:K.default.string.isRequired,initialValue:K.default.string,onSuccess:K.default.func,onCancel:K.default.func};var nn=({canManage:e,asset:t})=>{let[n,r]=(0,J.useState)(!1);return(0,q.jsx)(q.Fragment,{children:e?n?(0,q.jsx)(tn,{assetId:t.id,initialValue:t.reference||``,onSuccess:()=>r(!1),onCancel:()=>r(!1)}):(0,q.jsxs)(`div`,{className:`flex justify-between items-center`,children:[(0,q.jsx)(`div`,{children:t.reference}),(0,q.jsx)(T,{iconOnly:!0,icons:{center:{accessibilityLabel:`Edit`,src:Ie}},onClick:()=>{r(!0)},variation:`ghost-secondary`,small:!0,testId:`edit-reference-button`})]}):t.reference})};nn.propTypes={canManage:K.default.bool.isRequired,asset:K.default.shape({id:K.default.string.isRequired,reference:K.default.string})};var rn=e=>{let{isSelected:t,data:n}=e;return(0,q.jsxs)(xe.Option,{...e,children:[(0,q.jsxs)(`div`,{className:`flex items-center gap-sm`,children:[(0,q.jsx)(Ge,{rating:n.label.toUpperCase()}),(0,q.jsx)(bt,{rating:n.label.toUpperCase()})]}),t&&(0,q.jsx)(st,{})]})};rn.propTypes={isSelected:K.default.bool,data:K.default.shape({label:K.default.string.isRequired}).isRequired},F();var an=e(b()),on=window.constants.assetInventory.maxSeverityOptions,sn=f`
  mutation updateAssetMaxSeverity(
    $assetId: ID!
    $maxSeverity: SeverityRatingEnum!
  ) {
    updateAssetMaxSeverity(
      input: { asset_id: $assetId, max_severity: $maxSeverity }
    ) {
      was_successful
      asset {
        id
        max_severity
      }
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
`,cn=({assetId:e,initialValue:t,onSuccess:n,onCancel:r})=>{let i={maxSeverity:t},a=new p(new Y.default({maxSeverity:{type:String,label:null,required:!0,defaultValue:`critical`,allowedValues:on,uniforms:{id:`asset-type`,components:{Option:rn},options:on.map(e=>({value:e,label:(0,an.default)(e)}))}}})),[o,{loading:s}]=z(sn,{onCompleted:({updateAssetMaxSeverity:{was_successful:e,errors:t,asset:r}})=>{e?(G(),n(r.reference)):W()}}),c=({maxSeverity:t})=>{o({variables:{assetId:e,maxSeverity:t}})},l=(0,J.createRef)();return(0,q.jsxs)(`div`,{className:`flex justify-between`,children:[(0,q.jsx)(it,{schema:a,model:i,onSubmit:c,showInlineError:!0,ref:l,children:(0,q.jsx)(R,{name:`maxSeverity`,wrapperClassName:`m-spacing-0`,disabled:s})}),(0,q.jsxs)(`div`,{className:`flex`,children:[(0,q.jsx)(T,{iconOnly:!0,icons:{center:{accessibilityLabel:`Cancel`,src:A}},onClick:()=>{r?.()},variation:`ghost-secondary`,testId:`cancel-reference`,small:!0}),(0,q.jsx)(T,{iconOnly:!0,icons:{center:{accessibilityLabel:`Confirm`,src:ye}},onClick:()=>{l.current?.submit()},variation:`ghost-secondary`,testId:`submit-max-severity`,small:!0})]})]})};cn.propTypes={assetId:K.default.string.isRequired,initialValue:K.default.string,onSuccess:K.default.func,onCancel:K.default.func};var ln=({canManage:e,asset:t})=>{let[n,r]=(0,J.useState)(!1);return(0,q.jsx)(q.Fragment,{children:n?(0,q.jsx)(cn,{assetId:t.id,initialValue:t.max_severity||``,onSuccess:()=>r(!1),onCancel:()=>r(!1)}):(0,q.jsxs)(`div`,{className:`flex justify-between items-center`,children:[(0,q.jsxs)(`div`,{className:`flex items-center gap-sm`,children:[(0,q.jsx)(Ge,{rating:t.max_severity?.toUpperCase()}),(0,q.jsx)(bt,{rating:t.max_severity?.toUpperCase()})]}),(0,q.jsx)(T,{iconOnly:!0,disabled:!e,icons:{center:{accessibilityLabel:`Edit`,src:Ie}},onClick:()=>{r(!0)},variation:`ghost-secondary`,small:!0,testId:`edit-severity-button`})]})})};ln.propTypes={canManage:K.default.bool.isRequired,asset:K.default.shape({id:K.default.string.isRequired,max_severity:K.default.string})};var un=e(Ee()),dn=e(D()),fn=window.constants.assetPorts?.protocols??[],pn=e=>{if(!e||typeof e!=`string`)return`UNKNOWN`;let t=e.toLowerCase().trim();return fn.includes(t)?t.toUpperCase():`UNKNOWN`},mn=({name:e,rating:t,setShowChangeCVSSModal:n,testId:r,canManage:i})=>(0,q.jsxs)(I.Row,{children:[(0,q.jsx)(I.Cell,{children:e}),(0,q.jsx)(I.Cell,{children:(0,q.jsxs)(`div`,{className:`flex items-center justify-between`,children:[(0,q.jsxs)(`div`,{className:`flex items-center gap-sm`,children:[(0,q.jsx)(Ge,{rating:t?.toUpperCase()}),(0,q.jsx)(bt,{rating:t?.toUpperCase()})]}),(0,q.jsx)(Gt,{messageKey:`organization_manager`,disabled:!i,children:(0,q.jsx)(T,{disabled:!i,iconOnly:!0,icons:{center:{accessibilityLabel:`Edit`,src:Ie}},onClick:()=>{n(!0)},variation:`ghost-secondary`,small:!0,testId:r})})]})})]});mn.propTypes={name:K.default.string,rating:K.default.string,setShowChangeCVSSModal:K.default.func.isRequired,testId:K.default.string,canManage:K.default.bool};var hn=({loading:e,canManage:t,asset:n,setAssetAttachment:r,setShowAddTagModal:i,setShowChangeCVSSModal:a,setShowAssetAttachmentModal:o,risksEnabled:s,attachmentsEnabled:c,assetScannerBetaEnabled:l})=>{let u=`${n?.attachments?.length??0} ${un.default.pluralize(n?.attachments?.length??0,`screenshot`)} (found by Asset Scanner):`,d=n?.external_source?`Asset Scanner (${n.external_source})`:`Asset Scanner`;return(0,q.jsx)(w,{children:(0,q.jsx)(`div`,{className:`spec-asset-sidebar`,children:e?(0,q.jsx)(I,{fixed:!0,children:(0,q.jsx)(I.Body,{children:(0,dn.default)(10).map(e=>(0,q.jsxs)(I.Row,{children:[(0,q.jsx)(I.Cell,{children:(0,q.jsx)(M,{lines:1})}),(0,q.jsx)(I.Cell,{children:(0,q.jsx)(M,{lines:1})}),(0,q.jsx)(I.Cell,{})]},e))})}):(0,q.jsxs)(q.Fragment,{children:[(0,q.jsx)(I,{children:(0,q.jsxs)(I.Body,{children:[(0,q.jsxs)(I.Row,{children:[(0,q.jsx)(I.Cell,{children:`Identifier`}),(0,q.jsx)(I.Cell,{children:(0,q.jsx)(Qt,{canManage:t,asset:n})})]}),(0,q.jsxs)(I.Row,{className:`spec-asset-type`,children:[(0,q.jsx)(I.Cell,{children:`Asset type`}),(0,q.jsx)(I.Cell,{children:n?.display_name})]}),(0,q.jsxs)(I.Row,{className:`spec-asset-tags`,children:[(0,q.jsx)(I.Cell,{children:`Tags`}),(0,q.jsxs)(I.Cell,{children:[n?.asm_tags?.nodes?.map(e=>(0,q.jsx)(Jt,{asset:n,tag:e,canManage:t},e.id)),(0,q.jsx)(Gt,{messageKey:`organization_manager`,disabled:!t,children:(0,q.jsx)(T,{disabled:!t,onClick:()=>{i(!0)},small:!0,variation:`ghost`,testId:`spec-add-tag`,icons:{left:{src:Vt}},children:`Add Tag`})})]})]}),l&&(0,q.jsxs)(I.Row,{className:`spec-asset-ports`,children:[(0,q.jsx)(I.Cell,{children:`Ports`}),(0,q.jsx)(I.Cell,{children:n?.asset_ports&&n.asset_ports.length>0?(0,q.jsx)(`div`,{className:`flex flex-wrap gap-xs`,children:[...n.asset_ports].sort((e,t)=>e.port-t.port).map(e=>(0,q.jsxs)(C,{rounded:!1,color:`gray`,children:[e.port,`:`,pn(e.protocol)]},e.id))}):(0,q.jsx)(`span`,{className:`text-gray-500`,children:`No ports discovered`})})]}),(0,q.jsx)(mn,{name:`Confidentiality requirement`,rating:n?.confidentiality_requirement,setShowChangeCVSSModal:a,canManage:t}),(0,q.jsx)(mn,{name:`Integrity requirement`,rating:n?.integrity_requirement,setShowChangeCVSSModal:a,canManage:t}),(0,q.jsx)(mn,{name:`Availability requirement`,rating:n?.availability_requirement,setShowChangeCVSSModal:a,canManage:t}),(0,q.jsxs)(I.Row,{children:[(0,q.jsx)(I.Cell,{children:`Maximum Severity`}),(0,q.jsx)(I.Cell,{children:(0,q.jsx)(ln,{canManage:t,asset:n})})]}),(0,q.jsxs)(I.Row,{className:`spec-asset-programs`,children:[(0,q.jsx)(I.Cell,{children:`Programs`}),(0,q.jsx)(I.Cell,{children:n?.teams?.edges?.map(e=>(0,q.jsx)(`div`,{className:`inline-block m-spacing-4`,children:(0,q.jsx)(ot,{to:`/${e.node.handle}`,newTab:!0,children:(0,q.jsx)(C,{rounded:!1,color:{[constants.assetInventory.coverageTypes.untested]:`gray`,[constants.assetInventory.coverageTypes.inScope]:`green`,[constants.assetInventory.coverageTypes.outOfScope]:`yellow`}[e.coverage],children:e.node.name},e.node.handle)})},e.node.handle))})]}),n?.source===`DarktraceIntegration`&&(0,q.jsxs)(I.Row,{className:`spec-asset-source`,children:[(0,q.jsx)(I.Cell,{children:`Source`}),(0,q.jsx)(I.Cell,{children:d})]}),(0,q.jsxs)(I.Row,{children:[(0,q.jsx)(I.Cell,{children:`Created at`}),(0,q.jsx)(I.Cell,{children:yt({date:n?.created_at})})]}),(0,q.jsxs)(I.Row,{children:[(0,q.jsx)(I.Cell,{children:`ID`}),(0,q.jsx)(I.Cell,{children:n?.databaseId})]}),(0,q.jsxs)(I.Row,{children:[(0,q.jsx)(I.Cell,{children:`Description (internal)`}),(0,q.jsx)(I.Cell,{children:(0,q.jsx)(Kt,{canManage:t,asset:n})})]}),(0,q.jsxs)(I.Row,{children:[(0,q.jsx)(I.Cell,{children:`Reference`}),(0,q.jsx)(I.Cell,{children:(0,q.jsx)(nn,{canManage:t,asset:n})})]}),s&&(0,q.jsxs)(I.Row,{children:[(0,q.jsx)(I.Cell,{children:`Risk Rating`}),(0,q.jsxs)(I.Cell,{children:[(0,q.jsx)(Rt,{riskRating:n?.risk_rating}),` `]})]})]})}),c&&(0,q.jsxs)(`ul`,{className:`attachments-list`,children:[(0,q.jsx)(`li`,{className:`attachments-heading spec-attachments-heading`,children:u}),n?.attachments?.map(e=>(0,q.jsx)(`li`,{className:`attachments-item`,children:(0,q.jsx)($t,{attachment:e,onClick:t=>{t.preventDefault(),r(e),o(!0)}})},e.id))]})]})})})};hn.propTypes={loading:K.default.bool.isRequired,asset:K.default.object,refetch:K.default.func,canManage:K.default.bool.isRequired,setAssetAttachment:K.default.func.isRequired,setShowAddTagModal:K.default.func.isRequired,setShowChangeCVSSModal:K.default.func.isRequired,setShowAssetAttachmentModal:K.default.func.isRequired,risksEnabled:K.default.bool.isRequired,attachmentsEnabled:K.default.bool.isRequired,assetScannerBetaEnabled:K.default.bool.isRequired};var gn=({name:e,value:t})=>(0,q.jsx)(q.Fragment,{children:(0,q.jsxs)(`div`,{className:`flex flex-row p-md border-b border-neutral-700 border-solid first:border-none`,children:[(0,q.jsx)(`div`,{className:`basis-1/3`,children:e}),(0,q.jsx)(`div`,{className:`basis-2/3 text-neutral-100 dark:text-neutral-950`,children:t})]})});gn.propTypes={name:K.default.string.isRequired,value:K.default.any};var _n=e(ie()),vn=({whois:e})=>{let t=e=>e.includes(`_`)?e.toUpperCase():(0,an.default)(e);return(0,_n.default)(e)?null:(0,q.jsx)(q.Fragment,{children:e&&(0,q.jsxs)(`div`,{className:`flex flex-col mt-lg`,children:[(0,q.jsx)(`div`,{className:`flex flex-row`,children:(0,q.jsx)(`div`,{className:`grow font-bold`,children:`WHOIS`})}),Object.keys(e).map(n=>(0,q.jsx)(gn,{name:t(n),value:e[n]},n))]})})};vn.propTypes={whois:K.default.object.isRequired};var X={SET_SEARCH_TERM:`SET_SEARCH_TERM`,SET_ROW_MENU_ASSET_ID:`SET_ROW_MENU_ASSET_ID`,SET_SELECTED_ASSET_ID:`SET_SELECTED_ASSET_ID`,SET_SELECTED_ASSET_TYPES:`SET_SELECTED_ASSET_TYPES`,SET_SELECTED_PROGRAMS:`SET_SELECTED_PROGRAMS`,SET_SELECTED_ASM_TAG_IDS:`SET_SELECTED_ASM_TAG_IDS`,SET_TAG_CATEGORY_CLAUSES:`SET_TAG_CATEGORY_CLAUSES`,SET_SELECTED_PORTS:`SET_SELECTED_PORTS`,SET_SELECTED_PROTOCOLS:`SET_SELECTED_PROTOCOLS`,CLEAR_SEARCH_FILTERS:`CLEAR_SEARCH_FILTERS`,SET_SHOW_FILTERS_SHEET:`SET_SHOW_FILTERS_SHEET`,SET_SELECTED_ASSETS_GROUP_MODE:`SET_SELECTED_ASSETS_GROUP_MODE`,SET_SHOW_ADD_SCOPE_MODAL:`SET_SHOW_ADD_SCOPE_MODAL`,SET_SHOW_ADD_ASSET_MODAL:`SET_SHOW_ADD_ASSET_MODAL`,SET_SHOW_IMPORT_FROM_CSV_MODAL:`SET_SHOW_IMPORT_FROM_CSV_MODAL`,SET_SHOW_IMPORT_SUMMARY_MODAL:`SET_SHOW_IMPORT_SUMMARY_MODAL`,SET_SHOW_OUT_OF_SCOPE_MODAL:`SET_SHOW_OUT_OF_SCOPE_MODAL`,SET_SHOW_REMOVE_SCOPE_MODAL:`SET_SHOW_REMOVE_SCOPE_MODAL`,SET_SHOW_ARCHIVE_ASSETS_MODAL:`SHOW_ARCHIVE_ASSETS_MODAL`,SET_SHOW_UNARCHIVE_ASSETS_MODAL:`SET_UNARCHIVE_ASSETS_MODAL`,SET_SELECTED_TAB:`SET_SELECTED_TAB`,SET_CHECKED_ASSETS:`SET_CHECKED_ASSETS`,CLEAR_CHECKED_ASSETS:`CLEAR_CHECKED_ASSETS`,TOGGLE_CHECK_ASSET:`TOGGLE_CHECK_ASSET`,TOGGLE_CHECK_ASSET_GROUP:`TOGGLE_CHECK_ASSET_GROUP`,TOGGLE_SELECT_ALL_ASSETS:`TOGGLE_SELECT_ALL_ASSETS`,SET_CURRENT_PAGE:`SET_CURRENT_PAGE`,SET_HAS_H1_ASSETS_ENTERPRISE_FEATURE:`SET_HAS_H1_ASSETS_ENTERPRISE_FEATURE`,SET_ASSET_SIDEBAR_TAB_INDEX:`SET_ASSET_SIDEBAR_TAB_INDEX`,SET_RECOMMENDATION_ASSET_IDS:`SET_RECOMMENDATION_ASSET_IDS`,OPEN_ADD_SCOPE_FROM_RECOMMENDATIONS:`OPEN_ADD_SCOPE_FROM_RECOMMENDATIONS`,SET_SELECTED_AI_RISK_RATINGS:`SET_SELECTED_AI_RISK_RATINGS`,SET_SELECTED_DOMAINS:`SET_SELECTED_DOMAINS`,RESET:`RESET`},Z={searchTerm:``,checkedAssets:[],checkedAssetIdentifiers:[],checkedAssetsInProgram:[],checkedAssetObjects:[],allAssetsSelected:!1,rowMenuAssetId:null,selectedAssetId:null,assetSidebarTabIndex:0,selectedProgramIds:[],selectedAssetTypes:[],selectedAsmTagIds:{},selectedTagCategoryClauses:{},selectedPorts:[],selectedProtocols:[],showFiltersSheet:!1,selectedTab:`all`,selectedAssetsGroupMode:`DEFAULT`,showAddAssetModal:!1,showAddScopeModal:!1,showOutOfScopeModal:!1,showRemoveScopeModal:!1,showArchiveAssetsModal:!1,showUnarchiveAssetsModal:!1,showImportFromCsvModal:!1,showImportSummaryModal:!1,recommendationAssetIds:[],selectedAiRiskRatings:[],selectedDomains:[],currentPage:0},yn=(e,t,n)=>{let r=n===`identifier`?t.map(({identifier:e})=>e):t.map(({databaseId:e})=>Number(e));if(e.length>0&&t.length>0&&r.every(t=>e.includes(t))){let t=new Set(r);return e.filter(e=>!t.has(e))}return Array.from(new Set([...e,...r]))},bn=(e,t)=>{if(e.length>0&&t.length>0&&t.every(t=>e.includes(t))){let n=new Set(t);return e.filter(e=>!n.has(e))}return Array.from(new Set([...e,...t]))},xn=(e,t,n)=>{let r;switch(n){case`identifier`:r=t.identifier;break;case`id`:r=Number(t.databaseId);break;case`coverage`:if(![constants.assetInventory.coverageTypes.inScope,constants.assetInventory.coverageTypes.outOfScope].includes(t.coverage))return e;r=Number(t.databaseId);break;default:break}return e.includes(r)?e.filter(e=>e!==r):[...e,r]},Sn=(e,t)=>e.includes(t)?e.filter(e=>e!==t):[...e,t],Q={currentPage:0,checkedAssets:[],checkedAssetsInProgram:[],checkedAssetIdentifiers:[],checkedAssetObjects:[],allAssetsSelected:!1},Cn=(e={},t)=>{switch(t.type){case X.SET_SEARCH_TERM:return{...e,searchTerm:t.value,...Q};case X.SET_ROW_MENU_ASSET_ID:return{...e,rowMenuAssetId:t.value};case X.SET_SELECTED_ASSET:return{...e,selectedAsset:t.value};case X.SET_SELECTED_ASSET_ID:return{...e,selectedAssetId:t.value};case X.SET_SELECTED_PROGRAMS:return{...e,selectedProgramIds:t.value,...Q};case X.SET_SELECTED_ASSET_TYPES:return{...e,selectedAssetTypes:t.value,...Q};case X.SET_SELECTED_ASM_TAG_IDS:return{...e,selectedAsmTagIds:t.value,...Q};case X.SET_TAG_CATEGORY_CLAUSES:return{...e,selectedTagCategoryClauses:t.value,...Q};case X.SET_SELECTED_PORTS:return{...e,selectedPorts:Array.from(new Set(t.value)),...Q};case X.SET_SELECTED_PROTOCOLS:return{...e,selectedProtocols:Array.from(new Set(t.value)),...Q};case X.CLEAR_SEARCH_FILTERS:return{...e,selectedProgramIds:Z.selectedProgramIds,selectedAssetTypes:Z.selectedAssetTypes,selectedAsmTagIds:Z.selectedAsmTagIds,selectedTagCategoryClauses:Z.selectedTagCategoryClauses,selectedPorts:Z.selectedPorts,selectedProtocols:Z.selectedProtocols,selectedAiRiskRatings:Z.selectedAiRiskRatings,selectedDomains:Z.selectedDomains,...Q};case X.SET_SHOW_FILTERS_SHEET:return{...e,showFiltersSheet:t.value};case X.SET_SELECTED_ASSETS_GROUP_MODE:return{...e,selectedAssetsGroupMode:t.value,...Q};case X.SET_ASSET_SIDEBAR_TAB_INDEX:return{...e,assetSidebarTabIndex:t.value};case X.SET_CHECKED_ASSETS:return{...e,checkedAssets:t.value.map(e=>Number(e.globalId)),checkedAssetObjects:t.value};case X.CLEAR_CHECKED_ASSETS:return{...e,checkedAssets:[],checkedAssetsInProgram:[],checkedAssetIdentifiers:[],checkedAssetObjects:[]};case X.TOGGLE_CHECK_ASSET:return{...e,checkedAssets:xn(e.checkedAssets,t.value,`id`),checkedAssetIdentifiers:xn(e.checkedAssetIdentifiers,t.value,`identifier`),checkedAssetsInProgram:xn(e.checkedAssetsInProgram,t.value,`coverage`),checkedAssetObjects:Sn(e.checkedAssetObjects,t.value)};case X.TOGGLE_CHECK_ASSET_GROUP:return{...e,checkedAssets:yn(e.checkedAssets,t.value,`id`),checkedAssetIdentifiers:yn(e.checkedAssetIdentifiers,t.value,`identifier`),checkedAssetObjects:bn(e.checkedAssetObjects,t.value)};case X.TOGGLE_SELECT_ALL_ASSETS:return{...e,checkedAssets:e.allAssetsSelected?[]:t.value.map(({databaseId:e})=>Number(e)),checkedAssetObjects:e.allAssetsSelected?[]:t.value,allAssetsSelected:!e.allAssetsSelected};case X.SET_SELECTED_TAB:return{...e,selectedTab:t.value||constants.assetInventory.coverageTypes.all,...Q};case X.SET_SHOW_ADD_SCOPE_MODAL:return{...e,showAddScopeModal:t.value};case X.SET_SHOW_ADD_ASSET_MODAL:return{...e,showAddAssetModal:t.value};case X.SET_SHOW_OUT_OF_SCOPE_MODAL:return{...e,showOutOfScopeModal:t.value};case X.SET_SHOW_REMOVE_SCOPE_MODAL:return{...e,showRemoveScopeModal:t.value};case X.SET_SHOW_ARCHIVE_ASSETS_MODAL:return{...e,showArchiveAssetsModal:t.value};case X.SET_SHOW_UNARCHIVE_ASSETS_MODAL:return{...e,showUnarchiveAssetsModal:t.value};case X.SET_SHOW_IMPORT_FROM_CSV_MODAL:return{...e,showImportFromCsvModal:t.value};case X.SET_SHOW_IMPORT_SUMMARY_MODAL:return{...e,showImportSummaryModal:t.value};case X.SET_CURRENT_PAGE:return{...e,currentPage:t.value,checkedAssets:[],checkedAssetObjects:[]};case X.SET_RECOMMENDATION_ASSET_IDS:return{...e,recommendationAssetIds:t.value.map(Number)};case X.SET_SELECTED_AI_RISK_RATINGS:return{...e,selectedAiRiskRatings:t.value,...Q};case X.SET_SELECTED_DOMAINS:return{...e,selectedDomains:t.value,...Q};case X.OPEN_ADD_SCOPE_FROM_RECOMMENDATIONS:return{...e,recommendationAssetIds:t.value.map(Number),showAddScopeModal:!0};case X.RESET:return{...Z};default:return e}};F();var wn=({asset:e})=>{let{dispatch:t}=(0,J.useContext)($),n=e=>{t({type:X.SET_ASSET_SIDEBAR_TAB_INDEX,value:0}),t({type:X.SET_SELECTED_ASSET_ID,value:e})};return(0,q.jsx)(`a`,{className:`spec-asset-dns-tab-asset-link asset-link-item flex-1`,onClick:()=>{n(e.id)},children:(0,q.jsxs)(`div`,{className:`flex content-center`,children:[(0,q.jsx)(`span`,{className:`flex-grow py-spacing-8`,children:e.identifier}),(0,q.jsx)(T,{iconOnly:!0,icons:{center:{accessibilityLabel:`View asset overview`,src:u}},onClick:function(){},variation:`ghost-secondary`})]})})};wn.propTypes={asset:K.default.object.isRequired};var Tn=()=>(0,q.jsx)(I,{fixed:!0,children:(0,q.jsx)(I.Body,{children:(0,dn.default)(10).map(e=>(0,q.jsxs)(I.Row,{children:[(0,q.jsx)(I.Cell,{children:(0,q.jsx)(M,{lines:1})}),(0,q.jsx)(I.Cell,{children:(0,q.jsx)(M,{lines:1})}),(0,q.jsx)(I.Cell,{})]},e))})}),En=({associatedIPs:e,relatedDomains:t,nameservers:n,provider:r,cname:i,whois:a})=>(0,q.jsxs)(`div`,{className:`border-spacing-12--bottom mt-lg`,children:[e?.length?(0,q.jsxs)(`div`,{className:`flex flex-col mt-md border-b border-neutral-700 border-solid`,children:[(0,q.jsx)(`div`,{className:`grow font-bold`,children:`Associated IPs`}),e.map(e=>(0,q.jsx)(`div`,{className:`flex items-stretch border-b border-neutral-700 border-solid last:border-none`,children:e.id?(0,q.jsx)(`div`,{className:`px-md flex-1 py-2xs`,children:(0,q.jsx)(wn,{asset:e})}):(0,q.jsx)(`div`,{className:`px-md py-sm`,children:(0,q.jsx)(`span`,{children:e.identifier})})},e.identifier))]}):null,t?.length?(0,q.jsxs)(`div`,{className:`flex flex-col mt-md border-b border-neutral-700 border-solid`,children:[(0,q.jsx)(`div`,{className:`grow font-bold`,children:`Related Domains`}),t.map(e=>(0,q.jsx)(`div`,{className:`flex flex-row border-b border-neutral-700 border-solid last:border-none`,children:(0,q.jsx)(`div`,{className:`px-md flex-1 py-2xs`,children:(0,q.jsx)(wn,{asset:e})})},e.identifier))]}):null,n?.length?(0,q.jsx)(gn,{name:`Nameservers`,value:n.join(`, `)}):null,r&&(0,q.jsx)(gn,{name:`Provider`,value:r}),i&&(0,q.jsx)(gn,{name:`CNAME`,value:i}),a&&(0,q.jsx)(vn,{whois:a})]});En.propTypes={associatedIPs:K.default.array,relatedDomains:K.default.array,nameservers:K.default.array,provider:K.default.string,cname:K.default.string,whois:K.default.object};var Dn=({loading:e,dns_detail:t,related_domains:n,related_ip_addresses:r})=>{let i=t?[...t?.ipv4||[],...t?.ipv6||[]].map(e=>{let t=r.find(t=>t.identifier===e);return t?{...t}:{identifier:e}}):[];return(0,q.jsx)(w,{children:(0,q.jsxs)(`div`,{className:`spec-asset-sidebar`,children:[e&&(0,q.jsx)(Tn,{}),!e&&(t||n)&&(0,q.jsx)(En,{associatedIPs:i,relatedDomains:n,whois:t?.whois,nameservers:t?.nameservers,provider:t?.provider,cname:t?.cname})]})})};Dn.fragments={dns_detail_fragment:f`
    fragment DnsDetailFragment on Asset {
      asset_dns_detail {
        id
        ipv4
        ipv6
        cname
        provider
        nameservers
        whois
      }
    }
  `},Dn.propTypes={loading:K.default.bool.isRequired,dns_detail:K.default.object,related_domains:K.default.array,related_ip_addresses:K.default.array},F();var On=f`
  mutation updateStructuredScope($scopeId: ID!, $instruction: String!) {
    updateStructuredScope(
      input: { structured_scope_id: $scopeId, instruction: $instruction }
    ) {
      was_successful
      structured_scope {
        id
        instruction
      }
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
`,kn=({scopeId:e,initialValue:t,onSuccess:n,onCancel:r})=>{let i={instruction:t},a=new p(new Y.default({instruction:{type:String,label:null,uniforms:{id:`spec-edit-scope-instruction`,component:qe,placeholder:`Add an asset instruction`},optional:!0}})),[o,{loading:s}]=z(On,{onCompleted:({updateStructuredScope:{was_successful:e,errors:t,structured_scope:r}})=>{e?(G(),n(r.instruction)):W()}}),c=({instruction:t})=>{o({variables:{scopeId:e,instruction:t}})},l=(0,J.createRef)();return(0,q.jsxs)(`div`,{children:[(0,q.jsx)(it,{schema:a,model:i,onSubmit:c,showInlineError:!0,ref:l,className:`flex grow shrink flex-col`,children:(0,q.jsx)(`div`,{style:{maxWidth:`100%`},children:(0,q.jsx)(R,{name:`instruction`,disabled:s})})}),(0,q.jsxs)(`div`,{className:`flex justify-end gap-md`,children:[(0,q.jsx)(T,{iconOnly:!0,icons:{center:{accessibilityLabel:`Cancel`,src:A}},onClick:()=>{r?.()},variation:`ghost-secondary`,testId:`cancel-instruction`}),(0,q.jsx)(T,{iconOnly:!0,icons:{center:{accessibilityLabel:`Confirm`,src:ye}},onClick:()=>{l.current?.submit()},variation:`ghost-secondary`,testId:`submit-instruction`})]})]})};kn.propTypes={scopeId:K.default.string.isRequired,initialValue:K.default.string,onSuccess:K.default.func,onCancel:K.default.func};var An=({canManage:e,scope:t})=>{let[n,r]=(0,J.useState)(!1),i=t.instruction?.length>300?(0,q.jsx)(tt,{content:t.instruction,truncateHeight:72,enableMarkdown:!0,disableContextMenu:!0}):(0,q.jsx)(We,{className:`markdownable`,markdown:t.instruction,disableContextMenu:!0});return(0,q.jsx)(q.Fragment,{children:e?n?(0,q.jsx)(kn,{scopeId:t.id,initialValue:t.instruction,onSuccess:()=>r(!1),onCancel:()=>r(!1)}):(0,q.jsxs)(`div`,{className:`flex justify-between items-center`,children:[i,(0,q.jsx)(T,{iconOnly:!0,icons:{center:{accessibilityLabel:`Edit`,src:Ie}},onClick:()=>{r(!0)},variation:`ghost-secondary`,small:!0,testId:`edit-instruction-button`})]}):i})};An.propTypes={canManage:K.default.bool.isRequired,scope:K.default.shape({id:K.default.string.isRequired,instruction:K.default.string})},F();var jn=f`
  query ScopeAttachmentsQuery($id: ID!) {
    scope: node(id: $id) {
      id
      ... on StructuredScope {
        attachments {
          id
          file_name
          file_size
          content_type
          expiring_url
        }
      }
    }
  }
`,Mn=f`
  mutation UploadScopeAttachments($structuredScopeId: ID!, $files: [Upload!]!) {
    uploadScopeAttachments(
      input: { structured_scope_id: $structuredScopeId, files: $files }
    ) {
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
`,Nn=f`
  mutation DestroyScopeAttachments(
    $attachmentIds: [ID!]!
    $structuredScopeId: ID!
  ) {
    destroyScopeAttachments(
      input: {
        attachment_ids: $attachmentIds
        structured_scope_id: $structuredScopeId
      }
    ) {
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
`,Pn=({scopeId:e})=>{let[t,n]=(0,J.useState)(`border-neutral-700`),[r,{loading:i}]=z(Mn,{onCompleted:e=>{e.uploadScopeAttachments.was_successful?G():W()},refetchQueries:[`ScopeAttachmentsQuery`]}),[a,{loading:o}]=z(Nn,{onCompleted:e=>{e.destroyScopeAttachments.was_successful?G():W()},refetchQueries:[`ScopeAttachmentsQuery`]}),{getRootProps:s,getInputProps:l,open:u}=c({maxSize:1024*1024*250,onDrop:(0,J.useCallback)((t,i)=>{i.length>0&&L(`error`,`Some files were rejected. Please check the file size and try again.`),t.length!==0&&(r({variables:{structuredScopeId:e,files:t}}),n(`border-neutral-700`))},[e,r]),onDragEnter:()=>n(`border-blue-400`),onDragLeave:()=>n(`border-neutral-700`)}),{data:d,loading:f}=U(jn,{variables:{id:e}}),p=t=>{a({variables:{attachmentIds:[t],structuredScopeId:e}})};return(0,q.jsx)(`div`,{className:i||o?`disabled`:``,children:(0,q.jsxs)(`div`,{className:`border-dashed border-2 ${t} rounded-md p-md cursor-pointer scope-tab-attachments`,children:[f&&(0,q.jsx)(M,{lines:3}),!f&&d.scope.attachments.map(e=>(0,q.jsxs)(`div`,{className:`p-sm rounded-md bg-neutral-900 flex items-center mb-sm dark:bg-neutral-100`,children:[(0,q.jsx)(`div`,{className:`flex-1`,children:(0,q.jsx)(`a`,{href:e.expiring_url,download:e.file_name,className:`spec-attachment-link`,target:`_blank`,rel:`noreferrer`,children:e.file_name})}),(0,q.jsx)(`div`,{className:`text-neutral-300 dark:text-neutral-800`,children:Ot(e.file_size)}),(0,q.jsx)(`div`,{className:`ml-md text-neutral-300 cursor-pointer spec-attachment-remove dark:text-neutral-800`,onClick:t=>{t.stopPropagation(),p(e.id)},children:(0,q.jsx)(`div`,{className:`mt-[-2px]`,children:(0,q.jsx)(P,{src:`data:image/svg+xml,%3csvg%20xmlns='http://www.w3.org/2000/svg'%20width='24'%20height='24'%20viewBox='0%200%2024%2024'%3e%3cpath%20d='M19%206.41L17.59%205L12%2010.59L6.41%205L5%206.41L10.59%2012L5%2017.59L6.41%2019L12%2013.41L17.59%2019L19%2017.59L13.41%2012L19%206.41z'/%3e%3c/svg%3e`,accessibilityLabel:`Remove file`})})})]},e.id)),(0,q.jsxs)(`div`,{...s({className:`assets-csv-dropzone`}),children:[(0,q.jsx)(`input`,{...l(),className:`spec-scope-attachments-file-input`}),(0,q.jsxs)(`p`,{className:`text-center dark:text-white`,children:[`Drag and drop some files here, or`,` `,(0,q.jsx)(`a`,{onClick:e=>{e.stopPropagation(),e.preventDefault(),u()},children:`click to select files (max 250MB per file)`})]})]})]})})};Pn.propTypes={scopeId:K.default.string.isRequired},F();var Fn=({canManage:e,scopes:t,contextToUse:n})=>{let r=e=>e.eligible_for_submission?(0,q.jsx)(C,{color:`green`,rounded:!1,children:`In scope`}):(0,q.jsx)(C,{color:`yellow`,rounded:!1,children:`Out of scope`});return t?(0,q.jsx)(w,{children:(0,q.jsx)(`div`,{className:`border-spacing-12--bottom`,children:t?.map(t=>(0,q.jsxs)(`div`,{className:`flex flex-col mb-xl`,children:[(0,q.jsx)(`h1`,{className:`text-xl`,children:t.team.name}),(0,q.jsx)(gn,{name:`Coverage`,value:r(t)},t.team.id),(0,q.jsx)(gn,{name:`Bounty`,value:(0,q.jsx)(nt,{value:t.eligible_for_bounty})}),(0,q.jsx)(gn,{name:`Instruction`,value:(0,q.jsx)(An,{canManage:e,scope:t})}),e&&(0,q.jsxs)(`div`,{className:`flex flex-col p-md border-b border-neutral-700 border-solid first:border-none`,children:[(0,q.jsxs)(`div`,{className:`mb-md flex items-center`,children:[(0,q.jsx)(`span`,{children:`Attachments`}),(0,q.jsx)(N,{text:`Attachments will be available for download on the policy scope page`,children:(0,q.jsx)(`span`,{className:`text-neutral-500 flex items-center ml-2xs dark:text-neutral-950`,children:(0,q.jsx)(P,{src:`data:image/svg+xml,%3csvg%20width='25'%20height='24'%20viewBox='0%200%2025%2024'%20xmlns='http://www.w3.org/2000/svg'%3e%3cpath%20fill-rule='evenodd'%20clip-rule='evenodd'%20d='M2.5%2014C2.5%208.48%206.98%204%2012.5%204C18.02%204%2022.5%208.48%2022.5%2014C22.5%2019.52%2018.02%2024%2012.5%2024C6.98%2024%202.5%2019.52%202.5%2014ZM13.5%2013V19H11.5V13H13.5ZM12.5%2022C8.09%2022%204.5%2018.41%204.5%2014C4.5%209.59%208.09%206%2012.5%206C16.91%206%2020.5%209.59%2020.5%2014C20.5%2018.41%2016.91%2022%2012.5%2022ZM13.5%209V11H11.5V9H13.5Z'%20/%3e%3c/svg%3e`,size:`md`,accessibilityLabel:`info`})})})]}),(0,q.jsx)(`div`,{className:`text-neutral-100 dark:text-neutral-950`,children:(0,q.jsx)(Pn,{scopeId:t.id})})]})]},t.id))})}):null};Fn.fragments={structured_scopes_fragment:f`
    fragment StructuredScopeDocument on Asset {
      structured_scopes {
        nodes {
          id
          instruction
          eligible_for_bounty
          eligible_for_submission
          team {
            name
          }
        }
      }
    }
  `},Fn.propTypes={canManage:K.default.bool.isRequired,scopes:K.default.array.isRequired,contextToUse:K.default.object.isRequired},F();var In=({loading:e,asset:t})=>{let n=t?.latest_risk_assessment;return e?(0,q.jsx)(w,{children:(0,q.jsx)(`div`,{className:`spec-risk-score-tab`,children:(0,q.jsx)(I,{fixed:!0,children:(0,q.jsx)(I.Body,{children:(0,dn.default)(8).map(e=>(0,q.jsxs)(I.Row,{children:[(0,q.jsx)(I.Cell,{children:(0,q.jsx)(M,{lines:1})}),(0,q.jsx)(I.Cell,{children:(0,q.jsx)(M,{lines:1})})]},e))})})})}):n?(0,q.jsx)(w,{children:(0,q.jsx)(`div`,{className:`spec-risk-score-tab`,children:(0,q.jsx)(I,{children:(0,q.jsxs)(I.Body,{children:[(0,q.jsxs)(I.Row,{children:[(0,q.jsx)(I.Cell,{children:`Overall Score`}),(0,q.jsx)(I.Cell,{children:(0,q.jsxs)(`div`,{className:`flex items-center gap-sm`,children:[(0,q.jsx)(`span`,{className:`text-xl font-semibold`,children:n.overall_score}),(0,q.jsx)(`span`,{className:`text-gray-500`,children:`/ 100`})]})})]}),(0,q.jsxs)(I.Row,{children:[(0,q.jsx)(I.Cell,{children:`Risk Rating`}),(0,q.jsx)(I.Cell,{children:(0,q.jsx)(Rt,{riskRating:n.risk_rating})})]}),n.key_findings&&n.key_findings.length>0&&(0,q.jsx)(I.Row,{children:(0,q.jsxs)(I.Cell,{colSpan:2,children:[(0,q.jsx)(`div`,{className:`font-semibold mb-2`,children:`Key Findings`}),(0,q.jsx)(`ul`,{className:`list-disc list-inside space-y-3 text-sm`,children:n.key_findings.map((e,t)=>(0,q.jsx)(`li`,{children:e},t))})]})}),n.analyzed_at&&(0,q.jsxs)(I.Row,{children:[(0,q.jsx)(I.Cell,{children:`Analyzed At`}),(0,q.jsx)(I.Cell,{children:yt({date:n.analyzed_at})})]}),(0,q.jsxs)(I.Row,{children:[(0,q.jsx)(I.Cell,{children:`Status`}),(0,q.jsx)(I.Cell,{children:(0,q.jsx)(`span`,{className:`capitalize`,children:n.status})})]})]})})})}):(0,q.jsx)(w,{children:(0,q.jsx)(`div`,{className:`spec-risk-score-tab p-md text-gray-500`,children:`No risk assessment data available for this asset.`})})};In.propTypes={loading:K.default.bool.isRequired,asset:K.default.object},In.fragments={asset:f`
    fragment RiskScoreTab_asset on Asset {
      latest_risk_assessment {
        id
        overall_score
        risk_rating
        key_findings
        analyzed_at
        status
      }
    }
  `};var Ln=e(S()),Rn=({loading:e,asset:t,canManage:r,refetch:i,setAssetAttachment:a,setShowAddTagModal:o,setShowChangeCVSSModal:s,setShowAssetAttachmentModal:c,dnsEnabled:l,risksEnabled:u,attachmentsEnabled:d,assetScannerBetaEnabled:f,advancedAssetScannerManagement:p,contextToUse:m})=>{let{dispatch:h,store:{assetSidebarTabIndex:g}}=(0,J.useContext)(m),_=t?.asset_risks?.filter(e=>!Ln.default.any.existy(e.ended_at,e.mitigated_at)),v=_?.length||0,y=l&&(e=>[e?.related_domains,e?.related_ip_addresses,e?.asset_dns_detail?.whois,e?.asset_dns_detail?.ipv4,e?.asset_dns_detail?.ipv6,e?.asset_dns_detail?.cname,e?.asset_dns_detail?.nameservers,e?.asset_dns_detail?.provider].map(e=>!(0,_n.default)(e)).some(e=>e))(t),b=[{id:`overview`,label:`Overview`,show:!0},{id:`scope`,label:`Programs`,show:!(0,_n.default)(t?.teams?.edges)},{id:`dns`,label:`DNS`,show:y},{id:`risk-score`,label:`Risk Score`,show:f&&p&&!!t?.latest_risk_assessment},{id:`risks`,label:`Risks (${v})`,show:u}].filter(e=>e.show);return(0,q.jsxs)(q.Fragment,{children:[(0,q.jsx)(be.Group,{selectedIndex:g,onChange:e=>{h({type:X.SET_ASSET_SIDEBAR_TAB_INDEX,value:e})},children:(0,q.jsx)(be.List,{tabs:b,size:n.Small})}),(0,q.jsx)(`div`,{className:`mt-spacing-24`,children:(n=>{switch(n){case`risks`:return(0,q.jsx)(Bt,{loading:e,risks:_,canManage:r,refetch:i});case`scope`:return(0,q.jsx)(Fn,{contextToUse:m,canManage:r,scopes:t?.structured_scopes?.nodes});case`dns`:return(0,q.jsx)(Dn,{loading:e,dns_detail:t.asset_dns_detail,related_domains:t.related_domains,related_ip_addresses:t.related_ip_addresses});case`risk-score`:return(0,q.jsx)(In,{loading:e,asset:t});default:return(0,q.jsx)(hn,{setAssetAttachment:a,asset:t,loading:e,canManage:r,setShowAddTagModal:o,setShowChangeCVSSModal:s,setShowAssetAttachmentModal:c,risksEnabled:u,attachmentsEnabled:d,assetScannerBetaEnabled:f})}})(b[g].id)})]})};Rn.propTypes={loading:K.default.bool.isRequired,asset:K.default.object,refetch:K.default.func.isRequired,setAssetAttachment:K.default.func.isRequired,setShowAddTagModal:K.default.func.isRequired,setShowChangeCVSSModal:K.default.func.isRequired,setShowAssetAttachmentModal:K.default.func.isRequired,canManage:K.default.bool.isRequired,risksEnabled:K.default.bool.isRequired,dnsEnabled:K.default.bool.isRequired,attachmentsEnabled:K.default.bool.isRequired,assetScannerBetaEnabled:K.default.bool.isRequired,advancedAssetScannerManagement:K.default.bool.isRequired,contextToUse:K.default.object.isRequired},F();var zn=e(re()),Bn=e(d()),Vn=({innerProps:e,innerRef:t,label:n,data:r,isFocused:i,isSelected:a})=>{let o=r.disabled;return(0,q.jsx)(`div`,{role:`option`,"aria-selected":a,"aria-label":n,ref:t,...e,onClick:o?e=>e.preventDefault():e.onClick,className:(0,Bn.default)(`py-[0.625rem] px-xs bg-white dark:bg-neutral-50`,i&&!o&&`!bg-blue-900 dark:!bg-neutral-100`,o?`text-neutral-400 dark:text-neutral-600 cursor-not-allowed pointer-events-none`:`cursor-pointer dark:text-neutral-950 hover:bg-blue-900 dark:hover:bg-neutral-100`,a&&!o&&`font-semibold`),children:n})};Vn.propTypes={innerProps:K.default.object,innerRef:K.default.any,label:K.default.string,data:K.default.object,isFocused:K.default.bool,isSelected:K.default.bool};var Hn=({innerProps:e,innerRef:t,label:n,data:r,isFocused:i,isSelected:a})=>{let o=r.disabled;return(0,q.jsx)(`div`,{ref:t,...e,onClick:o?e=>e.preventDefault():e.onClick,className:(0,Bn.default)(`py-[0.625rem] px-xs bg-white dark:bg-neutral-50`,o?`text-neutral-400 dark:text-neutral-600 cursor-not-allowed pointer-events-none`:`cursor-pointer dark:text-neutral-950 hover:bg-blue-900 dark:hover:bg-neutral-100`,i&&!o&&`!bg-blue-900 dark:!bg-neutral-100`,a&&!o&&`font-semibold`),children:n})};Hn.propTypes={innerProps:K.default.object,innerRef:K.default.any,label:K.default.string,data:K.default.object,isFocused:K.default.bool,isSelected:K.default.bool};var Un=f`
  mutation AddTagToAssets($assetIds: [Int!]!, $tagId: ID!) {
    addTagToAssets(input: { asset_ids: $assetIds, tag_id: $tagId }) {
      was_successful
      errors {
        nodes {
          message
        }
      }
    }
  }
`,Wn=f`
  query AddTagModalCategoriesQuery($handle: String!) {
    organizations(first: 1, where: { handle: { _eq: $handle } }) {
      nodes {
        id
        asm_tag_categories(include_empty: true) {
          nodes {
            id
            name
            unique_tag_per_asset
            asm_tags(first: 1) {
              nodes {
                id
              }
            }
          }
        }
      }
    }
  }
`,Gn=f`
  query AddTagModalAssetsQuery($handle: String!, $assetIds: [Int!]!) {
    organizations(first: 1, where: { handle: { _eq: $handle } }) {
      nodes {
        id
        assets(where: { id: { _in: $assetIds } }) {
          nodes {
            _id
            identifier
            asm_tags {
              nodes {
                id
                asm_tag_category {
                  id
                }
              }
            }
          }
        }
      }
    }
  }
`,Kn=f`
  query AddTagModalQuery(
    $handle: String!
    $categoryId: ID
    $query: String
    $tagsCount: Int!
  ) {
    organizations(first: 1, where: { handle: { _eq: $handle } }) {
      nodes {
        id
        asm_tag_categories(id: $categoryId, include_empty: true) {
          nodes {
            id
            name
            asm_tags(first: $tagsCount, query: $query) {
              nodes {
                id
                name
              }
            }
          }
        }
      }
    }
  }
`,qn=({assetIds:e,organization:n,closeModal:r,onSuccess:a,showModal:o})=>{let[s,c]=(0,J.useState)(null),[l,u]=(0,J.useState)(null),[d,f]=(0,J.useState)([]),[p,m]=(0,J.useState)(!1),[h,_]=(0,J.useState)(!1),[v,y]=(0,J.useState)(null),{data:b,loading:x}=U(Wn,{variables:{handle:n?.handle},fetchPolicy:`network-only`,skip:!o}),{data:S}=U(Gn,{variables:{handle:n?.handle,assetIds:e},fetchPolicy:`network-only`,skip:!o||!e||e.length===0}),C=ae(),w=(0,J.useCallback)(async(e=``)=>{if(!s){f([]);return}m(!0),y(null);try{let{data:t}=await C.query({query:Kn,variables:{handle:n?.handle,categoryId:s.value,query:e,tagsCount:e?25:100},fetchPolicy:`network-only`});if(t?.organizations){let e=t.organizations.nodes[0].asm_tag_categories.nodes[0].asm_tags.nodes.map(e=>{let t={value:e.id,label:e.name,disabled:!1},n=S?.organizations?.nodes?.[0]?.assets?.nodes||[],r=n.filter(t=>t.asm_tags.nodes.some(t=>t.id===e.id));if(r.length>0)if(n.length===1)t.label=`${e.name} — Tag already assigned to this asset`,t.disabled=!0;else if(r.length===n.length)t.label=`${e.name} — Tag already assigned to these assets`,t.disabled=!0;else{let n=r.map(e=>e.identifier).join(`, `);t.label=`${e.name} — Tag already assigned to ${n}`}return t});f(e)}}catch{y(`Failed to load tags. Please try again.`)}finally{m(!1)}},[s,C,n?.handle,S]),T=(0,J.useMemo)(()=>(0,zn.default)(e=>{w(e)},150),[w]);(0,J.useEffect)(()=>()=>{T.cancel()},[T]),(0,J.useEffect)(()=>{s?w(``):(f([]),u(null))},[s,w]);let[ee]=z(Un,{variables:{assetIds:e,tagId:l?.value},refetchQueries:[`OrganizationAssetsOverviewQuery`,`AssetGroupAssetsQuery`,`AssetGroupSearchQuery`,`AssetGroupCountsQuery`,`ProgramSettingsScopeManagement`],onCompleted:e=>{if(e.addTagToAssets.was_successful)L(`notice`,`Tag was successfully added to the asset`),a?.(),r();else{let t=e.addTagToAssets.errors?.nodes?.[0]?.message;t?L(`error`,t):W()}}}),te=(b?.organizations?.nodes?.[0]?.asm_tag_categories?.nodes||[]).map(e=>{let t=e.asm_tags?.nodes?.length===0;return{value:e.id,label:t?`${e.name} — No tags yet`:e.name,disabled:t,uniqueTagPerAsset:e.unique_tag_per_asset,categoryName:e.name}}),E=(0,J.useMemo)(()=>!l||!s?.uniqueTagPerAsset?!1:(S?.organizations?.nodes?.[0]?.assets?.nodes||[]).some(e=>e.asm_tags.nodes.some(e=>e.asm_tag_category?.id===s.value&&e.id!==l.value)),[l,s,S]);return(0,q.jsx)(Ae,{title:e?`Add tag to ${e.length} selected asset${e.length>1?`s`:``}`:`Add tag`,open:o,onClose:r,confirmationButtonProps:{children:`Add Tag`,disabled:Ln.default.falsy(l),onClick:ee},children:(0,q.jsxs)(`div`,{className:`flex flex-col gap-sm`,children:[(0,q.jsxs)(`div`,{className:`flex gap-sm`,children:[(0,q.jsxs)(`div`,{className:`flex-1`,children:[(0,q.jsxs)(`div`,{className:`flex flex-row gap-2xs items-center`,children:[(0,q.jsx)(t,{text:`Tag Category`,required:!0}),(0,q.jsx)(N,{text:`Categories need at least one tag before they can be assigned to assets.`,children:(0,q.jsx)(P,{src:oe,accessibilityLabel:`Information about tag categories`})})]}),(0,q.jsx)(De,{selectedOption:s,onChange:e=>{e?.disabled||(u(null),c(e))},options:te,optionComponent:Vn,testId:`spec-dropdown-category`,placeholder:x?`Loading categories...`:`Select category...`,disabled:x})]}),(0,q.jsxs)(`div`,{className:`flex-1`,children:[(0,q.jsx)(t,{text:`Tag`,required:!0}),(0,q.jsx)(De,{selectedOption:l,onChange:e=>{e?.disabled||u(e)},options:d,optionComponent:Hn,placeholder:`Select tag...`,disabled:s===null,isLoading:p&&!h,onInputChange:e=>{e?(_(!0),T(e)):(_(!1),w(``))},testId:`spec-dropdown-tag`})]})]}),E&&(0,q.jsx)(g,{variation:i.Default,contentSecondary:(0,q.jsxs)(q.Fragment,{children:[`Note: assets can only have one tag from the '${s.categoryName}' category.`,(0,q.jsx)(`br`,{}),`Applying this tag will replace the existing one.`]})}),v&&(0,q.jsx)(`div`,{className:`text-red-600 text-sm`,children:v})]})})};qn.propTypes={assetIds:K.default.array,closeModal:K.default.func.isRequired,onSuccess:K.default.func,organization:K.default.object.isRequired,showModal:K.default.bool.isRequired};var Jn=e(_()),Yn=e(kt()),Xn=({requirement:e,rating:n,onClick:r})=>{let i=t=>(0,Bn.default)(`spec-${e}-${t}`,{[`button-coloring--${t}`]:t===n});return(0,q.jsx)(`div`,{className:`flex flex-column pt-spacing-24`,children:(0,q.jsxs)(`div`,{className:`flex justify-start`,children:[(0,q.jsx)(`div`,{className:`flex w-[130px] pt-spacing-4`,children:(0,q.jsx)(t,{text:(0,Yn.default)(e.replace(`_requirement`,``))})}),(0,q.jsx)(`div`,{className:`flex`,children:(0,q.jsx)(at,{className:`requirement-ratings__button-group`,children:constants.securityRequirementRatings.map(e=>(0,q.jsx)(_t,{size:`medium`,variation:`secondary`,value:e,onClick:r,className:i(e),children:(0,Yn.default)(e)},e))})})]})})};Xn.propTypes={requirement:K.default.string.isRequired,rating:K.default.string,onClick:K.default.func.isRequired};var Zn=({requirements:e,setRequirements:t})=>{let n=(n,r)=>{let i=(0,Jn.default)(n),a=r===e[i]?null:r;t({...e,[i]:a})};return(0,q.jsxs)(w,{children:[(0,q.jsxs)(`div`,{className:`font-bold mb-spacing-8`,children:[`Environmental score `,(0,q.jsx)(ot,{to:`https://docs.hackerone.com/organizations/environmental-score.html`,target:`_blank`,rel:`noopener noreferrer`,external:!0,newTab:!0,children:`[?]`})]}),(0,q.jsxs)(`p`,{className:`text-sm text-neutral-300 dark:text-neutral-600 mb-spacing-0`,children:[`These metrics modify severity of submissions depending on the importance of the affected asset to your organization, measured in terms of maximum impact to Confidentiality, Integrity or Availability. If using`,` `,(0,q.jsx)(ot,{to:`https://www.first.org/cvss/specification-document#4-1-Security-Requirements-CR-IR-AR`,external:!0,children:`CVSS`}),`, these modifiers will be applied as the Environmental Score. The value`,` `,(0,q.jsx)(`em`,{children:`None`}),` will be treated as `,(0,q.jsx)(`em`,{children:`Low`}),` in CVSS version 3.1 and beyond.`]}),(0,q.jsx)(`div`,{className:`mb-spacing-16`,children:constants.assetInventory.securityRequirements.map(t=>(0,q.jsx)(Xn,{requirement:t,rating:e[(0,Jn.default)(t)],onClick:e=>{e.preventDefault(),n(t,e.target.value)}},t))})]})};Zn.propTypes={requirements:K.default.object.isRequired,setRequirements:K.default.func.isRequired},F();var Qn=f`
  mutation UpdateAssetCVSSScore(
    $assetId: ID!
    $availabilityRequirement: SeveritySecurityRequirementEnum
    $confidentialityRequirement: SeveritySecurityRequirementEnum
    $integrityRequirement: SeveritySecurityRequirementEnum
  ) {
    updateAssetCvssScore(
      input: {
        asset_id: $assetId
        availability_requirement: $availabilityRequirement
        confidentiality_requirement: $confidentialityRequirement
        integrity_requirement: $integrityRequirement
      }
    ) {
      was_successful
    }
  }
`,$n=({asset:e,showModal:t,onSuccess:n,closeModal:r})=>{let[i,a]=(0,J.useState)(e.max_severity?{availabilityRequirement:e.availability_requirement,confidentialityRequirement:e.confidentiality_requirement,integrityRequirement:e.integrity_requirement}:{}),[o,{loading:s}]=z(Qn,{onCompleted:({updateAssetCvssScore:{was_successful:e}})=>{e?(G(),r(),n()):W()}});return(0,q.jsx)(V,{showModal:t,size:`large`,title:`Change CVSS score`,handleCloseModal:r,buttonText:`Save`,handleButtonClick:()=>{o({variables:{assetId:e.id,...i}})},buttonDisabled:Ln.default.empty(i),cancelLinkText:`Cancel`,shouldCloseOnOverlayClick:!0,shouldCloseOnEsc:!0,children:(0,q.jsx)(Zn,{disabled:s,requirements:i,setRequirements:a})})};$n.propTypes={asset:K.default.object.isRequired,showModal:K.default.bool.isRequired,closeModal:K.default.func.isRequired,onSuccess:K.default.func.isRequired},F();var er=f`
  query AssetSidebarQuery($id: ID!) {
    asset: node(id: $id) {
      id
      ... on Asset {
        id
        databaseId: _id
        created_at
        updated_at
        identifier
        description
        coverage
        max_severity
        availability_requirement
        confidentiality_requirement
        integrity_requirement
        display_name
        risk_rating
        external_source
        reference
        source
        organization {
          handle
          i_can_create_spot_checks
        }
        teams {
          edges {
            coverage
            eligible_for_bounty
            node {
              id
              handle
              name
            }
          }
        }
        related_domains {
          id
          databaseId: _id
          identifier
        }
        related_ip_addresses {
          id
          databaseId: _id
          identifier
        }
        asm_tags {
          nodes {
            id
            name_with_category
          }
        }
        attachments {
          id
          database_id: _id
          file_name
          expiring_url
          content_type
        }
        asset_risks {
          id
          title
          description
          evidence
          proposed_action
          readable_type
          rating
          ended_at
          mitigated
        }
        asset_ports {
          id
          port
          protocol
        }
        ...DnsDetailFragment
        ...StructuredScopeDocument
        ...RiskScoreTab_asset
      }
    }
  }
  ${Dn.fragments.dns_detail_fragment}
  ${Fn.fragments.structured_scopes_fragment}
  ${In.fragments.asset}
`,tr=({close:e,canManage:t,contextToUse:n})=>{let{store:{selectedAssetId:r},organization:i,organization:{asset_package:a}}=(0,J.useContext)(n),{risks_enabled:o,dns_enabled:s,attachments_enabled:c}=a||{risks_enabled:!1,dns_enabled:!1,attachments_enabled:!1},{feature:l}=Qe(`asset-scanner-beta`,i?.handle),u=!!l,{feature:d}=Qe(`advanced-asset-scanner-management`,i?.handle),f=!!d,{data:p,loading:m,refetch:h}=U(er,{variables:{id:r},fetchPolicy:`cache-and-network`}),{asset:g}=p||{asset:null},[_,v]=(0,J.useState)(!1),[y,b]=(0,J.useState)(!1),[x,S]=(0,J.useState)(!1),[C,w]=(0,J.useState)(null);return _?(0,q.jsx)(qn,{assetIds:[Number(g.databaseId)],showModal:_,closeModal:()=>v(!1),onSuccess:()=>h?.(),organization:i}):y?(0,q.jsx)($n,{asset:g,showModal:y,closeModal:()=>b(!1),onSuccess:()=>h?.()}):x?(0,q.jsx)(Tt,{closeModal:()=>S(!1),file_name:C.file_name,expiring_url:C.expiring_url,type:C.content_type}):(0,q.jsx)(se,{open:!0,onClose:e,title:g?.identifier||`Loading...`,size:{default:`10/12`,lg:`7/12`,xl:`5/12`,"2xl":`4/12`},children:(0,q.jsx)(Rn,{setAssetAttachment:w,setShowAddTagModal:v,setShowChangeCVSSModal:b,setShowAssetAttachmentModal:S,refetch:h,canManage:t,loading:m,asset:g,risksEnabled:o,dnsEnabled:s,attachmentsEnabled:c,assetScannerBetaEnabled:u,advancedAssetScannerManagement:f,contextToUse:n})})};tr.propTypes={close:K.default.func.isRequired,canManage:K.default.bool.isRequired,contextToUse:K.default.object.isRequired};var nr=({containerId:e=`main-content`,threshold:t=100,throttleMs:n=100}={})=>{let[r,i]=(0,J.useState)(!1),a=(0,J.useRef)(null),o=(0,J.useRef)(null),s=(0,J.useCallback)(()=>{let e=o.current;e&&e.scrollTo({top:0,behavior:`smooth`})},[]);return(0,J.useEffect)(()=>{let r=document.getElementById(e);if(!r)return;o.current=r;let s=()=>{if(a.current)return;a.current=window.setTimeout(()=>{a.current=null},n);let e=r.scrollTop>t;i(t=>t===e?t:e)};return s(),r.addEventListener(`scroll`,s,{passive:!0}),()=>{r.removeEventListener(`scroll`,s),a.current&&window.clearTimeout(a.current)}},[e,t,n]),{scrollToTop:s,showScrollToTopButton:r}},rr=`data:image/svg+xml,%3csvg%20xmlns='http://www.w3.org/2000/svg'%20width='24'%20height='24'%20viewBox='0%200%2024%2024'%3e%3cpath%20d='M12%201L3%205v6c0%205.55%203.84%2010.74%209%2012c5.16-1.26%209-6.45%209-12V5l-9-4zm7%2010c0%201.85-.51%203.65-1.38%205.21l-1.45-1.45a4.994%204.994%200%200%200-.64-6.29a5.003%205.003%200%200%200-7.07%200a5.003%205.003%200%200%200%200%207.07a5.006%205.006%200%200%200%206.29.64l1.72%201.72c-1.19%201.42-2.73%202.51-4.47%203.04c-4.02-1.25-7-5.42-7-9.94V6.3l7-3.11l7%203.11V11zm-7%204c-1.66%200-3-1.34-3-3s1.34-3%203-3s3%201.34%203%203s-1.34%203-3%203z'/%3e%3c/svg%3e`,ir=`data:image/svg+xml,%3csvg%20xmlns='http://www.w3.org/2000/svg'%20width='24'%20height='24'%20viewBox='0%200%2024%2024'%3e%3cpath%20d='M20.54%205.23l-1.39-1.68C18.88%203.21%2018.47%203%2018%203H6c-.47%200-.88.21-1.16.55L3.46%205.23C3.17%205.57%203%206.02%203%206.5V19c0%201.1.9%202%202%202h14c1.1%200%202-.9%202-2V6.5c0-.48-.17-.93-.46-1.27zM6.24%205h11.52l.81.97H5.44l.8-.97zM5%2019V8h14v11H5zm8.45-9h-2.9v3H8l4%204l4-4h-2.55z'/%3e%3c/svg%3e`,{ASSET_PLACEHOLDER_DOCUMENTATION:ar}=window.constants.featureToggles,or=({mode:e,model:t,onChangeModel:n,onSubmit:r,currentAssetType:i,children:a,assetTypes:o,flexibleAssetTypesEnabled:s})=>{let c=(0,J.useRef)(),{organization:l}=ht(),{feature:u}=Qe(ar,l?.handle??``),d=o||constants.assetInventory.assetTypes,f=window.constants.assetInventory.maxSeverityOptions,m=e=>e?e.indexOf(`*`)===-1?u?e.indexOf(`{`)!==-1||e.indexOf(`}`)!==-1:!1:!0:!1,h=()=>{let{domain:e,url:t,otherAsset:n}=d;return[e.key,t.key,n&&n.key].includes(i)},g=e=>{if(s&&h()&&m(e))return`urlValueIsAWildcard`},_=()=>({assetType:{type:String,label:`Asset type`,required:!0,defaultValue:d.domain.key,allowedValues:Object.keys(d),uniforms:{id:`asset-type`,options:Object.keys(d).map(e=>({value:e,label:d[e].action,tooltipText:d[e].description}))}},maxSeverity:{type:String,required:!0,label:`Maximum severity`,defaultValue:`critical`,allowedValues:f,uniforms:{id:`asset-type`,components:{Option:rn},options:f.map(e=>({value:e,label:(0,an.default)(e)}))}},identifier:{type:String,label:d[i].identifier,required:!0,uniforms:{id:`identifier`,placeholder:d[i].placeholder},custom:function(){return g(this.value)}}}),v=()=>({reference:{type:String,label:`Reference`,required:!1}}),y=()=>({description:{type:String,label:`Description`,uniforms:{id:`spec-add-asset-description`,component:qe,placeholder:`Add an asset description`},optional:!0}});return Y.default.setDefaultMessages({messages:{en:{urlValueIsAWildcard:`This asset should use the wildcard asset type.`}}}),(0,q.jsx)(it,{schema:new p(new Y.default((()=>{switch(e){case`new`:return{..._(),...v(),...y()};default:return{}}})())),model:t,placeholder:!0,onChangeModel:n,onSubmit:r,showInlineError:!0,ref:c,children:a})};or.propTypes={mode:K.default.oneOf([`new`]).isRequired,model:K.default.object.isRequired,onChangeModel:K.default.func,onSubmit:K.default.func.isRequired,currentAssetType:K.default.string.isRequired,children:K.default.node.isRequired,assetTypes:K.default.object,flexibleAssetTypesEnabled:K.default.bool};var sr=({model:e,onChangeModel:t,onSubmit:n,assetTypes:r,currentAssetType:i,flexibleAssetTypesEnabled:a,children:o})=>(0,q.jsx)(or,{mode:`new`,model:e,onChangeModel:t,onSubmit:n,assetTypes:r,currentAssetType:i,flexibleAssetTypesEnabled:a,children:o});sr.propTypes={model:K.default.object.isRequired,onChangeModel:K.default.func,onSubmit:K.default.func.isRequired,assetTypes:K.default.object,currentAssetType:K.default.string.isRequired,flexibleAssetTypesEnabled:K.default.bool,children:K.default.arrayOf(K.default.node).isRequired},F();var cr=f`
  mutation CreateAsset(
    $organizationId: ID!
    $assetType: AssetImplementationTypeEnum!
    $identifier: String!
    $availabilityRequirement: String
    $confidentialityRequirement: String
    $integrityRequirement: String
    $reference: String
    $description: String
    $maxSeverity: SeverityRatingEnum
    $assetTagsIds: [Int!]
  ) {
    createAsset(
      input: {
        organization_id: $organizationId
        asset_type: $assetType
        identifier: $identifier
        availability_requirement: $availabilityRequirement
        confidentiality_requirement: $confidentialityRequirement
        integrity_requirement: $integrityRequirement
        max_severity: $maxSeverity
        reference: $reference
        description: $description
        asset_tags_ids: $assetTagsIds
      }
    ) {
      was_successful
      asset {
        id
        databaseId: _id
        description
      }
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
`,lr=(e,t)=>{let[n,{loading:r}]=z(cr,{refetchQueries:[`AssetGroupSearchQuery`,`AssetGroupCountsQuery`],onCompleted:n=>{if(!n.createAsset.was_successful){let e=n.createAsset.errors.edges.map(e=>e.node).filter(e=>e.field===`identifier`);if(e.length>0){L(`error`,`Identifier ${e[0].message}`),t&&t(n);return}throw new Xe(n.createAsset.errors)}G(),e(n)}});return[n,r]};F();var{ASSET_PLACEHOLDER_DOCUMENTATION:ur}=window.constants.featureToggles,dr=f`
  query RewardCategoriesForAddAsset($handle: String!) {
    organizations(first: 1, where: { handle: { _eq: $handle } }) {
      nodes {
        id
        asm_tag_categories(include_empty: true) {
          nodes {
            id
            _id
            name
            rewards_eligible
            asm_tags(first: 1) {
              nodes {
                id
              }
            }
          }
        }
      }
    }
  }
`,fr=f`
  query RewardTagsForAddAsset(
    $handle: String!
    $categoryId: ID
    $query: String
    $tagsCount: Int!
  ) {
    organizations(first: 1, where: { handle: { _eq: $handle } }) {
      nodes {
        id
        asm_tag_categories(id: $categoryId, include_empty: true) {
          nodes {
            id
            asm_tags(first: $tagsCount, query: $query) {
              nodes {
                id
                _id
                name
              }
            }
          }
        }
      }
    }
  }
`,pr=({innerProps:e,innerRef:t,label:n,data:r,isFocused:i,isSelected:a})=>{let o=r.disabled;return(0,q.jsx)(`div`,{role:`option`,"aria-selected":a,"aria-label":n,ref:t,...e,onClick:o?e=>e.preventDefault():e.onClick,className:(0,Bn.default)(`py-[0.625rem] px-xs`,!i&&`bg-white dark:bg-neutral-50`,i&&!o&&`!bg-blue-900 dark:bg-neutral-100`,o?`text-neutral-400 dark:text-neutral-600 cursor-not-allowed opacity-50 pointer-events-none`:`cursor-pointer dark:text-neutral-950 hover:bg-blue-900 dark:hover:bg-neutral-100`,a&&!o&&`font-semibold`),children:n})};pr.propTypes={innerProps:K.default.object,innerRef:K.default.any,label:K.default.string,data:K.default.object,isFocused:K.default.bool,isSelected:K.default.bool};var mr=({organizationId:e,showModal:n,setShowModal:r,afterCreate:i,onFail:a,hasGateway:o})=>{let s={organizationId:e,assetType:constants.assetInventory.assetTypes.domain.key},[c,l]=(0,J.useState)(s.assetType),[u,d]=(0,J.useState)({}),[f,p]=(0,J.useState)(null),[m,h]=(0,J.useState)(null),[g,_]=(0,J.useState)([]),[v,y]=(0,J.useState)(!1),[b,S]=(0,J.useState)(null),{organization:C}=ht(),{feature:ee}=Qe(ur,C?.handle??``),te=C?.gate_flexible_asset_types_opened,E=(0,J.useMemo)(()=>{let e=constants.assetInventory.assetTypes;return te?e:Object.keys(e).reduce((t,n)=>(n!==`wildcard`&&n!==`otherAsset`&&(t[n]=e[n]),t),{})},[te]),{data:ne}=U(dr,{variables:{handle:C?.handle},fetchPolicy:`network-only`,skip:!n||!C?.handle}),D=(0,J.useMemo)(()=>(ne?.organizations?.nodes?.[0]?.asm_tag_categories?.nodes||[]).filter(e=>e.rewards_eligible),[ne]),O=(0,J.useMemo)(()=>D.map(e=>{let t=e.asm_tags?.nodes?.length===0;return{value:e.id,label:t?`${e.name} — No tags yet`:e.name,disabled:t,databaseId:e._id}}),[D]);(0,J.useEffect)(()=>{!f&&O.length===1&&!O[0].disabled&&p(O[0])},[O,f]);let re=ae(),k=(0,J.useCallback)(async(e=``)=>{if(!f){_([]);return}y(!0),S(null);try{let{data:t}=await re.query({query:fr,variables:{handle:C?.handle,categoryId:f.value,query:e,tagsCount:e?25:100},fetchPolicy:`network-only`});if(t?.organizations){let e=t.organizations?.nodes?.[0]?.asm_tag_categories?.nodes?.[0]?.asm_tags?.nodes?.map(e=>({value:e._id,label:e.name}))||[];_(e)}}catch{S(`Failed to load tags. Please try again.`)}finally{y(!1)}},[f,re,C?.handle]),A=(0,J.useMemo)(()=>(0,zn.default)(e=>k(e),300),[k]);(0,J.useEffect)(()=>()=>A.cancel(),[A]),(0,J.useEffect)(()=>{f?k(``):(_([]),h(null))},[f,k]);let j=e=>{r(!1),l(s.assetType),d({}),p(null),h(null),i&&i(e)},[ie,oe]=lr(j,a),se=t=>ie({variables:{...t,...u,organizationId:e,assetType:E[c].name,assetTagsIds:m?[parseInt(m.value,10)]:null}}),ce=E.wildcard&&c===E.wildcard.key,le=D.length>0;return(0,q.jsx)(V,{shouldCloseOnEsc:!0,shouldCloseOnOverlayClick:!le,showModal:n,size:`large`,title:`Add an asset`,handleCloseModal:()=>r(!1),children:(0,q.jsx)(w,{children:(0,q.jsxs)(x,{top:`32`,children:[o&&ce&&(0,q.jsx)(x,{bottom:`16`,children:(0,q.jsxs)(`p`,{className:`text-neutral-100 dark:text-neutral-950`,children:[`For Gateway programs, only wildcard routes on the third level domain are accepted at the moment, e.g. *.hackerone.com. Learn more about Gateway accepted assets types on our`,` `,(0,q.jsx)(`a`,{href:`https://docs.hackerone.com/en/articles/8369822-traffic-identification`,children:`docsite`}),`.`]})}),(0,q.jsxs)(sr,{model:s,onSubmit:se,onChangeModel:e=>l(e.assetType),assetTypes:E,currentAssetType:c,flexibleAssetTypesEnabled:te,children:[(0,q.jsxs)(`div`,{className:`flex flex-col w-1/2`,children:[(0,q.jsx)(R,{name:`assetType`,placeholder:`Select an asset type`,className:`asset-type`}),(0,q.jsx)(R,{name:`identifier`})]}),ce&&ee?(0,q.jsxs)(`div`,{className:`mb-sm`,children:[`A wildcard asset supports the following wildcards:`,(0,q.jsxs)(`div`,{className:`flex flex-row justify-start items-baseline mb-2xs`,children:[(0,q.jsx)(`code`,{className:`font-mono`,children:`*`}),(0,q.jsx)(`span`,{children:`, as in the asset`}),(0,q.jsx)(`code`,{className:`font-mono ml-xs`,children:`*.example.com`})]}),(0,q.jsxs)(`div`,{className:`flex flex-row justify-start items-baseline`,children:[(0,q.jsx)(`code`,{className:`font-mono`,children:`{wildcard}`}),(0,q.jsx)(`span`,{children:`, as in the asset `}),(0,q.jsx)(`code`,{className:`font-mono ml-xs`,children:`{subdomain}.example.com`})]})]}):null,(0,q.jsx)(Zn,{requirements:u,setRequirements:d}),(0,q.jsx)(`div`,{className:`flex flex-col w-1/2`,children:(0,q.jsx)(R,{name:`maxSeverity`})}),(0,q.jsx)(R,{name:`description`}),le&&(0,q.jsxs)(q.Fragment,{children:[(0,q.jsxs)(`div`,{className:`flex gap-sm mb-sm`,children:[(0,q.jsxs)(`div`,{className:`flex-1`,children:[(0,q.jsx)(t,{text:`Reward Category`}),(0,q.jsx)(De,{selectedOption:f,onChange:e=>{e?.disabled||(h(null),p(e))},options:O,optionComponent:pr,placeholder:`Select category...`,testId:`spec-reward-category-dropdown`})]}),(0,q.jsxs)(`div`,{className:`flex-1`,children:[(0,q.jsx)(t,{text:`Reward Tag`}),(0,q.jsx)(De,{selectedOption:m,onChange:e=>h(e),options:g,placeholder:v?`Loading tags...`:`Select tag...`,disabled:!f||v,searchable:!0,onInputChange:e=>{e?A(e):k(``)},testId:`spec-reward-tag-dropdown`})]})]}),b&&(0,q.jsx)(`div`,{className:`text-red-600 text-sm`,children:b})]}),(0,q.jsx)(R,{name:`reference`,placeholder:`Add a reference to your internal system`,wrapperClassName:`asset-reference`}),(0,q.jsx)(xt,{}),(0,q.jsx)(Ue,{}),(0,q.jsx)(x,{top:`48`,children:(0,q.jsxs)(`div`,{className:`flex justify-end align-baseline gap-md`,children:[(0,q.jsx)(T,{type:`reset`,variation:`tertiary`,onClick:j,children:`Cancel`}),(0,q.jsx)(T,{type:`submit`,variation:`primary`,disabled:oe,children:`Add asset`})]})})]})]})})})};mr.propTypes={organizationId:K.default.string.isRequired,showModal:K.default.bool.isRequired,setShowModal:K.default.func.isRequired,afterCreate:K.default.func,onFail:K.default.func,hasGateway:K.default.bool};var hr=e=>e.rewards_eligible?`Reward category`:e.unique_tag_per_asset?`Unique category`:null,gr=(e,t)=>e.map(e=>{let n=t?hr(e):null;return{value:e.id,label:n?(0,q.jsxs)(`span`,{children:[e.name,(0,q.jsx)(`span`,{className:`text-neutral-500 ml-xs`,children:n})]}):e.name}}),_r=({tagCategory:e,onDeleteTag:t,onEditTag:n,onEditCategory:r,onDeleteCategory:i,tagFilter:a,canModifyTags:o,showCategoryMetadata:s})=>{let[c,l]=(0,J.useState)(!1),u=Et()!==pt.LIGHT,d=s?hr(e):null,[f,p]=(0,J.useState)(null);return(0,q.jsxs)(q.Fragment,{children:[(0,q.jsxs)(I.Row,{className:`spec-manage-tags-row hover:bg-neutral-900 dark:hover:bg-neutral-100 group cursor-pointer`,onClick:()=>{l(!c)},children:[(0,q.jsx)(I.CellHeader,{className:`cursor-pointer`,children:(0,q.jsxs)(H,{alignItems:`center`,className:`h-spacing-32 gap-xs whitespace-nowrap`,children:[(0,q.jsxs)(`span`,{className:`daisy-text--small daisy-text--bold`,children:[e.name,` (`,e.asm_tags.nodes.filter(a).length,`)`]}),d&&(0,q.jsx)(`span`,{className:`text-neutral-500 text-sm ml-xs`,children:d}),o&&!e.system&&(0,q.jsxs)(`span`,{className:`sm:group-hover:inline-block sm:hidden mr-sm`,children:[r&&(0,q.jsx)(T,{small:!0,iconOnly:!0,icons:{center:{accessibilityLabel:`Edit Category`,src:`data:image/svg+xml,%3csvg%20xmlns='http://www.w3.org/2000/svg'%20width='24'%20height='24'%20viewBox='0%200%2024%2024'%3e%3cpath%20d='M14.06%209.02l.92.92L5.92%2019H5v-.92l9.06-9.06M17.66%203c-.25%200-.51.1-.7.29l-1.83%201.83l3.75%203.75l1.83-1.83a.996.996%200%200%200%200-1.41l-2.34-2.34c-.2-.2-.45-.29-.71-.29zm-3.6%203.19L3%2017.25V21h3.75L17.81%209.94l-3.75-3.75z'/%3e%3c/svg%3e`}},onClick:t=>{t.stopPropagation(),r(e)},variation:`ghost-secondary`,testId:`spec-edit-category-button`}),i&&(e.rewards_eligible?(0,q.jsx)(N,{text:`Disable rewards eligibility before deleting this category`,children:(0,q.jsx)(`span`,{onClick:e=>e.stopPropagation(),children:(0,q.jsx)(T,{small:!0,iconOnly:!0,disabled:!0,icons:{center:{accessibilityLabel:`Delete Category`,src:`data:image/svg+xml,%3csvg%20xmlns='http://www.w3.org/2000/svg'%20width='24'%20height='24'%20viewBox='0%200%2024%2024'%3e%3cpath%20d='M16%209v10H8V9h8m-1.5-6h-5l-1%201H5v2h14V4h-3.5l-1-1zM18%207H6v12c0%201.1.9%202%202%202h8c1.1%200%202-.9%202-2V7z'/%3e%3c/svg%3e`}},variation:`ghost-secondary`,testId:`spec-delete-category-button`})})}):(0,q.jsx)(T,{small:!0,iconOnly:!0,icons:{center:{accessibilityLabel:`Delete Category`,src:`data:image/svg+xml,%3csvg%20xmlns='http://www.w3.org/2000/svg'%20width='24'%20height='24'%20viewBox='0%200%2024%2024'%3e%3cpath%20d='M16%209v10H8V9h8m-1.5-6h-5l-1%201H5v2h14V4h-3.5l-1-1zM18%207H6v12c0%201.1.9%202%202%202h8c1.1%200%202-.9%202-2V7z'/%3e%3c/svg%3e`}},onClick:t=>{t.stopPropagation(),i({id:e.id,name:e.name})},variation:`ghost-secondary`,testId:`spec-delete-category-button`}))]}),o&&e.system&&(0,q.jsx)(`span`,{className:`sm:group-hover:inline-block sm:hidden`,children:(0,q.jsx)(N,{text:`System categories cannot be edited`,children:(0,q.jsx)(P,{src:`data:image/svg+xml,%3csvg%20xmlns='http://www.w3.org/2000/svg'%20width='24'%20height='24'%20viewBox='0%200%2024%2024'%3e%3cpath%20d='M11%207h2v2h-2zm0%204h2v6h-2zm1-9C6.48%202%202%206.48%202%2012s4.48%2010%2010%2010s10-4.48%2010-10S17.52%202%2012%202zm0%2018c-4.41%200-8-3.59-8-8s3.59-8%208-8s8%203.59%208%208s-3.59%208-8%208z'/%3e%3c/svg%3e`,accessibilityLabel:`Information about system tag categories`})})})]})}),(0,q.jsx)(I.Cell,{children:(0,q.jsx)(H,{justifyContent:`flex-end`,alignItems:`center`,children:(0,q.jsx)(`button`,{"data-testid":`spec-tag-collapse-button`,onClick:e=>{e.stopPropagation(),l(!c)},children:(0,q.jsx)(P,{src:c?Ze:ze,size:`medium`,color:u?`white`:`black`,className:`margin-8--left`})})})})]},`tags-group-${e.id}`),c&&e.asm_tags.nodes.filter(a).map(r=>(0,q.jsx)(I.Row,{className:`spec-tag-row tag-row hover:bg-neutral-900 dark:hover:bg-neutral-100`,onMouseEnter:()=>p(r.id),onMouseLeave:()=>p(null),children:(0,q.jsx)(I.Cell,{colSpan:2,className:`py-spacing-0 h-spacing-48`,children:(0,q.jsxs)(H,{justifyContent:`space-between`,alignItems:`center`,children:[(0,q.jsx)(C,{variation:`blue`,size:`small`,children:(0,q.jsx)(`span`,{className:`text-truncate`,style:{maxWidth:300},title:r.name,children:r.name})}),f===r.id&&o&&(0,q.jsxs)(H,{shrink:`0`,children:[(0,q.jsx)(T,{iconOnly:!0,small:!0,icons:{center:{accessibilityLabel:`Edit`,src:`data:image/svg+xml,%3csvg%20xmlns='http://www.w3.org/2000/svg'%20width='24'%20height='24'%20viewBox='0%200%2024%2024'%3e%3cpath%20d='M14.06%209.02l.92.92L5.92%2019H5v-.92l9.06-9.06M17.66%203c-.25%200-.51.1-.7.29l-1.83%201.83l3.75%203.75l1.83-1.83a.996.996%200%200%200%200-1.41l-2.34-2.34c-.2-.2-.45-.29-.71-.29zm-3.6%203.19L3%2017.25V21h3.75L17.81%209.94l-3.75-3.75z'/%3e%3c/svg%3e`}},onClick:()=>n({id:r.id,name:r.name,categoryId:e.id}),variation:`ghost-secondary`,testId:`spec-edit-tag-button`}),(0,q.jsx)(T,{iconOnly:!0,small:!0,icons:{center:{accessibilityLabel:`Delete`,src:`data:image/svg+xml,%3csvg%20xmlns='http://www.w3.org/2000/svg'%20width='24'%20height='24'%20viewBox='0%200%2024%2024'%3e%3cpath%20d='M16%209v10H8V9h8m-1.5-6h-5l-1%201H5v2h14V4h-3.5l-1-1zM18%207H6v12c0%201.1.9%202%202%202h8c1.1%200%202-.9%202-2V7z'/%3e%3c/svg%3e`}},onClick:()=>t({id:r.id,name:r.name}),variation:`ghost-secondary`,testId:`spec-delete-tag-button`})]})]})})},`tag-${r.id}`))]})};_r.propTypes={tagCategory:K.default.object.isRequired,onDeleteTag:K.default.func,onEditTag:K.default.func,onEditCategory:K.default.func,onDeleteCategory:K.default.func,tagFilter:K.default.func.isRequired,canModifyTags:K.default.bool.isRequired,showCategoryMetadata:K.default.bool},F();var{ASSET_TAG_REWARD_CATEGORIES:vr}=window.constants.featureToggles,yr=f`
  query ManageTagsQuery($handle: String!) {
    organizations(first: 1, where: { handle: { _eq: $handle } }) {
      nodes {
        id
        asm_tag_categories {
          nodes {
            id
            name
            system
            can_mutate_tags
            unique_tag_per_asset
            rewards_eligible
            asm_tags {
              nodes {
                id
                name
              }
            }
          }
        }
      }
    }
  }
`,br=({onNewTag:e,onNewTagCategory:t})=>{let[n,r]=(0,J.useState)(!1),i=()=>r(!n),a=(0,J.useRef)(null);return Ye(a,()=>r(!1)),(0,q.jsx)(q.Fragment,{children:(0,q.jsx)(`div`,{className:`asset-row__menu-holder`,ref:a,children:(0,q.jsx)(wt,{popperClassname:`mt-spacing-16 mr-[10rem] spec-manage-tags-menu`,popperPlacement:`bottom-end`,showPopper:n,componentToTarget:(0,q.jsx)(`div`,{className:`h-[44px] flex items-stretch`,children:(0,q.jsx)(T,{variation:`primary`,onClick:i,children:`Create`})}),componentToPop:(0,q.jsxs)(`ul`,{className:`select-menu`,children:[(0,q.jsx)(`li`,{className:`menu-item spec-create-new-tag`,role:`button`,onClick:()=>e(!0),children:`New Tag`}),(0,q.jsx)(`li`,{className:`menu-item spec-create-new-tag-category`,role:`button`,onClick:()=>t(!0),children:`New Category`})]})})})})};br.propTypes={onNewTag:K.default.func.isRequired,onNewTagCategory:K.default.func.isRequired};var xr=({organization:e,close:t,setShowAddCustomTagModal:n,setShowAddCustomTagCategoryModal:r,onEditTag:i,onDeleteTag:a,onEditCategory:o,onDeleteCategory:s})=>{let{data:c,loading:l}=U(yr,{variables:{handle:e?.handle},fetchPolicy:`cache-and-network`}),{enabled:u}=B(vr,e?.handle),[d,f]=(0,J.useState)(``);return(0,q.jsx)(q.Fragment,{children:(0,q.jsx)(se,{open:!0,onClose:t,title:`Custom tags`,accessibilityLabel:`Manage tags`,children:(0,q.jsxs)(`div`,{className:`spec-manage-tags-sheet`,children:[(l||!c)&&(0,q.jsx)(et,{}),!l&&c&&(0,q.jsxs)(q.Fragment,{children:[(0,q.jsxs)(`div`,{className:`flex justify-between gap-md`,children:[(0,q.jsx)(`div`,{className:`flex-grow`,children:(0,q.jsx)(ue,{placeholder:`Search`,icons:{left:{src:`data:image/svg+xml,%3csvg%20viewBox='0%200%2024%2024'%20xmlns='http://www.w3.org/2000/svg'%3e%3cpath%20d='M15.5%2014h-.79l-.28-.27C15.41%2012.59%2016%2011.11%2016%209.5%2016%205.91%2013.09%203%209.5%203S3%205.91%203%209.5%205.91%2016%209.5%2016c1.61%200%203.09-.59%204.23-1.57l.27.28v.79l5%204.99L20.49%2019l-4.99-5zm-6%200C7.01%2014%205%2011.99%205%209.5S7.01%205%209.5%205%2014%207.01%2014%209.5%2011.99%2014%209.5%2014z'/%3e%3cpath%20d='M0%200h24v24H0z'%20fill='none'/%3e%3c/svg%3e`,accessibilityLabel:`Search`}},onChange:e=>f(e.target.value),value:d})}),(0,q.jsx)(br,{onNewTag:n,onNewTagCategory:r})]}),(0,q.jsx)(I,{fixed:!0,children:(0,q.jsx)(I.Body,{children:c.organizations.nodes[0]?.asm_tag_categories?.nodes.map(e=>(0,q.jsx)(_r,{tagCategory:e,canModifyTags:!e.can_mutate_tags,onDeleteTag:a,onEditTag:i,onEditCategory:o,onDeleteCategory:s,tagFilter:e=>e.name.toLowerCase().startsWith(d.toLowerCase()),showCategoryMetadata:u},`tags-group-${e.id}`))})})]})]})})})};xr.propTypes={organization:K.default.object.isRequired,close:K.default.func.isRequired,setShowAddCustomTagModal:K.default.func.isRequired,setShowAddCustomTagCategoryModal:K.default.func.isRequired,onEditTag:K.default.func.isRequired,onDeleteTag:K.default.func.isRequired,onEditCategory:K.default.func,onDeleteCategory:K.default.func};var Sr=J.createContext({});F();var Cr=({mode:e,model:t,onSubmit:n,children:r})=>{let i=(0,J.useRef)(),{teams:a}=(0,J.useContext)(Sr),o=()=>({teamIds:{type:Array,required:!0,minCount:1,defaultValue:a.length===1?[a[0].databaseId]:[],label:`Select program(s)`,uniforms:{id:`asset-team-ids`,component:He,options:a.map(e=>({value:e.databaseId,label:e.name}))}},"teamIds.$":{type:String}}),s=()=>({eligibleForSubmission:{type:String,label:`Define scope`,required:!1,uniforms:{id:`asset-eligible-for-submission`,options:[{value:`true`,label:`In scope`},{value:`false`,label:`Out of scope`}]}}}),c=()=>({eligibleForBounty:{type:String,label:`Bounty eligible`,required:!1,uniforms:{id:`asset-eligible-for-bounty`,options:[{value:`true`,label:`Yes`},{value:`false`,label:`No`}],condition:function(e,t){return t.model.eligibleForSubmission===`true`}}}}),l=()=>({notifySubscribersOnChanges:{type:Boolean,required:!1,label:`Notify subscribers of changes to the scope.`,uniforms:{id:`asset-notify-subscribers-on-changes`}}});return(0,q.jsx)(it,{schema:new p(new Y.default((()=>{switch(e){case`new`:return{...o(),...s(),...c(),...l()};default:return{}}})())),model:t,onSubmit:n,showInlineError:!0,placeholder:!0,ref:i,children:r})};Cr.propTypes={mode:K.default.oneOf([`new`]).isRequired,model:K.default.object.isRequired,onSubmit:K.default.func.isRequired,children:K.default.node.isRequired},Cr.fragments={team:f`
    fragment AddScopeFormWrapperTeamFragment on Team {
      id
      databaseId: _id
      name
    }
  `},F();var wr=({model:e,onSubmit:t,organization:n,children:r})=>{let{scope_management_teams:{nodes:i},i_can_manage_pentest_scope:a,i_can_manage_all_programs_scope:o}=n,s=a?i:i.filter(e=>e.type!==`Engagements::Assessment`);s=o?s:s.filter(e=>e.i_can_manage_program);let c=(0,J.useMemo)(()=>({teams:s}),[s]);return(0,q.jsx)(Sr.Provider,{value:c,children:(0,q.jsx)(Cr,{mode:`new`,model:e,onSubmit:t,children:r})})};wr.propTypes={model:K.default.object.isRequired,onSubmit:K.default.func.isRequired,organization:K.default.object.isRequired,children:K.default.arrayOf(K.default.node.isRequired).isRequired},wr.fragments={organization:f`
    fragment FormOrganizationAssetInventoryFragment on Organization {
      id
      i_can_manage_pentest_scope
      i_can_manage_all_programs_scope
      scope_management_teams {
        nodes {
          id
          type
          i_can_manage_program
          ...AddScopeFormWrapperTeamFragment
        }
      }
    }
    ${Cr.fragments.team}
  `};var Tr=({organizationName:e,customMessage:t,setCustomMessage:n})=>{let[r,i]=(0,J.useState)(!1);return(0,q.jsxs)(`span`,{children:[(0,q.jsx)(ot,{className:`daisy-link--small`,to:`#custom-message-modal`,onClick:e=>{e.preventDefault(),i(!0)},children:t?`Edit custom summary`:`Add a custom summary`}),(0,q.jsxs)(V,{size:`medium`,showModal:r,handleCloseModal:()=>{n(``),i(!1)},cancelLinkText:`Cancel`,buttonText:`Save message`,buttonColor:`blue`,handleButtonClick:()=>i(!1),children:[(0,q.jsx)(`h2`,{className:`modal-title`,children:`Add a summary of your changes`}),(0,q.jsx)(St,{bottom:!0,children:(0,q.jsx)(ct,{id:`custom_message_input`,name:`custom_message_input`,showPreview:!1,placeholder:`${e} updated their policy`,value:t,onChange:e=>n(e.target.value),maxLength:constants.notification.custom_message_character_limit})}),(0,q.jsxs)(lt,{children:[constants.notification.custom_message_character_limit-t.length,` `,`characters remaining`]})]})]})};Tr.propTypes={organizationName:K.default.string.isRequired,customMessage:K.default.string.isRequired,setCustomMessage:K.default.func.isRequired},F();var Er=f`
  mutation AddAssetsToStructuredScopes(
    $organizationId: ID!
    $assetIds: [Int!]!
    $teamIds: [Int!]!
    $eligibleForSubmission: Boolean
    $eligibleForBounty: Boolean
    $notifySubscribersOnChanges: Boolean
    $customMessage: String
    $instruction: String
    $fromRecommendation: Boolean
  ) {
    addAssetsToStructuredScopes(
      input: {
        organization_id: $organizationId
        asset_ids: $assetIds
        team_ids: $teamIds
        eligible_for_submission: $eligibleForSubmission
        eligible_for_bounty: $eligibleForBounty
        notify_subscribers_on_changes: $notifySubscribersOnChanges
        custom_message: $customMessage
        instruction: $instruction
        from_recommendation: $fromRecommendation
      }
    ) {
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
`,Dr=e(je()),Or=e(O());F();var kr=({organization:e,showModal:t,setShowModal:n})=>{let{store:r,dispatch:i}=(0,J.useContext)($),a=r.checkedAssets.length>0?(0,Or.default)(r.checkedAssets,Dr.default):[(0,Dr.default)(r.rowMenuAssetId)],[o,s]=(0,J.useState)(``),[c,{loading:l}]=z(Er,{refetchQueries:[`AssetsSearchQuery`,`AssetGroupAssetsQuery`,`AssetsSearchCountsQuery`,`AssetGroupCountsQuery`],onCompleted:({addAssetsToStructuredScopes:{was_successful:e,errors:t}})=>{if(!e){L(`error`,t.edges.map(e=>e.node.message).join(` `));return}G(),i({type:X.CLEAR_CHECKED_ASSETS}),i({type:X.SET_ROW_MENU_ASSET_ID,value:null}),n(!1),s(``)},onError:W});return(0,q.jsx)(V,{shouldCloseOnEsc:!0,showModal:t,size:`extra-large`,title:`Add to scope`,handleCloseModal:()=>{n(!1),i({type:X.SET_ROW_MENU_ASSET_ID,value:null})},children:(0,q.jsxs)(wr,{model:{assetIds:a,eligibleForSubmission:!0,eligibleForBounty:!0,notifySubscribersOnChanges:!0},onSubmit:({teamIds:t,eligibleForSubmission:n,eligibleForBounty:r,notifySubscribersOnChanges:i})=>c({variables:{organizationId:e.id,assetIds:a,teamIds:(0,Or.default)(t,Dr.default),eligibleForSubmission:n===`true`,eligibleForBounty:r===`true`&&n===`true`,notifySubscribersOnChanges:i,customMessage:o}}),organization:e,children:[(0,q.jsxs)(`p`,{className:`daisy-text`,children:[`You have selected`,` `,(0,q.jsxs)(`span`,{className:`daisy-text--bold daisy-text--blue`,children:[a.length,` Assets`]}),` `,`to be added to scope`]}),(0,q.jsx)(`div`,{children:(0,q.jsxs)(H,{justifyContent:`flex-end`,className:`w-full mb-spacing-12`,style:{width:`100%`},children:[(0,q.jsx)(H,{flexShrink:10,flexBasis:`33.33%`,children:(0,q.jsx)(R,{name:`teamIds`,placeholder:`Select programs`,wrapperClassName:`asset-dropdown-wrapper asset-teams`})}),(0,q.jsx)(H,{flexBasis:`33.33%`,children:(0,q.jsx)(R,{name:`eligibleForSubmission`,placeholder:`Select asset scope`,wrapperClassName:`asset-dropdown-wrapper asset-eligible-for-submission`})}),(0,q.jsx)(H,{flexBasis:`33.33%`,children:(0,q.jsx)(R,{name:`eligibleForBounty`,placeholder:`Select bounty eligibility`,wrapperClassName:`asset-dropdown-wrapper asset-eligible-for-bounty w-full`,children:(0,q.jsx)(lt,{children:`Only applicable to BBP and Challenges`})})})]})}),(0,q.jsx)(xt,{}),(0,q.jsx)(Ue,{}),(0,q.jsxs)(H,{justifyContent:`space-between`,children:[(0,q.jsx)(H,{alignItems:`baseline`,children:(0,q.jsx)(St,{top:!0,size:`medium`,children:(0,q.jsxs)(H,{style:{gap:8},children:[(0,q.jsx)(R,{name:`notifySubscribersOnChanges`,wrapperClassName:`asset-notify-subscribers-on-changes`}),(0,q.jsx)(Tr,{organizationName:e.name,customMessage:o,setCustomMessage:s})]})})}),(0,q.jsxs)(H,{alignItems:`baseline`,children:[(0,q.jsx)(_t,{type:`reset`,variation:`secondary`,color:`black`,onClick:()=>{n(!1),s(``)},className:`margin-16--right`,children:`Cancel`}),(0,q.jsx)(_t,{type:`submit`,variation:`primary`,color:`blue`,disabled:l,onClick:()=>{$e.track(`add scope flow submitted`)},children:`Add scope`})]})]})]})})};kr.propTypes={organization:K.default.object.isRequired,showModal:K.default.bool.isRequired,setShowModal:K.default.func.isRequired},kr.fragments={organization:f`
    fragment AddScopeModalOrganizationFragment on Organization {
      id
      ...FormOrganizationAssetInventoryFragment
    }
    ${wr.fragments.organization}
  `},F();var Ar=f`
  mutation AddAssetsToStructuredScopesModal(
    $organizationId: ID!
    $assetIds: [Int!]!
    $teamIds: [Int!]!
    $eligibleForSubmission: Boolean
    $eligibleForBounty: Boolean
    $notifySubscribersOnChanges: Boolean
    $customMessage: String
  ) {
    addAssetsToStructuredScopes(
      input: {
        organization_id: $organizationId
        asset_ids: $assetIds
        team_ids: $teamIds
        eligible_for_submission: $eligibleForSubmission
        eligible_for_bounty: $eligibleForBounty
        notify_subscribers_on_changes: $notifySubscribersOnChanges
        custom_message: $customMessage
      }
    ) {
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
`,jr=({organization:e,showModal:t,setShowModal:n})=>{let{store:r,dispatch:i}=(0,J.useContext)($),a=r.checkedAssetObjects.filter(e=>e.coverage!==constants.assetInventory.coverageTypes.outOfScope).map(e=>parseInt(e.databaseId,10)),[o,s]=(0,J.useState)(``),[c,{loading:l}]=z(Ar,{refetchQueries:[`AssetsSearchQuery`,`AssetGroupAssetsQuery`,`AssetGroupSearchQuery`,`AssetGroupCountsQuery`,`AssetsSearchCountsQuery`,`AttackSurfaceAssetsQuery`],onCompleted:e=>{if(!e.addAssetsToStructuredScopes.was_successful)return W();G(),i({type:X.CLEAR_CHECKED_ASSETS}),i({type:X.SET_ROW_MENU_ASSET_ID,value:null}),n(!1),s(``)},onError:W});return(0,q.jsx)(V,{shouldCloseOnEsc:!0,showModal:t,size:`extra-large`,title:`Set out of scope`,handleCloseModal:()=>{n(!1),i({type:X.SET_ROW_MENU_ASSET_ID,value:null})},children:(0,q.jsxs)(wr,{model:{assetIds:a,notifySubscribersOnChanges:!0},onSubmit:({teamIds:t,notifySubscribersOnChanges:n})=>c({variables:{organizationId:e.id,assetIds:a,teamIds:t.map(e=>parseInt(e,10)),eligibleForSubmission:!1,eligibleForBounty:!1,notifySubscribersOnChanges:n,customMessage:o}}),organization:e,children:[(0,q.jsx)(`div`,{children:(0,q.jsx)(H,{justifyContent:`flex-end`,className:`w-full border-b border-solid border-neutral-700 dark:border-neutral-50 mb-spacing-12`,style:{width:`100%`},children:(0,q.jsx)(H,{flexShrink:10,flexBasis:`100%`,children:(0,q.jsx)(R,{name:`teamIds`,placeholder:`Select programs`,wrapperClassName:`asset-dropdown-wrapper asset-teams`})})})}),(0,q.jsxs)(`p`,{className:`daisy-text pb-spacing-40`,children:[`You are managing the scope of`,` `,(0,q.jsxs)(`span`,{className:`daisy-text--bold daisy-text--red`,children:[a.length,` Assets`]}),` `]}),(0,q.jsx)(xt,{}),(0,q.jsx)(Ue,{}),(0,q.jsxs)(H,{justifyContent:`space-between`,children:[(0,q.jsx)(H,{alignItems:`baseline`,children:(0,q.jsx)(St,{top:!0,size:`medium`,children:(0,q.jsxs)(H,{style:{gap:8},children:[(0,q.jsx)(R,{name:`notifySubscribersOnChanges`,wrapperClassName:`asset-notify-subscribers-on-changes`}),(0,q.jsx)(Tr,{organizationName:e.name,customMessage:o,setCustomMessage:s})]})})}),(0,q.jsxs)(H,{alignItems:`baseline`,children:[(0,q.jsx)(_t,{type:`reset`,variation:`secondary`,color:`black`,onClick:()=>{n(!1),s(``)},className:`margin-16--right`,children:`Cancel`}),(0,q.jsx)(_t,{type:`submit`,variation:`primary`,color:`blue`,disabled:l,children:`Update scope`})]})]})]})})};jr.propTypes={organization:K.default.object.isRequired,showModal:K.default.bool.isRequired,setShowModal:K.default.func.isRequired},jr.fragments={organization:f`
    fragment SetOutOfScopeModalOrganizationFragment on Organization {
      id
      ...FormOrganizationAssetInventoryFragment
    }
    ${wr.fragments.organization}
  `},F();var Mr=f`
  mutation BulkUnarchiveAssets($assetIds: [Int!]!) {
    bulkUnarchiveAssets(input: { asset_ids: $assetIds }) {
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
    }
  }
`,Nr=f`
  mutation ArchiveMultipleAssets($assetIds: [Int!]!) {
    archiveMultipleAssets(input: { asset_ids: $assetIds }) {
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
    }
  }
`,Pr=({showModal:e,setShowModal:t})=>{let{store:n,dispatch:r}=(0,J.useContext)($),i=(n.checkedAssets.length>0?(0,Or.default)(n.checkedAssets,Dr.default):[n.rowMenuAssetId]).filter(e=>e),[a,{loading:o}]=z(Nr,{refetchQueries:[`AssetsSearchQuery`,`AssetsSearchCountsQuery`,`AssetGroupAssetsQuery`,`AssetGroupSearchQuery`,`AssetGroupCountsQuery`,`AttackSurfaceAssetsQuery`],onCompleted:e=>{if(!e.archiveMultipleAssets.was_successful)return W();$e.track(`assets archived`,{label:`The amount of ${i.length} assets was archived`}),G(),r({type:X.CLEAR_CHECKED_ASSETS}),r({type:X.SET_ROW_MENU_ASSET_ID,value:null}),t(!1)},onError:W});return(0,q.jsx)(V,{shouldCloseOnEsc:!0,showModal:e,size:`large`,title:`Archiving assets`,handleCloseModal:()=>{t(!1),r({type:X.SET_ROW_MENU_ASSET_ID,value:null})},children:(0,q.jsxs)(`div`,{className:`flex flex-col`,children:[(0,q.jsx)(`span`,{className:`text-md text-muted mt-spacing-24`,children:`Archiving assets will result in:`}),(0,q.jsx)(x,{top:`16`,children:(0,q.jsxs)(`ul`,{className:`list-none`,children:[(0,q.jsxs)(`li`,{className:`mb-sm`,children:[(0,q.jsx)(`span`,{className:`w-[24px] h-[24px] text-center align-middle bg-blue-900 mr-spacing-16 rounded-full`,children:(0,q.jsx)(P,{src:A,size:`sm`})}),`Removing the asset from your organisations asset inventory`]}),(0,q.jsxs)(`li`,{children:[(0,q.jsx)(`span`,{className:`w-[24px] h-[24px] text-center align-middle bg-yellow-900 mr-spacing-16 rounded-full`,children:(0,q.jsx)(P,{src:jt,size:`sm`})}),`Affect related enrichment and group metrics`]})]})}),(0,q.jsxs)(x,{top:`40`,children:[`You have selected`,` `,(0,q.jsxs)(`span`,{className:`daisy-text--bold daisy-text--red`,children:[i.length,` assets`]}),` `,`to be archived`]}),(0,q.jsx)(`div`,{className:`flex flex-col`,children:(0,q.jsx)(`div`,{className:`flex justify-end`,children:(0,q.jsx)(T,{type:`submit`,variation:`danger`,onClick:()=>a({variables:{assetIds:i}}),disabled:o,children:`Confirm`})})})]})})};Pr.propTypes={showModal:K.default.bool.isRequired,setShowModal:K.default.func.isRequired,rowMenuAssetId:K.default.number},F();var Fr=({mode:e,model:t,onSubmit:n,children:r})=>{let i=(0,J.useRef)(),{teams:a}=(0,J.useContext)(Sr),o=()=>({teamIds:{type:Array,required:!0,defaultValue:[],label:`Select programs`,uniforms:{id:`asset-team-ids`,component:He,options:a.map(e=>({value:e.databaseId,label:e.name}))}},"teamIds.$":{type:String}});return(0,q.jsx)(it,{schema:new p(new Y.default((()=>{switch(e){case`new`:return{...o()};default:return{}}})())),model:t,onSubmit:n,showInlineError:!0,placeholder:!0,ref:i,children:r})};Fr.propTypes={mode:K.default.oneOf([`new`]).isRequired,model:K.default.object.isRequired,onSubmit:K.default.func.isRequired,children:K.default.node.isRequired},Fr.fragments={team:f`
    fragment RemoveScopeFormWrapperTeamFragment on Team {
      id
      databaseId: _id
      name
    }
  `},F();var Ir=({model:e,onSubmit:t,organization:n,children:r})=>{let{scope_management_teams:{nodes:i},i_can_manage_pentest_scope:a,i_can_manage_all_programs_scope:o}=n,s=a?i:i.filter(e=>e.type!==`Engagements::Assessment`);s=o?s:s.filter(e=>e.i_can_manage_program);let c=(0,J.useMemo)(()=>({teams:s}),[s]);return(0,q.jsx)(Sr.Provider,{value:c,children:(0,q.jsx)(Fr,{mode:`new`,model:e,onSubmit:t,children:r})})};Ir.propTypes={model:K.default.object.isRequired,onSubmit:K.default.func.isRequired,organization:K.default.object.isRequired,children:K.default.arrayOf(K.default.node.isRequired).isRequired},Ir.fragments={organization:f`
    fragment ScopeRemoveFormOrganizationFragment on Organization {
      id
      i_can_manage_pentest_scope
      i_can_manage_all_programs_scope
      scope_management_teams {
        nodes {
          id
          i_can_manage_program
          type
          ...RemoveScopeFormWrapperTeamFragment
        }
      }
    }
    ${Fr.fragments.team}
  `},F();var Lr=f`
  mutation RemoveAssetsFromStructuredScopes(
    $organizationId: ID!
    $assetIds: [Int!]!
    $teamIds: [Int!]!
  ) {
    removeAssetsFromStructuredScopes(
      input: {
        organization_id: $organizationId
        asset_ids: $assetIds
        team_ids: $teamIds
      }
    ) {
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
`,Rr=({organization:e,showModal:t,setShowModal:n})=>{let{store:r,dispatch:i}=(0,J.useContext)($),a=r.checkedAssetObjects.filter(e=>e.coverage===constants.assetInventory.coverageTypes.inScope||e.coverage===constants.assetInventory.coverageTypes.outOfScope),o=a.length>0?a.map(e=>Number(e.databaseId)):[r.rowMenuAssetId],[s,{loading:c}]=z(Lr,{refetchQueries:[`AssetsSearchQuery`,`AssetGroupAssetsQuery`,`AssetsSearchCountsQuery`,`AssetGroupCountsQuery`,`AttackSurfaceAssetsQuery`],onCompleted:e=>{if(!e.removeAssetsFromStructuredScopes.was_successful)return W();G(),i({type:X.CLEAR_CHECKED_ASSETS}),i({type:X.SET_ROW_MENU_ASSET_ID,value:null}),n(!1)},onError:W});return(0,q.jsx)(V,{shouldCloseOnEsc:!0,showModal:t,size:`extra-large`,title:`Remove from scope`,handleCloseModal:()=>{n(!1),i({type:X.SET_ROW_MENU_ASSET_ID,value:null})},children:(0,q.jsxs)(Ir,{model:{assetIds:o},onSubmit:({teamIds:t,notifySubscribersOnChanges:n})=>{s({variables:{organizationId:e.id,assetIds:o,teamIds:(0,Or.default)(t,Dr.default)}})},organization:e,children:[(0,q.jsx)(`div`,{children:(0,q.jsx)(H,{justifyContent:`space-between`,className:`w-full border-b border-solid border-neutral-700 dark:border-neutral-50 mb-spacing-12`,style:{width:`100%`},children:(0,q.jsx)(R,{name:`teamIds`,placeholder:`Select programs`,wrapperClassName:`asset-dropdown-wrapper asset-teams`})})}),(0,q.jsxs)(`p`,{className:`daisy-text pb-spacing-40`,children:[`You have selected`,` `,(0,q.jsxs)(`span`,{className:`daisy-text--bold daisy-text--red`,children:[o.length,` Assets`]}),` `,`to be removed from scope`]}),(0,q.jsx)(xt,{}),(0,q.jsx)(Ue,{}),(0,q.jsx)(H,{justifyContent:`flex-end`,children:(0,q.jsxs)(H,{alignItems:`baseline`,children:[(0,q.jsx)(_t,{type:`reset`,variation:`secondary`,color:`black`,onClick:()=>n(!1),className:`margin-16--right`,children:`Cancel`}),(0,q.jsx)(_t,{type:`submit`,variation:`primary`,color:`blue`,disabled:c,children:`Remove selected assets`})]})})]})})};Rr.propTypes={organization:K.default.object.isRequired,showModal:K.default.bool.isRequired,setShowModal:K.default.func.isRequired},Rr.fragments={organization:f`
    fragment RemoveScopeModalOrganizationFragment on Organization {
      id
      ...ScopeRemoveFormOrganizationFragment
    }
    ${Ir.fragments.organization}
  `},F();var{ASSET_TAG_REWARD_CATEGORIES:zr}=window.constants.featureToggles,Br=({organization:e,closeModal:n,onSuccess:r,showModal:i,setShowModal:a})=>{let{enabled:o}=B(zr,e?.handle),s=f`
    mutation CreateAsmTagCategoryMutation(
      $name: String!
      $organizationId: ID!
      $uniqueTagPerAsset: Boolean
      $rewardsEligible: Boolean
    ) {
      createAsmTagCategory(
        input: {
          asm_tag_category_name: $name
          organization_id: $organizationId
          unique_tag_per_asset: $uniqueTagPerAsset
          rewards_eligible: $rewardsEligible
        }
      ) {
        was_successful
        errors {
          edges {
            node {
              type
              field
              message
            }
          }
        }
      }
    }
  `,[c,l]=(0,J.useState)(``),[u,d]=(0,J.useState)(!1),[p,m]=(0,J.useState)(!1),[h,g]=(0,J.useState)(null),_=e=>{m(e),e&&d(!0)},v=e=>{!e&&p||d(e)},y=()=>{l(``),d(!1),m(!1),g(null),a(!1)},[b,{loading:x}]=z(s,{onCompleted:e=>{if(e.createAsmTagCategory.was_successful)L(`notice`,`Tag category successfully created`),r?.(),n(),y();else{let t=e.createAsmTagCategory.errors?.edges||[];if(t.length>0){let e=t.map(e=>e.node.message).join(`, `);g(e)}else W()}},onError:e=>{g(e.message)}});return(0,q.jsx)(Ae,{open:i,title:`Create a tag category`,size:`large`,onClose:()=>{y(),n()},confirmationButtonProps:{onClick:()=>{if(g(null),!c.trim()){g(`Category name is required`);return}b({variables:{organizationId:e.id,name:c.trim(),uniqueTagPerAsset:u,...o&&{rewardsEligible:p}}})},loading:x,disabled:!c.trim()||x,children:`Create tag category`,testId:`create-tag-category-button`},children:(0,q.jsxs)(`div`,{className:`flex flex-col gap-sm`,children:[(0,q.jsxs)(`div`,{className:`flex items-center gap-1`,children:[(0,q.jsx)(t,{text:`Category name`,htmlFor:`custom-tag-category-name`}),(0,q.jsx)(`span`,{className:`text-red-600`,children:`*`})]}),(0,q.jsx)(ue,{id:`custom-tag-category-name`,value:c,onChange:e=>l(e.target.value),required:!0,maxLength:255,className:`custom-tag-category-name`,testId:`custom-tag-category-name-input`}),o&&(0,q.jsxs)(`div`,{className:`flex flex-row gap-2xs items-center`,children:[(0,q.jsx)(le,{checked:p,label:`Enable rewards for tags in this category`,onChange:e=>_(e.target.checked),testId:`rewards-eligible-checkbox`}),(0,q.jsx)(N,{text:`When enabled, tags in this category can be associated with bounty amounts. This helps streamline reward workflows by connecting specific tags to predetermined payment values.`,children:(0,q.jsx)(P,{src:`data:image/svg+xml,%3csvg%20xmlns='http://www.w3.org/2000/svg'%20width='24'%20height='24'%20viewBox='0%200%2024%2024'%3e%3cpath%20d='M11%207h2v2h-2zm0%204h2v6h-2zm1-9C6.48%202%202%206.48%202%2012s4.48%2010%2010%2010s10-4.48%2010-10S17.52%202%2012%202zm0%2018c-4.41%200-8-3.59-8-8s3.59-8%208-8s8%203.59%208%208s-3.59%208-8%208z'/%3e%3c/svg%3e`,accessibilityLabel:`Information about reward categories`})})]}),(0,q.jsx)(le,{checked:u,label:`Assets can only have one tag from this category`,onChange:e=>v(e.target.checked),disabled:p,testId:`unique-tag-per-asset-checkbox`}),h&&(0,q.jsx)(`div`,{className:`text-red-600 text-sm mt-2`,children:h})]})})};Br.propTypes={closeModal:K.default.func.isRequired,onSuccess:K.default.func,organization:K.default.object.isRequired,showModal:K.default.bool.isRequired,setShowModal:K.default.func.isRequired};var Vr=({model:e,onSubmit:t,children:n})=>{let r=(0,J.useRef)();return(0,q.jsx)(it,{schema:new p(new Y.default({name:{type:String,label:`Tag name`,required:!0,uniforms:{id:`custom-tag-name`}}})),model:e,placeholder:!0,onSubmit:t,showInlineError:!0,ref:r,children:n})};Vr.propTypes={model:K.default.object.isRequired,onSubmit:K.default.func.isRequired,children:K.default.arrayOf(K.default.node).isRequired},F();var{ASSET_TAG_REWARD_CATEGORIES:Hr}=window.constants.featureToggles,Ur=({organization:e,closeModal:n,onSuccess:r,showModal:i,setShowModal:a})=>{let o=f`
    mutation CreateAsmTagMutation($name: String!, $asmTagCategoryId: ID!) {
      createAsmTag(
        input: { name: $name, asm_tag_category_id: $asmTagCategoryId }
      ) {
        was_successful
        errors {
          edges {
            node {
              type
              field
              message
            }
          }
        }
      }
    }
  `,{data:s,loading:c}=U(f`
    query TagCategoriesQuery($handle: String!) {
      organizations(first: 1, where: { handle: { _eq: $handle } }) {
        nodes {
          id
          asm_tag_categories {
            nodes {
              id
              name
              rewards_eligible
              unique_tag_per_asset
            }
          }
        }
      }
    }
  `,{variables:{handle:e?.handle},fetchPolicy:`network-only`}),{enabled:l}=B(Hr,e?.handle),[u,d]=(0,J.useState)(null),[p,m]=(0,J.useState)(null),h={name:``},g=()=>{d(null),m(null),a(!1)},[_,{loading:v}]=z(o,{onCompleted:e=>{if(e.createAsmTag.was_successful)L(`notice`,`Tag was successfully created`),r?.(),n(),g();else{let t=e.createAsmTag.errors?.edges||[];t.length>0?m(t.map(e=>e.node.message).join(`, `)):W()}},onError:e=>{m(e.message)}}),y=e=>{if(u)return m(null),_({variables:{name:e.name,asmTagCategoryId:u}})},b=null;if(c)b=(0,q.jsx)(`div`,{children:(0,q.jsx)(H,{className:`justify-between`,children:(0,q.jsx)(M,{lines:1})})});else{let e=s?.organizations?.nodes[0].asm_tag_categories.nodes,n=gr(e,l),r=n.find(e=>e.value===u);b=(0,q.jsxs)(`div`,{children:[`Create a custom tag that will be added to the selected category`,(0,q.jsx)(x,{top:`8`,children:(0,q.jsxs)(Vr,{model:h,onSubmit:y,children:[(0,q.jsxs)(`div`,{className:`flex gap-sm`,children:[(0,q.jsxs)(`div`,{className:`shrink basis-1/2 gap-2xs flex flex-col`,children:[(0,q.jsx)(t,{text:`Tag category`,required:!0}),(0,q.jsx)(De,{selectedOption:r,onChange:e=>d(e?.value),options:n,testId:`spec-asm-tag-category`})]}),(0,q.jsx)(R,{name:`name`,className:`custom-tag-name`,wrapperClassName:`shrink basis-1/2`})]}),p&&(0,q.jsx)(`div`,{className:`text-red-600 text-sm mt-2`,children:p}),(0,q.jsx)(xt,{}),(0,q.jsx)(Ue,{}),(0,q.jsxs)(`div`,{className:`flex justify-end mt-spacing-32`,children:[(0,q.jsx)(x,{right:`16`,children:(0,q.jsx)(T,{type:`reset`,variation:`tertiary`,onClick:g,children:`Cancel`})}),(0,q.jsx)(T,{type:`submit`,variation:`primary`,disabled:v||!u,children:`Create tag`})]})]})})]})}return(0,q.jsx)(V,{shouldCloseOnEsc:!0,shouldCloseOnOverlayClick:!1,showModal:i,title:`Create a custom tag`,handleCloseModal:()=>a(!1),children:(0,q.jsx)(w,{children:b})})};Ur.propTypes={closeModal:K.default.func.isRequired,onSuccess:K.default.func,organization:K.default.object.isRequired,showModal:K.default.bool.isRequired,setShowModal:K.default.func.isRequired},F();var Wr=f`
  mutation DeleteAsmTagMutation($tagId: ID!) {
    deleteAsmTag(input: { tag_id: $tagId }) {
      was_successful
    }
  }
`,Gr=({showModal:e,tagId:t,onClose:n,tagName:r,onComplete:i})=>{let[a,{loading:o}]=z(Wr,{variables:{tagId:t},onError(){W()},onCompleted({deleteAsmTag:{was_successful:e}}){e?(L(`notice`,`The tag was deleted successfully.`),i?.()):W()}});return(0,q.jsx)(V,{showModal:e,shouldCloseOnOverlayClick:!0,shouldCloseOnEsc:!0,handleCloseModal:n,buttonText:`Confirm`,handleButtonClick:a,cancelLinkText:`Cancel`,buttonDisabled:o,cancelLinkDisabled:o,buttonColor:`blue`,title:(0,q.jsxs)(`span`,{className:`leading-normal`,children:[`Are you sure you want to delete the custom tag '`,(0,q.jsx)(`span`,{className:`text-blue-300`,children:r}),`'?`]}),children:(0,q.jsx)(w,{children:`The custom tag will be deleted and be removed from all connected assets.`})})};Gr.propTypes={tagId:K.default.string.isRequired,tagName:K.default.string.isRequired,showModal:K.default.bool.isRequired,onClose:K.default.func.isRequired,onComplete:K.default.func.isRequired},F();var Kr=f`
  mutation DeleteAsmTagCategoryMutation($asmTagCategoryId: ID!) {
    deleteAsmTagCategory(input: { asm_tag_category_id: $asmTagCategoryId }) {
      was_successful
      errors {
        edges {
          node {
            message
          }
        }
      }
    }
  }
`,qr=({showModal:e,categoryId:t,categoryName:n,onClose:r,onComplete:i})=>{let[a,{loading:o}]=z(Kr,{variables:{asmTagCategoryId:t},update(e){e.evict({id:e.identify({__typename:`AsmTagCategory`,id:t})}),e.gc()},onError(){W()},onCompleted({deleteAsmTagCategory:{was_successful:e}}){e?(L(`notice`,`The tag category was deleted successfully.`),i?.()):W()}});return(0,q.jsx)(V,{showModal:e,shouldCloseOnOverlayClick:!0,shouldCloseOnEsc:!0,handleCloseModal:r,buttonText:`Delete tag category`,handleButtonClick:a,cancelLinkText:`Cancel`,buttonDisabled:o,cancelLinkDisabled:o,buttonColor:`danger`,title:`Delete tag category`,children:(0,q.jsxs)(`div`,{className:`flex flex-col gap-md`,children:[(0,q.jsxs)(w,{children:[`Deleting this tag category will permanently remove`,` `,(0,q.jsx)(`strong`,{children:n}),` from your asset inventory. The asset tags within the category will be removed from any assets they are currently assigned to. This may impact:`]}),(0,q.jsxs)(`ul`,{className:`list-disc pl-lg`,children:[(0,q.jsx)(`li`,{children:`Asset Spend categories`}),(0,q.jsx)(`li`,{children:`Reward group assignments`}),(0,q.jsx)(`li`,{children:`Reporting and filtering across your program`})]}),(0,q.jsx)(w,{children:`Assets will not be deleted, but they may lose scope or reward associations if those were defined using this category.`}),(0,q.jsx)(w,{children:(0,q.jsx)(`strong`,{children:`This action cannot be undone. Please confirm that you want to permanently delete this tag category.`})})]})})};qr.propTypes={categoryId:K.default.string.isRequired,categoryName:K.default.string.isRequired,showModal:K.default.bool.isRequired,onClose:K.default.func.isRequired,onComplete:K.default.func.isRequired},F();var{ASSET_TAG_REWARD_CATEGORIES:Jr}=window.constants.featureToggles,Yr=f`
  mutation EditAsmTagMutation(
    $asmTagId: ID!
    $asmTagCategoryId: ID
    $name: String
  ) {
    editAsmTag(
      input: {
        asm_tag_id: $asmTagId
        asm_tag_category_id: $asmTagCategoryId
        name: $name
      }
    ) {
      was_successful
      asm_tag {
        id
        name
        asm_tag_category {
          id
          name
        }
      }
      errors {
        edges {
          node {
            type
            field
            message
          }
        }
      }
    }
  }
`,Xr=f`
  query EditTagModalQuery($handle: String!) {
    organizations(first: 1, where: { handle: { _eq: $handle } }) {
      nodes {
        id
        asm_tag_categories {
          nodes {
            id
            name
            rewards_eligible
            unique_tag_per_asset
          }
        }
      }
    }
  }
`,Zr=({showModal:e,tagId:n,onClose:r,tagName:i,categoryId:o,organizationHandle:s,onComplete:c})=>{let[l,u]=(0,J.useState)(i),[d,f]=(0,J.useState)(o),[p,m]=(0,J.useState)(null),{enabled:h}=B(Jr,s),{data:g,loading:_}=U(Xr,{variables:{handle:s},fetchPolicy:`network-only`,skip:!e}),[v,{loading:y}]=z(Yr,{onError(){W()},onCompleted({editAsmTag:e}){if(e.was_successful)L(`notice`,`The tag was edited successfully.`),c?.(),r();else{let t=e.errors?.edges?.[0]?.node?.message;t?m(t):W()}}}),b=()=>!l||l.trim()===``?(m(`Tag name is required`),!1):d?!0:(m(`Tag category is required`),!1),x=()=>{b()&&v({variables:{asmTagId:n,asmTagCategoryId:d,name:l}})},S=i.length>25?`${i.substring(0,25)}...`:i,C=null;if(_)C=(0,q.jsxs)(`div`,{className:`flex justify-between gap-sm`,children:[(0,q.jsx)(M,{}),(0,q.jsx)(M,{})]});else{let e=g?.organizations?.nodes[0].asm_tag_categories.nodes,n=gr(e,h),r=n.find(e=>e.value===d);C=(0,q.jsxs)(`div`,{className:`flex flex-col gap-sm`,children:[(0,q.jsxs)(`div`,{className:`flex gap-sm`,children:[(0,q.jsxs)(`div`,{className:`flex-1 gap-2xs flex flex-col`,children:[(0,q.jsx)(t,{text:`Tag category`,required:!0}),(0,q.jsx)(De,{selectedOption:r,onChange:e=>f(e?.value),options:n,testId:`spec-asm-tag-category`})]}),(0,q.jsx)(`div`,{className:`flex-1`,children:(0,q.jsx)(a,{labelText:`Tag name`,value:l,onChange:e=>u(e.target.value),required:!0,testId:`custom-tag-name`})})]}),p&&(0,q.jsx)(`div`,{className:`text-red-600 text-sm`,children:p})]})}return(0,q.jsx)(Ae,{open:e,onClose:r,title:`Edit '${S}'`,confirmationButtonProps:{children:`Confirm`,disabled:y||_,onClick:x},children:C})};Zr.propTypes={tagId:K.default.string.isRequired,tagName:K.default.string.isRequired,categoryId:K.default.string.isRequired,organizationHandle:K.default.string.isRequired,showModal:K.default.bool.isRequired,onClose:K.default.func.isRequired,onComplete:K.default.func.isRequired},F();var{ASSET_TAG_REWARD_CATEGORIES:Qr}=window.constants.featureToggles,$r=({tagCategory:e,organization:n,closeModal:r,onSuccess:i,showModal:a,setShowModal:o})=>{let{enabled:s}=B(Qr,n?.handle),c=f`
    mutation UpdateAsmTagCategoryMutation(
      $id: ID!
      $name: String
      $uniqueTagPerAsset: Boolean
      $rewardsEligible: Boolean
    ) {
      updateAsmTagCategory(
        input: {
          asm_tag_category_id: $id
          asm_tag_category_name: $name
          unique_tag_per_asset: $uniqueTagPerAsset
          rewards_eligible: $rewardsEligible
        }
      ) {
        was_successful
        asm_tag_category {
          id
          name
          unique_tag_per_asset
          rewards_eligible
        }
        errors {
          edges {
            node {
              type
              field
              message
            }
          }
        }
      }
    }
  `,[l,u]=(0,J.useState)(``),[d,p]=(0,J.useState)(!1),[m,h]=(0,J.useState)(!1),[g,_]=(0,J.useState)(null),v=(0,J.useRef)(!1),y=e=>{h(e),e&&p(!0)},b=e=>{!e&&m||p(e)};(0,J.useEffect)(()=>{a&&e&&!v.current&&(u(e.name||``),p(e.unique_tag_per_asset||!1),h(e.rewards_eligible||!1),_(null),v.current=!0),a||(v.current=!1)},[a,e]);let x=()=>{u(``),p(!1),h(!1),_(null),o(!1)},[S,{loading:C}]=z(c,{onCompleted:e=>{if(e.updateAsmTagCategory.was_successful)L(`notice`,`Tag category successfully updated`),i?.(),r(),x();else{let t=e.updateAsmTagCategory.errors?.edges||[];if(t.length>0){let e=t.map(e=>e.node.message).join(`, `);_(e)}else W()}},onError:e=>{_(e.message)}});return(0,q.jsx)(Ae,{open:a,title:`Edit tag category`,size:`large`,onClose:()=>{x(),r()},confirmationButtonProps:{onClick:()=>{if(_(null),!l.trim()){_(`Category name is required`);return}S({variables:{id:e.id,name:l.trim(),uniqueTagPerAsset:d,...s&&{rewardsEligible:m}}})},loading:C,disabled:!l.trim()||C,children:`Update tag category`,testId:`update-tag-category-button`},children:(0,q.jsxs)(`div`,{className:`flex flex-col gap-sm`,children:[(0,q.jsxs)(`div`,{className:`flex items-center gap-1`,children:[(0,q.jsx)(t,{text:`Category name`,htmlFor:`edit-custom-tag-category-name`}),(0,q.jsx)(`span`,{className:`text-red-600`,children:`*`})]}),(0,q.jsx)(ue,{id:`edit-custom-tag-category-name`,value:l,onChange:e=>u(e.target.value),required:!0,maxLength:255,className:`edit-custom-tag-category-name`,testId:`edit-custom-tag-category-name-input`}),s&&(0,q.jsxs)(`div`,{className:`flex flex-row gap-2xs items-center`,children:[(0,q.jsx)(le,{checked:m,label:`Enable rewards for tags in this category`,onChange:e=>y(e.target.checked),testId:`edit-rewards-eligible-checkbox`}),(0,q.jsx)(N,{text:`When enabled, tags in this category can be associated with bounty amounts. This helps streamline reward workflows by connecting specific tags to predetermined payment values.`,children:(0,q.jsx)(P,{src:`data:image/svg+xml,%3csvg%20xmlns='http://www.w3.org/2000/svg'%20width='24'%20height='24'%20viewBox='0%200%2024%2024'%3e%3cpath%20d='M11%207h2v2h-2zm0%204h2v6h-2zm1-9C6.48%202%202%206.48%202%2012s4.48%2010%2010%2010s10-4.48%2010-10S17.52%202%2012%202zm0%2018c-4.41%200-8-3.59-8-8s3.59-8%208-8s8%203.59%208%208s-3.59%208-8%208z'/%3e%3c/svg%3e`,accessibilityLabel:`Information about reward categories`})})]}),(0,q.jsx)(le,{checked:d,label:`Assets can only have one tag from this category`,onChange:e=>b(e.target.checked),disabled:m,testId:`edit-unique-tag-per-asset-checkbox`}),g&&(0,q.jsx)(`div`,{className:`text-red-600 text-sm mt-2`,children:g})]})})};$r.propTypes={tagCategory:K.default.object,closeModal:K.default.func.isRequired,onSuccess:K.default.func,organization:K.default.object.isRequired,showModal:K.default.bool.isRequired,setShowModal:K.default.func.isRequired};var ei=25,ti=({setCurrentPage:e,currentPage:t,totalCount:n,loading:r,pageSize:i})=>(0,q.jsx)(j,{disabled:r,alignment:`right`,itemsPerPage:i,currentPage:t,onClickPrevious:()=>{e(t-1)},onClickNext:()=>{e(t+1)},totalItems:n,nextPageLabel:`Next page`,previousPageLabel:`Previous page`});ti.propTypes={currentPage:K.default.number.isRequired,setCurrentPage:K.default.func.isRequired,totalCount:K.default.number.isRequired,loading:K.default.bool,pageSize:K.default.number.isRequired};var ni=({paginationInfoObject:e,loading:t,pageSize:n=ei})=>{let{store:r,dispatch:i}=(0,J.useContext)($),{currentPage:a}=r;return(0,q.jsx)(ti,{currentPage:a,setCurrentPage:e=>{i({type:X.SET_CURRENT_PAGE,value:e})},loading:t,totalCount:e?.total_count||0,pageSize:n})};ni.propTypes={store:K.default.object.isRequired,dispatch:K.default.func.isRequired,paginationInfoObject:K.default.object,loading:K.default.bool,pageSize:K.default.number};var ri=({loadMore:e,paginationInfoObject:t,loading:n,isMax:r})=>{let i=t?.total_count,a=t?.current_count,o=a===i;return(0,q.jsxs)(`div`,{className:`text-sm text-muted`,children:[(0,q.jsxs)(`span`,{className:`mr-spacing-8`,children:[`Viewing `,o?`all `:`first `,n?`...`:a,r?` (max)`:``,` groups`]}),(0,q.jsx)(T,{size:`small`,variation:`ghost`,onClick:e,disabled:r||o||n,children:`Load more`})]})};ri.propTypes={paginationInfoObject:K.default.object,loading:K.default.bool.isRequired,loadMore:K.default.func.isRequired,isMax:K.default.bool.isRequired};var ii=({showModal:e,setShowModal:t})=>{let{store:n,dispatch:r}=(0,J.useContext)($),i=(n.checkedAssets.length>0?(0,Or.default)(n.checkedAssets,Dr.default):[n.rowMenuAssetId]).filter(e=>e),[a,{loading:o}]=z(Mr,{refetchQueries:[`AssetsSearchQuery`,`AssetsSearchCountsQuery`,`AssetGroupAssetsQuery`,`AssetGroupSearchQuery`,`AssetGroupCountsQuery`],onCompleted:e=>{if(!e.bulkUnarchiveAssets.was_successful)return W();G(),r({type:X.CLEAR_CHECKED_ASSETS}),r({type:X.SET_ROW_MENU_ASSET_ID,value:null}),t(!1)},onError:W});return(0,q.jsx)(V,{shouldCloseOnEsc:!0,showModal:e,size:`large`,title:`Unarchiving assets`,handleCloseModal:()=>{t(!1),r({type:X.SET_ROW_MENU_ASSET_ID,value:null})},children:(0,q.jsxs)(`div`,{className:`flex flex-col`,children:[(0,q.jsx)(`span`,{className:`text-md text-muted mt-spacing-24`,children:`Unarchiving assets will result in:`}),(0,q.jsx)(x,{top:`16`,children:(0,q.jsxs)(`ul`,{className:`list-none`,children:[(0,q.jsxs)(`li`,{className:`mb-sm`,children:[(0,q.jsx)(`span`,{className:`w-[24px] h-[24px] text-center align-middle bg-green-900 mr-spacing-16 rounded-full`,children:(0,q.jsx)(P,{src:Mt,size:`sm`})}),`Assets will appear in your organization's asset inventory`]}),(0,q.jsxs)(`li`,{children:[(0,q.jsx)(`span`,{className:`w-[24px] h-[24px] text-center align-middle bg-blue-900 mr-spacing-16 rounded-full`,children:(0,q.jsx)(P,{src:A,size:`sm`})}),`Assets will not be added back to scope of programs`]})]})}),(0,q.jsxs)(x,{top:`40`,children:[`You have selected`,` `,(0,q.jsxs)(`span`,{className:`daisy-text--bold daisy-text--red`,children:[i.length,` assets`]}),` `,`to be unarchived`]}),(0,q.jsx)(`div`,{className:`flex flex-col`,children:(0,q.jsx)(`div`,{className:`flex justify-end`,children:(0,q.jsx)(T,{type:`submit`,variation:`primary`,onClick:()=>a({variables:{assetIds:i}}),disabled:o,children:`Confirm`})})})]})})};ii.propTypes={showModal:K.default.bool.isRequired,setShowModal:K.default.func.isRequired,rowMenuAssetId:K.default.number},F();var{ASSET_SCANNER_BETA:ai}=window.constants.featureToggles,oi={columns:[`identifier`,`asset_type`,`ports`,`technologies`,`confidentiality_requirement`,`integrity_requirement`,`availability_requirement`,`description`,`reference`],rows:[{identifier:`hackerone.com`,asset_type:`Domain`,ports:`80,443`,technologies:`technology1,technology2,technology3`,confidentiality_requirement:`high`,integrity_requirement:`medium`,availability_requirement:`low`,description:`Asset1 description`,reference:`ref1`},{identifier:`192.168.1.1/32`,asset_type:`Cidr`,ports:`22,80,443`,technologies:`technology4,technology5,technology6`,confidentiality_requirement:`medium`,integrity_requirement:`low`,availability_requirement:`high`,description:`Asset2 description`,reference:`ref2`},{identifier:`com.hackerone.example`,asset_type:`IosAppStore`,ports:`443`,technologies:`technology1,technology2,technology3`,confidentiality_requirement:`low`,integrity_requirement:`high`,availability_requirement:`medium`,description:`Asset3 description`,reference:`ref3`},{identifier:`com.hackerone.example`,asset_type:`AndroidPlayStore`,ports:`8080/udp,8443/tcp`,technologies:`technology7,technology8,technology9`,confidentiality_requirement:`high`,integrity_requirement:`low`,availability_requirement:`medium`,description:`Asset4 description`,reference:`ref4`}]},si=e=>{let t=e?oi.columns:oi.columns.filter(e=>e!==`ports`);return[t.join(`;`),...oi.rows.map(e=>t.map(t=>e[t]||``).join(`;`))].join(`
`)},ci=f`
  mutation ImportAssetsCsv($organization_id: ID!, $file: Upload!) {
    importAssetsCsv(input: { organization_id: $organization_id, file: $file }) {
      was_successful
      errors {
        edges {
          node {
            id
            message
          }
        }
      }
      asset_import {
        id
        _id
        state
      }
    }
  }
`,li=({setSelectedFile:e})=>{let[t,n]=(0,J.useState)(null),{getRootProps:r,getInputProps:i}=c({onDrop:(0,J.useCallback)(t=>{let r=t[0]?t[0]:null;n(r),e(r)},[e]),accept:{"text/csv":[`.csv`]},maxFiles:1});return(0,q.jsx)(`div`,{children:(0,q.jsx)(`div`,{className:`border-dashed border-2 border-neutral-700 rounded-md p-md cursor-pointer`,children:(0,q.jsxs)(`div`,{...r({className:`assets-csv-dropzone`}),children:[(0,q.jsx)(`input`,{...i(),id:`spec-assets-import-csv-file-input`,className:`spec-assets-import-csv-file-input`}),t==null&&(0,q.jsx)(`p`,{children:`Drag and drop some files here, or click to select files`}),t!=null&&(0,q.jsxs)(`div`,{className:`p-sm rounded-md bg-neutral-900 flex items-center dark:bg-transparent dark:p-0`,children:[(0,q.jsx)(`div`,{className:`flex-1`,children:t.name}),(0,q.jsx)(`div`,{className:`text-neutral-300 dark:text-neutral-800`,children:Ot(t.size)}),(0,q.jsx)(`div`,{className:`ml-md text-neutral-300 cursor-pointer dark:text-neutral-800`,onClick:t=>{t.stopPropagation(),n(null),e(null)},children:(0,q.jsx)(`div`,{className:`mt-[-2px]`,children:(0,q.jsx)(P,{src:`data:image/svg+xml,%3csvg%20xmlns='http://www.w3.org/2000/svg'%20width='24'%20height='24'%20viewBox='0%200%2024%2024'%3e%3cpath%20d='M19%206.41L17.59%205L12%2010.59L6.41%205L5%206.41L10.59%2012L5%2017.59L6.41%2019L12%2013.41L17.59%2019L19%2017.59L13.41%2012L19%206.41z'/%3e%3c/svg%3e`,accessibilityLabel:`Remove file`})})})]})]})})})};li.propTypes={setSelectedFile:K.default.func.isRequired};var ui=({organizationId:e,organizationHandle:t,showModal:n,setShowModal:r,afterCreate:i,onFail:a})=>{let[o,s]=(0,J.useState)(null),[c,l]=(0,J.useState)(null),{enabled:u}=B(ai,t),[d,{loading:f}]=z(ci,{onCompleted:e=>{e.importAssetsCsv.was_successful?(G(),r(!1),i instanceof Function&&i(e.importAssetsCsv)):(l(e.importAssetsCsv.errors.edges[0].node.message),W(),a instanceof Function&&a(e))}}),p=()=>{d({variables:{organization_id:e,file:o}})};return(0,q.jsx)(V,{shouldCloseOnEsc:!0,size:`medium`,showModal:n,title:`Upload file`,handleCloseModal:()=>r(!1),children:(0,q.jsxs)(w,{children:[(0,q.jsx)(x,{top:`32`,children:(0,q.jsx)(`div`,{className:`p-md bg-blue-950 dark:bg-black`,children:(0,q.jsxs)(`ol`,{type:`1`,className:`ml-md list-decimal`,children:[(0,q.jsxs)(`li`,{children:[`Structure your data by downloading the`,` `,(0,q.jsx)(ot,{onClick:()=>{let e=si(u);if(window.navigator.msSaveOrOpenBlob){let t=new Blob([e]);window.navigator.msSaveOrOpenBlob(t,`hackerone-assets.csv`)}else{let t=`data:text/csv;charset=utf-8,${encodeURIComponent(e)}`,n=document.createElement(`a`);n.setAttribute(`href`,t),n.setAttribute(`download`,`hackerone-assets.csv`),document.body.appendChild(n),n.click()}},children:`hackerone-assets.csv`}),`.`]}),(0,q.jsx)(`li`,{children:`Upload your assets in a semicolon (;) separated CSV file when ready`})]})})}),(0,q.jsx)(x,{top:`32`,children:(0,q.jsx)(`div`,{children:(0,q.jsx)(li,{setSelectedFile:s})})}),c&&(0,q.jsx)(x,{top:`32`,children:(0,q.jsx)(`div`,{className:`p-md bg-danger-100`,children:(0,q.jsxs)(w,{variation:`body`,children:[(0,q.jsx)(x,{bottom:`8`,children:(0,q.jsx)(`strong`,{children:`Import failed`})}),(0,q.jsx)(x,{bottom:`8`,children:c})]})})}),(0,q.jsxs)(`div`,{className:`flex gap-md mt-md place-content-end`,children:[(0,q.jsx)(T,{variation:`secondary`,onClick:()=>{r(!1)},testId:`spec-cancel`,children:`Cancel`}),(0,q.jsx)(T,{testId:`spec-import`,disabled:!o||f,variation:`primary`,onClick:()=>{p()},children:`Import`})]})]})})};ui.propTypes={organizationId:K.default.string.isRequired,organizationHandle:K.default.string.isRequired,showModal:K.default.bool.isRequired,setShowModal:K.default.func.isRequired,afterCreate:K.default.func,onFail:K.default.func},F();var di=f`
  query OrganizationAssetImportStatus($handle: String!, $assetImportId: ID!) {
    organizations(first: 1, where: { handle: { _eq: $handle } }) {
      nodes {
        id
        asset_import(id: $assetImportId) {
          id
          state
          source
        }
      }
    }
  }
`,fi=()=>{let{dispatch:e}=(0,J.useContext)($);return(0,q.jsx)(`button`,{className:`ml-sm border border-gray-300 px-sm py-xs rounded`,onClick:()=>{e({type:X.SET_SHOW_IMPORT_SUMMARY_MODAL,value:!0})},children:`View summary`})},pi=({assetImportId:e,organizationHandle:t,hide:n})=>{let r=ae(),[a,o]=(0,J.useState)(!1),{data:s,stopPolling:c,startPolling:l}=U(di,{variables:{handle:t,assetImportId:e},pollInterval:0}),u=s?.organizations.nodes[0]?.asset_import,d=u?.state||constants.assetImport.statuses.created,f=u?.source,p=d===constants.assetImport.statuses.processed||d===constants.assetImport.statuses.processed_with_errors,m=d===constants.assetImport.statuses.failed,h=d===constants.assetImport.statuses.importing||d===constants.assetImport.statuses.created,g=p&&f!==`AssetScanner`;return(0,J.useEffect)(()=>{p?a&&(c(),o(!1),r.refetchQueries({include:[`OrganizationAssetsOverviewQuery`,`AssetGroupSearchQuery`,`AssetGroupCountsQuery`,`AssetsSearchQuery`,`AssetsSearchCountsQuery`]})):(l(5e3),o(!0))},[p,l,o,c,r,a]),(0,q.jsxs)(`div`,{className:`mt-md`,children:[m&&(0,q.jsx)(E,{variation:i.Danger,dismissable:!0,onDismiss:()=>{n instanceof Function&&n()},dismissAccessibilityLabel:`Close`,contentPrimary:`Import failed.`,contentSecondary:(0,q.jsx)(fi,{})}),g&&(0,q.jsx)(E,{variation:i.Success,dismissable:!0,onDismiss:()=>{n instanceof Function&&n()},dismissAccessibilityLabel:`Close`,contentPrimary:`Import complete.`,contentSecondary:(0,q.jsx)(fi,{})}),h&&(0,q.jsx)(E,{contentPrimary:`Importing assets into your inventory. This might take a while, in the meantime feel free to navigate to other pages.`,contentSecondary:(0,q.jsx)(`span`,{className:`mr-sm`,children:(0,q.jsx)(P,{src:`data:image/svg+xml,%3csvg%20xmlns='http://www.w3.org/2000/svg'%20width='24'%20height='24'%20viewBox='0%200%2024%2024'%3e%3cpath%20d='M18%2015v3H6v-3H4v3c0%201.1.9%202%202%202h12c1.1%200%202-.9%202-2v-3h-2zM7%209l1.41%201.41L11%207.83V16h2V7.83l2.59%202.58L17%209l-5-5l-5%205z'/%3e%3c/svg%3e`,accessabilityLabel:`Importing assets`})})})]})};pi.propTypes={assetImportId:K.default.string.isRequired,organizationHandle:K.default.string.isRequired,hide:K.default.func.isRequired},F();var mi=f`
  query OrganizationAssetImportSummary($handle: String!, $assetImportId: ID!) {
    organizations(first: 1, where: { handle: { _eq: $handle } }) {
      nodes {
        id
        asset_import(id: $assetImportId) {
          id
          _id
          state
          import_errors
          processed_existing_ids
          processed_new_ids
        }
      }
    }
  }
`,hi=({assetImportId:e})=>{let{store:t,dispatch:n,organization:r}=(0,J.useContext)($),{showImportSummaryModal:i}=t,a=e=>{n({type:X.SET_SHOW_IMPORT_SUMMARY_MODAL,value:e})},{data:o,loading:s}=ne(mi,{variables:{handle:r.handle,assetImportId:e}});if(s)return null;let c=o?.organizations.nodes[0].asset_import,l=c.import_errors;return(0,q.jsxs)(V,{shouldCloseOnEsc:!0,size:`large`,showModal:i,title:`Import Summary`,handleCloseModal:()=>a(!1),children:[(0,q.jsxs)(w,{children:[(0,q.jsxs)(`ul`,{children:[(0,q.jsxs)(`li`,{children:[(0,q.jsx)(`span`,{className:`text-green-300`,children:(0,q.jsx)(P,{size:`lg`,src:me})}),` `,c.processed_new_ids.length,` assets have been imported as new into your inventory.`]}),(0,q.jsxs)(`li`,{children:[(0,q.jsx)(`span`,{className:`text-blue-300`,children:(0,q.jsx)(P,{size:`lg`,src:me})}),` `,c.processed_existing_ids.length,` assets have been updated in your inventory.`]}),(0,q.jsxs)(`li`,{children:[(0,q.jsx)(`span`,{className:`text-red-300`,children:(0,q.jsx)(P,{size:`lg`,src:Pt})}),` `,l.length,` assets failed to be imported into the inventory.`]})]}),l.length>0&&(0,q.jsx)(`div`,{className:`overflow-y-auto px-md py-xs rounded-b max-h-[50vh]`,children:(0,q.jsx)(x,{top:`md`,children:l.map((e,t)=>(0,q.jsx)(`div`,{className:`flex`,children:(0,q.jsx)(`div`,{className:`flex flex-col`,children:(0,q.jsx)(`span`,{className:`text-red-300 font-semibold text-lg`,children:e})})},t))})})]}),(0,q.jsx)(x,{top:`md`,children:(0,q.jsx)(`div`,{className:`flex justify-end align-baseline gap-md mb-lg`,children:(0,q.jsx)(T,{medium:!0,variation:`ghost`,onClick:()=>a(!1),children:`Close`})})})]})};hi.propTypes={assetImportId:K.default.string.isRequired},F();var{ASM_PENTEST_DEMO_INTEGRATION:gi}=window.constants.featureToggles,_i=300,vi=`last_asset_import_id`,yi=()=>{try{return localStorage.getItem(vi)}catch{return null}},bi=e=>{try{return e==null?localStorage.removeItem(vi):localStorage.setItem(vi,e)}catch{return null}},xi=()=>{let{store:e,dispatch:t}=(0,J.useContext)($),{checkedAssetIdentifiers:n}=e,i=r(),a=`/pentest_opportunities/new?identifiers[]=${n.join(`&identifiers[]=`)}`,o=e=>{t({type:X.SET_SHOW_ADD_SCOPE_MODAL,value:e})},[c,l]=(0,J.useState)(!1),u=()=>l(!c),d=(0,J.useRef)(null);return Ye(d,()=>l(!1)),(0,q.jsx)(q.Fragment,{children:(0,q.jsx)(`div`,{className:`asset-row__menu-holder -ml-[1px]`,ref:d,children:(0,q.jsx)(wt,{popperClassname:`mt-spacing-16 spec-manage-tags-menu`,popperPlacement:`bottom-end`,showPopper:c,componentToTarget:(0,q.jsx)(T,{icons:{left:{accessibilityLabel:`test asset`,src:rr},right:{accessibilityLabel:`expand`,src:s}},onClick:u,variation:`tertiary`,children:`Test asset`}),componentToPop:(0,q.jsx)(w,{children:(0,q.jsxs)(`ul`,{className:`select-menu`,children:[(0,q.jsx)(`li`,{className:`menu-item spec-add-scope`,role:`button`,onClick:e=>{o(!0),e.stopPropagation()},children:`Add scope`}),(0,q.jsx)(`li`,{className:`menu-item spec-start-a-pentest`,role:`button`,onClick:e=>{i.push(a),e.stopPropagation()},children:`Start a pentest`})]})})})})})},Si=({name:e,actions:t,leftIcon:n,rightIcon:r})=>{let[i,a]=(0,J.useState)(!1),o=()=>a(!i),c=(0,J.useRef)(null);Ye(c,()=>a(!1));let l={};return n&&(l.left=n),r?l.right=r:l.right={accessibilityLabel:`expand`,src:s},(0,q.jsx)(q.Fragment,{children:(0,q.jsx)(`div`,{className:`asset-row__menu-holder -ml-[1px]`,ref:c,children:(0,q.jsx)(wt,{popperClassname:`mt-spacing-16 spec-manage-scope-menu`,popperPlacement:`bottom-start`,showPopper:i,componentToTarget:(0,q.jsx)(T,{icons:l,onClick:o,variation:`ghost-secondary`,small:!0,children:e}),componentToPop:(0,q.jsx)(w,{children:(0,q.jsx)(`ul`,{className:`select-menu`,children:t.map(e=>(0,q.jsx)(`li`,{className:e.disabled?`menu-item--disabled spec-menu-item-${e.id}--disabled daisy-link--graphite`:`menu-item spec-menu-item-${e.id}`,role:`button`,onClick:e.disabled?null:e.action,children:(0,q.jsxs)(H,{style:{gap:8},children:[(0,q.jsx)(H,{alignItems:`center`,justifyContent:`center`,width:24,children:e.icon&&(0,q.jsx)(P,{src:e.icon,accessabilityLabel:e.name})}),(0,q.jsx)(H,{children:e.name})]})},e.name))})})})})})};Si.propTypes={name:K.default.string.isRequired,actions:K.default.arrayOf(K.default.object),leftIcon:K.default.object,rightIcon:K.default.object};var Ci=({showSelectAllToggle:e,assetsDataObject:t,loading:n,isGroupedView:r,pageSize:i,loadMoreGroups:a,hasGateway:o})=>{let{store:s,dispatch:c,organization:l}=(0,J.useContext)($),{checkedAssets:u,checkedAssetObjects:d,showAddScopeModal:f,showOutOfScopeModal:p,showRemoveScopeModal:m,showArchiveAssetsModal:h,showUnarchiveAssetsModal:g,showAddAssetModal:_,showImportFromCsvModal:v,showImportSummaryModal:y,selectedTab:b}=s,[x,S]=(0,J.useState)(!1),[C,ee]=(0,J.useState)(!1),[te,E]=(0,J.useState)(!1),[ne,D]=(0,J.useState)(!1),[O,re]=J.useState(void 0),[k,A]=J.useState(void 0),[j,ie]=J.useState(void 0),[ae,oe]=J.useState(void 0),[se,ce]=(0,J.useState)(yi()),{scrollToTop:ue,showScrollToTopButton:de}=nr(),fe=d.filter(e=>e.coverage!==constants.assetInventory.coverageTypes.outOfScope),pe=()=>d.every(e=>e.coverage===constants.assetInventory.coverageTypes.new||e.coverage===constants.assetInventory.coverageTypes.untested),me=x&&!te&&!ne&&O===void 0&&k===void 0&&j===void 0&&ae===void 0,{enabled:he}=vt(gi),M=e=>{c({type:X.SET_SHOW_IMPORT_FROM_CSV_MODAL,value:e})},N=e=>{c({type:X.SET_SHOW_ADD_ASSET_MODAL,value:e})},_e=e=>{c({type:X.SET_SHOW_ADD_SCOPE_MODAL,value:e})},ve=e=>{c({type:X.SET_SHOW_OUT_OF_SCOPE_MODAL,value:e})},ye=e=>{c({type:X.SET_SHOW_REMOVE_SCOPE_MODAL,value:e})},be=e=>{c({type:X.SET_SHOW_ARCHIVE_ASSETS_MODAL,value:e})},xe=e=>{c({type:X.SET_SHOW_UNARCHIVE_ASSETS_MODAL,value:e})},Se=()=>{c({type:X.TOGGLE_SELECT_ALL_ASSETS,value:t?.nodes||[]})},Ce=u.length>0,we=!n&&u.length===t?.nodes?.length,F=()=>{_e(!0)},Te=()=>{ye(!0)},Ee=()=>{ve(!0)},De=()=>{xe(!0)},Oe=b===`archived`,ke=t?.current_count===_i;return(0,q.jsxs)(q.Fragment,{children:[(0,q.jsxs)(`div`,{className:`sticky top-md z-10 flex flex-col`,children:[(0,q.jsx)(ge,{fill:!0,padding:`none`,border:!1,children:(0,q.jsxs)(`div`,{className:`h-[70px] p-sm flex items-center menu border-b border-neutral-700 dark:border-neutral-50 relative `,children:[e&&(0,q.jsx)(w,{children:(0,q.jsx)(`div`,{children:(0,q.jsx)(le,{name:`assets-select-all`,testId:`spec-assets-select-all`,onChange:()=>{Se(),$e.track(`select all checkbox clicked for searched assets`)},checked:we,indeterminate:!n&&Ce&&!we,label:`Select all (${u.length})`})})}),(0,q.jsx)(`div`,{className:`grow`}),l.i_can_manage_organization_assets&&!Oe&&(0,q.jsxs)(`div`,{className:`flex items-center pr-spacing-32`,children:[u.length<=0&&(0,q.jsxs)(`div`,{className:`flex items-center assets-bulk-menu gap-1`,children:[(0,q.jsx)(`div`,{className:`border-r border-solid pr-sm border-neutral-600`,children:(0,q.jsx)(Si,{name:`Add assets`,leftIcon:{src:`data:image/svg+xml,%3csvg%20xmlns='http://www.w3.org/2000/svg'%20width='24'%20height='24'%20viewBox='0%200%2024%2024'%3e%3cpath%20d='M19%2013h-6v6h-2v-6H5v-2h6V5h2v6h6v2z'/%3e%3c/svg%3e`,accessibilityLabel:`add assets`},actions:[{id:`create-new-asset-button`,name:`Create new`,action:e=>{e.preventDefault(),N(!0),$e.track(`asset creation modal opened`,{category:window.constants.analytics.asset_inventory}),e.stopPropagation()},className:`spec-add-asset-button add-asset-button`},{id:`import-assets-button`,name:`Import from CSV`,action:e=>{e.preventDefault(),M(!0),$e.track(`asset import csv modal opened`,{category:window.constants.analytics.asset_inventory}),e.stopPropagation()},className:`spec-import-assets-button import-assets-button`}]})}),(0,q.jsx)(`div`,{className:`manage-tags-button spec-manage-tags-button pl-sm`,children:(0,q.jsx)(T,{variation:`ghost-secondary`,disabled:!l.i_am_asset_inventory_manager,small:!0,icons:{left:{src:`data:image/svg+xml,%3csvg%20xmlns='http://www.w3.org/2000/svg'%20width='24'%20height='24'%20viewBox='0%200%2024%2024'%3e%3cpath%20d='M19.43%2012.98c.04-.32.07-.64.07-.98c0-.34-.03-.66-.07-.98l2.11-1.65c.19-.15.24-.42.12-.64l-2-3.46a.5.5%200%200%200-.61-.22l-2.49%201c-.52-.4-1.08-.73-1.69-.98l-.38-2.65A.488.488%200%200%200%2014%202h-4c-.25%200-.46.18-.49.42l-.38%202.65c-.61.25-1.17.59-1.69.98l-2.49-1a.566.566%200%200%200-.18-.03c-.17%200-.34.09-.43.25l-2%203.46c-.13.22-.07.49.12.64l2.11%201.65c-.04.32-.07.65-.07.98c0%20.33.03.66.07.98l-2.11%201.65c-.19.15-.24.42-.12.64l2%203.46a.5.5%200%200%200%20.61.22l2.49-1c.52.4%201.08.73%201.69.98l.38%202.65c.03.24.24.42.49.42h4c.25%200%20.46-.18.49-.42l.38-2.65c.61-.25%201.17-.59%201.69-.98l2.49%201c.06.02.12.03.18.03c.17%200%20.34-.09.43-.25l2-3.46c.12-.22.07-.49-.12-.64l-2.11-1.65zm-1.98-1.71c.04.31.05.52.05.73c0%20.21-.02.43-.05.73l-.14%201.13l.89.7l1.08.84l-.7%201.21l-1.27-.51l-1.04-.42l-.9.68c-.43.32-.84.56-1.25.73l-1.06.43l-.16%201.13l-.2%201.35h-1.4l-.19-1.35l-.16-1.13l-1.06-.43c-.43-.18-.83-.41-1.23-.71l-.91-.7l-1.06.43l-1.27.51l-.7-1.21l1.08-.84l.89-.7l-.14-1.13c-.03-.31-.05-.54-.05-.74s.02-.43.05-.73l.14-1.13l-.89-.7l-1.08-.84l.7-1.21l1.27.51l1.04.42l.9-.68c.43-.32.84-.56%201.25-.73l1.06-.43l.16-1.13l.2-1.35h1.39l.19%201.35l.16%201.13l1.06.43c.43.18.83.41%201.23.71l.91.7l1.06-.43l1.27-.51l.7%201.21l-1.07.85l-.89.7l.14%201.13zM12%208c-2.21%200-4%201.79-4%204s1.79%204%204%204s4-1.79%204-4s-1.79-4-4-4zm0%206c-1.1%200-2-.9-2-2s.9-2%202-2s2%20.9%202%202s-.9%202-2%202z'/%3e%3c/svg%3e`,accessibilityLabel:`manage tags`}},onClick:e=>{if(e.preventDefault(),e.stopPropagation(),!l.i_am_asset_inventory_manager)return!1;S(!0)},children:`Manage tags`})})]}),u.length>0&&!Oe&&(0,q.jsxs)(`div`,{className:`flex items-center assets-bulk-menu`,children:[(0,q.jsxs)(ot,{to:`#`,className:`daisy-link daisy-link--black archive-assets-button spec-archive-assets-button`,onClick:e=>{e.preventDefault(),be(!0),e.stopPropagation()},children:[(0,q.jsx)(`span`,{className:`mr-sm`,children:(0,q.jsx)(P,{src:`data:image/svg+xml,%3csvg%20xmlns='http://www.w3.org/2000/svg'%20width='24'%20height='24'%20viewBox='0%200%2024%2024'%3e%3cpath%20d='M20.54%205.23l-1.39-1.68C18.88%203.21%2018.47%203%2018%203H6c-.47%200-.88.21-1.16.55L3.46%205.23C3.17%205.57%203%206.02%203%206.5V19c0%201.1.9%202%202%202h14c1.1%200%202-.9%202-2V6.5c0-.48-.17-.93-.46-1.27zM6.24%205h11.52l.81.97H5.44l.8-.97zM5%2019V8h14v11H5zm8.45-9h-2.9v3H8l4%204l4-4h-2.55z'/%3e%3c/svg%3e`,accessabilityLabel:`Archive`})}),`Archive`]}),(0,q.jsxs)(ot,{className:`daisy-link daisy-link--black add-asset-button spec-add-asset-button`,to:`#`,onClick:e=>{e.preventDefault(),ee(!0),e.stopPropagation()},children:[(0,q.jsx)(`span`,{className:`mr-sm`,children:(0,q.jsx)(P,{src:`data:image/svg+xml,%3csvg%20xmlns='http://www.w3.org/2000/svg'%20width='24'%20height='24'%20viewBox='0%200%2024%2024'%3e%3cpath%20d='M21%2012l-4.37%206.16c-.37.52-.98.84-1.63.84h-3v-2h3l3.55-5L15%207H5v3H3V7c0-1.1.9-2%202-2h10c.65%200%201.26.31%201.63.84L21%2012zm-11%203H7v-3H5v3H2v2h3v3h2v-3h3v-2z'/%3e%3c/svg%3e`,accessabilityLabel:`Add tags`})}),`Assign tags`]}),he?(0,q.jsx)(xi,{}):(0,q.jsx)(Si,{name:`Manage Scope`,actions:[{id:`add-scope-button`,name:`Add to program`,icon:`data:image/svg+xml,%3csvg%20xmlns='http://www.w3.org/2000/svg'%20width='24'%20height='24'%20viewBox='0%200%2024%2024'%3e%3cpath%20d='M19%2013h-6v6h-2v-6H5v-2h6V5h2v6h6v2z'/%3e%3c/svg%3e`,action:F,className:`spec-add-scope-button`},{id:`set-out-of-scope-button`,name:`Set out of scope`,icon:`data:image/svg+xml,%3csvg%20xmlns='http://www.w3.org/2000/svg'%20width='24'%20height='24'%20viewBox='0%200%2024%2024'%3e%3cpath%20d='M12%202C6.48%202%202%206.48%202%2012s4.48%2010%2010%2010s10-4.48%2010-10S17.52%202%2012%202zM4%2012c0-4.42%203.58-8%208-8c1.85%200%203.55.63%204.9%201.69L5.69%2016.9A7.902%207.902%200%200%201%204%2012zm8%208c-1.85%200-3.55-.63-4.9-1.69L18.31%207.1A7.902%207.902%200%200%201%2020%2012c0%204.42-3.58%208-8%208z'/%3e%3c/svg%3e`,disabled:fe.length===0,action:Ee,className:`spec-out-of-scope-button`},{id:`remove-scope-button`,name:`Remove from program`,icon:`data:image/svg+xml,%3csvg%20xmlns='http://www.w3.org/2000/svg'%20width='24'%20height='24'%20viewBox='0%200%2024%2024'%3e%3cpath%20d='M16%209v10H8V9h8m-1.5-6h-5l-1%201H5v2h14V4h-3.5l-1-1zM18%207H6v12c0%201.1.9%202%202%202h8c1.1%200%202-.9%202-2V7z'/%3e%3c/svg%3e`,disabled:pe(),action:Te,className:`spec-remove-scope-button`}]})]})]}),Oe&&u.length>0&&(0,q.jsx)(`div`,{className:`flex items-center bulk-unarchive mr-spacing-16`,children:(0,q.jsx)(T,{onClick:De,variation:`primary`,icons:{left:{src:`data:image/svg+xml,%3csvg%20xmlns='http://www.w3.org/2000/svg'%20width='24'%20height='24'%20viewBox='0%200%2024%2024'%3e%3cpath%20d='M12.5%208c-2.65%200-5.05.99-6.9%202.6L2%207v9h9l-3.62-3.62c1.39-1.16%203.16-1.88%205.12-1.88c3.54%200%206.55%202.31%207.6%205.5l2.37-.78C21.08%2011.03%2017.15%208%2012.5%208z'/%3e%3c/svg%3e`,accessibilityLabel:`Unarchive asset`}},children:`Unarchive`})}),r?(0,q.jsx)(ri,{loading:n,loadMore:a,paginationInfoObject:t,isMax:ke}):(0,q.jsx)(ni,{loading:n,paginationInfoObject:t,pageSize:i})]})}),de&&(0,q.jsx)(`div`,{className:`fixed assets-scroll-to-top self-center m-auto shadow bg-white dark:bg-black border-neutral-700 rounded`,onClick:ue,children:(0,q.jsx)(T,{icons:{left:{src:`data:image/svg+xml,%3csvg%20xmlns='http://www.w3.org/2000/svg'%20width='24'%20height='24'%20viewBox='0%200%2024%2024'%3e%3cpath%20d='M4%2012l1.41%201.41L11%207.83V20h2V7.83l5.58%205.59L20%2012l-8-8l-8%208z'/%3e%3c/svg%3e`,accessibilityLabel:`Upward arrow`}},variation:`ghost`,children:`Scroll to top`})}),ke&&(0,q.jsx)(Nt,{analyticsLabel:`asset groups max banner displayed`,maxGroupCount:_i})]}),_&&(0,q.jsx)(mr,{organizationId:l.id,showModal:!0,setShowModal:N,hasGateway:o,afterCreate:e=>{c({type:X.SET_ROW_MENU_ASSET_ID,value:e.createAsset.asset.databaseId}),c({type:X.SET_SHOW_ADD_SCOPE_MODAL,value:!0})}}),te&&(0,q.jsx)(Ur,{showModal:!0,setShowModal:E,closeModal:()=>E(!1),organization:l}),v&&(0,q.jsx)(ui,{organizationId:l.id,organizationHandle:l.handle,showModal:!0,setShowModal:M,afterCreate:e=>{ce(e.asset_import.id),bi(e.asset_import.id)}}),se&&(0,q.jsx)(pi,{hide:()=>{ce(null),bi(null)},assetImportId:se,organizationHandle:l.handle}),y&&(0,q.jsx)(hi,{assetImportId:se}),k!==void 0&&(0,q.jsx)(qr,{showModal:!0,categoryId:k?.id,categoryName:k?.name,onClose:()=>{A(void 0)},onComplete:()=>{A(void 0)}}),O!==void 0&&(0,q.jsx)(Gr,{showModal:!0,tagId:O?.id,tagName:O?.name,onClose:()=>{re(void 0)},onComplete:()=>{re(void 0)}}),j!==void 0&&(0,q.jsx)(Zr,{showModal:!0,tagId:j.id,tagName:j.name,categoryId:j.categoryId,organizationHandle:l.handle,onClose:()=>{ie(void 0)},onComplete:()=>{ie(void 0)}}),me&&(0,q.jsx)(xr,{setShowAddCustomTagModal:E,setShowAddCustomTagCategoryModal:D,organization:l,close:()=>S(!1),onEditTag:ie,onDeleteTag:re,onDeleteCategory:A,onEditCategory:oe}),ne&&(0,q.jsx)(Br,{showModal:!0,setShowModal:D,closeModal:()=>D(!1),organization:l}),ae!==void 0&&(0,q.jsx)($r,{showModal:!0,setShowModal:e=>{e||oe(void 0)},tagCategory:ae,closeModal:()=>oe(void 0),organization:l}),f&&(0,q.jsx)(kr,{organization:l,showModal:!0,setShowModal:_e}),p&&(0,q.jsx)(jr,{organization:l,showModal:!0,setShowModal:ve}),h&&(0,q.jsx)(Pr,{showModal:!0,setShowModal:be}),g&&(0,q.jsx)(ii,{showModal:!0,setShowModal:xe}),m&&(0,q.jsx)(Rr,{organization:l,showModal:!0,setShowModal:ye}),C&&(0,q.jsx)(qn,{assetIds:u,organization:l,showModal:!0,closeModal:()=>ee(!1)})]})};Ci.propTypes={showSelectAllToggle:K.default.bool,assetsDataObject:K.default.object,loading:K.default.bool.isRequired,pageSize:K.default.number,isGroupedView:K.default.bool,loadMoreGroups:K.default.func,hasGateway:K.default.bool},Ci.fragments={organization:f`
    fragment AssetActionsOrganizationFragment on Organization {
      id
      ...AddScopeModalOrganizationFragment
      ...SetOutOfScopeModalOrganizationFragment
    }
    ${kr.fragments.organization}
    ${jr.fragments.organization}
  `};var wi=({numberOfRows:e=5})=>(0,q.jsx)(I,{fixed:!0,className:`spec-domains-table`,children:(0,q.jsx)(I.Body,{children:(0,dn.default)(e).map(e=>(0,q.jsxs)(I.Row,{children:[(0,q.jsx)(I.Cell,{children:(0,q.jsx)(M,{lines:1})}),(0,q.jsx)(I.Cell,{children:(0,q.jsx)(M,{lines:1})})]},e))})});wi.propTypes={numberOfRows:K.default.number};var Ti=({actions:e})=>{let[t,n]=(0,J.useState)(!1),r=()=>{n(!t)},i=(0,J.useRef)(null);return Ye(i,()=>{n(!1)}),(0,q.jsx)(`div`,{className:`flex justify-end`,children:(0,q.jsx)(`div`,{className:`asset-row__menu-holder`,ref:i,children:(0,q.jsx)(wt,{popperClassname:`spec-asset-row-menu asset-row-menu`,popperPlacement:`bottom-end`,showPopper:t,componentToTarget:(0,q.jsx)(T,{onClick:r,variation:Oe.GhostSecondary,iconOnly:!0,icons:{center:{accessibilityLabel:`Asset actions`,src:_e}},testId:`spec-asset-row-button`}),componentToPop:(0,q.jsx)(`ul`,{className:`select-menu`,children:e.map(e=>(0,q.jsx)(`li`,{className:e.disabled?`menu-item--disabled spec-menu-item-${e.id}--disabled text-neutral-400`:`menu-item spec-menu-item-${e.id}`,onClick:()=>{e.disabled||(e.action(),r())},children:(0,q.jsxs)(`div`,{className:`flex gap-sm items-end`,children:[e.icon&&(0,q.jsx)(`div`,{className:`align-center justify-center`,children:(0,q.jsx)(P,{src:e.icon,size:Te.Large})}),(0,q.jsx)(`div`,{className:`w-40`,children:e.name}),e.isBeta&&(0,q.jsx)(`div`,{className:`align-center justify-center`,children:(0,q.jsx)(C,{color:v.Green,children:`Beta`})})]})},e.name))})})})})};Pe();var Ei=`spot checks from asset row menu clicked`,{ASSET_SCANNER_BETA:Di,ASSET_TAG_REWARD_CATEGORIES:Oi}=window.constants.featureToggles,ki=2,Ai=e=>[...e].sort((e,t)=>{let n=!!e.asm_tag_category?.unique_tag_per_asset;if(n!==!!t.asm_tag_category?.unique_tag_per_asset)return n?-1:1;let r=!!e.asm_tag_category?.system;return r===!!t.asm_tag_category?.system?e.name.localeCompare(t.name):r?-1:1}),ji=({asset:e,organization:t})=>{let n=r(),{store:{checkedAssets:i,selectedTab:a},dispatch:s,organization:{asset_package:c}}=(0,J.useContext)($),l=c?.risks_enabled,u=a===`archived`,d=a===`untested`,f=a===`in_scope`,p=a===`out_of_scope`,m=()=>{s({type:X.SET_ASSET_SIDEBAR_TAB_INDEX,value:0}),s({type:X.SET_SELECTED_ASSET_ID,value:e.asset_id})},h=e=>{s({type:X.SET_ROW_MENU_ASSET_ID,value:Number(e)})},g=()=>{h(e.databaseId),s({type:X.SET_SHOW_ADD_SCOPE_MODAL,value:!0})},_=()=>{h(e.databaseId),s({type:X.SET_SHOW_REMOVE_SCOPE_MODAL,value:!0})},v=()=>{h(e.databaseId),s({type:X.SET_SHOW_ARCHIVE_ASSETS_MODAL,value:!0})},[y,b]=(0,J.useState)(!1),x=e=>{s({type:X.SET_SHOW_UNARCHIVE_ASSETS_MODAL,value:e})},S=e=>i.includes(Number(e.databaseId)),w=e=>{s({type:X.TOGGLE_CHECK_ASSET,value:e})},{enabled:ee}=B(Di,t.handle),{enabled:te}=B(Oi,t.handle),[E,{loading:ne}]=k(ft),[D,O]=(0,J.useState)(e.reachability),re=e.open_vulnerabilities,A;if(e.coverage===constants.assetInventory.coverageTypes.inScope){let e;e=re<10?`green`:re<50?`orange`:`red`,A=(0,q.jsx)(C,{icons:{right:{src:It,accessibilityLabel:`Search`}},color:e,children:String(re)})}else A=(0,q.jsx)(C,{color:`gray`,icons:{right:{src:It,accessibilityLabel:`Search`}},children:`-`});let j=()=>{h(e.databaseId),x(!0)},ie=!u&&i.length===0,ae=![constants.assetInventory.coverageTypes.inScope,constants.assetInventory.coverageTypes.outOfScope].includes(e.coverage),oe=()=>{let t=e.in_scope_team_names.map(e=>(0,q.jsx)(N,{text:`In scope`,children:(0,q.jsx)(`span`,{className:p?`opacity-30`:``,children:(0,q.jsx)(C,{color:`gray`,children:e})})},e));return e.out_of_scope_team_names.length&&(t=t.concat(e.out_of_scope_team_names.map(e=>(0,q.jsx)(N,{text:`Out of scope`,children:(0,q.jsx)(`span`,{className:f?`opacity-30`:``,children:(0,q.jsx)(C,{color:`gray`,children:e})})},e)))),t},se=[{id:`view-overview`,name:`View overview`,icon:de,action:m},{id:`add-to-scope`,name:`Add to program`,disabled:!t.i_can_manage_organization_assets,icon:o,action:g},{id:`remove-from-scope`,name:`Remove from program`,disabled:ae||!t.i_can_manage_organization_assets,icon:pe,action:_},{id:`archive`,name:`Archive`,disabled:!t.i_am_asset_inventory_manager,icon:Se,action:v},{id:`add-tag`,name:`Add Tag`,disabled:!t.i_am_asset_inventory_manager,icon:Vt,action:()=>b(!0)}];return t.i_can_create_spot_checks&&se.push({id:`run-spot-check`,name:`Run a spot check`,icon:rr,action:()=>{Ct(Ei,{organization_handle:t.handle}),n.push(`/organizations/${t.handle}/spot_checks/select_type`)}}),ee&&se.push({id:`check-reachability`,name:`Check reachability`,disabled:!ne&&D&&!D?.refreshable,icon:he,action:()=>{E({variables:{assetId:e.asset_id},onCompleted:e=>{e.checkAssetReachability.was_successful&&O(e.checkAssetReachability.asset_reachability)}})}}),(0,q.jsxs)(I.Row,{className:`spec-asset-row asset-row group`,children:[(0,q.jsxs)(I.Cell,{className:`dark:bg-black pl-spacing-32`,children:[(0,q.jsx)(`span`,{className:`spec-asset-row-checkbox align-middle mr-spacing-16`,children:(0,q.jsx)(le,{name:`asset-${e.id}`,checked:S(e),onChange:()=>{w(e)}})}),!u&&l?(0,q.jsx)(Rt,{riskRating:e.risk_rating}):null]}),(0,q.jsx)(I.Cell,{className:`dark:bg-black`,children:(0,q.jsxs)(`div`,{className:`cursor-pointer flex gap-sm`,onClick:m,children:[ee&&(0,q.jsx)(`span`,{className:`align-middle`,children:(0,q.jsx)(Ve,{lastStatus:D?.last_status})}),e.coverage===constants.assetInventory.coverageTypes.untested&&Me().subtract(30,`d`).isBefore(e.created_at)?(0,q.jsx)(`span`,{children:(0,q.jsx)(C,{testId:`spec-new-asset`,color:`blue`,rounded:!1,children:`New`})}):null,(0,q.jsx)(`span`,{className:`truncate spec-asset-identifier`,children:e.identifier})]})}),!u&&!d&&(0,q.jsx)(I.Cell,{className:`dark:bg-black`,children:(0,q.jsx)(`div`,{className:`flex gap-spacing-4 flex-wrap`,children:oe()})}),(0,q.jsx)(I.Cell,{className:`dark:bg-black`,children:!u&&A}),te&&!u&&!d&&(0,q.jsx)(I.Cell,{className:`dark:bg-black`,children:(0,q.jsx)(`div`,{className:`flex gap-spacing-4 flex-wrap`,children:(()=>{let t=Ai(e.asm_tags?.nodes??[]),n=t.slice(0,ki),r=t.length-ki;return(0,q.jsxs)(q.Fragment,{children:[n.map(e=>(0,q.jsx)(C,{color:`gray`,children:e.name_with_category},e.id)),r>0&&(0,q.jsxs)(C,{color:`gray`,children:[`+`,r]})]})})()})}),(0,q.jsxs)(I.Cell,{className:`actions dark:bg-black h-[64px]`,children:[u&&i.length===0&&(0,q.jsx)(`div`,{className:`flex justify-end`,children:(0,q.jsx)(T,{onClick:j,variation:`ghost`,small:!0,iconOnly:!0,icons:{center:{src:`data:image/svg+xml,%3csvg%20xmlns='http://www.w3.org/2000/svg'%20width='24'%20height='24'%20viewBox='0%200%2024%2024'%3e%3cpath%20d='M12.5%208c-2.65%200-5.05.99-6.9%202.6L2%207v9h9l-3.62-3.62c1.39-1.16%203.16-1.88%205.12-1.88c3.54%200%206.55%202.31%207.6%205.5l2.37-.78C21.08%2011.03%2017.15%208%2012.5%208z'/%3e%3c/svg%3e`,accessibilityLabel:`Unarchive asset`}},children:`Unarchive`})}),ie&&(0,q.jsx)(q.Fragment,{children:(0,q.jsx)(Ti,{actions:se})}),y&&(0,q.jsx)(qn,{assetIds:[Number(e.databaseId)],showModal:!0,closeModal:()=>b(!1),organization:t})]})]},`asset-${e.id}`)};ji.propTypes={asset:K.default.object.isRequired,organization:K.default.object.isRequired,canManageAssets:K.default.bool};var Mi=()=>(0,q.jsx)(I.Row,{className:`spec-asset-row-loading asset-row`,children:(0,q.jsx)(I.Cell,{colSpan:5,className:`dark:bg-black`,children:(0,q.jsx)(M,{lines:1})})}),Ni=e(ke()),Pi=e=>e.map(e=>Number(e)),Fi=(e,t,n)=>Object.keys(e).map(r=>({category_id:Number(n.find(e=>(0,Ni.default)(e.name)===r)?.databaseId),tag_ids:t[r]?t[r].map(e=>Number(e)):[],clause:e[r]})),Ii=({store:{searchTerm:e,selectedProgramIds:t,selectedAssetTypes:n,selectedAsmTagIds:r,selectedTagCategoryClauses:i,selectedPorts:a,selectedProtocols:o},organization:s,debounced:c})=>{let l=rt(e,300),u=Pi(t),d=Fi(i,r,s.asm_tag_categories.nodes),f=[];return a.forEach(e=>{let t=parseInt(e,10);!isNaN(t)&&t>=1&&t<=65535&&f.push({port:t})}),o.forEach(e=>{f.push({protocol:e})}),{assetTypes:n,handle:s.handle,programIds:u,searchString:c?l:e,asmTagCategoryClauses:d,ports:f.length>0?f:void 0}},Li=({store:{searchTerm:e,selectedTab:t,selectedProgramIds:n,selectedAssetTypes:r,selectedAsmTagIds:i,selectedTagCategoryClauses:a,selectedPorts:o,selectedProtocols:s},organization:c,debounced:l})=>{let u=rt(e,300),d=Pi(n),f=Fi(a,i,c.asm_tag_categories.nodes),p=[];return o.forEach(e=>{let t=parseInt(e,10);!isNaN(t)&&t>=1&&t<=65535&&p.push({port:t})}),s.forEach(e=>{p.push({protocol:e})}),{archived:t===`archived`,assetTypes:r,coverage:t===`archived`?void 0:t,handle:c.handle,programIds:d,searchString:l?u:e,asmTagCategoryClauses:f,ports:p.length>0?p:void 0}};F();var Ri=e(Fe()),zi=f`
  mutation ExportAssetsInventory(
    $organizationId: ID!
    $email: String!
    $archived: Boolean
    $asmTagIds: [Int]
    $asmTagCategoryClauses: [AssetTagCategoryClauseInput]
    $assetTypes: [AssetImplementationTypeEnum]
    $coverage: AssetCoverageEnum
    $searchString: String
    $programIds: [Int]
    $ports: [AssetPortFilterInputType]
    $state: AssetStateEnum
  ) {
    exportAssets(
      input: {
        organization_id: $organizationId
        email: $email
        archived: $archived
        asm_tag_ids: $asmTagIds
        asm_tag_category_clauses: $asmTagCategoryClauses
        asset_types: $assetTypes
        coverage: $coverage
        search_string: $searchString
        team_ids: $programIds
        ports: $ports
        state: $state
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
    }
  }
`,Bi=({currentAssetsCount:e})=>{let n=e==null?`...`:`${e} ${un.default.pluralize(e,`asset`)}`,{store:r,organization:i,me:{email:a}}=(0,J.useContext)($),[o,s]=(0,J.useState)(!1),[c,l]=(0,J.useState)(a??``),[u,d]=(0,J.useState)(!1),[f]=z(zi,{variables:{organizationId:i.id,state:`confirmed`,email:c,...(0,Ri.default)(Li({store:r,organization:i,debounced:!1}),[`handle`])},onCompleted:({exportAssets:e})=>{if(e.was_successful)d(!1),s(!1),L(`notice`,`We've successfully received your request. You'll receive an email shortly!`);else{d(!1);let t=ut(e.errors);t.organization_id?L(`error`,t.organization_id):W()}}});return(0,q.jsxs)(`div`,{children:[(0,q.jsxs)(T,{variation:`ghost`,onClick:()=>{s(!0)},disabled:!e,children:[`Export Assets CSV (`,n,`)`]}),(0,q.jsxs)(V,{title:`Export Assets CSV`,showModal:o,shouldCloseOnOverlayClick:!0,shouldCloseOnEsc:!0,handleCloseModal:()=>s(!1),size:`medium`,children:[(0,q.jsxs)(`div`,{className:`mb-spacing-24`,children:[`Enter your email address to receive a link to download a CSV list.`,(0,q.jsx)(`br`,{}),`Note: It may take a few hours to export all assets.`]}),(0,q.jsx)(t,{text:`E-mail address`,optional:!1}),(0,q.jsxs)(`div`,{className:`flex mt-spacing-8 mb-spacing-12 gap-spacing-8`,children:[(0,q.jsx)(`div`,{className:`grow`,children:(0,q.jsx)(ue,{name:`email_address`,value:c,onChange:({target:{value:e}})=>l(e)})}),(0,q.jsx)(T,{disabled:!c||c.trim().length===0||u,onClick:()=>{c.trim().length!==0&&(d(!0),f())},children:`Send`})]})]})]})};Bi.propTypes={currentAssetsCount:K.PropTypes.number},Bi.fragments={me:f`
    fragment AssetInventoryExportAssetsFragment on User {
      id
      email
    }
  `},F();var Vi=f`
  mutation ExportRisks(
    $organizationId: ID!
    $email: String!
    $archived: Boolean
    $asmTagIds: [Int]
    $assetTypes: [AssetImplementationTypeEnum]
    $coverage: AssetCoverageEnum
    $searchString: String
    $programIds: [Int]
  ) {
    exportRisks(
      input: {
        organization_id: $organizationId
        email: $email
        archived: $archived
        asm_tag_ids: $asmTagIds
        asset_types: $assetTypes
        coverage: $coverage
        search_string: $searchString
        team_ids: $programIds
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
    }
  }
`,Hi=()=>{let{store:e,organization:n,me:{email:r}}=(0,J.useContext)($),[i,a]=(0,J.useState)(!1),[o,s]=(0,J.useState)(r??``),[c,l]=(0,J.useState)(!1),[u]=z(Vi,{variables:{organizationId:n.id,email:o,...(0,Ri.default)(Li({store:e,organization:n,debounced:!1}),[`handle`,`asmTagCategoryClauses`,`ports`])},onCompleted:({exportRisks:e})=>{if(e.was_successful)l(!1),a(!1),L(`notice`,`We've successfully received your request. You'll receive an email shortly!`);else{l(!1);let t=ut(e.errors);t.organization_id?L(`error`,t.organization_id):W()}}});return(0,q.jsxs)(`div`,{children:[(0,q.jsx)(T,{variation:`ghost`,onClick:()=>{a(!0)},children:`Export Risks CSV`}),(0,q.jsxs)(V,{title:`Export Risks CSV`,showModal:i,shouldCloseOnOverlayClick:!0,shouldCloseOnEsc:!0,handleCloseModal:()=>a(!1),size:`medium`,children:[(0,q.jsxs)(`div`,{className:`mb-spacing-24`,children:[`Enter your email address to receive a link to download a CSV list.`,(0,q.jsx)(`br`,{}),`Note: It may take a few hours to export all risks.`]}),(0,q.jsx)(t,{text:`E-mail address`,optional:!1}),(0,q.jsxs)(`div`,{className:`flex mt-spacing-8 mb-spacing-12 gap-spacing-8`,children:[(0,q.jsx)(`div`,{className:`grow`,children:(0,q.jsx)(ue,{name:`email_address`,value:o,onChange:({target:{value:e}})=>s(e)})}),(0,q.jsx)(T,{disabled:!o||o.trim().length===0||c,onClick:()=>{o.trim().length!==0&&(l(!0),u())},children:`Send`})]})]})]})};Hi.propTypes={currentAssetsCount:K.PropTypes.number},Hi.fragments={me:f`
    fragment ExportRisksFragment on User {
      id
      email
    }
  `};var Ui=(e,t)=>{switch(t){case constants.assetInventory.coverageTypes.all:return e.total_assets_count;case constants.assetInventory.coverageTypes.new:return e.total_new_count;case constants.assetInventory.coverageTypes.inScope:return e.total_in_scope_count;case constants.assetInventory.coverageTypes.outOfScope:return e.total_out_of_scope_count;case constants.assetInventory.coverageTypes.untested:return e.total_untested_count;case`archived`:return e.total_archived_count}},Wi=({assetCounts:e})=>{let{dispatch:t,store:{selectedTab:n},organization:r}=(0,J.useContext)($),i=[{id:`all`,value:constants.assetInventory.coverageTypes.all,label:`All (${e.total_assets_count})`},{id:`new`,value:constants.assetInventory.coverageTypes.new,label:`New (${e.total_new_count})`},{id:`in scope`,value:constants.assetInventory.coverageTypes.inScope,label:`In scope (${e.total_in_scope_count})`},{id:`out of scope`,value:constants.assetInventory.coverageTypes.outOfScope,label:`Out of scope (${e.total_out_of_scope_count})`},{id:`untested`,value:constants.assetInventory.coverageTypes.untested,label:`Untested (${e.total_untested_count})`},{id:`archived`,value:`archived`,label:`Archived (${e.total_archived_count})`}],a=e=>{t({type:X.CLEAR_CHECKED_ASSETS}),t({type:X.SET_SELECTED_TAB,value:e})},o=Number.parseInt(Ui(e,n));return(0,q.jsx)(Ce,{children:(0,q.jsxs)(`div`,{className:`flex mt-spacing-12 h-[60px] items-center`,children:[(0,q.jsx)(`div`,{className:`spec-assets-submenu grow`,children:(0,q.jsx)(Ft,{items:i,onChange:e=>{let t=i[e];a(t.value)},selectedIndex:i.findIndex(e=>e.value===n)})}),r.asset_package?.risks_enabled&&(0,q.jsx)(Hi,{}),(0,q.jsx)(Bi,{currentAssetsCount:Number.isNaN(o)?void 0:o})]})})};Wi.propTypes={assetCounts:K.default.object};var Gi={total_assets_count:`...`,total_new_count:`...`,total_in_scope_count:`...`,total_out_of_scope_count:`...`,total_untested_count:`...`,total_archived_count:`...`},Ki=e=>({total_assets_count:e.aggs.total_count?.buckets.unarchived?.doc_count||0,total_new_count:e.aggs.coverage_assets_count?.buckets.total_new_count?.doc_count||0,total_in_scope_count:e.aggs.coverage_assets_count?.buckets.total_in_scope_count?.doc_count||0,total_out_of_scope_count:e.aggs.coverage_assets_count?.buckets.total_out_of_scope_count?.doc_count||0,total_untested_count:e.aggs.coverage_assets_count?.buckets.total_untested_count?.doc_count||0,total_archived_count:e.aggs.total_count?.buckets.archived?.doc_count||0}),qi=`/assets/static/empty_search_results-BD7L3Pta.svg`,Ji=()=>(0,q.jsxs)(`div`,{className:`flex flex-col items-center py-2xl`,children:[(0,q.jsx)(`div`,{className:`overflow-hidden mb-l`,children:(0,q.jsx)(fe,{src:qi})}),(0,q.jsx)(`span`,{className:`text-center w-1/2 text-neutral-100 text-2xl dark:text-neutral-950`,children:`No results`}),(0,q.jsx)(`span`,{className:`text-center w-1/2 text-neutral-100 dark:text-neutral-950`,children:`Try a different search term`})]}),Yi=({organization:e})=>{let{dispatch:t}=(0,J.useContext)($);return(0,q.jsx)(y,{icon:`targeted_scope`,header:`No assets in this category!`,description:`Add or update assets to keep your inventory organized and simplify your attack surface management.`,primaryButton:{children:`Add an asset`,renderAs:ve.Link,onClick:()=>{t({type:X.SET_SHOW_ADD_ASSET_MODAL,value:!0})}},secondaryButton:{children:`Learn more`,renderAs:ve.Link,external:!0,openNewTab:!0,to:`https://docs.hackerone.com/en/articles/8486230-asset-inventory`,icons:{right:{src:Le}}}})};Yi.propTypes={organization:K.default.object.isRequired};var{ASSET_TAG_REWARD_CATEGORIES:Xi}=window.constants.featureToggles,Zi=100,Qi=()=>{let{store:e,organization:t,organization:{asset_package:{risks_enabled:n}},countsData:r}=(0,J.useContext)($),{currentPage:i,searchTerm:a}=e,{data:o,loading:s}=U(Je,{variables:{...Li({store:e,organization:t,debounced:!0}),from:i*Zi,size:Zi},fetchPolicy:`network-only`}),c=a?(0,q.jsx)(Ji,{}):(0,q.jsx)(Yi,{organization:t}),l=o?o.organizations.nodes[0].assets_search:{nodes:[]},u=r?Ki(r.organizations.nodes[0].assets_search):Gi,d=e.selectedTab===`archived`,f=e.selectedTab===`untested`,{enabled:p}=B(Xi,t.handle),m=o?o.organizations.nodes[0].has_gateway_teams:!1;return(0,q.jsxs)(q.Fragment,{children:[(0,q.jsx)(Ci,{showSelectAllToggle:l.nodes.length>0,assetsDataObject:l,loading:s,pageSize:Zi,hasGateway:m}),(0,q.jsx)(Wi,{assetCounts:u}),s?(0,q.jsx)(wi,{numberOfRows:Zi}):l.nodes.length===0?c:(0,q.jsxs)(I,{fixed:!0,separate:!0,className:`spec-assets-table`,children:[(0,q.jsx)(I.Head,{className:`text-sm`,children:(0,q.jsxs)(I.Row,{children:[n?(0,q.jsxs)(I.CellHeader,{width:140,children:[(0,q.jsx)(`span`,{className:`align-middle ml-spacing-8`,children:`Risk rating`}),` `,(0,q.jsx)(N,{text:`The highest rating identified for this asset`,children:(0,q.jsx)(`span`,{className:`text-white align-middle h-[25px] ml-spacing-4 text-neutral-500 dark:text-neutral-950`,children:(0,q.jsx)(P,{src:Ke,size:`md`})})})]}):(0,q.jsx)(I.CellHeader,{width:50}),(0,q.jsx)(I.CellHeader,{width:300,children:`Asset name`}),!d&&!f&&(0,q.jsx)(I.CellHeader,{children:`Programs`}),(0,q.jsx)(I.CellHeader,{width:120,className:`whitespace-nowrap`,children:`Open Vulnerabilities`}),p&&!d&&!f&&(0,q.jsx)(I.CellHeader,{children:`Tags`}),(0,q.jsx)(I.CellHeader,{width:220,className:`actions`})]})}),(0,q.jsx)(I.Body,{children:l.nodes.map(e=>(0,q.jsx)(ji,{asset:e,organization:t},e.id))})]}),(0,q.jsx)(`div`,{className:`justify-end p-md pr-0 border-b border-solid border-neutral-700 dark:border-neutral-50 relative`,children:(0,q.jsx)(ni,{loading:s,paginationInfoObject:l,pageSize:Zi})})]})},$i=`data:image/svg+xml,%3csvg%20xmlns='http://www.w3.org/2000/svg'%20width='24'%20height='24'%20viewBox='0%200%2024%2024'%3e%3cpath%20d='M9.17%206l2%202H20v10H4V6h5.17M10%204H4c-1.1%200-1.99.9-1.99%202L2%2018c0%201.1.9%202%202%202h16c1.1%200%202-.9%202-2V8c0-1.1-.9-2-2-2h-8l-2-2z'/%3e%3c/svg%3e`,ea=`data:image/svg+xml,%3csvg%20xmlns='http://www.w3.org/2000/svg'%20width='24'%20height='24'%20viewBox='0%200%2024%2024'%3e%3cpath%20d='M20%206h-8l-2-2H4c-1.1%200-1.99.9-1.99%202L2%2018c0%201.1.9%202%202%202h16c1.1%200%202-.9%202-2V8c0-1.1-.9-2-2-2zm0%2012H4V8h16v10z'/%3e%3c/svg%3e`;F();var{ASSET_TAG_REWARD_CATEGORIES:ta}=window.constants.featureToggles,na=100,ra=f`
  query AssetGroupAssetsQuery(
    $handle: String!
    $coverage: AssetCoverageEnum
    $defaultGroupNames: [String]
    $tagNames: [String]
    $missingTagForCategory: String
    $searchString: String
    $programIds: [Int]
    $assetTypes: [AssetImplementationTypeEnum]
    $asmTagIds: [Int]
    $asmTagCategoryClauses: [AssetTagCategoryClauseInput]
    $ports: [AssetPortFilterInputType]
    $from: Int
    $size: Int
    $archived: Boolean
  ) {
    organizations(first: 1, where: { handle: { _eq: $handle } }) {
      nodes {
        id
        assets_search(
          search_string: $searchString
          team_ids: $programIds
          asset_types: $assetTypes
          asm_tag_ids: $asmTagIds
          asm_tag_category_clauses: $asmTagCategoryClauses
          ports: $ports
          coverage: $coverage
          from: $from
          size: $size
          default_group_names: $defaultGroupNames
          tag_names: $tagNames
          missing_tag_for_category: $missingTagForCategory
          archived: $archived
          state: confirmed
        ) {
          nodes {
            ... on AssetDocument {
              id
              ...AssetInventoryAssetDocumentFragment
            }
          }
          pageInfo {
            startCursor
            hasPreviousPage
            endCursor
            hasNextPage
          }
          total_count
        }
      }
    }
  }
  ${mt}
`,ia=({groupedBy:e,groupKey:t,assetsCount:n,organization:r,setGroupAssets:i})=>{let[a,o]=(0,J.useState)(0),{store:s,organization:{asset_package:c}}=(0,J.useContext)($),l=c?.risks_enabled,{enabled:u}=B(ta,r.handle),{data:d,loading:f}=U(ra,{variables:{from:a*na,size:na,defaultGroupNames:e===`DEFAULT`?[t]:[],tagNames:e===`DEFAULT`?[]:[t],missingTagForCategory:t?null:e,...Li({store:s,organization:r,debounced:!0})}}),p=d?.organizations.nodes[0].assets_search.nodes,m=s.selectedTab===`archived`,h=s.selectedTab===`untested`;return(0,J.useEffect)(()=>{i(p||[])},[d]),(0,q.jsxs)(I,{fixed:!0,striped:!0,className:`assets-table-row spec-assets-table-row border-solid border border-neutral-700 dark:border-white shadow`,children:[(0,q.jsx)(I.Head,{className:`text-sm`,children:(0,q.jsxs)(I.Row,{children:[!m&&l?(0,q.jsxs)(I.CellHeader,{width:130,children:[(0,q.jsx)(`span`,{className:`align-middle ml-spacing-8`,children:`Risk rating`}),` `,(0,q.jsx)(N,{text:`The highest rating identified for this asset`,children:(0,q.jsx)(`span`,{className:`align-middle h-[25px] ml-spacing-4 text-neutral-500 dark:text-neutral-950`,children:(0,q.jsx)(P,{src:Ke,size:`md`,accessibilityLabel:`info`})})})]}):(0,q.jsx)(I.CellHeader,{width:50}),(0,q.jsx)(I.CellHeader,{width:300,children:`Identifier`}),(0,q.jsx)(I.CellHeader,{children:!m&&!h&&`Programs`}),(0,q.jsx)(I.CellHeader,{width:120,children:!m&&`Open Vulnerabilities`}),u&&!m&&!h&&(0,q.jsx)(I.CellHeader,{children:`Tags`}),(0,q.jsx)(I.CellHeader,{width:250,className:`actions`,children:(0,q.jsx)(j,{currentPage:a,previousPageLabel:`Previous asset group page`,nextPageLabel:`Next asset group page`,onClickNext:()=>{$e.track(`asset group assets next page clicked`,{category:window.constants.analytics.asset_inventory}),o(a+1)},onClickPrevious:()=>{$e.track(`asset group assets previous page clicked`,{category:window.constants.analytics.asset_inventory}),o(a-1)},disabled:f,itemsPerPage:na,totalItems:n,alignment:`right`})})]})}),(0,q.jsx)(I.Body,{children:f?[...Array(Math.min(n,100))].map((e,t)=>(0,q.jsx)(Mi,{},t)):p.map(e=>(0,q.jsx)(ji,{asset:e,organization:r},e.id))})]})};ia.propTypes={name:K.default.string.isRequired,groupKey:K.default.string,groupedBy:K.default.string.isRequired,assetsCount:K.default.number.isRequired,organization:K.default.object.isRequired,setGroupAssets:K.default.func.isRequired};var aa=({coverageItemsCount:e,totalCount:t,color:n})=>(0,q.jsx)(`div`,{className:`w-[30px] h-[8px]`,children:(0,q.jsx)(ee,{progress:e>0?Math.max(e/t*100,10):0,color:n})});aa.propTypes={coverageItemsCount:K.default.number.isRequired,totalCount:K.default.number.isRequired,color:K.default.string.isRequired};var oa=({groupedBy:e,data:t,organization:n})=>{let[r,i]=(0,J.useState)(!1),[a,o]=(0,J.useState)([]),{store:{selectedTab:c,checkedAssets:l},dispatch:u}=(0,J.useContext)($),d=c===`archived`,f=t.newCount>0,p=0,h=0,g=0,_=0;switch(c){case constants.assetInventory.coverageTypes.inScope:p=h=t.inScopeCount;break;case constants.assetInventory.coverageTypes.outOfScope:p=g=t.outOfScopeCount;break;case constants.assetInventory.coverageTypes.new:case constants.assetInventory.coverageTypes.untested:p=_=t.untestedCount;break;default:p=t.assetsCount,h=t.inScopeCount,g=t.outOfScopeCount,_=t.untestedCount;break}let v=a.filter(e=>l.includes(Number(e.databaseId))),y=a.length>0&&v.length===a.length,b=v.length>0,x=()=>{u({type:X.TOGGLE_CHECK_ASSET_GROUP,value:a})};return(0,q.jsxs)(q.Fragment,{children:[(0,q.jsxs)(I.Row,{className:(0,Bn.default)(`spec-assets-group-row shadow`,r?`rounded-t`:`rounded`),children:[(0,q.jsx)(I.Cell,{width:50,className:(0,Bn.default)(`dark:bg-black`,`pl-spacing-20`,`pr-spacing-0`,r&&`rounded-b-none`),children:(0,q.jsx)(`div`,{className:`w-lg spec-asset-row-checkbox`,children:r&&(0,q.jsx)(le,{name:`asset-${t.name}`,checked:y,onChange:()=>{x()},indeterminate:b&&!y})})}),(0,q.jsx)(I.Cell,{width:285,className:`dark:bg-black`,children:(0,q.jsx)(`div`,{className:`w-[280px] max-w-full`,children:(0,q.jsxs)(`a`,{href:`asset_inventory/assets_group_row#`,className:`truncate spec-group-identifier flex items-center`,onClick:e=>{e.preventDefault(),i(!r)},children:[(0,q.jsx)(`div`,{className:`inline mr-spacing-8 -mt-spacing-4 text-neutral-50 dark:text-neutral-950`,children:(0,q.jsx)(P,{src:r?ea:$i,size:`md`,scale:1.2})}),t.name]})})}),(0,q.jsx)(I.Cell,{width:126,className:`dark:bg-black min-w-[126px]`,children:f?(0,q.jsx)(C,{testId:`spec-new-asset`,color:`blue`,rounded:!1,children:`New`}):null}),(0,q.jsx)(I.Cell,{width:`99%`,className:`dark:bg-black`,children:(0,q.jsx)(`span`,{className:`text-sm font-bold`,children:p?`${p} asset${p===1?``:`s`}`:null})}),!d&&(0,q.jsxs)(q.Fragment,{children:[(0,q.jsx)(I.Cell,{className:`dark:bg-black pr-spacing-0 pl-spacing-16 whitespace-nowrap`,children:(0,q.jsxs)(`div`,{className:`flex justify-start items-center gap-xs`,children:[(0,q.jsx)(aa,{coverageItemsCount:h,totalCount:p,color:m.Green}),(0,q.jsxs)(`div`,{className:`text-sm whitespace-nowrap`,children:[`In scope (`,h,`)`]})]})}),(0,q.jsx)(I.Cell,{className:`dark:bg-black pr-spacing-0 pl-spacing-16 whitespace-nowrap`,children:(0,q.jsxs)(`div`,{className:`flex justify-start items-center gap-xs`,children:[(0,q.jsx)(aa,{coverageItemsCount:g,totalCount:p,color:m.Yellow}),(0,q.jsxs)(`div`,{className:`text-sm whitespace-nowrap`,children:[`Out of scope (`,g,`)`]})]})}),(0,q.jsx)(I.Cell,{className:`dark:bg-black pr-spacing-0 pl-spacing-16 whitespace-nowrap`,children:(0,q.jsxs)(`div`,{className:`flex justify-start items-center gap-xs`,children:[(0,q.jsx)(aa,{coverageItemsCount:_,totalCount:p,color:m.Gray}),(0,q.jsxs)(`div`,{className:`text-sm whitespace-nowrap`,children:[`Untested (`,_,`)`]})]})})]}),(0,q.jsx)(I.Cell,{width:50,className:(0,Bn.default)(`dark:bg-black`,`py-spacing-0`,`px-spacing-12`,r&&`rounded-b-none`),children:(0,q.jsx)(`div`,{className:`flex justify-end`,children:(0,q.jsx)(T,{iconOnly:!0,icons:{center:{accessibilityLabel:r?`Collapse`:`Expand`,src:r?Ne:s}},onClick:()=>i(!r),variation:`ghost-secondary`})})})]},`assets-group-${t.name}`),r&&(0,q.jsx)(I.Row,{className:`asset`,children:(0,q.jsx)(I.Cell,{colSpan:9,className:`no-padding-important border-none dark:bg-black`,children:(0,q.jsx)(ia,{name:t.name,groupKey:t.groupKey,groupedBy:e,assetsCount:p,organization:n,setGroupAssets:e=>{o(e),u({type:X.TOGGLE_CHECK_ASSET_GROUP,value:v})}})})},`assets-${t.name}`)]})};oa.propTypes={data:K.default.shape({name:K.default.string.isRequired,assetsCount:K.default.number.isRequired,inScopeCount:K.default.number.isRequired,outOfScopeCount:K.default.number.isRequired,untestedCount:K.default.number.isRequired,newCount:K.default.number.isRequired,groupKey:K.default.string}).isRequired,groupedBy:K.default.oneOf([`DEFAULT`,`CATEGORY`]).isRequired,organization:K.default.object.isRequired},F();var sa=100,ca=`Uncategorized`,la=f`
  query AssetGroupCountsQuery(
    $handle: String!
    $searchString: String
    $programIds: [Int]
    $assetTypes: [AssetImplementationTypeEnum]
    $asmTagCategoryClauses: [AssetTagCategoryClauseInput]
    $ports: [AssetPortFilterInputType]
  ) {
    organizations(first: 1, where: { handle: { _eq: $handle } }) {
      nodes {
        id
        assets_search(
          search_string: $searchString
          team_ids: $programIds
          asset_types: $assetTypes
          asm_tag_category_clauses: $asmTagCategoryClauses
          ports: $ports
          state: confirmed
        ) {
          total_count
          aggs
        }
      }
    }
  }
`,ua=f`
  query AssetGroupSearchQuery(
    $handle: String!
    $coverage: AssetCoverageEnum
    $searchString: String
    $programIds: [Int]
    $assetTypes: [AssetImplementationTypeEnum]
    $asmTagCategoryClauses: [AssetTagCategoryClauseInput]
    $ports: [AssetPortFilterInputType]
    $group: String!
    $count: Int
    $archived: Boolean
  ) {
    organizations(first: 1, where: { handle: { _eq: $handle } }) {
      nodes {
        id
        has_gateway_teams
        assets_search(
          # Keep in sync with export_assets_mutation.rb so that assets export reflects these filters
          search_string: $searchString
          team_ids: $programIds
          asset_types: $assetTypes
          asm_tag_category_clauses: $asmTagCategoryClauses
          ports: $ports
          coverage: $coverage
          group: $group
          size: $count
          archived: $archived
          state: confirmed
        ) {
          aggs
        }
      }
    }
  }
`,da=()=>{let{store:e,organization:t}=(0,J.useContext)($),{selectedAssetsGroupMode:n,searchTerm:r}=e,{data:i,loading:a,fetchMore:o}=U(ua,{variables:{...Li({store:e,organization:t,debounced:!0}),group:n,count:sa},fetchPolicy:`network-only`}),s=()=>{$e.track(`asset groups more loaded`,{load_asset_groups_count:h.length+sa}),o({variables:{count:h.length+sa},updateQuery:(e,{fetchMoreResult:t})=>t})},{data:c,loading:l}=U(la,{variables:Ii({store:e,organization:t,debounced:!0}),fetchPolicy:`network-only`}),u=l||!c?Gi:Ki(c.organizations.nodes[0].assets_search),d=i?.organizations.nodes[0].assets_search,f=i?.organizations.nodes[0].has_gateway_teams,p=n===`DEFAULT`?d?.aggs?.grouped:d?.aggs?.grouped?.asm_tag_category?.asm_tag,m=d?.aggs?.uncategorized,h=p?.buckets,g=p?.buckets?.length+p?.sum_other_doc_count,_=h?.length,v=r?(0,q.jsx)(Ji,{}):(0,q.jsx)(Yi,{organization:t});return(0,q.jsxs)(q.Fragment,{children:[(0,q.jsx)(Ci,{loadMoreGroups:s,assetsDataObject:{total_count:g,current_count:_},loading:a,pageSize:sa,isGroupedView:!0,hasGateway:f}),(0,q.jsx)(Wi,{assetCounts:u}),a?(0,q.jsx)(wi,{numberOfRows:sa}):h?.length>0||m?.doc_count>0?(0,q.jsx)(I,{separate:!0,className:`border-spacing-12--bottom spec-assets-table`,children:(0,q.jsxs)(I.Body,{children:[m?.doc_count>0&&(0,q.jsx)(oa,{groupedBy:n,organization:t,data:{name:ca,inScopeCount:m.coverage_assets_count.buckets.total_in_scope_count.doc_count,outOfScopeCount:m.coverage_assets_count.buckets.total_out_of_scope_count.doc_count,newCount:m.coverage_assets_count.buckets.total_new_count.doc_count,untestedCount:m.coverage_assets_count.buckets.total_untested_count.doc_count,assetsCount:m.doc_count}},`uncategorized`),h?.map(e=>{let r=n===`DEFAULT`?e.coverage_assets_count.buckets:e.unnested.coverage_assets_count.buckets;return(0,q.jsx)(oa,{data:{inScopeCount:r.total_in_scope_count.doc_count,outOfScopeCount:r.total_out_of_scope_count.doc_count,newCount:r.total_new_count.doc_count,untestedCount:r.total_untested_count.doc_count,assetsCount:e.doc_count,name:e.key,groupKey:n===`DEFAULT`?e.key:`${n}::${e.key}`},groupedBy:n,organization:t},e.key)})]})}):v]})};da.fragments={organization:f`
    fragment AssetGroupsTableOrganizationFragment on Organization {
      id
      ...AssetActionsOrganizationFragment
    }
    ${Ci.fragments.organization}
  `},F();var fa=()=>{let{store:e}=(0,J.useContext)($),{selectedAssetsGroupMode:t}=e;return t===`NONE`?(0,q.jsx)(Qi,{}):(0,q.jsx)(da,{})};fa.fragments={organization:f`
    fragment AssetsTableWrapperOrganizationFragment on Organization {
      id
      ...AssetGroupsTableOrganizationFragment
    }
    ${da.fragments.organization}
  `},F();var pa=[{value:`severe`,label:`Severe`,grades:[`D`]},{value:`major`,label:`Major`,grades:[`C`]},{value:`moderate`,label:`Moderate`,grades:[`B`]},{value:`minimal`,label:`Minimal`,grades:[`A`]}],ma={D:`severe`,C:`major`,B:`moderate`,A:`minimal`},ha=({availablePorts:e,availableDomains:t})=>{let{organization:n,store:{selectedProgramIds:r,selectedAssetTypes:i,selectedAsmTagIds:a,selectedTagCategoryClauses:o,selectedPorts:s,selectedProtocols:c,selectedAiRiskRatings:l,selectedDomains:u,showFiltersSheet:d},dispatch:f}=(0,J.useContext)($),p=n?.features?.some(e=>e.key===`asset-scanner-beta`);return(0,q.jsx)(At,{isOpen:d,onClose:()=>f({type:X.SET_SHOW_FILTERS_SHEET,value:!1}),organization:n,selectedProgramIds:r,selectedAssetTypes:i,selectedAsmTagIds:a,selectedTagCategoryClauses:o,selectedPorts:s,selectedProtocols:c,selectedAiRiskRatings:(0,J.useMemo)(()=>{if(!l||l.length===0)return[];let e=new Set;for(let t of l){let n=ma[t];n&&e.add(n)}return Array.from(e)},[l]),availablePorts:e,assetScannerBetaEnabled:p,onClearFilters:()=>f({type:X.CLEAR_SEARCH_FILTERS}),onProgramFilterChange:e=>f({type:X.SET_SELECTED_PROGRAMS,value:e}),onAssetTypeFilterChange:e=>f({type:X.SET_SELECTED_ASSET_TYPES,value:e}),onAsmTagFilterChange:(e,t)=>f({type:X.SET_SELECTED_ASM_TAG_IDS,value:{...a,[e]:t}}),onTagCategoryClauseChange:(e,t)=>f({type:X.SET_TAG_CATEGORY_CLAUSES,value:{...o,[e]:t}}),onPortFilterChange:e=>f({type:X.SET_SELECTED_PORTS,value:e}),onProtocolFilterChange:e=>f({type:X.SET_SELECTED_PROTOCOLS,value:e}),onAiRiskRatingFilterChange:e=>{let t=e.flatMap(e=>pa.find(t=>t.value===e)?.grades||[]);f({type:X.SET_SELECTED_AI_RISK_RATINGS,value:t})},selectedDomains:u||[],availableDomains:t||[],onDomainFilterChange:e=>f({type:X.SET_SELECTED_DOMAINS,value:e}),exposureSignalOptions:pa.map(({value:e,label:t})=>({value:e,label:t})),filterCategories:window.constants.assetInventory.filterCategories,tagClauseOptions:window.constants.assetInventory.tagClauses,assetTypeOptions:window.constants.assetInventory.assetTypes})};ha.fragments={organization:f`
    fragment FilterSheetOrganizationFragment on Organization {
      id
      asset_types
      features {
        id
        key
      }
      asm_tag_categories {
        nodes {
          id
          databaseId: _id
          name
          system
          asm_tags {
            nodes {
              id
              databaseId: _id
              name
            }
          }
        }
      }
      teams {
        nodes {
          id
          databaseId: _id
          name
        }
      }
    }
  `},ha.propTypes={availablePorts:K.PropTypes.array,availableDomains:K.PropTypes.array},ha.defaultProps={availablePorts:[],availableDomains:[]},F();var ga=f`
  query GroupAssetsDropdownQuery($handle: String!) {
    organizations(first: 1, where: { handle: { _eq: $handle } }) {
      nodes {
        id
        asm_tag_categories {
          nodes {
            id
            name
          }
        }
      }
    }
  }
`,_a=[{value:`NONE`,label:`No grouping`},{value:`DEFAULT`,label:`Default`}],va=()=>{let{organization:e,store:{selectedAssetsGroupMode:n},dispatch:r}=(0,J.useContext)($),{data:i}=U(ga,{variables:{handle:e.handle}}),a=[..._a,...i?.organizations.nodes[0].asm_tag_categories.nodes.map(({name:e})=>({value:e,label:e}))??[]];return(0,q.jsxs)(`div`,{className:`flex flex-col ml-spacing-16 min-w-[200px]`,children:[(0,q.jsx)(t,{text:`Grouping`}),(0,q.jsx)(x,{top:`2xs`}),(0,q.jsx)(De,{testId:`spec-group-assets-dropdown`,selectedOption:a.find(({value:e})=>e===n),placeholder:`Grouping`,options:a,onChange:e=>{r({type:X.SET_SELECTED_ASSETS_GROUP_MODE,value:e.value})}})]})},ya=({pageName:e})=>(0,q.jsx)(gt,{content:(0,q.jsx)(y,{icon:`lock_shield`,header:`Sorry! You don't have access to this page.`,description:`You or your organization must be granted access before viewing ${e}.`,secondaryButton:{children:`Learn more`,renderAs:ve.Link,external:!0,openNewTab:!0,to:`https://docs.hackerone.com/en/articles/8486230-asset-inventory`,icons:{right:{src:Le}}}})});F();var $=J.createContext(),ba=f`
  query AssetsSearchCountsQuery(
    $handle: String!
    $searchString: String
    $programIds: [Int]
    $assetTypes: [AssetImplementationTypeEnum]
    $asmTagCategoryClauses: [AssetTagCategoryClauseInput]
    $ports: [AssetPortFilterInputType]
  ) {
    organizations(first: 1, where: { handle: { _eq: $handle } }) {
      nodes {
        id
        assets_search(
          search_string: $searchString
          team_ids: $programIds
          asset_types: $assetTypes
          asm_tag_category_clauses: $asmTagCategoryClauses
          ports: $ports
          state: confirmed
        ) {
          aggs
        }
      }
    }
  }
`,xa=f`
  query OrganizationAssetsOverviewQuery($handle: String!) {
    organizations(first: 1, where: { handle: { _eq: $handle } }) {
      nodes {
        id
        handle
        name
        asset_package {
          id
          risks_enabled
          dns_enabled
          attachments_enabled
        }
        i_can_manage_organization_assets
        i_am_asset_inventory_manager
        i_can_create_spot_checks
        i_can_view_organization_assets
        scope_management_teams {
          nodes {
            id
          }
        }
        ...AssetsTableWrapperOrganizationFragment
        ...FilterSheetOrganizationFragment
      }
    }
    me {
      ...AssetInventoryExportAssetsFragment
    }
  }
  ${fa.fragments.organization}
  ${ha.fragments.organization}
  ${Bi.fragments.me}
`,Sa=({match:e})=>{let[t,n]=(0,J.useReducer)(Cn,Z),{organizationHandle:r,coverage:i}=e.params,{data:o,networkStatus:s}=U(xa,{notifyOnNetworkStatusChange:!0,variables:{handle:r},fetchPolicy:`cache-and-network`,errorPolicy:`ignore`}),c=o?.organizations?.nodes?.[0],l=Ii({store:t,organization:c||{handle:r,asm_tag_categories:{nodes:[]}},debounced:!1}),{data:u}=U(ba,{skip:!c,variables:l,fetchPolicy:`cache-and-network`});if(s===1&&!o||!o)return(0,q.jsx)(et,{});let d=o.me;if(!c)return null;if(!c.i_can_view_organization_assets)return(0,q.jsx)(ya,{pageName:`Asset Inventory`});let f=u?.organizations?.nodes?.[0]?.assets_search?.aggs,p=Array.from(new Set(f?.available_ports?.unique_ports?.buckets?.map(e=>e.key)||[])).sort((e,t)=>e-t),m=+!!t.selectedProgramIds.length+ +!!t.selectedAssetTypes.length+ +!!t.selectedPorts.length+ +!!t.selectedProtocols.length+Object.keys(t.selectedTagCategoryClauses).length;return(0,q.jsx)(w,{children:(0,q.jsxs)($.Provider,{value:{store:t,organization:c,me:d,coverage:i,dispatch:n,countsData:u},children:[(0,q.jsx)(h,{children:(0,q.jsx)(`title`,{children:`${c.name} - Asset Inventory`})}),(0,q.jsx)(`div`,{className:`mx-auto w-full max-w-[1920px] p-spacing-24 gap-spacing-24 flex flex-col`,children:(0,q.jsxs)(ge,{padding:`lg`,fill:!0,border:!1,children:[(0,q.jsx)(Ce,{children:(0,q.jsxs)(`div`,{className:`flex justify-between`,children:[(0,q.jsxs)(`div`,{className:`flex flex-col grow`,children:[t.selectedAssetId&&(0,q.jsx)(tr,{close:()=>{n({type:X.SET_SELECTED_ASSET_ID,value:null})},canManage:(c.i_am_asset_inventory_manager||c.i_can_manage_organization_assets)&&t.selectedTab!==`archived`,contextToUse:$}),(0,q.jsx)(a,{value:t.searchTerm,labelText:`Search your inventory`,placeholder:`Search`,type:`search`,name:`asset-search`,icons:{left:{src:we,accessibilityLabel:`Search`}},onChange:e=>n({value:e.target.value,type:X.SET_SEARCH_TERM})})]}),(0,q.jsx)(va,{}),(0,q.jsxs)(`div`,{className:`flex filter-button-wrapper ml-spacing-16 mt-spacing-28 w-[40px]`,children:[(0,q.jsx)(T,{variation:`tertiary`,testId:`spec-filter-toggler`,onClick:()=>{n({type:X.SET_SHOW_FILTERS_SHEET,value:!0})},iconOnly:!0,icons:{center:{src:Dt,accessibilityLabel:`Filter`}},fill:!0}),m>0&&(0,q.jsx)(`div`,{className:`count-bubble spec-filtered-categories-count`,children:(0,q.jsx)(C,{color:`blue`,size:`sm`,children:m})})]})]})}),(0,q.jsx)(ha,{availablePorts:p})]})}),(0,q.jsxs)(x,{horizontal:`24`,children:[(0,q.jsx)(x,{bottom:`24`,children:(0,q.jsx)(fa,{})}),(0,q.jsx)(Be,{})]})]})})};Sa.propTypes={match:K.default.object.isRequired};export{qn as A,Er as C,mr as D,xr as E,It as F,Z as M,Cn as N,ir as O,Vt as P,kr as S,wr as T,Ur as _,ha as a,Pr as b,wi as c,ui as d,ti as f,Gr as g,qr as h,ya as i,X as j,tr as k,hi as l,Zr as m,xa as n,Bi as o,$r as p,Sa as r,Ti as s,$ as t,pi as u,Br as v,Tr as w,jr as x,Rr as y};
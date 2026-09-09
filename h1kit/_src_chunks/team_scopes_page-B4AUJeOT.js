import{o as e}from"./rolldown-runtime-DAXXjFlN.js";import{$_ as t,Ca as n,Cp as r,Fw as i,Kx as a,Ma as o,Pf as s,Qd as c,Qy as l,Rw as u,Vb as d,Wd as f,Y_ as p,bb as m,cp as h,cv as g,lp as _,lv as v,ma as y,ov as b,pu as x,qx as S,sd as C,ua as w,zx as T}from"./vendor-_WdvpBLr.js";import{Jc as E,Ju as ee,Oo as D,Pf as O,Sd as k,Sh as A,Sm as j,T as M,Th as N,Uc as te,V as ne,W as re,Wi as ie,_h as P,df as ae,ep as F,k as oe,qr as se,vh as I,vm as L,wo as ce,ym as R}from"./app-5pKgUmmm.js";import{C as le,D as ue,c as de,k as fe,s as pe}from"./assets_overview-gAIT_Z1N.js";import{t as me}from"./moment-gwVCHLJU.js";var z=e(u()),B=e(T()),V={SET_SEARCH_TERM:`SET_SEARCH_TERM`,SET_SCOPE_DESCRIPTION:`SET_SCOPE_DESCRIPTION`,TOGGLE_SELECT:`TOGGLE_SELECT`,TOGGLE_SELECT_ALL:`TOGGLE_SELECT_ALL`,SET_CURRENT_PAGE:`SET_CURRENT_PAGE`,SET_SORTING:`SET_SORTING`,SET_SELECTED_ASSET_ID:`SET_SELECTED_ASSET_ID`,SET_ASSET_SIDEBAR_TAB_INDEX:`SET_ASSET_SIDEBAR_TAB_INDEX`,SET_SHOW_ADD_ASSETS_MODAL:`SET_SHOW_ADD_ASSETS_MODAL`,SET_SELECTED_CATEGORY_ID:`SET_SELECTED_CATEGORY_ID`,SET_SELECTED_TAG_IDS:`SET_SELECTED_TAG_IDS`},he={searchTerm:``,selectedIds:[],currentPage:0,sortingField:`created_at`,sortingDirection:`DESC`,selectedAssetId:null,assetSidebarTabIndex:0,showAddAssetsModal:!1,selectedCategoryId:null,selectedTagIds:[]},H=(e,t)=>Array.isArray(e)?e:t.includes(e)?t.filter(t=>t!==e):[...t,e],U={ASC:`ASC`,DESC:`DESC`},ge=e=>e===U.ASC?U.DESC:U.ASC,_e=(e={},t)=>{switch(t.type){case V.SET_SEARCH_TERM:return{...e,searchTerm:t.value};case V.TOGGLE_SELECT:return{...e,selectedIds:H(t.value,e.selectedIds)};case V.TOGGLE_SELECT_ALL:return{...e,selectedIds:H(t.value,e.selectedIds)};case V.SET_CURRENT_PAGE:return{...e,currentPage:t.value,selectedIds:[]};case V.SET_SORTING:return{...e,sortingField:t.value,sortingDirection:e.sortingField===t.value?ge(e.sortingDirection):U.ASC};case V.SET_SELECTED_ASSET_ID:return{...e,selectedAssetId:t.value};case V.SET_ASSET_SIDEBAR_TAB_INDEX:return{...e,assetSidebarTabIndex:t.value};case V.SET_SHOW_ADD_ASSETS_MODAL:return{...e,showAddAssetsModal:t.value};case V.SET_SELECTED_CATEGORY_ID:return{...e,selectedCategoryId:t.value,selectedTagIds:[],currentPage:0};case V.SET_SELECTED_TAG_IDS:return{...e,selectedTagIds:t.value,currentPage:0};default:return e}};S();var ve=a`
  query RewardCategoriesQuery($orgHandle: String!) {
    organizations(first: 1, where: { handle: { _eq: $orgHandle } }) {
      nodes {
        id
        asm_tag_categories(rewards_eligible: true, include_empty: false) {
          nodes {
            id
            _id
            name
          }
        }
      }
    }
  }
`,ye=a`
  query CategoryTagsQuery($categoryId: ID!, $query: String, $first: Int) {
    node(id: $categoryId) {
      ... on AsmTagCategory {
        id
        asm_tags(first: $first, query: $query) {
          nodes {
            id
            _id
            name
          }
        }
      }
    }
  }
`,W=i(),{ASSET_TAG_REWARD_CATEGORIES:be}=window.constants.featureToggles,xe={value:null,label:(0,W.jsx)(`span`,{className:`text-neutral-400 italic`,children:`No filter`})},Se=50,Ce=()=>{let{store:e,dispatch:r,team:i}=(0,z.useContext)(Z),{enabled:a,loading:o}=ae(be,i.organization?.handle),{data:s}=I(ve,{variables:{orgHandle:i.organization?.handle},skip:!a||o}),c=s?.organizations?.nodes?.[0]?.asm_tag_categories?.nodes||[],l=a===!0&&c.length>0,u=c.find(t=>t._id===e.selectedCategoryId),[d,f]=w(``,300),{data:p,loading:m}=I(ye,{variables:{categoryId:u?.id,query:d||void 0,first:Se},skip:!u}),h=(0,z.useRef)({}),g=(p?.node?.asm_tags?.nodes||[]).map(e=>({value:parseInt(e._id,10),label:e.name}));g.forEach(e=>{h.current[e.value]=e});let _=[xe,...c.map(e=>({value:e._id,label:e.name}))],v=(0,z.useCallback)(e=>(f(e),e),[f]);return(0,W.jsxs)(`div`,{className:l?`flex gap-md items-end`:``,children:[(0,W.jsxs)(`div`,{className:l?`flex-1`:``,children:[l&&(0,W.jsx)(t,{text:`Search`}),(0,W.jsx)(n,{value:e.searchTerm,placeholder:`Search`,type:`search`,name:`asset-search`,icons:{left:{src:x,accessibilityLabel:`Search`}},onChange:e=>{r({value:e.target.value,type:V.SET_SEARCH_TERM}),r({value:0,type:V.SET_CURRENT_PAGE})}})]}),l&&(0,W.jsxs)(W.Fragment,{children:[(0,W.jsxs)(`div`,{className:`flex-1`,children:[(0,W.jsx)(t,{text:`Reward category name`}),(0,W.jsx)(C,{placeholder:`Select a category`,testId:`spec-reward-category-select`,selectedOption:e.selectedCategoryId?_.find(t=>t.value===e.selectedCategoryId):null,options:_,onChange:e=>{h.current={},r({value:e?.value??null,type:V.SET_SELECTED_CATEGORY_ID})}})]}),(0,W.jsxs)(`div`,{className:`flex-1`,children:[(0,W.jsx)(t,{text:`Reward tag name`}),(0,W.jsx)(C,{isMulti:!0,placeholder:`Select one or more tags`,testId:`spec-reward-tag-select`,isLoading:m,selectedOption:e.selectedTagIds.map(e=>h.current[e]).filter(Boolean),options:g,onInputChange:v,onChange:e=>{r({value:e?e.map(e=>e.value):[],type:V.SET_SELECTED_TAG_IDS})},disabled:!e.selectedCategoryId})]})]})]})},G=100,we=({handle:e,teamName:t,showModal:r,setShowModal:i,selectedAssets:a,setSelectedAssets:o,onContinue:s,onCancel:c,onFail:u})=>{let[d,m]=(0,z.useState)(``),h=ie(d,300),[g,_]=(0,z.useState)(0),[v,y]=(0,z.useState)(!1),{data:b,loading:S}=I(D,{variables:{handle:e,searchString:h,from:g*G,size:G,archived:!1,excludeTeams:[t]}}),C=b?b.organizations.nodes[0].assets_search:{nodes:[],total_count:0},w=C.nodes.map(e=>e.databaseId),T=b?.organizations.nodes[0].id,E=b?.organizations.nodes[0].has_gateway_teams,ee=a.length&&w.every(e=>a.includes(e));return v&&T?(0,W.jsx)(ue,{organizationId:T,showModal:!0,setShowModal:y,hasGateway:E,onFail:u,afterCreate:e=>{let t=e.createAsset.asset.description;o([e.createAsset.asset.databaseId]),t&&t.length>0?A.track(`asset was created with description from the modal`,{category:window.constants.analytics.scope_management}):A.track(`asset was created from the modal`,{category:window.constants.analytics.scope_management}),s()}}):(0,W.jsx)(F,{shouldCloseOnEsc:!0,showModal:r,size:`large`,title:`Select assets from your inventory`,handleCloseModal:()=>{i(!1),c()},children:(0,W.jsxs)(`div`,{children:[(0,W.jsxs)(`div`,{className:`flex gap-md mb-lg mt-lg`,children:[(0,W.jsx)(`div`,{className:`search flex-1`,children:(0,W.jsx)(n,{value:d,placeholder:`Search`,type:`search`,name:`asset-search`,icons:{left:{src:x,accessibilityLabel:`Search`}},onChange:e=>{m(e.target.value)}})}),(0,W.jsx)(`div`,{className:`create-asset`,children:(0,W.jsx)(l,{variation:`secondary`,testId:`spec-create-asset-button`,onClick:()=>{y(!0)},children:`Create new asset`})})]}),(0,W.jsx)(`div`,{className:`overflow-y-scroll max-h-[33rem] mb-lg`,children:S?(0,W.jsx)(de,{numberOfRows:G}):C.nodes.length===0?(0,W.jsx)(`div`,{children:`No assets found`}):(0,W.jsxs)(k,{className:`spec-assets-table`,children:[(0,W.jsx)(k.Head,{className:`sticky top-0`,children:(0,W.jsxs)(k.Row,{children:[(0,W.jsx)(k.CellHeader,{width:50,children:(0,W.jsx)(p,{testId:`spec-assets-select-all`,checked:ee,onChange:e=>{e.target.checked?o(Array.from(new Set([...a,...w]))):o([...a.filter(e=>!w.includes(e))])}})}),(0,W.jsx)(k.CellHeader,{width:300,children:`Asset name`}),(0,W.jsxs)(k.CellHeader,{children:[(0,W.jsx)(f,{disabled:S,alignment:`right`,itemsPerPage:G,currentPage:g,onClickPrevious:()=>{_(g-1)},onClickNext:()=>{_(g+1)},totalItems:C.total_count,nextPageLabel:`Next page`,previousPageLabel:`Previous page`}),` `]})]})}),(0,W.jsx)(k.Body,{children:C.nodes.map(e=>(0,W.jsxs)(k.Row,{hoverable:!0,children:[(0,W.jsx)(k.Cell,{width:50,children:(0,W.jsx)(p,{checked:a.includes(e.databaseId),onChange:t=>{t.target.checked?o([...a,e.databaseId]):o(a.filter(t=>t!==e.databaseId))}})}),(0,W.jsx)(k.Cell,{width:300,colSpan:2,children:e.identifier})]},e.id))})]})}),(0,W.jsxs)(`div`,{className:`flex gap-md mt-md place-content-end`,children:[(0,W.jsx)(l,{variation:`secondary`,onClick:()=>{i(!1),c()},testId:`spec-cancel`,children:`Cancel`}),(0,W.jsx)(l,{testId:`spec-continue`,disabled:a.length===0,variation:`primary`,onClick:()=>{s(a)},children:`Continue`})]})]})})};we.propTypes={handle:B.default.string.isRequired,teamName:B.default.string.isRequired,showModal:B.default.bool.isRequired,setShowModal:B.default.func.isRequired,onContinue:B.default.func.isRequired,selectedAssets:B.default.arrayOf(B.default.string),setSelectedAssets:B.default.func.isRequired,onCancel:B.default.func.isRequired,onFail:B.default.func.isRequired};var Te=[{label:`In scope`,value:`true`},{label:`Out of scope`,value:`false`}],Ee=[{label:`Yes`,value:`true`},{label:`No`,value:`false`}],K=({eligibleForSubmission:e,onEligibleForSubmissionChange:n,eligibleForBounty:r,onEligibleForBountyChange:i,instruction:a,onInstructionChange:o,showInstruction:s=!0,disabled:c=!1,placeholder:l=null,scopeLabel:u=`Scope status`,scopeTestId:d=`spec-select-scope`,bountyTestId:f=`spec-select-bounty`,layout:p=`horizontal`})=>{let m=({value:e})=>{n(e),e===`false`&&i(`false`)},h=Te.find(t=>t.value===e),g=Ee.find(e=>e.value===r),_=p===`horizontal`?`flex gap-lg`:`flex flex-col gap-lg`,y=p===`horizontal`?`flex-1`:``;return(0,W.jsxs)(W.Fragment,{children:[(0,W.jsxs)(`div`,{className:_,children:[(0,W.jsxs)(`div`,{className:y,children:[(0,W.jsx)(t,{htmlFor:`select-scope`,text:u}),(0,W.jsx)(`div`,{onClick:e=>e.stopPropagation(),children:(0,W.jsx)(C,{id:`select-scope`,testId:d,selectedOption:h,placeholder:l,onChange:m,options:Te,isDisabled:c})})]}),(0,W.jsxs)(`div`,{className:y,children:[(0,W.jsx)(t,{htmlFor:`select-bounty`,text:`Bounty eligible`}),(0,W.jsx)(`div`,{onClick:e=>e.stopPropagation(),children:(0,W.jsx)(C,{id:`select-bounty`,testId:f,selectedOption:g,placeholder:l,onChange:({value:e})=>i(e),options:Ee,isDisabled:c})})]})]}),s&&(0,W.jsxs)(`div`,{className:`mt-lg`,children:[(0,W.jsx)(t,{text:`Instructions`,htmlFor:`instruction-input`,id:`instruction-input-label`}),(0,W.jsx)(`p`,{className:`text-neutral-300 dark:text-neutral-800 text-sm mb-sm`,children:`Guide hackers on what to expect or not for this asset.`}),(0,W.jsx)(v,{value:a,testId:`spec-instruction-input`,rows:5,onChange:e=>o(e.target.value),id:`instruction-input`,className:`spec-instruction-input`,labelledBy:`instruction-input-label`,disabled:c})]})]})};K.propTypes={eligibleForSubmission:B.default.string.isRequired,onEligibleForSubmissionChange:B.default.func.isRequired,eligibleForBounty:B.default.string.isRequired,onEligibleForBountyChange:B.default.func.isRequired,instruction:B.default.string,onInstructionChange:B.default.func,showInstruction:B.default.bool,disabled:B.default.bool,placeholder:B.default.string,scopeLabel:B.default.string,scopeTestId:B.default.string,bountyTestId:B.default.string,layout:B.default.oneOf([`horizontal`,`vertical`])};var De=({showInstruction:e,showModal:n,setShowModal:r,onBack:i,onAdd:a,onCancel:o})=>{let[s,c]=(0,z.useState)(``),[u,d]=(0,z.useState)(``),[f,p]=(0,z.useState)(``);return(0,W.jsxs)(F,{shouldCloseOnEsc:!0,showModal:n,size:`medium`,title:`Add scope details`,handleCloseModal:()=>{r(!1),o()},children:[(0,W.jsx)(`div`,{className:`mb-md mt-lg w-3/5`,children:(0,W.jsx)(K,{eligibleForSubmission:u,onEligibleForSubmissionChange:d,eligibleForBounty:f,onEligibleForBountyChange:p,showInstruction:!1,placeholder:`Select an option`,scopeLabel:`Define scope`,scopeTestId:`spec-select-asset-scope`,bountyTestId:`spec-select-elgible-for-bounty`,layout:`vertical`})}),e&&(0,W.jsx)(`div`,{className:`mb-md mt-lg`,children:(0,W.jsxs)(`div`,{className:`mt-md`,children:[(0,W.jsx)(t,{htmlFor:`id-of-some-form-field-element`,text:`Instruction`}),(0,W.jsx)(`p`,{className:`text-neutral-300 dark:text-neutral-800`,children:`Guide hackers on what to expect or not for this asset. This will be visible to the hacker in the program scope page.`}),(0,W.jsx)(`div`,{className:`mt-md`,children:(0,W.jsx)(y,{value:s,onChange:({target:e})=>{c(e.value)}})})]})}),(0,W.jsxs)(`div`,{className:`flex mt-md `,children:[(0,W.jsx)(`div`,{children:(0,W.jsx)(l,{variation:`secondary`,onClick:()=>{i()},testId:`spec-back`,children:`Back`})}),(0,W.jsxs)(`div`,{className:`place-content-end flex flex-1 gap-md`,children:[(0,W.jsx)(l,{variation:`secondary`,onClick:()=>{r(!1),o()},testId:`spec-cancel`,children:`Cancel`}),(0,W.jsx)(l,{testId:`spec-add-scope-details`,disabled:u===``||f===``,variation:`primary`,onClick:()=>{r(!1),a(u,f,s)},children:`Add`})]})]})]})};De.propTypes={showInstruction:B.default.bool.isRequired,showModal:B.default.bool.isRequired,setShowModal:B.default.func.isRequired,onBack:B.default.func.isRequired,onAdd:B.default.func.isRequired,onCancel:B.default.func.isRequired},S();var q=()=>{let{team:e,store:{showAddAssetsModal:t},dispatch:n}=(0,z.useContext)(Z),r=e=>{n({type:V.SET_SHOW_ADD_ASSETS_MODAL,value:e})},[i,a]=(0,z.useState)([]),[o,s]=(0,z.useState)(!1),[c,{loading:u}]=P(le,{refetchQueries:[`ProgramSettingsScopeManagement`],onCompleted:({addAssetsToStructuredScopes:{was_successful:e,errors:t}})=>{if(!e){j(`error`,t.edges.map(e=>e.node.message).join(` `));return}R(),a([])},onError:L}),d=(t,n,r)=>{c({variables:{organizationId:e.organization.id,assetIds:i.map(e=>parseInt(e,10)),teamIds:parseInt(e.databaseId,10),eligibleForSubmission:t===`true`,eligibleForBounty:n===`true`&&t===`true`,instruction:r}})};return e.organization.i_can_manage_organization_assets&&(e.type!==window.constants.team.type.assessment||e.organization.i_can_manage_pentest_scope)?(0,W.jsxs)(W.Fragment,{children:[(0,W.jsx)(l,{variation:`secondary`,testId:`spec-add-asset-button`,disabled:u,onClick:()=>{A.track(`asset creation modal opened`,{category:window.constants.analytics.scope_management}),r(!0)},children:`Add asset`}),t&&(0,W.jsx)(we,{showModal:t,setShowModal:r,selectedAssets:i,setSelectedAssets:a,handle:e.organization.handle,onContinue:()=>{r(!1),s(!0),A.track(`asset from the inventory is selected in the modal`,{category:window.constants.analytics.scope_management})},onCancel:()=>{a([])},onFail:e=>{e.createAsset.errors.edges[0].node.message===window.constants.assetInventory.errors.duplicate&&A.track(`asset creation of unique identifier failed`,{category:window.constants.analytics.scope_management})},teamName:e.name}),o&&(0,W.jsx)(De,{showModal:o,setShowModal:s,showInstruction:i.length===1,onBack:()=>{s(!1),r(!0)},onAdd:(e,t,n)=>{d(e,t,n)},onCancel:()=>{a([])}})]}):(0,W.jsx)(W.Fragment,{})};q.fragments={team:a`
    fragment AddAssetFragment on Team {
      id
      databaseId: _id
      organization {
        id
        handle
        i_can_manage_pentest_scope
        i_can_manage_organization_assets
        asset_package {
          risks_enabled
          dns_enabled
          attachments_enabled
        }
      }
      type
    }
  `};var Oe=e(me()),ke=25,Ae=({setCurrentPage:e,currentPage:t,totalCount:n,loading:r,pageSize:i})=>(0,W.jsx)(f,{disabled:r,alignment:`right`,itemsPerPage:i,currentPage:t,onClickPrevious:()=>{e(t-1)},onClickNext:()=>{e(t+1)},totalItems:n,nextPageLabel:`Next page`,previousPageLabel:`Previous page`});Ae.propTypes={currentPage:B.default.number.isRequired,setCurrentPage:B.default.func.isRequired,totalCount:B.default.number.isRequired,loading:B.default.bool,pageSize:B.default.number.isRequired};var je=({paginationInfoObject:e,loading:t,pageSize:n=ke})=>{let{store:r,dispatch:i}=(0,z.useContext)(Z),{currentPage:a}=r;return(0,W.jsx)(Ae,{currentPage:a,setCurrentPage:e=>{i({type:V.SET_CURRENT_PAGE,value:e})},loading:t,totalCount:e?.total_count||0,pageSize:n})};je.propTypes={paginationInfoObject:B.default.object,loading:B.default.bool,pageSize:B.default.number};var Me=e(d()),Ne=({numberOfRows:e=5})=>(0,W.jsxs)(k,{fixed:!0,className:`spec-domains-table`,children:[(0,W.jsx)(k.Head,{className:`text-sm`,children:(0,W.jsxs)(k.Row,{children:[(0,W.jsx)(k.CellHeader,{children:(0,W.jsx)(p,{name:`scope-select-all`,checked:!1,disabled:!0})}),(0,W.jsx)(k.CellHeader,{children:`Asset name`}),(0,W.jsx)(k.CellHeader,{width:`100`,children:`Asset type`}),(0,W.jsx)(k.CellHeader,{children:`Coverage`}),(0,W.jsx)(k.CellHeader,{children:`CVSS`}),(0,W.jsx)(k.CellHeader,{children:`Bounty`}),(0,W.jsx)(k.CellHeader,{children:`Last added`})]})}),(0,W.jsx)(k.Body,{children:(0,Me.default)(e).map(e=>(0,W.jsxs)(k.Row,{children:[(0,W.jsx)(k.Cell,{children:(0,W.jsx)(g,{lines:1})}),(0,W.jsx)(k.Cell,{width:`50%`,children:(0,W.jsx)(g,{lines:3})}),(0,W.jsx)(k.Cell,{children:(0,W.jsx)(g,{lines:1})}),(0,W.jsx)(k.Cell,{children:(0,W.jsx)(g,{lines:1})}),(0,W.jsx)(k.Cell,{children:(0,W.jsx)(g,{lines:1})})]},e))})]});Ne.propTypes={numberOfRows:B.default.number};var Pe=`/assets/static/empty_asset_inventory-NXv_FcpP.svg`,Fe=()=>{let{dispatch:e}=(0,z.useContext)(Z);return(0,W.jsxs)(`div`,{className:`flex flex-col items-center py-2xl`,children:[(0,W.jsx)(`div`,{className:`overflow-hidden mb-l`,children:(0,W.jsx)(m,{src:Pe})}),(0,W.jsx)(`span`,{className:`text-center w-1/2 text-400 text-xl`,children:`No assets in scope`}),(0,W.jsx)(`span`,{className:`text-center mt-sm`,children:(0,W.jsx)(l,{testId:`spec-empty-table-add-asset-button`,onClick:()=>{e({type:V.SET_SHOW_ADD_ASSETS_MODAL,value:!0})},children:`Add an asset`})})]})},Ie=({showModal:e,setShowModal:n,onSubmit:r,singleSelectedId:i,presetInstruction:a})=>{let{store:o}=(0,z.useContext)(Z),[s,c]=(0,z.useState)(a||``),u=i?[i]:o.selectedIds;return(0,W.jsx)(W.Fragment,{children:(0,W.jsxs)(F,{shouldCloseOnEsc:!0,showModal:e,size:`medium`,title:u.length>1?`Edit instructions for ${u.length} selected assets`:`Edit instructions`,handleCloseModal:()=>{n(!1)},children:[(0,W.jsx)(`div`,{className:`mb-md mt-lg`,children:(0,W.jsxs)(`div`,{className:`mt-md`,children:[(0,W.jsx)(t,{text:`Instruction`,htmlFor:`instruction-input`,id:`instruction-input-label`}),(0,W.jsx)(`p`,{className:`text-neutral-300 dark:text-neutral-800`,children:`Guide hackers oh what to expect or not for the selected assets.`}),(0,W.jsx)(v,{value:s,testId:`spec-instruction-input`,rows:7,onChange:e=>c(e.target.value),id:`instruction-input`,className:`spec-instruction-input`,labelledBy:`instruction-input-label`})]})}),(0,W.jsxs)(`div`,{className:`flex gap-md mt-md place-content-end`,children:[(0,W.jsx)(l,{variation:`tertiary`,onClick:()=>{n(!1)},children:`Cancel`}),(0,W.jsx)(l,{testId:`spec-save-instruction`,variation:`primary`,disabled:!s,onClick:()=>{r(s,u),n(!1)},children:`Save`})]})]})})};Ie.propTypes={singleSelectedId:B.default.string,presetInstruction:B.default.string,showModal:B.default.bool.isRequired,setShowModal:B.default.func.isRequired,onSubmit:B.default.func.isRequired},S();var Le=a`
  mutation BulkUpdateScopes(
    $scopeIds: [Int!]!
    $eligibleForBounty: Boolean
    $eligibleForSubmission: Boolean
    $instruction: String
  ) {
    bulkUpdateScopes(
      input: {
        scope_ids: $scopeIds
        eligible_for_bounty: $eligibleForBounty
        eligible_for_submission: $eligibleForSubmission
        instruction: $instruction
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
`,Re=a`
  mutation BulkArchiveScopes($scopeIds: [Int!]!) {
    bulkArchiveScopes(input: { scope_ids: $scopeIds }) {
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
`,ze=(e,t)=>{let[n,{loading:r}]=P(Le,{refetchQueries:[`ProgramSettingsScopeManagement`],onCompleted:({bulkUpdateScopes:{was_successful:t,errors:n}})=>{if(!t){j(`error`,n.edges.map(e=>e.node.message).join(` `));return}R(),e&&e()},onError:()=>{t&&t(),L()}});return[n,r]},Be=(e,t)=>{let[n,{loading:r}]=P(Re,{refetchQueries:[`ProgramSettingsScopeManagement`],onCompleted:({bulkArchiveScopes:{was_successful:t,errors:n}})=>{if(!t){j(`error`,n.edges.map(e=>e.node.message).join(` `));return}R(),e&&e()},onError:()=>{t&&t(),L()}});return[n,r]},J=({name:e,actions:t,testId:n})=>{let[i,a]=(0,z.useState)(!1),o=()=>a(!i),s=(0,z.useRef)(null);return O(s,()=>a(!1)),(0,W.jsx)(W.Fragment,{children:(0,W.jsx)(`div`,{className:`asset-row__menu-holder -ml-[1px]`,ref:s,"data-testid":n,children:(0,W.jsx)(ce,{popperClassname:`mt-spacing-16 spec-manage-scope-menu`,popperPlacement:`bottom-start`,showPopper:i,componentToTarget:(0,W.jsx)(l,{small:!0,icons:{right:{accessibilityLabel:`expand`,src:r}},onClick:o,variation:`tertiary`,children:e}),componentToPop:(0,W.jsx)(c,{children:(0,W.jsx)(`ul`,{className:`select-menu`,children:t.map(e=>(0,W.jsx)(`li`,{className:e.disabled?`menu-item--disabled spec-menu-item-${e.id}--disabled daisy-link--graphite`:`menu-item spec-menu-item-${e.id}`,role:`button`,"data-testid":`spec-menu-item-${e.id}`,onClick:e.disabled?null:()=>{e.action(),o()},children:(0,W.jsx)(`div`,{className:`flex gap-spacing-8`,children:e.name})},e.name))})})})})})};J.propTypes={name:B.default.string.isRequired,actions:B.default.arrayOf(B.default.object),testId:B.default.string};var Ve=({assets:e})=>{let{store:t,dispatch:n}=(0,z.useContext)(Z),{selectedIds:r}=t,i=r.length===e.length,[a,o]=(0,z.useState)(!1),[s,c]=ze(()=>{n({type:V.TOGGLE_SELECT_ALL,value:[]})}),[u]=Be(()=>{n({type:V.TOGGLE_SELECT_ALL,value:[]})}),d=e=>{s({variables:{scopeIds:r.map(e=>parseInt(e,10)),...e}})},f=()=>{u({variables:{scopeIds:r.map(e=>parseInt(e,10))}})},m=(e,t)=>{s({variables:{scopeIds:t.map(e=>parseInt(e,10)),instruction:e}})};return(0,W.jsxs)(W.Fragment,{children:[(0,W.jsxs)(`div`,{className:`flex items-center py-8`,children:[(0,W.jsxs)(`div`,{className:`flex mr-lg`,children:[(0,W.jsx)(p,{name:`scope-select-all`,checked:i,indeterminate:r.length&&!i,onChange:()=>{n({type:V.TOGGLE_SELECT_ALL,value:r.length>0?[]:e.map(e=>e.id)})}}),r.length,` selected items`]}),(0,W.jsx)(`div`,{className:`flex mr-sm`,children:(0,W.jsx)(l,{small:!0,variation:`tertiary`,disabled:c,testId:`spec-edit-instructions-button`,onClick:()=>{o(!0),A.track(`scopes instructions being edited`,{category:window.constants.analytics.scope_management})},children:`Edit instructions`})}),(0,W.jsx)(`div`,{className:`flex mr-sm`,children:(0,W.jsx)(J,{testId:`spec-edit-coverage-menu`,name:`Edit coverage`,disabled:c,actions:[{id:`set-as-in-scope`,name:`Set as in scope`,action:()=>{d({eligibleForSubmission:!0})},className:`spec-set-in-scope`},{id:`set-as-out-of-scope`,name:`Set as out scope`,action:()=>{d({eligibleForSubmission:!1,eligibleForBounty:!1})},className:`spec-set-out-scope`}]})}),(0,W.jsx)(`div`,{className:`flex mr-sm`,children:(0,W.jsx)(J,{testId:`spec-edit-eligibility-menu`,name:`Edit bounty eligibility`,disabled:c,actions:[{id:`set-as-eligible-for-bounty`,name:`Eligible for bounty`,action:()=>{d({eligibleForSubmission:!0,eligibleForBounty:!0})},className:`spec-set-in-scope`},{id:`set-as-not-eligible-for-bounty`,name:`Not eligible for bounty`,action:()=>{d({eligibleForBounty:!1})},className:`spec-set-out-scope`}]})}),(0,W.jsx)(`div`,{className:`flex mr-sm`,children:(0,W.jsx)(l,{small:!0,testId:`spec-remove-from-program`,variation:`tertiary`,disabled:c,onClick:()=>{f(),A.track(`remove multiple assets from program`,{category:window.constants.analytics.scope_management})},children:`Remove from program`})})]}),a&&(0,W.jsx)(Ie,{showModal:!0,setShowModal:o,onSubmit:(e,t)=>{m(e,t),o(!1)}})]})};Ve.propTypes={assets:B.default.arrayOf(B.default.object).isRequired},S();var He=a`
  mutation EditScopeModalUpdateStructuredScope(
    $scopeId: ID!
    $assetIdentifier: String
    $instruction: String
    $eligibleForSubmission: Boolean
    $eligibleForBounty: Boolean
  ) {
    updateStructuredScope(
      input: {
        structured_scope_id: $scopeId
        asset_identifier: $assetIdentifier
        instruction: $instruction
        eligible_for_submission: $eligibleForSubmission
        eligible_for_bounty: $eligibleForBounty
      }
    ) {
      was_successful
      structured_scope {
        id
        asset_identifier
        instruction
        eligible_for_submission
        eligible_for_bounty
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
`,Ue=({showModal:e,setShowModal:r,scopeId:i,initialValues:a,onSuccess:o})=>{let[s,c]=(0,z.useState)(a?.identifier||``),[u,d]=(0,z.useState)(a?.instruction||``),[f,p]=(0,z.useState)(a?.eligibleForSubmission===!0?`true`:`false`),[m,h]=(0,z.useState)(a?.eligibleForBounty===!0?`true`:`false`);(0,z.useEffect)(()=>{c(a?.identifier||``),d(a?.instruction||``),p(a?.eligibleForSubmission===!0?`true`:`false`),h(a?.eligibleForBounty===!0?`true`:`false`)},[a]);let[g,{loading:_}]=P(He,{refetchQueries:[`ProgramSettingsScopeManagement`],onCompleted:({updateStructuredScope:{was_successful:e,errors:t,structured_scope:n}})=>{e?(R(),r(!1),o?.(n)):j(`error`,t.edges.map(e=>e.node.message).join(` `))},onError:()=>{L()}}),v=()=>{let e=f===`true`;g({variables:{scopeId:i,assetIdentifier:s,instruction:u||null,eligibleForSubmission:e,eligibleForBounty:m===`true`&&e}})},y=s.trim().length>0,b=s!==(a?.identifier||``)||u!==(a?.instruction||``)||f!==(a?.eligibleForSubmission===!0?`true`:`false`)||m!==(a?.eligibleForBounty===!0?`true`:`false`);return(0,W.jsxs)(F,{shouldCloseOnEsc:!0,showModal:e,size:`medium`,title:`Edit scope`,handleCloseModal:()=>{r(!1)},children:[(0,W.jsxs)(`div`,{className:`mb-md mt-lg`,children:[(0,W.jsxs)(`div`,{className:`mt-md`,children:[(0,W.jsx)(t,{text:`Asset identifier`,htmlFor:`identifier-input`,id:`identifier-input-label`}),(0,W.jsx)(`p`,{className:`text-neutral-300 dark:text-neutral-800 text-sm mb-sm`,children:`The name or identifier of the asset as it appears in the scope and bounty tables.`}),(0,W.jsx)(n,{value:s,testId:`spec-identifier-input`,onChange:e=>c(e.target.value),id:`identifier-input`,className:`spec-identifier-input`,labelledBy:`identifier-input-label`,disabled:_})]}),(0,W.jsx)(`div`,{className:`mt-lg`,children:(0,W.jsx)(K,{eligibleForSubmission:f,onEligibleForSubmissionChange:p,eligibleForBounty:m,onEligibleForBountyChange:h,instruction:u,onInstructionChange:d,showInstruction:!0,disabled:_})})]}),(0,W.jsxs)(`div`,{className:`flex gap-md mt-lg place-content-end`,children:[(0,W.jsx)(l,{variation:`tertiary`,onClick:()=>{r(!1)},disabled:_,children:`Cancel`}),(0,W.jsx)(l,{testId:`spec-save-scope`,variation:`primary`,disabled:!y||!b||_,onClick:v,children:_?`Saving...`:`Save`})]})]})};Ue.propTypes={scopeId:B.default.string.isRequired,initialValues:B.default.shape({identifier:B.default.string,instruction:B.default.string,eligibleForSubmission:B.default.bool,eligibleForBounty:B.default.bool}),showModal:B.default.bool.isRequired,setShowModal:B.default.func.isRequired,onSuccess:B.default.func},S();var We=e(o()),{ASSET_TAG_REWARD_CATEGORIES:Ge}=window.constants.featureToggles,Y=50,Ke=a`
  query ProgramSettingsScopeManagement(
    $teamHandle: String!
    $searchString: String
    $from: Int
    $size: Int
    $sort: SortInput
    $rewardTagIds: [Int]
    $rewardTagCategoryId: Int
  ) {
    team(handle: $teamHandle) {
      id
      handle
      structured_scopes_search(
        search_string: $searchString
        from: $from
        size: $size
        sort: $sort
        reward_tag_ids: $rewardTagIds
        reward_tag_category_id: $rewardTagCategoryId
      ) {
        nodes {
          ... on StructuredScopeDocument {
            id
            databaseId: _id
            identifier
            display_name
            eligible_for_submission
            cvss_score
            eligible_for_bounty
            created_at
            instruction
            asm_reward_tags
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
`,qe=a`
  query StructuredScopeAsset($handle: String!, $ids: [Int!]!) {
    teams(first: 1, where: { handle: { _eq: $handle } }) {
      nodes {
        id
        structured_scopes(ids: $ids) {
          nodes {
            id
            databaseId: _id
            asset {
              id
              databaseId: _id
            }
          }
        }
      }
    }
  }
`,Je=()=>{let{team:e,store:t,dispatch:n}=(0,z.useContext)(Z),{currentPage:r,selectedIds:i}=t,a=ie(t.searchTerm,300),{enabled:o,loading:c}=ae(Ge,e.organization?.handle),l=o===!0&&!c,[u,d]=(0,z.useState)({}),{data:f,loading:m}=I(Ke,{variables:{teamHandle:e.handle,searchString:a,from:r*Y,size:Y,sort:{field:t.sortingField,direction:t.sortingDirection},rewardTagIds:t.selectedTagIds?.length>0?t.selectedTagIds:void 0,rewardTagCategoryId:t.selectedCategoryId&&t.selectedTagIds?.length===0?parseInt(t.selectedCategoryId,10):void 0},onCompleted:()=>{d({})}}),h=f?f.team.structured_scopes_search:{nodes:[]},g=h.nodes,{data:_,loading:v}=I(qe,{variables:{handle:e.handle,ids:g.map(e=>parseInt(e.databaseId,10))}}),y=m||v,b=_?_.teams.nodes[0].structured_scopes.nodes:[],[x]=ze(),[S]=Be(),[C,w]=(0,z.useState)(!1),[T,E]=(0,z.useState)(null),[D,O]=(0,z.useState)(null),[j,M]=(0,z.useState)(null),N=e=>{let t=(0,We.default)(e);return constants.assetInventory.assetTypes[t].action},P=i.length===g.length,F=e=>i.includes(e),oe=e=>{let t=b.find(t=>t.databaseId===e).asset.id;n({type:V.SET_ASSET_SIDEBAR_TAB_INDEX,value:0}),n({type:V.SET_SELECTED_ASSET_ID,value:t})};if(!y&&g.length===0)return(0,W.jsx)(Fe,{});let se=e=>{let t=u[e.databaseId],n=t?.eligibleForBounty??e.eligible_for_bounty,r=t?.eligibleForSubmission??e.eligible_for_submission,i=[{id:`row-edit-scope`,name:`Edit scope`,action:()=>{let n=b.find(t=>t.databaseId===e.databaseId);n&&(E(n.id),M(e.databaseId),O({identifier:t?.identifier??e.identifier,instruction:t?.instruction??e.instruction??``,eligibleForSubmission:t?.eligibleForSubmission??e.eligible_for_submission===!0,eligibleForBounty:t?.eligibleForBounty??e.eligible_for_bounty===!0}),w(!0),A.track(`scope editing`,{category:window.constants.analytics.scope_management}))}},{id:`row-remove-from-program`,name:`Remove from program`,action:()=>{S({variables:{scopeIds:[parseInt(e.databaseId,10)]}}),A.track(`asset removed from the program`,{category:window.constants.analytics.scope_management})}}];return n?i.unshift({id:`row-not-eligible-for-bounty`,name:`Not eligible for bounty`,action:()=>{x({variables:{scopeIds:[parseInt(e.databaseId,10)],eligibleForBounty:!1}})}}):i.unshift({id:`row-eligible-for-bounty`,name:`Eligible for bounty`,action:()=>{x({variables:{scopeIds:[parseInt(e.databaseId,10)],eligibleForBounty:!0,eligibleForSubmission:!0}})}}),r?i.unshift({id:`row-set-as-out-of-scope`,name:`Set as out of scope`,action:()=>{x({variables:{scopeIds:[parseInt(e.databaseId,10)],eligibleForBounty:!1,eligibleForSubmission:!1}})}}):i.unshift({id:`row-set-as-in-scope`,name:`Set as in scope`,action:()=>{x({variables:{scopeIds:[parseInt(e.databaseId,10)],eligibleForSubmission:!0}})}}),i};return(0,W.jsxs)(W.Fragment,{children:[y?(0,W.jsx)(Ne,{numberOfRows:Y}):(0,W.jsxs)(k,{currentSortingColumn:t.sortingField,currentSortingDirection:t.sortingDirection,onSort:e=>{n({type:V.SET_SORTING,value:e})},className:`spec-assets-table`,children:[(0,W.jsx)(k.Head,{className:`text-sm`,children:(0,W.jsx)(k.Row,{children:i.length>0?(0,W.jsx)(W.Fragment,{children:(0,W.jsx)(k.CellHeader,{colSpan:l?14:13,children:(0,W.jsx)(Ve,{assets:g})})}):(0,W.jsxs)(W.Fragment,{children:[(0,W.jsx)(k.CellHeader,{children:(0,W.jsx)(p,{name:`scope-select-all`,testId:`spec-assets-select-all`,checked:P,indeterminate:!y&&i.length&&!P,onChange:()=>{n({type:V.TOGGLE_SELECT_ALL,value:g.map(e=>e.databaseId)})}})}),(0,W.jsx)(k.CellHeader,{sortingFieldName:`identifier`,children:`Asset name`}),(0,W.jsx)(k.CellHeader,{width:`120`,sortingFieldName:`display_name`,children:`Type`}),(0,W.jsx)(k.CellHeader,{sortingFieldName:`eligible_for_submission`,children:`Coverage`}),(0,W.jsx)(k.CellHeader,{sortingFieldName:`cvss_score`,children:`CVSS`}),l&&(0,W.jsx)(k.CellHeader,{sortingFieldName:`asm_reward_tags`,children:`Reward Tag`}),(0,W.jsx)(k.CellHeader,{sortingFieldName:`eligible_for_bounty`,children:`Bounty`}),(0,W.jsx)(k.CellHeader,{sortingFieldName:`created_at`,colSpan:2,children:`Added to program`})]})})}),(0,W.jsx)(k.Body,{children:g.map(e=>(0,W.jsxs)(k.Row,{className:`spec-asset-row`,children:[(0,W.jsx)(k.Cell,{children:(0,W.jsx)(p,{name:`scope-${e.id}`,checked:F(e.databaseId),onChange:()=>{n({type:V.TOGGLE_SELECT,value:e.databaseId})}})}),(0,W.jsx)(k.Cell,{children:(0,W.jsxs)(`div`,{className:`flex flex-col`,style:{maxWidth:`400px`},children:[(0,W.jsx)(`div`,{className:`flex`,children:(0,W.jsx)(`strong`,{className:`truncate spec-asset-identifier cursor-pointer`,onClick:()=>{oe(e.databaseId)},children:u[e.databaseId]?.identifier||e.identifier})}),(0,W.jsx)(`div`,{className:`text-neutral-400 dark:text-neutral-950`,children:(()=>{let t=u[e.databaseId]?.instruction??e.instruction;return t?t.length>300?(0,W.jsx)(te,{content:t,className:`text-neutral-400 pb-sm dark:text-neutral-950`,truncateHeight:72,enableMarkdown:!0,disableContextMenu:!0}):(0,W.jsx)(ee,{className:`markdownable text-neutral-400 pb-sm dark:text-neutral-950`,markdown:t,disableContextMenu:!0}):(0,W.jsx)(`span`,{children:`-`})})()})]})}),(0,W.jsx)(k.Cell,{children:N(e.display_name)}),(0,W.jsx)(k.Cell,{children:u[e.databaseId]?.eligibleForSubmission??e.eligible_for_submission?(0,W.jsx)(s,{color:`green`,children:`In scope`}):(0,W.jsx)(s,{color:`yellow`,children:`Out of scope`})}),(0,W.jsx)(k.Cell,{children:(0,W.jsx)(re,{value:e.cvss_score})}),l&&(0,W.jsx)(k.Cell,{children:e.asm_reward_tags?.length>0?(0,W.jsxs)(`div`,{className:`flex flex-wrap gap-xs`,children:[e.asm_reward_tags.slice(0,3).map(e=>(0,W.jsx)(s,{color:`blue`,children:e},e)),e.asm_reward_tags.length>3&&(0,W.jsxs)(s,{color:`blue`,children:[`+`,e.asm_reward_tags.length-3]})]}):(0,W.jsx)(`span`,{children:`-`})}),(0,W.jsx)(k.Cell,{children:(0,W.jsx)(ne,{value:u[e.databaseId]?.eligibleForBounty??e.eligible_for_bounty})}),(0,W.jsx)(k.Cell,{children:(0,Oe.default)(e.created_at).format(`MM/DD/YYYY`)}),(0,W.jsx)(k.Cell,{children:(0,W.jsx)(pe,{actions:se(e)})})]},e.id))})]}),(0,W.jsx)(`div`,{className:`justify-end p-md pr-0 pb-0 relative`,children:(0,W.jsx)(je,{loading:y,paginationInfoObject:h,pageSize:Y})}),C&&T&&D&&(0,W.jsx)(Ue,{showModal:C,scopeId:T,initialValues:D,setShowModal:w,onSuccess:e=>{e&&j&&d(t=>({...t,[j]:{identifier:e.asset_identifier,instruction:e.instruction,eligibleForSubmission:e.eligible_for_submission,eligibleForBounty:e.eligible_for_bounty}})),O(null),E(null),M(null)}},`${T}-${D.eligibleForSubmission}-${D.eligibleForBounty}`)]})};S();var Ye=a`
  mutation UpdateTeamScopeDescription(
    $teamId: ID!
    $scopeDescription: String!
  ) {
    updateTeamScopeDescription(
      input: { team_id: $teamId, scope_description: $scopeDescription }
    ) {
      was_successful
      team {
        id
        scope_description
      }
    }
  }
`,X=()=>{let{team:e}=(0,z.useContext)(Z),[t,n]=(0,z.useState)(e.scope_description||``),[r]=P(Ye,{variables:{teamId:e.id,scopeDescription:t},onCompleted:e=>{e.updateTeamScopeDescription.was_successful?j(`notice`,`Scope description was successfully updated!`):L()}});return(0,W.jsx)(h,{border:!1,fill:!0,children:(0,W.jsxs)(_,{children:[(0,W.jsx)(`div`,{children:(0,W.jsx)(`span`,{className:`text-xl font-normal`,children:`Additional Details`})}),(0,W.jsx)(`div`,{className:`mt-xl`,children:(0,W.jsx)(E,{textareaId:`scope_description`,name:`description`,value:t,onChange:e=>n(e),showPreview:!0,label:`Program scope description (optional)`,required:!1})}),(0,W.jsx)(`div`,{className:`flex justify-end mt-md`,children:(0,W.jsx)(l,{onClick:r,children:`Update`})})]})})};X.fragments={team:a`
    fragment AdditionalDetailsScopeManagementFragment on Team {
      id
      scope_description
    }
  `},S();var Z=z.createContext(),Xe=a`
  query ScopeManagementQuery($handle: String!) {
    teams(first: 1, where: { handle: { _eq: $handle } }) {
      nodes {
        id
        handle
        name
        ...AdditionalDetailsScopeManagementFragment
        ...AddAssetFragment
      }
    }
  }
  ${X.fragments.team}
  ${q.fragments.team}
`,Q=({teamHandle:e})=>{let[t,n]=(0,z.useReducer)(_e,he),{data:r,networkStatus:i}=I(Xe,{notifyOnNetworkStatusChange:!0,variables:{handle:e},fetchPolicy:`cache-and-network`});if(i===1&&!r||!r)return(0,W.jsx)(N,{});let a=r.teams.nodes[0],{organization:o}=a;return a?(0,W.jsxs)(Z.Provider,{value:{store:t,dispatch:n,team:a,organization:o},children:[(0,W.jsx)(`div`,{className:`mb-md`,children:(0,W.jsx)(b,{children:`Scope`})}),(0,W.jsx)(h,{border:!1,fill:!0,children:(0,W.jsxs)(_,{children:[(0,W.jsx)(`div`,{children:(0,W.jsx)(`span`,{className:`text-xl font-normal`,children:`Manage Scope`})}),(0,W.jsxs)(`div`,{className:`mt-xl flex gap-md items-end`,children:[(0,W.jsx)(`div`,{className:`grow`,children:(0,W.jsx)(Ce,{})}),(0,W.jsx)(`div`,{className:`shrink-0`,children:(0,W.jsx)(q,{})})]}),(0,W.jsx)(`div`,{className:`overflow-x-scroll mt-xl`,children:(0,W.jsx)(Je,{})}),t.selectedAssetId&&(0,W.jsx)(fe,{close:()=>{n({type:V.SET_SELECTED_ASSET_ID,value:null})},canManage:o.i_can_manage_organization_assets,contextToUse:Z})]})}),(0,W.jsx)(`div`,{className:`mt-lg`,children:(0,W.jsx)(X,{})})]}):null};Q.propTypes={teamHandle:B.default.string.isRequired};var $=e=>(0,W.jsx)(se,{children:(0,W.jsx)(M,{header:(0,W.jsx)(oe,{...e}),content:(0,W.jsx)(Q,{teamHandle:e.match.params.handle}),hasBackground:!1})});$.propTypes={match:B.default.shape({params:B.default.shape({handle:B.default.string.isRequired}).isRequired}).isRequired};export{$ as default};
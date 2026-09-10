import{o as e}from"./rolldown-runtime-DAXXjFlN.js";import{Fw as t,Hx as n,Iw as r,Rw as i,Vu as a,sb as o,sd as s}from"./vendor-_WdvpBLr.js";import{Cp as c,Sm as l,eh as u,gh as d,ih as f,lh as p}from"./app-5pKgUmmm.js";var m=e(i()),h=e(r()),g=e(a()),_=c(`
  query AssetSelectorSharedQuery(
    $teamHandle: String!
    $query: String
    $assetType: [String!]
    $first: Int
    $after: String
    $eligibleForBounty: Boolean
    $startDate: DateTime
  ) {
    team(handle: $teamHandle) {
      id
      handle
      structured_scope_asset_types
      offers_bounties
      structured_scopes(
        start_date: $startDate
        after: $after
        first: $first
        archived: false
        search: $query
        eligible_for_submission: true
        eligible_for_bounty: $eligibleForBounty
        asset_type: $assetType
        order_by: { field: asset_identifier, direction: ASC }
      ) {
        pageInfo {
          hasNextPage
          endCursor
        }
        edges {
          node {
            id
            databaseId: _id
            asset_type
            asset_identifier
            eligible_for_submission
            eligible_for_bounty
            max_severity
            instruction
          }
        }
      }
    }
  }
`),v=e(o()),y=t(),{assetTypes:b}=window.constants,x=({structuredScope:e,active:t})=>(0,y.jsxs)(p,{justifyContent:`space-between`,alignItems:`center`,children:[(0,y.jsxs)(`div`,{className:`text-truncate spec-asset-suggestion`,children:[t?(0,y.jsx)(`strong`,{children:e.asset_identifier}):e.asset_identifier,e.asset_type!==``&&(0,y.jsx)(`div`,{className:`meta-text`,children:(0,y.jsxs)(`ul`,{className:`list list--inline no-wrap`,children:[(0,y.jsx)(`li`,{children:b[e.asset_type].action}),e.max_severity&&e.eligible_for_submission?(0,y.jsx)(`li`,{children:v.default.capitalize(e.max_severity)}):null,e.eligible_for_bounty&&e.eligible_for_submission?(0,y.jsx)(`li`,{children:`Eligible for bounty`}):null]})})]}),t?(0,y.jsx)(f,{color:`blue`,glyph:u,size:`medium`,className:void 0,glyphScale:void 0,background:void 0,round:void 0,transform:void 0}):null]}),S=({teamHandle:e})=>(0,y.jsxs)(`p`,{className:`inline-banner inline-banner--warning margin-10--bottom`,children:[`Your program scope has not been configured!`,` `,(0,y.jsx)(`a`,{href:`/${e}/scopes`,children:`Add assets to program scope`})]}),{assetTypes:C}=window.constants,w=500,T=({innerProps:e,innerRef:t,data:n,isFocused:r,isSelected:i})=>(0,y.jsx)(`div`,{ref:t,...e,className:(0,h.default)(`flex flex-col py-[0.625rem] bg-white px-xs dark:bg-neutral-50 dark:text-white`,r&&`!bg-blue-900 dark:!bg-neutral-100`),children:(0,y.jsx)(x,{structuredScope:n,active:i})}),E=({teamHandle:e,onSetAssets:t,selectedAssets:r,showConfigureScopesCta:i,allScopes:a,preFilters:o,hideAssetTypeDropdown:c,filterEligibleForBounty:u,filterNewAssets:f,singleSelection:p,assetsLabel:v,assetsTypeLabel:b,helperLabel:x,disabled:E=!1})=>{let D=null;f&&(D=new Date,D.setMonth(D.getMonth()-1));let[O,k]=(0,m.useState)({startDate:D,eligibleForBounty:u,teamHandle:e,first:w}),[A,j]=(0,m.useState)([]),[M,N]=(0,m.useState)(null),[P,F]=(0,m.useState)(o??[]),[I,L]=(0,m.useState)(!0),R=(0,m.useCallback)(e=>e===null?[]:e.filter(e=>e.node!==null||e.node!==void 0).map(e=>({value:e.node.id,label:e.node.asset_identifier,...e.node})),[]),z=(e,t)=>{let n=e?.team?.structured_scopes?.edges??[];if(e?.team?.structured_scopes===null||e?.team?.structured_scopes===void 0||n.length===0)return;L(e.team.structured_scopes.pageInfo.hasNextPage);let r=R(n);if(t&&(r=A.concat(r)),j(r),!M){let t=e.team.structured_scope_asset_types?.map(e=>({value:e,label:C[e]?.action}));N(t??[])}k({...O,assetType:P.length===0?null:P.map(e=>e.value),after:e.team.structured_scopes.pageInfo.endCursor})},[B]=n(_),V=()=>{I&&B({variables:{...O,assetType:P.length===0?null:P.map(e=>e.value)}}).then(({data:e})=>{z(e,!0)},()=>{l(`error`,`Error while fetching your data`)})};if((0,m.useEffect)(()=>{V()},[]),(0,m.useEffect)(()=>{if(a!=null){if(A.find(e=>e.label===`All scopes`)||f||o)return;let e=[a].concat(A);j(e)}},[A]),i&&A.length===0)return(0,y.jsx)(S,{teamHandle:e});let H=(e,t,n)=>{if(!a)return e;if(t.filter(e=>e.label===n).length===1)return e.filter(e=>e.label!==n);let r=e.filter(e=>e.label===n);return r.length===1?r:e},U=t=>{let n=H(t,P,`All types`);k({startDate:D,eligibleForBounty:u,teamHandle:e,first:w}),L(!0),F(n),B({variables:{startDate:D,eligibleForBounty:u,teamHandle:e,first:w,assetType:n.length===0?null:n.map(e=>e.value)}}).then(({data:e})=>{z(e,!1)},()=>{l(`error`,`Error while fetching your data`)})},W=e=>{if(p){t(e);return}t(H(e,r,`All scopes`))},G=(0,g.default)(t=>{k({...O,query:t}),B({variables:{...O,after:null,teamHandle:e,query:t,assetType:P.length===0?null:P.map(e=>e.value)}}).then(({data:e})=>{z(e,!1)},()=>{l(`error`,`Error while fetching your data`)})},500);return(0,y.jsx)(y.Fragment,{children:(0,y.jsxs)(d,{children:[(0,y.jsxs)(`div`,{className:(0,h.default)(`grid grid-row justify-center gap-spacing-24 grid-cols-6 pt-spacing-12`,!x&&`pb-spacing-12`),children:[(0,y.jsxs)(d.Column,{className:(0,h.default)(`grid col-span-4 auto-rows-min`,c&&`col-span-6`),children:[(0,y.jsx)(`div`,{className:`text-base font-bold mb-spacing-8`,children:v??`Assets`}),(0,y.jsx)(s,{placeholder:`Select an asset`,onChange:W,disabled:E,selectedOption:r,testId:`spec-select-asset`,options:A,onReachMenuBottom:V,onInputChange:G,optionComponent:T,isMulti:!p})]}),c?null:(0,y.jsxs)(d.Column,{className:`grid col-span-2 auto-rows-min`,children:[(0,y.jsx)(`div`,{className:`text-base font-bold mb-spacing-8`,children:b??`Asset type`}),(0,y.jsx)(s,{placeholder:`Select an asset type`,isMulti:!0,disabled:o!==void 0,onChange:U,selectedOption:P,testId:`spec-select-asset-type`,options:M??[]})]})]}),x&&(0,y.jsx)(`div`,{className:`pb-spacing-12`,children:(0,y.jsx)(`p`,{className:`text-base font-normal text-neutral-400 dark:text-neutral-700`,children:x})})]})})};export{E as t};
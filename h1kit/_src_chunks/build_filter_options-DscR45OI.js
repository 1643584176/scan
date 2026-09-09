import{o as e}from"./rolldown-runtime-DAXXjFlN.js";import{Ux as t,Va as n}from"./vendor-_WdvpBLr.js";import{Cp as r,No as i}from"./app-5pKgUmmm.js";var a=r(`
  query AnalyticsDashboardFilterDefinitions(
    $dashboardKey: String!
    $organizationId: ID
  ) {
    analytics_dashboard_filter_definitions(
      dashboard_key: $dashboardKey
      organization_id: $organizationId
    ) {
      key
      label
      filter_type
      value_type
      tooltip
      description
      options {
        value
        label
        group
        subtext
      }
      operators {
        value
        label
      }
    }
  }
`),o=(e,n,r=!1)=>{let{data:i}=t(a,{variables:{dashboardKey:e??``,organizationId:n??null},skip:r||!e});return i?.analytics_dashboard_filter_definitions?i.analytics_dashboard_filter_definitions:[]},s=e(n()),c=e=>{let t=[],n=[];return e.forEach(e=>{let r=i[e.type]||`Other`;t.some(e=>e.id===r)||t.push({id:r,label:r}),n.push({belongsToGroupId:r,value:e.databaseId,subtext:e.handle,label:e.name})}),{checkboxGroups:t,checkboxes:n}},l=e=>{if(!(0,s.isEmpty)(e))return e.map(e=>({value:parseInt(e.structured_scope_id,10),label:`${e.asset_identifier} (${parseInt(e.structured_scope_id,10)})`,belongsToGroupId:`all-assets`})).concat({value:null,label:`(not set)`,belongsToGroupId:`all-assets`}).filter((e,t,n)=>n.findIndex(t=>t.value===e.value)===t)},u=e=>{if(!(0,s.isEmpty)(e))return e.map(e=>{let t=e.asset_type;return{value:t,label:window.constants&&window.constants.assetTypes&&window.constants.assetTypes[t]&&window.constants.assetTypes[t].readableName||t,belongsToGroupId:`all-asset-types`}}).concat({value:null,label:`(not set)`,belongsToGroupId:`all-asset-types`}).filter((e,t,n)=>n.findIndex(t=>t.value===e.value)===t).sort((e,t)=>e.label===`(not set)`?1:t.label===`(not set)`?-1:e.label.localeCompare(t.label))},d=e=>{if(!(0,s.isEmpty)(e))return e.map(e=>({value:parseInt(e.id,10),label:e.name,belongsToGroupId:`all-weakness-types`})).concat({value:null,label:`(not set)`,belongsToGroupId:`all-weakness-types`}).filter((e,t,n)=>n.findIndex(t=>t.value===e.value)===t)},f=e=>{if(!(0,s.isEmpty)(e))return e.map(e=>({value:parseInt(e._id,10),label:e.name||``})).filter((e,t,n)=>n.findIndex(t=>t.value===e.value)===t)},p=e=>(0,s.isEmpty)(e)?[]:e.flatMap(e=>{let t=new Map;return e.custom_field_values.nodes.forEach(e=>{let n=e.value||``,r=parseInt(e._id,10);t.has(n)||t.set(n,[]),t.get(n).push(r)}),Array.from(t.entries()).map(([t,n])=>({value:n,label:t,belongsToGroupId:e._id,belongsToGroupLabel:e.label}))}),m=/^(dim_|mv_|fct_|amazon_)/,h=(e,t)=>t===`number`&&e!==`__not_set__`?Number(e):e,g=(e,t)=>{let n=new Map((t||[]).map(e=>[e.key,e]));return(e||[]).map(e=>{let t=e.filters||{},r=Object.keys(t);if(r.some(e=>m.test(e)||t[e]?.where?.predicates))return{...e,filters:{}};if(n.size===0)return{...e,filters:t};let i={};return r.forEach(e=>{let r=n.get(e);if(!r)return;if(r.filter_type===`numeric`){i[e]=t[e];return}let a=new Set((r.options||[]).map(e=>h(e.value,r.value_type))),o=(Array.isArray(t[e])?t[e]:[]).map(e=>h(e,r.value_type)).filter(e=>e===`__not_set__`||a.has(e));o.length>0&&(i[e]=o)}),{...e,filters:i}})},_=e=>e.map(e=>{if(e.filter_type===`numeric`)return{label:e.label,filterType:`numeric`,operators:e.operators??[],...e.tooltip?{tooltip:e.tooltip}:{},...e.description?{description:e.description}:{},getValuesFromFilters:t=>{let n=t[e.key],r=n?.values?.[0];return r==null||r===``?[]:[{value:r,operator:n.operator}]},toQuery:(t,n)=>{let r=n?.value;if(r==null||r===``){let{[e.key]:n,...r}=t;return r}return{...t,[e.key]:{values:[Number(r)],operator:n.operator??e.operators?.[0]?.value??`eq`}}}};let t=[...new Map(e.options.filter(e=>e.group).map(e=>[e.group,{id:e.group,label:e.group}])).values()];return{label:e.label,...e.tooltip?{tooltip:e.tooltip}:{},...e.description?{description:e.description}:{},getValuesFromFilters:t=>t[e.key]||[],toQuery:(t,n)=>{if(!n||n.length===0){let{[e.key]:n,...r}=t;return r}return{...t,[e.key]:n}},options:{...t.length>0?{checkboxGroups:t}:{},checkboxes:e.options.map(t=>({value:e.value_type===`number`&&t.value!==`__not_set__`?Number(t.value):t.value,label:t.label,...t.group?{belongsToGroupId:t.group}:{},...t.subtext?{subtext:t.subtext}:{}}))}}});export{c as a,g as c,p as i,o as l,l as n,f as o,u as r,d as s,_ as t};
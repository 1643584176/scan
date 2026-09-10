import{o as e}from"./rolldown-runtime-DAXXjFlN.js";import{$_ as t,By as n,Ca as r,Ci as i,Cp as a,Fw as o,Gb as s,Hi as c,Hy as l,Iw as u,Kx as d,Ly as f,Pb as p,Pf as m,Q_ as h,Qd as g,Qy as _,R_ as v,Rw as y,Uu as b,Ux as x,Vx as S,Wx as ee,X_ as te,Z_ as C,br as w,db as T,h_ as E,ma as D,nb as O,ov as ne,qx as k,sd as A,sv as re,tb as j,zx as ie}from"./vendor-_WdvpBLr.js";import{$f as M,Bm as ae,Cp as N,Oi as oe,Qs as se,Sm as P,Th as ce,Tm as F,Wi as le,_h as ue,cf as de,ep as fe,fc as pe,fl as me,fm as he,gc as ge,gh as I,pc as L,rc as R,sm as z,tc as _e,uc as ve,uh as B,ui as ye,vh as V,vm as H,yl as U}from"./app-5pKgUmmm.js";import{t as be}from"./outline-CMBCGQ5D.js";import{n as xe}from"./bounty_competitiveness-Byys0NW5.js";import{t as Se}from"./custom_message_dialog-CrE8EryV.js";var W=e(y()),G=e(ie());k();var K=d`
  mutation UpdateBountyTable(
    $team_id: ID!
    $bounty_table_rows: [BountyTableRowInput!]!
    $use_range: Boolean
    $low_label: String!
    $medium_label: String!
    $high_label: String!
    $critical_label: String!
    $description: String
    $notify_subscribers_of_changes: Boolean
    $custom_message: String
    $reward_category_id: ID
  ) {
    updateBountyTable(
      input: {
        team_id: $team_id
        use_range: $use_range
        bounty_table_rows: $bounty_table_rows
        low_label: $low_label
        medium_label: $medium_label
        high_label: $high_label
        critical_label: $critical_label
        description: $description
        notify_subscribers_of_changes: $notify_subscribers_of_changes
        custom_message: $custom_message
        reward_category_id: $reward_category_id
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
        bounty_table {
          id
          low_label
          medium_label
          high_label
          critical_label
          description
          use_range
          reward_category {
            id
            name
          }
          bounty_table_rows(first: 100) {
            edges {
              node {
                id
                low
                medium
                high
                critical
                low_minimum
                medium_minimum
                high_minimum
                critical_minimum
                use_range
                smart_rewards_start_at
                name
                description
                structured_scope {
                  id
                }
                asm_tags(first: 50) {
                  edges {
                    node {
                      id
                      name
                    }
                  }
                }
              }
            }
          }
        }
      }
    }
  }
`;k();var Ce=d`
  mutation RemoveBountyTable($bounty_table_id: ID!) {
    removeBountyTable(input: { bounty_table_id: $bounty_table_id }) {
      was_successful
      team {
        id
        bounty_table {
          id
        }
      }
    }
  }
`,q=o(),we=({header:e,count:t,children:n})=>{let[r,i]=(0,W.useState)(!1);return(0,q.jsxs)(`div`,{className:`py-md`,children:[(0,q.jsxs)(`button`,{type:`button`,className:`flex w-full items-center justify-start text-left gap-x-sm`,onClick:()=>{i(!r)},children:[(0,q.jsx)(`span`,{className:`transition-transform duration-200 ${r?`rotate-180`:``}`,children:(0,q.jsx)(O,{src:a,accessibilityLabel:r?`Collapse`:`Expand`})}),(0,q.jsxs)(`div`,{className:`flex flex-row gap-x-2xs`,children:[(0,q.jsx)(`span`,{className:`font-medium`,children:t}),e]})]}),r&&(0,q.jsx)(`div`,{className:`mt-sm ml-sm`,children:n})]})},Te=({warnings:e,loading:t,orgHandle:n,categoryName:r})=>{if(t===!0||!e)return null;let{untagged_assets:i,unmapped_tags:a}=e;return i.length>0||a.length>0?(0,q.jsx)(`div`,{className:`my-lg rounded-md bg-yellow-900 border border-solid border-yellow-300 p-md dark:bg-yellow-50 pb-lg`,children:(0,q.jsxs)(`div`,{className:`flex items-start gap-x-sm`,children:[(0,q.jsx)(`div`,{className:`mt-1px`,children:(0,q.jsx)(O,{src:l,accessibilityLabel:`Warning`})}),(0,q.jsxs)(`div`,{className:`flex flex-1 gap-y-md flex-col`,children:[(0,q.jsxs)(`div`,{className:`flex flex-col gap-y-xs`,children:[(0,q.jsx)(ne,{size:re.Scale300,children:`Fix in-scope tagging and reward mappings`}),(0,q.jsx)(`p`,{children:`Some of your in-scope assets can't be assigned yet because they're either missing a tag in the selected category or using tags that aren't assigned to a reward group. Review the items below to either add the required tags / map tags to a reward table, or remove the in-scope flag from assets that shouldn't be included.`})]}),(0,q.jsxs)(`div`,{className:`flex flex-col divide-y divide-y-sm divide-solid divide-neutral-700 dark:divide-neutral-300`,children:[i.length>0&&(0,q.jsxs)(we,{count:i.length,header:`assets missing required tag`,children:[(0,q.jsxs)(`p`,{children:[`These assets are marked in scope but don't have any tag from the `,(0,q.jsx)(`strong`,{children:r}),` category. To continue,`,` `,(0,q.jsx)(`a`,{href:`/organizations/${n}/assets`,children:`add a tag in Asset Inventory`}),` `,`or remove the in-scope flag for assets that shouldn't be included.`]}),(0,q.jsx)(`ul`,{className:`mt-sm list-disc pl-lg text-sm font-bold`,children:i.map(e=>(0,q.jsx)(`li`,{children:e.asset_identifier},e.id))})]}),a.length>0&&(0,q.jsxs)(we,{count:a.length,header:`tags not mapped to a reward group`,children:[(0,q.jsxs)(`p`,{children:[`These tags are applied to in-scope assets but aren't assigned to a reward group. To resolve this, assign each tag to a reward table, or`,` `,(0,q.jsx)(`a`,{href:`/organizations/${n}/assets`,children:`remove the in-scope flag from the assets using that tag`}),`.`]}),(0,q.jsx)(`div`,{className:`mt-sm flex flex-wrap gap-xs`,children:a.map(e=>(0,q.jsx)(m,{rounded:!1,icons:{left:{accessibilityLabel:`Tag icon`,src:`data:image/svg+xml,%3csvg%20xmlns='http://www.w3.org/2000/svg'%20width='24'%20height='24'%20viewBox='0%200%2024%2024'%3e%3cpath%20d='M17.63%205.84C17.27%205.33%2016.67%205%2016%205L5%205.01C3.9%205.01%203%205.9%203%207v10c0%201.1.9%201.99%202%201.99L16%2019c.67%200%201.27-.33%201.63-.84L22%2012l-4.37-6.16zM16%2017H5V7h11l3.55%205L16%2017z'/%3e%3c/svg%3e`}},children:e.name},e.id))})]})]})]})]})}):null},Ee=N(`
  query TeamRewardCategory($handle: String!) {
    team(handle: $handle) {
      id
      organization {
        id
        handle
      }
      bounty_table {
        id
        reward_category {
          id
          name
        }
      }
    }
  }
`),De=N(`
  query RewardCategoryWarningsData($handle: String!, $asmTagCategoryId: ID!) {
    team(handle: $handle) {
      id
      reward_category_warnings(asm_tag_category_id: $asmTagCategoryId) {
        untagged_assets {
          id
          asset_identifier
        }
        unmapped_tags {
          id
          name
        }
        mapped_tags {
          id
          name
        }
      }
    }
  }
`),Oe=({teamHandle:e,assignedTagIds:t=[]})=>{let{data:n}=x(Ee,{variables:{handle:e}}),r=n?.team?.bounty_table?.reward_category?.id,i=n?.team?.bounty_table?.reward_category?.name,a=n?.team?.organization?.handle,{data:o,loading:s}=x(De,{variables:{handle:e,asmTagCategoryId:r??``},skip:!r,fetchPolicy:`network-only`}),c=o?.team?.reward_category_warnings,l=(0,W.useMemo)(()=>{if(!c)return c;let e=new Set(t),n=c.unmapped_tags.filter(t=>!e.has(t.id)),r=(c.mapped_tags??[]).filter(t=>!e.has(t.id));return{...c,unmapped_tags:[...n,...r]}},[c,t]),u=(0,W.useRef)(!1);return(0,W.useEffect)(()=>{if(u.current||!l)return;let t=l.untagged_assets.length,n=l.unmapped_tags.length;t===0&&n===0||(u.current=!0,ye(`scope rewards warnings shown`,{team_handle:e,untagged_assets_count:t,unmapped_tags_count:n}))},[l,e]),r?(0,q.jsx)(Te,{warnings:l,loading:s,orgHandle:a??``,categoryName:i}):null},ke=({groupNames:e})=>e.length===0?null:(0,q.jsx)(`div`,{className:`my-lg rounded-md bg-yellow-900 border border-solid border-yellow-300 p-md dark:bg-yellow-50 pb-lg`,role:`alert`,children:(0,q.jsxs)(`div`,{className:`flex items-start gap-x-sm`,children:[(0,q.jsx)(`div`,{className:`mt-1px`,children:(0,q.jsx)(O,{src:l,accessibilityLabel:`Warning`})}),(0,q.jsxs)(`div`,{className:`flex flex-1 gap-y-md flex-col`,children:[(0,q.jsxs)(`div`,{className:`flex flex-col gap-y-xs`,children:[(0,q.jsx)(ne,{size:re.Scale300,children:`Reward groups with no in-scope assets`}),(0,q.jsx)(`p`,{children:`The following reward groups have no in-scope assets linked to their tags. They will not be visible to hackers and will not appear in opportunities search.`})]}),(0,q.jsx)(`div`,{className:`flex flex-wrap gap-xs`,children:e.map((e,t)=>(0,q.jsx)(m,{rounded:!1,icons:{left:{accessibilityLabel:`Tag icon`,src:be}},children:e},t))})]})]})}),Ae=e(c()),je=e(E()),J=`ALL_ASSETS`,Y={CHANGE_LOW:`CHANGE_LOW`,CHANGE_LOW_MINIMUM:`CHANGE_LOW_MINIMUM`,CHANGE_MEDIUM:`CHANGE_MEDIUM`,CHANGE_MEDIUM_MINIMUM:`CHANGE_MEDIUM_MINIMUM`,CHANGE_HIGH:`CHANGE_HIGH`,CHANGE_HIGH_MINIMUM:`CHANGE_HIGH_MINIMUM`,CHANGE_CRITICAL:`CHANGE_CRITICAL`,CHANGE_CRITICAL_MINIMUM:`CHANGE_CRITICAL_MINIMUM`,CHANGE_LOW_LABEL:`CHANGE_LOW_LABEL`,CHANGE_MEDIUM_LABEL:`CHANGE_MEDIUM_LABEL`,CHANGE_HIGH_LABEL:`CHANGE_HIGH_LABEL`,CHANGE_CRITICAL_LABEL:`CHANGE_CRITICAL_LABEL`,ADD_ERRORS:`ADD_ERRORS`,CHANGE_DESCRIPTION:`CHANGE_DESCRIPTION`,CHANGE_STRUCTURED_SCOPE:`CHANGE_STRUCTURED_SCOPE`,ADD_BOUNTY_TABLE_ROW:`ADD_BOUNTY_TABLE_ROW`,REMOVE_BOUNTY_TABLE_ROW:`REMOVE_BOUNTY_TABLE_ROW`,TOGGLE_NOTIFY_SUBSCRIBERS_OF_CHANGES:`TOGGLE_NOTIFY_SUBSCRIBERS_OF_CHANGES`,TOGGLE_CUSTOM_MESSAGE_MODAL:`TOGGLE_CUSTOM_MESSAGE_MODAL`,SET_CUSTOM_MESSAGE:`SET_CUSTOM_MESSAGE`,CLEAR_CUSTOM_MESSAGE:`CLEAR_CUSTOM_MESSAGE`,RESET:`RESET`,ENABLE_SMART_REWARDS:`ENABLE_SMART_REWARDS`,DISABLE_SMART_REWARDS:`DISABLE_SMART_REWARDS`,CHANGE_ROW_NAME:`CHANGE_ROW_NAME`,CHANGE_ROW_DESCRIPTION:`CHANGE_ROW_DESCRIPTION`,CHANGE_ROW_TAGS:`CHANGE_ROW_TAGS`,TOGGLE_ROW_USE_RANGE:`TOGGLE_ROW_USE_RANGE`},Me=e=>e===null?[{destroyed:{value:!1,type:Boolean,errors:[]},disabled:{value:!1,type:Boolean,errors:[]},id:{value:null,type:String,errors:[]},low:{value:``,type:Number,errors:[]},medium:{value:``,type:Number,errors:[]},high:{value:``,type:Number,errors:[]},critical:{value:``,type:Number,errors:[]},low_minimum:{value:``,type:Number,errors:[]},medium_minimum:{value:``,type:Number,errors:[]},high_minimum:{value:``,type:Number,errors:[]},critical_minimum:{value:``,type:Number,errors:[]},smart_rewards_start_at:{value:``,type:Date,errors:[]},structured_scope_id:{value:J,type:J,errors:[]},name:{value:``,type:String,errors:[]},row_description:{value:``,type:String,errors:[]},asm_tag_ids:{value:[],type:Array,errors:[]},row_use_range:{value:!1,type:Boolean,errors:[]},has_scoped_assets:{value:!0,type:Boolean,errors:[]}}]:e.bounty_table_rows.edges.map(e=>({destroyed:{value:!1,type:Boolean,errors:[]},id:{value:e.node.id,type:String,errors:[]},low:{value:e.node.low||``,type:Number,errors:[]},medium:{value:e.node.medium||``,type:Number,errors:[]},high:{value:e.node.high||``,type:Number,errors:[]},critical:{value:e.node.critical||``,type:Number,errors:[]},low_minimum:{value:e.node.low_minimum||``,type:Number,errors:[]},medium_minimum:{value:e.node.medium_minimum||``,type:Number,errors:[]},high_minimum:{value:e.node.high_minimum||``,type:Number,errors:[]},critical_minimum:{value:e.node.critical_minimum||``,type:Number,errors:[]},smart_rewards_start_at:{value:e.node.smart_rewards_start_at||``,type:Date,errors:[]},structured_scope_id:{value:e.node.structured_scope&&e.node.structured_scope.id||`ALL_ASSETS`,type:J,errors:[]},name:{value:e.node.name||``,type:String,errors:[]},row_description:{value:e.node.description||``,type:String,errors:[]},asm_tag_ids:{value:(e.node.asm_tags?.edges||[]).map(e=>e.node.id),type:Array,errors:[]},row_use_range:{value:e.node.use_range??!1,type:Boolean,errors:[]},has_scoped_assets:{value:e.node.has_scoped_assets??!0,type:Boolean,errors:[]}})),X=e=>({form:{rows:{type:Array,value:Me(e)},low_label:{value:e&&e.low_label||`Low`,type:String,errors:[]},medium_label:{value:e&&e.medium_label||`Medium`,type:String,errors:[]},high_label:{value:e&&e.high_label||`High`,type:String,errors:[]},critical_label:{value:e&&e.critical_label||`Critical`,type:String,errors:[]},use_range:{value:e?e.use_range:!1,type:Boolean,errors:[]},description:{value:e&&e.description||``,type:String,errors:[]},notify_subscribers_of_changes:{value:!0,type:Boolean,errors:[]},show_custom_message_modal:{value:!1,type:Boolean,errors:[]},custom_message:{value:``,type:String,errors:[]}}}),Ne=(e,t={})=>{switch(t.type){case Y.CHANGE_CRITICAL_LABEL:{let n={...e};return n.form.critical_label={...n.form.critical_label,value:t.value,errors:[]},n}case Y.CHANGE_HIGH_LABEL:{let n={...e};return n.form.high_label={...n.form.high_label,value:t.value,errors:[]},n}case Y.CHANGE_MEDIUM_LABEL:{let n={...e};return n.form.medium_label={...n.form.medium_label,value:t.value,errors:[]},n}case Y.CHANGE_LOW_LABEL:{let n={...e};return n.form.low_label={...n.form.low_label,value:t.value,errors:[]},n}case Y.TOGGLE_USE_RANGE:{let t={...e};return t.form.use_range={...t.form.use_range,value:!e.form.use_range.value,errors:[]},t}case Y.CHANGE_ROW_NAME:{let n={...e};return n.form.rows.value[t.key].name={...n.form.rows.value[t.key].name,value:t.value,errors:[]},n}case Y.CHANGE_ROW_DESCRIPTION:{let n={...e};return n.form.rows.value[t.key].row_description={...n.form.rows.value[t.key].row_description,value:t.value,errors:[]},n}case Y.CHANGE_ROW_TAGS:{let n={...e};return n.form.rows.value[t.key].asm_tag_ids={...n.form.rows.value[t.key].asm_tag_ids,value:t.value,errors:[]},n}case Y.TOGGLE_ROW_USE_RANGE:{let n={...e};return n.form.rows.value[t.key].row_use_range={...n.form.rows.value[t.key].row_use_range,value:!e.form.rows.value[t.key].row_use_range.value,errors:[]},n}case Y.CHANGE_STRUCTURED_SCOPE:{let n={...e};return n.form.rows.value[t.key].structured_scope_id={...n.form.rows.value[t.key].structured_scope_id,value:t.value,errors:[]},n}case Y.CHANGE_LOW:{let n={...e};return n.form.rows.value[t.key].low={...n.form.rows.value[t.key].low,value:parseInt(t.value,10)||``,errors:[]},n}case Y.CHANGE_MEDIUM:{let n={...e};return n.form.rows.value[t.key].medium={...n.form.rows.value[t.key].medium,value:parseInt(t.value,10)||``,errors:[]},n}case Y.CHANGE_HIGH:{let n={...e};return n.form.rows.value[t.key].high={...n.form.rows.value[t.key].high,value:parseInt(t.value,10)||``,errors:[]},n}case Y.CHANGE_CRITICAL:{let n={...e};return n.form.rows.value[t.key].critical={...n.form.rows.value[t.key].critical,value:parseInt(t.value,10)||``,errors:[]},n}case Y.CHANGE_LOW_MINIMUM:{let n={...e};return n.form.rows.value[t.key].low_minimum={...n.form.rows.value[t.key].low_minimum,value:parseInt(t.value,10)||``,errors:[]},n}case Y.CHANGE_MEDIUM_MINIMUM:{let n={...e};return n.form.rows.value[t.key].medium_minimum={...n.form.rows.value[t.key].medium_minimum,value:parseInt(t.value,10)||``,errors:[]},n}case Y.CHANGE_HIGH_MINIMUM:{let n={...e};return n.form.rows.value[t.key].high_minimum={...n.form.rows.value[t.key].high_minimum,value:parseInt(t.value,10)||``,errors:[]},n}case Y.CHANGE_CRITICAL_MINIMUM:{let n={...e};return n.form.rows.value[t.key].critical_minimum={...n.form.rows.value[t.key].critical_minimum,value:parseInt(t.value,10)||``,errors:[]},n}case Y.ADD_ERRORS:{let n={...e};return n.form={...n.form},n.form.rows={...n.form.rows},n.form.rows.value=[...n.form.rows.value],Object.keys(t.value).forEach(e=>{let r=/^(.*?)\[(\d*)\]\.(.*)$/.exec(e);if(r===null)n.form[e]&&(n.form[e]={...n.form[e],errors:t.value[e]});else{let i=parseInt(r[2],10),a=n.form.rows.value[i];a&&a[r[3]]&&(n.form.rows.value[i]={...a,[r[3]]:{...a[r[3]],errors:t.value[e]}})}}),n}case Y.ADD_BOUNTY_TABLE_ROW:{let t={...e};return t.form.rows.value=t.form.rows.value.concat(Me(null)),t}case Y.CHANGE_DESCRIPTION:{let n={...e};return n.form.description={...n.form.description,value:t.value,errors:[]},n}case Y.REMOVE_BOUNTY_TABLE_ROW:{let n={...e};return n.form.rows.value[t.key].destroyed.value=!0,n}case Y.TOGGLE_NOTIFY_SUBSCRIBERS_OF_CHANGES:{let t={...e};return t.form.notify_subscribers_of_changes.value=!t.form.notify_subscribers_of_changes.value,t}case Y.TOGGLE_CUSTOM_MESSAGE_MODAL:{let t={...e};return t.form.show_custom_message_modal.value=!t.form.show_custom_message_modal.value,t}case Y.SET_CUSTOM_MESSAGE:{let n={...e};return n.form.custom_message.value=t.value.substring(0,constants.notification.custom_message_character_limit),n}case Y.CLEAR_CUSTOM_MESSAGE:{let t={...e};return t.form.custom_message.value=``,t}case Y.RESET:return X(t.bountyTable);case Y.ENABLE_SMART_REWARDS:return(0,je.default)({},e,{form:{rows:{value:{[t.key]:{smart_rewards_start_at:{value:t.value}}}}}});case Y.DISABLE_SMART_REWARDS:return(0,je.default)({},e,{form:{rows:{value:{[t.key]:{smart_rewards_start_at:{value:null}}}}}});default:return e}},Pe=e=>{let t=e=>e===``||e===null?null:parseInt(e,10),n=e=>e===null?null:String(e),r=e=>e===null?null:new Date(e),i=e=>(0,Ae.default)(e,e=>{let a={...e};switch(a.type){case Array:a.mutationValue=a.value.length>0&&typeof a.value[0]==`object`&&a.value[0]!==null?a.value.map(e=>i(e)):a.value;break;case J:a.mutationValue=a.value===`ALL_ASSETS`?null:n(a.value);break;case Number:a.mutationValue=t(a.value);break;case String:a.mutationValue=n(a.value);break;case Date:a.mutationValue=r(a.value);break;case Boolean:a.mutationValue=a.value;break;default:a.mutationValue=a.value}return a}),a={...e};return a.form=i(a.form),a},Z=W.createContext({store:X(null),dispatch:e=>null}),Fe=(e,t={})=>Pe(Ne(e,t),t),Ie=({children:e,maybeBountyTable:t})=>{let[n,r]=(0,W.useReducer)(Fe,X(t));return(0,q.jsx)(Z.Provider,{value:{store:n,dispatch:r},children:e})};Ie.propTypes={children:G.default.node.isRequired,maybeBountyTable:G.default.object};var Q=e(p()),Le=[{rating:`critical`,action:Y.CHANGE_CRITICAL_LABEL,key:`critical_label`,name:`spec-bounty-table-critical-label`,id:`table-heading-critical`},{rating:`high`,action:Y.CHANGE_HIGH_LABEL,key:`high_label`,name:`spec-bounty-table-high-label`,id:`table-heading-high`},{rating:`medium`,action:Y.CHANGE_MEDIUM_LABEL,key:`medium_label`,name:`spec-bounty-table-medium-label`,id:`table-heading-medium`},{rating:`low`,action:Y.CHANGE_LOW_LABEL,key:`low_label`,name:`spec-bounty-table-low-label`,id:`table-heading-low`}],$=({showNewFlow:e})=>{let{store:t,dispatch:n}=(0,W.useContext)(Z),r=e=>({name:e.name,id:e.id,type:`text`,hasErrors:Q.default.any.existy(t.form[e.key].errors),value:t.form[e.key].value,onChange:t=>n({value:t.target.value,type:e.action})});return e?(0,q.jsxs)(`div`,{className:`mb-lg`,children:[(0,q.jsx)(`p`,{className:`font-bold`,children:`Reward value labels`}),(0,q.jsx)(`p`,{className:`text-neutral-200 dark:text-neutral-900 mt-0`,children:`Customize the labels shown for each severity level across all reward groups.`}),(0,q.jsx)(`div`,{className:`mt-md flex gap-x-lg`,children:Le.map(e=>(0,q.jsxs)(`div`,{className:`flex items-center gap-x-xs`,children:[(0,q.jsx)(U,{rating:e.rating,showScore:!1,showLabel:!1}),(0,q.jsx)(`div`,{className:`w-[140px]`,children:(0,q.jsx)(R,{...r(e)})})]},e.rating))})]}):(0,q.jsxs)(q.Fragment,{children:[(0,q.jsx)(L,{htmlFor:`table-heading-critical`,children:`Bounty table heading`}),(0,q.jsx)(B,{size:`large`,children:(0,q.jsx)(I,{children:(0,q.jsx)(I.Row,{children:Le.map(e=>(0,q.jsx)(I.Column,{size:`one-quarter`,children:(0,q.jsx)(R,{prefix:(0,q.jsx)(`div`,{className:`mt-xs`,children:(0,q.jsx)(U,{rating:e.rating,showScore:!1,showLabel:!1})}),...r(e)})},e.rating))})})})]})};$.propTypes={showNewFlow:G.default.bool};var Re=e(u()),ze=({useRange:e,name:t,field:n,minimumField:r,onChange:i,onChangeMinimum:a,disabled:o})=>{let s=e?r?.errors:[],c=n.errors,l=[...s||[],...c||[]].filter(Boolean);return(0,q.jsxs)(`div`,{className:`flex flex-col`,children:[(0,q.jsxs)(`div`,{className:`flex items-center space-x-[8px]`,children:[(0,q.jsx)(`div`,{className:`flex justify-center items-center max-w-[100px]`,children:e&&(0,q.jsx)(`div`,{className:`flex flex-col`,children:(0,q.jsx)(R,{prefix:`$`,name:`${t}-minimum`,className:`${t}-minimum mr-2`,type:`number`,value:r.value,disabled:o||!r,onChange:a,hasErrors:Q.default.any.existy(r?.errors),placeholder:`min`})})}),e&&(0,q.jsx)(`div`,{className:`flex space-x-[8px] items-center`,children:`-`}),(0,q.jsx)(`div`,{className:`max-w-[100px]`,children:(0,q.jsx)(`div`,{className:`flex flex-col`,children:(0,q.jsx)(R,{prefix:`$`,name:t,type:`number`,value:n.value,hasErrors:Q.default.any.existy(n.errors),disabled:o,onChange:i,placeholder:`max`})})})]}),l.length>0&&(0,q.jsx)(`div`,{className:`text-red-600 text-sm mt-2xs`,children:l.join(`, `)})]})};ze.propTypes={name:G.default.string.isRequired,useRange:G.default.bool.isRequired,field:G.default.object.isRequired,minimumField:G.default.object,onChange:G.default.func.isRequired,onChangeMinimum:G.default.func,disabled:G.default.bool};var Be=({bountyTableRowId:e,isEnabled:t,isLoading:n,onEnable:r,onDisable:i,useRange:a})=>{let[o,s]=(0,W.useState)(t),[c,l]=(0,W.useState)(!1),u=async()=>{(o?await i(e):await r(e))&&s(!o)},d=(0,q.jsx)(b,{testId:`toggle-bounty-pilot`,accessibilityLabel:`Switch to toggle Bounty Autopilot`,checked:o,onChange:()=>{u()},disabled:n||a||!e});return(0,q.jsx)(q.Fragment,{children:(0,q.jsx)(`div`,{className:`ml-spacing-16 my-spacing-24`,style:{maxWidth:`510px`},children:(0,q.jsxs)(g,{children:[(0,q.jsxs)(`div`,{className:`flex justify-between`,children:[(0,q.jsx)(`span`,{className:`text-2xl flex items-center gap-xs`,children:`Bounty Autopilot`}),a?(0,q.jsx)(T,{text:`Bounty Autopilot is not available when using a range. Please use fixed bounty values before enabling Bounty Autopillot.`,children:d}):d]}),(0,q.jsxs)(`p`,{className:`text-neutral-400 dark:text-neutral-950`,children:[`Increase hacker engagement by letting HackerOne's A.I. optimize bounties using market-based algorithms. Disabling Bounty Autopilot will freeze the bounty rewards to the current values.`,(0,q.jsxs)(`a`,{onClick:()=>{l(!0)},children:[` `,`See how it works`]}),c&&(0,q.jsxs)(fe,{shouldCloseOnEsc:!0,showModal:c,buttonText:`Got it, thanks!`,buttonColor:`blue`,size:`small`,handleButtonClick:()=>{l(!1)},handleCloseModal:()=>{l(!1)},children:[(0,q.jsx)(`h1`,{className:`modal-title`,style:{maxWidth:`400px`},children:`How does Bounty Autopilot work?`}),(0,q.jsxs)(M,{children:[(0,q.jsx)(M.Item,{className:`my-spacing-16`,children:`Once you enable Autopilot, the bounty amount will increase on average by approx. 12% each week.`}),(0,q.jsx)(M.Item,{className:`my-spacing-16`,children:`Autopilot will continue to increase the bounties for 90 days or until a high or critical vulnerability is resolved.`}),(0,q.jsx)(M.Item,{className:`my-spacing-16`,children:`Once a vulnerability is resolved, the bounty amount is locked, and Autopilot will deactivate.`}),(0,q.jsx)(M.Item,{className:`my-spacing-16`,children:`If there are no valid submissions after 90 days, the rewards will cap at a maximum of 2x the initial bounty.`})]})]})]})]})})})},Ve=N(`
  mutation EnableSmartRewards($input: EnableSmartRewardsInput!) {
    enableSmartRewards(input: $input) {
      bounty_table_row {
        id
        smart_rewards_start_at
      }
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
`),He=N(`
  mutation DisableSmartRewards($input: DisableSmartRewardsInput!) {
    disableSmartRewards(input: $input) {
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
`),Ue=e=>{P(`error`,`Something went wrong: ${e.join(`, `)}`)},We=({bountyTableRowId:e,smartRewardsStartAt:t,useRange:n,keyProp:r})=>{let[i,{loading:a}]=S(Ve),[o,{loading:s}]=S(He),{dispatch:c}=(0,W.useContext)(Z);return(0,q.jsx)(Be,{bountyTableRowId:e,isEnabled:!!t,isLoading:a||s,onEnable:async e=>{try{let{data:t}=await i({variables:{input:{bounty_table_row_id:e}}}),n=!!t?.enableSmartRewards?.was_successful,a=(t?.enableSmartRewards?.errors?.edges??[]).flatMap(e=>{let t=e?.node?.message??``;return t===``?[]:[t]});if(n)return P(`notice`,`Bounty Autopilot has been enabled.`),c({type:Y.ENABLE_SMART_REWARDS,key:r,value:t?.enableSmartRewards?.bounty_table_row?.smart_rewards_start_at}),!0;a.length>0?Ue(a):H()}catch{H()}return!1},onDisable:async e=>{try{let{data:t}=await o({variables:{input:{bounty_table_row_id:e}}}),n=!!t?.disableSmartRewards?.was_successful,i=(t?.disableSmartRewards?.errors?.edges??[]).flatMap(e=>{let t=e?.node?.message??``;return t===``?[]:[t]});if(n)return P(`notice`,`Bounty Autopilot has been disabled.`),c({type:Y.DISABLE_SMART_REWARDS,key:r}),!0;i.length>0?Ue(i):H()}catch{H()}return!1},useRange:n})},Ge=({visible:e,hasTags:t})=>e?(0,q.jsxs)(`div`,{className:`flex items-center gap-x-xs rounded-md bg-yellow-900 border border-solid border-yellow-300 p-sm dark:bg-yellow-50 text-sm`,role:`alert`,children:[(0,q.jsx)(O,{src:l,accessibilityLabel:`Warning`}),(0,q.jsx)(`span`,{children:t?`This reward group has no in-scope assets linked to its tags.`:`This reward group has no in-scope assets linked to it. Add a tag with linked assets that are in-scope.`})]}):null,Ke=({innerProps:e,innerRef:t,label:n,data:r,isFocused:i})=>{let a=r.disabled;return(0,q.jsx)(`div`,{ref:t,...e,onClick:a?e=>e.preventDefault():e.onClick,className:(0,Re.default)(`py-[0.625rem] px-xs`,a?`bg-neutral-900 text-neutral-400 dark:text-neutral-600 dark:bg-neutral-200 cursor-not-allowed pointer-events-none`:`cursor-pointer dark:text-neutral-950 hover:bg-blue-900 dark:hover:bg-neutral-100`,i&&!a&&`!bg-blue-900 dark:!bg-neutral-100`),children:n})};Ke.propTypes={innerProps:G.default.object,innerRef:G.default.any,label:G.default.string,data:G.default.object,isFocused:G.default.bool};var qe=({row:e,teamHandle:n,orgHandle:i,keyProp:a,useRange:o,dropdownOptions:s,showNewFlow:c,tagOptions:l=[],usedTagIds:u=[],saving:d=!1,hasNoScopedAssets:f=!1})=>{let{store:p,dispatch:m}=(0,W.useContext)(Z),g=d||!c&&!!e.smart_rewards_start_at.value,y=c?!!e.row_use_range?.value:o,[b,x]=(0,W.useState)(!1),S=(e,t)=>n=>m({value:n.target.value,key:e,type:t}),ee=le({low:e.low.value,medium:e.medium.value,high:e.high.value,critical:e.critical.value},2e3);return(0,q.jsx)(`span`,{className:(0,Re.default)(`spec-bounty-table-row`,{"display-none":e.destroyed.value}),children:(0,q.jsx)(`div`,{className:`mb-md`,children:(0,q.jsxs)(F,{children:[c?(0,q.jsx)(F.Content,{children:(0,q.jsxs)(`div`,{className:`flex flex-col gap-y-lg`,children:[(0,q.jsx)(r,{labelText:`Reward group name`,descriptionText:`Visible to hackers in the scope and rewards page.`,value:e.name?.value||``,disabled:d,maxLength:50,onChange:e=>m({value:e.target.value,key:a,type:Y.CHANGE_ROW_NAME}),invalid:e.name?.errors?.length>0,validationChildren:e.name?.errors?.length>0?e.name.errors.join(`, `):void 0,validationVariation:`danger`}),(0,q.jsxs)(`div`,{children:[(0,q.jsx)(t,{text:`Reward tags`}),(0,q.jsx)(h,{text:(0,q.jsxs)(q.Fragment,{children:[`Edit the tag names or add more options in`,` `,(0,q.jsx)(`a`,{href:`/organizations/${i}/assets`,children:`the Asset Inventory`}),`.`]})}),(0,q.jsx)(A,{isMulti:!0,disabled:d,invalid:e.asm_tag_ids?.errors?.length>0,selectedOption:l.filter(t=>(e.asm_tag_ids?.value||[]).includes(t.value)),onChange:e=>{m({value:(e||[]).map(e=>e.value),key:a,type:Y.CHANGE_ROW_TAGS})},options:l.map(e=>({...e,disabled:u.includes(e.value)})),optionComponent:Ke,placeholder:`Select one or more tags`}),e.asm_tag_ids?.errors?.length>0&&(0,q.jsx)(te,{variation:C.Danger,children:e.asm_tag_ids.errors.join(`, `)})]}),(0,q.jsx)(Ge,{visible:f,hasTags:(e.asm_tag_ids?.value||[]).length>0}),(0,q.jsxs)(`div`,{children:[(0,q.jsx)(`span`,{className:`font-bold`,children:`Reward value setting`}),(0,q.jsxs)(`div`,{className:`flex gap-x-md mt-xs`,children:[(0,q.jsx)(v,{checked:!e.row_use_range?.value,onChange:()=>e.row_use_range?.value&&m({key:a,type:Y.TOGGLE_ROW_USE_RANGE}),value:`fixed`,name:`use_range_${a}`,label:`Fixed`,disabled:d,accessibilityLabel:`Fixed reward values`}),(0,q.jsx)(v,{checked:!!e.row_use_range?.value,onChange:()=>!e.row_use_range?.value&&m({key:a,type:Y.TOGGLE_ROW_USE_RANGE}),value:`range`,name:`use_range_${a}`,label:`Range`,disabled:d,accessibilityLabel:`Range reward values`})]})]})]})}):(0,q.jsxs)(q.Fragment,{children:[(0,q.jsx)(F.Heading,{children:(0,q.jsx)(se,{fullWidth:!0,value:e.structured_scope_id.value,disabled:g,onChange:e=>{m({value:e.target.value,key:a,type:Y.CHANGE_STRUCTURED_SCOPE})},options:s})}),e.id.value&&(0,q.jsx)(We,{bountyTableRowId:e.id.value,smartRewardsStartAt:e.smart_rewards_start_at?.value,useRange:o,keyProp:a})]}),(0,q.jsxs)(F.Content,{children:[c&&(0,q.jsx)(`span`,{className:`font-bold`,children:`Reward values`}),(0,q.jsxs)(`div`,{className:`flex justify-between`,children:[(0,q.jsx)(`div`,{className:`flex flex-col gap-y-md flex-1`,children:[{rating:`critical`,label:p.form.critical_label.value,field:e.critical,min:e.critical_minimum,name:`spec-bounty-table-critical`,action:Y.CHANGE_CRITICAL,minAction:Y.CHANGE_CRITICAL_MINIMUM},{rating:`high`,label:p.form.high_label.value,field:e.high,min:e.high_minimum,name:`spec-bounty-table-high`,action:Y.CHANGE_HIGH,minAction:Y.CHANGE_HIGH_MINIMUM},{rating:`medium`,label:p.form.medium_label.value,field:e.medium,min:e.medium_minimum,name:`spec-bounty-table-medium`,action:Y.CHANGE_MEDIUM,minAction:Y.CHANGE_MEDIUM_MINIMUM},{rating:`low`,label:p.form.low_label.value,field:e.low,min:e.low_minimum,name:`spec-bounty-table-low`,action:Y.CHANGE_LOW,minAction:Y.CHANGE_LOW_MINIMUM}].map(e=>(0,q.jsxs)(`div`,{className:`flex items-start`,children:[(0,q.jsxs)(`div`,{className:`flex items-center gap-x-xs w-[120px] shrink-0 h-[40px]`,children:[(0,q.jsx)(U,{rating:e.rating,showScore:!1,showLabel:!1}),e.label]}),(0,q.jsx)(ze,{name:e.name,useRange:y,field:e.field,minimumField:e.min,disabled:g,onChange:S(a,e.action),onChangeMinimum:S(a,e.minAction)})]},e.rating))}),(0,q.jsx)(`div`,{className:`my-auto flex justify-center max-w-[300px] flex-[3]`,children:b?(0,q.jsx)(de,{children:(0,q.jsx)(xe,{teamHandle:n,bountyTableRow:ee,high:1,critical:1})}):(0,q.jsx)(_,{variation:`ghost`,onClick:()=>x(!0),children:`Calculate Reward Competitiveness`})})]}),c&&(0,q.jsx)(`div`,{className:`mt-lg`,children:(0,q.jsx)(D,{labelText:`Reward group description (Optional)`,value:e.row_description?.value||``,disabled:d,onChange:e=>m({value:e.target.value,key:a,type:Y.CHANGE_ROW_DESCRIPTION})})}),c?(0,q.jsx)(`div`,{className:`mt-lg`,children:(0,q.jsx)(_,{variation:j.DangerSecondary,small:!0,disabled:d,icons:{left:{src:w,accessibilityLabel:`Remove`}},onClick:()=>m({type:Y.REMOVE_BOUNTY_TABLE_ROW,key:a}),children:`Remove reward group`})}):a>0?(0,q.jsxs)(q.Fragment,{children:[(0,q.jsx)(z,{removeCardSpacing:!0,size:`small`}),g?(0,q.jsx)(`span`,{children:`This row cannot be manually updated because Bounty Autopilot is enabled. Contact your HackerOne program manager to change the settings.`}):(0,q.jsx)(`a`,{className:`daisy-text--red daisy-text--small spec-delete-link`,onClick:()=>m({type:Y.REMOVE_BOUNTY_TABLE_ROW,key:a}),children:`Remove this asset`})]}):null]})]})})},a)};qe.propTypes={row:G.default.object.isRequired,keyProp:G.default.number.isRequired,teamHandle:G.default.string.isRequired,orgHandle:G.default.string,useRange:G.default.bool.isRequired,dropdownOptions:G.default.array,competitivenessEnabled:G.default.bool,showNewFlow:G.default.bool,tagOptions:G.default.array,usedTagIds:G.default.array,saving:G.default.bool,hasNoScopedAssets:G.default.bool};var Je=W.memo(qe),Ye=e(s()),Xe=()=>{let{store:e,dispatch:t}=(0,W.useContext)(Z),r=(0,W.useCallback)(()=>{t({type:Y.TOGGLE_USE_RANGE})},[t]),i=(0,Ye.default)(e?.form?.rows?.value,e=>!!e.smart_rewards_start_at?.value);return(0,q.jsxs)(q.Fragment,{children:[(0,q.jsx)(z,{removeCardSpacing:!0}),(0,q.jsx)(L,{children:`Bounty value setting`}),(0,q.jsxs)(`div`,{className:`mb-spacing-24`,children:[(0,q.jsxs)(`div`,{className:`flex gap-spacing-8`,children:[(0,q.jsx)(_e,{name:`range`,checked:!e.form.use_range.value,value:`Fixed`,onChange:r,disabled:i,children:`Fixed`}),(0,q.jsx)(_e,{name:`range`,checked:e.form.use_range.value,value:`Range`,onChange:r,disabled:i,children:`Range`})]}),i&&(0,q.jsx)(f,{variation:n.Information,contentPrimary:`There is currently at least one bounty table with Bounty Autopilot
            enabled. To enable bounty table ranges, please disable Bounty
            Autopilot for all bounty tables.`})]}),(0,q.jsx)(z,{removeCardSpacing:!0})]})};Xe.propTypes={};var Ze=({teamName:e})=>{let{store:t,dispatch:n}=(0,W.useContext)(Z);return(0,q.jsx)(`div`,{className:`pull-left`,children:(0,q.jsx)(B,{top:!0,size:`small`,children:(0,q.jsxs)(ve,{checked:t.form.notify_subscribers_of_changes.value,id:`notify_subscribers_of_changes`,name:`notify_subscribers_of_changes`,postfix:(0,q.jsx)(oe,{className:`margin-8--left`,tooltipText:`Users will be notified via web and email notifications of updates to your program.`,iconGlyph:ae}),onChange:e=>n({value:e.target.value,type:Y.TOGGLE_NOTIFY_SUBSCRIBERS_OF_CHANGES}),children:[`Notify subscribers of changes. \xA0`,(0,q.jsx)(Se,{teamName:e,showModal:t.form.show_custom_message_modal.value,customMessage:t.form.custom_message.value,onShowModal:()=>n({type:Y.TOGGLE_CUSTOM_MESSAGE_MODAL}),onCancel:()=>{n({type:Y.TOGGLE_CUSTOM_MESSAGE_MODAL}),n({value:``,type:Y.SET_CUSTOM_MESSAGE})},onChange:e=>n({value:e,type:Y.SET_CUSTOM_MESSAGE}),onSave:()=>n({type:Y.TOGGLE_CUSTOM_MESSAGE_MODAL})})]})})})};Ze.propTypes={teamName:G.default.string.isRequired},k();var Qe=d`
  query BountyTableSettings($handle: String!) {
    team(handle: $handle) {
      id
      handle
      name
      i_can_view_bounty_table
      bounty_table {
        id
        low_label
        medium_label
        high_label
        critical_label
        description
        use_range
        reward_category {
          id
          name
          asm_tags(first: 100) {
            edges {
              node {
                id
                name
              }
            }
          }
        }
        bounty_table_rows(first: 100) {
          edges {
            node {
              id
              low
              medium
              high
              critical
              low_minimum
              medium_minimum
              high_minimum
              critical_minimum
              use_range
              smart_rewards_start_at
              name
              description
              has_scoped_assets
              structured_scope {
                id
              }
              asm_tags(first: 50) {
                edges {
                  node {
                    id
                    name
                  }
                }
              }
            }
          }
        }
      }
      inactive_new_flow_bounty_table {
        id
        low_label
        medium_label
        high_label
        critical_label
        description
        use_range
        reward_category {
          id
          name
          asm_tags(first: 100) {
            edges {
              node {
                id
                name
              }
            }
          }
        }
        bounty_table_rows(first: 100) {
          edges {
            node {
              id
              low
              medium
              high
              critical
              low_minimum
              medium_minimum
              high_minimum
              critical_minimum
              use_range
              name
              description
              has_scoped_assets
              asm_tags(first: 50) {
                edges {
                  node {
                    id
                    name
                  }
                }
              }
            }
          }
        }
      }
      structured_scopes(first: 650) {
        edges {
          node {
            id
            asset_identifier
          }
        }
      }
      # TODO: Consider splitting into a separate query with @include(if: $showNewFlow) to avoid loading tag categories for old flow teams
      organization {
        id
        handle
        asm_tag_categories(first: 50) {
          edges {
            node {
              id
              _id
              name
              rewards_eligible
              unique_tag_per_asset
              asm_tags(first: 100) {
                edges {
                  node {
                    id
                    name
                  }
                }
              }
            }
          }
        }
      }
    }
  }
`,$e=d`
  query RewardEligibleCategories($handle: String!) {
    team(handle: $handle) {
      id
      reward_eligible_category_ids
    }
  }
`,et=d`
  query TagScopedAssets($handle: String!, $categoryId: ID!) {
    node(id: $categoryId) {
      ... on AsmTagCategory {
        id
        asm_tags(first: 100) {
          edges {
            node {
              id
              has_scoped_assets(team_handle: $handle)
            }
          }
        }
      }
    }
  }
`,tt=(e,t,n,{showNewFlow:r,selectedCategoryId:i}={})=>{let a=t.form.rows.mutationValue.filter(e=>r||!e.smart_rewards_start_at.value).map(e=>{let n=r?e.row_use_range?.value??!1:t.form.use_range.mutationValue,i={id:e.id.mutationValue,destroy:e.destroyed.value,low:e.low.mutationValue,medium:e.medium.mutationValue,high:e.high.mutationValue,critical:e.critical.mutationValue,low_minimum:n?e.low_minimum.mutationValue:null,medium_minimum:n?e.medium_minimum.mutationValue:null,high_minimum:n?e.high_minimum.mutationValue:null,critical_minimum:n?e.critical_minimum.mutationValue:null};return r?{...i,use_range:n,name:e.name?.value||null,description:e.row_description?.value||null,asm_tag_ids:e.asm_tag_ids?.value||[]}:{...i,structured_scope_id:e.structured_scope_id.mutationValue}}),o={team_id:n.id,bounty_table_rows:a,use_range:t.form.use_range.mutationValue,low_label:t.form.low_label.mutationValue,medium_label:t.form.medium_label.mutationValue,high_label:t.form.high_label.mutationValue,critical_label:t.form.critical_label.mutationValue,description:t.form.description.mutationValue,notify_subscribers_of_changes:t.form.notify_subscribers_of_changes.mutationValue,custom_message:t.form.custom_message.mutationValue};r&&i&&(o.reward_category_id=i),e({variables:o})},nt=(e,t)=>{e({variables:{bounty_table_id:t.id}})},rt=({team:e,isBbpOnboarding:t,showNewFlow:n,onSaveReady:r})=>{let{store:a,dispatch:o}=(0,W.useContext)(Z),s=ee(),[c,l]=(0,W.useState)(!1),u=(0,W.useRef)(!1),[d,f]=(0,W.useState)(e.bounty_table?.reward_category?.id||e.inactive_new_flow_bounty_table?.reward_category?.id||null),{data:p}=V($e,{variables:{handle:e.handle},skip:!n}),m=(0,W.useMemo)(()=>new Set(p?.team?.reward_eligible_category_ids||[]),[p]),{data:h}=V(et,{variables:{handle:e.handle,categoryId:d},skip:!n||!d}),g=(0,W.useMemo)(()=>{let e=new Map;return(h?.node?.asm_tags?.edges||[]).forEach(t=>{e.set(t.node.id,t.node.has_scoped_assets)}),e},[h]),v=(0,W.useMemo)(()=>n?a.form.rows.value.map(e=>{if(e.destroyed?.value)return!1;let t=e.asm_tag_ids?.value||[];return t.length===0?!0:g.size===0?!e.has_scoped_assets?.value:!t.some(e=>g.get(e)===!0)}):[],[a,g,n]),y=(0,W.useMemo)(()=>a.form.rows.value.filter((e,t)=>v[t]&&!e.destroyed?.value).map(e=>e.name?.value||`Unnamed group`),[a,v]),b=(0,W.useMemo)(()=>n?(e.organization?.asm_tag_categories?.edges||[]).filter(e=>e.node.rewards_eligible&&m.has(parseInt(e.node._id,10))).map(e=>({value:e.node.id,label:e.node.name})):[],[e,n,m]),x=(0,W.useMemo)(()=>{if(!n||!d)return[];let t=(e.organization?.asm_tag_categories?.edges||[]).find(e=>e.node.id===d);return t?(t.node.asm_tags?.edges||[]).map(e=>({value:e.node.id,label:e.node.name})):[]},[e,n,d]),S=(0,W.useMemo)(()=>{let t=e.structured_scopes.edges.map(e=>({value:e.node.id,label:e.node.asset_identifier}));return t.unshift({value:J,label:`All Assets`}),t},[e]),[te,{loading:C}]=ue(Ce,{onCompleted:({removeBountyTable:e})=>{e.was_successful&&(P(`notice`,`Bounty Table is successfully removed`),o({type:Y.RESET,bountyTable:null}))}}),[w,{loading:T}]=ue(K,{onCompleted:({updateBountyTable:e})=>{if(e.was_successful)P(`notice`,`Bounty Table is successfully updated`),u.current=!0,o({type:Y.RESET,bountyTable:e.team.bounty_table}),n&&s.refetchQueries({include:[`RewardCategoryWarningsData`,`TeamRewardCategory`,`TeamFeatureQuery`]});else{let t=ge(e.errors);o({value:t,type:Y.ADD_ERRORS})}}}),E=(0,W.useCallback)(()=>{if(n&&!d){P(`error`,`Please select a reward tag category before publishing.`);return}tt(w,a,e,{showNewFlow:n,selectedCategoryId:d})},[w,a,e,n,d]),D=(0,W.useRef)(!1);if((0,W.useEffect)(()=>{if(!D.current){D.current=!0;return}u.current?(u.current=!1,l(!1)):l(!0)},[a]),(0,W.useEffect)(()=>{n&&r&&r({triggerSave:E,isSaving:T,isDirty:c})},[n,r,E,T,c]),!n&&(C||T))return(0,q.jsx)(ce,{overlay:!0,centered:!0});let O=(0,q.jsxs)(q.Fragment,{children:[n&&(0,q.jsxs)(`div`,{className:`mb-lg`,children:[(0,q.jsx)(`p`,{className:`font-bold`,children:`Reward tag category`}),(0,q.jsxs)(`p`,{className:`mt-0 text-neutral-200 dark:text-neutral-900`,children:[`Select a tag category to create a combined scope and rewards table. Edit tag categories in`,` `,(0,q.jsx)(`a`,{className:`text-blue-400 dark:text-blue-600`,href:`/organizations/${e.organization?.handle}/assets`,children:`Asset Inventory`}),`.`]}),(0,q.jsx)(`div`,{className:`mt-xs`,children:(0,q.jsx)(A,{selectedOption:b.find(e=>e.value===d)||null,disabled:T,onChange:e=>{f(e?.value||null),a.form.rows.value.forEach((e,t)=>{o({value:[],key:t,type:Y.CHANGE_ROW_TAGS})})},options:b,placeholder:`Select a category`})})]}),a.form.rows.value.map((t,r)=>{let i=n?a.form.rows.value.filter((e,t)=>t!==r&&!a.form.rows.value[t].destroyed?.value).flatMap(e=>e.asm_tag_ids?.value||[]):[];return(0,q.jsx)(Je,{row:t,keyProp:r,useRange:a.form.use_range.value,dropdownOptions:S,teamHandle:e.handle,orgHandle:e.organization?.handle,showNewFlow:n,tagOptions:x,usedTagIds:i,saving:n&&T,hasNoScopedAssets:n&&v[r]},r)}),n?(0,q.jsx)(_,{variation:j.Secondary,small:!0,disabled:T,icons:{left:{src:i,accessibilityLabel:`Add`}},onClick:()=>o({type:Y.ADD_BOUNTY_TABLE_ROW}),children:`Add new reward group`}):(0,q.jsx)(B,{size:`large`,children:(0,q.jsx)(`a`,{className:`daisy-text spec-add-new-bounty-table-row`,onClick:()=>o({type:Y.ADD_BOUNTY_TABLE_ROW}),children:`+ add another bounty table row`})}),!n&&(0,q.jsxs)(q.Fragment,{children:[(0,q.jsx)(Xe,{}),(0,q.jsx)($,{})]}),!n&&(0,q.jsxs)(q.Fragment,{children:[(0,q.jsx)(z,{removeCardSpacing:!0}),(0,q.jsx)(B,{size:`large`,children:(0,q.jsxs)(pe,{className:`spec-bounty-table-description`,hasErrors:a.form.description.errors.length>0,children:[(0,q.jsx)(L,{children:`Optional description`}),(0,q.jsx)(me,{onChange:e=>o({value:e.target.value,type:Y.CHANGE_DESCRIPTION}),value:a.form.description.value,markdownOptions:{enableUnderline:!0}}),(0,q.jsx)(he,{errors:a.form.description.errors})]})})]}),!n&&(0,q.jsxs)(`div`,{style:t?{position:`absolute`,bottom:`-53px`,right:`300px`}:null,children:[t?null:(0,q.jsx)(Ze,{teamName:e.name}),(0,q.jsxs)(`div`,{className:`flex items-center pull-right`,children:[!t&&e.bounty_table!==null&&(0,q.jsx)(_,{onClick:()=>confirm(`Are you sure you want to remove your bounty table?`)&&nt(te,e.bounty_table),variation:j.DangerSecondary,children:`Remove bounty table`}),(0,q.jsx)(`div`,{className:`spec-create-update-bounty-table-button`,children:(0,q.jsxs)(_,{onClick:()=>tt(w,a,e),children:[e.bounty_table===null?`Create`:`Update`,` bounty table`]})})]}),(0,q.jsx)(`div`,{className:`clearfix`})]})]});return n?(0,q.jsxs)(q.Fragment,{children:[(0,q.jsx)($,{showNewFlow:!0}),(0,q.jsx)(Oe,{teamHandle:e.handle,assignedTagIds:a.form.rows.value.filter(e=>!e.destroyed?.value).flatMap(e=>e.asm_tag_ids?.value||[])}),d&&(0,q.jsx)(ke,{groupNames:y}),O]}):O};rt.propTypes={team:G.default.object.isRequired,isBbpOnboarding:G.default.bool,showNewFlow:G.default.bool,onSaveReady:G.default.func};var it=({handle:e,isBbpOnboarding:t,showNewFlow:n,onSaveReady:r})=>{let{data:i,loading:a}=V(Qe,{variables:{handle:e}});if(a)return(0,q.jsx)(ce,{overlay:!0,centered:!0});let{team:o}=i,s=n&&!o.bounty_table?.reward_category?o.inactive_new_flow_bounty_table||null:o.bounty_table;return(0,q.jsx)(q.Fragment,{children:o.i_can_view_bounty_table&&(0,q.jsx)(Ie,{maybeBountyTable:s,children:(0,q.jsx)(rt,{team:o,isBbpOnboarding:t,showNewFlow:n,onSaveReady:r})},n?`new-flow`:`old-flow`)})};it.propTypes={handle:G.default.string.isRequired,isBbpOnboarding:G.default.bool,showNewFlow:G.default.bool,onSaveReady:G.default.func};export{K as n,it as t};
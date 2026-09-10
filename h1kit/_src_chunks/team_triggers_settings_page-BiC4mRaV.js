import{o as e}from"./rolldown-runtime-DAXXjFlN.js";import{Ax as t,Fw as n,Kx as r,Lr as i,Nb as a,Qd as o,Qy as s,Rd as c,Rw as l,Uu as u,cp as d,df as f,jn as p,jr as m,lp as h,qx as g,wf as _,zx as v}from"./vendor-_WdvpBLr.js";import{$f as y,Ah as b,Eh as x,Km as ee,Sm as S,T as C,Th as te,Tm as w,Wm as T,_h as E,_l as D,ba as O,dh as k,dl as A,fm as j,ih as M,k as ne,qr as re,tp as N,vh as P}from"./app-5pKgUmmm.js";import{t as F}from"./Fade-CvqdNsO9.js";import{t as I}from"./trigger_preview-OK8EJ0Nc.js";var L=e(l()),R=e(_()),z=e(v());g();var B=n(),V=({trigger:e,handleRemove:t})=>(0,B.jsx)(`div`,{className:`spec-trigger trigger-wrapper`,children:(0,B.jsx)(a,{vertical:`16`,children:(0,B.jsx)(w,{children:(0,B.jsxs)(w.Heading,{children:[(0,B.jsxs)(`div`,{className:`pull-right margin-48--left`,children:[(0,B.jsx)(k,{className:`icon-link margin-16--right spec-edit-link`,to:`/${e.team.handle}/triggers/${e.database_id}/edit`,children:(0,B.jsx)(M,{glyph:T,size:`small`})}),(0,B.jsx)(`span`,{role:`button`,className:`icon-link icon-link--delete spec-delete-link`,onClick:t,children:(0,B.jsx)(M,{glyph:ee,size:`small`})})]}),(0,B.jsx)(I,{expressions:e.expressions.edges.map(({node:e})=>e),operator:e.expression_operator,actionType:e.action_type}),(0,B.jsx)(`div`,{className:`spec-trigger-hits margin-5--top`,children:(0,B.jsx)(j,{children:(0,B.jsxs)(y,{horizontal:!0,separator:!0,className:`daisy-text--grey`,children:[(0,B.jsxs)(y.Item,{children:[`Hits: `,e.trigger_action_logs.total_count]}),e.seeded&&(0,B.jsx)(y.Item,{children:(0,B.jsx)(D,{placement:`top`,className:`inline-help spec-default-trigger-helper-text`,tooltipText:`Default triggers are provided and managed by HackerOne to reduce the most common invalid reports. You can remove or edit the trigger if it doesn't fit your program.`,children:`Default Trigger`})})]})})})]})})})});V.propTypes={trigger:z.default.object.isRequired,handleRemove:z.default.func.isRequired},V.fragments={trigger:r`
    fragment CustomTriggerListItemTrigger on Trigger {
      ...TriggerPreviewTrigger
      id
      database_id: _id
      action_type
      action_message
      expression_operator
      percolated_query_string
      expressions(first: 100) {
        edges {
          node {
            id
            _id
            left_value
            operand
            right_value
          }
        }
      }
      team {
        id
        handle
      }
      trigger_action_logs {
        total_count
      }
      seeded
    }
    ${I.fragments.trigger}
  `},g();var H=r`
  mutation ToggleTrigger($trigger_id: ID!) {
    toggleTrigger(input: { trigger_id: $trigger_id }) {
      was_successful
      trigger {
        id
        disabled_at
      }
      errors {
        edges {
          node {
            id
            message
          }
        }
      }
    }
  }
`,U=({trigger:e})=>{let[t,n]=(0,L.useState)(!1),[r]=E(H,{optimisticResponse:{toggleTrigger:{__typename:`Mutation`,trigger:{id:e.id,__typename:`Trigger`,disabled_at:!e.disabled_at},was_successful:!0,errors:{__typename:`ErrorConnection`,edges:[]}}},onCompleted:e=>{let{errors:t,was_successful:n}=e.toggleTrigger;!n&&t.length>0&&S(`error`,t.edges.map(e=>e.node.message).join(` `))}});return(0,B.jsx)(`div`,{children:(0,B.jsx)(a,{vertical:`16`,children:(0,B.jsxs)(d,{fill:!0,variation:`subtle`,children:[(0,B.jsx)(h,{children:(0,B.jsxs)(`div`,{className:`flex justify-between`,"data-testid":`system-trigger-item`,children:[(0,B.jsx)(`div`,{children:e.title}),(0,B.jsx)(u,{screenReaderLabel:`Enable system trigger`,testId:`trigger-switch`,checked:!e.disabled_at,className:`pull-right`,onChange:()=>r({variables:{trigger_id:e.id}})})]})}),(0,B.jsxs)(h,{children:[(0,B.jsxs)(`div`,{className:`flex`,children:[(0,B.jsxs)(`span`,{className:`text-neutral-200 spec-trigger-hits dark:text-neutral-950`,children:[`Hits: `,e.trigger_action_logs.total_count]}),(0,B.jsx)(a,{horizontal:`8`,children:(0,B.jsx)(`span`,{className:`text-neutral-500 dark:text-neutral-950`,children:`|`})}),(0,B.jsx)(`span`,{onClick:()=>n(!t),className:`daisy-link`,"data-testid":`show-trigger-query`,role:`button`,children:t?`Hide details`:`Show details`})]}),t&&(0,B.jsxs)(`div`,{children:[(0,B.jsx)(a,{vertical:`8`,children:(0,B.jsx)(f,{variation:`light`})}),(0,B.jsx)(I,{percolated_query_string:e.percolated_query_string,expressions:e.expressions.edges.map(({node:e})=>e),operator:e.expression_operator,actionType:e.action_type,actionMessage:e.action_message})]})]})]})})})};U.propTypes={trigger:z.default.object.isRequired},U.fragments={trigger:r`
    fragment SystemTriggerListItemTrigger on Trigger {
      ...TriggerPreviewTrigger
      id
      title
      seeded
      database_id: _id
      action_type
      action_message
      expression_operator
      disabled_at
      percolated_query_string
      expressions(first: 100) {
        edges {
          node {
            id
            _id
            left_value
            operand
            right_value
          }
        }
      }
      team {
        id
        handle
      }
      trigger_action_logs {
        total_count
      }
    }
    ${I.fragments.trigger}
  `};var W=`/assets/static/triggers-lightmode-D77RMDBU.svg`;g();var G=e(c()),K=constants.pagination.page_size,q={SYSTEM:`system`,CUSTOM:`custom`},J=r`
  mutation DeleteTrigger($trigger_id: ID!) {
    deleteTrigger(input: { trigger_id: $trigger_id }) {
      was_successful
      errors {
        edges {
          node {
            id
            type
          }
        }
      }
    }
  }
`,Y=r`
  query TriggerListTeamQuery(
    $handle: String!
    $pageSize: Int!
    $cursor: String
    $filter: FiltersTriggerFilterInput!
  ) {
    team(handle: $handle) {
      id
      handle
      i_can_create_triggers
      system_triggers: triggers(where: { seeded: { _eq: true } }) {
        total_count
      }
      custom_triggers: triggers(where: { seeded: { _eq: false } }) {
        total_count
      }
      triggers(first: $pageSize, after: $cursor, where: $filter) {
        total_count
        edges {
          cursor
          node {
            id
            database_id: _id
            ...SystemTriggerListItemTrigger
            ...CustomTriggerListItemTrigger
          }
        }
        pageInfo {
          endCursor
          hasNextPage
        }
      }
    }
  }
  ${U.fragments.trigger}
  ${V.fragments.trigger}
`,X=({team:e,loadMore:t,handleRemove:n})=>(0,B.jsx)(p,{dataLength:e.triggers.edges.length,next:t,hasMore:e.triggers.pageInfo.hasNextPage,loader:(0,B.jsx)(x,{}),scrollableTarget:`main-content`,children:(0,R.default)(e.triggers.edges,({node:e})=>e.database_id).reverse().map(({node:e},t)=>(0,B.jsx)(F,{baseClassActive:`fade--show`,timeout:t%K*50,children:e.seeded?(0,B.jsx)(U,{trigger:e}):(0,B.jsx)(V,{trigger:e,handleRemove:()=>n(e)})},e.id))});X.propTypes={handleRemove:z.default.func.isRequired,loadMore:z.default.any,team:z.default.shape({triggers:z.default.shape({edges:z.default.any,pageInfo:z.default.any})})};var Z=({loadMore:e,handleRemove:t,team:n,notReady:r})=>(0,B.jsx)(`div`,{children:r?(0,B.jsx)(`div`,{style:{height:300},children:(0,B.jsx)(te,{})}):n.triggers.total_count<=0?(0,B.jsx)(ie,{}):(0,B.jsx)(X,{team:n,loadMore:e,handleRemove:t})});Z.propTypes={loadMore:z.default.func,handleRemove:z.default.func,team:z.default.object,notReady:z.default.bool};var ie=()=>(0,B.jsx)(`div`,{children:(0,B.jsxs)(`div`,{className:`flex flex-col items-center text-center mt-3xl`,children:[(0,B.jsx)(`img`,{src:W,className:`h-[240px] w-[240px]`,alt:`zero triggers illustration`}),(0,B.jsxs)(o,{children:[(0,B.jsx)(`p`,{className:`mt-spacing-20 text-xl`,children:`No custom triggers set for this program`}),(0,B.jsx)(`p`,{className:`text-base`,children:`Automate actions and responses to incoming reports using triggers`})]})]})}),Q=({teamHandle:e,location:n})=>{let r=t(),i=(0,G.parse)(n.search,{arrayFormat:`bracket`}),[a,o]=(0,L.useState)(i?.tab||q.SYSTEM);(0,L.useEffect)(()=>{if(!i?.tab){r.replace(`${n.pathname}?tab=${a}`);return}i?.tab!==a&&r.push(`${n.pathname}?tab=${a}`)},[a]),(0,L.useEffect)(()=>{i?.tab&&i.tab!==a&&o(i.tab)},[i.tab]);let{data:c,loading:l,fetchMore:u,error:d,refetch:f}=P(Y,{variables:{handle:e,pageSize:K,filter:{seeded:{_eq:a===q.SYSTEM}}}});(0,L.useEffect)(()=>{l||(window.scrollTo(0,0),f())},[]);let{team:p}=c||{},h=l||!c,g=A(c,`team.triggers`,u),[_]=E(J,{onCompleted:e=>(e.deleteTrigger.was_successful&&S(`notice`,`Trigger successfully deleted`),f())}),v=e=>{if(confirm(`Are you sure you want to delete this trigger?`))return _({variables:{trigger_id:e.id}})};if(d)return(0,B.jsx)(N,{variation:`red`,children:`An error occurred...`});if(p&&p.triggers===null)return(0,B.jsx)(N,{variation:`red`,children:`Triggers are not available on this program.`});let y=[{label:`System triggers`,tag:p?.system_triggers?.total_count||`0`,key:q.SYSTEM},...p?.i_can_create_triggers?[{label:`Custom triggers`,tag:p?.custom_triggers?.total_count||`0`,key:q.CUSTOM}]:[]],b=y.findIndex(e=>e.key===a);return(0,B.jsxs)(`div`,{children:[(0,B.jsxs)(`div`,{className:`flex flex-col lg:flex-row items-start lg:items-center justify-between settings-title-container`,children:[(0,B.jsx)(`h3`,{className:`daisy-h3`,style:{marginRight:`auto`},children:`Configured Triggers`}),p?.i_can_create_triggers?(0,B.jsx)(k,{className:`daisy-link`,to:`/${e}/triggers/new`,children:(0,B.jsx)(s,{small:!0,variation:`primary`,testId:`add-custom-trigger-btn`,children:`Add custom trigger`})}):null]}),(0,B.jsx)(m.Group,{selectedIndex:b,onChange:e=>o(y[e].key),children:(0,B.jsx)(m.List,{tabs:y})}),(0,B.jsx)(Z,{loadMore:g,handleRemove:v,team:p,notReady:h})]})};Q.propTypes={teamHandle:z.default.string.isRequired,location:z.default.any};var $=({match:e,location:t})=>{let n=e.params.handle;return(0,B.jsx)(re,{children:(0,B.jsx)(C,{header:(0,B.jsx)(ne,{match:e}),content:(0,B.jsxs)(`div`,{children:[(0,B.jsx)(i,{children:(0,B.jsx)(`div`,{className:`text-6xl`,children:O(`Triggers`)})}),(0,B.jsx)(Q,{teamHandle:n,location:t})]}),footer:(0,B.jsx)(b,{}),hasBackground:!1})})};$.propTypes={location:z.default.any,match:z.default.shape({params:z.default.shape({handle:z.default.string.isRequired}).isRequired}).isRequired};export{$ as default};
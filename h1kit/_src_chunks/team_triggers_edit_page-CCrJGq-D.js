import{o as e}from"./rolldown-runtime-DAXXjFlN.js";import{Fw as t,Kx as n,Rw as r,Tx as i,qx as a,zx as o}from"./vendor-_WdvpBLr.js";import{Ah as s,Sm as c,T as l,_h as u,dh as d,k as f,op as p,qr as m,vh as h,vm as g}from"./app-5pKgUmmm.js";import{a as _,i as v,o as y,r as b,s as x}from"./trigger_form_components-B3Raogl6.js";var S=e(o()),C=e(r());a();var w=t(),T=({onSaveClick:e,cancelPath:t,disabled:n})=>(0,w.jsxs)(`div`,{className:`pull-right`,children:[(0,w.jsx)(d,{to:t,children:(0,w.jsx)(p,{className:`spec-trigger-cancel margin-16--right`,variation:`tertiary`,disabled:n,children:`Cancel`})}),(0,w.jsx)(p,{className:`spec-trigger-update`,onClick:e,disabled:n,children:`Save trigger`})]});T.propTypes={onSaveClick:S.default.func.isRequired,cancelPath:S.default.string.isRequired,disabled:S.default.bool.isRequired};var E=e=>({expressions:e.expressions,operand:e.expression_operator,actionType:e.action_type,actionMessage:e.action_message,actionMessageErrors:[],canSubmit:!0,showErrors:!1,hasEverSeenAValidExpressionForm:!0}),D=n`
  mutation UpdateTrigger(
    $trigger_id: ID!
    $action_type: String!
    $action_message: String!
    $expressions: [ExpressionInput]!
    $expression_operator: String!
  ) {
    updateTrigger(
      input: {
        trigger_id: $trigger_id
        action_type: $action_type
        action_message: $action_message
        expressions: $expressions
        expression_operator: $expression_operator
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
    }
  }
`,O=n`
  query UpdateTriggerFormQuery($url: URI!) {
    resource(url: $url) {
      ... on Trigger {
        id
        action_type
        action_message
        expression_operator
        seeded
        expressions(first: 100) {
          edges {
            node {
              id
              left_value
              right_value
              operand
            }
          }
        }
        team {
          id
          handle
          ...WeaknessSearchInputTeam
        }
      }
    }
  }
  ${x.fragments.team}
`,k=({url:e,teamHandle:t})=>{let[n,r]=(0,C.useState)(!1),[a,o]=(0,C.useState)(null),[s,l]=(0,C.useState)({filter:{},naFilter:{},filterGiven:!1}),d=e=>{let t={_and:[{substate:{_eq:`not_applicable`}},e.filter]};l({...e,naFilter:t})},{filter:f,filterGiven:p,naFilter:m}=s,{data:x,refetch:S,loading:k}=h(O,{variables:{filter:f,filterGiven:p,na_filter:m,url:e},onCompleted:e=>{if(e.resource?.seeded){c(`error`,`System triggers cannot be edited`),o(`/${t}/triggers?tab=system`);return}r(!0)}}),[A,{loading:j}]=u(D,{onCompleted:e=>{let{was_successful:n}=e.updateTrigger||{};n?(c(`notice`,`Trigger was successfully updated`),S(),o(`/${t}/triggers?tab=custom`)):g()}});if(a)return(0,w.jsx)(i,{to:a});if(!n)return(0,w.jsx)(_,{title:`Edit Trigger`,handle:t});let M=x.resource,N=y(E(M),{type:b});return(0,w.jsx)(v,{initialFormState:N,title:`Edit Trigger`,team:M.team,handleSubmit:({form_state:e})=>{let t={trigger_id:M.id,expressions:e.expressions.map(e=>({left_value:e.left_value,operand:e.operand,right_value:e.right_value})),action_message:e.actionMessage,action_type:e.actionType,expression_operator:e.operand};return A({variables:t})},formButtonsComponent:T,buttonsAreDisabled:j,filterState:s,setFilterState:d,reportsLoading:k})};k.propTypes={url:S.default.string.isRequired,teamHandle:S.default.string.isRequired};var A=class extends C.Component{static propTypes={location:S.default.shape({pathname:S.default.string.isRequired}),match:S.default.shape({params:S.default.shape({handle:S.default.string.isRequired}).isRequired}).isRequired};render(){let e=this.props.match.params.handle,t=this.props.location.pathname;return(0,w.jsx)(m,{children:(0,w.jsx)(l,{header:(0,w.jsx)(f,{...this.props}),content:(0,w.jsx)(`div`,{children:(0,w.jsx)(k,{url:t,teamHandle:e})}),footer:(0,w.jsx)(s,{}),hasBackground:!1})})}};export{A as default};
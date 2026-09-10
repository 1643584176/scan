import{o as e}from"./rolldown-runtime-DAXXjFlN.js";import{Fw as t,Kx as n,Rw as r,Tx as i,qx as a,zx as o}from"./vendor-_WdvpBLr.js";import{Ah as s,Sm as c,T as l,Uo as u,_h as d,dh as f,k as p,op as m,qr as h,vh as g,vm as _}from"./app-5pKgUmmm.js";import{a as v,i as y,n as b,o as x,s as S,t as C}from"./trigger_form_components-B3Raogl6.js";var w=e(o()),T=e(r());a();var E=t(),D=({onSaveClick:e,cancelPath:t,disabled:n})=>(0,E.jsxs)(`div`,{className:`pull-right`,children:[(0,E.jsx)(f,{to:t,children:(0,E.jsx)(m,{className:`spec-trigger-cancel margin-16--right`,variation:`tertiary`,disabled:n,children:`Cancel`})}),(0,E.jsx)(m,{className:`spec-trigger-create`,onClick:e,disabled:n,children:`Save trigger`})]});D.propTypes={onSaveClick:w.default.func.isRequired,cancelPath:w.default.string.isRequired,disabled:w.default.bool.isRequired};var O=()=>({expressions:[],operand:`AND`,actionType:C,actionMessage:``,actionMessageErrors:[u],canSubmit:!1,showErrors:!1,previewFilter:{},hasEverSeenAValidExpressionForm:!1}),k=n`
  mutation CreateTrigger(
    $team_id: ID!
    $action_type: String!
    $action_message: String!
    $expressions: [ExpressionInput]!
    $expression_operator: String!
  ) {
    createTrigger(
      input: {
        team_id: $team_id
        action_type: $action_type
        action_message: $action_message
        expressions: $expressions
        expression_operator: $expression_operator
      }
    ) {
      team {
        id
      }
      new_trigger {
        node {
          id
        }
      }
      was_successful
    }
  }
`,A=n`
  query CreateTriggerFormQuery($handle: String!) {
    team(handle: $handle) {
      id
      handle
      ...WeaknessSearchInputTeam
    }
  }
  ${S.fragments.team}
`,j=({teamHandle:e})=>{let t=x(O(),{type:b}),[n,r]=(0,T.useState)(!1),[a,o]=(0,T.useState)(null),[s,l]=(0,T.useState)({filter:{},naFilter:{},filterGiven:!1}),u=e=>{let t={_and:[{substate:{_eq:`not_applicable`}},e.filter]};l({...e,naFilter:t})},{filter:f,filterGiven:p,naFilter:m}=s,{data:h,loading:S}=g(A,{variables:{filter:f,filterGiven:p,na_filter:m,handle:e},onCompleted:()=>{r(!0)}}),[C,{loading:w}]=d(k,{onCompleted:t=>{t.createTrigger.was_successful?(c(`notice`,`Trigger was successfully created`),o(`/${e}/triggers?tab=custom`)):_()}});if(a)return(0,E.jsx)(i,{to:a});if(!n)return(0,E.jsx)(v,{title:`Create Trigger`,handle:e});let j=h.team;return(0,E.jsx)(y,{initialFormState:t,title:`Create Trigger`,team:j,handleSubmit:({form_state:e})=>{let t={team_id:j.id,expressions:e.expressions.map(e=>({left_value:e.left_value,operand:e.operand,right_value:e.right_value})),action_message:e.actionMessage,action_type:e.actionType,expression_operator:e.operand};return C({variables:t})},formButtonsComponent:D,buttonsAreDisabled:w,filterState:s,setFilterState:u,reportsLoading:S})};j.propTypes={teamHandle:w.default.string.isRequired};var M=e=>{let t=e.match.params.handle;return(0,E.jsx)(h,{children:(0,E.jsx)(l,{header:(0,E.jsx)(p,{...e}),content:(0,E.jsx)(`div`,{children:(0,E.jsx)(j,{teamHandle:t})}),footer:(0,E.jsx)(s,{}),hasBackground:!1})})};M.propTypes={match:w.default.shape({params:w.default.shape({handle:w.default.string.isRequired}).isRequired}).isRequired};export{M as default};
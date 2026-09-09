import{o as e}from"./rolldown-runtime-DAXXjFlN.js";import{Fw as t,Kx as n,Pb as r,Rw as i,n as a,qx as o,zx as s}from"./vendor-_WdvpBLr.js";import{Ah as c,Rn as l,Sm as u,T as d,Th as f,Tm as p,_h as m,_i as h,ap as g,dh as _,fc as v,fm as y,gc as b,gh as x,k as S,op as C,pc as w,rc as T,uh as E,vh as D,ym as O}from"./app-5pKgUmmm.js";var k=e(i()),A=e(r()),j=e(s());o();var M=t(),N=n`
  mutation DeleteAgileAcceleratorIntegration($team_id: ID!) {
    deleteAgileAcceleratorIntegration(input: { team_id: $team_id }) {
      was_successful
      team {
        id
        agile_accelerator_integration {
          id
        }
      }
    }
  }
`,P=({team:e})=>{let[t]=m(N,{variables:{team_id:e.id},onCompleted:({deleteAgileAcceleratorIntegration:t})=>{t.was_successful&&g(`/${e.handle}/integrations`)}});return(0,M.jsx)(`div`,{className:`margin-20--top`,children:(0,M.jsxs)(`div`,{className:`inline-banner`,children:[(0,M.jsxs)(`div`,{className:`pull-left margin-5--top`,children:[`Connected with`,` `,(0,M.jsx)(`strong`,{children:e.agile_accelerator_integration.api_url})]}),(0,M.jsx)(`div`,{className:`pull-right`,children:(0,M.jsx)(C,{type:`button`,onClick:()=>t(),size:`small`,color:`danger`,children:`Disconnect`})}),(0,M.jsx)(`div`,{className:`clearfix`})]})})};P.fragments={team:n`
    fragment DisconnectForm on Team {
      id
      handle
      agile_accelerator_integration {
        id
        api_url
      }
    }
  `},P.propTypes={team:j.default.object.isRequired};var F=e(a());o();var I={SET_SANDBOX:`SET_SANDBOX`,SET_API_URL:`SET_API_URL`,SET_CLIENT_ID:`SET_CLIENT_ID`,SET_CLIENT_SECRET:`SET_CLIENT_SECRET`,SET_FIELD_PREFIX:`SET_FIELD_PREFIX`,SET_INVESTIGATION_TYPE_ID:`SET_INVESTIGATION_TYPE_ID`,SET_PRODUCT_TAG:`SET_PRODUCT_TAG`,SET_ASSIGNEE_ID:`SET_ASSIGNEE_ID`},L=n`
  mutation UpdateSfdcAgileAcceleratorSettings(
    $team_id: ID!
    $api_url: URI!
    $client_id: String!
    $client_secret: String!
    $product_tag: String!
    $assignee_id: String!
    $field_prefix: String
    $investigation_type_id: String!
    $sandbox: Boolean
  ) {
    updateSfdcAgileAcceleratorSettings(
      input: {
        team_id: $team_id
        api_url: $api_url
        client_id: $client_id
        client_secret: $client_secret
        product_tag: $product_tag
        assignee_id: $assignee_id
        field_prefix: $field_prefix
        investigation_type_id: $investigation_type_id
        sandbox: $sandbox
      }
    ) {
      team {
        id
        agile_accelerator_integration {
          id
        }
      }
      was_successful
      errors {
        edges {
          node {
            id
            field
            message
          }
        }
      }
    }
  }
`,R=n`
  query SfdcAgileAcceleratorFormQuery($handle: String!) {
    team(handle: $handle) {
      id
      handle
      agile_accelerator_integration {
        id
        connected
        api_url
        client_id
        client_secret
        product_tag
        assignee_id
        field_prefix
        investigation_type_id
        sandbox
      }
      ...DisconnectForm
    }
  }
  ${P.fragments.team}
`,z=e=>{if(e.agile_accelerator_integration&&e.agile_accelerator_integration.connected)return(0,M.jsx)(P,{team:e})},B=(e,t={})=>{switch(t.type){case I.SET_SANDBOX:return{...e,sandbox:t.value===`on`};case I.SET_API_URL:return{...e,api_url:t.value};case I.SET_CLIENT_ID:return{...e,client_id:t.value};case I.SET_CLIENT_SECRET:return{...e,client_secret:t.value};case I.SET_FIELD_PREFIX:return{...e,field_prefix:t.value};case I.SET_INVESTIGATION_TYPE_ID:return{...e,investigation_type_id:t.value};case I.SET_PRODUCT_TAG:return{...e,product_tag:t.value};case I.SET_ASSIGNEE_ID:return{...e,assignee_id:t.value};default:return e}},V=e=>({api_url:e.api_url,client_id:e.client_id,client_secret:e.client_secret,product_tag:e.product_tag,assignee_id:e.assignee_id,field_prefix:e.field_prefix||``,investigation_type_id:e.investigation_type_id,sandbox:e.sandbox}),H={api_url:``,client_id:``,client_secret:``,product_tag:``,assignee_id:``,field_prefix:``,investigation_type_id:``,sandbox:!1},U=({team:e})=>{let{agile_accelerator_integration:t}=e,[n,r]=(0,k.useState)({}),i=A.default.existy(t)?V(t):H,[a,o]=(0,k.useReducer)(B,i),s=()=>{let t=e.agile_accelerator_integration;return t&&t.connected},c=e=>{u(`error`,`Something went wrong. Please check the errors and submit the form again.`),r(e)},[d]=m(L,{variables:{team_id:e.id,api_url:a.api_url,client_id:a.client_id,client_secret:a.client_secret,product_tag:a.product_tag,assignee_id:a.assignee_id,field_prefix:a.field_prefix,investigation_type_id:a.investigation_type_id,sandbox:a.sandbox},onCompleted:({updateSfdcAgileAcceleratorSettings:t})=>{t.was_successful?s()?O():g(`/sfdc_agile_accelerator_oauths?state=${e.handle}`):c(b(t.errors))}});return(0,M.jsxs)(v,{children:[(0,M.jsxs)(h,{children:[(0,M.jsx)(_,{className:`daisy-text daisy-link`,to:`/${e.handle}/integrations`,children:`← back to integrations`}),(0,M.jsx)(h.Title,{children:`Connect with Agile Accelerator`}),(0,M.jsx)(h.Description,{children:z(e)})]}),(0,M.jsxs)(p,{children:[s()?(0,M.jsx)(p.Heading,{children:`Update your Agile Accelerator integration settings.`}):(0,M.jsxs)(p.Heading,{children:[(0,M.jsx)(`p`,{children:`Enter your API settings details to enable the integration with Agile Accelerator.`}),(0,M.jsx)(w,{children:`OAuth Callback URL`}),(0,M.jsx)(T,{id:`callback_url`,name:`callback_url`,value:`https://hackerone.com/sfdc_agile_accelerator_oauths/callback`,className:`margin-5--bottom`,readOnly:!0}),(0,M.jsx)(F.default,{text:`https://hackerone.com/sfdc_agile_accelerator_oauths/callback`,children:(0,M.jsx)(C,{variation:`secondary`,size:`small`,className:`pull-right`,children:`Copy`})}),(0,M.jsx)(y,{children:`Use this callback URL in your Salesforce App Oauth settings.`}),(0,M.jsx)(`div`,{className:`clearfix`})]}),(0,M.jsx)(p.Content,{children:(0,M.jsxs)(x,{children:[(0,M.jsx)(x.Row,{children:(0,M.jsx)(x.Column,{children:(0,M.jsx)(E,{children:(0,M.jsxs)(v,{children:[(0,M.jsx)(l,{id:`sandbox`,name:`sandbox`,checked:a.sandbox,type:`text`,label:`Sandbox Org`,onChange:e=>{o({type:I.SET_SANDBOX,value:e.target.value})},hasErrors:A.default.existy(n.sandbox)}),(0,M.jsx)(y,{errors:[n.sandbox],className:`margin-8--top`})]})})})}),!s()&&(0,M.jsxs)(`span`,{children:[(0,M.jsx)(x.Row,{children:(0,M.jsx)(x.Column,{children:(0,M.jsx)(E,{children:(0,M.jsxs)(v,{children:[(0,M.jsx)(w,{isRequired:!0,children:`API URL`}),(0,M.jsx)(T,{id:`api_url`,name:`api_url`,value:a.api_url,type:`text`,onChange:e=>{o({type:I.SET_API_URL,value:e.target.value})},hasErrors:A.default.existy(n.api_url),required:!0}),(0,M.jsx)(y,{errors:[n.api_url],className:`margin-8--top`})]})})})}),(0,M.jsx)(x.Row,{children:(0,M.jsx)(x.Column,{children:(0,M.jsx)(E,{children:(0,M.jsxs)(v,{children:[(0,M.jsx)(w,{isRequired:!0,children:`Consumer Key`}),(0,M.jsx)(T,{id:`client_id`,name:`client_id`,value:a.client_id,type:`text`,onChange:e=>o({type:I.SET_CLIENT_ID,value:e.target.value}),hasErrors:A.default.existy(n.client_id),required:!0}),(0,M.jsx)(y,{errors:[n.client_id],className:`margin-8--top`})]})})})}),(0,M.jsx)(x.Row,{children:(0,M.jsx)(x.Column,{children:(0,M.jsx)(E,{children:(0,M.jsxs)(v,{children:[(0,M.jsx)(w,{isRequired:!0,children:`Consumer Secret`}),(0,M.jsx)(T,{id:`client_secret`,name:`client_secret`,value:a.client_secret,type:`text`,onChange:e=>o({type:I.SET_CLIENT_SECRET,value:e.target.value}),hasErrors:A.default.existy(n.client_secret),required:!0}),(0,M.jsx)(y,{errors:[n.client_secret],className:`margin-8--top`})]})})})})]}),(0,M.jsx)(x.Row,{children:(0,M.jsx)(x.Column,{children:(0,M.jsx)(E,{children:(0,M.jsxs)(v,{children:[(0,M.jsx)(w,{isRequired:!0,children:`Product Tag`}),(0,M.jsx)(T,{id:`product_tag`,name:`product_tag`,value:a.product_tag,type:`text`,onChange:e=>o({type:I.SET_PRODUCT_TAG,value:e.target.value}),hasErrors:A.default.existy(n.product_tag),required:!0}),(0,M.jsx)(y,{errors:[n.product_tag],className:`margin-8--top`})]})})})}),(0,M.jsx)(x.Row,{children:(0,M.jsx)(x.Column,{children:(0,M.jsx)(E,{children:(0,M.jsxs)(v,{children:[(0,M.jsx)(w,{isRequired:!0,children:`Assigned Salesforce User ID`}),(0,M.jsx)(T,{id:`assignee_id`,name:`assignee_id`,value:a.assignee_id,type:`text`,onChange:e=>o({type:I.SET_ASSIGNEE_ID,value:e.target.value}),hasErrors:A.default.existy(n.assignee_id),required:!0}),(0,M.jsx)(y,{errors:[n.assignee_id],className:`margin-8--top`})]})})})}),(0,M.jsx)(x.Row,{children:(0,M.jsx)(x.Column,{children:(0,M.jsx)(E,{children:(0,M.jsxs)(v,{children:[(0,M.jsx)(w,{isRequired:!0,children:`Investigation Type ID`}),(0,M.jsx)(T,{id:`investigation_type_id`,name:`investigation_type_id`,value:a.investigation_type_id,type:`text`,onChange:e=>o({type:I.SET_INVESTIGATION_TYPE_ID,value:e.target.value}),hasErrors:A.default.existy(n.investigation_type_id),required:!0}),(0,M.jsx)(y,{errors:[n.investigation_type_id],className:`margin-8--top`})]})})})}),(0,M.jsx)(x.Row,{children:(0,M.jsx)(x.Column,{children:(0,M.jsx)(E,{children:(0,M.jsxs)(v,{children:[(0,M.jsx)(w,{children:`Field Prefix`}),(0,M.jsx)(T,{id:`field_prefix`,name:`field_prefix`,value:a.field_prefix,type:`text`,onChange:e=>o({type:I.SET_FIELD_PREFIX,value:e.target.value}),hasErrors:A.default.existy(n.field_prefix)})]})})})}),(0,M.jsx)(x.Row,{children:(0,M.jsx)(x.Column,{size:`one-whole`,children:(0,M.jsx)(`div`,{className:`pull-right`,children:(0,M.jsx)(C,{onClick:()=>d(),children:s()?`Save`:`Connect`})})})})]})})]})]})};U.propTypes={team:j.default.object.isRequired};var W=({handle:e})=>{let{data:t,loading:n}=D(R,{variables:{handle:e}});return n?(0,M.jsx)(f,{}):(0,M.jsx)(U,{team:t.team})};W.propTypes={handle:j.default.string.isRequired};var G=class extends k.Component{static propTypes={match:j.default.shape({params:j.default.shape({handle:j.default.string.isRequired}).isRequired}).isRequired};render(){let e=this.props.match.params.handle;return(0,M.jsx)(d,{header:(0,M.jsx)(S,{...this.props}),content:(0,M.jsx)(`div`,{children:(0,M.jsx)(W,{handle:e})}),footer:(0,M.jsx)(c,{}),hasBackground:!1})}};export{G as default};
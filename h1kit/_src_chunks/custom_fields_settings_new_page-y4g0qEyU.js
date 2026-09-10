import{o as e}from"./rolldown-runtime-DAXXjFlN.js";import{Fw as t,Kx as n,Px as r,qx as i,zx as a}from"./vendor-_WdvpBLr.js";import{T as o,Th as s,Tm as c,_i as l,dh as u,k as d,qr as f,vh as p}from"./app-5pKgUmmm.js";import{t as m}from"./form-LRPg1qZU.js";var h=e(a());i();var g=t(),_=n`
  query CustomFieldsSettingsNewPage($handle: String!) {
    team(handle: $handle) {
      id
      handle
    }
  }
`,v=n`
  mutation CreateCustomFieldAttribute(
    $team_id: ID!
    $label: String!
    $type: String!
    $configuration: String
    $internal: Boolean!
    $helper_text: String
    $error_message: String
    $regex: String
    $required: Boolean
    $checkbox_text: String
  ) {
    createCustomFieldAttribute(
      input: {
        team_id: $team_id
        label: $label
        type: $type
        configuration: $configuration
        internal: $internal
        helper_text: $helper_text
        error_message: $error_message
        regex: $regex
        required: $required
        checkbox_text: $checkbox_text
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
`,y=({match:e,history:t})=>{let n=e.params.handle,{data:r,loading:i}=p(_,{variables:{handle:n}});if(i)return(0,g.jsx)(s,{overlay:!0});let{team:a}=r;return(0,g.jsx)(f,{children:(0,g.jsx)(o,{header:(0,g.jsx)(d,{match:e}),content:(0,g.jsxs)(`div`,{className:`settings-title-container`,children:[(0,g.jsxs)(l,{children:[(0,g.jsxs)(u,{className:`daisy-text daisy-link`,to:`/${n}/custom_fields`,children:[`←`,` Back to overview`]}),(0,g.jsx)(l.Title,{children:`Create Custom Field`}),(0,g.jsx)(l.Description,{children:`Configure the custom field you'd like to add to your reports.`})]}),(0,g.jsx)(c,{children:(0,g.jsx)(c.Content,{children:(0,g.jsx)(m,{team:a,mutation:v,history:t,editForm:!1})})})]}),hasBackground:!1})})};y.propTypes={match:h.default.shape({params:h.default.shape({handle:h.default.string.isRequired})}).isRequired,history:h.default.object.isRequired};var b=r(y);export{b as default};
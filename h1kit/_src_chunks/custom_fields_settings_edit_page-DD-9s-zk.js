import{o as e}from"./rolldown-runtime-DAXXjFlN.js";import{Fw as t,Kx as n,Px as r,qx as i,zx as a}from"./vendor-_WdvpBLr.js";import{T as o,Th as s,Tm as c,_i as l,dh as u,k as d,qr as f,vh as p}from"./app-5pKgUmmm.js";import{t as m}from"./form-LRPg1qZU.js";var h=e(a());i();var g=t(),_=n`
  query CustomFieldsEditPage($handle: String!, $customFieldAttributeId: Int!) {
    team(handle: $handle) {
      id
      handle
      customFieldAttribute: custom_field_attributes(
        first: 1
        where: { id: { _eq: $customFieldAttributeId } }
      ) {
        edges {
          node {
            ... on CustomFieldAttributeInterface {
              id
            }
            ...FormCustomFieldAttribute
          }
        }
      }
    }
  }
  ${m.fragments.customFieldAttribute}
`,v=n`
  mutation UpdateCustomFieldAttributePageMutation(
    $id: ID!
    $label: String!
    $configuration: String
    $internal: Boolean!
    $helper_text: String
    $error_message: String
    $regex: String
    $required: Boolean
    $checkbox_text: String
  ) {
    updateCustomFieldAttribute(
      input: {
        id: $id
        label: $label
        configuration: $configuration
        internal: $internal
        helper_text: $helper_text
        error_message: $error_message
        regex: $regex
        required: $required
        checkbox_text: $checkbox_text
      }
    ) {
      custom_field_attribute {
        id
        label
        key
        ...FormCustomFieldAttribute
      }
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
  ${m.fragments.customFieldAttribute}
`,y=({match:e,history:t})=>{let n=e.params.handle,r=e.params.id,{data:i,loading:a}=p(_,{variables:{handle:n,customFieldAttributeId:parseInt(r,10)}});if(a)return(0,g.jsx)(s,{overlay:!0});let{team:h}=i;return(0,g.jsx)(f,{children:(0,g.jsx)(o,{header:(0,g.jsx)(d,{match:e}),content:(0,g.jsxs)(`div`,{className:`settings-title-container`,children:[(0,g.jsxs)(l,{children:[(0,g.jsxs)(u,{className:`daisy-text daisy-link`,to:`/${n}/custom_fields`,children:[`←`,` Back to overview`]}),(0,g.jsx)(l.Title,{children:`Edit Custom Field`}),(0,g.jsx)(l.Description,{children:`Make changes to your existing custom field.`})]}),(0,g.jsx)(c,{children:(0,g.jsx)(c.Content,{children:(0,g.jsx)(m,{team:h,mutation:v,history:t,editForm:!0})})})]}),hasBackground:!1})})};y.propTypes={},y.propTypes={match:h.default.shape({params:h.default.shape({handle:h.default.string.isRequired,id:h.default.string.isRequired}).isRequired}).isRequired,history:h.default.object.isRequired};var b=r(y);export{b as default};
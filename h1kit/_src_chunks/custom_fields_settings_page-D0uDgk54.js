import{o as e,r as t}from"./rolldown-runtime-DAXXjFlN.js";import{Fw as n,Iw as r,Kx as i,Nb as a,Qy as o,ov as s,qx as c,rv as l,tb as u,zx as d}from"./vendor-_WdvpBLr.js";import{$f as f,Nn as p,Sd as m,Sh as h,Sm as g,T as _,Th as v,_h as y,dh as b,ih as x,k as S,lh as C,qr as w,vh as T,vm as E,vp as D}from"./app-5pKgUmmm.js";import{i as O,n as k,r as A,t as j}from"./react-sortable-hoc.esm-Ct2qVI2M.js";var M=e(r()),N=e(d()),P=`data:image/svg+xml,%3csvg%20viewBox='0%200%2010%2016'%20fill='none'%20xmlns='http://www.w3.org/2000/svg'%3e%3cpath%20d='M4%2014C4%2015.1%203.1%2016%202%2016C0.9%2016%200%2015.1%200%2014C0%2012.9%200.9%2012%202%2012C3.1%2012%204%2012.9%204%2014ZM2%206C0.9%206%200%206.9%200%208C0%209.1%200.9%2010%202%2010C3.1%2010%204%209.1%204%208C4%206.9%203.1%206%202%206ZM2%200C0.9%200%200%200.9%200%202C0%203.1%200.9%204%202%204C3.1%204%204%203.1%204%202C4%200.9%203.1%200%202%200ZM8%204C9.1%204%2010%203.1%2010%202C10%200.9%209.1%200%208%200C6.9%200%206%200.9%206%202C6%203.1%206.9%204%208%204ZM8%206C6.9%206%206%206.9%206%208C6%209.1%206.9%2010%208%2010C9.1%2010%2010%209.1%2010%208C10%206.9%209.1%206%208%206ZM8%2012C6.9%2012%206%2012.9%206%2014C6%2015.1%206.9%2016%208%2016C9.1%2016%2010%2015.1%2010%2014C10%2012.9%209.1%2012%208%2012Z'%20fill='currentColor'/%3e%3c/svg%3e`;c();var F=e(O()),I=n(),L=i`
  mutation UpdateCustomFieldAttributeArchiveMutation(
    $id: ID!
    $archived: Boolean!
  ) {
    toggleArchivedCustomFieldAttribute(
      input: { id: $id, archived: $archived }
    ) {
      was_successful
      errors {
        edges {
          node {
            id
          }
        }
      }
    }
  }
`,R=i`
  mutation RepositionCustomFieldAttribute($id: ID!, $position: Int!) {
    repositionCustomFieldAttribute(input: { id: $id, position: $position }) {
      was_successful
      errors {
        edges {
          node {
            id
          }
        }
      }
    }
  }
`,z=i`
  query CustomFieldsAttributePositionsQuery($handle: String!) {
    team(handle: $handle) {
      id
      hacker_facing_custom_fields: custom_field_attributes(
        first: 100
        where: { internal: { _eq: false } }
      ) {
        edges {
          node {
            ... on CustomFieldAttributeInterface {
              id
              position
              archived_at
              label
              internal
            }
          }
        }
      }
      internal_custom_fields: custom_field_attributes(
        first: 100
        where: { internal: { _eq: true } }
      ) {
        edges {
          node {
            ... on CustomFieldAttributeInterface {
              id
              position
              archived_at
              label
              internal
            }
          }
        }
      }
    }
  }
`,B=1,V=2,H=(e,t,n,r)=>{let i=e.readQuery({query:z,variables:{handle:t.handle}});if(!i)return null;e.writeQuery({query:z,variables:{handle:t.handle},data:{...i,team:{...i.team,hacker_facing_custom_fields:{...i.team.hacker_facing_custom_fields,edges:(0,F.default)(i.team.hacker_facing_custom_fields.edges,n,r)}}}})},U=A(()=>(0,I.jsx)(x,{glyph:P,size:`extra-small`,color:`slate`})),W=k(({handle:e,customField:t,sortable:n,onCustomFieldArchiveUpdate:r})=>(0,I.jsxs)(m.Row,{className:(0,M.default)(`spec-custom-fields-${t.database_id}`,{"text-muted":t.archived_at}),children:[(0,I.jsx)(m.Cell,{maxWidth:25,children:(0,I.jsx)(C,{flexDirection:`row`,alignItems:`center`,children:n&&!t.archived_at&&(0,I.jsx)(U,{})})}),(0,I.jsx)(m.Cell,{children:t.label}),(0,I.jsx)(m.Cell,{truncate:!0,children:t.key}),(0,I.jsx)(m.Cell,{children:t.internal?`Internal`:`Hacker Facing`}),(0,I.jsx)(m.Cell,{children:t.archived_at?(0,I.jsx)(f,{horizontal:!0,separator:!0,children:(0,I.jsx)(f.Item,{children:(0,I.jsx)(`a`,{onClick:()=>r(t,!1),className:`daisy-link`,children:`Unarchive`})})}):(0,I.jsxs)(f,{horizontal:!0,separator:!0,children:[(0,I.jsx)(f.Item,{children:(0,I.jsx)(b,{to:`/${e}/custom_fields/${t.database_id}/edit`,className:`daisy-link`,children:`Edit`})}),(0,I.jsx)(f.Item,{children:(0,I.jsx)(`a`,{onClick:()=>r(t,!0),className:`daisy-link`,children:`Archive`})})]})})]},t.id)),G=j(({handle:e,customFields:t,mutating:n,sortable:r,onCustomFieldArchiveUpdate:i})=>(0,I.jsx)(m.Body,{children:t.map(t=>{let a=t.archived_at!==null;return(0,I.jsx)(W,{index:t.position,collection:a?V:B,disabled:a||n||!r,sortable:r,customField:t,handle:e,onCustomFieldArchiveUpdate:i},`item-${t.id}`)})})),K=({team:{handle:e},team:t,customFields:n,sortable:r,className:i})=>{let[a,{client:o,loading:s}]=y(R,{onCompleted:({repositionCustomFieldAttribute:e})=>{e.was_successful?g(`notice`,`Custom field was successfully updated.`):E()}}),[c]=y(L,{onCompleted:({toggleArchivedCustomFieldAttribute:e})=>{e.was_successful?g(`notice`,`Custom field was successfully updated.`):E()}}),l=(t,n)=>{a({variables:{id:t.id,...n},refetchQueries:[{query:z,variables:{handle:e}}]})},u=(t,{archived:n})=>{c({variables:{id:t.id,archived:n},refetchQueries:[{query:z,variables:{handle:e}}]})};return(0,I.jsxs)(m,{className:i,children:[(0,I.jsx)(m.Head,{children:(0,I.jsxs)(m.Row,{children:[(0,I.jsx)(m.CellHeader,{}),(0,I.jsx)(m.CellHeader,{children:`Field Title`}),(0,I.jsx)(m.CellHeader,{children:(0,I.jsx)(D,{className:`inline-help`,tooltipText:`Used as a reference in integrations and CSV exports`,children:`Key`})}),(0,I.jsx)(m.CellHeader,{children:`Visibility`}),(0,I.jsx)(m.CellHeader,{children:`Action`})]})}),n.length===0?(0,I.jsx)(m.Body,{children:(0,I.jsx)(m.Row,{children:(0,I.jsx)(m.Cell,{colSpan:5,children:(0,I.jsx)(`p`,{className:`daisy-text`,children:`No custom fields created yet.`})})})}):(0,I.jsx)(G,{customFields:n,handle:e,helperClass:`daisy-table__row--drag-and-drop`,mutating:s,sortable:r,onCustomFieldArchiveUpdate:(e,t)=>{u(e,{archived:t}),t?h.track(`custom field archived`):h.track(`custom field unarchived`)},onSortEnd:({oldIndex:e,newIndex:r,collection:i})=>{if(i===B){let i=e=>n.findIndex(t=>!t.archived_at&&t.position===e),a=i(e),s=i(r);if(a<=-1||s<=-1)return null;let c=n[a];return H(o,t,a,s),l(c,{position:r})}},onSortStart:({node:e,helper:t})=>e.childNodes.forEach((e,n)=>t.childNodes[n].style.width=`${e.offsetWidth}px`),useDragHandle:!0,lockToContainerEdges:!0,lockAxis:`y`})]})};K.propTypes={team:N.default.shape({handle:N.default.string.isRequired}),sortable:N.default.bool,className:N.default.string,customFields:N.default.arrayOf(N.default.shape({id:N.default.string.isRequired,database_id:N.default.string.isRequired,label:N.default.string.isRequired,type:N.default.string.isRequired,internal:N.default.bool.isRequired,position:N.default.number.isRequired,archived_at:N.default.string}))},K.fragments={team:i`
    fragment CustomFieldsTableTeamFragment on Team {
      id
      handle
    }
  `,customField:i`
    fragment CustomFieldsTableCustomFieldFragment on CustomFieldAttributeInterface {
      id
      label
      key
      internal
      position
      database_id: _id
      type: __typename
      archived_at
    }
  `},c();var q=({team:e})=>{let t=e.hacker_facing_custom_fields.edges.map(({node:e})=>e),n=e.internal_custom_fields.edges.map(({node:e})=>e);return(0,I.jsxs)(I.Fragment,{children:[(0,I.jsxs)(C,{children:[(0,I.jsx)(C,{flexGrow:1,children:(0,I.jsxs)(`div`,{className:`spec-scopes-title mb-md`,children:[(0,I.jsx)(s,{children:`Custom Fields`}),(0,I.jsx)(a,{top:`16`}),(0,I.jsxs)(l,{children:[`Add a custom field to tag your reports with key-value data. Learn more about`,` `,(0,I.jsx)(`a`,{href:`https://docs.hackerone.com/organizations/custom-fields.html`,target:`_blank`,rel:`noreferrer`,children:`custom fields`}),`.`]})]})}),(0,I.jsx)(o,{variation:u.Primary,renderAs:`link`,to:`/${e.handle}/custom_fields/new`,children:`Add custom field`})]}),(0,I.jsxs)(C,{flexDirection:`column`,children:[(0,I.jsx)(`strong`,{className:`daisy-text`,children:`Hacker Facing Custom Fields`}),(0,I.jsx)(`p`,{className:`daisy-text`,children:`Manage your public custom fields. You can reorder them in the order you prefer to display them on the report form.`}),(0,I.jsx)(C,{flexGrow:1,className:`card`,children:(0,I.jsx)(K,{customFields:t,team:e,sortable:!0,className:`spec-team-hacker-facing-custom-fields-table`})})]}),(0,I.jsxs)(C,{flexDirection:`column`,className:`margin-32--top`,children:[(0,I.jsx)(`strong`,{className:`daisy-text`,children:`Internal Custom Fields`}),(0,I.jsx)(`p`,{className:`daisy-text`,children:`Manage your internal custom fields.`}),(0,I.jsx)(C,{flexGrow:1,className:`card`,children:(0,I.jsx)(K,{customFields:n,team:e,className:`spec-team-internal-custom-fields-table`})})]})]})};q.fragments={team:i`
    fragment CustomFieldsOverviewTeamFragment on Team {
      id
      handle
      ...CustomFieldsTableTeamFragment
      internal_custom_fields: custom_field_attributes(
        first: 100
        where: { internal: { _eq: true } }
      ) {
        edges {
          node {
            ...CustomFieldsTableCustomFieldFragment
          }
        }
      }
      hacker_facing_custom_fields: custom_field_attributes(
        first: 100
        where: { internal: { _eq: false } }
      ) {
        edges {
          node {
            ...CustomFieldsTableCustomFieldFragment
          }
        }
      }
    }
    ${K.fragments.customField}
    ${K.fragments.team}
  `},q.propTypes={team:N.default.shape({handle:N.default.string.isRequired,internal_custom_fields:N.default.shape({edges:N.default.arrayOf(N.default.shape({node:N.default.shape({id:N.default.string.isRequired,database_id:N.default.string.isRequired,label:N.default.string.isRequired,position:N.default.number.isRequired,internal:N.default.bool.isRequired,type:N.default.string.isRequired,archived_at:N.default.string})}))}),hacker_facing_custom_fields:N.default.shape({edges:N.default.arrayOf(N.default.shape({node:N.default.shape({id:N.default.string.isRequired,database_id:N.default.string.isRequired,label:N.default.string.isRequired,position:N.default.number.isRequired,internal:N.default.bool.isRequired,type:N.default.string.isRequired,archived_at:N.default.string})}))})})};var J=t({CUSTOM_FIELDS_QUERY:()=>Y,default:()=>X});c();var Y=i`
  query CustomFieldsSettingsPageQuery($handle: String!) {
    team(handle: $handle) {
      id
      i_can_manage_custom_fields
      ...CustomFieldsOverviewTeamFragment
    }
  }
  ${q.fragments.team}
`,X=({match:e})=>{let{data:t,loading:n}=T(Y,{variables:{handle:e.params.handle}});if(n&&!t)return(0,I.jsx)(v,{});let r=e.params.handle,i=t.team;return(0,I.jsx)(w,{children:(0,I.jsx)(_,{header:(0,I.jsx)(S,{match:e}),content:i.i_can_manage_custom_fields?(0,I.jsx)(q,{team:i}):(0,I.jsxs)(p.Context,{name:constants.gates.all.custom_fields,teamHandle:r,children:[(0,I.jsx)(p.Open,{children:(0,I.jsx)(q,{team:i})}),(0,I.jsx)(p.Closed,{children:(0,I.jsxs)(`div`,{className:`settings-title-container mb-md`,children:[(0,I.jsx)(s,{children:`Custom Fields`}),(0,I.jsx)(a,{top:`16`}),(0,I.jsxs)(l,{children:[`Add a custom field to tag your reports with key-value data. Learn more about`,` `,(0,I.jsx)(b,{to:`https://docs.hackerone.com/organizations/custom-fields.html`,newTab:!0,children:`custom fields.`})]}),(0,I.jsx)(p.CustomFieldsUpgradeNotice,{})]})}),(0,I.jsx)(`br`,{})]}),hasBackground:!1})})};X.propTypes={match:N.default.shape({params:N.default.shape({handle:N.default.string.isRequired}).isRequired}).isRequired};export{J as n,Y as t};
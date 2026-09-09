import{o as e}from"./rolldown-runtime-DAXXjFlN.js";import{Fw as t,Hl as n,Iw as r,Kx as i,Lr as a,Qy as o,Rw as s,Ul as c,Uu as l,Y_ as u,Za as d,cp as f,lp as p,nb as m,qx as h,sd as g,zx as _}from"./vendor-_WdvpBLr.js";import{Ah as v,Pn as y,Sd as b,T as x,Th as S,_h as C,_i as w,ba as T,dh as E,dl as D,k as O,qr as k,vh as A,vm as j,ym as M}from"./app-5pKgUmmm.js";var N=e(s());h();var P=e(_()),F=t(),I=i`
  mutation UpdateTeamSwagSetting($team_id: ID!, $offers_swag: Boolean!) {
    updateTeamSwagSetting(
      input: { team_id: $team_id, offers_swag: $offers_swag }
    ) {
      was_successful
      team {
        id
        offers_swag
        product_edition {
          id
          swag_enabled
        }
      }
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
`,L=({team:e})=>{let[t,{loading:n}]=C(I,{onCompleted({updateTeamSwagSetting:e}){e.was_successful?M():j()}});return(0,F.jsx)(f,{fill:!0,children:(0,F.jsx)(p,{children:(0,F.jsx)(`div`,{className:`flex justify-between text-base`,children:(0,F.jsx)(l,{screenReaderLabel:`Enable program to award swag`,label:`Allow program to award swag?`,testId:`swag-switch`,checked:e.offers_swag,className:`pull-right`,disabled:n,onChange:()=>{t({variables:{team_id:e.id,offers_swag:!e.offers_swag}})}})})})})};L.fragments={team:i`
    fragment TeamSwagSettings on Team {
      id
      offers_swag
    }
  `},L.propTypes={team:P.default.shape({id:P.default.string.isRequired,offers_swag:P.default.bool.isRequired})};var R=({address:e})=>(0,F.jsxs)(`div`,{children:[e.street,`, `,e.city,`, `,e.state,`, `,e.postal_code,`,`,` `,e.country,`, Phone: `,e.phone_number]});R.propTypes={address:P.default.shape({street:P.default.string.isRequired,city:P.default.string.isRequired,state:P.default.string.isRequired,postal_code:P.default.string.isRequired,country:P.default.string.isRequired,phone_number:P.default.string.isRequired}).isRequired},h();var z=e(r()),B=i`
  mutation MarkSwagAsSent($swag_id: ID!, $sent: Boolean!) {
    markSwagAsSent(input: { swag_id: $swag_id, sent: $sent }) {
      was_successful
      swag {
        id
        sent
      }
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
`,V=({title:e,field:t,orderBy:r,setOrderBy:i})=>{let a=Object.keys(r)[0],o=r[a]._direction;return(0,F.jsxs)(b.CellHeader,{children:[e,(0,F.jsx)(`span`,{className:(0,z.default)(`cursor-pointer ml-spacing-4`,{"text-blue-500":a===t}),onClick:()=>{i({[t]:{_direction:o===`ASC`?`DESC`:`ASC`}})},children:(0,F.jsx)(m,{src:a===t&&o===`ASC`?c:n,size:`md`})})]})};V.propTypes={title:P.default.string.isRequired,field:P.default.string.isRequired,orderBy:P.default.object.isRequired,setOrderBy:P.default.func.isRequired};var H=({swagEnabled:e,swagTransactions:t,loadMore:n,orderBy:r,setOrderBy:i})=>{let[a,s]=(0,N.useState)(null),[c]=C(B,{onCompleted({markSwagAsSent:e}){s(null),e.was_successful?M():j()}});return(0,F.jsxs)(b,{className:`table`,children:[(0,F.jsx)(b.Head,{children:(0,F.jsxs)(b.Row,{children:[(0,F.jsx)(b.CellHeader,{}),(0,F.jsx)(V,{title:`Report`,field:`report_id`,orderBy:r,setOrderBy:i}),(0,F.jsx)(V,{title:`Reporter`,field:`user_id`,orderBy:r,setOrderBy:i}),(0,F.jsx)(b.CellHeader,{children:`Address`}),(0,F.jsx)(b.CellHeader,{width:`100px`,children:`T-Shirt size`}),(0,F.jsx)(V,{title:`Status`,field:`sent`,orderBy:r,setOrderBy:i})]})}),(0,F.jsxs)(b.Body,{children:[t.edges.map(e=>e.node).map(t=>(0,F.jsxs)(b.Row,{className:`spec-swag-transaction-${t._id}`,children:[(0,F.jsx)(b.Cell,{children:(0,F.jsx)(u,{testId:`swag-transaction-checkbox-${t._id}`,checked:t.sent,accessibilityLabel:`Mark swag as ${t.sent?`unsent`:`sent`}`,disabled:!e||a===t.id,onChange:()=>{s(t.id),c({variables:{swag_id:t.id,sent:!t.sent}})}},t.id)}),(0,F.jsx)(b.Cell,{children:(0,F.jsxs)(`a`,{className:`daisy-link`,href:`/reports/${t.report._id}`,children:[`#`,t.report._id]})}),(0,F.jsx)(b.Cell,{children:(0,F.jsx)(`a`,{className:`daisy-link`,href:`/${t.user.username}`,children:t.user.address&&t.user.address.name||t.user.username})}),(0,F.jsx)(b.Cell,{children:t.user.address?(0,F.jsx)(R,{address:t.user.address}):`Address request sent`}),(0,F.jsx)(b.Cell,{children:t.user.address&&t.user.address.tshirt_size||`-`}),(0,F.jsx)(b.Cell,{children:a===t.id?`Saving`:t.sent?`Sent`:`Unsent`})]},t.id)),t.pageInfo.hasNextPage&&(0,F.jsx)(b.Row,{children:(0,F.jsx)(b.Cell,{className:`text-aligned-center`,colSpan:6,children:(0,F.jsx)(o,{variation:`tertiary`,onClick:n,children:`Load more`})})})]})]})};H.fragments={team:i`
    fragment TeamSwagTransactions on Team {
      id
      swag(
        first: $pageSize
        after: $cursor
        order_by: $orderBy
        where: $where
      ) {
        edges {
          node {
            _id
            id
            sent
            created_at
            report {
              id
              _id
            }
            user {
              id
              username
              address {
                id
                name
                street
                city
                state
                postal_code
                country
                phone_number
                tshirt_size
              }
            }
          }
        }
        pageInfo {
          endCursor
          hasNextPage
        }
      }
    }
  `},H.propTypes={swagTransactions:P.default.shape({edges:P.default.arrayOf(P.default.shape({node:P.default.shape({id:P.default.string.isRequired,sent:P.default.bool.isRequired,user:P.default.shape({username:P.default.string.isRequired,address:P.default.shape({street:P.default.string.isRequired,city:P.default.string.isRequired,state:P.default.string.isRequired,postal_code:P.default.string.isRequired,country:P.default.string.isRequired,phone_number:P.default.string.isRequired})}),report:P.default.shape({_id:P.default.string.isRequired})})}).isRequired),pageInfo:P.default.shape({endCursor:P.default.string,hasNextPage:P.default.bool.isRequired})}),swagEnabled:P.default.bool.isRequired,loadMore:P.default.func.isRequired,orderBy:P.default.object.isRequired,setOrderBy:P.default.func.isRequired},h();var U=d(),W=i`
  query TeamSwagQuery(
    $handle: String!
    $pageSize: Int!
    $cursor: String
    $orderBy: FiltersSwagFilterOrder!
    $where: FiltersSwagFilterInput!
  ) {
    team(handle: $handle) {
      id
      offers_swag
      allowed_to_offer_swag
      ...TeamSwagSettings
      ...TeamSwagTransactions
    }
  }

  ${L.fragments.team}
  ${H.fragments.team}
`,G=[{label:`Sent`,value:!0},{label:`Unsent`,value:!1}],K=({handle:e})=>{let[t,n]=(0,N.useState)({id:{_direction:`ASC`}}),[r,i]=(0,N.useState)([!0,!1]),{data:a,loading:o,fetchMore:s}=A(W,{variables:{handle:e,pageSize:100,orderBy:t,where:{sent:{_in:r.length===0?[!0,!1]:r}}}}),c=D(a,`team.swag`,s);if(o&&!a)return(0,F.jsx)(S,{});let l=()=>{let e=new U.CsvBuilder(`export.csv`);e.addRow([`id`,`report_id`,`name`,`street`,`city`,`state`,`postal_code`,`country`,`phone_number`,`tshirt_size`,`status`,`created_at`]),a.team.swag.edges.forEach(({node:t})=>{e.addRow([t._id,t.report?._id,t.user?.address?.name||`@${t.user?.username}`,t.user?.address?.street,t.user?.address?.city,t.user?.address?.state,t.user?.address?.postal_code,t.user?.address?.country,t.user?.address?.phone_number,t.user?.address?.tshirt_size,t.sent?`sent`:`unsent`,t.created_at])}),e.exportFile()};return(0,F.jsxs)(`div`,{children:[(0,F.jsxs)(w,{children:[(0,F.jsx)(w.Title,{children:`Swag`}),(0,F.jsx)(w.Description,{children:`Manage awarding and awarded swag to hackers.`})]}),a.team?.allowed_to_offer_swag||a.team?.offers_swag?(0,F.jsxs)(F.Fragment,{children:[(0,F.jsx)(L,{team:a.team}),(0,F.jsx)(`div`,{className:`mt-sm`,children:(0,F.jsxs)(f,{children:[(0,F.jsx)(p,{children:(0,F.jsxs)(`div`,{className:`flex flex-row`,children:[(0,F.jsx)(`div`,{className:`my-auto flex-0`,children:(0,F.jsx)(`strong`,{children:`Status`})}),(0,F.jsx)(`div`,{className:`ml-spacing-8 flex-0`,children:(0,F.jsx)(g,{onChange:e=>{i(e.map(e=>e.value))},isMulti:!0,options:G,selectedOption:G.filter(e=>r.includes(e.value))})}),(0,F.jsx)(`div`,{className:`flex-auto`}),(0,F.jsx)(`div`,{className:`my-auto flex-0`,children:(0,F.jsx)(E,{to:``,onClick:e=>{l(),e.preventDefault()},children:`Download as CSV`})})]})}),(0,F.jsx)(p,{edgeToEdge:!0,children:(0,F.jsx)(H,{swagEnabled:a.team.offers_swag,swagTransactions:a.team.swag,loadMore:c,orderBy:t,setOrderBy:n})})]})})]}):(0,F.jsx)(y,{})]})};K.propTypes={handle:P.default.string.isRequired};var q=e=>{let t=e.match.params.handle;return(0,F.jsx)(k,{children:(0,F.jsx)(x,{header:(0,F.jsx)(O,{...e}),hasBackground:!1,content:(0,F.jsxs)(`div`,{children:[(0,F.jsx)(a,{children:(0,F.jsx)(`title`,{children:T(`Swag`)})}),(0,F.jsx)(K,{handle:t})]}),footer:(0,F.jsx)(v,{})})})};q.propTypes={match:P.default.shape({params:P.default.shape({handle:P.default.string.isRequired}).isRequired}).isRequired};export{q as default};
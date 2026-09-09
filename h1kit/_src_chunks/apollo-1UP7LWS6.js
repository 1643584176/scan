import{o as e}from"./rolldown-runtime-DAXXjFlN.js";import{Fw as t,Kx as n,Rw as r,gw as i,qx as a,zx as o}from"./vendor-_WdvpBLr.js";import{$f as s,Th as c,Tm as l,_h as u,dh as d,fm as f,hh as p,lh as m,mm as h,op as g,pm as _,tc as v,tp as y,uh as b,vh as x}from"./app-5pKgUmmm.js";var S=e(r());a();var C=t(),w=n`
  query SimpleQuery($handle: String!) {
    team(handle: $handle) {
      id
      handle
      name
      about
      profile_picture(size: medium)
    }
  }
`,T=()=>{let{data:e,loading:t,error:n}=x(w,{variables:{handle:`security`}});if(t)return(0,C.jsx)(c,{renderInBody:!0,children:`Loading...`});if(n)return(0,C.jsx)(`span`,{children:`an error occurred...`});let{team:r}=e;return(0,C.jsxs)(S.default.Fragment,{children:[(0,C.jsx)(b,{children:(0,C.jsxs)(m,{width:300,alignItems:`center`,children:[(0,C.jsx)(_,{size:`medium`,src:r.profile_picture,object:r,className:`margin-16--right`}),(0,C.jsx)(d,{className:`daisy-link`,to:`/${r.handle}`,children:r.name})]})}),(0,C.jsx)(b,{children:r.about})]})},E=()=>(0,C.jsxs)(l,{children:[(0,C.jsx)(l.Heading,{children:`Simple Apollo Query Example`}),(0,C.jsx)(l.Content,{children:(0,C.jsx)(T,{})})]});a();var D={CHANGE_SELECTION:`CHANGE_SELECTION`},O=e=>({selection:e}),k=(e,t)=>{switch(t.type){case D.CHANGE_SELECTION:return{...e,selection:t.value};default:return e}},A=e=>({handle:e.selection}),j=n`
  query ReducerQuery($handle: String!) {
    team(handle: $handle) {
      id
      handle
      name
      about
      profile_picture(size: medium)
    }
  }
`,M=()=>{let[e,t]=(0,S.useReducer)(k,O(`security`)),{data:n,loading:r,error:i}=x(j,{variables:A(e)});return r?(0,C.jsx)(c,{renderInBody:!0,children:`Loading...`}):i?(0,C.jsx)(`span`,{children:`an error occurred...`}):(0,C.jsxs)(S.default.Fragment,{children:[(0,C.jsx)(b,{children:(0,C.jsxs)(m,{alignItems:`center`,children:[(0,C.jsx)(v,{name:`program`,value:`security`,checked:e.selection===`security`,onChange:({target:{value:e}})=>t({type:D.CHANGE_SELECTION,value:e}),children:`HackerOne`}),(0,C.jsx)(v,{className:`margin-8--left`,name:`program`,value:`shopify`,checked:e.selection===`shopify`,onChange:({target:{value:e}})=>t({type:D.CHANGE_SELECTION,value:e}),children:`Shopify`})]})}),(0,C.jsxs)(S.default.Fragment,{children:[(0,C.jsx)(b,{children:(0,C.jsxs)(m,{width:300,alignItems:`center`,children:[(0,C.jsx)(_,{size:`medium`,src:n.team.profile_picture,object:n.team,className:`margin-16--right`}),(0,C.jsx)(d,{className:`daisy-link`,to:`/${n.team.handle}`,children:n.team.name})]})}),(0,C.jsx)(b,{children:n.team.about})]})]})},N=()=>(0,C.jsxs)(l,{children:[(0,C.jsx)(l.Heading,{children:`With Reducer Example`}),(0,C.jsx)(l.Content,{children:(0,C.jsx)(M,{})})]}),P=e(o());a();var F=n`
  mutation BookmarkTeamExample($teamId: ID!) {
    updateBookmarkedTeam(input: { team_id: $teamId }) {
      team {
        id
        bookmarked
      }
    }
  }
`,I=({team:e})=>{let[t,{loading:n}]=u(F,{variables:{teamId:e.id},optimisticResponse:{updateBookmarkedTeam:{__typename:`Mutation`,team:{__typename:`Team`,id:e.id,bookmarked:!e.bookmarked}}}});return(0,C.jsx)(h,{onClick:()=>t({teamId:e.id}),loading:n,bookmarked:e.bookmarked,showLabel:!0})};I.propTypes={team:P.default.object.isRequired},I.fragments={team:n`
    fragment BookmarkLinkTeam on Team {
      id
      bookmarked
    }
  `};var L=n`
  query SimpleMutationQuery($handle: String!) {
    me {
      id
    }
    team(handle: $handle) {
      id
      handle
      name
      profile_picture(size: medium)
      ...BookmarkLinkTeam
    }
  }
  ${I.fragments.team}
`,R=()=>{let{data:e,loading:t,error:n}=x(L,{variables:{handle:`security`}});if(t)return(0,C.jsx)(c,{renderInBody:!0,children:`Loading...`});if(n)return(0,C.jsx)(`span`,{children:`an error occurred...`});let{team:r,me:i}=e;return(0,C.jsxs)(S.default.Fragment,{children:[(0,C.jsx)(b,{children:(0,C.jsxs)(m,{width:300,alignItems:`center`,children:[(0,C.jsx)(_,{size:`medium`,src:r.profile_picture,object:r,className:`margin-16--right`}),(0,C.jsx)(d,{className:`daisy-link`,to:`/${r.handle}`,children:r.name})]})}),i?(0,C.jsx)(I,{team:r}):(0,C.jsx)(`span`,{children:`You have to be signed in to bookmark a team`})]})},z=()=>(0,C.jsxs)(l,{children:[(0,C.jsx)(l.Heading,{children:`Mutation Example`}),(0,C.jsx)(l.Content,{children:(0,C.jsx)(R,{})})]}),B=e(i());a();var V=5,H=n`
  query PaginationQuery($pageSize: Int!, $cursor: String) {
    teams(first: $pageSize, after: $cursor) {
      pageInfo {
        endCursor
        hasNextPage
      }
      edges {
        node {
          id
          handle
          name
          profile_picture(size: medium)
        }
      }
    }
  }
`,U=(e,t,n)=>()=>n({variables:{cursor:(0,B.default)(e,`${t}.pageInfo.endCursor`)},updateQuery:(e,{fetchMoreResult:n})=>{let r=(0,B.default)(n,`${t}.edges`),i=(0,B.default)(n,`${t}.pageInfo`);return r.length?{...e,[t]:{__typename:(0,B.default)(e,`${t}.__typename`),edges:[...(0,B.default)(e,`${t}.edges`),...r],pageInfo:i}}:e}}),W=()=>{let{data:e,loading:t,error:n,fetchMore:r}=x(H,{variables:{pageSize:V}});if(t)return(0,C.jsx)(c,{renderInBody:!0,children:`Loading...`});if(n)return(0,C.jsx)(`span`,{children:`an error occurred...`});let{teams:i}=e,a=U(e,`teams`,r);return(0,C.jsx)(S.default.Fragment,{children:(0,C.jsxs)(b,{children:[(0,C.jsx)(s,{unstyled:!0,children:i.edges.map(({node:e})=>(0,C.jsx)(s.Item,{children:(0,C.jsx)(b,{children:(0,C.jsxs)(m,{width:300,alignItems:`center`,children:[(0,C.jsx)(_,{size:`medium`,src:e.profile_picture,object:e,className:`margin-16--right`}),(0,C.jsx)(d,{className:`daisy-link`,to:`/${e.handle}`,children:e.name})]})})},e.id))}),(0,C.jsx)(g,{onClick:a,disabled:!i.pageInfo.hasNextPage,children:`Load more`})]})})},G=()=>(0,C.jsxs)(l,{children:[(0,C.jsx)(l.Heading,{children:`Pagination Example`}),(0,C.jsx)(l.Content,{children:(0,C.jsx)(W,{})})]}),K=()=>(0,C.jsx)(p,{children:(0,C.jsxs)(p.Content,{children:[(0,C.jsxs)(b,{top:!0,children:[(0,C.jsx)(b,{children:(0,C.jsxs)(y,{variation:`green`,children:[`Your reconnaissance game is on point if you are a Hacker and you found this page! Unfortunately, there's not much to exploit here and reporting this will probably end up with a `,(0,C.jsx)(`code`,{children:`-7`}),` `,`reputation hit.`]})}),(0,C.jsx)(b,{children:(0,C.jsx)(E,{})}),(0,C.jsx)(b,{children:(0,C.jsx)(N,{})}),(0,C.jsx)(b,{children:(0,C.jsx)(z,{})}),(0,C.jsx)(b,{children:(0,C.jsx)(G,{})})]}),(0,C.jsx)(b,{children:(0,C.jsx)(f,{children:`This information was fetched using Apollo Client`})})]})});export{K as default};
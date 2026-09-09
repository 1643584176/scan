import{o as e}from"./rolldown-runtime-DAXXjFlN.js";import{Fw as t,Kx as n,Pb as r,Rw as i,qx as a,sb as o,zx as s}from"./vendor-_WdvpBLr.js";import{Qs as c,Tm as l,dh as u,fm as d,lh as f,oh as p,sm as m,vh as h,vp as g}from"./app-5pKgUmmm.js";var _=e(i()),v=e(r()),y=e(s()),b=e(o());a();var x=t(),S=`last_90_days`,C=`past_year`,w=`all_time`,T=[{value:S,label:`90 Days`},{value:C,label:`Past Year`},{value:w,label:`All Time`}],E=n`
  query UserProfileStatsCardAllTime($username: String!) {
    user(username: $username) {
      id
      signal
      signal_percentile
      impact
      impact_percentile
      reputation
      rank
    }
  }
`,D=n`
  query UserProfileStatsCardSnapshot(
    $username: String!
    $snapshotType: UserStatisticsSnapshotTypeEnum!
  ) {
    user(username: $username) {
      id
      statistics_snapshot(snapshot_type: $snapshotType) {
        id
        signal
        signal_percentile
        impact
        impact_percentile
        reputation
        rank
      }
    }
  }
`,O=_.createContext(!0),k=({value:e,label:t,tooltipText:n})=>(0,x.jsxs)(f,{flexBasis:`50%`,justifyContent:`center`,marginBottom:`32px`,flexDirection:`column`,alignItems:`center`,children:[(0,x.jsx)(`h4`,{className:`daisy-h4 no-margin`,children:(0,_.useContext)(O)?(0,x.jsx)(p,{width:`50px`}):e}),n?(0,x.jsx)(g,{tooltipText:n,children:(0,x.jsx)(d,{className:`inline-help spec-label-hover`,children:t})}):(0,x.jsx)(d,{children:t})]});k.propTypes={value:y.default.oneOfType([y.default.number,y.default.string]),label:y.default.string.isRequired,tooltipText:y.default.string};var A=({label:e,value:t,percentile:n,tooltipText:r})=>{let i=v.default.number(t)?t.toFixed(2):`-`,a=v.default.number(n)?b.default.ordinal(n):`-`;return(0,x.jsxs)(x.Fragment,{children:[(0,x.jsx)(k,{value:i,label:e,tooltipText:r}),(0,x.jsx)(k,{value:a,label:`Percentile`})]})};A.propTypes={value:y.default.number,label:y.default.string.isRequired,percentile:y.default.number,tooltipText:y.default.string};var j=({reputation:e,rank:t})=>{let n=e||`-`,r=v.default.number(t)&&t<=100?b.default.ordinal(t):`-`,i=v.default.not.number(e)?`Reputation is automatically calculated once enough activity is available.`:null;return(0,x.jsxs)(x.Fragment,{children:[(0,x.jsx)(k,{value:n,label:`Reputation`,tooltipText:i}),(0,x.jsx)(k,{value:r,label:`Rank`})]})};j.propTypes={reputation:y.default.number,rank:y.default.number};var M=({username:e,user:t={},me:n,cardTitle:r})=>{let{id:i}=t,a=e||t.username,o=n&&i===n.id,[s,d]=(0,_.useState)(S),p=s===w,{data:g,loading:v}=h(p?E:D,{variables:{username:a,snapshotType:s}}),{signal:y,signal_percentile:b,impact:C,impact_percentile:k,reputation:M,rank:N}=g?p?g.user:g.user.statistics_snapshot||{}:{};return(0,x.jsx)(O.Provider,{value:v,children:(0,x.jsxs)(l,{children:[(0,x.jsx)(l.Heading,{children:(0,x.jsxs)(f,{flexDirection:`row`,alignItems:`center`,children:[r,(0,x.jsx)(f,{flexGrow:1,justifyContent:`flex-end`,children:(0,x.jsx)(c,{className:`spec-stats-dropdown`,value:s,onChange:e=>d(e.target.value),options:T})})]})}),(0,x.jsxs)(l.Content,{children:[(0,x.jsxs)(f,{flexWrap:`wrap`,marginBottom:`-32px`,children:[(0,x.jsx)(A,{label:`Signal`,tooltipText:`The average Reputation per report (-10 to 7).`,value:y,percentile:b}),(0,x.jsx)(A,{label:`Impact`,tooltipText:`The average Reputation per bounty (0 to 50).`,value:C,percentile:k}),(0,x.jsx)(j,{reputation:M,rank:N})]}),o&&(0,x.jsxs)(x.Fragment,{children:[(0,x.jsx)(m,{removeCardSpacing:!0}),(0,x.jsx)(u,{to:`https://docs.hackerone.com/hackers/invitations.html`,className:`daisy-text daisy-text--small`,children:`Learn how your stats affect invitations to private programs.`})]})]})]})})};M.propTypes={username:y.default.string,user:y.default.object,me:y.default.object,cardTitle:y.default.node.isRequired},M.defaultProps={cardTitle:`Stats`},M.fragments={user:n`
    fragment UserStatsUser on User {
      id
      username
    }
  `,me:n`
    fragment UserStatsMe on User {
      id
    }
  `};export{M as t};
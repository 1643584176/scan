import{o as e,t}from"./rolldown-runtime-DAXXjFlN.js";import{$y as n,By as r,Cf as i,Ei as a,Fw as o,Iw as s,Kx as c,L_ as l,Lr as u,Ly as d,Mf as ee,Nb as f,Pb as p,Pf as m,Qd as te,Qr as ne,Qy as h,R_ as g,Rw as re,Ux as ie,Vb as ae,Vx as _,Xu as oe,br as se,cp as ce,cv as le,df as v,eb as ue,ff as y,iv as b,jw as de,lp as x,mw as fe,nb as S,nv as C,od as pe,ov as me,ow as he,qu as ge,qv as _e,qx as w,rb as T,rv as E,sb as ve,sd as ye,sp as be,sv as xe,tb as D,tv as Se,zx as Ce}from"./vendor-_WdvpBLr.js";import{Ah as we,Bm as Te,Cp as O,Eh as Ee,Ff as De,Hi as Oe,If as ke,Ip as k,Jp as Ae,Ju as je,Kf as Me,Mp as A,Nf as j,Oi as Ne,Ps as M,Qs as Pe,Sm as N,Tm as P,Uf as Fe,Xm as Ie,Xu as Le,_l as Re,ba as ze,ch as Be,cp as Ve,dh as F,dl as He,ed as Ue,ep as I,fm as L,gh as R,hp as We,lh as z,md as Ge,mh as Ke,nh as qe,od as Je,oh as B,op as Ye,pf as Xe,pm as V,sm as Ze,td as Qe,th as $e,uh as H,v as et,vh as U,vm as W,vp as tt,wm as nt,xu as rt,ya as it}from"./app-5pKgUmmm.js";import{t as at}from"./arrow-forward-1cCFCWu1.js";import{t as ot}from"./stats-Dei3giJr.js";import{t as st}from"./read_reports-CKOzZnm4.js";import{n as ct,t as lt}from"./full_hacktivity-CM9lW4Cn.js";import{t as ut}from"./_baseRandom-ZwHBN15W.js";import{a as dt,i as ft,n as pt,o as mt,r as ht,t as gt}from"./us_states-BmmO3vf8.js";import{n as _t,r as vt,t as yt}from"./user_profile_card-mjpCqC7A.js";w();var bt=e(fe()),G=e(re()),K=e(Ce()),q=o(),xt=5,St=c`
  query UserProfileTestimonialSkills(
    $username: String!
    $count: Int!
    $cursor: String
  ) {
    user(username: $username) {
      id
      hacker_skills(where: { skill: { approved: { _eq: true } } }) {
        nodes {
          id
          skill {
            id
            database_id: _id
            name
          }
        }
      }
      pentester_profile {
        id
        name
        certifications: certifications_pentester_profiles(
          first: $count
          after: $cursor
        ) {
          pageInfo {
            endCursor
            hasNextPage
          }
          edges {
            node {
              id
              certification {
                id
                name
                short_name
              }
              certification_identifier
              starts_at
              ends_at
            }
          }
        }
      }
    }
  }
`,Ct=({username:e,loading:t,skills:n})=>{let r=t||n?.length>0,i=t&&!n.length;return(0,q.jsx)(H,{top:!0,children:(0,q.jsxs)(P,{children:[(0,q.jsx)(P.Heading,{children:(0,q.jsx)(`span`,{children:`Skills`})}),r?(0,q.jsx)(P.Content,{children:(0,q.jsx)(`div`,{className:`grid grid-cols-1 md:grid-cols-2 gap-xs`,children:i?(0,q.jsx)(Be,{}):n.map(e=>(0,q.jsx)(z,{padding:`2px`,paddingBottom:0,children:(0,q.jsx)(nt,{variation:`grey`,size:`base`,rounded:!0,children:e.name})},e.id))})}):(0,q.jsx)(P.Content,{children:(0,q.jsxs)(et,{children:[(0,q.jsx)(`h3`,{className:`daisy-h3 no-margin`,children:`No skills found.`}),e,` hasn't cited any skills yet.`]})})]})})};Ct.propTypes={username:K.default.string.isRequired,loading:K.default.bool.isRequired,skills:K.default.array.isRequired};var wt=({cert:e})=>{let t=[e.starts_at&&(0,q.jsx)(L,{children:`Issued ${Me({date:e.starts_at})}`}),e.ends_at&&(0,q.jsx)(L,{children:`Expires ${Me({date:e.ends_at})}`}),e.certification_identifier&&(0,q.jsx)(L,{children:`Certification ID:  ${e.certification_identifier}`})].filter(bt.default);return(0,q.jsx)(z,{flexGrow:1,children:(0,q.jsxs)(z,{flexDirection:`column`,children:[(0,q.jsx)(z,{children:(0,q.jsx)(`strong`,{children:`${e.certification.name} (${e.certification.short_name})`})}),(0,q.jsx)(z,{children:t.map((e,n)=>(0,q.jsxs)(G.default.Fragment,{children:[e,n<t.length-1&&(0,q.jsx)(Oe,{width:14})]},n))})]})})};wt.propTypes={cert:K.default.object.isRequired};var Tt=({username:e,certs:t,loading:n,loadMore:r,hasNextPage:i})=>{let a=n||t?.length>0,o=n&&!t.length;return(0,q.jsx)(H,{top:!0,children:(0,q.jsxs)(P,{children:[(0,q.jsx)(P.Heading,{children:(0,q.jsx)(`span`,{children:`Certifications`})}),a?(0,q.jsxs)(P.Content,{children:[o?(0,q.jsx)(Be,{}):t.map((e,n)=>(0,q.jsxs)(q.Fragment,{children:[(0,q.jsx)(wt,{cert:e},e.id),n+1<t.length&&(0,q.jsx)(Ze,{style:{marginLeft:`-24px`,marginRight:`-24px`}})]})),i&&(0,q.jsx)(z,{justifyContent:`center`,alignItems:`center`,marginTop:16,children:n?(0,q.jsx)(Ee,{}):(0,q.jsx)(Ye,{className:`spec-thanks-view-more`,size:`small`,onClick:r,children:`View more`})})]}):(0,q.jsx)(P.Content,{children:(0,q.jsxs)(et,{children:[(0,q.jsx)(`h3`,{className:`daisy-h3 no-margin`,children:`No certifications found.`}),e,` hasn't cited any certifications yet.`]})})]})})};Tt.propTypes={username:K.default.string.isRequired,certs:K.default.array.isRequired,loading:K.default.bool,loadMore:K.default.func.isRequired,hasNextPage:K.default.bool};var Et=({username:e})=>{let{data:t,loading:n,fetchMore:r}=U(St,{variables:{username:e,count:xt},notifyOnNetworkStatusChange:!0}),i=He(t,`user.pentester_profile.certifications`,r),{user:a}=t||{},{pentester_profile:o,hacker_skills:s={}}=a||{},{certifications:c={}}=o||{},l=s?.nodes?.map(({skill:e})=>e)||[],u=c?.edges?.map(({node:e})=>e)||[],d=c.pageInfo?.hasNextPage;return(0,q.jsxs)(q.Fragment,{children:[(0,q.jsx)(Ct,{username:e,skills:l,loading:n}),(0,q.jsx)(Tt,{username:e,certs:u,loading:n,loadMore:i,hasNextPage:d})]})};Et.propTypes={username:K.default.string.isRequired};var J=e(p()),Dt=e(i()),Y=e(s()),Ot=({tooltipText:e,children:t})=>e?(0,q.jsx)(tt,{tooltipText:e,children:t}):t;Ot.propTypes={tooltipText:K.default.string,children:K.default.node};var kt=({amount:e,amountPrefix:t,amountTooltip:n,label:r,labelTooltip:i,className:a,loading:o})=>{let s=(0,Y.default)(`daisy-h4`,{"spec-amount-hover":n,"inline-help":n}),c=(0,Y.default)(`daisy-helper-text`,{"spec-label-hover":i,"inline-help":i});return(0,q.jsx)(H,{children:(0,q.jsxs)(`div`,{className:a,children:[(0,q.jsx)(Ot,{tooltipText:n,children:(0,q.jsx)(`div`,{className:`profile-stats-amount`,children:(0,q.jsxs)(`span`,{className:s,children:[t,o?(0,q.jsx)(B,{width:30}):e||0]})})}),(0,q.jsx)(`div`,{children:(0,q.jsx)(Ot,{tooltipText:i,children:(0,q.jsx)(`span`,{className:c,children:r})})})]})})};kt.propTypes={amount:K.default.oneOfType([K.default.string,K.default.number,K.default.node]),amountPrefix:K.default.oneOf([`>`,`<`,null]),amountTooltip:K.default.string,label:K.default.node.isRequired,labelTooltip:K.default.string,className:K.default.string.isRequired,size:K.default.string,titleColorIndicator:K.default.string,loading:K.default.bool},w();var At=({user:e={}})=>{let t=!e.id;return(0,q.jsx)(H,{top:!0,children:(0,q.jsxs)(P,{children:[(0,q.jsx)(P.Heading,{children:`Credits`}),(0,q.jsxs)(P.Content,{children:[(0,q.jsx)(kt,{className:`profile-metric__item spec-thanked`,amount:e.resolved_report_count,label:`Vulnerabilities found`,loading:t}),(0,q.jsx)(kt,{className:`profile-metric__item spec-thanked margin-15--bottom`,amount:e.thanks_items_total_count,label:`Thanks received`,loading:t})]})]})})};At.propTypes={user:K.default.object.isRequired},At.fragments={user:c`
    fragment CreditsUser on User {
      id
      username
      resolved_report_count
      thanks_items_total_count
    }
  `};var jt=class extends G.Component{static displayName=`Avatar`;static propTypes={size:K.default.oneOf([`tiny`,`small`,`emailmedium`,`emaillarge`,`medium`,`large`,`xtralarge`]),src:K.default.string.isRequired,object:K.default.shape({slug:K.default.string,username:K.default.string,handle:K.default.string,extended_display_name:K.default.string,name:K.default.string}).isRequired,className:K.default.string,showTitle:K.default.bool.isRequired};static defaultProps={size:`small`,object:{},showTitle:!0};alt=()=>{if(this.props.object)return this.props.object.slug||this.props.object.handle||this.props.object.username};title=()=>{if(this.props.object&&this.props.showTitle)return this.props.object.extended_display_name||this.props.object.name};render(){let e=(0,Y.default)([`better-avatar`,this.props.className,this.props.size]);return(0,q.jsx)(`img`,{src:this.props.src,alt:this.alt(),title:this.title(),className:e})}},Mt=({path:e})=>e?(0,q.jsx)(jt,{size:`medium`,className:`user-item__avatar spec-user-item__avatar`,src:e}):(0,q.jsx)(`span`,{className:`spec-user-item__bullet`,children:`•`}),Nt=({primaryTextUrl:e,primaryText:t,secondaryText:n,avatarImagePath:r})=>(0,q.jsx)(G.default.Fragment,{children:(0,q.jsxs)(z,{justifyContent:`flex-start`,marginBottom:`24px`,children:[e?(0,q.jsx)(F,{to:e,className:`spec-user__picture-url`,children:(0,q.jsx)(Mt,{path:r})}):(0,q.jsx)(Mt,{path:r}),(0,q.jsxs)(z,{flexDirection:`column`,marginLeft:`16px`,children:[e?(0,q.jsx)(F,{className:`daisy-h6 text-truncate break-word spec-user__url`,style:{margin:0},to:e,children:t}):t,n&&(0,q.jsx)(`div`,{className:`daisy-helper-text text-truncate break-word spec-user__meta`,children:n})]})]})});Nt.propTypes={primaryText:K.default.string.isRequired,primaryTextUrl:K.default.string,avatarImagePath:K.default.string,secondaryText:K.default.string},Mt.propTypes={path:K.default.string.isRequired},w();var Pt=({user:e={}})=>{let t=e.badges?.edges||[];return t.length===0?null:(0,q.jsx)(H,{top:!0,children:(0,q.jsxs)(P,{className:`spec-user-profile-recent-badges`,children:[(0,q.jsx)(P.Heading,{children:`Recent Badges`}),(0,q.jsxs)(P.Content,{children:[t.map((e,t)=>(0,q.jsx)(Nt,{primaryText:e.node.name,avatarImagePath:e.node.image_path,secondaryText:Fe({date:e.awarded_at,options:{monthAndYear:!0}})},t)),(0,q.jsx)(`a`,{className:`daisy-link`,href:`/${e.username}/badges`,children:(0,q.jsxs)(`div`,{style:{display:`flex`,alignItems:`center`},children:[(0,q.jsx)(`div`,{children:`All badges`}),(0,q.jsx)(S,{src:at,size:T.Medium})]})})]})]})})};Pt.propTypes={user:K.default.object},Pt.fragments={user:c`
    fragment BadgesUser on User {
      id
      username
      badges(first: 3) {
        edges {
          awarded_at
          node {
            id
            name
            image_path
          }
        }
      }
    }
  `};var Ft=t(((e,t)=>{var n=ut();function r(e){var t=e.length;return t?e[n(0,t-1)]:void 0}t.exports=r})),It=t(((e,t)=>{var n=Ft(),r=he();function i(e){return n(r(e))}t.exports=i})),Lt=e(t(((e,t)=>{var n=Ft(),r=It(),i=de();function a(e){return(i(e)?n:r)(e)}t.exports=a}))());w();var Rt=({user:e={}})=>{let t=(0,Lt.default)(e.public_reviews?.edges);return J.default.existy(t)&&(0,q.jsx)(H,{top:!0,children:(0,q.jsxs)(P,{className:`spec-user-reviews`,children:[(0,q.jsx)(P.Heading,{children:`What Programs Say`}),(0,q.jsx)(P.Content,{children:(0,q.jsxs)(H,{size:`extra-large`,children:[(0,q.jsx)(H,{size:`small`,children:`"${t.node.public_feedback}"`}),(0,q.jsx)(F,{className:`daisy-link pull-right`,to:`/${t.node.team.handle}`,children:`- ${t.node.team.name}`})]})})]})})};Rt.propTypes={user:K.default.object.isRequired},Rt.fragments={user:c`
    fragment ReviewUser on User {
      id
      public_reviews(first: 5) {
        edges {
          node {
            id
            public_feedback
            team {
              id
              name
              handle
            }
          }
        }
      }
    }
  `},w();var zt=({node:e,edge:t,style:n})=>(0,q.jsxs)(`div`,{className:`hacker-badge`,children:[(0,q.jsx)(`div`,{className:`hacker-badge-image`,children:(0,q.jsx)(`img`,{src:e.image_path,style:n})}),(0,q.jsxs)(H,{children:[(0,q.jsx)(`strong`,{children:e.name}),(0,q.jsx)(L,{children:Fe({date:t.awarded_at})})]}),(0,q.jsx)(`div`,{className:`hacker-badge-description`,children:e.description})]});zt.propTypes={node:K.default.object.isRequired,edge:K.default.object.isRequired,style:K.default.object};var Bt=({edge:e,style:t})=>{let{node:n}=e;return n.name===`Hack The Box Bounty Hunter`?(0,q.jsx)(F,{to:`https://academy.hackthebox.com/path/preview/bug-bounty-hunter?utm_source=partner&utm_medium=badge&utm_campaign=h1&utm_content=20211021-`,className:`badge-link-tile`,external:!0,newTab:!0,children:(0,q.jsx)(zt,{node:n,edge:e,style:t})}):(0,q.jsx)(zt,{node:n,edge:e,style:t})};Bt.propTypes={edge:K.default.object.isRequired,style:K.default.object};var Vt=class extends G.Component{filterBadges(e){return(0,Dt.default)(this.props.query?.user?.all_badges.edges,t=>t.node.category===e)}render(){let{username:e,query:t}=this.props,n=!t,r=this.filterBadges(window.constants.badges.categories.live_hacking_event),i=this.filterBadges(window.constants.badges.categories.platform_activity),a=this.filterBadges(window.constants.badges.categories.certification),o=this.filterBadges(window.constants.badges.categories.other);return(0,q.jsxs)(R,{children:[!J.default.empty(a)&&(0,q.jsx)(R.Row,{children:(0,q.jsx)(R.Column,{size:`one-whole`,children:(0,q.jsx)(H,{children:(0,q.jsxs)(P,{children:[(0,q.jsxs)(P.Heading,{children:[(0,q.jsx)(`strong`,{children:`Certifications`}),(0,q.jsxs)(L,{children:[a.length,` certifications`]})]}),(0,q.jsx)(P.Content,{children:(0,q.jsx)(R,{children:(0,q.jsx)(R.Row,{children:a.map(e=>(0,q.jsx)(R.Column,{size:`one-quarter`,children:(0,q.jsx)(H,{children:(0,q.jsx)(P,{children:(0,q.jsx)(P.Content,{children:(0,q.jsx)(Bt,{style:{height:`inherit`,width:`auto`},edge:e})})})})},e.node.id))})})})]})})})}),!J.default.empty(r)&&(0,q.jsx)(R.Row,{children:(0,q.jsx)(R.Column,{size:`one-whole`,children:(0,q.jsx)(H,{children:(0,q.jsxs)(P,{children:[(0,q.jsxs)(P.Heading,{children:[(0,q.jsx)(`strong`,{children:`Live Hacking Event Awards & Participation`}),(0,q.jsxs)(L,{children:[r.length,` total awards`]})]}),(0,q.jsx)(P.Content,{children:(0,q.jsx)(R,{children:(0,q.jsx)(R.Row,{children:r.map(e=>(0,q.jsx)(R.Column,{size:`one-quarter`,children:(0,q.jsx)(H,{children:(0,q.jsx)(P,{children:(0,q.jsx)(P.Content,{children:(0,q.jsx)(Bt,{style:{height:`inherit`,width:`auto`},edge:e})})})})},e.node.id))})})})]})})})}),!J.default.empty(o)&&(0,q.jsx)(R.Row,{children:(0,q.jsx)(R.Column,{size:`one-whole`,children:(0,q.jsx)(H,{children:(0,q.jsxs)(P,{children:[(0,q.jsxs)(P.Heading,{children:[(0,q.jsx)(`strong`,{children:`Other Badges`}),(0,q.jsxs)(L,{children:[o.length,` total awards`]})]}),(0,q.jsx)(P.Content,{children:(0,q.jsx)(R,{children:(0,q.jsx)(R.Row,{children:o.map(e=>(0,q.jsx)(R.Column,{size:`one-quarter`,children:(0,q.jsx)(H,{children:(0,q.jsx)(P,{children:(0,q.jsx)(P.Content,{children:(0,q.jsx)(Bt,{edge:e})})})})},e.node.id))})})})]})})})}),(0,q.jsx)(R.Row,{children:(0,q.jsx)(R.Column,{size:`one-whole`,children:(0,q.jsxs)(P,{children:[(0,q.jsxs)(P.Heading,{children:[(0,q.jsx)(`strong`,{children:`Platform Badges`}),(0,q.jsxs)(L,{children:[n?(0,q.jsx)(B,{inline:!0,width:10}):i.length,` `,`total badges`]})]}),(0,q.jsx)(P.Content,{children:(0,q.jsx)(R,{children:(0,q.jsx)(R.Row,{children:n?(0,q.jsx)(R.Column,{children:(0,q.jsx)(Be,{})}):J.default.empty(i)?(0,q.jsxs)(R.Column,{children:[e,` hasn't received any badges yet.`]}):i.map(e=>(0,q.jsx)(R.Column,{size:`one-quarter`,children:(0,q.jsx)(H,{children:(0,q.jsx)(P,{children:(0,q.jsx)(P.Content,{children:(0,q.jsx)(Bt,{edge:e})})})})},e.node.id))})})})]})})})]})}};Vt.propTypes={query:K.default.object,username:K.default.string.isRequired};var Ht=c`
  query UserBadgesQuery($username: String!) {
    me {
      id
      username
      ...UserProfileMe
      ...UserStatsMe
    }
    user(username: $username) {
      id
      username
      all_badges: badges(first: 100) {
        edges {
          awarded_at
          node {
            id
            name
            description
            image_path
            category
          }
        }
      }
      ...UserStatsUser
      ...UserProfileUser
      ...UserProfileCardUser
      ...CreditsUser
      ...ReviewUser
      ...BadgesUser
    }
  }
  ${_t.me}
  ${_t.user}
  ${yt.fragments.user}
  ${At.fragments.user}
  ${Rt.fragments.user}
  ${Pt.fragments.user}
  ${ot.fragments.me}
  ${ot.fragments.user}
`,Ut=({username:e})=>{let{data:t}=U(Ht,{variables:{username:e}});return(0,q.jsx)(Vt,{username:e,query:t})};Ut.propTypes={username:K.default.string.isRequired};var Wt=`/assets/static/hero_background-DrGVh_k-.png`,Gt=O(`
  query IdvClearQuery {
    me {
      id
      signal
      impact
      verified
      cleared
      user_identity {
        id
        rules_of_engagement_status
        meets_idv_one_valid_report_criteria
        __typename
      }
      total_earnings
    }
    id_verification {
      status
      url
      __typename
    }
    background_check {
      status
      url
      __typename
    }
    idVerificationTerms: terms(
      where: { name: { _eq: "id_verification" } }
      order_by: { created_at: { _direction: DESC } }
      first: 1
    ) {
      edges {
        node {
          copy
        }
      }
    }
    backgroundCheckTerms: terms(
      where: { name: { _eq: "background_check" } }
      order_by: { created_at: { _direction: DESC } }
      first: 1
    ) {
      edges {
        node {
          copy
        }
      }
    }
    __typename
  }
`),Kt=({requirement:e})=>(0,q.jsxs)(`div`,{className:`inline-flex gap-xs align-middle h-min items-center`,children:[(0,q.jsx)(`div`,{"data-testid":e.checked?`requirement-checked`:`requirement-unchecked`,className:e.checked?`text-green-300`:`text-neutral-600`,children:(0,q.jsx)(S,{src:$e,size:T.Large,scale:.75})}),(0,q.jsx)(`span`,{className:`text-md align-middle`,children:e.label})]}),qt=function(e){return e.Checked=`checked`,e.Hidden=`hidden`,e}({}),Jt=({variation:e})=>(0,q.jsx)(`div`,{className:(0,Y.default)(`flex justify-center h-spacing-32 w-spacing-32 lg:h-spacing-48 lg:w-spacing-48 rounded-full border-2 border-solid border-blue-400`,{invisible:e===`hidden`}),children:(0,q.jsx)(`span`,{className:`leading-[26px] lg:leading-[42px] text-2xl lg:text-3xl text-blue-400`,children:(0,q.jsx)(S,{src:qe})})}),Yt=({iconSrc:e,title:t,children:n,requirements:r,button:i,completed:a,duration:o})=>(0,q.jsxs)(`div`,{className:`md:flex`,children:[(0,q.jsx)(`div`,{className:`pr-spacing-32 hidden md:flex md:flex-col`,children:(0,q.jsx)(Jt,{variation:a?qt.Checked:qt.Hidden})}),(0,q.jsxs)(`div`,{className:`w-full -mt-spacing-4 pb-[110px]`,children:[(0,q.jsx)(`h1`,{className:(0,Y.default)(`text-3xl m-0 font-normal text-center md:text-start`,a?`text-blue-400`:`text-neutral-50 dark:text-white`),children:t}),(0,q.jsxs)(`div`,{className:`md:flex flex-row-reverse`,children:[(0,q.jsx)(`div`,{className:`flex justify-center md:justify-end md:w-full pb-spacing-24 md:pb-0`,children:(0,q.jsx)(`div`,{className:`w-1/2 md:w-10/12`,children:(0,q.jsx)(`img`,{src:e})})}),(0,q.jsxs)(`div`,{className:`w-full flex flex-col md:block`,children:[(0,q.jsxs)(`div`,{className:`w-full w-1/2`,children:[(0,q.jsxs)(`div`,{className:`pb-spacing-16 md:pb-spacing-32 lg:pb-spacing-40`,children:[(0,q.jsx)(f,{vertical:`8`}),(0,q.jsx)(`p`,{className:`font-normal text-md lg:text-xl`,children:n})]}),r&&r.length>0&&(0,q.jsxs)(`div`,{className:`flex flex-col pb-spacing-16 md:pb-spacing-32 lg:pb-spacing-40`,children:[(0,q.jsx)(`h2`,{className:`font-normal text-xl`,children:`Requirements`}),(0,q.jsx)(f,{vertical:`8`}),r.map(e=>(0,q.jsx)(Kt,{requirement:e},e.label))]})]}),(0,q.jsx)(m,{color:ee.Gray,children:o}),(0,q.jsx)(f,{vertical:`16`}),i]})]})]})]},t),Xt=`/assets/static/roe_icon_dark-JsvZxLks.png`,Zt=`/assets/static/roe_icon-C53t-Vc4.png`,Qt=({loading:e,completed:t})=>{let{isDarkModeEnabled:n}=j();return(0,q.jsx)(Yt,{iconSrc:n?Xt:Zt,title:`Rules of Engagement`,button:(0,q.jsx)(pt,{disabled:e,completed:t}),completed:t,duration:`5 minutes`,children:(0,q.jsxs)(q.Fragment,{children:[`Hackers participating in Clear or ID Verified Programs often get increased levels of internal access, credentials or additional parameters. This document describes the`,` `,(0,q.jsx)(`a`,{href:`https://www.hackerone.com/policies/clear-rules-of-engagement`,target:`_blank`,rel:`noopener noreferrer`,children:`Rules of Engagement and Additional Terms`}),` `,`for being part of HackerOne Clear/ID Verified and participating in these programs.`]})})},$t=`/assets/static/idv_form_dark-DjkokGVc.png`,en=`/assets/static/idv_form-CeX2Adh8.png`,tn=()=>(0,q.jsxs)(`div`,{className:`flex gap-xs text-green-300`,children:[(0,q.jsx)(S,{src:ke,size:T.Large}),(0,q.jsx)(`div`,{children:`Your identity is verified`})]}),nn=`data:image/svg+xml,%3csvg%20xmlns='http://www.w3.org/2000/svg'%20width='24'%20height='24'%20viewBox='0%200%2024%2024'%3e%3cpath%20d='M13.89%208.7L12%2010.59L10.11%208.7a.996.996%200%201%200-1.41%201.41L10.59%2012L8.7%2013.89a.996.996%200%201%200%201.41%201.41L12%2013.41l1.89%201.89a.996.996%200%201%200%201.41-1.41L13.41%2012l1.89-1.89a.996.996%200%200%200%200-1.41c-.39-.38-1.03-.38-1.41%200zM12%202C6.47%202%202%206.47%202%2012s4.47%2010%2010%2010s10-4.47%2010-10S17.53%202%2012%202zm0%2018c-4.41%200-8-3.59-8-8s3.59-8%208-8s8%203.59%208%208s-3.59%208-8%208z'/%3e%3c/svg%3e`,rn=()=>(0,q.jsxs)(`div`,{className:`flex gap-xs text-red-400`,children:[(0,q.jsx)(S,{src:nn,size:T.Large}),(0,q.jsx)(`div`,{children:`We couldn’t verify your identity. You have one more attempt.`})]}),an=()=>(0,q.jsxs)(`div`,{className:`flex gap-xs text-red-400`,children:[(0,q.jsx)(S,{src:nn,size:T.Large}),(0,q.jsx)(`div`,{children:`We couldn’t verify your identity and you have no more attempts. Please wait 30 days before applying again.`})]}),on=`data:image/svg+xml,%3csvg%20xmlns='http://www.w3.org/2000/svg'%20width='24'%20height='24'%20viewBox='0%200%2024%2024'%3e%3cpath%20d='M11.99%202C6.47%202%202%206.48%202%2012s4.47%2010%209.99%2010C17.52%2022%2022%2017.52%2022%2012S17.52%202%2011.99%202zM12%2020c-4.42%200-8-3.58-8-8s3.58-8%208-8s8%203.58%208%208s-3.58%208-8%208zm-.22-13h-.06c-.4%200-.72.32-.72.72v4.72c0%20.35.18.68.49.86l4.15%202.49c.34.2.78.1.98-.24a.71.71%200%200%200-.25-.99l-3.87-2.3V7.72c0-.4-.32-.72-.72-.72z'/%3e%3c/svg%3e`,sn=()=>(0,q.jsxs)(`div`,{className:`flex gap-xs text-neutral-300 dark:text-white`,children:[(0,q.jsx)(S,{src:on,size:T.Large}),(0,q.jsx)(`div`,{className:`flex flex-wrap content-center`,children:`Processing your info. This typically takes 7 days. We will email you when we are finished.`})]}),cn=()=>(0,q.jsx)(d,{contentPrimary:`Your ID Verification will expire soon`,contentSecondary:`Please renew your ID Verification as soon as possible to ensure that you keep your access to ID Verification programs and privileges.`,variation:r.Warning});function ln(){return(0,q.jsx)(d,{contentPrimary:`You can skip the "One valid report submission" requirement`,contentSecondary:`A program has vouched for you! That's why you can skip this requirement for ID Verification. You must still sign the Rules of Engagement above.`,variation:r.Success})}var un=({status:e,resumeUrl:t,terms:r,roeCompleted:i})=>{let[a,o]=(0,G.useState)(!1),[s,c]=(0,G.useState)(!1),l=async()=>{if(t)window.location.href=t;else{o(!0);try{let e=await mt();window.location.href=e}catch{N(`error`,`Something went wrong while starting the identity verification application. Please retry and check your e-mail inbox for a confirmation e-mail. If this problem persists, contact us via ${window.constants.notification.support_link}`)}finally{o(!1)}}},u=!0,d=(0,q.jsx)(q.Fragment,{});switch(e){case k.NotEligible:break;case k.Success:d=(0,q.jsx)(tn,{});break;case k.Failed:u=!1,d=(0,q.jsx)(rn,{});break;case k.Blocked:d=(0,q.jsx)(an,{});break;case k.Processing:d=(0,q.jsx)(sn,{});break;case k.RenewalEligible:u=!1,d=(0,q.jsx)(cn,{});break;case k.Vouched:u=!i,d=(0,q.jsx)(ln,{});break;case k.Eligible:default:u=!1;break}return(0,q.jsxs)(`div`,{className:`font-normal text-md`,children:[(0,q.jsx)(ft,{showModal:s,isStartingIdVerification:a,handleButtonClick:()=>{l()},handleCloseModal:()=>{c(!1)},terms:r,"data-testid":`id-verification-welcome-modal`}),(0,q.jsxs)(`div`,{className:`flex flex-col gap-xs`,children:[(0,q.jsx)(h,{renderAs:ue.Button,type:n.Button,onClick:()=>{c(!0)},disabled:u,children:(0,q.jsx)(`span`,{className:`dark:text-white`,children:`Start Verification`})}),(0,q.jsx)(`div`,{className:`flex justify-center md:justify-start`,children:d})]})]})},dn=({completed:e,status:t,url:n,requirements:r,terms:i,roeCompleted:a})=>{let{isDarkModeEnabled:o}=j();return(0,q.jsx)(Yt,{iconSrc:o?$t:en,title:`ID Verification`,button:(0,q.jsx)(un,{status:t,resumeUrl:n,terms:i,roeCompleted:a}),completed:e,duration:`5 minutes`,requirements:r,children:`Become an ID verified hacker today. Gain access to more exclusive programs.`})},fn=`/assets/static/clear_form-Dd8t3YKs.png`,pn=`/assets/static/clear_form_dark-CK8M8GZF.png`,mn=(0,a().getData)().filter(e=>![`AF`,`DJ`,`PF`,`GG`,`HK`,`IR`,`IM`,`IL`,`JE`,`LA`,`MO`,`YT`,`SL`,`SY`].includes(e.code)).map(e=>({label:e.name,value:e.code})),hn=gt.map(e=>({label:e.name,value:e.code})),gn=({workLocation:e,setWorkLocation:t,setSelectedCountryCode:n,setSelectedStateCode:r})=>(0,q.jsxs)(`div`,{className:`px-spacing-4`,children:[(0,q.jsx)(`h1`,{children:`Start your background check process`}),(0,q.jsx)(v,{variation:y.Light}),(0,q.jsx)(f,{vertical:`32`}),(0,q.jsx)(l,{label:`Where are you located?`,options:[{id:`usa`,label:`USA`},{id:`other`,label:`Other countries`}],value:e??``,onChange:e=>{t(e)}}),e===`usa`&&(0,q.jsxs)(`div`,{className:`pb-[130px]`,onClick:e=>{e.stopPropagation()},children:[(0,q.jsx)(f,{vertical:`32`}),(0,q.jsx)(`p`,{className:`font-bold text-black`,children:`Select your state`}),(0,q.jsx)(ye,{maxMenuHeight:230,options:hn,onChange:e=>{r(e.value)}})]}),e===`other`&&(0,q.jsxs)(`div`,{className:`pb-[130px]`,onClick:e=>{e.stopPropagation()},children:[(0,q.jsx)(f,{vertical:`32`}),(0,q.jsx)(`p`,{className:`font-bold text-black`,children:`Select your country`}),(0,q.jsx)(ye,{maxMenuHeight:230,options:mn,onChange:e=>{n(e.value)}}),(0,q.jsx)(f,{vertical:`32`}),(0,q.jsx)(d,{contentPrimary:`Users from the following countries can not start a background check:
            Afghanistan, Djibouti, French Polynesia, Guernsey, Hong Kong, Iran,
            Isle of Man, Israel, Jersey, Lao People's Democratic Republic,
            Macao, Mayotte, Sierra Leone and Syrian Arab Republic`})]})]}),_n=({status:e,url:t})=>(0,q.jsxs)(q.Fragment,{children:[e===A.Failed&&(0,q.jsxs)(`div`,{className:`flex gap-xs text-red-400`,children:[(0,q.jsx)(S,{src:`data:image/svg+xml,%3csvg%20xmlns='http://www.w3.org/2000/svg'%20width='24'%20height='24'%20viewBox='0%200%2024%2024'%3e%3cpath%20d='M13.89%208.7L12%2010.59L10.11%208.7a.996.996%200%201%200-1.41%201.41L10.59%2012L8.7%2013.89a.996.996%200%201%200%201.41%201.41L12%2013.41l1.89%201.89a.996.996%200%201%200%201.41-1.41L13.41%2012l1.89-1.89a.996.996%200%200%200%200-1.41c-.39-.38-1.03-.38-1.41%200zM12%202C6.47%202%202%206.47%202%2012s4.47%2010%2010%2010s10-4.47%2010-10S17.53%202%2012%202zm0%2018c-4.41%200-8-3.59-8-8s3.59-8%208-8s8%203.59%208%208s-3.59%208-8%208z'/%3e%3c/svg%3e`,size:T.Large}),(0,q.jsxs)(`p`,{children:[`Your background check was rejected.`,t&&(0,q.jsxs)(q.Fragment,{children:[` `,`You can review your results `,(0,q.jsx)(`a`,{href:t,children:`here`}),`.`]})]})]}),e===A.InProgress&&(0,q.jsxs)(`div`,{className:`flex gap-xs`,children:[(0,q.jsx)(S,{src:`data:image/svg+xml,%3csvg%20xmlns='http://www.w3.org/2000/svg'%20width='24'%20height='24'%20viewBox='0%200%2024%2024'%3e%3cpath%20d='M11%207h2v2h-2zm0%204h2v6h-2zm1-9C6.48%202%202%206.48%202%2012s4.48%2010%2010%2010s10-4.48%2010-10S17.52%202%2012%202zm0%2018c-4.41%200-8-3.59-8-8s3.59-8%208-8s8%203.59%208%208s-3.59%208-8%208z'/%3e%3c/svg%3e`,size:T.Large}),(0,q.jsxs)(`p`,{children:[`Your background check is in progress.`,t&&(0,q.jsxs)(q.Fragment,{children:[` `,`Please complete it `,(0,q.jsx)(`a`,{href:t,children:`here.`})]}),` `,`If you've completed it, we'll reach out to you with the final result soon.`]})]}),e===A.Processing&&(0,q.jsxs)(`div`,{className:`flex gap-xs`,children:[(0,q.jsx)(S,{src:`data:image/svg+xml,%3csvg%20xmlns='http://www.w3.org/2000/svg'%20width='24'%20height='24'%20viewBox='0%200%2024%2024'%3e%3cpath%20d='M11%207h2v2h-2zm0%204h2v6h-2zm1-9C6.48%202%202%206.48%202%2012s4.48%2010%2010%2010s10-4.48%2010-10S17.52%202%2012%202zm0%2018c-4.41%200-8-3.59-8-8s3.59-8%208-8s8%203.59%208%208s-3.59%208-8%208z'/%3e%3c/svg%3e`,size:T.Large}),(0,q.jsxs)(`p`,{children:[`Your background check is being processed.`,t&&(0,q.jsxs)(q.Fragment,{children:[` `,`You can track its status `,(0,q.jsx)(`a`,{href:t,children:`here.`})]})]})]}),e===A.Vouched&&(0,q.jsx)(d,{contentPrimary:`You can skip the signal, impact and bounty requirements`,contentSecondary:`A program has vouched for you! That's why you can skip these requirements for a background check. You must still sign the Rules of Engagement and complete ID Verification above.`,variation:r.Success}),e===A.RenewalEligible&&(0,q.jsx)(d,{contentPrimary:`Your Background Check will expire soon`,contentSecondary:`Please renew your Background Check as soon as possible to ensure that you keep your access to Clear programs and privileges.`,variation:r.Warning}),e===A.Success&&(0,q.jsxs)(`div`,{className:`flex gap-xs text-green-300`,children:[(0,q.jsx)(S,{src:`data:image/svg+xml,%3csvg%20xmlns='http://www.w3.org/2000/svg'%20width='24'%20height='24'%20viewBox='0%200%2024%2024'%3e%3cpath%20d='M12%202C6.48%202%202%206.48%202%2012s4.48%2010%2010%2010s10-4.48%2010-10S17.52%202%2012%202zm0%2018c-4.41%200-8-3.59-8-8s3.59-8%208-8s8%203.59%208%208s-3.59%208-8%208zm4.59-12.42L10%2014.17l-2.59-2.58L6%2013l4%204l8-8z'/%3e%3c/svg%3e`,size:T.Large}),(0,q.jsx)(`p`,{children:`Your background is checked.`})]})]}),X={WORK_LOCATION_SELECTOR:`work_location_selector`,TERMS:`terms`},vn=({disabled:e,status:t,terms:n,url:r})=>{let{isDarkModeEnabled:i}=j(),[a,o]=(0,G.useState)(!1),[s,c]=(0,G.useState)(!1),[l,u]=(0,G.useState)(X.WORK_LOCATION_SELECTOR),[d,ee]=(0,G.useState)(``),[p,m]=(0,G.useState)(``),[te,ne]=(0,G.useState)(``),g=`Something went wrong while starting the background check application. Please retry and check your e-mail inbox for a confirmation e-mail. If this problem persists, contact us via ${window.constants.notification.support_link}`,[re,{loading:ie}]=_(ht,{variables:{input:{country:p===``?`US`:p,state:p===``?te:null}},onCompleted:({startBackgroundCheck:{was_successful:e,url:t}})=>{e&&t?window.location.href=t:N(`error`,g)},onError:()=>{N(`error`,g)}}),ae=()=>{o(!1)},oe=()=>{re()},se=p!==``!=(te!==``),ce=s&&se;return(0,q.jsxs)(E,{children:[(0,q.jsxs)(`div`,{className:`flex flex-col gap-xs`,children:[(0,q.jsx)(h,{disabled:e,onClick:()=>{o(!0)},children:`Start Clear process`}),(0,q.jsx)(_n,{status:t,url:r})]}),(0,q.jsxs)(I,{shouldCloseOnEsc:!0,showModal:a,size:`large`,handleCloseModal:ae,scrollableContent:!0,className:`over`,children:[l===X.WORK_LOCATION_SELECTOR?(0,q.jsx)(gn,{workLocation:d,setWorkLocation:e=>{m(``),ne(``),ee(e)},setSelectedCountryCode:m,setSelectedStateCode:ne}):(0,q.jsxs)(q.Fragment,{children:[(0,q.jsx)(`h1`,{children:`Know more about Background Check`}),(0,q.jsx)(v,{variation:y.Light}),(0,q.jsx)(f,{vertical:`32`}),(0,q.jsx)(`div`,{className:`flex justify-center`,children:(0,q.jsx)(`img`,{className:`w-1/3`,alt:`Background Check image`,src:i?pn:fn})}),(0,q.jsxs)(`div`,{children:[(0,q.jsx)(f,{vertical:`28`}),(0,q.jsxs)(`div`,{className:`flex`,children:[(0,q.jsx)(`span`,{className:`mr-sm align-text-top`,children:(0,q.jsx)(S,{src:Ie,size:T.ExtraLarge})}),(0,q.jsx)(`h1`,{className:`text-2xl lg:text-3xl`,children:`Clear - Background Check`})]}),(0,q.jsx)(f,{vertical:`16`}),(0,q.jsx)(`p`,{children:`Congrats on meeting all of the performance requirements to be eligible for background checks. Now it is time to start the background check process.`})]}),(0,q.jsx)(f,{vertical:`16`}),(0,q.jsxs)(`div`,{children:[(0,q.jsx)(`strong`,{children:`What is Background checked?`}),(0,q.jsx)(`p`,{children:`The background check is essentially a process of using the information provided by a Community Member during the ID verification process and potentially additional documentation provided by the Community member during the background check process to complete a criminal background check, covering a 7 year history.`}),(0,q.jsx)(f,{vertical:`16`}),(0,q.jsxs)(`p`,{children:[`HackerOne partners with `,(0,q.jsx)(`strong`,{children:`Checkr`}),` to conduct all global criminal background checks. For all countries, the maximum criminal background check allowed by law is performed. Countries where it’s illegal to perform criminal background checks, unfortunately, won’t be eligible to participate in the background check process.`]})]}),(0,q.jsx)(f,{vertical:`16`}),(0,q.jsxs)(`div`,{children:[(0,q.jsxs)(`p`,{children:[`The process time depends on the countries that need to be checked for your criminal background history. Some examples of average completion times are:`,` `]}),(0,q.jsx)(`strong`,{children:`How long does it take?`}),(0,q.jsxs)(`ul`,{className:`list-disc ml-md`,children:[(0,q.jsx)(`li`,{children:`United States - 4 business days`}),(0,q.jsx)(`li`,{children:`India - 7 to 8 business days`}),(0,q.jsx)(`li`,{children:`Argentina - 5 to 6 business days`}),(0,q.jsx)(`li`,{children:`United Kingdom - 11 to 12 business days`}),(0,q.jsx)(`li`,{children:`Pakistan - 7 to 8 business days`})]}),(0,q.jsx)(f,{vertical:`16`}),`You will be informed of your background check status on the platform.`]}),(0,q.jsx)(f,{vertical:`16`}),(0,q.jsxs)(`div`,{children:[(0,q.jsx)(`strong`,{children:`What do I gain from being a Background checked?`}),(0,q.jsx)(`p`,{children:`Being background checked gives you access to exclusive programs.`})]}),(0,q.jsx)(dt,{terms:n,signed:s,sign:()=>{c(!s)}})]}),(0,q.jsx)(f,{vertical:`40`}),(0,q.jsx)(v,{variation:y.Light}),(0,q.jsx)(f,{vertical:`16`}),(0,q.jsxs)(`div`,{className:`flex justify-end gap-spacing-16`,children:[l===X.TERMS&&(0,q.jsx)(h,{variation:D.Secondary,onClick:()=>{u(X.WORK_LOCATION_SELECTOR)},children:`Back`}),(0,q.jsx)(h,{variation:D.Secondary,onClick:ae,children:`Cancel`}),l===X.WORK_LOCATION_SELECTOR&&(0,q.jsx)(h,{disabled:!se,onClick:()=>{u(X.TERMS)},children:`Next`}),l===X.TERMS&&(0,q.jsx)(h,{disabled:!ce||ie,onClick:()=>{oe()},children:`Start the process`})]})]})]})},yn=({loading:e,status:t,url:n,requirements:r,terms:i,roeCompleted:a,idvCompleted:o,submissionsAllowedWithoutCheck:s=!1})=>{let{isDarkModeEnabled:c}=j();return(0,q.jsx)(Yt,{iconSrc:c?pn:fn,title:`Background Check`,button:(0,q.jsx)(vn,{disabled:e||!(t===A.Eligible||t===A.RenewalEligible||t===A.Vouched&&a&&o),status:t,url:n,terms:i}),completed:t===A.Success,duration:`1-2 weeks`,requirements:r,children:(0,q.jsxs)(q.Fragment,{children:[`Become a cleared hacker today. Gain access to high-value programs with better rewards and quicker response times.`,s&&(0,q.jsx)(`span`,{className:`block mt-spacing-16`,children:`You can submit reports without a background check. Background checks are only required if you want access to programs that require HackerOne Clear.`})]})})},bn=4,xn=15,Sn=15e3,{IDV_REQUIRED_ON_BBP_SUBMISSION:Cn}=window.constants.featureToggles,wn=()=>{let{data:e,loading:t}=ie(Gt),{enabled:n}=Xe(Cn),r=e?.me?.user_identity?.rules_of_engagement_status===Ae.RulesOfEngagementSigned,i=e?.me?.verified===!0,a=[{label:`Sign the Rules of Engagement`,checked:r},...n?[]:[{label:`One valid report submission`,checked:!!e?.me?.user_identity?.meets_idv_one_valid_report_criteria}]],o=[{label:`Sign the Rules of Engagement`,checked:r},{label:`Be ID verified`,checked:i},{label:`Be over 18 years old`,checked:e?.me?.verified===!0},{label:`Lifetime signal of 4`,checked:e?.me?.signal?e?.me?.signal>=bn:!1},{label:`Lifetime impact of 15`,checked:e?.me?.impact?e?.me?.impact>=xn:!1},{label:`Lifetime earnings of 15000`,checked:e?.me?.total_earnings?e?.me?.total_earnings>=Sn:!1}];return(0,q.jsx)(`div`,{className:`flex justify-center w-full`,children:(0,q.jsx)(`div`,{className:`daisy-grid--has-outside-gutter pb-spacing-24`,children:(0,q.jsx)(E,{children:(0,q.jsxs)(ce,{fill:!0,children:[(0,q.jsx)(x,{edgeToEdge:!0,children:(0,q.jsx)(`div`,{className:`p-lg bg-neutral-900 dark:bg-neutral-50`,children:`Learn more about ID Verification and Clear processes`})}),!n&&(0,q.jsx)(`div`,{className:`pb-spacing-16`,children:(0,q.jsx)(x,{edgeToEdge:!0,children:(0,q.jsx)(`div`,{className:`lg:px-xl bg-center bg-black bg-cover`,style:{backgroundImage:`url(/assets/static/hero_background-DrGVh_k-.png)`},children:(0,q.jsxs)(`div`,{className:`flex flex-col-reverse gap-xl md:gap-0 md:grid md:grid-rows-1 md:grid-cols-5 p-2xl md:p-xl lg:py-2xl lg:px-spacing-80`,children:[(0,q.jsxs)(`div`,{className:`flex flex-col text-white font-normal gap-lg md:col-span-2`,children:[(0,q.jsx)(`h1`,{className:`text-[32px] lg:text-5xl m-0`,children:`Maximize the benefits of our verification process today.`}),(0,q.jsx)(`p`,{className:`text-[16px] lg:text-xl m-0`,children:`Discover how to join our Verified or Clear Teams today and enhance your program-matching benefits.`})]}),(0,q.jsx)(`img`,{src:`/assets/static/hero_image-BJZiG4WS.png`,className:`aspect-[1/1] object-contain max-h-fit px-spacing-64 md:px-0 md:col-start-4 md:col-span-2 hidden md:block`})]})})})}),(0,q.jsxs)(x,{children:[n&&(0,q.jsxs)(`div`,{className:`md:flex`,children:[(0,q.jsx)(`div`,{className:`pr-spacing-32 hidden md:flex md:flex-col`,children:(0,q.jsx)(Jt,{variation:qt.Hidden})}),(0,q.jsxs)(`div`,{className:`w-full -mt-spacing-4 pb-spacing-40`,children:[(0,q.jsx)(`h1`,{className:`text-3xl m-0 font-normal text-neutral-50 dark:text-white`,children:`Getting ID verified`}),(0,q.jsx)(f,{vertical:`8`}),(0,q.jsx)(`p`,{className:`font-normal text-md lg:text-xl`,children:`Rules of Engagement and ID Verification are both required to become ID verified. You'll need to be ID verified to submit reports to bug bounty programs. Vulnerability disclosure programs aren't changing; they stay open with no verification required.`}),(0,q.jsx)(`p`,{className:`font-normal text-md lg:text-xl`,children:`Verification is free and takes a few minutes. It's handled by a third-party identity partner, your details aren't shared with programs, and your public handle doesn't change. It renews once a year.`}),(0,q.jsx)(`p`,{className:`font-normal text-md lg:text-xl`,children:`Once you've built a track record on the platform and meet the requirements, you'll be eligible for HackerOne Clear, which additionally requires a background check.`})]})]}),(0,q.jsx)(Qt,{loading:t,completed:r}),(0,q.jsx)(dn,{completed:e?.me?.verified===!0,status:e?.id_verification?.status??k.NotEligible,url:e?.id_verification?.url??``,requirements:a,terms:e?.idVerificationTerms?.edges?.[0]?.node?.copy,roeCompleted:r}),n&&(0,q.jsxs)(`div`,{className:`md:flex`,children:[(0,q.jsx)(`div`,{className:`pr-spacing-32 hidden md:flex md:flex-col`,children:(0,q.jsx)(Jt,{variation:qt.Hidden})}),(0,q.jsx)(`div`,{className:`w-full pb-spacing-40`,children:(0,q.jsx)(v,{variation:y.Light,testId:`clearances-background-check-divider`})})]}),(0,q.jsx)(yn,{loading:t,requirements:o,submissionsAllowedWithoutCheck:!!n,status:e?.background_check?.status??A.NotEligible,url:e?.background_check?.url??``,terms:e?.backgroundCheckTerms?.edges?.[0]?.node?.copy,roeCompleted:r,idvCompleted:i})]})]})})})})},Tn=`/assets/static/hero_image-DmAC6fwH.png`,En=`/assets/static/citizenship_icon-CVJrA3h7.png`,Dn=`/assets/static/citizenship_icon_dark-IzPBf7rF.png`,On=O(`
  mutation InvalidateCitizenshipVerificationMutation(
    $input: InvalidateCitizenshipVerificationInput!
  ) {
    invalidateCitizenshipVerification(input: $input) {
      was_successful
      user_identity {
        id
        citizenship_verifications {
          nodes {
            id
            __typename
          }
        }
        __typename
      }
      errors {
        edges {
          node {
            id
            field
            type
            message
          }
        }
      }
    }
  }
`),kn=({citizenshipVerification:e})=>{let[t,n]=(0,G.useState)(!1),[r,{loading:i}]=_(On,{onError:W,onCompleted:({invalidateCitizenshipVerification:e})=>{if(e.was_successful)N(`notice`,`Citizenship verification deleted`);else throw N(`error`,`Could not delete citizenship verification, please try again later`),new M(e.errors)}}),a=async()=>{await r({variables:{input:{citizenship_verification_id:e.id}}})};return(0,q.jsxs)(q.Fragment,{children:[(0,q.jsxs)(`div`,{className:`flex flex-row items-center gap-xs`,children:[(0,q.jsx)(`div`,{className:`rounded-full bg-blue-950 aspect-1 w-[40px] flex justify-center align-center overflow-hidden`,children:(0,q.jsx)(`img`,{src:`https://flagcdn.com/${e.country_code.toLowerCase()}.svg`,className:`object-cover w-full h-full`})}),(0,q.jsxs)(E,{size:C.Scale500,children:[`Your `,e.nationality,` citizenship has been verified`]}),(0,q.jsx)(`div`,{className:`ml-auto`,children:(0,q.jsx)(h,{onClick:()=>{n(e=>!e)},disabled:i,iconOnly:!0,icons:{center:{src:se,accessibilityLabel:`Delete ${e.nationality} citizenship`}},variation:D.GhostSecondary})})]}),(0,q.jsxs)(I,{title:`Delete ${e.nationality} citizenship`,shouldCloseOnEsc:!0,shouldCloseOnOverlayClick:!0,showModal:t,size:`medium`,handleCloseModal:()=>{n(e=>!e)},children:[(0,q.jsx)(v,{variation:y.Light}),(0,q.jsx)(E,{children:`Are you sure you want to delete your citizenship verification? This step is irreversible. To add the citizenship again, you must go through the process again.`}),(0,q.jsx)(v,{variation:y.Light}),(0,q.jsxs)(`div`,{className:`flex justify-end gap-md`,children:[(0,q.jsx)(h,{variation:D.Tertiary,onClick:()=>{n(e=>!e)},small:!0,children:`Cancel`}),(0,q.jsx)(h,{variation:D.Danger,onClick:()=>{a()},small:!0,children:`Delete citizenship`})]})]})]})},An=`/assets/static/citizenship_modal_icon-CZ3u6-Qp.png`,jn=`/assets/static/citizenship_modal_icon_dark-DVAej52S.png`;w();var Mn=c`
  mutation StartCitizenshipVerification(
    $input: StartCitizenshipVerificationInput!
  ) {
    startCitizenshipVerification(input: $input) {
      url
      was_successful
      errors {
        edges {
          node {
            id
            message
            type
          }
        }
      }
    }
  }
`,Nn=({activeVerificationUrl:e,terms:t,disabled:n})=>{let{isDarkModeEnabled:i}=j(),[a,o]=(0,G.useState)(!1),[s,c]=(0,G.useState)(!1),[l]=_(Mn,{onCompleted:({startCitizenshipVerification:{url:e,was_successful:t,errors:n}})=>{if(t)window.location.href=e;else throw u(),new M(n)},onError:()=>{u()}}),u=()=>{N(`error`,`Could not start citizenship verification, please try again later`)},ee=async()=>{await l({variables:{input:{}}})},p=()=>{e?window.location.href=e:ee()},m=()=>{o(!1)};return(0,q.jsxs)(E,{children:[n&&(0,q.jsxs)(`div`,{children:[(0,q.jsx)(`p`,{className:`text-red-400 text-sm`,children:`You have reached your limit for requesting citizenship verifications.`}),(0,q.jsx)(f,{vertical:`4`})]}),(0,q.jsx)(h,{testId:`open-modal`,disabled:n,onClick:()=>{o(!0)},children:`Add citizenship`}),(0,q.jsxs)(I,{title:`Welcome to Citizenship verification`,shouldCloseOnEsc:!0,showModal:a,size:`large`,handleCloseModal:m,children:[(0,q.jsx)(v,{variation:y.Light}),(0,q.jsx)(d,{contentPrimary:`Please ensure submitted documents contain your nationality`,contentSecondary:`Your citizenship can only be verified if the provided document contains your nationality. Your application will be rejected if you provide a document that does not contain your nationality.`,variation:r.Warning}),(0,q.jsx)(f,{vertical:`32`}),(0,q.jsx)(`div`,{className:`flex justify-center`,children:(0,q.jsx)(`img`,{alt:`Citizenship image`,src:i?jn:An})}),(0,q.jsxs)(`div`,{children:[(0,q.jsx)(f,{vertical:`16`}),(0,q.jsx)(`h1`,{className:`text-2xl lg:text-3xl`,children:`Citizenship general information`})]}),(0,q.jsxs)(`div`,{children:[(0,q.jsx)(`strong`,{children:`How does it work?`}),(0,q.jsx)(`p`,{children:`For access to select private programs, you must verify your country of citizenship. If you have more than one country of citizenship, complete the process for each country of citizenship.`})]}),(0,q.jsxs)(`div`,{children:[(0,q.jsx)(`strong`,{children:`What is Citizenship?`}),(0,q.jsx)(`p`,{children:`Citizenship means having formal membership of a state/country, providing entitlement to hold a country's passport.`})]}),(0,q.jsxs)(`div`,{children:[(0,q.jsx)(`strong`,{children:`What do you need to get it done?`}),(0,q.jsxs)(`ul`,{className:`list-disc ml-md`,children:[(0,q.jsx)(`li`,{children:`Have your ID which shows your citizenship ready (Passport or Identity Card)`}),(0,q.jsx)(`li`,{children:`Capture the ID image`}),(0,q.jsx)(`li`,{children:`Take a selfie (use a good quality webcam or phone camera)`})]}),(0,q.jsx)(`p`,{children:`Don't have an ID with your country of citizenship? Tell us about the country/ies to which you have citizenship. You can validate them at a later date.`})]}),(0,q.jsxs)(`div`,{children:[(0,q.jsx)(`strong`,{children:`How long does it take?`}),(0,q.jsx)(`p`,{children:`The whole process might take between 2-5 minutes. You will be informed of your status on the platform.`})]}),(0,q.jsx)(dt,{terms:t,signed:s,sign:()=>{c(!s)}}),(0,q.jsx)(f,{vertical:`40`}),(0,q.jsx)(v,{variation:y.Light}),(0,q.jsx)(f,{vertical:`16`}),(0,q.jsxs)(`div`,{className:`flex justify-end`,children:[(0,q.jsx)(h,{variation:D.Tertiary,onClick:m,children:`Cancel`}),(0,q.jsx)(f,{horizontal:`16`}),(0,q.jsx)(h,{disabled:!s,onClick:()=>{p()},children:`Start the process`})]})]})]})},Pn=O(`
  mutation SaveUnverifiableResidency(
    $input: SaveUnverifiableResidencyVerificationInput!
  ) {
    saveUnverifiableResidency(input: $input) {
      was_successful
      user_identity {
        id
        has_unverifiable_residency
        __typename
      }
      errors {
        edges {
          node {
            id
            message
            type
          }
        }
      }
    }
  }
`),Fn=O(`
  mutation SaveUnverifiableCitizenship(
    $input: SaveUnverifiableCitizenshipVerificationInput!
  ) {
    saveUnverifiableCitizenship(input: $input) {
      was_successful
      user_identity {
        id
        has_unverifiable_citizenship
        __typename
      }
      errors {
        edges {
          node {
            id
            message
            type
          }
        }
      }
    }
  }
`),In=({hasUnverifiableCitizenship:e})=>{let[t,n]=(0,G.useState)(!1),[r,i]=(0,G.useState)(e),[a]=_(Fn,{onCompleted:({saveUnverifiableCitizenship:{was_successful:e,errors:t}})=>{if(e)N(`notice`,`Information about non-verifiable citizenship saved`),o();else throw W(),new M(t)},onError:W}),o=()=>{n(!1)},s=async()=>{await a({variables:{input:{has_unverifiable_citizenship:r}}})};return(0,G.useEffect)(()=>{i(e)},[e]),(0,q.jsxs)(q.Fragment,{children:[(0,q.jsxs)(E,{size:C.Scale200,variation:b.Subtle,children:[`If you can’t verify your citizenship add the information`,` `,(0,q.jsx)(`span`,{onClick:()=>{n(!0)},className:`text-blue-400 underlined cursor-pointer`,children:`here`})]}),(0,q.jsxs)(I,{title:`Add another citizenship`,shouldCloseOnEsc:!0,showModal:t,size:`large`,handleCloseModal:o,children:[(0,q.jsx)(v,{}),(0,q.jsx)(f,{vertical:`12`}),(0,q.jsx)(d,{contentPrimary:``,contentSecondary:(0,q.jsx)(q.Fragment,{children:`By the terms of Rules of Engagement please provide us with this information.`})}),(0,q.jsx)(f,{vertical:`16`}),(0,q.jsx)(`p`,{children:`Do you have a citizenship that you can’t verify?`}),(0,q.jsx)(f,{vertical:`16`}),(0,q.jsxs)(`div`,{className:`flex flex-col gap-xs`,children:[(0,q.jsx)(g,{accessibilityLabel:`Yes`,label:`Yes`,testId:`spec-option-yes`,checked:r,onChange:()=>{i(!0)}}),(0,q.jsx)(g,{accessibilityLabel:`No`,label:`No`,testId:`spec-option-no`,checked:!r,onChange:()=>{i(!1)}})]}),(0,q.jsx)(f,{vertical:`16`}),(0,q.jsx)(E,{size:C.Scale200,variation:b.Subtle,children:`We will come back to you to confirm the country later.`}),(0,q.jsx)(f,{vertical:`28`}),(0,q.jsx)(v,{variation:y.Light}),(0,q.jsx)(f,{vertical:`16`}),(0,q.jsxs)(`div`,{className:`flex justify-end`,children:[(0,q.jsx)(h,{variation:D.Tertiary,onClick:o,children:`Cancel`}),(0,q.jsx)(f,{horizontal:`16`}),(0,q.jsx)(h,{disabled:r===e,onClick:()=>{s()},children:`Save`})]})]})]})},Ln=({citizenshipVerifications:e,activeVerificationUrl:t,hasUnverifiableCitizenship:n,terms:r,disabled:i,loading:a})=>(0,q.jsxs)(`div`,{className:`flex flex-col gap-lg`,children:[(0,q.jsx)(`div`,{className:`flex flex-col gap-xs`,children:a?(0,q.jsx)(le,{lines:2,testId:`citizenship-row-loading`}):e.map(e=>(0,q.jsx)(kn,{citizenshipVerification:e},e.id))}),(0,q.jsx)(E,{size:C.Scale200,variation:b.Subtle,children:`This information is only visible for you`}),(0,q.jsx)(Nn,{activeVerificationUrl:t,terms:r,disabled:a?!0:i}),(0,q.jsx)(In,{hasUnverifiableCitizenship:n})]}),Rn=({citizenshipVerifications:e,activeVerificationUrl:t,hasUnverifiableCitizenship:n,terms:r,disabled:i,loading:a,idVerified:o})=>{let{isDarkModeEnabled:s}=j();return(0,q.jsx)(Yt,{iconSrc:s?Dn:En,title:`Citizenship`,button:o?(0,q.jsx)(Ln,{citizenshipVerifications:e,activeVerificationUrl:t,disabled:i,loading:a,terms:r,hasUnverifiableCitizenship:n}):(0,q.jsx)(h,{disabled:!0,children:`Add residency`}),completed:e.length>0,duration:`2 minutes`,requirements:[{label:`Be ID Verified`,checked:o}],children:`Find out how to become a citizenship-verified hacker and gain access to additional programs. If you have more than one citizenship, please attempt to validate all of them.`})},zn=O(`
  query NationalStatusesQuery {
    me {
      id
      verified
      user_identity {
        id
        has_unverifiable_residency
        has_unverifiable_citizenship
        residency_verifications {
          nodes {
            id
            nationality
          }
        }
        citizenship_verifications {
          nodes {
            id
            nationality
            country_code
          }
        }
        residency_verification_limit_reached
        citizenship_verification_limit_reached
        active_residency_verification_url
        active_citizenship_verification_url
      }
    }
    residencyVerificationTerms: terms(
      where: { name: { _eq: "residency_verification" } }
      order_by: { created_at: { _direction: DESC } }
      first: 1
    ) {
      edges {
        node {
          copy
        }
      }
    }
    citizenshipVerificationTerms: terms(
      where: { name: { _eq: "citizenship_verification" } }
      order_by: { created_at: { _direction: DESC } }
      first: 1
    ) {
      edges {
        node {
          copy
        }
      }
    }
  }
`),Bn=`/assets/static/residency_icon-ByYPkCMo.png`,Vn=`/assets/static/residency_icon_dark-CIfJ747n.png`,Hn=`data:image/svg+xml,%3csvg%20width='24'%20height='24'%20viewBox='0%200%2024%2024'%20fill='none'%20xmlns='http://www.w3.org/2000/svg'%3e%3cg%20id='real-estate-action-house-check%201'%3e%3cpath%20id='Vector'%20d='M8.48438%2019.0312H5.67188C5.29891%2019.0312%204.94123%2018.8831%204.67751%2018.6194C4.41378%2018.3556%204.26562%2017.998%204.26562%2017.625V10.5938'%20stroke='%233F3AFC'%20stroke-width='1.5'%20stroke-linecap='round'%20stroke-linejoin='round'/%3e%3cpath%20id='Vector_2'%20d='M1.45312%209.18759L9.68531%202.22197C9.93923%202.00708%2010.2611%201.88916%2010.5938%201.88916C10.9264%201.88916%2011.2483%202.00708%2011.5022%202.22197L18.3309%208.00072'%20stroke='%233F3AFC'%20stroke-width='1.5'%20stroke-linecap='round'%20stroke-linejoin='round'/%3e%3cpath%20id='Vector_3'%20d='M15.5156%202.15625H18.3281V4.96875'%20stroke='%233F3AFC'%20stroke-width='1.5'%20stroke-linecap='round'%20stroke-linejoin='round'/%3e%3cpath%20id='Vector_4'%20d='M11.2969%2016.2188C11.2969%2017.7106%2011.8895%2019.1413%2012.9444%2020.1962C13.9993%2021.2511%2015.43%2021.8437%2016.9219%2021.8438C18.4137%2021.8437%2019.8445%2021.2511%2020.8994%2020.1962C21.9542%2019.1413%2022.5469%2017.7106%2022.5469%2016.2188C22.5469%2014.7269%2021.9542%2013.2962%2020.8994%2012.2413C19.8445%2011.1864%2018.4137%2010.5938%2016.9219%2010.5938C15.43%2010.5938%2013.9993%2011.1864%2012.9444%2012.2413C11.8895%2013.2962%2011.2969%2014.7269%2011.2969%2016.2188Z'%20stroke='%233F3AFC'%20stroke-width='1.5'%20stroke-linecap='round'%20stroke-linejoin='round'/%3e%3cpath%20id='Vector_5'%20d='M19.4288%2014.5828L16.7053%2018.2146C16.6448%2018.2952%2016.5676%2018.3618%2016.4791%2018.4099C16.3906%2018.4581%2016.2928%2018.4867%2016.1923%2018.4938C16.0918%2018.5009%2015.9909%2018.4864%2015.8965%2018.4512C15.8021%2018.4159%2015.7163%2018.3609%2015.645%2018.2896L14.2388%2016.8834'%20stroke='%233F3AFC'%20stroke-width='1.5'%20stroke-linecap='round'%20stroke-linejoin='round'/%3e%3c/g%3e%3c/svg%3e`,Un=O(`
  mutation InvalidateResidencyVerificationMutation(
    $input: InvalidateResidencyVerificationInput!
  ) {
    invalidateResidencyVerification(input: $input) {
      was_successful
      user_identity {
        id
        residency_verifications {
          nodes {
            id
            __typename
          }
        }
        __typename
      }
      errors {
        edges {
          node {
            id
            field
            type
            message
          }
        }
      }
    }
  }
`),Wn=({residencyVerification:e})=>{let[t,n]=(0,G.useState)(!1),[r,{loading:i}]=_(Un,{onError:W,onCompleted:({invalidateResidencyVerification:e})=>{if(e.was_successful)N(`notice`,`Residency verification deleted`);else throw N(`error`,`Could not delete residency verification, please try again later`),new M(e.errors)}}),a=async()=>{await r({variables:{input:{residency_verification_id:e.id}}})};return(0,q.jsxs)(q.Fragment,{children:[(0,q.jsxs)(`div`,{className:`flex flex-row items-center gap-xs`,children:[(0,q.jsx)(`div`,{className:`rounded-full bg-blue-950 w-min aspect-1 p-xs flex justify-center align-center`,children:(0,q.jsx)(S,{src:Hn,size:T.Large})}),(0,q.jsxs)(E,{size:C.Scale500,children:[`Your `,e.nationality,` residency has been verified`]}),(0,q.jsx)(`div`,{className:`ml-auto`,children:(0,q.jsx)(h,{onClick:()=>{n(e=>!e)},disabled:i,iconOnly:!0,icons:{center:{src:se,accessibilityLabel:`Delete ${e.nationality} residency`}},variation:D.GhostSecondary})})]}),(0,q.jsxs)(I,{title:`Delete ${e.nationality} residency`,shouldCloseOnEsc:!0,shouldCloseOnOverlayClick:!0,showModal:t,size:`medium`,handleCloseModal:()=>{n(e=>!e)},children:[(0,q.jsx)(v,{variation:y.Light}),(0,q.jsx)(E,{children:`Are you sure you want to delete your residency verification? This step is irreversible. To add the residency again, you must go through the process again.`}),(0,q.jsx)(v,{variation:y.Light}),(0,q.jsxs)(`div`,{className:`flex justify-end gap-md`,children:[(0,q.jsx)(h,{variation:D.Tertiary,onClick:()=>{n(e=>!e)},small:!0,children:`Cancel`}),(0,q.jsx)(h,{variation:D.Danger,onClick:()=>{a()},small:!0,children:`Delete residency`})]})]})]})};w();var Gn=c`
  mutation StartResidencyVerification(
    $input: StartResidencyVerificationInput!
  ) {
    startResidencyVerification(input: $input) {
      url
      was_successful
      errors {
        edges {
          node {
            id
            message
            type
          }
        }
      }
    }
  }
`,Kn=({activeVerificationUrl:e,terms:t,disabled:n})=>{let{isDarkModeEnabled:i}=j(),[a,o]=(0,G.useState)(!1),[s,c]=(0,G.useState)(!1),[l]=_(Gn,{onCompleted:({startResidencyVerification:{url:e,was_successful:t,errors:n}})=>{if(t)window.location.href=e;else throw u(),new M(n)},onError:()=>{u()}}),u=()=>{N(`error`,`Could not start residency verification, please try again later`)},ee=async()=>{await l({variables:{input:{}}})},p=()=>{e?window.location.href=e:ee()},m=()=>{o(!1)};return(0,q.jsxs)(E,{children:[n&&(0,q.jsxs)(`div`,{children:[(0,q.jsx)(`p`,{className:`text-red-400 text-sm`,children:`You have reached your limit for requesting residency verifications.`}),(0,q.jsx)(f,{vertical:`4`})]}),(0,q.jsx)(h,{disabled:n,onClick:()=>{o(!0)},children:`Add residency`}),(0,q.jsxs)(I,{title:`Welcome to Residency verification`,shouldCloseOnEsc:!0,showModal:a,size:`large`,handleCloseModal:m,children:[(0,q.jsx)(v,{variation:y.Light}),(0,q.jsx)(d,{contentPrimary:`Please ensure submitted documents contain your address`,contentSecondary:`Your residency can only be verified if the provided document contains your address. Your application will be rejected if you provide a document that does not contain your address.`,variation:r.Warning}),(0,q.jsx)(f,{vertical:`32`}),(0,q.jsx)(`div`,{className:`flex justify-center`,children:(0,q.jsx)(`img`,{alt:`Residency image`,src:i?Vn:Bn})}),(0,q.jsxs)(`div`,{children:[(0,q.jsx)(f,{vertical:`16`}),(0,q.jsx)(`h1`,{className:`text-2xl lg:text-3xl`,children:`Residency general information`})]}),(0,q.jsxs)(`div`,{children:[(0,q.jsx)(`strong`,{children:`How does it work?`}),(0,q.jsx)(`p`,{children:`For access to select private programs, you must verify your country of residence. If you have more than one country of residency, complete the process for each country of residency.`})]}),(0,q.jsxs)(`div`,{children:[(0,q.jsx)(`strong`,{children:`What is residency?`}),(0,q.jsx)(`p`,{children:`Residency means the legal right to live and work in a country or state.`})]}),(0,q.jsxs)(`div`,{children:[(0,q.jsx)(`strong`,{children:`What do you need to get it done?`}),(0,q.jsxs)(`ul`,{className:`list-disc ml-md`,children:[(0,q.jsx)(`li`,{children:`Have your ID which shows your residency ready (Identify Card, Residence Permit, or Driver's License)`}),(0,q.jsx)(`li`,{children:`Capture the ID image`}),(0,q.jsx)(`li`,{children:`Take a selfie (use a good quality webcam or phone camera)`})]}),(0,q.jsx)(`p`,{children:`Don't have an ID with your country of residence? Tell us about the country/ies to which you have residency. You can validate them at a later date.`})]}),(0,q.jsxs)(`div`,{children:[(0,q.jsx)(`strong`,{children:`How long does it take?`}),(0,q.jsx)(`p`,{children:`The whole process might take between 2-5 minutes. You will be informed of your status on the platform.`})]}),(0,q.jsx)(dt,{terms:t,signed:s,sign:()=>{c(!s)}}),(0,q.jsx)(f,{vertical:`40`}),(0,q.jsx)(v,{variation:y.Light}),(0,q.jsx)(f,{vertical:`16`}),(0,q.jsxs)(`div`,{className:`flex justify-end`,children:[(0,q.jsx)(h,{variation:D.Tertiary,onClick:m,children:`Cancel`}),(0,q.jsx)(f,{horizontal:`16`}),(0,q.jsx)(h,{disabled:!s,onClick:()=>{p()},children:`Start the process`})]})]})]})},qn=({hasUnverifiableResidency:e})=>{let[t,n]=(0,G.useState)(!1),[r,i]=(0,G.useState)(e),[a]=_(Pn,{onCompleted:({saveUnverifiableResidency:{was_successful:e,errors:t}})=>{if(e)N(`notice`,`Information about non-verifiable residency saved`),o();else throw W(),new M(t)},onError:W}),o=()=>{n(!1)},s=async()=>{await a({variables:{input:{has_unverifiable_residency:r}}})};return(0,G.useEffect)(()=>{i(e)},[e]),(0,q.jsxs)(q.Fragment,{children:[(0,q.jsxs)(E,{size:C.Scale200,variation:b.Subtle,children:[`If you can’t verify your residency add the information`,` `,(0,q.jsx)(`span`,{onClick:()=>{n(!0)},className:`text-blue-400 underlined cursor-pointer`,children:`here`})]}),(0,q.jsxs)(I,{title:`Add another residency`,shouldCloseOnEsc:!0,showModal:t,size:`large`,handleCloseModal:o,children:[(0,q.jsx)(v,{}),(0,q.jsx)(f,{vertical:`12`}),(0,q.jsx)(d,{contentPrimary:``,contentSecondary:(0,q.jsx)(q.Fragment,{children:`By the terms of Rules of Engagement please provide us with this information.`})}),(0,q.jsx)(f,{vertical:`16`}),(0,q.jsx)(`p`,{children:`Do you have a residency that you can’t verify?`}),(0,q.jsx)(f,{vertical:`16`}),(0,q.jsxs)(`div`,{className:`flex flex-col gap-xs`,children:[(0,q.jsx)(g,{accessibilityLabel:`Yes`,label:`Yes`,testId:`spec-option-yes`,checked:r,onChange:()=>{i(!0)}}),(0,q.jsx)(g,{accessibilityLabel:`No`,label:`No`,testId:`spec-option-no`,checked:!r,onChange:()=>{i(!1)}})]}),(0,q.jsx)(f,{vertical:`16`}),(0,q.jsx)(E,{size:C.Scale200,variation:b.Subtle,children:`We will come back to you to confirm the country later.`}),(0,q.jsx)(f,{vertical:`28`}),(0,q.jsx)(v,{variation:y.Light}),(0,q.jsx)(f,{vertical:`16`}),(0,q.jsxs)(`div`,{className:`flex justify-end`,children:[(0,q.jsx)(h,{variation:D.Tertiary,onClick:o,children:`Cancel`}),(0,q.jsx)(f,{horizontal:`16`}),(0,q.jsx)(h,{disabled:r===e,onClick:()=>{s()},children:`Save`})]})]})]})},Jn=({residencyVerifications:e,activeVerificationUrl:t,hasUnverifiableResidency:n,terms:r,disabled:i,loading:a})=>(0,q.jsxs)(`div`,{className:`flex flex-col gap-lg`,children:[(0,q.jsx)(`div`,{className:`flex flex-col gap-xs`,children:a?(0,q.jsx)(le,{lines:2,testId:`residency-row-loading`}):e.map(e=>(0,q.jsx)(Wn,{residencyVerification:e},e.id))}),(0,q.jsx)(E,{size:C.Scale200,variation:b.Subtle,children:`This information is only visible for you`}),(0,q.jsx)(Kn,{activeVerificationUrl:t,terms:r,disabled:a?!0:i}),(0,q.jsx)(qn,{hasUnverifiableResidency:n})]}),Yn=({residencyVerifications:e,activeVerificationUrl:t,hasUnverifiableResidency:n,terms:r,disabled:i,loading:a,idVerified:o})=>{let{isDarkModeEnabled:s}=j();return(0,q.jsx)(Yt,{iconSrc:s?Vn:Bn,title:`Residency`,button:o?(0,q.jsx)(Jn,{residencyVerifications:e,activeVerificationUrl:t,hasUnverifiableResidency:n,disabled:i,loading:a,terms:r}):(0,q.jsx)(h,{disabled:!0,children:`Add residency`}),completed:e.length>0,duration:`2 minutes`,requirements:[{label:`Be ID Verified`,checked:o}],children:`Find out how to become a residency-verified hacker and gain access to additional programs. If you have more than one residence, please attempt to validate all of them.`})},Xn=()=>{let{data:e,loading:t}=ie(zn);return(0,q.jsx)(`div`,{className:`flex justify-center w-full`,children:(0,q.jsx)(`div`,{className:`daisy-grid--has-outside-gutter pb-spacing-24`,children:(0,q.jsx)(E,{children:(0,q.jsxs)(ce,{fill:!0,children:[(0,q.jsx)(x,{edgeToEdge:!0,children:(0,q.jsx)(`div`,{className:`p-lg bg-neutral-900 dark:bg-neutral-50`,children:`Learn more about additional verifications regarding your residency and citizenship.`})}),(0,q.jsx)(`div`,{className:`pb-spacing-16`,children:(0,q.jsx)(x,{edgeToEdge:!0,children:(0,q.jsx)(`div`,{className:`lg:px-xl bg-center bg-black bg-cover`,style:{backgroundImage:`url(${Wt})`},children:(0,q.jsxs)(`div`,{className:`flex flex-col-reverse gap-xl md:gap-0 md:grid md:grid-rows-1 md:grid-cols-5 p-2xl md:p-xl lg:py-2xl lg:px-spacing-80`,children:[(0,q.jsxs)(`div`,{className:`flex flex-col text-white font-normal gap-lg md:col-span-2`,children:[(0,q.jsx)(`h1`,{className:`text-[32px] lg:text-5xl m-0`,children:`Residency & Citizenship verification process`}),(0,q.jsx)(`p`,{className:`text-[16px] lg:text-xl m-0`,children:`Discover the advantages of verifiying your residency and citizenship(s).`})]}),(0,q.jsx)(`img`,{src:Tn,className:`aspect-[1/1] object-contain max-h-fit px-spacing-64 md:px-0 md:col-start-4 md:col-span-2 hidden md:block`})]})})})}),(0,q.jsx)(x,{children:(0,q.jsxs)(`div`,{className:`p-sm md:px-md md:py-xl lg:px-xl`,children:[(0,q.jsx)(Yn,{residencyVerifications:e?.me?.user_identity?.residency_verifications?.nodes??[],activeVerificationUrl:e?.me?.user_identity?.active_residency_verification_url??null,hasUnverifiableResidency:e?.me?.user_identity?.has_unverifiable_residency??!1,terms:e?.residencyVerificationTerms?.edges?.[0]?.node?.copy,disabled:!!e?.me?.user_identity?.residency_verification_limit_reached,loading:t,idVerified:e?.me?.verified??!1}),(0,q.jsx)(Rn,{citizenshipVerifications:e?.me?.user_identity?.citizenship_verifications?.nodes??[],activeVerificationUrl:e?.me?.user_identity?.active_citizenship_verification_url??null,hasUnverifiableCitizenship:e?.me?.user_identity?.has_unverifiable_citizenship??!1,terms:e?.citizenshipVerificationTerms?.edges?.[0]?.node?.copy,disabled:!!e?.me?.user_identity?.citizenship_verification_limit_reached,loading:t,idVerified:e?.me?.verified??!1})]})})]})})})})};w();var Zn=e(ve()),Qn=({pentester_profile:e={}})=>{let t=e.completed_pentests_number||0;return(0,q.jsx)(H,{top:!0,children:(0,q.jsxs)(P,{children:[(0,q.jsx)(P.Heading,{children:`Pentest stats`}),(0,q.jsx)(P.Content,{children:(0,q.jsx)(kt,{className:`profile-metric__item spec-thanked`,amount:t,label:`Completed ${Zn.default.pluralize(t,`pentest`)}`})})]})})};Qn.propTypes={pentester_profile:K.default.object.isRequired},Qn.fragments={pentester_profile:c`
    fragment PentestsPentesterProfile on PentesterProfile {
      id
      completed_pentests_number
    }
  `};var $n=`data:image/svg+xml,%3csvg%20xmlns='http://www.w3.org/2000/svg'%20width='21'%20height='23'%20fill='none'%3e%3cpath%20fill='%23F8546F'%20d='M19.117%206h-.367l-2.632%203.29c-.997-3.04-.87-6.337.36-9.29A13.4%2013.4%200%200%200%205.386%206.978L3%204.651A10.5%2010.5%200%201%200%2019.117%206Z'/%3e%3cpath%20fill='%23FFE98A'%20d='M9.1%209.394a5.227%205.227%200%200%201%20.53%205.957%201.861%201.861%200%200%201-1.986-1.588%204.216%204.216%200%200%200-2.185%203.972%204.766%204.766%200%200%200%204.767%204.766%204.832%204.832%200%200%200%204.766-4.766c.176-4.701-2.554-7.249-5.892-8.341Z'/%3e%3c/svg%3e`,er=`data:image/svg+xml,%3csvg%20xmlns='http://www.w3.org/2000/svg'%20width='18'%20height='20'%20fill='none'%3e%3cpath%20fill='%23DEE8FC'%20d='M6.61%2015.92H1.963A1.162%201.162%200%200%201%20.8%2014.758V5.461A1.162%201.162%200%200%201%201.962%204.3h10.46a1.162%201.162%200%200%201%201.161%201.162v3.486'/%3e%3cpath%20stroke='%23262B44'%20stroke-linecap='round'%20stroke-linejoin='round'%20d='M6.61%2015.92H1.963A1.162%201.162%200%200%201%20.8%2014.758V5.461A1.162%201.162%200%200%201%201.962%204.3h10.46a1.162%201.162%200%200%201%201.161%201.162v3.486M.8%207.398h12.783M4.674%203.524V1.2M10.484%203.524V1.2'/%3e%3cpath%20fill='%2386A3F9'%20stroke='%23262B44'%20stroke-linecap='round'%20stroke-linejoin='round'%20d='M7.385%2013.983a4.649%204.649%200%201%200%209.297%200%204.649%204.649%200%200%200-9.297%200Z'/%3e%3cpath%20stroke='%23262B44'%20stroke-linecap='round'%20stroke-linejoin='round'%20d='M13.701%2014.875h-2.055V12.82'/%3e%3c/svg%3e`,tr=e=>_e(new Date(2023,e),`MMM`),nr=e=>{switch(e){case Q.Active:return{icon:$n,bgClass:`bg-orange-900 pl-[3px] pt-[2px]`,monthClass:`text-orange-400`,testId:`active-month-streak`};case Q.Current:return{icon:er,bgClass:`bg-neutral-800 dark:bg-neutral-100 pl-[8px] pt-[6px]`,monthClass:`text-neutral-500`,testId:`current-month-streak`};default:return{icon:``,bgClass:`bg-neutral-800 dark:bg-neutral-100`,monthClass:`text-neutral-500`,testId:`empty-month-streak`}}},Z=({variation:e,month:t,presentationMode:n})=>{let{icon:r,bgClass:i,monthClass:a,testId:o}=nr(e);return(0,q.jsxs)(`div`,{className:(0,Y.default)(`flex flex-col items-center gap-2xs`,n?`px-xs`:`basis-1/6`),"data-testid":o,children:[(0,q.jsx)(`div`,{className:(0,Y.default)(`flex w-xl h-xl rounded-full items-center justify-center`,i),children:(0,q.jsx)(S,{size:T.Large,src:r})}),(0,q.jsx)(`span`,{className:(0,Y.default)(`text-xs`,a),children:tr(t)})]})},rr=()=>[...Array(12).keys()].map(e=>(0,q.jsx)(Z,{variation:Q.Empty,month:e},e)),ir=(e,t,n)=>{if(!e||!t||!n)return rr();let r=t instanceof Date?t:new Date(t),i=n instanceof Date?n:new Date(n);if(isNaN(r.getTime())||isNaN(i.getTime()))return rr();let a=new Date().getUTCMonth(),o=new Date().getUTCFullYear(),s=r.getUTCMonth(),c=i.getUTCMonth(),l=r.getUTCFullYear(),u=i.getUTCFullYear(),d=e=>Date.UTC(l,s)<=Date.UTC(o,e)&&Date.UTC(o,e)<=Date.UTC(u,c);return[...Array(12).keys()].map((e,t)=>c<a-1?(0,q.jsx)(Z,{variation:Q.Empty,month:t},t):d(e)?(0,q.jsx)(Z,{variation:Q.Active,month:t},t):e===a?(0,q.jsx)(Z,{variation:Q.Current,month:t},t):(0,q.jsx)(Z,{variation:Q.Empty,month:t},t))},ar=({streakExists:e,streakStartDate:t,streakEndDate:n})=>ir(e,t,n),Q=function(e){return e[e.Empty=0]=`Empty`,e[e.Active=1]=`Active`,e[e.Current=2]=`Current`,e}({}),or=(e,t)=>{if(t===null||e===null)return!1;let n=new Date().getUTCMonth();return new Date(t).getUTCMonth()>=n-1},sr=({userStreak:e,displayHint:t})=>{let n=e?.length??0,r=e?.start_date??null,i=e?.end_date??null,a=or(r,i);return a||(n=0),(0,q.jsxs)(`div`,{className:`flex flex-col gap-lg`,children:[(0,q.jsx)(me,{size:xe.Scale300,children:`${n} ${Zn.default.pluralize(n,`month`)} streak!`}),(0,q.jsx)(`div`,{className:`flex flex-col`,children:(0,q.jsx)(`div`,{className:`flex flex-wrap gap-y-md`,children:(0,q.jsx)(ar,{streakExists:a,streakStartDate:r,streakEndDate:i})})}),t&&(0,q.jsx)(E,{renderAs:Se.Span,variation:b.Subtle,children:`Submit at least one valid report each month and get your streak on track.`})]})},cr=`data:image/svg+xml,%3csvg%20xmlns='http://www.w3.org/2000/svg'%20width='112'%20height='134'%20fill='none'%3e%3cmask%20id='a'%20width='112'%20height='121'%20x='0'%20y='0'%20maskUnits='userSpaceOnUse'%20style='mask-type:alpha'%3e%3cpath%20fill='%23F8546F'%20d='M102%2032h-2L86%2049.5A71.2%2071.2%200%200%201%2087.9%200a71.5%2071.5%200%200%200-59.2%2037.2L16%2024.8a56%2056%200%201%200%2086%207.2Z'/%3e%3cpath%20fill='%23FFE98A'%20d='M48.5%2050.1a27.9%2027.9%200%200%201%202.9%2031.8%2010%2010%200%200%201-10.6-8.5A22.5%2022.5%200%200%200%2029%2094.6%2025.4%2025.4%200%200%200%2054.5%20120%2025.8%2025.8%200%200%200%2080%2094.6c.9-25-13.7-38.7-31.5-44.5Z'/%3e%3c/mask%3e%3cg%20mask='url(%23a)'%3e%3cpath%20fill='%23717A88'%20d='M53.7-38.4h93.9v209.1H53.7z'/%3e%3c/g%3e%3cmask%20id='b'%20width='52'%20height='71'%20x='29'%20y='49'%20maskUnits='userSpaceOnUse'%20style='mask-type:alpha'%3e%3cpath%20fill='%23FFE98A'%20d='M49.3%2049.9a27.9%2027.9%200%200%201%202.9%2031.7%2010%2010%200%200%201-10.6-8.4%2022.5%2022.5%200%200%200-11.7%2021.2%2025.4%2025.4%200%200%200%2025.4%2025.4%2025.8%2025.8%200%200%200%2025.5-25.4c.9-25.1-13.7-38.7-31.5-44.5Z'/%3e%3c/mask%3e%3cg%20mask='url(%23b)'%3e%3cpath%20fill='%23D9D9D9'%20d='M55.4-16.4h72.5v149.3H55.4z'/%3e%3c/g%3e%3cmask%20id='c'%20width='112'%20height='120'%20x='0'%20y='0'%20maskUnits='userSpaceOnUse'%20style='mask-type:alpha'%3e%3cpath%20fill='%23717A88'%20d='m102%2032-1-1.4-15%2019A71.2%2071.2%200%200%201%2087.9%200a71.5%2071.5%200%200%200-59.2%2037.2L16%2024.8a56%2056%200%201%200%2086%207.2Z'/%3e%3c/mask%3e%3cg%20mask='url(%23c)'%3e%3cpath%20fill='%23717A88'%20d='M-5.3%204.4H56v115.5H-5.3z'/%3e%3cmask%20id='d'%20width='52'%20height='71'%20x='29'%20y='49'%20maskUnits='userSpaceOnUse'%20style='mask-type:alpha'%3e%3cpath%20fill='%23B8BDC8'%20d='M49.2%2049.9A27.9%2027.9%200%200%201%2052%2081.6a10%2010%200%200%201-10.5-8.4%2022.5%2022.5%200%200%200-11.7%2021.2%2025.4%2025.4%200%200%200%2025.4%2025.4%2025.8%2025.8%200%200%200%2025.4-25.4c1-25.1-13.6-38.7-31.4-44.5Z'/%3e%3c/mask%3e%3cg%20mask='url(%23d)'%3e%3cpath%20fill='%23D9D9D9'%20d='M-20.7-13h76.8v187.7h-76.8z'/%3e%3c/g%3e%3c/g%3e%3cpath%20fill='%23F8546F'%20d='m52%20100.8-.6.1-1.7%205.8c-2.9-3.5-4.5-7.9-4.5-12.4a19%2019%200%200%200-10.8%2015.1l-4.3-1.7a14.9%2014.9%200%201%200%2021.8-7Z'/%3e%3cpath%20fill='%23FFE98A'%20d='M40.6%20110.6a7.4%207.4%200%200%201%203.9%207.5%202.6%202.6%200%200%201-3.5-1%206%206%200%200%200-.7%206.4%206.7%206.7%200%201%200%2012.5-5.2c-2.3-6.2-7.2-8-12.2-7.7Z'/%3e%3cpath%20fill='%23F8546F'%20d='m61.7%20100.7.4.2%201.3%205.8c3.2-3.2%205-7.5%205.4-12a19%2019%200%200%201%209.7%2015.8L83%20109a14.9%2014.9%200%201%201-21.3-8.3Z'/%3e%3cpath%20fill='%23FFE98A'%20d='M72.3%20111.2a7.4%207.4%200%200%200-4.4%207.3%202.6%202.6%200%200%200%203.5-.8%206%206%200%200%201%20.3%206.4%206.7%206.7%200%201%201-12-6c2.6-6%207.7-7.5%2012.6-6.9Z'/%3e%3c/svg%3e`,lr=()=>(0,q.jsxs)(`div`,{className:`flex flex-col gap-xs`,children:[(0,q.jsx)(E,{size:C.Scale300,children:`Commit to your hacker goals`}),(0,q.jsx)(me,{size:xe.Scale300,children:`Light up this fire!`}),(0,q.jsx)(`div`,{className:`flex py-md justify-center`,children:(0,q.jsx)(`img`,{src:cr,alt:`Fire icon`})}),(0,q.jsx)(E,{variation:b.Subtle,size:C.Scale300,children:`Submit at least one valid report each month and get your streak on track.`})]}),ur=({showModal:e,setShowModal:t})=>(0,q.jsxs)(I,{handleCloseModal:()=>{t(!1)},title:`What is a streak?`,showModal:e,size:`medium`,cancelLinkText:`Close`,buttonSize:`medium`,buttonColor:`black`,children:[(0,q.jsx)(f,{vertical:`md`}),(0,q.jsx)(`p`,{children:`Streaks are a way of tracking your consistent engagement in submitting valid reports each month. Every month you successfully submit a valid report, your streak increases by one. However, missing a month will reset your streak to 0, but worry not, your streak will restart the moment you submit another valid report.`}),(0,q.jsx)(`p`,{children:`The primary objective of streaks is to keep you committed to your hacker goals and maintain your dedication to submitting accurate and valuable reports. By fostering a sense of commitment and accountability, streaks encourage you to stay active and consistently contribute to the security of the platform.`}),(0,q.jsx)(`p`,{children:`Remember, the longer your streak, the more you demonstrate your commitment to ethical hacking and making a positive impact within our community. So, keep those reports coming, and let's work together to ensure a secure and reliable platform for everyone. Happy hacking!`}),(0,q.jsx)(f,{vertical:`md`}),(0,q.jsxs)(`div`,{className:`flex justify-center gap-0`,children:[(0,q.jsx)(Z,{variation:Q.Active,month:6,presentationMode:!0}),(0,q.jsx)(Z,{variation:Q.Active,month:7,presentationMode:!0}),(0,q.jsx)(Z,{variation:Q.Empty,month:8,presentationMode:!0})]})]}),dr=({userStreak:e,isMyOwnStreak:t})=>{let[n,r]=(0,G.useState)(!1),i=t&&(e==null||e.length===0||e.start_date==null||e.end_date==null||!(()=>{let t=new Date().getUTCMonth(),n=new Date;n.setUTCMonth(t-1);let r=n.getUTCMonth();if(e.end_date==null)return!1;let i=new Date(e.end_date).getUTCMonth();return i===t||i===r})());return(0,q.jsxs)(q.Fragment,{children:[(0,q.jsx)(ur,{showModal:n,setShowModal:r}),(0,q.jsxs)(P,{children:[(0,q.jsx)(P.Heading,{children:`Streak`}),(0,q.jsx)(P.Content,{children:(0,q.jsxs)(`div`,{className:`flex flex-col gap-lg`,children:[(0,q.jsx)(`div`,{children:i?(0,q.jsx)(lr,{}):(0,q.jsx)(sr,{userStreak:e,displayHint:t})}),(0,q.jsx)(`div`,{className:`flex justify-center`,children:(0,q.jsx)(h,{renderAs:ue.Link,variation:D.Ghost,icons:{right:{accessibilityLabel:`Open in new window`,src:ge}},to:`#`,onClick:()=>{r(!0)},testId:`button-what-is-a-streak`,children:`What is a streak?`})})]})})]})]})};w();var fr=c`
  query getTeams($username: String!) {
    user(username: $username) {
      id
      memberships(first: 10, where: { concealed: { _eq: false } }) {
        total_count
        edges {
          node {
            id
            team {
              id
              name
              handle
              state
              profile_picture(size: small)
            }
          }
        }
      }
    }
  }
`,pr=({username:e})=>{let{loading:t,error:n,data:r}=U(fr,{variables:{username:e}});if(t||n)return null;let{user:i}=r;return J.default.not.empty(i.memberships.edges)&&(0,q.jsx)(H,{top:!0,children:(0,q.jsxs)(P,{className:`spec-user-profile-recent-badges`,children:[(0,q.jsxs)(P.Heading,{children:[(0,q.jsx)(`span`,{children:`Programs`}),(0,q.jsx)(Ne,{className:`margin-4--left`,tooltipText:`This user is involved in the creation or management of the following programs`,iconGlyph:`data:image/svg+xml,%3csvg%20xmlns='http://www.w3.org/2000/svg'%20viewBox='0%200%2024%2024'%3e%3cpath%20fill='none'%20d='M0%200h24v24H0z'/%3e%3cpath%20d='M11%2018h2v-2h-2v2zm1-16C6.48%202%202%206.48%202%2012s4.48%2010%2010%2010%2010-4.48%2010-10S17.52%202%2012%202zm0%2018c-4.41%200-8-3.59-8-8s3.59-8%208-8%208%203.59%208%208-3.59%208-8%208zm0-14c-2.21%200-4%201.79-4%204h2c0-1.1.9-2%202-2s2%20.9%202%202c0%202-3%201.75-3%205h2c0-2.25%203-2.5%203-5%200-2.21-1.79-4-4-4z'/%3e%3c/svg%3e`,eventType:`hover`})]}),(0,q.jsx)(P.Content,{children:(0,q.jsxs)(H,{children:[i.memberships.edges.map(({node:{team:e}})=>(0,q.jsx)(H,{children:(0,q.jsxs)(z,{children:[(0,q.jsx)(z,{width:50,children:(0,q.jsx)(V,{src:e.profile_picture})}),(0,q.jsxs)(z,{alignItems:`center`,flexWrap:`wrap`,children:[(0,q.jsx)(z,{children:(0,q.jsx)(F,{className:`daisy-link text-truncate`,to:`/${e.handle}`,children:e.name})}),(0,q.jsx)(z,{children:e.state===`soft_launched`&&(0,q.jsx)(nt,{className:`margin-8--right margin-8--left daisy-text--red`,children:`Confidential`})})]})]})},e.id)),i.memberships.total_count>10&&(0,q.jsxs)(`div`,{children:[`and `,i.memberships.total_count-10,` more`]})]})})]})})};pr.propTypes={username:K.default.string};var mr=e(ae()),hr=O(`
  query UserProfileTestimonialList(
    $username: String!
    $count: Int!
    $cursor: String
  ) {
    user(username: $username) {
      id
      testimonials(
        first: $count
        after: $cursor
        where: { visible_on_user_profile: { _eq: true } }
        order_by: { survey_rating: { completed_at: { _direction: DESC } } }
      ) {
        pageInfo {
          endCursor
          hasNextPage
        }
        edges {
          node {
            id
            key
            rating
            public_comment
            survey_rating {
              id
              type
              completed_at
              created_at
              team {
                id
                name
                profile_picture(size: small)
              }
            }
          }
        }
      }
    }
  }
`),gr=({survey_rating_item:e,username:t,isLast:n})=>{let r=e?.survey_rating?.team||{},i=r?.name||`a pentest program`;return(0,q.jsxs)(q.Fragment,{children:[(0,q.jsxs)(z,{className:`spec-testimonial-item`,alignItems:`center`,style:{padding:`16px 24px`},width:`100%`,children:[(0,q.jsx)(z,{minWidth:50,className:`margin-8--right`,children:(0,q.jsx)(V,{src:r?.profile_picture||`data:image/png;base64,iVBORw0KGgoAAAANSUhEUgAAAIIAAACCCAAAAACvaE8hAAACwklEQVR4Ae3aBXPjMBAF4Pv/P0/OwUCZu7blo8QWbJP2ldcHkdTsgd5Q543G+UraLbxrS4e2TXEC6RIgqARSJ1AlQKBLoEqAQJdAlQCBIgGCSiBdAgSVQLoECCqBdAkQVALpEiCoBNIlQFAJpE6g/4nQ9XaYi5WR6bs2n9APp58ak5jm44ntcgn9lTn+OjmfFDd9PTaXXR6hG0w7QZBmmFpj2yxCf3q0AYSYmLBBHJ12WQT76fPkIycn+unzpz6LMDQrF/gmORzcqrF5BDP6mEOIfjS5hOkZgW+DN2UlGxCmYgRmjgheQVayKUtgjiH424QQ8XhZyaYggTl656bbOLdpZivZFCVEf9EYpLmYr1g0ZQnBNd39dGobF+6r1iJ3FYumKCEGZwaMaLLGhYgKDydULJqCBDxpgIDsXffi4ahkU5wAQSWQOoEUCfiOAEHpOwL3gkXo6V6g5xWjKX8vzNyOlw/V5YuK0bzZ7cgxPEwgjCBZyUZ/Uv57+4Li1iQJdXGri9v5dovb+Vssbu2z21hUu1ncLGmOKTmHFfaFSqgE/e8IK++Fnf5AB4LY0hZPi9viecV3jdjuMglktRc3Iqs9KUHQ3BcIBK2tCQJ9guonAgLlL0cCQWFxEwS937gRIi/onf1kTc8JCmNKEhSGNakTqBIg0CUQovYdIQkKixtJAra0LX7jlry4SYHO4kYPUZiUQqCwLwhB5tZUlpCQVAKpE6gSINAlUCXcCSqB1An0txIYKUKgBIIclDkE2p7AHB+WAx9uFQqEGLybELdBZBJoSwIEq4OFQd7vL2FIJlASwR8c9hbpjva9AiG4RU8P6Rcu5BAogcAx4NHyWAKB0gj+nyKQOoEqoRL+IsLoI8vg32rlsflzuQTn40y8w6PlMXkul7AcnZ+JG5fGymPz5zIJ35fjOImM4/K7sfLYz8/NZg3aNthXs3ZabwAAAABJRU5ErkJggg==`})}),(0,q.jsxs)(z,{flexDirection:`column`,flexGrow:1,className:`margin-8--right`,justifyContent:`space-between`,children:[(0,q.jsxs)(L,{children:[`When asked about working with a pentest team`,` `,(0,q.jsx)(`strong`,{className:`text-neutral-50 dark:text-neutral-900`,children:t}),` `,`was on,`,` `,(0,q.jsx)(`strong`,{className:`text-neutral-50 dark:text-neutral-900`,children:i}),` `,`said...`]}),(0,q.jsx)(z,{children:`"${e.public_comment}"`})]}),(0,q.jsx)(z,{justifyContent:`center`,flexShrink:0,alignItems:`center`,alignSelf:`baseline`,style:{whiteSpace:`nowrap`},children:(0,q.jsx)(L,{children:e?.survey_rating?.completed_at||e?.survey_rating?.created_at?(0,q.jsx)(Ue,{time:e?.survey_rating?.completed_at||e?.survey_rating?.created_at}):`Some time ago`})})]}),!n&&(0,q.jsx)(Ze,{size:`no-spacing`})]})};gr.propTypes={survey_rating_item:K.default.object,username:K.default.string.isRequired,isLast:K.default.bool};var _r=({survey_rating_item:e,username:t,isLast:n})=>{let r=e?.survey_rating?.team||{},i=r?.name||`a private team`;return(0,q.jsxs)(q.Fragment,{children:[(0,q.jsxs)(z,{className:`spec-testimonial-item`,alignItems:`center`,style:{padding:`16px 24px`},width:`100%`,children:[(0,q.jsx)(z,{minWidth:50,className:`margin-8--right`,children:(0,q.jsx)(V,{src:r?.profile_picture||`data:image/png;base64,iVBORw0KGgoAAAANSUhEUgAAAIIAAACCCAAAAACvaE8hAAACwklEQVR4Ae3aBXPjMBAF4Pv/P0/OwUCZu7blo8QWbJP2ldcHkdTsgd5Q543G+UraLbxrS4e2TXEC6RIgqARSJ1AlQKBLoEqAQJdAlQCBIgGCSiBdAgSVQLoECCqBdAkQVALpEiCoBNIlQFAJpE6g/4nQ9XaYi5WR6bs2n9APp58ak5jm44ntcgn9lTn+OjmfFDd9PTaXXR6hG0w7QZBmmFpj2yxCf3q0AYSYmLBBHJ12WQT76fPkIycn+unzpz6LMDQrF/gmORzcqrF5BDP6mEOIfjS5hOkZgW+DN2UlGxCmYgRmjgheQVayKUtgjiH424QQ8XhZyaYggTl656bbOLdpZivZFCVEf9EYpLmYr1g0ZQnBNd39dGobF+6r1iJ3FYumKCEGZwaMaLLGhYgKDydULJqCBDxpgIDsXffi4ahkU5wAQSWQOoEUCfiOAEHpOwL3gkXo6V6g5xWjKX8vzNyOlw/V5YuK0bzZ7cgxPEwgjCBZyUZ/Uv57+4Li1iQJdXGri9v5dovb+Vssbu2z21hUu1ncLGmOKTmHFfaFSqgE/e8IK++Fnf5AB4LY0hZPi9viecV3jdjuMglktRc3Iqs9KUHQ3BcIBK2tCQJ9guonAgLlL0cCQWFxEwS937gRIi/onf1kTc8JCmNKEhSGNakTqBIg0CUQovYdIQkKixtJAra0LX7jlry4SYHO4kYPUZiUQqCwLwhB5tZUlpCQVAKpE6gSINAlUCXcCSqB1An0txIYKUKgBIIclDkE2p7AHB+WAx9uFQqEGLybELdBZBJoSwIEq4OFQd7vL2FIJlASwR8c9hbpjva9AiG4RU8P6Rcu5BAogcAx4NHyWAKB0gj+nyKQOoEqoRL+IsLoI8vg32rlsflzuQTn40y8w6PlMXkul7AcnZ+JG5fGymPz5zIJ35fjOImM4/K7sfLYz8/NZg3aNthXs3ZabwAAAABJRU5ErkJggg==`})}),(0,q.jsxs)(z,{flexDirection:`column`,flexGrow:1,className:`margin-8--right`,justifyContent:`space-between`,children:[(0,q.jsxs)(L,{children:[`When asked about working with`,` `,(0,q.jsx)(`strong`,{className:`text-neutral-50 dark:text-neutral-900`,children:t}),` `,`on a vulnerability submission,`,` `,(0,q.jsx)(`strong`,{className:`text-neutral-50 dark:text-neutral-900`,children:i}),` `,`said...`]}),(0,q.jsx)(z,{children:`"${e.public_comment}"`})]}),(0,q.jsx)(z,{justifyContent:`center`,flexShrink:0,alignItems:`center`,alignSelf:`baseline`,style:{whiteSpace:`nowrap`},children:(0,q.jsx)(L,{children:e?.survey_rating?.completed_at||e?.survey_rating?.created_at?(0,q.jsx)(Ue,{time:e?.survey_rating?.completed_at||e?.survey_rating?.created_at}):`Some time ago`})})]}),!n&&(0,q.jsx)(Ze,{size:`no-spacing`})]})};_r.propTypes={survey_rating_item:K.default.object,username:K.default.string.isRequired,isLast:K.default.bool};var vr=e=>{let{survey_rating_item:t}=e,n={pentester:gr,lead_pentester_pentester_overall_experience:gr,supporting_pentester_other_pentester_overall_experience:gr,hacker_review_legacy:_r}[t.key];return n&&n?(0,q.jsx)(n,{...e}):null};vr.propTypes={survey_rating_item:K.default.object.isRequired,username:K.default.string.isRequired,isLast:K.default.bool},vr.Loading=()=>(0,q.jsxs)(q.Fragment,{children:[(0,q.jsxs)(z,{className:`spec-testimonial-item`,justifyContent:`space-between`,alignItems:`center`,style:{padding:`16px 24px`},width:`100%`,children:[(0,q.jsx)(z,{alignItems:`center`,width:80,children:(0,q.jsx)(V,{loading:!0,src:``})}),(0,q.jsx)(z,{flexGrow:1,children:(0,q.jsxs)(z,{flexDirection:`column`,width:`100%`,children:[(0,q.jsxs)(z,{justifyContent:`space-between`,marginBottom:`8px`,children:[(0,q.jsx)(z,{children:(0,q.jsx)(L,{children:(0,q.jsx)(B,{width:200,height:`12px`})})}),(0,q.jsx)(z,{children:(0,q.jsx)(L,{children:(0,q.jsx)(B,{width:80,height:`12px`})})})]}),(0,q.jsx)(z,{children:(0,q.jsx)(Be,{lineHeight:`12px`})})]})})]}),(0,q.jsx)(Ze,{size:`no-spacing`})]}),vr.Loading.displayName=`TestimonialItem.Loading`;var yr=window.constants?.pagination?.user_testimonials_items_per_page,br=({username:e})=>{let{data:t,loading:n,fetchMore:r}=ie(hr,{variables:{username:e,count:yr},notifyOnNetworkStatusChange:!0}),i=He(t,`user.testimonials`,r),{user:a}=t??{},{testimonials:o}=a??{},s=o?.edges??[];return(0,q.jsx)(`div`,{className:`mt-[20px]`,children:(0,q.jsxs)(ce,{fill:!0,padding:be.None,children:[(0,q.jsx)(P.Heading,{children:(0,q.jsx)(`span`,{children:`Testimonials`})}),n||s?.length>0?(0,q.jsx)(x,{edgeToEdge:!0,children:n&&!s.length?(0,mr.default)(3).map(e=>(0,q.jsx)(vr.Loading,{},e)):(0,q.jsxs)(q.Fragment,{children:[s.map((t,n)=>{let{node:r}=t;return r?(0,q.jsx)(`div`,{"data-testid":`testimonial-text`,children:(0,q.jsx)(vr,{survey_rating_item:r,username:e,isLast:n===s.length-1},r.id)},r.id):null}),o?.pageInfo?.hasNextPage&&(0,q.jsx)(`div`,{className:`flex justify-center p-[20px] items-center`,children:n?(0,q.jsx)(Ee,{}):(0,q.jsx)(h,{onClick:i,variation:D.Emphasized,small:!0,children:`View more`})})]})}):(0,q.jsx)(x,{children:(0,q.jsx)(`div`,{"data-testid":`no-testimonials`,className:`p-[20px]`,children:(0,q.jsxs)(te,{children:[e,` hasn't received any testimonials yet.`]})})})]})})};w();var xr=({rank:e})=>{let t;switch(e){case 1:t=`daisy-text--yellow spec-gold`;break;case 2:t=`daisy-text--stone spec-silver`;break;case 3:t=`daisy-text--orange_dark spec-bronze`;break;default:t=`daisy-text--blue`}let n;return e&&e<=3&&(n=(0,q.jsx)(`i`,{className:`icon-small-cup spec-cup`})),(0,q.jsxs)(`span`,{className:`spec-rank ${t}`,children:[n,e||`-`]})};xr.propTypes={rank:K.default.number};var $=({thanks_item:e})=>(0,q.jsxs)(`div`,{className:`spec-thanks-item flex justify-between items-center px-lg py-md border-t dark:first:border-0 border-neutral-700 dark:border-neutral-200 border-solid`,children:[(0,q.jsx)(z,{alignItems:`center`,flexBasis:180,children:e.team?(0,q.jsxs)(q.Fragment,{children:[(0,q.jsx)(`div`,{children:(0,q.jsx)(z,{flexBasis:50,className:`margin-8--right`,children:(0,q.jsx)(F,{to:e.team.url,children:(0,q.jsx)(V,{size:`medium`,object:e.team,src:e.team.profile_picture})})})}),(0,q.jsx)(`div`,{children:(0,q.jsxs)(z,{flexDirection:`column`,children:[(0,q.jsx)(z,{children:(0,q.jsx)(Ve,{team:e.team})}),(0,q.jsx)(z,{children:(0,q.jsx)(We,{team:e.team})})]})})]}):(0,q.jsxs)(q.Fragment,{children:[(0,q.jsx)(z,{flexBasis:50,className:`margin-8--right`,children:(0,q.jsx)(V,{size:`medium`,src:rt})}),(0,q.jsxs)(z,{flexDirection:`column`,children:[(0,q.jsx)(z,{children:`Private Program`}),(0,q.jsxs)(z,{children:[` `,(0,q.jsx)(nt,{className:`margin-8--right daisy-text--red`,children:`Confidential`})]})]})]})}),(0,q.jsx)(z,{justifyContent:`center`,alignItems:`center`,flexBasis:80,children:(0,q.jsxs)(q.Fragment,{children:[(0,q.jsx)(`strong`,{children:(0,q.jsx)(`span`,{className:`daisy-h3`,children:e.report_count})}),(0,q.jsx)(`span`,{className:`daisy-text--stone`,children:`/`}),e.total_report_count]})}),(0,q.jsx)(z,{justifyContent:`center`,flexBasis:80,children:e.reputation}),(0,q.jsx)(z,{justifyContent:`center`,flexBasis:30,children:(0,q.jsx)(xr,{rank:e.rank})})]});$.propTypes={thanks_item:K.default.object.isRequired},$.fragments={thanksItem:c`
    fragment ThanksItem on ThanksItem {
      id
      rank
      report_count
      total_report_count
      reputation
      team {
        id
        handle
        name
        state
        url
        profile_picture(size: medium)
        ...TeamLinkMiniProfileComponent
      }
    }
    ${Ve.fragments.team}
  `},$.Loading=()=>(0,q.jsxs)(q.Fragment,{children:[(0,q.jsxs)(`div`,{style:{display:`flex`,justifyContent:`space-between`,alignItems:`center`,padding:`16px 24px`},children:[(0,q.jsxs)(z,{alignItems:`center`,flexBasis:180,children:[(0,q.jsx)(z,{flexBasis:50,className:`margin-8--right`,children:(0,q.jsx)(V,{size:`medium`,loading:!0,src:``})}),(0,q.jsxs)(z,{flexDirection:`column`,children:[(0,q.jsx)(z,{children:(0,q.jsx)(B,{width:70,height:`12px`})}),(0,q.jsx)(z,{children:(0,q.jsx)(B,{width:50,height:`12px`})})]})]}),(0,q.jsx)(z,{justifyContent:`center`,alignItems:`center`,flexBasis:80,children:(0,q.jsx)(B,{width:50})}),(0,q.jsx)(z,{justifyContent:`center`,flexBasis:80,children:(0,q.jsx)(B,{width:30})}),(0,q.jsx)(z,{justifyContent:`center`,flexBasis:30,children:(0,q.jsx)(B,{width:30})})]}),(0,q.jsx)(Ze,{size:`no-spacing`})]}),$.Loading.displayName=`ThanksItem.Loading`,w();var Sr=constants.pagination.user_thanks_items_per_page,Cr={vulnerabilities:`Valid reports include resolved and duplicates of resolved.`,rank:`Only shows top 100.`},wr=c`
  query UserProfileThanks(
    $username: String!
    $cursor: String
    $pageSize: Int!
  ) {
    user(username: $username) {
      id
      user_display_options {
        id
        show_private_team_thanks
      }
      username
      thanks_items_total_count
      thanks_items(first: $pageSize, after: $cursor) {
        pageInfo {
          hasNextPage
          endCursor
        }
        edges {
          node {
            id
            ...ThanksItem
          }
        }
      }
    }
  }
  ${$.fragments.thanksItem}
`,Tr=De([`isMin960`])(({isMin960:e,username:t})=>{let{data:n,loading:r,fetchMore:i}=U(wr,{variables:{username:t,pageSize:Sr},notifyOnNetworkStatusChange:!0}),a=He(n,`user.thanks_items`,i),{user:o={}}=n||{},{thanks_items:s={}}=o,c=o.user_display_options?.show_private_team_thanks;return(0,q.jsx)(H,{top:!0,children:(0,q.jsxs)(P,{children:[(0,q.jsx)(P.Heading,{children:(0,q.jsxs)(G.default.Fragment,{children:[(0,q.jsx)(`span`,{children:`Thanks`}),(0,q.jsx)(Ne,{tooltipText:`Contents represent both public and private programs that hacker has engaged with.`,iconGlyph:Te,eventType:`hover`,className:`margin-4--left`}),(0,q.jsxs)(z,{justifyContent:`space-between`,children:[(0,q.jsx)(z,{flexBasis:180,children:(0,q.jsxs)(L,{children:[r&&!o.thanks_items_total_count?(0,q.jsx)(B,{width:10,height:10,inline:!0}):o.thanks_items_total_count,` `,`thanks received`]})}),(0,q.jsx)(z,{children:(0,q.jsx)(Re,{placement:`top`,tooltipText:Cr.vulnerabilities,children:(0,q.jsx)(`span`,{className:`inline-help`,children:`Valid / Closed`})})}),(0,q.jsx)(z,{children:e?`Reputation`:`Rep`}),(0,q.jsx)(z,{children:(0,q.jsx)(Re,{placement:`top`,tooltipText:Cr.rank,children:(0,q.jsx)(`span`,{className:`inline-help`,children:`Rank`})})})]})]})}),r||s.edges?.length>0?(0,q.jsx)(P.Content,{className:`p-0`,children:(0,q.jsxs)(q.Fragment,{children:[r&&!s.edges?.length?(0,mr.default)(3).map(e=>(0,q.jsx)($.Loading,{},e)):s.edges.map(({node:e})=>!c&&!e.team?null:(0,q.jsx)(G.default.Fragment,{children:(0,q.jsx)($,{thanks_item:e},e.id)},e.id)),s.pageInfo?.hasNextPage&&(0,q.jsx)(z,{justifyContent:`center`,alignItems:`center`,className:`border-t border-solid border-neutral-700 dark:border-neutral-200 pt-md`,children:r?(0,q.jsx)(Ee,{}):(0,q.jsx)(H,{children:(0,q.jsx)(Ye,{className:`spec-thanks-view-more`,size:`small`,onClick:a,children:`View more`})})})]})}):(0,q.jsxs)(P.Content,{children:[t,` hasn't received any thanks yet.`]})]})})});Tr.propTypes={username:K.default.string.isRequired};var Er=({intro:e,name:t})=>(0,q.jsx)(H,{children:(0,q.jsxs)(P,{children:[(0,q.jsxs)(P.Heading,{children:[`About `,t]}),(0,q.jsx)(P.Content,{children:(0,q.jsx)(je,{markdown:e})})]})}),Dr=({username:e})=>{let t=Je,n=st(),{data:r,loading:i}=U(Ge,{variables:{queryString:`*:*`,reporterFilter:e,size:5,from:0,sort:t},onError(){W()}});return(0,q.jsxs)(P,{style:{backgroundColor:`transparent`},children:[(0,q.jsx)(ct,{}),(0,q.jsx)(P.Content,{style:{padding:0},children:r?.search?.total_count===0?(0,q.jsxs)(`div`,{className:`py-md pl-lg`,children:[e,` hasn’t submitted any reports yet.`]}):(0,q.jsxs)(q.Fragment,{children:[(0,q.jsx)(Le,{reports:r?.search?.nodes||[],isLoading:i,readReports:n,totalCount:r?.search?.total_count||0,withPagination:!1,compactView:!0}),(0,q.jsx)(P.Footer,{children:(0,q.jsxs)(h,{small:!0,renderAs:ue.Link,to:Ke(e,`hacktivity`),variation:D.Ghost,icons:{right:{accessibilityLabel:`arrow icon`,src:ne}},children:[`See all of `,e,`'s Hacktivity`]})})]})})]})};w();var Or=({onChange:e,current:t})=>(0,q.jsx)(Pe,{className:`spec-hacktivity-filter pull-right`,value:t,onChange:e,options:Qe.map(e=>({value:e.name,label:e.action}))});Or.propTypes={onChange:K.default.func.isRequired,current:K.default.string.isRequired};var kr=c`
  query UserProfilePageQuery($resourceIdentifier: String!) {
    me {
      id
      username
      ...UserProfileMe
      ...UserProfileCardMe
      ...UserStatsMe
    }
    user(username: $resourceIdentifier) {
      id
      username
      name
      intro
      profileActivated: profile_activated
      pentester_profile {
        id
        ...PentestsPentesterProfile
      }
      user_streak {
        id
        length
        start_date
        end_date
      }
      ...UserProfileUser
      ...UserProfileCardUser
      ...CreditsUser
      ...BadgesUser
      ...ReviewUser
      ...UserStatsUser
    }
    ...UserProfileCardIdV
  }
  ${_t.me}
  ${_t.user}
  ${yt.fragments.user}
  ${yt.fragments.me}
  ${yt.fragments.id_verification}
  ${Qn.fragments.pentester_profile}
  ${At.fragments.user}
  ${Pt.fragments.user}
  ${Rt.fragments.user}
  ${ot.fragments.user}
  ${ot.fragments.me}
`,Ar=({user:e,username:t})=>(0,q.jsxs)(q.Fragment,{children:[e?.id&&e?.intro&&(0,q.jsx)(Er,{intro:e.intro,name:e.name}),(0,q.jsx)(Dr,{username:t}),(0,q.jsx)(Tr,{username:t}),(0,q.jsx)(br,{username:t}),e.pentester_profile&&(0,q.jsx)(Et,{username:t})]});Ar.propTypes={user:K.default.object.isRequired,username:K.default.string.isRequired};var jr=({username:e,tab:t})=>{let{data:n,loading:r}=U(kr,{variables:{resourceIdentifier:e}}),{user:i={},me:a={},id_verification:o={}}=n||{},s={PROFILE:{component:(0,q.jsx)(Ar,{user:i,username:e}),title:`Profile`,fullScreen:!1},HACKTIVITY:{component:(0,q.jsx)(lt,{username:e}),title:`Hacktivity`,fullScreen:!1},BADGES:{component:(0,q.jsx)(Ut,{username:e}),title:`Platform Badges`,fullScreen:!1},CLEARANCES:{component:(0,q.jsx)(wn,{}),title:`ID verification + Clear`,fullScreen:!0},NATIONAL_STATUSES:{component:(0,q.jsx)(Xn,{}),title:`Residency & Citizenship`,fullScreen:!0}},c=s[t]||s.PROFILE,l=a&&a.id===i?.id;return(0,q.jsx)(oe,{children:(0,q.jsxs)(pe,{noPadding:!0,fullBleed:!0,tertiaryNavItems:vt(a,e),children:[r===!1?(0,q.jsxs)(u,{children:[(0,q.jsx)(`title`,{children:it(i.name||i.username,c.title)}),!i.profileActivated&&(0,q.jsx)(`meta`,{name:`robots`,content:`noindex`})]}):(0,q.jsx)(u,{title:ze(`User Profile`)}),(0,q.jsx)(H,{top:!0,size:`large`,children:c.fullScreen?c.component:(0,q.jsxs)(R,{hasOutsideGutter:!0,children:[(0,q.jsxs)(R.Row,{children:[(0,q.jsxs)(R.Column,{size:`one-quarter`,children:[(0,q.jsx)(yt,{user:i,me:a,idVerification:o}),(0,q.jsxs)(H,{children:[(0,q.jsx)(H,{top:!0,children:(0,q.jsx)(ot,{username:e,user:i,me:a})}),!r&&(0,q.jsx)(H,{top:!0,children:(0,q.jsx)(dr,{userStreak:i.user_streak,isMyOwnStreak:l})}),!!i.pentester_profile&&(0,q.jsx)(Qn,{pentester_profile:i.pentester_profile}),(0,q.jsx)(At,{user:i}),(0,q.jsx)(Pt,{user:i}),(0,q.jsx)(pr,{username:e})]})]}),(0,q.jsx)(R.Column,{children:c.component})]}),(0,q.jsx)(R.Row,{children:(0,q.jsx)(R.Column,{children:(0,q.jsx)(we,{})})})]})})]})})};jr.propTypes={username:K.default.string,tab:K.default.string};export{jr as default};
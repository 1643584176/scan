import{o as e}from"./rolldown-runtime-DAXXjFlN.js";import{Fw as t,Iw as n,Kx as r,Nx as i,Pb as a,Pf as o,qx as s,zx as c}from"./vendor-_WdvpBLr.js";import{$u as l,Om as u,Tm as d,Uf as f,_h as p,dh as m,fm as h,ih as g,jh as _,km as v,lh as y,mh as b,oh as x,pm as S,sm as C,uh as w,vm as T,ym as E}from"./app-5pKgUmmm.js";import"./outline-DJHNqRTH.js";import"./linkedin_blue-CKdRMc2A.js";import{t as D}from"./sub_header-5VON2W9q.js";var O=e(c()),k=e(n());s();var A=t(),j=r`
  mutation ToggleFollowUserMutationWithUser($user_id: ID!) {
    toggleFollowUserMutation(input: { user_id: $user_id }) {
      was_successful
      user {
        id
        followed
      }
    }
  }
`,M=({user:e})=>{let[t]=p(j,{variables:{user_id:e.id},refetchQueries:[`FollowedUsers`],optimisticResponse:{toggleFollowUserMutation:{__typename:`Mutation`,was_successful:!0,user:{...e,followed:!e.followed}}},onCompleted:({toggleFollowUserMutation:e})=>{e.was_successful?E():T()}}),n=e.followed;return(0,A.jsx)(`div`,{className:(0,k.default)(`follow spec-follow daisy-helper-text`,{"follow--followed":n,"follow--not-followed":!n}),children:(0,A.jsxs)(y,{alignItems:`center`,onClick:()=>t(),children:[(0,A.jsx)(y,{children:(0,A.jsx)(g,{glyph:n?v:u,color:n?`blue`:`grey`})}),(0,A.jsx)(y,{className:`margin-2--left`,children:(0,A.jsx)(`strong`,{children:n?`Following`:`Follow`})})]})})};M.fragments={user:r`
    fragment FollowUser on User {
      id
      followed
    }
  `},M.propTypes={user:O.default.object.isRequired};var N=()=>{let e=i();return(0,A.jsxs)(`div`,{className:`flex flex-col items-center`,children:[(0,A.jsx)(`span`,{className:`daisy-helper-text text-center`,children:`Your identity isn’t verified.`}),(0,A.jsx)(m,{to:`${e.url}/clearances`,className:`text-center`,children:`Start Verification`})]})};s();var P=e(a()),F=(e,t)=>{let n=[{label:`Profile`,to:b(t),exact:!0},{label:`Badges`,to:b(t,`badges`)},{label:`Hacktivity`,to:b(t,`hacktivity`)}];return e?.username===t&&n.push({label:`ID Verification + Clear`,to:b(t,`clearances`),tag:`New`}),e?.username===t&&n.push({label:`Residency & Citizenship`,to:b(t,`national_statuses`),tag:`New`}),n.filter(Boolean)},I=(e,t)=>P.default.existy(e)&&e.username===t&&(0,A.jsx)(D.ItemButton,{text:`Edit Profile`,to:`/settings/profile/edit`}),L={me:r`
    fragment UserProfileMe on User {
      id
      username
    }
  `,user:r`
    fragment UserProfileUser on User {
      id
      username
    }
  `};s();var R=({user:e,me:t,idVerification:n})=>{let{id:r,profile_picture:i,username:a,name:s,bio:c,website:u,location:p,created_at:g,cleared:v,verified:y}=e,b=!e.id,T=t&&r&&t.id===r,E=T&&[`eligible`,`failed`].includes(n?.status);return(0,A.jsx)(d,{children:(0,A.jsxs)(d.Content,{children:[(0,A.jsxs)(`div`,{style:{display:`flex`,justifyContent:`center`,alignItems:`center`,flexDirection:`column`},children:[(0,A.jsx)(S,{size:`large`,object:e,src:i||``,cleared:v,verified:y,loading:b}),(0,A.jsx)(`div`,{className:`flex items-center`,children:(0,A.jsx)(`strong`,{className:`text-center`,children:b?(0,A.jsx)(x,{width:100}):`${s} (${a})`})}),e.mark_as_company_on_leaderboards&&(0,A.jsx)(o,{rounded:!1,color:`blue`,icons:{left:{accessibilityLabel:``,src:`data:image/svg+xml,%3csvg%20xmlns='http://www.w3.org/2000/svg'%20width='24'%20height='24'%20viewBox='0%200%2024%2024'%3e%3cpath%20d='M16.24%2013.65c-1.17-.52-2.61-.9-4.24-.9c-1.63%200-3.07.39-4.24.9A2.988%202.988%200%200%200%206%2016.39V18h12v-1.61c0-1.18-.68-2.26-1.76-2.74zM8.07%2016a.96.96%200%200%201%20.49-.52c1.1-.49%202.26-.73%203.43-.73c1.18%200%202.33.25%203.43.73c.23.1.4.29.49.52H8.07zm-6.85-1.42A2.01%202.01%200%200%200%200%2016.43V18h4.5v-1.61c0-.83.23-1.61.63-2.29c-.37-.06-.74-.1-1.13-.1c-.99%200-1.93.21-2.78.58zm21.56%200A6.95%206.95%200%200%200%2020%2014c-.39%200-.76.04-1.13.1c.4.68.63%201.46.63%202.29V18H24v-1.57c0-.81-.48-1.53-1.22-1.85zM12%2012c1.66%200%203-1.34%203-3s-1.34-3-3-3s-3%201.34-3%203s1.34%203%203%203zm0-4c.55%200%201%20.45%201%201s-.45%201-1%201s-1-.45-1-1s.45-1%201-1zM1.497%2011L4%208.497L6.503%2011L4%2013.503zM20%209l-2.5%204h5z'/%3e%3c/svg%3e`}},children:`Business`}),E&&(0,A.jsx)(w,{children:(0,A.jsx)(N,{})}),c&&(0,A.jsx)(h,{className:`break-all`,children:c}),u&&(0,A.jsx)(`a`,{className:`daisy-link break-all`,href:u,rel:`noreferrer nofollow`,children:u})]}),(0,A.jsx)(C,{size:`medium`}),(0,A.jsxs)(`div`,{style:{display:`flex`,justifyContent:`center`,alignItems:`center`,flexDirection:`column`},children:[T?b&&(0,A.jsx)(w,{children:(0,A.jsx)(x,{width:70})}):(0,A.jsx)(w,{children:(0,A.jsx)(M,{user:e})}),(0,A.jsx)(l,{user:e}),(0,A.jsx)(h,{children:p}),(0,A.jsxs)(h,{children:[`Joined`,` `,b?(0,A.jsx)(x,{width:50,inline:!0}):f({date:g,options:{monthAndYear:!0}})]}),(0,A.jsxs)(w,{top:!0,children:[e.twitter_handle?(0,A.jsx)(m,{to:`https://x.com/${e.twitter_handle}`,className:`margin-5--left margin-5--right spec-twitter-handle`,external:!0,target:`_blank`,children:(0,A.jsx)(`img`,{className:`better-avatar no-border-tiny`,src:_,alt:`X`})}):null,e.github_handle&&(0,A.jsx)(m,{to:`https://github.com/${e.github_handle}`,className:`margin-5--left margin-5--right spec-github-handle`,external:!0,target:`_blank`,children:(0,A.jsx)(`img`,{className:`better-avatar no-border-tiny`,src:`data:image/png;base64,iVBORw0KGgoAAAANSUhEUgAAACAAAAAgCAYAAABzenr0AAAAGXRFWHRTb2Z0d2FyZQBBZG9iZSBJbWFnZVJlYWR5ccllPAAAAyRpVFh0WE1MOmNvbS5hZG9iZS54bXAAAAAAADw/eHBhY2tldCBiZWdpbj0i77u/IiBpZD0iVzVNME1wQ2VoaUh6cmVTek5UY3prYzlkIj8+IDx4OnhtcG1ldGEgeG1sbnM6eD0iYWRvYmU6bnM6bWV0YS8iIHg6eG1wdGs9IkFkb2JlIFhNUCBDb3JlIDUuMy1jMDExIDY2LjE0NTY2MSwgMjAxMi8wMi8wNi0xNDo1NjoyNyAgICAgICAgIj4gPHJkZjpSREYgeG1sbnM6cmRmPSJodHRwOi8vd3d3LnczLm9yZy8xOTk5LzAyLzIyLXJkZi1zeW50YXgtbnMjIj4gPHJkZjpEZXNjcmlwdGlvbiByZGY6YWJvdXQ9IiIgeG1sbnM6eG1wPSJodHRwOi8vbnMuYWRvYmUuY29tL3hhcC8xLjAvIiB4bWxuczp4bXBNTT0iaHR0cDovL25zLmFkb2JlLmNvbS94YXAvMS4wL21tLyIgeG1sbnM6c3RSZWY9Imh0dHA6Ly9ucy5hZG9iZS5jb20veGFwLzEuMC9zVHlwZS9SZXNvdXJjZVJlZiMiIHhtcDpDcmVhdG9yVG9vbD0iQWRvYmUgUGhvdG9zaG9wIENTNiAoTWFjaW50b3NoKSIgeG1wTU06SW5zdGFuY2VJRD0ieG1wLmlpZDpFNTE3OEEyQTk5QTAxMUUyOUExNUJDMTA0NkE4OTA0RCIgeG1wTU06RG9jdW1lbnRJRD0ieG1wLmRpZDpFNTE3OEEyQjk5QTAxMUUyOUExNUJDMTA0NkE4OTA0RCI+IDx4bXBNTTpEZXJpdmVkRnJvbSBzdFJlZjppbnN0YW5jZUlEPSJ4bXAuaWlkOkU1MTc4QTI4OTlBMDExRTI5QTE1QkMxMDQ2QTg5MDREIiBzdFJlZjpkb2N1bWVudElEPSJ4bXAuZGlkOkU1MTc4QTI5OTlBMDExRTI5QTE1QkMxMDQ2QTg5MDREIi8+IDwvcmRmOkRlc2NyaXB0aW9uPiA8L3JkZjpSREY+IDwveDp4bXBtZXRhPiA8P3hwYWNrZXQgZW5kPSJyIj8+m4QGuQAAAyRJREFUeNrEl21ojWEYx895TDPbMNlBK46IUiNmPvHBSUjaqc0H8pF5+aDUKPEBqU2NhRQpX5Rv5jWlDIWlMCv7MMSWsWwmb3tpXub4XXWdPHvc9/Gc41nu+nedc7/8r/99PffLdYdDPsvkwsgkTBwsA/PADJCnzX2gHTwBt8Hl7p537/3whn04XoDZDcpBlk+9P8AFcAghzRkJwPF4zGGw0Y9QS0mAM2AnQj77FqCzrtcwB1Hk81SYojHK4DyGuQ6mhIIrBWB9Xm7ug/6B/nZrBHBegrkFxoVGpnwBMSLR9EcEcC4qb8pP14BWcBcUgewMnF3T34VqhWMFkThLJAalwnENOAKiHpJq1FZgI2AT6HZtuxZwR9GidSHtI30jOrbawxlVX78/AbNfhHlomEUJJI89O2MqeE79T8/nk8nMBm/dK576hZgmA3cp/R4l9/UeSxiHLVIlNm4nFfT0bxyuIj7LHRTKai+zdJobwMKzcZSJb0ePV5PKN+BqAAKE47UlMnERELMM3EdYP/yrd+XYb2mOiYBiQ8OQnoRBlXrl9JZix7D1pHTazu4MoyBcnYamqAjIMTR8G4FT8LuhLsexXYYjICBiqhQBvYb6fLZIJCjPypVvaOoVAW2WcasCnL2Nq82xHJNSqlCeFcDshaPK0twkAhosjZL31QYw+1rlMpWGMArl23SBsZZO58F2tlJXmjOXS+s4WGvpMiBJT/I2PInZ6lIs9/hBsNS1hS6BG0DSqmYEDRlCXQrmy50P1oDRKTSegmNbUsA0zDMwRhPJXeCE3vWLPQMvan6X8AgIa1vcR4AkGZkDR4ejJ1UHpsaVI0g2LInpOsNFUud1rhxSV+fzC9Woz2EZkWQuja7/B+jUrgtIMpy9YCW4n4K41YfzRneW5E1KJTe4B2Zq1Q5EHEtj4U3AfEzR5SVY4l7QYQPJdN2as7RKBF0BPZqqH4VgMAMBL8Byxr7y8zCZiDlnOcEKIPmUpgB5Z2ww5RdOiiRiNajUmWda5IG6WbhsyY2fx6m8gLcoJDJFkH219M3We1+cnda93pfycZpIJEL/s/wSYADmOAwAQgdpBAAAAABJRU5ErkJggg==`})}),e.gitlab_handle&&(0,A.jsx)(m,{to:`https://gitlab.com/${e.gitlab_handle}`,className:`margin-5--left margin-5--right spec-gitlab-handle`,external:!0,target:`_blank`,children:(0,A.jsx)(`img`,{className:`better-avatar no-border-tiny`,src:`/assets/static/gitlab-C1ljyPRY.png`})}),e.linkedin_handle&&(0,A.jsx)(m,{to:`https://www.linkedin.com/in/${e.linkedin_handle}`,className:`margin-5--left margin-5--right spec-linkedin-handle`,external:!0,target:`_blank`,children:(0,A.jsx)(`img`,{className:`better-avatar no-border-tiny`,src:`/assets/static/linkedin_blue-CHBsXBEb.png`})}),e.bugcrowd_handle&&(0,A.jsx)(m,{to:`https://bugcrowd.com/${e.bugcrowd_handle}`,className:`margin-5--left margin-5--right spec-bugcrowd-handle`,external:!0,target:`_blank`,children:(0,A.jsx)(`img`,{className:`better-avatar no-border-tiny`,src:`/assets/static/bugcrowd-D9l8cApy.png`})}),e.hack_the_box_handle&&(0,A.jsx)(m,{to:`https://app.hackthebox.com/users/${e.hack_the_box_handle}`,className:`margin-5--left margin-5--right spec-hack-the-box-handle`,external:!0,target:`_blank`,children:(0,A.jsx)(`img`,{className:`better-avatar no-border-tiny`,src:`/assets/static/hack_the_box-CTdXqIKM.png`})})]}),T&&(0,A.jsx)(w,{top:!0,children:I(t,a)})]})]})})};R.propTypes={user:O.default.shape({created_at:O.default.string,location:O.default.string,website:O.default.string,bio:O.default.string,name:O.default.string,username:O.default.string,profile_picture:O.default.string,cleared:O.default.bool,verified:O.default.bool,twitter_handle:O.default.string,github_handle:O.default.string,gitlab_handle:O.default.string,linkedin_handle:O.default.string,bugcrowd_handle:O.default.string,hack_the_box_handle:O.default.string,followed:O.default.bool,id:O.default.string,open_for_employment:O.default.bool,mark_as_company_on_leaderboards:O.default.bool}),me:O.default.object,idVerification:O.default.shape({status:O.default.string})},R.fragments={user:r`
    fragment UserProfileCardUser on User {
      id
      created_at
      location
      website
      bio
      name
      username
      profile_picture(size: large)
      bugcrowd_handle
      hack_the_box_handle
      github_handle
      gitlab_handle
      linkedin_handle
      twitter_handle
      cleared
      verified
      open_for_employment
      mark_as_company_on_leaderboards
      ...FollowUser
    }
    ${M.fragments.user}
  `,me:r`
    fragment UserProfileCardMe on User {
      id
    }
  `,id_verification:r`
    fragment UserProfileCardIdV on Query {
      id_verification {
        status
      }
    }
  `};export{L as n,F as r,R as t};
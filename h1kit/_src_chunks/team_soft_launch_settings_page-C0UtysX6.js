import{o as e}from"./rolldown-runtime-DAXXjFlN.js";import{$y as t,Ax as n,By as r,Ca as i,Fw as a,Hx as o,Iw as s,Kx as c,Ly as l,Nb as u,Pf as d,Qd as f,Qy as p,R_ as m,Rw as h,Ry as g,Ux as _,Vw as v,Vx as y,X_ as b,Y_ as x,Yf as S,Z_ as C,br as w,cd as T,cp as E,db as D,df as O,eb as k,jn as A,lp as j,ma as M,ov as ee,qx as N,sd as te,tb as P,zx as ne}from"./vendor-_WdvpBLr.js";import{Ah as re,Cp as F,Dh as I,Eh as L,Jc as R,Kf as z,Sm as B,T as ie,Th as V,Wt as ae,_h as H,dl as U,ep as W,ff as oe,gc as se,k as ce,nl as G,np as le,pm as K,qr as ue,vh as q,vm as J,w as de,ym as fe}from"./app-5pKgUmmm.js";import{t as pe}from"./user-D5NR1HRB.js";var Y=e(ne()),X=e(h());N();var Z=a(),me=c`
  mutation UpdateTeamSuccessGoalsMutation(
    $teamId: ID!
    $goalValidReports: Int!
  ) {
    updateTeamSuccessGoals(
      input: { team_id: $teamId, goal_valid_reports: $goalValidReports }
    ) {
      team {
        id
      }
      was_successful
      errors {
        edges {
          node {
            id
            type
          }
        }
      }
    }
  }
`,he=c`
  query ReportVolumeSetting($handle: String!) {
    team(handle: $handle) {
      id
      handle
      goal_valid_reports
      has_enabled_invites
    }
  }
`,ge=({handle:e})=>{let[t,n]=(0,X.useState)(0),{data:i,loading:a}=q(he,{variables:{handle:e},onCompleted:({team:{goal_valid_reports:e}})=>{n(e)}}),[o]=H(me,{onCompleted:({updateTeamSuccessGoals:e})=>{e.was_successful?fe():B(`errors`,se(e.errors))}}),s=()=>(0,Z.jsxs)(Z.Fragment,{children:[(0,Z.jsx)(l,{variation:r.Error,contentPrimary:`Your Invitations setting is turned off`,contentSecondary:(0,Z.jsxs)(Z.Fragment,{children:[(0,Z.jsx)(`a`,{href:window.constants.notification.support_link,children:`Contact us`}),` `,`if you would like to turn it on.`]})}),(0,Z.jsx)(u,{vertical:`32`})]});if(a)return(0,Z.jsx)(I,{});let{team:c}=i,d=e=>!e.toString().match(/[0-9]*/)||parseInt(e,10)<0,f=d(t)||t===``,m=e=>{e.preventDefault(),o({variables:{teamId:c.id,goalValidReports:parseInt(t,10)}})};return(0,Z.jsx)(`div`,{children:(0,Z.jsxs)(`div`,{className:`flex flex-col`,children:[(0,Z.jsxs)(`div`,{children:[(0,Z.jsx)(`p`,{children:`Enable HackerOne to manage your hacker invitations so that you can ensure engagement of hackers and meet your target report volume. We steadily issue invitations to hackers who meet the following criteria within the last 90 days:`}),(0,Z.jsx)(u,{vertical:`16`}),(0,Z.jsxs)(`ul`,{className:`list`,children:[(0,Z.jsx)(`li`,{children:`Established reputation`}),(0,Z.jsx)(`li`,{children:`Positive signal`}),(0,Z.jsx)(`li`,{children:`Clear record with zero code of conduct violations`})]})]}),(0,Z.jsx)(u,{vertical:`40`}),c.has_enabled_invites?null:s(),(0,Z.jsxs)(`div`,{className:`flex`,children:[(0,Z.jsx)(`strong`,{children:`Report volume`}),(0,Z.jsx)(u,{horizontal:`12`}),(0,Z.jsx)(D,{text:`We’ll automatically adjust how many invitations are sent based on your monthly report volume and pause them when you meet your target.`,children:`[?]`})]}),(0,Z.jsx)(u,{vertical:`16`}),(0,Z.jsxs)(`p`,{className:`text-neutral-300 dark:text-neutral-800`,children:[`If this is set to 0, no invites will be sent for your program. We recommend starting out your report volume with 5 valid reports. Learn more`,` `,(0,Z.jsx)(`a`,{className:`daisy-text--blue`,href:`https://docs.hackerone.com/organizations/invitations.html`,children:`here`}),`.`]}),(0,Z.jsx)(u,{vertical:`32`}),(0,Z.jsxs)(`div`,{className:`flex gap-md`,children:[(0,Z.jsx)(`div`,{className:`w-[120px]`,children:(0,Z.jsx)(S,{type:`number`,value:t,invalid:d(t),onChange:e=>n(e.target.value),required:!0,testId:`spec-team-goal-valid-reports`})}),(0,Z.jsx)(p,{variation:`secondary`,className:`spec-team-valid-reports-goal-save`,onClick:e=>m(e),testId:`spec-save-team-goal-valid-reports`,disabled:f,children:`Save`})]}),d(t)&&(0,Z.jsxs)(`div`,{children:[(0,Z.jsx)(u,{vertical:`8`}),(0,Z.jsx)(b,{variation:C.Danger,children:`Report volume can not be less than 0`})]})]})})};ge.propTypes={handle:Y.default.string.isRequired};var _e=F(`
  mutation RemoveHackerFromProgram(
    $team_handle: String!
    $username: String!
    $reason: String!
  ) {
    removeHackerFromProgram(
      input: { team_handle: $team_handle, username: $username, reason: $reason }
    ) {
      was_successful
    }
  }
`),Q=`Other`,ve=[{label:`The user is no longer providing value to my program`,id:`no-value`},{label:`The user is no longer complying with the program rules`,id:`no-comply`},{label:`The user was accidentally invited to the program`,id:`accidental`},{label:Q,id:`other`}],ye=({username:e,teamHandle:t,toggleModal:n,onHackerRemoved:i})=>{let[a,o]=(0,X.useState)(),[s,c]=(0,X.useState)(),[l,{loading:u}]=y(_e,{variables:{username:e,reason:(a===Q?s:a)??``,team_handle:t},onError:e=>{J()},onCompleted:({removeHackerFromProgram:{was_successful:e}})=>{e?i():J()}}),d=()=>{l()},f=a===Q&&!s||!a;return(0,Z.jsx)(W,{type:`info`,shouldCloseOnEsc:!0,showModal:!0,title:`Remove hacker from your program`,size:`medium`,handleCloseModal:()=>{n()},children:(0,Z.jsxs)(`div`,{className:`flex flex-col gap-lg`,children:[(0,Z.jsxs)(`p`,{children:[`Please provide a reason for removing`,` `,(0,Z.jsx)(`a`,{href:`/${e}`,children:e}),` from your program. This reason will be included in the removal email and visible to HackerOne.`]}),(0,Z.jsx)(g,{variation:r.Warning,contentPrimary:`The hacker will still be able to manage past reports and can be reinvited to
          the program later. To ban them permanently, contact your CSM or Support.`}),(0,Z.jsxs)(`div`,{className:`flex flex-col gap-xs`,children:[ve.map(({label:e,id:t},n)=>(0,Z.jsx)(m,{checked:a===e,name:`reason`,accessibilityLabel:e,label:e,onChange:()=>{o(e)},testId:`reason-${t}`},n)),(0,Z.jsx)(S,{name:`other-reason`,onChange:e=>{c(e.target.value)},disabled:a!==Q,placeholder:`Please state a reason`})]}),(0,Z.jsxs)(`div`,{className:`flex flex-row gap-sm justify-end`,children:[(0,Z.jsx)(p,{variation:P.Tertiary,onClick:n,children:`Cancel`}),(0,Z.jsx)(p,{disabled:u||f,variation:P.Danger,onClick:d,children:`Remove`})]})]})})},be=({teamHandle:e})=>(0,Z.jsx)(p,{renderAs:k.Link,download:!0,external:!0,to:`/${e}/whitelisted_reporters.csv`,children:`Export CSV`});N();var xe=c`
  query SoftLaunchActiveResearchersQuery($handle: String!, $cursor: String) {
    team(handle: $handle) {
      id
      whitelisted_reporter_rows(first: 250, after: $cursor) {
        pageInfo {
          startCursor
          endCursor
          hasNextPage
          hasPreviousPage
        }
        edges {
          node {
            id
            created_at
            user {
              id
              profile_picture(size: small)
              username
              url
              cleared
            }
          }
        }
        total_count
      }
    }
  }
`,Se=({handle:e})=>{let[t,n]=(0,X.useState)(),{data:r,loading:i,fetchMore:a,refetch:o,error:s}=q(xe,{variables:{handle:e},onError:()=>{J()}}),c=()=>{n(null)},l=()=>{c(),o()};if(i)return(0,Z.jsx)(V,{});if(s)return(0,Z.jsx)(Z.Fragment,{});let d=U(r,`team.whitelisted_reporter_rows`,a),{whitelisted_reporter_rows:f}=r.team;return(0,Z.jsxs)(`div`,{children:[(0,Z.jsxs)(`div`,{className:`flex justify-between`,children:[(0,Z.jsxs)(`div`,{children:[(0,Z.jsx)(`span`,{children:(0,Z.jsxs)(`strong`,{children:[`Hackers in your program (`,f.total_count,`)`]})}),(0,Z.jsx)(u,{vertical:`5`}),(0,Z.jsx)(`p`,{className:`text-neutral-300 dark:text-neutral-800`,children:`These hackers have joined your program and can submit reports.`})]}),(0,Z.jsx)(be,{teamHandle:e})]}),(0,Z.jsx)(u,{vertical:`12`}),(0,Z.jsx)(`div`,{id:`whitelisted-reporters-container`,className:`max-h-[400px] overflow-y-auto`,children:(0,Z.jsxs)(A,{dataLength:f?.edges.length,next:d,hasMore:f?.pageInfo.hasNextPage,loader:(0,Z.jsx)(L,{}),scrollableTarget:`whitelisted-reporters-container`,children:[t&&(0,Z.jsx)(ye,{teamHandle:e,username:t,toggleModal:c,onHackerRemoved:l}),f?.edges.map(({node:e,node:{user:t}},r)=>(0,Z.jsxs)(`div`,{children:[(0,Z.jsxs)(`div`,{className:`flex items-center`,children:[(0,Z.jsxs)(`div`,{className:`flex-1 flex gap-sm items-center`,children:[(0,Z.jsx)(K,{size:`medium`,className:`user-item__avatar`,cleared:t.cleared,verified:t.verified,src:t.profile_picture,username:t.username,object:t}),(0,Z.jsx)(G,{label:t.username,username:t.username})]}),(0,Z.jsxs)(`div`,{className:`flex-1`,children:[`Joined on `,z({date:e.created_at})]}),(0,Z.jsx)(p,{className:`flex-none`,iconOnly:!0,icons:{center:{accessibilityLabel:`Remove ${t.username}`,src:w}},onClick:()=>n(t.username),variation:`ghost-secondary`})]}),(0,Z.jsx)(O,{variation:`light`})]},r))]})})]})};Se.propTypes={handle:Y.default.string.isRequired},N();var Ce=c`
  mutation RequestTeamReviewMutation($team_id: ID!) {
    requestTeamReview(input: { team_id: $team_id }) {
      was_successful
    }
  }
`,we=({teamId:e,teamState:t,changeIsPendingReview:n,changeIsReviewRejected:i,toggleShowPendingReviewModal:a})=>{let[o,s]=(0,X.useState)(!1),[c]=H(Ce,{variables:{team_id:e},onError(){J()},onCompleted({requestTeamReview:{was_successful:e}}){e?(n(!0),i(!1),a()):J()}});return(0,Z.jsxs)(`div`,{children:[(0,Z.jsxs)(E,{children:[(0,Z.jsx)(j,{children:`Private program`}),(0,Z.jsx)(O,{}),(0,Z.jsxs)(j,{children:[(0,Z.jsxs)(`div`,{children:[`To ensure a steady flow of reports, we recommend inviting a small number of hackers on an on-going basis using`,` `,(0,Z.jsx)(`a`,{className:`daisy-text--blue`,href:`https://docs.hackerone.com/organizations/invitations.html`,children:`invitations`}),`. If you receive more than 5`,` `,(0,Z.jsx)(D,{text:`Valid reports only include reports marked as Triaged or Resolved.`,children:(0,Z.jsx)(`span`,{className:`underline`,children:`valid reports`})}),` `,`in a 30 day period, we'll pause hacker invitations so you can catch your breath.`]}),(0,Z.jsx)(u,{vertical:`24`}),(0,Z.jsx)(p,{onClick:()=>s(!0),children:`Request Review`})]})]}),(0,Z.jsxs)(W,{type:`info`,shouldCloseOnEsc:!0,title:`Inviting Hackers`,showModal:o,size:`medium`,handleCloseModal:()=>s(!1),className:`spec-request-review-modal`,children:[(0,Z.jsxs)(`ul`,{className:`list`,children:[(0,Z.jsx)(`li`,{children:`Your program is pending verification and approval.`}),(0,Z.jsx)(`li`,{children:`Once approved, the first 5 hackers will be automatically invited to your private program`}),(0,Z.jsxs)(`li`,{children:[`Hackers are continuously invited to maintain a steady and manageable number of reports. You can pause`,` `,(0,Z.jsx)(`a`,{className:`daisy-text--blue`,href:`https://docs.hackerone.com/organizations/invitations.html`,children:`invitations`}),` `,`at any time.`]})]}),t!==`da_mode`&&(0,Z.jsx)(g,{variation:r.Warning,contentPrimary:`Sample reports will be removed after inviting your first hackers.`}),(0,Z.jsx)(u,{vertical:`24`}),(0,Z.jsxs)(`div`,{className:`flex justify-end`,children:[(0,Z.jsx)(p,{variation:`tertiary`,onClick:()=>s(!1),children:`Cancel`}),(0,Z.jsx)(u,{horizontal:`8`}),(0,Z.jsx)(p,{onClick:()=>{s(!1),c()},children:`Launch`})]})]})]})};we.propTypes={teamId:Y.default.string.isRequired,teamState:Y.default.string.isRequired,changeIsPendingReview:Y.default.func.isRequired,changeIsReviewRejected:Y.default.func.isRequired,toggleShowPendingReviewModal:Y.default.func.isRequired};var Te=`/assets/static/potentialvolume-tWu48pnl.jpg`,Ee=F(`
  query ShowTeamPosts($handle: String!) {
    team(handle: $handle) {
      id
      handle
      team_display_options {
        id
        show_private_team_posts
      }
    }
  }
`),De=F(`
  mutation UpdateTeamDisplayOptions(
    $team_id: ID!
    $show_private_team_posts: Boolean
  ) {
    updateTeamDisplayOptions(
      input: {
        team_id: $team_id
        show_private_team_posts: $show_private_team_posts
      }
    ) {
      was_successful
      errors(first: 100) {
        edges {
          node {
            id
            field
            message
            type
          }
        }
      }
      team_display_options {
        id
        show_private_team_posts
      }
    }
  }
`),Oe=F(`
  query BountyTableRecommendation($handle: String!) {
    team(handle: $handle) {
      id
      handle
      type
      bounty_table {
        id
      }
    }
  }
`),ke=R,Ae=({team:e,onCancel:n,hasExternalProgram:r,tooFewResearchers:i,tooManyOpenReports:a,launchPolicy:o})=>{let[s,c]=(0,X.useState)(!1),[l,u]=(0,X.useState)(!i),[d,f]=(0,X.useState)(!a),[m,h]=(0,X.useState)(!1),[g,v]=(0,X.useState)(()=>o??e.policy),[b,x]=(0,X.useState)(!1),[S,C]=(0,X.useState)(!1),{data:w}=_(Ee,{variables:{handle:e.handle}});(0,X.useEffect)(()=>{w&&h(w?.team?.team_display_options?.show_private_team_posts??!1)},[w]);let T=()=>{c(!s)},E=()=>{u(!l)},D=()=>{f(!d)},O=e=>{v(e)},k=()=>{h(!m)},[A,{loading:j}]=y(De,{onCompleted:e=>{e?.updateTeamDisplayOptions?.was_successful?fe():J()}});return j?(0,Z.jsx)(V,{}):S?(0,Z.jsx)(je,{handle:e.handle}):(0,Z.jsxs)(`div`,{className:`pt-sm spec-public-launch-checklist`,children:[(0,Z.jsx)(`a`,{onClick:n,children:`<< Back to Invitations`}),(0,Z.jsx)(`br`,{}),(0,Z.jsx)(`h2`,{children:`Public Launch`}),(0,Z.jsx)(`p`,{children:`Your private program is visible only to hackers you have invited. Launching your program publicly exposes your program to thousands of hackers. Report volume will spike dramatically on launch.`}),(0,Z.jsx)(`img`,{src:Te}),r&&(0,Z.jsx)(Me,{policy:g??``,onChange:O}),i&&(0,Z.jsx)(Ne,{agreed:l,onChange:E}),a&&(0,Z.jsx)(Pe,{agreed:d,onChange:D}),(0,Z.jsx)(Fe,{agreed:s,onChange:T}),(0,Z.jsx)(Le,{handle:e.handle}),(0,Z.jsx)(Re,{agreed:m,onChange:k}),(0,Z.jsxs)(`div`,{className:`flex justify-end gap-md mt-md pull-right`,children:[(0,Z.jsx)(p,{variation:P.Secondary,onClick:n,testId:`cancel-public-launch`,children:`Cancel`}),(0,Z.jsx)(p,{variation:P.Primary,onClick:t=>{if(!(s&&l&&d))return;t.preventDefault(),x(!0);let n={policy:g};fetch(`/${e.handle}/publish`,{method:`POST`,headers:{...ae(),"Content-Type":`application/json`,Accept:`application/json`},body:JSON.stringify(n)}).then(async t=>{if(t.ok)A({variables:{team_id:e.id,show_private_team_posts:m}}).then(()=>{x(!1),C(!0)}).catch(e=>{x(!1),e()});else if(t.status===422){let e=await t.json();B(`error`,e.error||e.errors?.join(`, `)||`Could not publish program`),x(!1)}else throw Error(`HTTP error! status: ${t.status}`)}).catch(()=>{B(`error`,`Something went wrong while publishing your team. Please contact
          ${window.constants.notification.support_link} if the problem persists.`),x(!1)})},type:t.Submit,testId:`submit-public-launch`,disabled:s&&l&&d?b:!0,children:`Launch Program`})]})]})},je=({handle:e})=>(0,Z.jsx)(de,{title:`Your program is now publicly accessible!`,narrowContainer:!1,children:(0,Z.jsxs)(`div`,{className:`spec-publish-success`,children:[(0,Z.jsxs)(`p`,{children:[`Expect to see more `,(0,Z.jsx)(`a`,{href:`/bugs`,children:`reports`}),` soon!`,(0,Z.jsx)(`br`,{}),`Feel free to`,` `,(0,Z.jsx)(`a`,{href:window.constants.notification.support_link,children:`contact us`}),` if you have any questions.`]}),(0,Z.jsxs)(`div`,{children:[(0,Z.jsx)(`a`,{href:`/bugs`,children:` Go to Inbox `}),` - or -`,` `,(0,Z.jsx)(`a`,{href:`/${e}`,children:` View Security Page `})]})]})}),Me=({policy:e,onChange:t})=>(0,Z.jsxs)(`div`,{className:`mt-sm mb-sm`,children:[(0,Z.jsx)(`h2`,{children:`Review your policy`}),(0,Z.jsx)(`p`,{children:`Your directory listing policy and private program policy have been merged. Please review and edit as necessary.`}),(0,Z.jsx)(`div`,{className:`input-wrapper`,children:(0,Z.jsx)(ke,{textareaId:`spec-text-area`,name:`team_policy`,minimumHeight:100,initialValue:e,onChange:t})})]}),Ne=({agreed:e,onChange:t})=>(0,Z.jsx)(`div`,{className:`mt-sm`,children:(0,Z.jsxs)(`div`,{className:`alert alert--error`,children:[`You have invited less than 100 hackers to your private program. We strongly recommend inviting more hackers to your private program before launching publicly.`,(0,Z.jsx)(`br`,{}),(0,Z.jsx)(x,{testId:`spec-too-few-hackers`,id:`too-few-hackers`,checked:e,onChange:t,label:`I understand and still want to launch publicly.`})]})}),Pe=({agreed:e,onChange:t})=>(0,Z.jsx)(`div`,{className:`mt-sm`,children:(0,Z.jsxs)(`div`,{className:`alert alert--error`,children:[`You have 10 or more reports that are still open. We recommend managing your open reports before launching publicly.`,(0,Z.jsx)(`br`,{}),(0,Z.jsx)(x,{testId:`spec-too-many-reports`,id:`too-many-reports`,checked:e,onChange:t,label:`I understand and still want to launch publicly.`})]})}),Fe=({agreed:e,onChange:t})=>(0,Z.jsx)(`div`,{className:`mt-sm`,children:(0,Z.jsxs)(`div`,{className:`alert alert--warning`,children:[`You will receive as many as 200 reports in the first week after which volume will subside. Reverting to private is not easily executed and negatively affects hackers.`,(0,Z.jsx)(`br`,{}),(0,Z.jsx)(x,{testId:`spec-agree-to-publish`,id:`agree`,checked:e,onChange:t,label:`I understand and still want to launch publicly.`})]})}),Ie=({handle:e,bountyTable:t,type:n})=>!n?.includes(`BugBountyProgram`)||t!==null?null:(0,Z.jsx)(`div`,{className:`mt-sm`,children:(0,Z.jsxs)(`div`,{className:`inline-banner`,children:[`You haven't configured a bounty table yet. A Bounty table helps set expectations for hackers and gives your bug bounty team a guideline to ensure fair and consistent reward amounts. You can create one by going to `,(0,Z.jsx)(`a`,{href:`/${e}/reward_settings`,children:`reward settings`}),`.`]})}),Le=({handle:e})=>{let{data:t,loading:n}=_(Oe,{variables:{handle:e}});return n?(0,Z.jsx)(V,{}):(0,Z.jsx)(Ie,{handle:e,type:t?.team?.type??``,bountyTable:t?.team?.bounty_table})},Re=({agreed:e,onChange:t})=>(0,Z.jsx)(`div`,{className:`mt-sm`,children:(0,Z.jsx)(x,{testId:`spec-agree-to-show-private-opportunities`,id:`agree`,checked:!e,onChange:t,label:`Hide updates from when the program was private.`})}),ze=({isPendingReview:e,teamState:t})=>e?null:t===`sandboxed`?(0,Z.jsxs)(`div`,{className:`flex flex-col`,children:[(0,Z.jsxs)(E,{children:[(0,Z.jsx)(j,{children:`Public program`}),(0,Z.jsx)(O,{}),(0,Z.jsx)(j,{children:(0,Z.jsxs)(`div`,{children:[`Volume may increase significantly with a public launch. We recommend you enable Invitations while keeping your program private until you have invited at least 100 hackers. If you want to launch publicly immediately, please`,` `,(0,Z.jsx)(`a`,{className:`daisy-text--blue`,href:`mailto:sales@hackerone.com`,children:`contact us`}),`.`]})})]}),(0,Z.jsx)(u,{vertical:`24`})]}):(0,Z.jsxs)(`div`,{className:`flex flex-col`,children:[(0,Z.jsxs)(`h4`,{className:`text-xl`,children:[`Ready to`,` `,(0,Z.jsx)(`a`,{className:`daisy-text--blue`,href:`public_launch`,children:`open your program`}),` `,`to the public?`]}),(0,Z.jsx)(u,{vertical:`24`})]});ze.propTypes={isPendingReview:Y.default.bool.isRequired,teamState:Y.default.string.isRequired};var Be=({isPendingReview:e,isReviewRejected:t})=>e===!1||t===!0?null:(0,Z.jsxs)(`div`,{style:{textAlign:`center`},children:[(0,Z.jsxs)(`div`,{children:[`Your `,(0,Z.jsx)(`strong`,{children:`private program`}),` is pending approval and will be reviewed within 5 business days.`]}),(0,Z.jsx)(`div`,{children:`Once approved, hackers will automatically be invited to your program.`}),(0,Z.jsx)(u,{vertical:`40`})]});Be.propTypes={isPendingReview:Y.default.bool.isRequired,isReviewRejected:Y.default.bool.isRequired};var Ve=window.constants.notification.support_link,He=({isReviewRejected:e})=>e===!1?null:(0,Z.jsxs)(Z.Fragment,{children:[(0,Z.jsxs)(`div`,{style:{textAlign:`center`},className:`text-neutral-400 dark:text-neutral-950`,children:[`A few items have prevented your `,(0,Z.jsx)(`strong`,{children:`private`}),` program from being validated at this time. Please reach out to`,` `,(0,Z.jsx)(`a`,{className:`daisy-text--blue`,href:Ve,children:Ve}),` `,`if you haven't received a message with next steps.`]}),(0,Z.jsx)(u,{vertical:`40`})]});He.propTypes={isReviewRejected:Y.default.bool.isRequired},N();var Ue=e(s()),We=c`
  query UsernameCheckHackerInvitation($username: String!) {
    users(where: { username: { _eq: $username } }) {
      edges {
        node {
          username
          cleared
        }
      }
    }
  }
`,{CLEAR_VOUCHER:Ge}=window.constants.featureToggles,Ke=({hackers:e,nonClearHackers:t,addHacker:n,removeHacker:r,hackersMissing:a,ineligibleHackers:s,clearProgram:c,addNonClearHacker:f,removeNonClearHacker:m,handle:h})=>{let[g,_]=(0,X.useState)(!1),[v,y]=(0,X.useState)(!1),{enabled:b}=oe(Ge,h),[x,{loading:S,data:C}]=o(We,{onCompleted:()=>{C.users.edges.length>0?(b&&c&&!C.users.edges[0].node.cleared?f(C.users.edges[0].node.username):n(C.users.edges[0].node.username),_(!1)):_(!0)},onError:()=>{J()}}),w=t=>!!(t.length<=0||t.length>255||e.includes(t)),E=e=>!s.includes(e),O=e=>{e.preventDefault();let t=e.target.querySelector(`input[name="add-hacker-text-field"]`),r=t.value;w(r)||(r.match(/.+@.+\..+/)?(n(r),_(!1)):x({variables:{username:r?.toLowerCase()}}),t.value=``)},k=e.length===0&&(g||a)&&!v;return(0,Z.jsxs)(`div`,{children:[(0,Z.jsxs)(`form`,{onSubmit:O,children:[(0,Z.jsx)(`h3`,{className:`text-base`,children:`Email or username*`}),(0,Z.jsx)(u,{vertical:`8`}),(0,Z.jsx)(`p`,{className:`text-base text-neutral-200 dark:text-neutral-950`,children:`Want to invite specific hackers? Enter the email or username here.`}),(0,Z.jsxs)(`div`,{className:`flex`,children:[(0,Z.jsx)(`div`,{className:`grow`,children:(0,Z.jsx)(i,{id:`add-hackers-input`,name:`add-hacker-text-field`,label:`add hackers`,placeholder:`Add a hacker`,testId:`spec-hacker-invitation-input`,invalid:k,validationChildren:g&&`Could not find username`,validationVariation:g?`danger`:`default`,onFocus:()=>y(!0),onBlur:()=>y(!1)})}),(0,Z.jsx)(u,{horizontal:`12`}),(0,Z.jsx)(p,{icons:{left:{src:T,accessibilityLabel:`Add a hacker`}},loading:S,children:`Add`})]})]}),(0,Z.jsxs)(`div`,{className:`flex flex-col gap-sm`,children:[(e.length>0||t.length>0)&&(0,Z.jsxs)(`ul`,{className:(0,Ue.default)(`flex flex-wrap gap-xs mt-sm`),children:[e.map(e=>(0,Z.jsx)(`li`,{children:(0,Z.jsx)(d,{rounded:!1,dismissable:!0,dismissAccessibilityLabel:`Remove a hacker`,color:E(e)?`blue`:`red`,onDismiss:()=>{r(e)},children:e})},e)),t.map(e=>(0,Z.jsx)(`li`,{children:(0,Z.jsx)(D,{text:`This hacker is not Clear-verified`,children:(0,Z.jsx)(d,{rounded:!1,dismissable:!0,dismissAccessibilityLabel:`Remove a hacker`,color:E(e)?`yellow`:`red`,onDismiss:()=>{m(e)},children:e})})},e))]}),t.length>0&&(0,Z.jsx)(l,{variation:`warning`,contentSecondary:`Some listed hackers lack Clear status. Inviting them will start the Clear process, and they can join your program once complete. `})]})]})};Ke.propTypes={hackers:Y.default.array.isRequired,addHacker:Y.default.func.isRequired,removeHacker:Y.default.func.isRequired,hackersMissing:Y.default.bool,ineligibleHackers:Y.default.array,nonClearHackers:Y.default.array.isRequired,clearProgram:Y.default.bool.isRequired,addNonClearHacker:Y.default.func.isRequired,removeNonClearHacker:Y.default.func.isRequired,handle:Y.default.string.isRequired};var qe=({teamName:e,teamHandle:t,messageType:n,changeMessageType:r,message:i,changeMessage:a,messageMissing:o})=>{let s=`invitation_message`,[c,l]=(0,X.useState)(!1);(0,X.useEffect)(()=>{let e=()=>{let e=document.getElementById(s);e&&e===document.activeElement?l(!0):l(!1)};return document.addEventListener(`focusin`,e),()=>{document.removeEventListener(`focusin`,e)}},[s]);let d=n=>{n.target.value===$.GENERIC?(r($.GENERIC),a(`You've been invited to a **private** program by [${e}](https://hackerone.com/${t})`)):(r($.PERSONALIZED),a(``))},f=n===$.GENERIC;return(0,Z.jsxs)(`div`,{children:[(0,Z.jsx)(`h3`,{className:`text-base`,children:`Message*`}),(0,Z.jsx)(u,{vertical:`12`}),(0,Z.jsxs)(`div`,{className:`flex`,children:[(0,Z.jsx)(`span`,{children:(0,Z.jsx)(m,{label:$.PERSONALIZED,value:$.PERSONALIZED,checked:n===$.PERSONALIZED,onChange:d,testId:`spec-personalized-radio-button`})}),(0,Z.jsx)(u,{horizontal:`40`}),(0,Z.jsx)(`span`,{children:(0,Z.jsx)(m,{label:$.GENERIC,value:$.GENERIC,checked:n===$.GENERIC,onChange:d,testId:`spec-generic-radio-button`})})]}),(0,Z.jsx)(u,{vertical:`12`}),(0,Z.jsx)(R,{textareaId:s,minimumHeight:100,onChange:e=>a(e),readOnly:f,value:i,name:`message`,errors:i.length===0&&!c&&o?[``]:[],showPreview:!0,placeholder:`Add a personalized message and increase your chances of acceptance`})]})};qe.propTypes={teamName:Y.default.string.isRequired,teamHandle:Y.default.string.isRequired,messageType:Y.default.string.isRequired,changeMessageType:Y.default.func.isRequired,message:Y.default.string.isRequired,changeMessage:Y.default.func.isRequired,messageMissing:Y.default.bool};var Je={label:`Just getting started`,value:`Just getting started`},Ye=[{label:`Hacker and Program representative met offline and agreed to work together`,value:`Hacker and Program representative`},{label:`Hacker has a ready submission for my program`,value:`Submission ready`},Je,{label:`Other`,value:`Other`}],Xe=({context:e,changeContext:t,otherContext:n,changeOtherContext:r,contextMessageMissing:i,gettingStarted:a})=>{let[o,s]=(0,X.useState)(!1),c=i&&n.length===0&&!o;return(0,Z.jsxs)(`div`,{children:[(0,Z.jsx)(`h3`,{className:`text-base`,children:`Context*`}),(0,Z.jsx)(`p`,{className:`text-base text-neutral-200 dark:text-neutral-950`,children:`Help us improve invitation workflows with some context. Why are you inviting this hacker(s)? Your answer is confidential and won't be shared.`}),(0,Z.jsx)(te,{id:`invitation-context-dropdown`,options:Ye,placeholder:`Select an option`,onChange:e=>{t(e.label)},defaultValue:a?Je:void 0,testId:`hacker-invitation-context-input`}),(0,Z.jsx)(u,{vertical:`16`}),e===`Other`&&(0,Z.jsxs)(Z.Fragment,{children:[(0,Z.jsx)(M,{name:`other context`,label:`Other Context`,placeholder:`type something here`,value:n,onChange:e=>r(e.target.value),invalid:c,testId:`hacker-invitation-context-message-input`,onFocus:()=>s(!0),onBlur:()=>s(!1)}),(0,Z.jsx)(u,{vertical:`16`})]})]})};Xe.propTypes={context:Y.default.string.isRequired,changeContext:Y.default.func.isRequired,otherContext:Y.default.string.isRequired,changeOtherContext:Y.default.func.isRequired,contextMissing:Y.default.bool,contextMessageMissing:Y.default.bool,gettingStarted:Y.default.bool};var Ze=({validationErrors:e,eligibilityErrors:t})=>(0,Z.jsx)(l,{variation:r.Error,contentPrimary:(0,Z.jsxs)(`div`,{children:[(0,Z.jsx)(`span`,{className:`text-neutral-300 text-base dark:text-neutral-800`,children:`Please correct the following errors:`}),(0,Z.jsx)(u,{vertical:`8`}),e.length>0&&(0,Z.jsx)(`ul`,{className:`list-disc pl-md`,children:e.map((e,t)=>(0,Z.jsx)(`li`,{children:e},t))}),t.length>0&&(0,Z.jsx)(`ul`,{className:`list-disc pl-md`,children:t.map((e,t)=>(0,Z.jsxs)(`li`,{children:[e.user,(0,Z.jsx)(`ul`,{className:`list-inside list-disc`,children:e.reasons.map((e,t)=>(0,Z.jsx)(`li`,{children:e},t))})]},t))})]})});Ze.propTypes={validationErrors:Y.default.array.isRequired,eligibilityErrors:Y.default.array.isRequired},N();var $={PERSONALIZED:`Personalized`,GENERIC:`Generic`},Qe=({visible:e,toggleModal:t,teamId:n,teamHandle:r,teamName:i,firstTimeInvite:a,toggleShowPendingReviewModal:o,gettingStarted:s,clearProgram:l})=>{let[d,f]=(0,X.useState)([]),[p,m]=(0,X.useState)([]),[h,g]=(0,X.useState)($.PERSONALIZED),[_,v]=(0,X.useState)(``),y=s?Je.label:``,[b,S]=(0,X.useState)(y),[C,w]=(0,X.useState)(``),[T,E]=(0,X.useState)(!1),[D,O]=(0,X.useState)([]),[k,A]=(0,X.useState)([]),[j,M]=(0,X.useState)(!1),[ee,N]=(0,X.useState)(!1),[te,P]=(0,X.useState)(!1),[ne]=H(c`
    mutation InviteEligibleHackers(
      $team_id: ID!
      $usernames: [String!]!
      $email_addresses: [String!]!
      $context: String!
      $message: String!
      $bcc_me: Boolean
    ) {
      inviteEligibleHackers(
        input: {
          team_id: $team_id
          usernames: $usernames
          email_addresses: $email_addresses
          context: $context
          message: $message
          bcc_me: $bcc_me
        }
      ) {
        was_successful
        users_validation_result
        errors {
          edges {
            node {
              type
              field
              message
            }
          }
        }
      }
    }
  `,{refetchQueries:[`TeamInvitations`],onCompleted:({inviteEligibleHackers:e})=>{if(e.was_successful){let t=ce(e.users_validation_result);t.length===0?(I(),B(`notice`,`Your invitation has been sent.`),a&&o()):A(t)}else{let t=e.errors?.edges?.map(e=>e.node.message)||[];t.length>0?O(t):(I(),J())}},onError:()=>{I(),J()}}),re=()=>{f([]),g($.PERSONALIZED),v(``),S(y),w(``),E(!1),O([]),A([])},F=()=>{O([]),A([]),M(!1),N(!1),P(!1)},I=()=>{re(),t()},L=e=>{f([...d,e])},R=e=>{let t=[...d],n=t.indexOf(e);n>-1&&(t.splice(n,1),f(t))},z=e=>{let t=[...p],n=t.indexOf(e);n>-1&&(t.splice(n,1),m(t))},ie=e=>v(e),V=e=>g(e),ae=e=>S(e),U=e=>w(e),oe=()=>{let e=se();e.length===0&&ne({variables:{team_id:n,usernames:le(),email_addresses:G(),context:C||b,message:_,bcc_me:T}}),O(e)},se=()=>{F();let e=[];return d.length<=0&&p.length<=0&&(M(!0),e.push(`No hackers specified to invite.`)),h===$.PERSONALIZED&&_.length<=0&&(N(!0),e.push(`Required field "Message" is missing`)),b.length<=0&&e.push(`Required field "Context" is missing`),b===`Other`&&C.trim().length<=0&&(P(!0),e.push(`Please add what is the other reason for this invitation`)),e},ce=e=>e.filter(e=>e.reasons.length>0),G=()=>d.filter(e=>e.match(/.+@.+\..+/)),le=()=>[...d,...p].filter(e=>!e.match(/.+@.+\..+/)),K=D.length>0||k.length>0;return(0,Z.jsx)(W,{type:`info`,shouldCloseOnEsc:!0,shouldCloseOnOverlayClick:!1,title:`Invitations`,showModal:e,size:`medium`,handleCloseModal:I,className:`spec-hacker-invitation-modal`,buttonColor:`blue`,buttonSize:`medium`,cancelLinkText:`Cancel`,handleCancelLinkClick:I,buttonText:`Send invitation`,handleButtonClick:oe,children:(0,Z.jsxs)(u,{horizontal:`xs`,children:[(0,Z.jsx)(u,{vertical:`8`}),(0,Z.jsx)(Ke,{hackers:d,addHacker:L,removeHacker:R,hackersMissing:j,ineligibleHackers:k.map(e=>e.user),clearProgram:l,nonClearHackers:p,addNonClearHacker:e=>m(t=>[...t,e]),removeNonClearHacker:z,handle:r}),(0,Z.jsx)(u,{vertical:`32`}),(0,Z.jsx)(qe,{teamName:i,teamHandle:r,messageType:h,message:_,changeMessage:ie,changeMessageType:V,messageMissing:ee}),(0,Z.jsx)(u,{vertical:`40`}),(0,Z.jsx)(Xe,{context:b,otherContext:C,changeContext:ae,changeOtherContext:U,contextMessageMissing:te,gettingStarted:s}),(0,Z.jsx)(u,{vertical:`18`}),(0,Z.jsxs)(`div`,{className:`flex`,children:[(0,Z.jsx)(x,{id:`send-copy-checkbox`,checked:T,accessibilityLabel:`send copy`,onChange:()=>{E(!T)}}),(0,Z.jsx)(u,{horizontal:`8`}),(0,Z.jsx)(`p`,{className:`text-base`,children:`Send me a copy of this message`})]}),K&&(0,Z.jsxs)(Z.Fragment,{children:[(0,Z.jsx)(u,{vertical:`40`}),(0,Z.jsx)(Ze,{validationErrors:D,eligibilityErrors:k})]})]})})};Qe.propTypes={visible:Y.default.bool.isRequired,toggleModal:Y.default.func.isRequired,teamId:Y.default.string.isRequired,teamName:Y.default.string.isRequired,teamHandle:Y.default.string.isRequired,firstTimeInvite:Y.default.bool.isRequired,toggleShowPendingReviewModal:Y.default.func.isRequired,gettingStarted:Y.default.bool,clearProgram:Y.default.bool},N();var $e=c`
  mutation CancelHackerInvitation($team_id: ID!, $invitee: String!) {
    cancelHackerInvitation(input: { team_id: $team_id, invitee: $invitee }) {
      was_successful
    }
  }
`,et=({invitee:e,teamId:t,toggleModal:n,visible:r,pendingInvitations:i,changePendingInvitations:a})=>{let[o]=H($e,{variables:{team_id:t,invitee:e},onError(){J()},onCompleted({cancelHackerInvitation:{was_successful:t}}){t?(n(),s(e),B(`notice`,`Your invitation has been cancelled.`)):J()}}),s=e=>{a(i.filter(t=>t.node.recipient?.username!==e&&t.node.email!==e))};return(0,Z.jsxs)(W,{type:`info`,shouldCloseOnEsc:!0,title:`Cancel Invitation`,showModal:r,size:`medium`,handleCloseModal:()=>n(),children:[(0,Z.jsx)(`div`,{children:(0,Z.jsxs)(`p`,{children:[`Are you sure you want to cancel the invitation to `,e,`?`]})}),(0,Z.jsx)(u,{vertical:`24`}),(0,Z.jsxs)(`div`,{className:`flex justify-end`,children:[(0,Z.jsx)(p,{variation:`tertiary`,onClick:()=>n(),children:`Cancel`}),(0,Z.jsx)(u,{horizontal:`8`}),(0,Z.jsx)(p,{testId:`spec-confirm-cancel-invitation-button`,onClick:()=>o(),children:`Cancel invitation`})]})]})};et.propTypes={invitee:Y.default.string.isRequired,teamId:Y.default.string.isRequired,toggleModal:Y.default.func.isRequired,visible:Y.default.bool.isRequired,pendingInvitations:Y.default.array.isRequired,changePendingInvitations:Y.default.func.isRequired};var tt=({recipient:e})=>e?(0,Z.jsx)(K,{size:`medium`,className:`user-item__avatar`,cleared:e.cleared,verified:e.verified,src:e.profile_picture,username:e.username,object:{username:e.username}}):(0,Z.jsx)(K,{size:`medium`,className:`unknown-user-item__avatar`,src:pe}),nt=({email:e,recipient:t})=>t?(0,Z.jsx)(G,{label:t.username,username:t.username}):e||`Unknown recipient`,rt=({email:e,recipient:t})=>t?t.username:e,it=({teamId:e,pendingInvitations:t,handleLoadMore:n,hasNextPage:r,changePendingInvitations:i,totalCount:a,isClear:o=!1})=>{let[s,c]=(0,X.useState)(!1),[l,f]=(0,X.useState)(``),m=()=>{c(!s)},h=e=>{f(e),m()};return(0,Z.jsxs)(`div`,{children:[(0,Z.jsx)(`span`,{children:(0,Z.jsx)(`strong`,{children:`Pending invitations (${a})`})}),(0,Z.jsx)(u,{vertical:`5`}),(0,Z.jsx)(`p`,{className:`text-neutral-300 dark:text-neutral-800`,children:`These hackers have been invited to your program but have not yet joined.`}),(0,Z.jsx)(u,{vertical:`12`}),(0,Z.jsx)(`div`,{id:`pending-invitations-container`,className:`max-h-[400px] overflow-y-auto`,children:(0,Z.jsx)(A,{dataLength:t.length,next:n,hasMore:r,loader:(0,Z.jsx)(L,{}),scrollableTarget:`pending-invitations-container`,children:t.map((n,r)=>{let a=n.node,c=tt(a),u=rt(a);return(0,Z.jsxs)(`div`,{children:[(0,Z.jsxs)(`div`,{className:`flex items-center`,children:[(0,Z.jsxs)(`div`,{className:`flex-1 flex gap-sm items-center`,children:[c,nt(a)]}),(0,Z.jsxs)(`div`,{className:`flex-1 flex gap-xs`,children:[(0,Z.jsxs)(`div`,{children:[`Invited on`,` `,z({date:a.created_at})]}),o&&a?.recipient?.cleared!==!0&&(0,Z.jsx)(d,{color:`gray`,children:a?.recipient?.verified?a?.recipient!=null&&`Background check pending`:`ID verification pending`})]}),(0,Z.jsx)(et,{teamId:e,invitee:l,visible:s,toggleModal:m,pendingInvitations:t,changePendingInvitations:i}),(0,Z.jsx)(p,{className:`flex-none`,onClick:()=>h(u),variation:`danger-secondary`,testId:`spec-cancel-invitation-button`,children:`Cancel`})]}),(0,Z.jsx)(O,{variation:`light`})]},r)})})})]})};it.propTypes={teamId:Y.default.string.isRequired,pendingInvitations:Y.default.array.isRequired,handleLoadMore:Y.default.func,hasNextPage:Y.default.bool,changePendingInvitations:Y.default.func.isRequired,totalCount:Y.default.number,isClear:Y.default.bool};var at=e(v()),ot=({visible:e,toggleModal:t,teamHandle:n})=>(0,Z.jsx)(W,{type:`info`,shouldCloseOnEsc:!0,title:`Professional edition only`,showModal:e,size:`medium`,handleCloseModal:t,className:`spec-professional-edition-modal`,children:(0,Z.jsxs)(`span`,{children:[(0,Z.jsx)(`a`,{className:`daisy-text--blue`,href:`/${n}/product_edition`,target:`_blank`,rel:`noreferrer`,children:`Change your Product Edition`}),` `,`to be able to invite hackers by username.`]})});ot.propTypes={visible:Y.default.bool.isRequired,toggleModal:Y.default.func.isRequired,teamHandle:Y.default.string.isRequired};var st=({teamName:e,visible:t,toggleModal:n})=>(0,Z.jsx)(W,{type:`info`,className:`spec-pending-review-modal`,shouldCloseOnEsc:!0,title:`Pending review`,showModal:t,size:`medium`,handleCloseModal:()=>n(),children:(0,Z.jsxs)(`div`,{className:`text-aligned-center`,children:[(0,Z.jsxs)(`p`,{children:[`Because this is the first time you are inviting hackers, we must verify that this launch is authorized by `,e,`.`]}),(0,Z.jsx)(`p`,{children:(0,Z.jsx)(`strong`,{children:`Your program will be reviewed within 5 business days.`})}),(0,Z.jsx)(`p`,{children:`Hackers will be automatically invited upon successful review.`}),(0,Z.jsx)(`p`,{children:`Thank you!`}),(0,Z.jsx)(p,{onClick:()=>n(),children:`Okay!`})]})});st.propTypes={teamName:Y.default.string.isRequired,toggleModal:Y.default.func.isRequired,visible:Y.default.bool.isRequired},N();var ct=c`
  query TeamInvitations($handle: String!, $cursor: String) {
    team(handle: $handle) {
      id
      handle
      state
      review_requested_at
      name
      has_avatar
      allowed_to_use_saml_in_sandbox
      offers_bounties
      has_payment_method
      policy_setting {
        policy
        has_policy
      }
      needs_payment_method
      can_request_review
      can_update_all_hacker_invitations
      is_pending_review
      first_time_invite
      is_review_rejected
      only_cleared_hackers
      pending_invitations(
        first: 10
        after: $cursor
        order_by: { field: invitation_created_at, direction: DESC }
      ) {
        total_count
        pageInfo {
          endCursor
          hasNextPage
        }
        edges {
          node {
            id
            email
            created_at
            recipient {
              id
              username
              profile_picture(size: small)
              cleared
              verified
            }
          }
        }
      }
    }
  }
`,lt=e=>(0,Z.jsx)(le,{teamNeedsAvatar:!e.has_avatar,teamNeedsPolicy:!e.policy_setting.has_policy,teamAllowedToUseSamlInSandbox:e.allowed_to_use_saml_in_sandbox,teamNeedsPaymentMethod:e.needs_payment_method,teamHandle:e.handle}),ut=e=>{let[t,n]=(0,X.useState)(null),[r,i]=(0,X.useState)(!0);return(0,X.useEffect)(()=>at.default.ajax({url:`/${e}/launch`,dataType:`json`,success:e=>{let t={hasExternalProgram:e.has_external_program,tooFewResearchers:e.too_few_researchers,tooManyOpenReports:e.too_many_open_reports,launchPolicy:e.launch_policy};n(t),i(!1)},error:()=>{B(`error`,`Something went wrong loading your settings. Please contact ${window.constants.notification.support_link} if the problem persists.`),i(!1)}}),[e]),{publicLaunchSettings:t,loading:r}},dt=({handle:e,isPublicLaunch:t})=>{let[r,i]=(0,X.useState)(!1),a=n(),{publicLaunchSettings:o,loading:s}=ut(e),[c,l]=(0,X.useState)([]),[d,m]=(0,X.useState)(!1),[h,g]=(0,X.useState)(!1),[_,v]=(0,X.useState)(!1),y=()=>{i(!r)},b=e=>{l(e)},x=e=>{m(e)},S=()=>{v(!_)},C=e=>{g(e)},{data:w,networkStatus:T,fetchMore:E}=q(ct,{notifyOnNetworkStatusChange:!0,variables:{handle:e},fetchPolicy:`cache-and-network`,onCompleted:e=>{b(e.team.pending_invitations.edges),x(e.team.is_pending_review),C(e.team.is_review_rejected)}});if(T===1&&!w||!w||!o||s)return(0,Z.jsx)(V,{});let D=U(w,`team.pending_invitations`,E),O=w?.team;return O.can_request_review===!1&&O.state!==`soft_launched`?lt(O):t?(0,Z.jsx)(Ae,{team:O,onCancel:()=>a.push(`launch`),hasExternalProgram:o.hasExternalProgram,tooFewResearchers:o.tooFewResearchers,tooManyOpenReports:o.tooManyOpenReports,launchPolicy:o.launchPolicy}):(0,Z.jsxs)(f,{children:[(0,Z.jsx)(`div`,{className:`mb-md`,children:(0,Z.jsx)(ee,{children:`Invites`})}),(0,Z.jsx)(ze,{isPendingReview:d,teamState:O.state}),d===!1&&O.state!==`soft_launched`&&(0,Z.jsxs)(Z.Fragment,{children:[(0,Z.jsx)(we,{teamId:O.id,teamState:O.state,changeIsPendingReview:x,changeIsReviewRejected:C,toggleShowPendingReviewModal:S}),(0,Z.jsx)(u,{vertical:`24`})]}),(0,Z.jsx)(st,{teamName:O.name,visible:_,toggleModal:S}),O.state===`soft_launched`&&(0,Z.jsxs)(Z.Fragment,{children:[(0,Z.jsx)(ge,{handle:e}),(0,Z.jsx)(u,{vertical:`40`})]}),(d===!1||O.state===`soft_launched`)&&(0,Z.jsxs)(Z.Fragment,{children:[(0,Z.jsxs)(`div`,{className:`flex items-center`,children:[(0,Z.jsx)(`span`,{children:`Manually invite a hacker by email or username`}),(0,Z.jsx)(u,{horizontal:`24`}),(0,Z.jsx)(Qe,{visible:r&&O.can_update_all_hacker_invitations===!0,toggleModal:y,teamId:O.id,teamName:O.name,teamHandle:e,teamState:O.state,firstTimeInvite:O.first_time_invite,toggleShowPendingReviewModal:S,clearProgram:O.only_cleared_hackers??!1,gettingStarted:d===!1&&O.state!==`soft_launched`}),(0,Z.jsx)(ot,{visible:r&&O.can_update_all_hacker_invitations===!1,toggleModal:y,teamHandle:e}),(0,Z.jsx)(p,{id:`invite_hacker_button`,variation:O.first_time_invite?`secondary`:`primary`,onClick:y,children:`Invite a hacker`})]}),(0,Z.jsx)(u,{vertical:`40`})]}),(0,Z.jsx)(Be,{isPendingReview:d,isReviewRejected:h}),(0,Z.jsx)(it,{teamId:O.id,pendingInvitations:c,handleLoadMore:D,hasNextPage:O.pending_invitations?.pageInfo.hasNextPage,changePendingInvitations:b,totalCount:O.pending_invitations.total_count,isClear:O.only_cleared_hackers}),(0,Z.jsx)(u,{vertical:`40`}),(0,Z.jsx)(He,{isReviewRejected:h}),(0,Z.jsx)(Se,{handle:e})]})};dt.propTypes={handle:Y.default.string.isRequired,isPublicLaunch:Y.default.bool.isRequired};var ft=e=>(0,Z.jsx)(ue,{children:(0,Z.jsx)(ie,{header:(0,Z.jsx)(ce,{...e}),content:(0,Z.jsx)(dt,{handle:e.match.params.handle,isPublicLaunch:e.match.path===`/:handle/public_launch`}),footer:(0,Z.jsx)(re,{})})});ft.propTypes={match:Y.default.shape({path:Y.default.string,params:Y.default.shape({handle:Y.default.string.isRequired}).isRequired}).isRequired};export{ft as default};
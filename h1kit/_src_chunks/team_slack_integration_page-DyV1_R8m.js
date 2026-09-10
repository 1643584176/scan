import{o as e}from"./rolldown-runtime-DAXXjFlN.js";import{Fw as t,Kx as n,Li as r,Lr as i,Ly as a,Nb as o,Of as s,Pb as c,Qy as l,Rw as u,Vf as d,Xi as f,qx as p,zx as m,zy as h}from"./vendor-_WdvpBLr.js";import{Ah as ee,Fn as te,Gs as ne,Iu as g,Js as _,Nn as v,Ps as re,T as ie,Th as y,Ws as ae,Xs as b,_h as x,ar as S,ba as C,dh as w,dl as T,ep as E,gh as D,k as oe,qs as se,sr as ce,vh as O,vm as k,ym as A}from"./app-5pKgUmmm.js";var j=e(u()),M=e(m()),N=t(),le=({fancy_slack_integration:e,slack_integration:t})=>t?e?t.team_url?(0,N.jsxs)(`div`,{children:[`Connected with the team`,` `,(0,N.jsx)(`a`,{href:t.team_url,children:(0,N.jsx)(`strong`,{children:t.team_name??t.team_url})}),`.`]}):(0,N.jsx)(`div`,{children:`Connected with your slack workspace`}):(0,N.jsxs)(`div`,{children:[`Connected with the channel `,(0,N.jsx)(`strong`,{children:t.channel}),`.`]}):(0,N.jsx)(`div`,{children:`Not connected with any slack workspace`});p();var ue=n`
  mutation deleteTeamSlackIntegrationMutation($slack_integration_id: ID!) {
    deleteTeamSlackIntegration(
      input: { slack_integration_id: $slack_integration_id }
    ) {
      team {
        id
        slack_integration {
          id
        }
      }
      was_successful
      errors(first: 100) {
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
`,P=({team:e})=>{let[t]=x(ue,{variables:{slack_integration_id:e.slack_integration.id},optimisticResponse:{team:{id:e.id,slack_integration:null,slack_pipelines:{total_count:0}}}});return(0,N.jsx)(`div`,{className:`settings-section`,children:(0,N.jsxs)(`div`,{className:`inline-banner`,children:[(0,N.jsx)(`div`,{className:`pull-left`,children:(0,N.jsx)(le,{slack_integration:e.slack_integration,fancy_slack_integration:e.fancy_slack_integration})}),(0,N.jsx)(`div`,{className:`pull-right`,children:(0,N.jsx)(`a`,{className:`link red`,onClick:n=>{n.preventDefault(),confirm(`Are you sure? This will deactivate and remove your Slack integration.`)&&t({variables:{slack_integration_id:e.slack_integration.id}}).then(()=>A(),()=>k())},children:`Disconnect`})}),(0,N.jsx)(`div`,{className:`clearfix`})]})})};P.propTypes={team:M.default.object.isRequired},P.fragments={team:n`
    fragment TemSlackDisconnectForm on Team {
      id
      fancy_slack_integration
      slack_integration {
        id
        channel
        team_url
        team_name
      }
    }
  `},p();var F=({team:e,session:t,reconnect:n})=>{let r,i=e=>{e.preventDefault(),r.submit()};return(0,N.jsx)(v.Context,{name:constants.gates.all.slack_integration,teamHandle:e.handle,children:(0,N.jsxs)(`form`,{ref:e=>{r=e},method:`post`,onSubmit:()=>null,action:`/auth/slack?team_handle=${e.handle}`,noValidate:!0,children:[(0,N.jsx)(`input`,{type:`hidden`,name:`authenticity_token`,value:t.csrf_token}),(0,N.jsx)(S,{children:n?(0,N.jsx)(a,{contentPrimary:`Authentication revoked`,contentSecondary:(0,N.jsxs)(N.Fragment,{children:[(0,N.jsx)(`p`,{children:`It looks like the authentication with Slack has been revoked. Re-authenticate with Slack to re-enable the integration or hit disconnect to remove this integration.`}),(0,N.jsx)(v.a,{className:`button button--success`,onClick:i,children:`Re-authenticate with Slack`})]}),variation:`error`}):(0,N.jsxs)(N.Fragment,{children:[(0,N.jsx)(`p`,{children:`Your program is currently not connected with any Slack instance.`}),(0,N.jsx)(v.a,{className:`button button--success`,onClick:i,children:`Authenticate with Slack`})]})}),(0,N.jsx)(v.ToggleModal,{children:(0,N.jsx)(v.SlackIntegrationUpgradeNotice,{})})]})})};F.propTypes={team:M.default.object.isRequired,session:M.default.object.isRequired,reconnect:M.default.bool};var I=n`
  query SessionConnectFormQuery {
    session {
      id
      csrf_token
    }
  }
`,L=({team:e,reconnect:t})=>{let{data:n,loading:r,error:i}=O(I,{fetchPolicy:`no-cache`});return r?(0,N.jsx)(y,{}):i?(0,N.jsx)(`div`,{children:`Some error occurred.`}):(0,N.jsx)(F,{team:e,session:n.session,reconnect:t})};L.propTypes={team:M.default.object.isRequired,reconnect:M.default.bool},L.fragments={team:n`
    fragment TemSlackConnectForm on Team {
      id
      handle
      slack_integration {
        id
        channel
      }
    }
  `};var R=e(d());p();var z=n`
  mutation updateSlackUserMutation(
    $team_member_id: ID!
    $slack_user_id: String!
  ) {
    updateSlackUser(
      input: { team_member_id: $team_member_id, slack_user_id: $slack_user_id }
    ) {
      team_member {
        id
        slack_user_id
      }
      was_successful
      errors(first: 100) {
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
`,B=({team_member:e,slack_integration:t})=>{let n=e.slack_user_id,[r,i]=(0,j.useState)(null),[a]=x(z,{refetchQueries:[`SlackTeamMembersQuery`]}),o=()=>{A(),i(null)},s=()=>t=>{t.preventDefault(),a({variables:{team_member_id:e.id,slack_user_id:r===`deleted`?``:r}}).then(()=>o(),()=>k())},c=e=>{let n=t.users,r=e.match(/^@?(.*)$/)[1];if(r===``)return n;let i=new RegExp(r,`i`);return n.filter(function(e){let t=e.real_name&&e.real_name.match(i),n=e.name.match(i);return t||n})},l=e=>{i(e.id)},u=e=>(0,N.jsxs)(`div`,{children:[`@`,e.name,` `,(0,N.jsx)(`span`,{className:`pull-right text-muted margin-10--right`,children:e.real_name})]}),d=e=>{let t=(0,N.jsx)(`a`,{href:`#`,className:`typeahead-selection__remove icon-remove`,onClick:e=>{e.preventDefault(),i(`deleted`)}});return e?(0,N.jsxs)(`div`,{className:`typeahead-selection`,children:[u(e),t]}):(0,N.jsxs)(`div`,{className:`typeahead-selection alert alert--warning`,children:[`Unknown User ID`,t]})},f=()=>(0,N.jsx)(`div`,{children:(0,N.jsx)(ce,{className:`spec-slack-user`,filterByQuery:c.bind(void 0),onSelectSuggestion:l.bind(void 0),placeHolder:``,displayOnFocus:!0,renderSuggestion:u.bind(void 0)})}),p=e=>t.users.find(t=>t.id===e);return(0,N.jsxs)(`tr`,{children:[(0,N.jsxs)(`td`,{children:[(0,N.jsx)(g,{size:`small`,src:e.user.profile_picture,object:e.user}),` `,(0,N.jsxs)(`span`,{children:[`@`,e.user.username]})]}),(0,N.jsx)(`td`,{children:(0,N.jsx)(`form`,{onSubmit:s(),children:(0,N.jsxs)(`div`,{className:`row`,children:[(0,N.jsx)(`div`,{className:`col col--four-fifths`,children:r===`deleted`?f():r?d(p(r)):n?d(p(n)):f()}),(0,N.jsx)(`div`,{className:`col col--one-fifth`,children:(0,N.jsx)(te,{disabled:!r||!1,className:`pull-right`,type:`submit`,children:`Save`})})]})})})]},e.user.username)};B.propTypes={team_member:M.default.object.isRequired,slack_integration:M.default.object.isRequired},B.fragments={slack_integration:n`
    fragment UserFormSlackIntegration on TeamIntegrationsSlack {
      id
      team {
        id
        fancy_slack_integration
      }
      users {
        id
        name
        real_name
      }
    }
  `,team_member:n`
    fragment UserFormTeamMember on TeamMember {
      id
      user {
        id
        username
        profile_picture(size: small)
      }
      slack_user_id
    }
  `},p();var V=({team:e,onLoadMore:t,onShowManuallyMapModal:n})=>(0,N.jsxs)(`div`,{className:`settings-section`,children:[(0,N.jsx)(`h3`,{children:`Slack Usernames`}),(0,N.jsx)(`p`,{children:`HackerOne username to Slack username mapping for @ mention notifications.`}),e.slack_integration.should_fetch_slack_users?(0,N.jsxs)(`table`,{className:`table table--separate table--no-margin spec-slack-username-list`,children:[(0,N.jsx)(`thead`,{children:(0,N.jsxs)(`tr`,{children:[(0,N.jsx)(`th`,{children:`User`}),(0,N.jsx)(`th`,{children:`Slack Username`})]})}),(0,N.jsxs)(`tbody`,{children:[(0,R.default)(e.team_members.edges,t=>(0,N.jsx)(B,{team_member:t.node,slack_integration:e.slack_integration},t.node.id)),e.team_members.pageInfo.hasNextPage&&(0,N.jsx)(`tr`,{children:(0,N.jsx)(`td`,{colSpan:`2`,children:(0,N.jsx)(D,{hasOutsideGutter:!0,children:(0,N.jsx)(D.Row,{children:(0,N.jsx)(D.Column,{children:(0,N.jsx)(`div`,{className:`text-aligned-center`,children:(0,N.jsx)(l,{onClick:t,variation:`primary`,size:`medium`,children:`Load more`})})})})})})})]})]}):(0,N.jsxs)(N.Fragment,{children:[(0,N.jsx)(`div`,{className:`py-sm`,children:(0,N.jsx)(a,{contentPrimary:`Heads up`,contentSecondary:`Your Slack team has a large number of users. To ensure this
            page stays performant, we have disabled automatic Slack to
            HackerOne username mapping. Below you can see mapping of
            HackerOne users to slack IDs. You can still manually map users via email address.`,variation:`warning`})}),(0,N.jsx)(`div`,{className:`flex justify-end mb-sm`,children:(0,N.jsx)(l,{onClick:n,variation:`primary`,children:`Manually map a user`})}),(0,N.jsxs)(`table`,{className:`table table--separate table--no-margin spec-slack-username-list`,children:[(0,N.jsx)(`thead`,{children:(0,N.jsxs)(`tr`,{children:[(0,N.jsx)(`th`,{children:`User`}),(0,N.jsx)(`th`,{children:`Slack ID`})]})}),(0,N.jsxs)(`tbody`,{children:[(0,R.default)(e.team_members.edges,e=>(0,N.jsxs)(`tr`,{children:[(0,N.jsx)(`td`,{children:e.node.user.username}),(0,N.jsx)(`td`,{children:e.node.slack_user_id?atob(e.node.slack_user_id).split(`/`).slice(-1):``})]},e.node.id)),e.team_members.pageInfo.hasNextPage&&(0,N.jsx)(`tr`,{children:(0,N.jsx)(`td`,{colSpan:`2`,children:(0,N.jsx)(D,{hasOutsideGutter:!0,children:(0,N.jsx)(D.Row,{children:(0,N.jsx)(D.Column,{children:(0,N.jsx)(`div`,{className:`text-aligned-center`,children:(0,N.jsx)(l,{onClick:t,variation:`secondary`,children:`Load more`})})})})})})})]})]})]})]});V.propTypes={team:M.default.object.isRequired,onLoadMore:M.default.func.isRequired,onShowManuallyMapModal:M.default.func.isRequired};var H=n`
  query SlackTeamMembersQuery($handle: String!, $cursor: String) {
    team(handle: $handle) {
      id
      slack_integration {
        id
        team_url
        should_fetch_slack_users
        ...UserFormSlackIntegration
      }
      team_members(
        first: 10
        after: $cursor
        order_by: { field: username, direction: ASC }
      ) {
        pageInfo {
          hasNextPage
          endCursor
        }
        edges {
          cursor
          node {
            id
            ...UserFormTeamMember
          }
        }
      }
    }
  }
  ${B.fragments.slack_integration}
  ${B.fragments.team_member}
`,U=({handle:e,onShowManuallyMapModal:t,team:n})=>{let{data:r,loading:i,error:s,fetchMore:c}=O(H,{variables:{handle:e,cursor:null}});if(i)return(0,N.jsx)(y,{size:`small`});if(s)return s.message===`Slack Error: token_revoked`?(0,N.jsx)(L,{team:n,reconnect:!0}):(0,N.jsx)(o,{bottom:`12`,children:(0,N.jsx)(a,{contentPrimary:` Oops! It looks like we've hit a limit on requests from Slack. Please
          wait 60 seconds and try again.`,variation:`error`})});let l=T(r,`team.team_members`,c);return(0,N.jsx)(V,{team:r.team,onLoadMore:l,onShowManuallyMapModal:t})};U.propTypes={handle:M.default.string.isRequired,onShowManuallyMapModal:M.default.func.isRequired,team:M.default.object.isRequired};var de=e(s()),fe=e(c());p();var pe=n`
  mutation deleteSlackPipelineMutation($slack_pipeline_id: ID!) {
    deleteSlackPipeline(input: { slack_pipeline_id: $slack_pipeline_id }) {
      team {
        id
        slack_pipelines {
          total_count
        }
      }
      was_successful
      errors(first: 100) {
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
`,W=n`
  query TeamPipelineList($handle: String!, $afterCursor: String) {
    team(handle: $handle) {
      id
      handle
      slack_pipelines(first: 10, after: $afterCursor) {
        total_count
        pageInfo {
          hasNextPage
        }
        edges {
          cursor
          node {
            id
            database_id: _id
            channel
            notification_report_assignee_changed
            notification_report_became_public
            notification_report_bounty_paid
            notification_report_internal_comment_added
            notification_report_not_eligible_for_bounty
            notification_report_public_comment_added
            notification_report_agreed_on_going_public
            notification_report_bounty_suggested
            notification_report_bug_closed_as_spam
            notification_report_bug_duplicate
            notification_report_bug_informative
            notification_report_bug_needs_more_info
            notification_report_bug_new
            notification_report_bug_not_applicable
            notification_report_closed_as_resolved
            notification_report_comments_closed
            notification_report_created
            notification_report_reopened
            notification_report_triaged
            notification_report_retesting
            notification_report_user_completed_retest
            notification_report_swag_awarded
            notification_report_manually_disclosed
            updated_at
            team {
              id
            }
          }
        }
      }
    }
  }
`,G=`SET_CURSOR`,K=({team:e,dispatch:t,store:n})=>{let r=e=>{e.preventDefault();let r=n.prevCursors;t({type:G,cursor:r.pop(),prevCursors:r})},i=r=>{r.preventDefault();let i=n.prevCursors;i.push(n.cursor),t({type:G,cursor:(0,de.default)(e.slack_pipelines.edges).cursor,prevCursors:i})},[a]=x(pe,{refetchQueries:[{query:W,variables:{handle:e.handle,afterCursor:null}}],onCompleted:A,onError:k}),o=e=>t=>{t.preventDefault(),confirm(`Are you sure?`)&&a({variables:{slack_pipeline_id:e.id}}).then(()=>A(),()=>k())};return(0,N.jsx)(`div`,{children:e.slack_pipelines.total_count===0?(0,N.jsx)(`div`,{className:`spec-slack-pipelines-empty-state`,children:(0,N.jsxs)(S,{children:[(0,N.jsx)(`p`,{children:`Nothing configured yet.`}),(0,N.jsx)(`a`,{href:`/${e.handle}/slack_pipelines/new`,className:`button button--success spec-empty-state-add-slack-pipeline-button`,children:`Create your first Notification Configuration`})]})}):(0,N.jsxs)(`div`,{children:[(0,N.jsxs)(`table`,{className:`table table--separate table--no-margin table--layout-auto spec-slack-pipeline-list`,children:[(0,N.jsx)(`thead`,{children:(0,N.jsxs)(`tr`,{children:[(0,N.jsx)(`th`,{children:`Channel`}),(0,N.jsx)(`th`,{children:`Activities`}),(0,N.jsx)(`th`,{})]})}),(0,N.jsx)(`tbody`,{children:(0,R.default)(e.slack_pipelines.edges,t=>(0,N.jsxs)(`tr`,{className:`spec-slack-pipeline-row spec-slack-pipeline-row-${t.database_id}`,children:[(0,N.jsxs)(`td`,{className:`table__row--align-top`,children:[`#`,t.node.channel]}),(0,N.jsx)(`td`,{children:(0,N.jsxs)(`ul`,{className:`list`,children:[t.node.notification_report_assignee_changed?(0,N.jsx)(`li`,{children:`The assignee of the report has been changed`}):null,t.node.notification_report_became_public?(0,N.jsx)(`li`,{children:`Report became public`}):null,t.node.notification_report_bounty_paid?(0,N.jsx)(`li`,{children:`A bounty has been paid`}):null,t.node.notification_report_manually_disclosed?(0,N.jsx)(`li`,{children:`Manually disclosed`}):null,t.node.notification_report_internal_comment_added?(0,N.jsx)(`li`,{children:`An internal comment was added to a report`}):null,t.node.notification_report_not_eligible_for_bounty?(0,N.jsx)(`li`,{children:`Not eligible for bounty`}):null,t.node.notification_report_public_comment_added?(0,N.jsx)(`li`,{children:`A public comment was added to a report`}):null,t.node.notification_report_agreed_on_going_public?(0,N.jsx)(`li`,{children:`Agreed on going public`}):null,t.node.notification_report_bounty_suggested?(0,N.jsx)(`li`,{children:`Bounty suggested`}):null,t.node.notification_report_bug_closed_as_spam?(0,N.jsx)(`li`,{children:`Report was closed as spam`}):null,t.node.notification_report_bug_duplicate?(0,N.jsx)(`li`,{children:`Report was closed as a duplicate`}):null,t.node.notification_report_bug_informative?(0,N.jsx)(`li`,{children:`Report was closed as informative`}):null,t.node.notification_report_bug_needs_more_info?(0,N.jsx)(`li`,{children:`Report needs more info from the reporter`}):null,t.node.notification_report_bug_new?(0,N.jsx)(`li`,{children:`Reporter provided more info`}):null,t.node.notification_report_bug_not_applicable?(0,N.jsx)(`li`,{children:`Report was closed as not applicable`}):null,t.node.notification_report_closed_as_resolved?(0,N.jsx)(`li`,{children:`Report was resolved`}):null,t.node.notification_report_comments_closed?(0,N.jsx)(`li`,{children:`Report locked, reporters can't reply on the report anymore`}):null,t.node.notification_report_created?(0,N.jsx)(`li`,{children:`Report was submitted`}):null,t.node.notification_report_reopened?(0,N.jsx)(`li`,{children:`Report was reopened`}):null,t.node.notification_report_triaged?(0,N.jsx)(`li`,{children:`Report was triaged`}):null,t.node.notification_report_retesting?(0,N.jsx)(`li`,{children:`Report retest requested`}):null,t.node.notification_report_user_completed_retest?(0,N.jsx)(`li`,{children:`User completed retest`}):null,t.node.notification_report_swag_awarded?(0,N.jsx)(`li`,{children:`Swag was awarded`}):null]})}),(0,N.jsx)(`td`,{className:`table__row--align-top`,children:(0,N.jsxs)(`ul`,{className:`list list--inline pull-right`,children:[(0,N.jsx)(`li`,{children:(0,N.jsx)(w,{to:`/${e.handle}/slack_pipelines/${t.node.database_id}/edit`,className:`spec-edit-link`,children:`Edit`})}),(0,N.jsx)(`li`,{children:(0,N.jsx)(`a`,{href:``,className:`spec-delete-link`,onClick:o(t.node),children:`Remove`})})]})})]},t.node.id))})]}),fe.default.empty(n.prevCursors)?null:(0,N.jsx)(`a`,{href:``,onClick:r,children:`Previous Page`}),e.slack_pipelines.pageInfo.hasNextPage?(0,N.jsx)(`a`,{href:``,onClick:i,className:`pull-right`,children:`Next Page`}):null]})})};K.propTypes={team:M.default.object.isRequired,dispatch:M.default.func.isRequired,store:M.default.object.isRequired};var me=(e,t={})=>{switch(t.type){case G:{let n={...e};return n.cursor=t.cursor,n.prevCursors=t.prevCursors,n}default:return e}},he=()=>({cursor:null,prevCursors:[]}),ge=(e,t)=>({handle:t,afterCursor:e.cursor}),q=({handle:e})=>{let[t,n]=(0,j.useReducer)(me,he()),{data:r,loading:i,error:a}=O(W,{variables:ge(t,e)});return i?(0,N.jsx)(y,{size:`small`}):a?(0,N.jsx)(`div`,{children:`Some error`}):(0,N.jsx)(K,{team:r.team,store:t,dispatch:n})};q.propTypes={handle:M.default.string.isRequired},p();var J=({team:e})=>(0,N.jsxs)(`div`,{className:`settings-section`,children:[(0,N.jsxs)(`div`,{children:[e.slack_pipelines.total_count===0?null:(0,N.jsxs)(`div`,{children:[(0,N.jsx)(`h3`,{className:`pull-left`,children:`Notification Configuration`}),(0,N.jsx)(w,{to:`/${e.handle}/slack_pipelines/new`,className:`button button--small pull-right spec-add-slack-pipeline-button`,children:`Add Notification Configuration`})]}),(0,N.jsx)(`div`,{className:`clearFix`})]}),(0,N.jsx)(q,{handle:e.handle})]});J.propTypes={team:M.default.object.isRequired},J.fragments={team:n`
    fragment TeamPipelineForm on Team {
      id
      slack_pipelines {
        total_count
      }
    }
  `},p();var _e=e(f()),Y=n`
  mutation MapSlackUserMutation(
    $teamId: ID!
    $username: String!
    $slack_email_address: String!
  ) {
    mapSlackUser(
      input: {
        team_id: $teamId
        username: $username
        slack_email_address: $slack_email_address
      }
    ) {
      was_successful
      errors {
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
`,X=({teamId:e,showModal:t,setShowModal:n})=>{let[i,{loading:a}]=x(Y,{refetchQueries:[`SlackTeamMembersQuery`],onCompleted:({mapSlackUser:{was_successful:e,errors:t}})=>{if(!e)throw new re(t);A(),n(!1)}}),s=new r(new _e.default({username:{label:`HackerOne Username`,type:String,required:!0,uniforms:{id:`username`,className:`spec-hackerone-username`,description:`Username`,helperText:`The username of the user in HackerOne`,component:b}},slack_email_address:{type:String,label:`Slack Email Address`,required:!0,uniforms:{id:`slack-email`,className:`spec-hackerone-username`,component:b}}}));return(0,N.jsx)(E,{shouldCloseOnEsc:!0,showModal:t,size:`medium`,title:`Manually map a slack user`,handleCloseModal:()=>n(!1),handleCancelLinkClick:()=>n(!1),children:(0,N.jsx)(N.Fragment,{children:(0,N.jsx)(o,{margin:`24`,children:(0,N.jsxs)(ae,{schema:s,onSubmit:({username:t,slack_email_address:n})=>i({variables:{teamId:e,username:t,slack_email_address:n}}),showInlineError:!0,children:[(0,N.jsx)(_,{}),(0,N.jsx)(se,{}),(0,N.jsx)(ne,{}),(0,N.jsx)(o,{margin:`lg`,right:`20`,children:(0,N.jsxs)(`div`,{className:`flex justify-end gap-xs`,children:[(0,N.jsx)(l,{variation:`ghost-secondary`,renderAs:`link`,onClick:()=>n(!1),children:`Cancel`}),(0,N.jsx)(l,{type:`submit`,loading:a,disabled:a,testId:`submit-field-button`,children:`Store mapping`})]})})]})})})})};X.propTypes={teamId:M.default.string.isRequired,showModal:M.default.bool.isRequired,setShowModal:M.default.func.isRequired},p();var Z=window.constants.notification.support_link,Q=({team:e})=>{let[t,n]=(0,j.useState)(!1),r=e.slack_integration&&e.slack_integration.id,i=e.fancy_slack_integration;return(0,N.jsxs)(`div`,{className:`spec-slack-settings`,children:[(0,N.jsx)(`p`,{children:(0,N.jsx)(w,{to:`/${e.handle}/integrations`,children:`← Back to Integrations`})}),(0,N.jsx)(`h2`,{children:`Slack Settings`}),(0,N.jsx)(`div`,{children:!r||i?null:(0,N.jsxs)(`div`,{className:`inline-banner inline-banner--success`,children:[(0,N.jsx)(`p`,{children:`We're happy to announce our new Slack integration! With the new integration you gain more granular control over the types of activities that are being posted from HackerOne to a Slack channel that you specify (e.g. #appsec only showing newly created reports; #appsec-ops showing all notifications and primarily used for reference/scroll back).`}),(0,N.jsx)(`p`,{children:(0,N.jsx)(`strong`,{children:`The only thing you need to do is disconnect your current integration below and hit "Authenticate with Slack" to authorize the new integration.`})}),(0,N.jsxs)(`p`,{children:[`If you have any feedback or questions, please let us know by sending an email to `,(0,N.jsx)(w,{to:Z,children:Z}),`.`]})]})}),r?(0,N.jsx)(P,{team:e}):null,r&&i?(0,N.jsx)(J,{team:e}):null,r&&i&&e.slack_pipelines.total_count!==0?(0,N.jsxs)(N.Fragment,{children:[(0,N.jsx)(U,{handle:e.handle,team:e,onShowManuallyMapModal:()=>n(!0)}),(0,N.jsx)(X,{setShowModal:n,teamId:e.id,showModal:t}),(0,N.jsx)(h.Container,{id:`manual-mapping`,children:(0,N.jsx)(h.Content,{variation:`default`,contentPrimary:`Struggling to find your user?`,contentSecondary:(0,N.jsxs)(N.Fragment,{children:[`This is sometimes caused by some limitations in the Slack API. In this case you can try to `,(0,N.jsx)(w,{to:`#`,onClick:()=>n(!0),children:`map them manually.`})]})})}),` `]}):null,r?null:(0,N.jsx)(L,{team:e})]})};Q.propTypes={team:M.default.object.isRequired};var ve=n`
  query TeamSlackLayoutQuery($handle: String!) {
    team(handle: $handle) {
      id
      slack_pipelines {
        total_count
      }
      slack_integration {
        id
      }
      handle
      fancy_slack_integration
      ...TemSlackDisconnectForm
      ...TemSlackConnectForm
      ...TeamPipelineForm
    }
  }
  ${P.fragments.team}
  ${L.fragments.team}
  ${J.fragments.team}
`,$=({handle:e})=>{let{data:t,loading:n,error:r}=O(ve,{variables:{handle:e}});return n?(0,N.jsx)(y,{size:`small`}):r?(0,N.jsx)(`div`,{children:`Some error occurred`}):(0,N.jsx)(Q,{team:t.team})};$.propTypes={handle:M.default.string.isRequired};var ye=class extends j.Component{static propTypes={match:M.default.shape({params:M.default.shape({handle:M.default.string.isRequired}).isRequired}).isRequired};render(){let e=this.props.match.params.handle;return(0,N.jsx)(ie,{header:(0,N.jsx)(oe,{...this.props}),content:(0,N.jsxs)(`div`,{children:[(0,N.jsx)(i,{children:(0,N.jsx)(`title`,{children:C(`Configure Slack Integrations`)})}),(0,N.jsx)($,{handle:e})]}),footer:(0,N.jsx)(ee,{})})}};export{ye as default};
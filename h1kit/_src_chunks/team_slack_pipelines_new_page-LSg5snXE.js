import{o as e}from"./rolldown-runtime-DAXXjFlN.js";import{Fw as t,Kx as n,Lr as r,Px as i,Rw as a,qx as o,zx as s}from"./vendor-_WdvpBLr.js";import{Ah as c,T as l,Th as u,_h as d,_m as f,ba as p,dh as m,gc as h,k as g,vh as _,vm as v,ym as y}from"./app-5pKgUmmm.js";import{t as b}from"./form-B9KGFUjS2.js";var x=e(s()),S=e(a());o();var C=t(),w=n`
  query TeamSlackIntegrationQuery($handle: String!) {
    team(handle: $handle) {
      id
      handle
      name
      offers_bounties
      slack_integration {
        id
        should_fetch_slack_channels
        channels {
          id
          name
        }
      }
    }
  }
`,T=n`
  mutation createSlackPipelineMutation(
    $team_id: ID!
    $descriptive_label: String
    $channel: String!
    $notification_report_created: Boolean!
    $notification_report_triaged: Boolean!
    $notification_report_retesting: Boolean!
    $notification_report_user_completed_retest: Boolean!
    $notification_report_closed_as_resolved: Boolean!
    $notification_report_assignee_changed: Boolean!
    $notification_report_internal_comment_added: Boolean!
    $notification_report_public_comment_added: Boolean!
    $notification_report_bounty_paid: Boolean!
    $notification_report_bounty_suggested: Boolean!
    $notification_report_agreed_on_going_public: Boolean!
    $notification_report_bug_duplicate: Boolean!
    $notification_report_bug_informative: Boolean!
    $notification_report_bug_needs_more_info: Boolean!
    $notification_report_bug_new: Boolean!
    $notification_report_bug_not_applicable: Boolean!
    $notification_report_bug_closed_as_spam: Boolean!
    $notification_report_comments_closed: Boolean!
    $notification_report_not_eligible_for_bounty: Boolean!
    $notification_report_became_public: Boolean!
    $notification_report_swag_awarded: Boolean!
    $notification_report_reopened: Boolean!
    $notification_report_manually_disclosed: Boolean!
  ) {
    createSlackPipeline(
      input: {
        team_id: $team_id
        descriptive_label: $descriptive_label
        channel: $channel
        notification_report_created: $notification_report_created
        notification_report_triaged: $notification_report_triaged
        notification_report_retesting: $notification_report_retesting
        notification_report_user_completed_retest: $notification_report_user_completed_retest
        notification_report_closed_as_resolved: $notification_report_closed_as_resolved
        notification_report_assignee_changed: $notification_report_assignee_changed
        notification_report_internal_comment_added: $notification_report_internal_comment_added
        notification_report_public_comment_added: $notification_report_public_comment_added
        notification_report_bounty_paid: $notification_report_bounty_paid
        notification_report_bounty_suggested: $notification_report_bounty_suggested
        notification_report_agreed_on_going_public: $notification_report_agreed_on_going_public
        notification_report_bug_duplicate: $notification_report_bug_duplicate
        notification_report_bug_informative: $notification_report_bug_informative
        notification_report_bug_needs_more_info: $notification_report_bug_needs_more_info
        notification_report_bug_new: $notification_report_bug_new
        notification_report_bug_not_applicable: $notification_report_bug_not_applicable
        notification_report_bug_closed_as_spam: $notification_report_bug_closed_as_spam
        notification_report_comments_closed: $notification_report_comments_closed
        notification_report_not_eligible_for_bounty: $notification_report_not_eligible_for_bounty
        notification_report_became_public: $notification_report_became_public
        notification_report_swag_awarded: $notification_report_swag_awarded
        notification_report_reopened: $notification_report_reopened
        notification_report_manually_disclosed: $notification_report_manually_disclosed
      }
    ) {
      was_successful
      errors(types: ARGUMENT, first: 100) {
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
`,E=({team:e,history:t})=>{let[n,r]=S.useState(!1),[i]=d(T,{onCompleted:({createSlackPipeline:{was_successful:n,errors:i}})=>{n?(y(),r(!1),t.push(`/${e.handle}/slack_integration`)):(f(`Something went wrong: `,h(i)),r(!1))},onError:()=>{v(),r(!1)}});return(0,C.jsxs)(`div`,{className:`spec-slack-pipeline-new`,children:[(0,C.jsxs)(`div`,{className:`settings-title-container`,children:[(0,C.jsx)(`p`,{children:(0,C.jsx)(m,{to:`/${e.handle}/slack_integration`,children:`← Back to Slack Settings`})}),(0,C.jsx)(`h2`,{className:`pull-left spec-title`,children:`Add Notification Configuration for Slack`})]}),(0,C.jsx)(b,{team:e,disabled:n,initialFormData:{channel:``,descriptive_label:``,notification_report_created:!1,notification_report_triaged:!1,notification_report_retesting:!1,notification_report_user_completed_retest:!1,notification_report_closed_as_resolved:!1,notification_report_assignee_changed:!1,notification_report_internal_comment_added:!1,notification_report_public_comment_added:!1,notification_report_bounty_paid:!1,notification_report_bounty_suggested:!1,notification_report_agreed_on_going_public:!1,notification_report_bug_duplicate:!1,notification_report_bug_informative:!1,notification_report_bug_needs_more_info:!1,notification_report_bug_new:!1,notification_report_bug_not_applicable:!1,notification_report_bug_closed_as_spam:!1,notification_report_comments_closed:!1,notification_report_not_eligible_for_bounty:!1,notification_report_became_public:!1,notification_report_swag_awarded:!1,notification_report_reopened:!1,notification_report_manually_disclosed:!1},onSubmit:({...t})=>(r(!0),i({variables:{team_id:e.id,...t}})),shouldFetchSlackChannels:e.slack_integration.should_fetch_slack_channels})]})};E.propTypes={team:x.default.object.isRequired,history:x.default.object.isRequired};var D=({handle:e,history:t})=>{let{data:n,loading:r,error:i}=_(w,{variables:{handle:e}});return r?(0,C.jsx)(u,{}):i?(0,C.jsx)(`div`,{children:`Something went wrong. Please retry and if this problem persists, contact us via https://support.hackerone.com/`}):(0,C.jsx)(E,{team:n.team,history:t})};D.propTypes={handle:x.default.string.isRequired,history:x.default.object.isRequired};var O=i(D),k=e=>(0,C.jsx)(l,{header:(0,C.jsx)(g,{...e}),content:(0,C.jsxs)(`div`,{children:[(0,C.jsx)(r,{children:(0,C.jsx)(`title`,{children:p(`Adding Slack Notification Configuration`)})}),(0,C.jsx)(O,{handle:e.match.params.handle})]}),footer:(0,C.jsx)(c,{})});k.propTypes={match:x.default.shape({params:x.default.shape({handle:x.default.string.isRequired}).isRequired}).isRequired};export{k as default};
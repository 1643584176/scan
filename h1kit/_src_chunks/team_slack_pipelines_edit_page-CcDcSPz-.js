import{o as e}from"./rolldown-runtime-DAXXjFlN.js";import{Fw as t,Kx as n,Lr as r,Px as i,Rw as a,qx as o,zx as s}from"./vendor-_WdvpBLr.js";import{Ah as c,T as l,Th as u,_h as d,_m as f,ba as p,dh as m,gc as h,k as g,vh as _,vm as v,ym as y}from"./app-5pKgUmmm.js";import{t as b}from"./form-B9KGFUjS2.js";var x=e(s()),S=e(a());o();var C=t(),w=({history:e,slackPipeline:t})=>{let[n,r]=S.useState(!1),[i]=d(T,{onCompleted:({updateSlackPipeline:{was_successful:n,errors:i}})=>{n?(y(),r(!1),e.push(`/${t.team.handle}/slack_integration`)):(r(!1),f(`Something went wrong: `,h(i)))},onError:()=>{v(),r(!1)}}),{team:a}=t,o=({...e})=>(r(!0),i({variables:{slack_pipeline_id:t.id,...e}})),s={channel:{name:t.channel},descriptive_label:t.descriptive_label,notification_report_created:t.notification_report_created,notification_report_triaged:t.notification_report_triaged,notification_report_retesting:t.notification_report_retesting,notification_report_user_completed_retest:t.notification_report_user_completed_retest,notification_report_closed_as_resolved:t.notification_report_closed_as_resolved,notification_report_assignee_changed:t.notification_report_assignee_changed,notification_report_internal_comment_added:t.notification_report_internal_comment_added,notification_report_public_comment_added:t.notification_report_public_comment_added,notification_report_bounty_paid:t.notification_report_bounty_paid,notification_report_bounty_suggested:t.notification_report_bounty_suggested,notification_report_agreed_on_going_public:t.notification_report_agreed_on_going_public,notification_report_bug_duplicate:t.notification_report_bug_duplicate,notification_report_bug_informative:t.notification_report_bug_informative,notification_report_bug_needs_more_info:t.notification_report_bug_needs_more_info,notification_report_bug_new:t.notification_report_bug_new,notification_report_bug_not_applicable:t.notification_report_bug_not_applicable,notification_report_bug_closed_as_spam:t.notification_report_bug_closed_as_spam,notification_report_comments_closed:t.notification_report_comments_closed,notification_report_not_eligible_for_bounty:t.notification_report_not_eligible_for_bounty,notification_report_became_public:t.notification_report_became_public,notification_report_swag_awarded:t.notification_report_swag_awarded,notification_report_manually_disclosed:t.notification_report_manually_disclosed,notification_report_reopened:t.notification_report_reopened};return(0,C.jsxs)(`div`,{className:`spec-slack-pipeline-edit`,children:[(0,C.jsx)(`p`,{children:(0,C.jsx)(m,{to:`/${t.team.handle}/slack_integration`,children:`← Back to Slack Settings`})}),(0,C.jsx)(`h2`,{children:`Edit Notification Configuration for Slack`}),(0,C.jsx)(b,{team:t.team,disabled:n,initialFormData:s,onSubmit:o,shouldFetchSlackChannels:a.slack_integration.should_fetch_slack_channels})]})};w.propTypes={slackPipeline:x.default.object.isRequired,history:x.default.object.isRequired};var T=n`
  mutation updateSlackPipelineMutation(
    $slack_pipeline_id: ID!
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
    updateSlackPipeline(
      input: {
        slack_pipeline_id: $slack_pipeline_id
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
      slack_pipeline {
        id
        channel
        descriptive_label
        notification_report_created
        notification_report_triaged
        notification_report_retesting
        notification_report_user_completed_retest
        notification_report_closed_as_resolved
        notification_report_assignee_changed
        notification_report_internal_comment_added
        notification_report_public_comment_added
        notification_report_bounty_paid
        notification_report_bounty_suggested
        notification_report_agreed_on_going_public
        notification_report_bug_duplicate
        notification_report_bug_informative
        notification_report_bug_needs_more_info
        notification_report_bug_new
        notification_report_bug_not_applicable
        notification_report_bug_closed_as_spam
        notification_report_comments_closed
        notification_report_not_eligible_for_bounty
        notification_report_became_public
        notification_report_swag_awarded
        notification_report_reopened
        notification_report_manually_disclosed
      }
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
`,E=n`
  query SlackPipelineEditQuery($url: URI!) {
    resource(url: $url) {
      ...SlackPipelineFragment
    }
  }
  fragment SlackPipelineFragment on SlackPipeline {
    id
    channel
    descriptive_label
    notification_report_created
    notification_report_triaged
    notification_report_retesting
    notification_report_user_completed_retest
    notification_report_closed_as_resolved
    notification_report_assignee_changed
    notification_report_internal_comment_added
    notification_report_public_comment_added
    notification_report_bounty_paid
    notification_report_bounty_suggested
    notification_report_agreed_on_going_public
    notification_report_bug_duplicate
    notification_report_bug_informative
    notification_report_bug_needs_more_info
    notification_report_bug_new
    notification_report_bug_not_applicable
    notification_report_bug_closed_as_spam
    notification_report_comments_closed
    notification_report_not_eligible_for_bounty
    notification_report_became_public
    notification_report_swag_awarded
    notification_report_reopened
    notification_report_manually_disclosed

    team {
      id
      handle
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
`,D=({url:e,history:t})=>{let{data:n,loading:r,error:i}=_(E,{variables:{url:e}});return r?(0,C.jsx)(u,{size:`small`}):i?(0,C.jsx)(`div`,{children:`Something went wrong. Please retry and if this problem persists, contact us via https://support.hackerone.com/`}):(0,C.jsx)(w,{slackPipeline:n.resource,history:t})};D.propTypes={url:x.default.string.isRequired,history:x.default.object.isRequired};var O=i(D),k=e=>(0,C.jsx)(l,{header:(0,C.jsx)(g,{...e}),content:(0,C.jsxs)(`div`,{children:[(0,C.jsx)(r,{children:(0,C.jsx)(`title`,{children:p(`Editing Slack Notification Configuration`)})}),(0,C.jsx)(O,{handle:e.match.params.handle,slack_pipeline_id:e.match.params.id,url:e.location.pathname})]}),footer:(0,C.jsx)(c,{})});k.propTypes={location:x.default.shape({pathname:x.default.string.isRequired}),match:x.default.shape({params:x.default.shape({handle:x.default.string.isRequired,id:x.default.string.isRequired}).isRequired}).isRequired};export{k as default};
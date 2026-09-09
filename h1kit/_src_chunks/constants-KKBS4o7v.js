import{Kx as e,qx as t}from"./vendor-_WdvpBLr.js";import{Dp as n,Ep as r,Hd as i,Op as a,Tp as o,Yd as s,nf as c,wp as l,yd as u}from"./app-5pKgUmmm.js";import{n as d,r as f}from"./subscript-D_hkpRvp.js";var p=(e,t=!0)=>{let n=new Date,r=new Date(Date.UTC(n.getUTCFullYear(),n.getUTCMonth(),n.getUTCDate()-e));return t?r.setUTCHours(0,0,0,0):r.setUTCHours(23,59,59,999),r.toISOString()},m=(e,t,n,r=!0)=>{let i=e.find(({uid:e})=>e===t)??{keys:[],values:[[]]},a=(i.keys??[]).indexOf(n),o=a===-1?`0`:i.values?.[0]?.[a];return r?Number.parseInt(o??`0`,10):Number(o)??0},ee=e=>m(e,C,w),te=e=>m(e,T,E),ne=e=>m(e,D,O),re=e=>{let t=m(e,k,j),n=t+m(e,k,M),r=n>0?t/n*100:0;return Math.round(r)},ie=e=>{let t=m(e,A,j),n=t+m(e,A,M);return n>0?t/n*100:0},ae=e=>{let t=m(e,I,L),n=m(e,I,R),r=n>0?t/n*100:0;return Math.round(r)},oe=e=>{let t=m(e,V,H),n=m(e,z,B),r=n>0?t/n*100:0;return Math.round(r)},se=e=>m(e,q,J),ce=e=>m(e,Y,$e),le=e=>{let t=m(e,X,Z),n=m(e,X,Q),r=t>0?n/t*100:0;return Math.round(r)},ue=e=>m(e,U,W),de=e=>m(e,G,W),fe=e=>m(e,K,W),pe=e=>m(e,P,Be),me=e=>m(e,F,He),he=e=>m(e,F,Ue,!1);t();var ge=window.constants.notification.type,_e=new Set([0,1,3,4]),ve={CAMPAIGN_STARTING:`Campaign starting`,CAMPAIGN_ENDING:`Campaign ending`,SPOT_CHECK_STARTING:`Spot Check starting`,PENTEST_STARTING:`Pentest starting`,PENTEST_ENDING:`Pentest ending`,PENTEST_REPORTING_STARTING:`Pentest reporting starting`,PENTEST_REMEDIATION_ENDING:`Pentest remediation ending`,CHALLENGE_STARTING:`Challenge starting`},ye={"Engagements::Legacy":`Legacy`,"Engagements::BugBountyProgram":`Bounty`,"Engagements::Assessment":`Pentest`,"Engagements::AssetDiscovery":`Asset Discovery`,"Engagements::VulnerabilityDisclosureProgram":`Response`,"Engagements::Challenge":`Bounty Challenge`},h={new:`#8046F2`,"pending-program-review":`#0038BB`,triaged:`#FF7550`,retesting:`#FAD542`,"needs-more-info":`#86A3F9`},g={critical:`#F8546F`,high:`#FF7550`,medium:`#FAD542`,low:`#3DE2C2`,none:`#5E78FB`,no_rating:`#D0D5DD`},be=432e5,xe=`https://docs.hackerone.com/en/articles/8365279-product-offerings`,Se=432e3,_=p(0,!1),v=p(90),Ce=p(91,!1),y=p(366,!1),we=p(181),b=p(456),Te={run_campaign:`/organizations/{ORG_HANDLE}/engagements?tab=campaigns`,update_policy_submissions:`/{TEAM_HANDLE}/policy`,check_bounty_table_action_submissions:`/{TEAM_HANDLE}/dashboards/bounty_table_benchmarking`,check_bounty_table_action_signal:`/{TEAM_HANDLE}/dashboards/bounty_table_benchmarking`,check_bounty_table_action_critical_sev:`/{TEAM_HANDLE}/dashboards/bounty_table_benchmarking`,check_bounty_table_action_high_sev:`/{TEAM_HANDLE}/dashboards/bounty_table_benchmarking`,check_bounty_table_action_medium_sev:`/{TEAM_HANDLE}/dashboards/bounty_table_benchmarking`,check_bounty_table_action_low_sev:`/{TEAM_HANDLE}/dashboards/bounty_table_benchmarking`,check_bounty_table_action_anchor_hackers:`/{TEAM_HANDLE}/dashboards/bounty_table_benchmarking`,check_response_times:`/organizations/{ORG_HANDLE}/analytics/dashboards/response_efficiency`,update_policy_signal:`/{TEAM_HANDLE}/policy`,tell_hackers_about_code_updates_submissions:`/{TEAM_HANDLE}/messaging`,tell_hackers_about_code_updates_signal:`/{TEAM_HANDLE}/messaging`,tell_hackers_about_code_updates_assets:`/{TEAM_HANDLE}/messaging`,tell_hackers_about_code_updates_anchor_hackers:`/{TEAM_HANDLE}/messaging`,run_spot_check:`/organizations/{ORG_HANDLE}/engagements?tab=spot_check`,update_guidelines:`/{TEAM_HANDLE}/policy`,reengage_researchers_campaign:`/organizations/{TEAM_HANDLE}/engagements?tab=campaigns`,recognize_top_hackers_anchor_hackers:`/organizations/{TEAM_HANDLE}/engagements?tab=campaigns`,review_targets_first:`/{TEAM_HANDLE}/response_targets`,review_targets_triage:`/{TEAM_HANDLE}/response_targets`,review_targets_resolution:`/{TEAM_HANDLE}/response_targets`,review_targets_bounty:`/{TEAM_HANDLE}/response_targets`,automate_report_routing_first:`/organizations/{ORG_HANDLE}/settings/automations`,automate_report_routing_triage:`/organizations/{ORG_HANDLE}/settings/automations`,automate_report_routing_resolution:`/organizations/{ORG_HANDLE}/settings/automations`,automate_report_routing_bounty:`/organizations/{ORG_HANDLE}/settings/automations`,organize_inbox_views_first:`/bugs?organization_inbox_handle={ORG_HANDLE}_inbox`,organize_inbox_views_triage:`/bugs?organization_inbox_handle={ORG_HANDLE}_inbox`,organize_inbox_views_resolution:`/bugs?organization_inbox_handle={ORG_HANDLE}_inbox`,organize_inbox_views_bounty:`/bugs?organization_inbox_handle={ORG_HANDLE}_inbox`,set_up_automations_generic:`/organizations/{ORG_HANDLE}/settings/automations/new`,set_up_report_routing:`/organizations/{ORG_HANDLE}/settings/automations/new`,set_up_hai_summary_automation:`/organizations/{ORG_HANDLE}/settings/automations/new`,run_weakness_spot_check:`/organizations/{ORG_HANDLE}/spot_checks/select_type`,review_recommended_methodologies:`/organizations/{ORG_HANDLE}/settings/methodologies`},Ee={run_campaign:`Go to Campaigns`,update_policy_submissions:`Go to policy editor`,check_bounty_table_action_submissions:`Go to dashboard`,check_bounty_table_action_signal:`Go to dashboard`,check_bounty_table_action_critical_sev:`Go to dashboard`,check_bounty_table_action_high_sev:`Go to dashboard`,check_bounty_table_action_medium_sev:`Go to dashboard`,check_bounty_table_action_low_sev:`Go to dashboard`,check_bounty_table_action_anchor_hackers:`Go to dashboard`,check_response_times:`Go to dashboard`,update_policy_signal:`Go to policy editor`,tell_hackers_about_code_updates_submissions:`Send message`,tell_hackers_about_code_updates_signal:`Send message`,tell_hackers_about_code_updates_assets:`Send message`,tell_hackers_about_code_updates_anchor_hackers:`Send message`,run_spot_check:`Go to Spot Checks`,update_guidelines:`Go to policy editor`,reengage_researchers_campaign:`Go to campaigns`,recognize_top_hackers_anchor_hackers:`Go to campaigns`,review_targets_first:`Review targets`,automate_report_routing_first:`Configure automation`,organize_inbox_views_first:`Go to inbox`,review_targets_triage:`Review targets`,automate_report_routing_triage:`Configure automation`,organize_inbox_views_triage:`Go to inbox`,review_targets_resolution:`Review targets`,automate_report_routing_resolution:`Configure automation`,organize_inbox_views_resolution:`Go to inbox`,review_targets_bounty:`Review targets`,automate_report_routing_bounty:`Configure automation`,organize_inbox_views_bounty:`Go to inbox`,set_up_automations_generic:`Configure automation`,set_up_report_routing:`Configure automation`,set_up_hai_summary_automation:`Configure automation`,run_weakness_spot_check:`Run a spot check`,review_recommended_methodologies:`Check it out`},De=new Set([`check_response_times`,`check_bounty_table_action_submissions`,`check_bounty_table_action_signal`,`review_targets_first`,`review_targets_triage`,`review_targets_resolution`,`review_targets_bounty`]),Oe={leave_hacker_feedback_anchor_hackers:`Keep your current anchors close`,send_hackers_swag_anchor_hackers:`Keep your current anchors close`,recognize_top_hackers_anchor_hackers:`Expand your list of anchor hackers`,check_bounty_table_action_anchor_hackers:`Expand your list of anchor hackers`,tell_hackers_about_code_updates_anchor_hackers:`Expand your list of anchor hackers`},x=e`
  fragment ActionableReportFragment on Report {
    id
    _id
    substate
    title
    url
    created_at
    submitted_at
    severity {
      id
      rating
      score
    }
    team {
      id
      _id
      handle
    }
    assignee {
      ... on User {
        id
        _id
        __typename
        username
        profilePicture: profile_picture(size: small)
      }

      ... on TeamMemberGroup {
        id
        _id
        name
        __typename
      }
    }
  }
`,ke=e`
  query OrganizationActionableReportsQuery(
    $handle: String!
    $teamIds: [Int!]
    $offset: Int!
    $pageSize: Int!
    $assignee: AssigneeInputType
    $hasAssignee: Boolean
    $upcomingDisclosureThreshold: Int!
    $missedTargetsOrderBy: FiltersReportFilterOrder
    $upcomingDisclosuresOrderBy: FiltersReportFilterOrder
    $sinceSubmittedOrderBy: FiltersReportFilterOrder
  ) {
    organizations(first: 1, where: { handle: { _eq: $handle } }) {
      nodes {
        id
        handle
        missedTarget: reports(
          where: { team: { id: { _in: $teamIds } } }
          actionable_sla_violations: [
            first_program_response
            report_resolved
            bounty_awarded
            report_triage
          ]
          offset: $offset
          first: $pageSize
          assignee: $assignee
          has_assignee: $hasAssignee
          secure_order_by: $missedTargetsOrderBy
        ) {
          total_count
          edges {
            node {
              timer_first_program_response_miss_at
              timer_first_program_response_elapsed_time
              timer_report_resolved_miss_at
              timer_report_resolved_elapsed_time
              timer_bounty_awarded_miss_at
              timer_bounty_awarded_elapsed_time
              timer_report_triage_miss_at
              timer_report_triage_elapsed_time
              ...ActionableReportFragment
            }
          }
        }
        approachingTarget: reports(
          where: { team: { id: { _in: $teamIds } } }
          approaching_sla_violation: [
            first_program_response
            report_resolved
            bounty_awarded
            report_triage
          ]
          offset: $offset
          first: $pageSize
          assignee: $assignee
        ) {
          total_count
          edges {
            node {
              timer_first_program_response_miss_at
              timer_first_program_response_elapsed_time
              timer_report_resolved_miss_at
              timer_report_resolved_elapsed_time
              timer_bounty_awarded_miss_at
              timer_bounty_awarded_elapsed_time
              timer_report_triage_miss_at
              timer_report_triage_elapsed_time
              ...ActionableReportFragment
            }
          }
        }
        newReports: reports(
          where: { team: { id: { _in: $teamIds } } }
          substate: new
          offset: $offset
          first: $pageSize
          has_assignee: false
          secure_order_by: $sinceSubmittedOrderBy
        ) {
          total_count
          edges {
            node {
              ...ActionableReportFragment
            }
          }
        }
        upcomingDisclosures: reports(
          where: {
            upcoming_singular_disclosures: $upcomingDisclosureThreshold
            team: { id: { _in: $teamIds } }
          }
          offset: $offset
          first: $pageSize
          assignee: $assignee
          secure_order_by: $upcomingDisclosuresOrderBy
        ) {
          total_count
          edges {
            node {
              allow_singular_disclosure_after
              ...ActionableReportFragment
            }
          }
        }
        teams(where: { id: { _in: $teamIds } }) {
          nodes {
            id
            handle
            assignableTeamMemberUsers: team_members {
              edges {
                node {
                  user {
                    __typename
                    id
                    _id
                    username
                    profilePicture: profile_picture(size: small)
                  }
                }
              }
            }
            assignableTeamMemberGroups: team_member_groups {
              __typename
              id
              _id
              name
            }
          }
        }
      }
    }
    retestsNeedApproval: report_retests(
      where: {
        state: { _in: [needs_approval] }
        derived_report_retest: { team: { id: { _in: $teamIds } } }
      }
      assignee: $assignee
      offset: $offset
      first: $pageSize
    ) {
      total_count
      edges {
        node {
          report {
            ...ActionableReportFragment
          }
        }
      }
    }
  }
  ${x}
`,Ae=e`
  mutation UpdateHomepageAssigneeToNobodyMutation($reportId: ID!) {
    updateAssigneeToNobody(input: { report_id: $reportId }) {
      was_successful
      report {
        id
        assignee {
          ... on TeamMemberGroup {
            id
            type: __typename
            assigned_to_h1_triage
          }
        }
      }
    }
  }
`,je=e`
  mutation UpdateHomepageAssigneeToGroupMutation(
    $reportId: ID!
    $groupId: ID!
  ) {
    updateAssigneeToGroup(input: { report_id: $reportId, group_id: $groupId }) {
      was_successful
      errors(first: 1) {
        edges {
          node {
            id
            message
          }
        }
      }
    }
  }
`,S=e`
  mutation UpdateHomepageAssigneeToUserMutation($reportId: ID!, $userId: ID!) {
    updateAssigneeToUser(input: { report_id: $reportId, user_id: $userId }) {
      was_successful
      errors(first: 1) {
        edges {
          node {
            id
            message
          }
        }
      }
    }
  }
`,Me=e`
  query AnalyticsQueriesHomepage($queries: [AnalyticsQueryInputType!]!) {
    analytics(queries: $queries) {
      id
      uid
      keys
      values
      sql
    }
  }
`,Ne=e`
  query DataCardQueries($queries: [AnalyticsQueryInputType!]!) {
    analytics(queries: $queries) {
      id
      uid
      keys
      values
      sql
    }
  }
`,Pe={uid:`submissions-by-status`,select:[{field:n.DimReportsReportId,function:a.Count,default:`0`,as:`new_count`,where:{predicates:[{left:{ref:`dim_reports__state`},function:r.Eq,right:{string:`new`}}]}},{field:n.DimReportsReportId,function:a.Count,default:`0`,as:`pending_program_review_count`,where:{predicates:[{left:{ref:`dim_reports__state`},function:r.Eq,right:{string:`pending-program-review`}}]}},{field:n.DimReportsReportId,function:a.Count,default:`0`,as:`triaged_count`,where:{predicates:[{left:{ref:`dim_reports__state`},function:r.Eq,right:{string:`triaged`}}]}},{field:n.DimReportsReportId,function:a.Count,default:`0`,as:`retesting_count`,where:{predicates:[{left:{ref:`dim_reports__state`},function:r.Eq,right:{string:`retesting`}}]}},{field:n.DimReportsReportId,function:a.Count,default:`0`,as:`needs_more_info_count`,where:{predicates:[{left:{ref:`dim_reports__state`},function:r.Eq,right:{string:`needs-more-info`}}]}}],from:l.DimReports},Fe={uid:`triaged-submissions-by-severity`,select:[{field:n.DimReportsReportId,function:a.Count,default:`0`,as:`critical_count`,where:{predicates:[{left:{ref:n.DimReportsSeverityRating},function:r.Eq,right:{string:`critical`}}]}},{field:n.DimReportsReportId,function:a.Count,default:`0`,as:`high_count`,where:{predicates:[{left:{ref:n.DimReportsSeverityRating},function:r.Eq,right:{string:`high`}}]}},{field:n.DimReportsReportId,function:a.Count,default:`0`,as:`medium_count`,where:{predicates:[{left:{ref:n.DimReportsSeverityRating},function:r.Eq,right:{string:`medium`}}]}},{field:n.DimReportsReportId,function:a.Count,default:`0`,as:`low_count`,where:{predicates:[{left:{ref:n.DimReportsSeverityRating},function:r.Eq,right:{string:`low`}}]}},{field:n.DimReportsReportId,function:a.Count,default:`0`,as:`none_count`,where:{predicates:[{left:{ref:n.DimReportsSeverityRating},function:r.Eq,right:{nil:!0}}]}}],from:l.DimReports,where:{predicates:[{left:{ref:`dim_reports__state`},function:r.In,right:{strings:[`triaged`,`open`]}}]}},C=`open-mediations`,w=`count`,Ie={uid:C,select:[{field:n.DimMediationsMediationId,function:a.Count,default:`0`,as:w}],from:l.DimMediations,where:{predicates:[{left:{ref:n.DimMediationsState},function:r.NotIn,right:{strings:[`Closed`,`Resolved`]}}]}},T=`hackers-submitting-reports`,E=`count`,Le={uid:T,select:[{field:n.DimReportsReporterId,function:a.Count,distinct:!0,default:`0`,as:E}],from:l.DimReports,where:{predicates:[{left:{ref:n.DimReportsSubmittedAtDay},function:r.Gteq,right:{timestamp:v}}]}},D=`hackers-submitting-reports-prior-year`,O=`count`,Re={uid:D,select:[{field:n.DimReportsReporterId,function:a.Count,distinct:!0,default:`0`,as:O}],from:l.DimReports,where:{predicates:[{left:{ref:n.DimReportsSubmittedAtDay},function:r.Gteq,right:{timestamp:b}},{left:{ref:n.DimReportsSubmittedAtDay},function:r.Lt,right:{timestamp:y}}]}},k=`current-reports-on-target`,A=`past-reports-on-target`,j=`on_target`,M=`missed_target`,N={select:[{field:n.DimReportsReportId,function:a.Count,as:j,where:{predicates:[{left:{ref:`dim_reports__is_first_program_response_sla_missed`},function:r.Eq,right:{boolean:!1}},{left:{ref:`dim_reports__is_triage_sla_missed`},function:r.Eq,right:{boolean:!1}},{left:{ref:`dim_reports__is_bounty_sla_missed`},function:r.Eq,right:{boolean:!1}},{left:{ref:`dim_reports__is_resolved_sla_missed`},function:r.Eq,right:{boolean:!1}}]}},{field:n.DimReportsReportId,function:a.Count,as:M,where:{predicates:[{left:{ref:`dim_reports__is_first_program_response_sla_missed`},function:r.Eq,right:{boolean:!0},or:[{left:{ref:`dim_reports__is_triage_sla_missed`},function:r.Eq,right:{boolean:!0},or:[{left:{ref:`dim_reports__is_bounty_sla_missed`},function:r.Eq,right:{boolean:!0},or:[{left:{ref:`dim_reports__is_resolved_sla_missed`},function:r.Eq,right:{boolean:!0}}]}]}]},{left:{ref:n.DimReportsSubmittedAtDay},function:r.Lt,right:{timestamp:_}},{left:{ref:n.DimReportsSubmittedAtDay},function:r.Gteq,right:{timestamp:v}}]}}],from:l.DimReports},ze={key:`submissions_by_status`,title:`Total`,type:`pie`,half_pie:!1,use_reduced_legend:!1,data_axes:[{select_field:`new_count`,label:`New`,query_key:`submissions-by-status`,format:`integer`,color:h.new},{select_field:`pending_program_review_count`,label:`Pending Program Review`,query_key:`submissions-by-status`,format:`integer`,color:h[`pending-program-review`]},{select_field:`triaged_count`,label:`Triaged`,query_key:`submissions-by-status`,format:`integer`,color:h.triaged},{select_field:`retesting_count`,label:`Retesting`,query_key:`submissions-by-status`,format:`integer`,color:h.retesting},{select_field:`needs_more_info_count`,label:`Needs More Info`,query_key:`submissions-by-status`,format:`integer`,color:h[`needs-more-info`]}]},P=`rom-return-on-mitigation-stats`,Be=`your_rom`,Ve={uid:P,select:[],from:l.MvDimReports,variables:[],start_at:y},F=`rom-estimated-losses-avoided-stats`,He=`estimated_losses_avoided`,Ue=`yoy_estimated_losses_avoided_percent_change`,We={uid:F,select:[],from:l.MvDimReports,variables:[],start_at:y},I=`critical-high-reports`,L=`critical_or_high_reports`,R=`total_reports`,Ge={uid:I,select:[{field:n.DimReportsReportId,function:a.Count,as:L,where:{predicates:[{left:{ref:n.DimReportsSeverityRating},function:r.In,right:{strings:[`critical`,`high`]}}]}},{field:n.DimReportsReportId,function:a.Count,as:R}],from:l.DimReports,where:{predicates:[{left:{ref:n.DimReportsIsValidReport},function:r.Eq,right:{boolean:!0}},{left:{ref:n.DimReportsSubmittedAtDay},function:r.Lt,right:{timestamp:_}},{left:{ref:n.DimReportsSubmittedAtDay},function:r.Gteq,right:{timestamp:v}}]}},z=`inscope-assets`,B=`total_assets`,Ke={uid:z,select:[{field:n.DimTeamsAssetsInScopeAssetIdentifier,function:a.Count,as:B}],from:l.DimTeamsAssetsInScope},V=`inscope-assets-with-reports`,H=`assets_with_reports`,qe={uid:V,select:[{field:n.DimTeamsAssetsInScopeAssetIdentifier,function:a.Count,distinct:!0,as:H}],from:l.DimTeamsAssetsInScope,join:[{with:l.DimReports,type:o.Inner,where:{predicates:[{left:{ref:n.DimTeamsAssetsInScopeAssetIdentifier},function:r.Eq,right:{ref:n.DimReportsAssetIdentifier}}]}}],where:{predicates:[{left:{ref:n.DimReportsSubmittedAtDay},function:r.Lt,right:{timestamp:_}},{left:{ref:n.DimReportsSubmittedAtDay},function:r.Gteq,right:{timestamp:v}}]}},U=`rewards-paid-all-time`,W=`total_rewards_paid`,Je={uid:U,select:[{field:n.DimPaymentsAwardedAmount,function:a.Sum,as:W,default:`0`}],from:l.DimPayments},G=`rewards-paid-last-90-days`,Ye={uid:G,select:[{field:n.DimPaymentsAwardedAmount,function:a.Sum,as:W,default:`0`}],from:l.DimPayments,where:{predicates:[{left:{ref:n.DimPaymentsCreatedAtDay},function:r.Lt,right:{timestamp:_}},{left:{ref:n.DimPaymentsCreatedAtDay},function:r.Gteq,right:{timestamp:v}}]}},K=`rewards-paid-previous-year-90-days`,Xe={uid:K,select:[{field:n.DimPaymentsAwardedAmount,function:a.Sum,as:W,default:`0`}],from:l.DimPayments,where:{predicates:[{left:{ref:n.DimPaymentsCreatedAtDay},function:r.Lt,right:{timestamp:y}},{left:{ref:n.DimPaymentsCreatedAtDay},function:r.Gteq,right:{timestamp:b}}]}},Ze={key:`triaged_submissions_by_severity`,title:`Total in triaged state`,type:`pie`,half_pie:!1,use_reduced_legend:!1,data_axes:[{select_field:`critical_count`,label:`Critical`,query_key:`triaged-submissions-by-severity`,format:`integer`,color:g.critical},{select_field:`high_count`,label:`High`,query_key:`triaged-submissions-by-severity`,format:`integer`,color:g.high},{select_field:`medium_count`,label:`Medium`,query_key:`triaged-submissions-by-severity`,format:`integer`,color:g.medium},{select_field:`low_count`,label:`Low`,query_key:`triaged-submissions-by-severity`,format:`integer`,color:g.low},{select_field:`none_count`,label:`None`,query_key:`triaged-submissions-by-severity`,format:`integer`,color:g.none}]},q=`submissions-count`,J=`count`,Qe={uid:q,select:[{field:n.DimReportsReportId,function:a.Count,default:`0`,as:J}],from:l.DimReports,where:{predicates:[{left:{ref:n.DimReportsSubmittedAtDay},function:r.Gteq,right:{timestamp:v}}]}},Y=`submissions-count-last-year`,$e=`count`,et={uid:Y,select:[{field:n.DimReportsReportId,function:a.Count,default:`0`,as:J}],from:l.DimReports,where:{predicates:[{left:{ref:n.DimReportsSubmittedAtDay},function:r.Gteq,right:{timestamp:b}},{left:{ref:n.DimReportsSubmittedAtDay},function:r.Lt,right:{timestamp:y}}]}},X=`remediated_reports`,Z=`retests_count`,Q=`fixed_retests_count`,tt={uid:X,select:[{field:n.DimReportRetestsReportRetestId,function:a.Count,default:`0`,as:Q,where:{predicates:[{left:{ref:n.DimReportRetestsIsFixed},function:r.Eq,right:{boolean:!0}}]}},{field:n.DimReportRetestsReportRetestId,function:a.Count,default:`0`,as:Z}],from:l.DimReportRetests,where:{predicates:[{left:{ref:n.DimReportRetestsCreatedAtDay},function:r.Gteq,right:{timestamp:v}}]}},nt={dim_reports:{uid:k,where:{predicates:[{left:{ref:n.DimReportsSubmittedAtDay},function:r.Lt,right:{timestamp:_}},{left:{ref:n.DimReportsSubmittedAtDay},function:r.Gteq,right:{timestamp:v}}]}}},rt={dim_reports:{uid:A,where:{predicates:[{left:{ref:n.DimReportsSubmittedAtDay},function:r.Lt,right:{timestamp:Ce}},{left:{ref:n.DimReportsSubmittedAtDay},function:r.Gteq,right:{timestamp:we}}]}}},it=e`
  query UpcomingEventsQuery(
    $teamIds: [Int!]
    $minDate: DateInput!
    $maxDate: DateInput!
  ) {
    teams(where: { id: { _in: $teamIds } }) {
      nodes {
        id
        handle
        pentest {
          id
          _id
          name
          starts_at
          ends_at
          retesting_ends_at
          summary_report_delivery_date
        }
        spot_checks(where: { start_date: { _gte: $minDate, _lt: $maxDate } }) {
          edges {
            node {
              id
              _id
              name
              start_date
            }
          }
        }
        campaigns(
          where: {
            _or: [
              { start_date: { _gte: $minDate, _lt: $maxDate } }
              { end_date: { _gte: $minDate, _lt: $maxDate } }
            ]
          }
        ) {
          edges {
            node {
              id
              _id
              start_date
              end_date
              status
              campaign_objective {
                id
                _id
                name
              }
            }
          }
        }
      }
    }
  }
`,$=e`
  query HomepageUserQuery(
    $page: Int!
    $teamIds: [Int!]
    $pageSize: Int!
    $type: String!
    $assignee: AssigneeInputType
    $newHackerCommentsSortDirection: String
    $createdAfter: DateTime
  ) {
    me {
      id
      __typename
      unread_notification_count(
        team_ids: $teamIds
        type: $type
        user_type: "hacker"
        assignee: $assignee
        created_after: $createdAfter
      )
      newHackerComments: notifications(
        page: $page
        page_size: $pageSize
        include_read: false
        just_mentions: false
        sort_direction: $newHackerCommentsSortDirection
        team_ids: $teamIds
        type: $type
        user_type: "hacker"
        assignee: $assignee
        created_after: $createdAfter
      ) {
        id
        _id
        __typename
        type
        timestamp
        created_at
        actor_name
        avatar
        is_internal
        report {
          ...ActionableReportFragment
        }
      }
    }
  }
  ${x}
`,at=e`
  query TeamInsightsQuery($teamIds: [Int!]!) {
    teams(where: { id: { _in: $teamIds } }) {
      nodes {
        id
        _id
        i_can_manage_program
        handle
        name
        profile_picture(size: small)
        team_insights {
          edges {
            node {
              id
              _id
              insight_text
              insight_summary
              insight_data_snapshot
              insight_template {
                identifier
                recommendations {
                  _id
                  identifier
                  recommendation_text
                  value_statement
                  cost
                  required_permissions
                  learn_more_link
                }
                title
              }
              __typename
            }
            __typename
          }
          __typename
        }
        completed_recommendations {
          edges {
            node {
              recommendation_id
              user_id
              created_at
              user {
                username
              }
            }
          }
        }
        __typename
      }
      __typename
    }
  }
`,ot=e`
  query userInsightQuery {
    user_insights {
      team_insight_id
      _id
      viewed
      dismissed
    }
  }
`,st=e`
  mutation createUserInsightMutation(
    $teamInsightId: Int!
    $viewed: Boolean
    $dismissed: Boolean
  ) {
    createUserInsight(
      input: {
        team_insight_id: $teamInsightId
        viewed: $viewed
        dismissed: $dismissed
      }
    ) {
      was_successful
    }
  }
`,ct=e`
  mutation updateUserInsightMutation(
    $userInsightId: Int!
    $viewed: Boolean
    $dismissed: Boolean
  ) {
    updateUserInsight(
      input: {
        user_insight_id: $userInsightId
        viewed: $viewed
        dismissed: $dismissed
      }
    ) {
      was_successful
    }
  }
`,lt=e`
  mutation createCompletedRecommendationMutation(
    $recommendationId: Int!
    $teamId: Int!
  ) {
    createCompletedRecommendation(
      input: { recommendation_id: $recommendationId, team_id: $teamId }
    ) {
      was_successful
    }
  }
`,ut=e`
  mutation requestBountyInsights($organization_id: ID!) {
    requestBountyInsights(input: { organization_id: $organization_id }) {
      was_successful
      organization {
        id
        bounty_insights_requested
      }
    }
  }
`,dt={mediations:{queries:[Ie],description:`Open mediations`,valueFunction:ee,footerLinkText:`View details`,footerLinkTo:e=>`/organizations/${e}/analytics/dashboards/mediation`,amplitudeEventName:u.OpenMediationsDataStatCardClicked},"90d_hackers":{queries:[Le,Re],description:`Hackers submitting reports (last 90d)`,descriptionInfoText:`Includes total reports (valid and invalid). Comparison is to the same timeframe the previous year (YoY).`,valueFunction:te,footerLinkText:`View details`,footerLinkTo:e=>`/organizations/${e}/analytics/dashboards/hacker_engagement`,amplitudeEventName:u.HackersSubmittingReportsDataStatCardClicked,subscript:{style:d.Arrow,positiveTrendIsGood:!0,suffix:f.Yearly},subscriptValueFunction:ne},"90d_on_target":{queries:[s(N,nt,{}),s(N,rt,{})],description:`Reports on target (last 90d)`,descriptionInfoText:`Percentage of reports at, or below, the program's targets for times to first response, triage,  bounty, and  resolution. Percentage increase/decrease reflects absolute change from the prior 90d period.`,footerLinkText:`View details`,footerLinkTo:e=>`/organizations/${e}/analytics/dashboards/response_efficiency`,amplitudeEventName:u.ReportsOnTargetDataStatCardClicked,valueFunction:re,valueIsPercentage:!0,subscript:{style:d.Arrow,positiveTrendIsGood:!0,suffix:f.Quarterly},subscriptValueFunction:ie},"90d_critical":{queries:[Ge],description:`Critical/high signal (last 90d)`,descriptionInfoText:`Calculated by valid high & critical submissions / total valid submissions. Goal for a healthy program is 15% or higher.`,valueFunction:ae,valueIsPercentage:!0,footerLinkText:`View details`,footerLinkTo:e=>`/organizations/${e}/analytics/dashboards/submissions`,amplitudeEventName:u.DataStatCardCriticalHighClicked},"90d_scope":{queries:[qe,Ke],description:`Surface coverage (last 90d)`,descriptionInfoText:`Percent of in-scope assets that have had reports submitted against them.`,valueFunction:oe,valueIsPercentage:!0,footerLinkText:`View details`,footerLinkTo:e=>`/organizations/${e}/analytics/dashboards/submissions`,amplitudeEventName:u.DataStatCardSurfaceCoverageClicked},"90d_submissions":{queries:[Qe,et],description:`Submissions (last 90d)`,descriptionInfoText:`Calculated based on the date the report was submitted. Comparison is to the same timeframe the previous year (YoY).`,valueFunction:se,subscript:{style:d.Arrow,positiveTrendIsGood:!0,suffix:f.Yearly},subscriptValueFunction:ce,footerLinkText:`View details`,footerLinkTo:e=>`/organizations/${e}/analytics/dashboards/submissions`,amplitudeEventName:u.DataStatCardSubmissionsClicked},"90d_remediation":{queries:[tt],description:`Remediation rate (last 90d)`,descriptionInfoText:`Percentage of Retests with a Fixed status, out of all Retests requested (Fixed, Not Fixed, Pending, or Not certain status). Requires use of the “Request Retest” feature in the inbox.`,valueFunction:le,valueIsPercentage:!0,footerLinkText:`View details`,footerLinkTo:e=>`/organizations/${e}/analytics/dashboards/statistics`,amplitudeEventName:u.DataStatCardRemediationRateClicked},all_rewards:{queries:[Je],description:`Rewards paid (all time)`,descriptionInfoText:`Calculated based on actual payments distributed (not the reports submitted)`,valueFunction:ue,valueFormatter:i(c,{abbreviated:!0}),footerLinkText:`View details`,footerLinkTo:e=>`/organizations/${e}/analytics/dashboards/bounty`,amplitudeEventName:u.RewardsPaidAllTimeDataStatCardClicked},"90d_rewards":{queries:[Ye,Xe],description:`Rewards paid (last 90d)`,descriptionInfoText:`Calculated based on actual payments distributed (not the reports submitted). Comparison is to the same timeframe the previous year (YoY).`,valueFunction:de,valueFormatter:i(c,{abbreviated:!0}),footerLinkText:`View details`,footerLinkTo:e=>`/organizations/${e}/analytics/dashboards/bounty`,amplitudeEventName:u.DataStatCardRewardsPaidClicked,subscript:{style:d.Arrow,positiveTrendIsGood:!0,suffix:f.Yearly},subscriptValueFunction:fe},rom_1yr:{queries:[Ve],description:`Return on mitigation (last 1yr)`,descriptionInfoText:`The ratio of estimated mitigated losses to all bounties paid in the last year.`,valueFunction:pe,valueFormatter:e=>`${e}x`,footerLinkText:`View details`,footerLinkTo:e=>`/organizations/${e}/analytics/dashboards/return_on_mitigation`,amplitudeEventName:u.DataStatCardROMStatsClicked},mitigated_losses_1yr:{queries:[We],description:`Mitigated losses (last 1yr)`,descriptionInfoText:`Estimated monetary losses avoided by fixing vulnerabilities in the last year.`,valueFunction:me,valueFormatter:i(c,{abbreviated:!0}),footerLinkText:`View details`,footerLinkTo:e=>`/organizations/${e}/analytics/dashboards/return_on_mitigation`,amplitudeEventName:u.DataStatCardMitigatedLossesClicked,subscript:{style:d.Arrow,positiveTrendIsGood:!0,suffix:f.Yearly,valueIsPercentage:!0},subscriptValueFunction:he}};export{ot as A,Ze as C,Ae as D,je as E,S as O,Fe as S,ve as T,Oe as _,De as a,_e as b,dt as c,h as d,$ as f,Ee as g,Te as h,lt as i,ye as j,ct as k,xe as l,Pe as m,Me as n,st as o,ge as p,be as r,Ne as s,ke as t,Se as u,ut as v,it as w,at as x,ze as y};
import{o as e}from"./rolldown-runtime-DAXXjFlN.js";import{Ax as t,Fw as n,Qy as r,Rw as i,Vx as a,tb as o}from"./vendor-_WdvpBLr.js";import{Cp as s,Sm as c,bt as l,xp as u,yt as d}from"./app-5pKgUmmm.js";var f=e(i()),p=s(`
  query DuplicateInfoQuery($originalReportId: Int!, $currentReportId: Int!) {
    originalReport: report(id: $originalReportId) {
      id
      _id
      title
      substate
      self_closed
      submitted_at
      original_report {
        id
        _id
      }
      external_users {
        edges {
          node {
            id
          }
        }
      }
      report_collaborators {
        edges {
          node {
            id
          }
        }
      }
      reporter {
        id
        username
        profile_picture(size: small)
      }
    }
    currentReport: report(id: $currentReportId) {
      id
      reporter {
        id
        username
      }
    }
  }
`),m=s(`
  query TriageIntakePageReportQuery($id: Int!) {
    reports(where: { id: { _eq: $id } }) {
      nodes {
        ...TriageIntakeReport
      }
    }
    intake_workflow(report_id: $id) {
      ...WorkflowRun
    }
  }
`),h=s(`
  fragment TriageIntakeReport on Report {
    id
    _id
    title
    state
    vulnerability_information
    impact
    submitted_at

    validation_agent_conversation {
      id
    }

    exploit_agent_conversation {
      id
    }

    weakness {
      id
      name
    }

    reporter {
      id
      username
      profile_picture(size: small)
      reputation
      signal
      impact
      rank
    }

    structured_scope {
      id
      asset_identifier
    }

    team {
      id
      handle
      name
      ...Policy
      organization {
        id
        handle
        features {
          id
          key
          enabled
          disabled
          global
        }
      }
      declarative_policy {
        id
        has_open_scope
        scope_exclusions {
          ...ScopeExclusion
        }
      }
    }

    attachments {
      id
      _id
      file_name
      file_size
      content_type
      expiring_url
    }
  }
`),g=s(`
  fragment WorkflowRun on WorkflowRun {
    id
    state
    output
    started_at
    finished_at
    aborted_at
    report_id
    assignee {
      id
      _id
    }
    workflow_step_runs {
      nodes {
        ...WorkflowStepRun
      }
    }
  }
`),_=s(`
  fragment WorkflowStepRun on WorkflowStepRun {
    id
    workflow_step_type
    started_at
    finished_at
    aborted_at
    values
    output
  }
`),v=s(`
  fragment ScopeExclusion on ScopeExclusion {
    id
    category
    details
  }
`);s(`
  mutation CompleteTriageIntakeStep(
    $input: CompleteTriageIntakeStepMutationInput!
  ) {
    completeTriageIntakeStep(input: $input) {
      workflow_run {
        ...WorkflowRun
      }
      wasSuccessful: was_successful
      errors {
        nodes {
          message
          type
        }
      }
    }
  }
`);var y=s(`
  mutation EndTriageIntakeWorkflowRun(
    $input: EndTriageIntakeWorkflowRunInput!
  ) {
    endTriageIntakeWorkflowRun(input: $input) {
      workflow_run {
        ...WorkflowRun
      }
      wasSuccessful: was_successful
      errors {
        nodes {
          message
          type
        }
      }
    }
  }
`),b=s(`
  query GetReportsQuery($reportId: Int!, $teamIds: [Int!]!, $after: String) {
    reports(
      first: 5
      after: $after
      where: { id_like: $reportId, team: { id: { _in: $teamIds } } }
      order_by: { field: submitted_at, direction: DESC }
    ) {
      edges {
        node {
          id
          _id
          state
          substate
          title
          submitted_at
        }
        cursor
      }
      pageInfo {
        endCursor
      }
    }
  }
`),x=s(`
  query GetTeamIdsByReportQuery($reportId: Int!) {
    reports(where: { id: { _eq: $reportId } }) {
      nodes {
        organization {
          teams {
            nodes {
              _id
            }
          }
        }
      }
    }
  }
`),S=s(`
  query GetIntakeGoalStatusQuery {
    me {
      id
      todays_intake_count
    }
  }
`),C=s(`
  mutation ClaimNextTriageIntakeReportMutation($input: AssignNextReportInput!) {
    assignNextReport(input: $input) {
      wasSuccessful: was_successful
      errors {
        nodes {
          message
          type
        }
      }
      assigned_report {
        id
        _id
      }
    }
  }
`),w=(0,f.createContext)({intakeWorkflow:null,report:null,tabIndex:0,setTabIndex:null}),T=w.Provider,E=()=>(0,f.useContext)(w),D=`/triage_inbox?count=100&view=owned_by_me`;function O(e={}){let n=t(),r=(0,f.useContext)(u),{report:i}=E();return a(C,{variables:{input:{user_id:parseInt(r.me?.id??`0`,10),current_report_id:parseInt(i?._id??`0`,10)}},onError:t=>{e.onError?e.onError(t):(c(`error`,`Something went wrong`),n.push(D))},onCompleted:({assignNextReport:t})=>{t.wasSuccessful&&t.assigned_report?(e.onSuccess?.(),n.push(`/triage_intake/${t.assigned_report._id}`)):(c(`error`,t.errors.nodes?.[0]?.message??`Something went wrong`),n.push(D))}})}var k=n(),A=({disabled:e})=>{let[t,{loading:n}]=O({onSuccess:()=>{c(`notice`,`Next report claimed.`)},onError:e=>{console.error(e)}});return(0,k.jsx)(r,{variation:o.Primary,onClick:()=>{(async()=>{await t()})()},disabled:e||n,children:`Intake Next Report`})},j=e=>[{icon:l,label:`Find duplicates`,handleClick:t=>{window.open(`/reports/${e}/duplicates?selectedTextQueries=${encodeURIComponent(t)}&isExactMatch=true&selectedSearchParamsGroups[]=${d.TEXT_QUERIES}`)}}];export{p as a,b as c,m as d,h as f,E as i,x as l,_ as m,A as n,y as o,g as p,T as r,S as s,j as t,v as u};
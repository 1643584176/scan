import{o as e}from"./rolldown-runtime-DAXXjFlN.js";import{$_ as t,Ax as n,Bl as r,By as i,Ca as a,Dx as o,Fw as s,Gu as c,Gw as l,Hd as u,Hx as d,I_ as f,Ir as p,Iw as m,Kw as h,Ky as g,L_ as _,Ll as v,Lr as y,Ly as b,Mf as x,Mx as S,Nb as ee,Nf as C,Ou as w,Pf as T,Pl as E,Pu as D,Q_ as O,Qy as k,Rw as te,Sx as ne,Ul as re,Ux as A,Vd as j,Vx as M,Wx as ie,Xf as N,Xu as ae,Yf as P,av as F,br as I,cb as oe,cp as se,cv as ce,da as le,db as ue,eb as de,eu as fe,ev as pe,iv as L,jx as me,la as he,lb as ge,nb as R,nn as _e,ov as z,pu as ve,rb as B,rd as ye,rv as V,sd as H,sv as U,tb as W,tf as be,tp as xe,tv as Se,ua as Ce,z_ as we}from"./vendor-_WdvpBLr.js";import{$t as Te,An as Ee,Bc as De,Cp as G,Dh as Oe,Hc as K,Hf as ke,Jc as Ae,Jt as je,Ju as Me,Kf as Ne,Mc as Pe,Qt as Fe,Rc as Ie,Sm as q,Th as Le,Vc as Re,Wp as ze,Xt as Be,Y as Ve,Yc as He,Yt as Ue,Zt as We,ba as Ge,cf as Ke,dh as J,dr as qe,en as Je,hl as Ye,jn as Xe,kf as Y,ml as Ze,of as Qe,pf as $e,qi as et,t as tt,yh as nt,zc as rt}from"./app-5pKgUmmm.js";import{t as it}from"./chat_bubble-DfCZQqH2.js";import{t as at}from"./async_table_helpers-BmVZlTzm.js";import{n as ot,t as st}from"./file_upload-DC_MLapw.js";import{n as ct,r as lt,t as ut}from"./severity_calculator_container-BzOpXHf6.js";import{t as dt}from"./arrow_back-7Fs5JaL-.js";import{t as ft}from"./block-Cf3PO9NQ.js";import{t as pt}from"./edit-ClNWlmHe.js";var X=e(te()),Z=s(),mt=G(`
  fragment ReportIntentAttachment on Attachment {
    _id
    id
    file_name
    file_size
    content_type
    expiring_url
    hai_analysis_status
  }
`),ht=G(`
  mutation UploadReportIntentAttachments(
    $input: UploadReportIntentAttachmentsInput!
  ) {
    uploadReportIntentAttachments(input: $input) {
      was_successful
      attachments {
        id
        ...ReportIntentAttachment
      }
      errors {
        edges {
          node {
            message
          }
        }
      }
    }
  }
`),gt=G(`
  mutation DeleteReportIntentAttachments(
    $input: DeleteReportIntentAttachmentsInput!
  ) {
    deleteReportIntentAttachments(input: $input) {
      was_successful
      report_intent {
        id
        attachments {
          id
          ...ReportIntentAttachment
        }
      }
    }
  }
`),_t=({reportIntentId:e,attachments:t,setAttachments:n,disabled:r,readOnly:i=!1})=>{let a=typeof e==`string`,[o]=M(ht,{refetchQueries:[`ReportIntentHaiQuery`],onCompleted:e=>{if(!e.uploadReportIntentAttachments?.was_successful)return;let r=Y(mt,e.uploadReportIntentAttachments.attachments??[]),i=(t??[]).concat(r);n?.(i)}}),[s]=M(gt);return(0,Z.jsx)(Z.Fragment,{children:(0,Z.jsx)(Ve,{maxFileSizeMB:250,onFilesAdded:(0,X.useCallback)(t=>{t.length&&o({variables:{input:{files:t,report_intent_id:e}}})},[e,o]),onFilesRemoved:(0,X.useCallback)(r=>{let i=r.map(e=>e.id);if(r.length)if(a)s({variables:{input:{report_intent_id:e,attachment_ids:i}}});else{let e=(t??[]).filter(e=>!i.includes(e.id));n?.(e)}},[a,e,s,t,n]),attachments:t,disabled:r,readOnly:i})})},vt=(e,t)=>async n=>{let r=await e({variables:{input:{files:n,report_intent_id:t}}});if(!r.data?.uploadReportIntentAttachments?.was_successful)throw Error(`Failed to upload files`);let i=Y(mt,r.data.uploadReportIntentAttachments.attachments??[]);return Array.isArray(i)?i:[]},yt=G(`
  query ReportAssistantSubmissionEligibility($teamHandle: String!) {
    me {
      id
      _id
      has_active_ban
      signal
      remaining_reports: remaining_reports(team_handle: $teamHandle)
      statistics_snapshot(snapshot_type: past_year) {
        id
        signal
      }
    }
  }
`),bt=()=>{let[e,t]=(0,X.useState)(),[n]=d(yt,{onError:e=>{alert(`Something went wrong: ${e.message}`)}});return[(0,X.useCallback)(e=>{n({variables:{teamHandle:e?.program?.handle}}).then(e=>{let n=e?.data?.me?.remaining_reports,r=e?.data?.me?.statistics_snapshot;t({me:{remaining_reports:n??0,statistics_snapshot:r??null},underSignalMinimum:typeof n==`number`,reachedTrialLimit:typeof n==`number`&&n<=0,loading:!1})}).catch(e=>{throw Error(`error checking program eligibility: ${e}`)})},[n]),{eligibility:e}]},xt=e(m()),St=G(`
  query ReportIntentsHistory($search: String) {
    me {
      report_intents(first: 100, search: $search, version: 1) {
        edges {
          node {
            id
            _id
            title
            state
            created_at
            team {
              handle
            }
          }
        }
      }
    }
  }
`),Ct=G(`
  mutation DeleteReportIntent($input: DeleteReportIntentMutationInput!) {
    deleteReportIntent(input: $input) {
      was_successful
      errors {
        edges {
          node {
            message
          }
        }
      }
    }
  }
`),wt=({searchQuery:e})=>{let{data:t,loading:n,error:r}=A(St,{variables:{search:e??null}}),i=t?.me?.report_intents?.edges?.map(e=>e?.node).filter(e=>!!e)??[];return n?(0,Z.jsx)(ce,{lines:3}):r?(0,Z.jsxs)(V,{children:[`Error: `,r.message]}):(0,Z.jsx)(`div`,{className:`flex flex-col gap-lg`,children:i.length<=0?(0,Z.jsx)(V,{variation:L.Subtle,children:`Nothing to see here! Once you start a report, it'll appear here.`}):(0,Z.jsx)(`div`,{className:`flex flex-col`,children:(0,Z.jsx)(`ul`,{className:`flex flex-col gap-xs`,children:i.map(e=>(0,Z.jsx)(Tt,{databaseId:parseInt(e._id,10),title:e.title,intentId:e.id},e.id))})})})},Tt=({databaseId:e,title:t,intentId:n})=>{let r=(0,X.useRef)(null),[i,a]=(0,X.useState)(!1),[o,{loading:s}]=M(Ct,{refetchQueries:[`ReportIntentsHistory`],onCompleted:()=>{a(!1)}});return(0,Z.jsxs)(Z.Fragment,{children:[(0,Z.jsxs)(`li`,{className:`report-intents-list line-clamp-1 w-full flex items-center justify-between group group-hover:opacity-100 transition-opacity p-2xs`,children:[(0,Z.jsx)(`div`,{ref:r,className:`max-w-fit`,children:(0,Z.jsx)(J,{to:`/hai/report_assistant/${e}`,className:(0,xt.default)(`py-xs`,`text-sm flex-grow max-w-fit`,`text-neutral-400 hover:text-neutral-300 visited:text-neutral-300`,`dark:text-neutral-800 dark:hover:text-neutral-700 dark:visited:text-neutral-700`),title:t??`Report ${e}`,children:t??`Untitled report`})}),(0,Z.jsx)(k,{icons:{center:{src:I,accessibilityLabel:`Delete ${t??`Untitled report`}`}},variation:W.GhostSecondary,onClick:()=>{a(!0)},iconOnly:!0,small:!0})]},e),(0,Z.jsx)(ue,{attachToRef:r,text:t??`Untitled report`}),i&&(0,Z.jsx)(xe,{title:`Delete Draft Report`,open:i,onClose:()=>{a(!1)},confirmationButtonProps:{onClick:()=>{o({variables:{input:{report_intent_id:n}}})},children:`Confirm Delete`,loading:s},cancelButtonProps:{onClick:()=>{a(!1)},disabled:s},children:(0,Z.jsxs)(`div`,{className:`p-lg`,children:[(0,Z.jsx)(V,{children:`Are you sure you want to delete this draft report?`}),(0,Z.jsx)(`p`,{}),(0,Z.jsx)(V,{variation:L.Subtle,children:t??`Untitled report`}),(0,Z.jsx)(`div`,{className:`flex justify-end gap-sm mt-lg`})]})})]})},Et=({onSearch:e,placeholder:t=`Search report title`,debounceMs:n=300})=>{let[r,i]=(0,X.useState)(``),a=(0,X.useRef)();return(0,X.useEffect)(()=>(a.current&&clearTimeout(a.current),a.current=setTimeout(()=>{e(r)},n),()=>{a.current&&clearTimeout(a.current)}),[r,e,n]),(0,Z.jsx)(`div`,{className:`flex`,children:(0,Z.jsx)(P,{type:N.Search,value:r,onChange:e=>{i(e.target.value)},placeholder:t,icons:{left:{accessibilityLabel:`Search reports by title`,src:ve}},"data-testid":`search-input`})})},Dt=()=>{let[e,t]=(0,X.useState)(``);return(0,Z.jsxs)(`div`,{className:`flex flex-col gap-lg h-[calc(100dvh-64px)] bg-neutral-950 dark:bg-neutral-50 p-lg py-md`,children:[(0,Z.jsxs)(`div`,{children:[(0,Z.jsx)(`h2`,{className:`text-sm text-neutral-200 dark:text-neutral-600 font-bold uppercase`,children:`Reports in progress`}),(0,Z.jsx)(`div`,{className:`mt-sm`,children:(0,Z.jsx)(Et,{onSearch:e=>{t(e)},placeholder:`Search report title`})})]}),(0,Z.jsx)(`div`,{className:`flex-1 overflow-auto`,children:(0,Z.jsx)(wt,{searchQuery:e})}),(0,Z.jsx)(`hr`,{className:`text-neutral-700 dark:text-neutral-200`}),(0,Z.jsx)(`div`,{children:(0,Z.jsx)(k,{onClick:()=>{window.Intercom?.(`startSurvey`,49979815)},variation:W.Quaternary,children:`Leave feedback`})})]})},Ot=({options:e,selectedProgram:n,onProgramChange:r,disabled:i=!1,isLoading:a=!1,onSearchChange:o,onReachMenuBottom:s,hasNextPage:c})=>{let l=ie();if(a&&e.length===0)return(0,Z.jsx)(Oe,{});let u=e.map(e=>({...e,label:`${e.name} (${e.handle})`,value:e.id})),d=u.find(e=>e.id===n?.id);return(0,Z.jsxs)(`div`,{className:`mb-lg`,children:[(0,Z.jsx)(t,{htmlFor:`report-assistant-check-select-program`,text:`Select the program you want to report to`}),(0,Z.jsx)(`div`,{children:(0,Z.jsx)(H,{id:`report-assistant-check-select-program`,isSearchable:!0,placeholder:`Search programs by name or handle`,onChange:e=>{let t=e;l.query({query:je,variables:{handle:t.handle}}).then(e=>{let n=e.data?.team,i=n?.signal_requirements_setting,a=Y(Te,n?.custom_field_attributes?.nodes?.filter(e=>e!=null))??[];r({...t,signal_requirements_setting:i,customFieldAttributes:a},t?.report_template)})},onInputChange:e=>{o&&o(e)},onReachMenuBottom:()=>{c&&!a&&s&&s()},testId:`spec-select-program`,options:u,disabled:i,selectedOption:d,isLoading:a})})]})},kt=1e5,At=`#Describe the security issue you would like to report

#What steps can we follow to reproduce this issue?

#What is the impact of this issue?`,jt=54651859,Mt=G(`
  mutation CreateReportIntentHaiMutation($input: CreateReportIntentInput!) {
    createReportIntent(input: $input) {
      was_successful
      report_intent {
        id
        _id
        metadata
      }
      errors {
        edges {
          node {
            message
          }
        }
      }
    }
  }
`),Nt=()=>{let[e,r]=(0,X.useState)(At),[i,a]=(0,X.useState)(null),[o,s]=(0,X.useState)(null),[c,l]=(0,X.useState)([]),[u,d]=(0,X.useState)(``),f=n(),p=me(),{trackWithOrganizationGroup:m}=Qe(),h=new URLSearchParams(p.search).get(`programHandle`),g=tt(),{data:_,loading:v,fetchMore:b}=A(Be,{variables:{search:h??``,after:null},notifyOnNetworkStatusChange:!0}),x=((_?.me?.teams_that_i_can_submit_reports_to?.edges??[]).filter(e=>!!e).map(e=>e.node)??[]).filter(e=>!!e),{hasNextPage:S,endCursor:C}=_?.me?.teams_that_i_can_submit_reports_to?.pageInfo??{},w=x.find(e=>e.handle===h)??null,[T,{eligibility:E}]=bt();(0,X.useEffect)(()=>{w&&!i&&(a(w),T({program:w}),w.report_template&&(r(w.report_template),s(w.report_template)),h&&(d(``),b({variables:{search:``,after:null},updateQuery:(e,{fetchMoreResult:t})=>t??{}}).catch(()=>{})))},[w,i,T,h,b]);let D=(t,n)=>{if(!t)return;a(t);let i=e===At||e===o||e.trim()===``;n&&i?(r(n),s(n)):!n&&i&&(r(At),s(null)),T({program:t})},O=he((0,X.useCallback)(e=>{e!==u&&(d(e),b({variables:{search:e,after:null},updateQuery:(e,{fetchMoreResult:t})=>t??{}}).catch(()=>{}))},[b,u]),500),te=(0,X.useCallback)(()=>{S&&!v&&b({variables:{search:u,after:C},updateQuery:(e,{fetchMoreResult:t})=>{if(!t)return e;let n=e,r=t,i=n?.me?.teams_that_i_can_submit_reports_to?.edges??[],a=r?.me?.teams_that_i_can_submit_reports_to?.edges??[];return{me:{...n?.me,...r?.me,id:n?.me?.id??r?.me?.id??``,teams_that_i_can_submit_reports_to:{...n?.me?.teams_that_i_can_submit_reports_to,...r?.me?.teams_that_i_can_submit_reports_to,edges:[...i,...a],pageInfo:r?.me?.teams_that_i_can_submit_reports_to?.pageInfo??n?.me?.teams_that_i_can_submit_reports_to?.pageInfo??{hasNextPage:!1,endCursor:null}}}}}}).catch(()=>{})},[S,v,b,u,C]),[re,{loading:j}]=M(Mt,{onCompleted:e=>{if(!e.createReportIntent?.was_successful){q(`error`,`Could not create report intent.`);return}let t=e.createReportIntent?.report_intent?._id;t&&f.push(`/hai/report_assistant/${t}`)}}),[ie]=M(ht),N=typeof i?.id==`string`&&i?.id.trim().length>0,P=e.trim().length>0,F=vt(ie,null),I=ot({onFilesProcessed:F,currentText:e??``,setText:r,setAttachments:l,disabled:j||!N}),{handleDrop:oe,handleDragOver:se}=st({onFilesProcessed:F,currentText:e??``,setText:r,setAttachments:l,disabled:j||!N}),ce=()=>{localStorage.getItem(`regular_form_survey_shown`)===`true`?f.push(`/${i?.handle}/reports/new`):(localStorage.setItem(`regular_form_survey_shown`,`true`),g(`/${i?.handle}/reports/new`,jt))},le=N&&P;return(0,Z.jsxs)(ae,{children:[(0,Z.jsx)(y,{children:(0,Z.jsx)(`title`,{children:Ge(`Report Assistant`)})}),(0,Z.jsxs)(`div`,{className:`flex grow`,children:[(0,Z.jsx)(`div`,{className:`w-[300px] h-[calc(100dvh-64px)] min-w-[250px] bg-neutral-900 dark:bg-neutral-50 fixed`,children:(0,Z.jsx)(Dt,{})}),(0,Z.jsx)(`div`,{className:`flex-1 ml-[300px]`,children:(0,Z.jsx)(`div`,{className:`flex p-[1.5rem] w-full`,children:(0,Z.jsxs)(`div`,{className:`w-full`,children:[(0,Z.jsxs)(`div`,{className:`flex justify-between items-center`,children:[(0,Z.jsx)(`div`,{className:`flex-1`,children:(0,Z.jsx)(z,{size:600,children:(0,Z.jsx)(`span`,{className:`bg-gradient-to-r from-[#3F3AFC] to-[#F922A3] bg-clip-text text-transparent`,children:`Report Assistant`})})}),i?.handle&&(0,Z.jsx)(ne,{to:`/${i?.handle}/reports/new`,onClick:e=>{e.preventDefault(),ce()},className:`p-spacing-8`,children:`Switch to the regular form`})]}),(0,Z.jsx)(`div`,{children:(0,Z.jsxs)(`p`,{children:[`Report Assistant, powered by Hai, makes writing reports faster and easier. It gives your submission a clear structure, catches missing details, and helps set expectations before the program ever sees it. Think of it as a co-pilot that tidies up your draft, asks the right questions, and makes sure nothing important slips through.`,` `,(0,Z.jsx)(`a`,{href:`https://docs.hackerone.com/en/articles/12648472-report-assistant`,target:`_blank`,rel:`noopener noreferrer`,children:`Learn more`})]})}),E&&(0,Z.jsxs)(Z.Fragment,{children:[!E?.reachedTrialLimit&&E?.underSignalMinimum&&(0,Z.jsx)(lt,{me:E?.me??{statistics_snapshot:null},team:i}),(0,Z.jsx)(ct,{team:i,teamHandle:i?.handle??``,me:E?.me,showModal:(E?.reachedTrialLimit&&E?.underSignalMinimum)??!1})]}),(0,Z.jsx)(ee,{top:`24`,children:(0,Z.jsx)(Ot,{options:x,selectedProgram:i??w,onProgramChange:D,disabled:j,isLoading:v,onSearchChange:O,onReachMenuBottom:te,hasNextPage:S??!1})}),(0,Z.jsxs)(`div`,{className:`mt-lg`,children:[(0,Z.jsx)(t,{htmlFor:`report-assistant-instructions`,text:`Describe the vulnerability`}),(0,Z.jsx)(`div`,{className:`text-neutral-200 mb-md dark:text-neutral-700`,children:(0,Z.jsx)(`p`,{children:`What asset is impacted, what kind of issue it is, and how someone could reproduce it.`})}),(0,Z.jsx)(`div`,{onDrop:oe,onDragOver:se,onPaste:I,children:(0,Z.jsx)(Ae,{testId:`spec-report-assistant-instructions`,textareaId:`report-assistant-instructions`,onChange:e=>{r(e)},value:e,disabled:j||!N,attachments:c,maxLength:kt})}),(0,Z.jsx)(ee,{top:`24`}),(0,Z.jsx)(t,{htmlFor:`report-assistant-attachments`,text:`Add attachments`}),(0,Z.jsx)(`div`,{className:`text-neutral-200 mb-md dark:text-neutral-700`,children:(0,Z.jsx)(`p`,{children:`The Report Assistant will pull details from attachments and add them to the report.`})}),(0,Z.jsx)(_t,{reportIntentId:null,attachments:c,setAttachments:l,disabled:j})]}),(0,Z.jsx)(`div`,{className:`mt-lg flex justify-end items-center`,children:(0,Z.jsx)(k,{disabled:!le&&!j,testId:`spec-start-report-button`,onClick:()=>{le&&(m(`hai interaction`,{feature:`report-assistant-start-report`}),re({variables:{input:{team_id:i.id,description:e,attachment_ids:c.map(e=>e.id)}}}))},children:`Start report`})})]})})})]})]})},Pt=G(`
  mutation UpdateReportIntentHai($input: UpdateReportIntentInput!) {
    updateReportIntent(input: $input) {
      was_successful
      report_intent {
        id
        description
        title
        metadata
        state
        team {
          id
          handle
        }
        revisions {
          id
          description
          created_at
          last_pipeline_run {
            id
            state
            job_runs {
              id
              ...SubmissionFormJobRunHaiFragment
            }
          }
        }
      }
    }
  }
`),Ft=G(`
  mutation UpdateReportIntentContent(
    $reportIntentId: ID!
    $content: String!
    $customFieldValues: [CustomFieldValueInput!]
  ) {
    updateReportIntent(
      input: {
        report_intent_id: $reportIntentId
        report_intent_content_override: $content
        custom_field_values: $customFieldValues
      }
    ) {
      was_successful
      report_intent {
        id
        description
        title
        metadata
        state
      }
      errors {
        edges {
          node {
            message
          }
        }
      }
    }
  }
`),It=G(`
  mutation SubmitReportIntentHaiMutation($input: SubmitReportIntentInput!) {
    submitReportIntent(input: $input) {
      was_successful
      errors {
        edges {
          node {
            message
          }
        }
      }
      report_intent {
        id
        _id
        report {
          id
          _id
        }
      }
    }
  }
`);G(`
  mutation UploadReportIntentAttachmentsFromChat(
    $input: UploadReportIntentAttachmentsInput!
  ) {
    uploadReportIntentAttachments(input: $input) {
      was_successful
      attachments {
        id
      }
      errors {
        edges {
          node {
            message
          }
        }
      }
    }
  }
`);var Lt=G(`
  mutation UpdateReportIntentFeedback(
    $report_intent_id: ID!
    $feedback_rating: String!
  ) {
    updateReportIntentFeedback(
      input: {
        report_intent_id: $report_intent_id
        feedback_rating: $feedback_rating
      }
    ) {
      was_successful
      report_intent {
        id
        feedback_rating
      }
      errors {
        edges {
          node {
            message
          }
        }
      }
    }
  }
`),Rt={isAgentThinking:!1,isUpdatingReportIntent:!1,isSubmittingReportIntent:!1,isManuallyEditingReportIntent:!1},zt=(e,t)=>{switch(t.type){case`SET_AGENT_THINKING`:return{...e,isAgentThinking:t.payload};case`SET_UPDATING_REPORT_INTENT`:return{...e,isUpdatingReportIntent:t.payload};case`SET_SUBMITTING_REPORT_INTENT`:return{...e,isSubmittingReportIntent:t.payload};case`SET_MANUALLY_EDITING_REPORT_INTENT`:return{...e,isManuallyEditingReportIntent:t.payload};case`RESET`:return Rt;default:return e}},Bt=(0,X.createContext)([Rt,()=>{}]),Vt=({children:e})=>{let t=(0,X.useReducer)(zt,Rt);return(0,Z.jsx)(Bt.Provider,{value:t,children:e})},Q=()=>(0,X.useContext)(Bt),Ht=window.constants.reportIntent.feedbackRatings,Ut=({reportIntentId:e})=>{let[t,n]=(0,X.useState)(null),[r,i]=(0,X.useState)(!1),[,a]=Q(),[o]=M(Lt,{onCompleted:e=>{i(!1),a({type:`SET_AGENT_THINKING`,payload:!0})},onError:e=>{i(!1),q(`error`,e.message)}}),s=t=>{n(t),i(!0),o({variables:{report_intent_id:e,feedback_rating:t}})};return(0,Z.jsxs)(`div`,{className:`grid grid-rows-[min-content,1fr] mb-xs gap-xs`,children:[(0,Z.jsx)(`div`,{className:`flex`,children:(0,Z.jsx)(V,{children:`How would you rate my assistance?`})}),(0,Z.jsx)(`div`,{className:`flex gap-md mb-md`,children:Ht.map(e=>(0,Z.jsx)(k,{onClick:()=>{s(e)},variation:t===e?W.Primary:W.Secondary,disabled:r,children:e},e))})]})},Wt=()=>(0,Z.jsx)(`div`,{className:`flex justify-center items-start pt-2xs`,children:(0,Z.jsx)(`div`,{className:`flex justify-center items-center animate-spin`,children:(0,Z.jsx)(R,{src:Pe,size:B.Medium})})}),Gt=()=>(0,Z.jsx)(`div`,{className:`inline-block mt-[-2px] text-green-300`,children:(0,Z.jsx)(R,{src:c,size:B.Medium})}),Kt=()=>(0,Z.jsx)(`div`,{className:`inline-block mt-[-2px] text-red-400`,style:{verticalAlign:`2px`},children:(0,Z.jsx)(R,{src:fe,size:B.Medium})}),qt=()=>(0,Z.jsx)(`div`,{className:`inline-block mt-[-2px] text-neutral-700`,style:{verticalAlign:`2px`},children:(0,Z.jsx)(ue,{text:`This check was canceled because pre-requisite checks failed.`,children:(0,Z.jsx)(R,{src:ft,size:B.Medium})})}),Jt=()=>{let[e,t]=(0,X.useState)(``);return(0,X.useEffect)(()=>{let e=setInterval(()=>{t(e=>e.length>=3?``:e+`.`)},500);return()=>{clearInterval(e)}},[]),(0,Z.jsxs)(`div`,{children:[`Thinking`,e,(0,Z.jsx)(`span`,{className:`invisible`,children:`...`})]})},Yt=({message:e})=>(0,Z.jsx)(`div`,{className:`ml-lg p-md rounded-lg dark:bg-neutral-50 bg-neutral-950`,children:(0,Z.jsx)(Me,{disableContextMenu:!0,markdown:e,className:`text-neutral-50 dark:bg-neutral-50 dark:text-neutral-950`})}),Xt=({state:e})=>{switch(e){case ze.Pending:return(0,Z.jsx)(Wt,{});case ze.Running:return(0,Z.jsx)(Wt,{});case ze.Succeeded:return(0,Z.jsx)(Gt,{});case ze.Failed:return(0,Z.jsx)(Kt,{});case ze.Canceled:return(0,Z.jsx)(qt,{});default:return(0,Z.jsx)(Z.Fragment,{})}},Zt=({children:e})=>(0,Z.jsxs)(`div`,{className:`flex flex-col`,children:[(0,Z.jsx)(`div`,{className:`font-bold mb-xs`,children:`Report Assistant`}),e]}),Qt=({reportIntent:e})=>{let[t,n]=Q(),{trackWithOrganizationGroup:r}=Qe(),i=(0,X.useMemo)(()=>{let t=[],n=e?.revisions??[],r=!1;return n.forEach(e=>{typeof e.description==`string`&&e.description.trim()!==``&&t.push((0,Z.jsx)(Yt,{message:e.description??``}));let n=Y(Ue,e.last_pipeline_run?.job_runs??[]),i=[];for(let e=0;e<n.length;e++){let t=n[e];if(t.job_type===`assistant_summary`&&t.state===`succeeded`&&(r=!0),(t.job_type===`assistant_response`||t.job_type===`assistant_feedback_response`)&&[`running`,`pending`].includes(t.state??``)&&i.push((0,Z.jsx)(Jt,{})),t.job_type===`assistant_summary`&&n.filter(e=>e.id!==t.id).every(e=>![`pending`,`running`].includes(e.state??``))&&t.state===`pending`&&i.push((0,Z.jsx)(Jt,{})),(t.job_type===`assistant_response`||t.job_type===`assistant_feedback_response`||t.job_type===`assistant_summary`)&&typeof t.output==`object`&&t.output!==null&&Object.hasOwnProperty.call(t.output,`message`)&&typeof t.output.message==`string`){i.push((0,Z.jsx)(Me,{className:`text-neutral-50 dark:text-neutral-950 bg-transparent mb-md`,markdown:t.output.message,disableContextMenu:!0}));continue}[`assistant_response`,`assistant_feedback_response`,`assistant_summary`].includes(t.job_type)||i.push((0,Z.jsxs)(`div`,{className:`grid grid-cols-[min-content,1fr] mb-xs gap-xs`,children:[(0,Z.jsx)(Xt,{state:t.state}),(0,Z.jsx)(V,{children:t.description})]}))}i.length&&t.push((0,Z.jsx)(Zt,{children:i}))}),e?.state===`ready_to_submit`&&!e?.feedback_rating&&r&&!e?.has_failing_pipelines&&!e?.has_canceled_pipelines&&t.push((0,Z.jsx)(Zt,{children:(0,Z.jsx)(`div`,{className:`mb-md`,children:(0,Z.jsx)(Ut,{reportIntentId:e.id})})})),t},[e]),a=(0,X.useRef)(null),{ref:o,isIntersecting:s}=le({threshold:.1,initialIsIntersecting:!0}),[c,l]=(0,X.useState)(``),[u]=M(Pt,{onCompleted:e=>{n({type:`SET_UPDATING_REPORT_INTENT`,payload:!1}),e.updateReportIntent?.was_successful?l(``):q(`error`,`Could not create new revision.`)},onError:e=>{n({type:`SET_UPDATING_REPORT_INTENT`,payload:!1}),q(`error`,`Error creating revision: ${e.message}`)}}),d=i=>{i.preventDefault(),!(!c.trim()||t.isUpdatingReportIntent||!e)&&(n({type:`SET_UPDATING_REPORT_INTENT`,payload:!0}),u({variables:{input:{report_intent_id:e.id,description:c}}}).catch(()=>{n({type:`SET_UPDATING_REPORT_INTENT`,payload:!1}),q(`error`,`Error creating revision`)}),r(`hai interaction`,{feature:`report-assistant-chat`}))};(0,X.useEffect)(()=>{a.current&&s&&a.current.scrollIntoView()},[(()=>{if(!e?.revisions.length)return 0;let t=e.revisions[e.revisions.length-1],n=Y(Ue,t.last_pipeline_run?.job_runs??[]);return JSON.stringify(n.map(e=>`${e.state}-${e.output}`))})()]);let f=e=>{l(e)},p=t.isAgentThinking||t.isUpdatingReportIntent||t.isSubmittingReportIntent||t.isManuallyEditingReportIntent;return(0,Z.jsxs)(`div`,{className:`relative flex grow max-w-[450px] w-[450px] overflow-hidden mb-sm flex-col`,"data-testid":`chat-container`,children:[(0,Z.jsx)(`div`,{className:`relative flex-1 px-lg overflow-y-auto bg-y-scroll-shadow-black dark:bg-y-scroll-shadow-white rounded`,children:(0,Z.jsxs)(`div`,{className:`flex-1 relative`,children:[(0,Z.jsx)(`div`,{className:`flex flex-1 flex-col gap-lg`,children:i}),(0,Z.jsx)(`div`,{ref:e=>{o(e),a.current=e},className:`absolute bottom-0 h-[100px] w-full z-[-1]`})]})}),(0,Z.jsx)(`div`,{className:`relative w-full flex items-center justify-end pr-md`,children:(0,Z.jsx)(`div`,{className:`absolute bottom-[4px]`,children:(0,Z.jsx)(ye,{appear:!0,show:!s,enter:`transition-opacity duration-75`,enterFrom:`opacity-0`,enterTo:`opacity-100`,leave:`transition-opacity duration-150`,leaveFrom:`opacity-100`,leaveTo:`opacity-0`,children:(0,Z.jsx)(T,{color:x.Gray,size:C.ExtraSmall,icons:{left:{accessibilityLabel:`Scroll to bottom`,src:re}},onClick:()=>{a.current?.scrollIntoView({behavior:`smooth`})},children:(0,Z.jsx)(`span`,{className:`flex items-center gap-sm p-2xs`,children:`Scroll down`})})})})}),(0,Z.jsx)(`div`,{className:`p-lg border-t border-gray-200 w-full`,children:(0,Z.jsx)(`form`,{onSubmit:d,className:`flex items-end align-middle report-assistant-footer`,children:(0,Z.jsxs)(`div`,{className:`hai-text-area h-full gap-xs flex flex-row relative w-full`,children:[(0,Z.jsx)(`div`,{className:`flex-auto my-auto`,children:(0,Z.jsx)(`textarea`,{disabled:p,autoFocus:!0,value:c,placeholder:`Add some more context...`,className:`bg-white dark:!bg-black dark:!text-neutral-600 placeholder-neutral-200 dark:placeholder-neutral-600`,rows:1,onChange:e=>{f(e.target.value)},onKeyDown:e=>{if(e.code===`Enter`&&!e.shiftKey){if(e.stopPropagation(),e.preventDefault(),p)return;d(e)}}})}),!p&&(0,Z.jsx)(`div`,{className:`absolute top-xs right-xs`,children:(0,Z.jsx)(k,{testId:`hai-submit-button`,iconOnly:!0,icons:{center:{accessibilityLabel:`HaiSendIcon`,src:`data:image/svg+xml,%3csvg%20xmlns='http://www.w3.org/2000/svg'%20width='48'%20height='48'%20viewBox='0%20-960%20960%20960'%3e%3cpath%20d='M814-452%20162-178q-15%206-28.5-2.5T120-205v-550q0-16%2013.5-24.5T162-782l652%20274q18%208%2018%2028t-18%2028ZM180-253l544-227-544-230v168l242%2062-242%2060v167Zm0%200v-457%20457Z'/%3e%3c/svg%3e`}},variation:W.GhostSecondary,onClick:e=>{d(e)}})})]})})})]})},$t=({reportId:e})=>(0,Z.jsx)(`div`,{className:`flex flex-col h-full items-center justify-center`,children:(0,Z.jsxs)(`div`,{className:`flex flex-col items-center gap-lg mb-[20%]`,children:[(0,Z.jsx)(f,{illustration:`robot_handshake`}),(0,Z.jsx)(z,{size:U.Scale200,children:`Report intent already submitted`}),(0,Z.jsx)(`div`,{className:`max-w-prose`,children:(0,Z.jsx)(V,{renderAs:Se.Paragraph,align:pe.Center,children:`This report intent has already been submitted. You can view the report or go back and create a new report intent.`})}),(0,Z.jsxs)(`div`,{className:`flex flex-row gap-md`,children:[(0,Z.jsx)(k,{renderAs:de.Link,variation:W.Tertiary,to:`/hai/report_assistant`,children:`Go back`}),(0,Z.jsx)(k,{renderAs:de.Link,variation:W.Primary,to:`/reports/${encodeURIComponent(e)}`,children:`View report`})]})]})}),en=`data:image/svg+xml,%3csvg%20xmlns='http://www.w3.org/2000/svg'%20width='48'%20height='48'%20viewBox='0%20-960%20960%20960'%3e%3cpath%20d='M324-111.5Q251-143%20197-197t-85.5-127Q80-397%2080-480t31.5-156Q143-709%20197-763t127-85.5Q397-880%20480-880t156%2031.5Q709-817%20763-763t85.5%20127Q880-563%20880-480t-31.5%20156Q817-251%20763-197t-127%2085.5Q563-80%20480-80t-156-31.5ZM721-239q99-99%2099-241t-99-241q-99-99-241-99t-241%2099q-99%2099-99%20241t99%20241q99%2099%20241%2099t241-99Zm-411-71q-70-70-70-170t70-170q70-70%20170-70t170%2070q70%2070%2070%20170t-70%20170q-70%2070-170%2070t-170-70Zm297.5-42.5Q660-405%20660-480t-52.5-127.5Q555-660%20480-660t-127.5%2052.5Q300-555%20300-480t52.5%20127.5Q405-300%20480-300t127.5-52.5Zm-184-71Q400-447%20400-480t23.5-56.5Q447-560%20480-560t56.5%2023.5Q560-513%20560-480t-23.5%2056.5Q513-400%20480-400t-56.5-23.5Z'/%3e%3c/svg%3e`,tn=`data:image/svg+xml,%3csvg%20xmlns='http://www.w3.org/2000/svg'%20width='48'%20height='48'%20viewBox='0%20-960%20960%20960'%3e%3cpath%20d='M365.5-155.5Q314-191%20282-247l-75%2043q-11%206-22.5%203T167-215q-6-11-3-23t14-18l79-46q-5-17-9-34t-6-34h-92q-13%200-21.5-8.5T120-400q0-13%208.5-21.5T150-430h92q2-17%206-34t9-34l-80-47q-11-6-13.5-18t3.5-23q6-11%2017.5-13.5T207-596l74%2043q9-16%2020-29.5t23-26.5q-2-8-3-15.5t-1-15.5q0-28%2010.5-54.5T360-742l-45-44q-9-9-9-21t9-21q9-9%2021.5-9.5T358-829l49%2049q17-10%2035-15t38-5q20%200%2038%205t35%2015l50-49q9-9%2021-8.5t21%209.5q9%209%209%2021t-9%2021l-45%2045q18%2021%2028.5%2047t10.5%2054q0%208-.5%2015t-2.5%2015q12%2013%2022.5%2026.5T678-554l75-42q11-6%2022.5-3t17.5%2014q6%2011%203%2023t-14%2018l-79%2045q6%2017%209.5%2034t5.5%2035h92q13%200%2021.5%208.5T840-400q0%2013-8.5%2021.5T810-370h-92q-2%2017-5.5%2034.5T703-301l79%2046q11%206%2014%2018t-3%2023q-6%2011-17.5%2013.5T753-204l-75-43q-32%2056-83.5%2091.5T480-120q-63%200-114.5-35.5ZM381-654q23-13%2048-19.5t51-6.5q26%200%2050.5%206.5T578-655q-6-33-35-59t-63-26q-34%200-63.5%2026T381-654Zm99%20474q77%200%20128.5-69T660-400q0-75-48.5-147.5T480-620q-83%200-131.5%2072.5T300-400q0%2082%2051.5%20151T480-180Zm-21.5-108.5Q450-297%20450-310v-180q0-13%208.5-21.5T480-520q13%200%2021.5%208.5T510-490v180q0%2013-8.5%2021.5T480-280q-13%200-21.5-8.5Z'/%3e%3c/svg%3e`,nn=G(`
  fragment MetaDataContainerTeamFragment on Team {
    id
    handle
    name
  }
`),rn=({label:e,icon:t,children:n})=>(0,Z.jsx)(`div`,{className:`w-full rounded border-solid border border-neutral-700 dark:border-neutral-200`,children:(0,Z.jsxs)(`div`,{className:`p-md grid grid-cols-[min-content,auto] gap-xs items-center`,children:[(0,Z.jsx)(R,{src:t,size:B.Medium}),(0,Z.jsx)(z,{size:U.Scale200,children:e}),(0,Z.jsx)(`div`,{}),(0,Z.jsx)(`div`,{className:`overflow-hidden`,children:n})]})}),an=({program:e,impactedAsset:t,vulnerabilityType:n,cifRecommendation:r,isIncompleteReport:i})=>{let[a]=Q();return(0,Z.jsxs)(`div`,{className:(0,xt.default)(a.isManuallyEditingReportIntent&&`p-md bg-neutral-950 dark:bg-neutral-100 rounded`),children:[(0,Z.jsxs)(`div`,{className:`grid grid-cols-3 gap-md`,children:[(0,Z.jsx)(rn,{label:`Program`,icon:D,children:(0,Z.jsx)(J,{to:`/${e?.handle}`,children:(0,Z.jsx)(`div`,{className:`text-ellipsis whitespace-nowrap overflow-hidden`,title:e?.name??`Unknown`,children:e?.name??`Unknown`})})}),(0,Z.jsx)(rn,{label:`Impacted asset`,icon:en,children:(0,Z.jsxs)(`div`,{className:`flex flex-col gap-2xs`,children:[(0,Z.jsx)(`div`,{className:`text-ellipsis whitespace-nowrap overflow-hidden`,title:t?.name??`Unknown`,children:t?.name??`Unknown`}),t?.inScope===!0?(0,Z.jsx)(T,{rounded:!1,color:x.Green,children:`In scope`}):t?.inScope===!1&&(0,Z.jsx)(T,{rounded:!1,color:x.Red,children:`Out of scope`})]})}),(0,Z.jsx)(rn,{label:`Vulnerability type`,icon:tn,children:(0,Z.jsxs)(`div`,{className:`flex flex-col gap-2xs`,children:[(0,Z.jsx)(`div`,{className:`text-ellipsis whitespace-nowrap overflow-hidden`,title:n??`Unknown`,children:n??`Unknown`}),(0,Z.jsxs)(`div`,{className:`flex flex-wrap gap-2xs`,children:[r===`COMMON_INFORMATIVE_REPORTS`&&(0,Z.jsx)(T,{rounded:!1,color:x.Yellow,children:`Informative`}),r===`CORE_INELIGIBLE_FINDINGS`&&(0,Z.jsx)(T,{rounded:!1,color:x.Red,children:`Not applicable`}),i===!0&&(0,Z.jsx)(T,{rounded:!1,color:x.Blue,children:`Needs more information`})]})]})})]}),a.isManuallyEditingReportIntent&&(0,Z.jsx)(`div`,{className:`mt-md`,children:(0,Z.jsx)(V,{variation:L.Subtle,children:`This information cannot be edited, but will be updated based on the report description you provide.`})})]})},on=e=>{let t=(0,X.useMemo)(()=>t=>{let n=e.find(e=>Number(e._id)===t.id)?.__typename;if(n==null)throw Error(`Unknown custom field type for value: ${JSON.stringify(t)}`);switch(n){case`CustomFieldAttributesText`:case`CustomFieldAttributesDatetime`:return t.value;case`CustomFieldAttributesCheckbox`:return t.value===`true`;case`CustomFieldAttributesList`:return{label:t.value,value:t.value};default:return n}},[e]),n=(0,X.useMemo)(()=>e=>typeof e.value==`boolean`?{id:e.id,value:e.value?`true`:`false`}:typeof e.value==`object`&&e.value!==null?{id:e.id,value:e.value.value}:{id:e.id,value:String(e.value??``)},[]);return{coerceBackendValue:t,coerceFrontendValue:n,convertToFrontendValues:(0,X.useMemo)(()=>n=>{let r={};return n.forEach(e=>{r[e.id]=t(e)}),e.map(e=>{let t=Number(e._id);return{id:t,value:t in r?r[t]:null}})},[e,t]),prepareValuesForBackend:(0,X.useMemo)(()=>e=>e.filter(e=>e.value!==null).map(e=>n(e)),[n]),prepareValuesForMutation:(0,X.useMemo)(()=>e=>e.map(({id:e,value:t})=>({custom_field_attribute_id:String(e),value:t})),[])}},sn=(e,t)=>{let n=(0,X.useMemo)(()=>()=>{if(!e.length)return{missingFields:[],hasRegexErrors:!1,invalidFields:[]};let n=[],r=[],i=!1;return e.forEach(e=>{if(!e)return;let a=Number(e._id),o=t.find(({id:e})=>e===a);if(e.required){if(e.__typename===`CustomFieldAttributesCheckbox`){if(o?.value!==`true`){n.push(e.label);return}}else if(!o?.value.trim()){n.push(e.label);return}}e.__typename===`CustomFieldAttributesText`&&e.regex&&o?.value.trim()&&!new RegExp(e.regex).test(o.value)&&(i=!0,r.push({field:e.label,error:e.error_message??`Format does not match the required pattern`}))}),{missingFields:n,hasRegexErrors:i,invalidFields:r}},[e,t]);return{validateFields:n,isValid:(0,X.useMemo)(()=>{let e=n();return e.missingFields.length===0&&!e.hasRegexErrors},[n]),getFieldValidation:(0,X.useMemo)(()=>n=>{let r=e.find(e=>Number(e._id)===n);if(!r)return{isValid:!0};let i=t.find(({id:e})=>e===n);if(r.required){if(r.__typename===`CustomFieldAttributesCheckbox`){if(i?.value!==`true`)return{isValid:!1}}else if(!i?.value.trim())return{isValid:!1}}return r.__typename===`CustomFieldAttributesText`&&r.regex&&i?.value.trim()&&!new RegExp(r.regex).test(i.value)?{isValid:!1,errorMessage:r.error_message??`Format does not match the required pattern`}:{isValid:!0}},[e,t])}},cn=({customFieldAttributes:e,customFieldValues:n,onCustomFieldValuesChange:r})=>{let{coerceFrontendValue:i,convertToFrontendValues:o}=on(e),{getFieldValidation:s}=sn(e,n),c=(0,X.useMemo)(()=>o(n),[n,o]),l=(e,t)=>{let n=c.findIndex(t=>t.id===e),a=[...c];n>=0?a[n]={id:e,value:t}:a.push({id:e,value:t}),r(a.filter(e=>e.value!==null).map(e=>i(e)))},u=e=>c.find(t=>t.id===e)?.value??null,d=e=>{let n=Number(e._id),r=u(n),i=s(n);switch(e.__typename){case`CustomFieldAttributesText`:return(0,Z.jsx)(a,{labelText:e.label,descriptionText:e.helper_text??void 0,optional:!e.required,invalid:e.regex!=null&&!i.isValid,validationChildren:!i.isValid&&i.errorMessage?i.errorMessage:void 0,value:String(r??``),onChange:({target:e})=>{l(n,e.value)},testId:e.label.toLowerCase().replace(/\s+/g,`-`)});case`CustomFieldAttributesCheckbox`:return(0,Z.jsx)(we,{label:e.label,description:e.helper_text??void 0,options:[{id:`accept`,label:e.checkbox_text??`Accept`}],value:r?[`accept`]:[],onChange:e=>{let t=e.includes(`accept`);l(n,t)},optional:!e.required,testId:e.label.toLowerCase().replace(/\s+/g,`-`)});case`CustomFieldAttributesList`:return(0,Z.jsxs)(`span`,{children:[(0,Z.jsx)(t,{htmlFor:e._id,text:e.label,optional:!e.required}),e.helper_text!=null&&(0,Z.jsx)(O,{text:e.helper_text}),(0,Z.jsx)(H,{id:e._id,options:e.items.map(e=>({label:e,value:e})),selectedOption:r,onChange:e=>{typeof e==`object`&&e&&`value`in e&&`label`in e&&l(n,e)},testId:e.label.toLowerCase().replace(/\s+/g,`-`)})]});case`CustomFieldAttributesDatetime`:return(0,Z.jsxs)(`span`,{children:[(0,Z.jsx)(t,{htmlFor:e._id,text:e.label,optional:!e.required}),e.helper_text!=null&&(0,Z.jsx)(O,{text:e.helper_text}),(0,Z.jsx)(P,{id:e._id,type:`datetime-local`,value:String(r??``),onChange:e=>{l(n,e.target.value)},testId:e.label.toLowerCase().replace(/\s+/g,`-`)})]})}};return(0,Z.jsx)(`div`,{className:`flex flex-col gap-md`,children:e.map(e=>(0,Z.jsx)(`div`,{children:d(e)},e.id))})},ln={missingFields:[],hasRegexErrors:!1,invalidFields:[]},un=({customFieldAttributes:e,initialValues:t=[]})=>{let n=t.map(e=>`custom_field_attribute_id`in e?{id:Number(e.custom_field_attribute_id),value:e.value}:e),[r,i]=(0,X.useState)(n),[a,o]=(0,X.useState)(!1),[s,c]=(0,X.useState)(ln),{coerceFrontendValue:l,prepareValuesForMutation:u}=on(e),{validateFields:d,isValid:f}=sn(e,r);return(0,X.useEffect)(()=>{t.length>0&&i(n)},[t]),(0,X.useEffect)(()=>{r.length>0&&c(d())},[r]),{values:r,updateValues:(0,X.useCallback)(e=>{i(e.map(e=>l(e)))},[l]),validationState:s,isValid:f,validateFields:d,validateAndUpdate:(0,X.useCallback)(()=>{let e=d();return c(e),e},[d]),showValidationModal:a,setShowValidationModal:o,resetValidation:(0,X.useCallback)(()=>{c(ln),o(!1)},[]),prepareForMutation:(0,X.useCallback)(()=>u(r),[r,u])}},dn=({customFieldAttributes:e,customFieldValues:t})=>{let{convertToFrontendValues:n}=on(e),r=t.map(e=>`custom_field_attribute_id`in e?{id:Number(e.custom_field_attribute_id),value:e.value}:e),i=[];i=n(r);let a=e.filter(e=>e?._id!=null).map(e=>{let t=Number(e._id);return{id:t,attribute:e,value:i.find(e=>e.id===t)?.value??null}});return(0,Z.jsx)(`div`,{className:`z-0 rounded-md overflow-hidden`,children:(0,Z.jsx)(v,{columns:[new E().setLabel(`Field`).setAccessorKey(`id`).setCellComponent(e=>(0,Z.jsx)(`span`,{className:`font-medium`,children:e.attribute.label})),new E().setLabel(`Value`).setAccessorKey(`value`).setCellComponent(e=>{if(e.value===null)return(0,Z.jsx)(`span`,{className:`text-neutral-200 italic`,children:`Not provided`});switch(e.attribute.__typename){case`CustomFieldAttributesText`:return(0,Z.jsx)(`span`,{children:String(e.value)});case`CustomFieldAttributesCheckbox`:return(0,Z.jsx)(`span`,{children:e.value?`Yes`:`No`});case`CustomFieldAttributesList`:return(0,Z.jsx)(`span`,{children:e.value&&typeof e.value==`object`&&`label`in e.value?e.value.label:String(e.value)});case`CustomFieldAttributesDatetime`:return(0,Z.jsx)(`span`,{children:e.value?String(e.value):``});default:return(0,Z.jsx)(`span`,{children:String(e.value)})}})],data:a,testId:`custom-fields-display-table`})})},fn=({reportIntent:e,description:t,setDescription:n,isUpdatingReportIntentContent:r,customFieldValues:i,onCustomFieldValuesChange:a,onPaste:o,onDrop:s,onDragOver:c})=>{let[l]=Q(),u=Y(mt,e?.attachments)??[],d=Y(Te,(Y(Je,e?.team)?.custom_field_attributes?.nodes??[]).filter(e=>e!=null)),{values:f}=un({customFieldAttributes:d,initialValues:i??e?.metadata?.custom_field_values??[]});return(0,Z.jsx)(`div`,{className:`flex flex-col gap-md`,children:(0,Z.jsx)(`div`,{className:`mt-sm`,children:l.isManuallyEditingReportIntent?(0,Z.jsxs)(`div`,{className:`flex flex-col gap-md`,children:[(0,Z.jsx)(`div`,{onDrop:s,onDragOver:c,onPaste:o,children:(0,Z.jsx)(He,{value:t,attachments:u,disabled:r,onChange:e=>{n(e)}})}),(0,Z.jsxs)(`div`,{children:[(0,Z.jsx)(z,{renderAs:F.H2,children:`Attachments`}),(0,Z.jsx)(_t,{reportIntentId:e?.id,attachments:u,disabled:r})]}),(0,Z.jsxs)(`div`,{children:[(0,Z.jsx)(z,{renderAs:F.H2,children:`Additional Information`}),(0,Z.jsx)(cn,{customFieldAttributes:d,customFieldValues:f,onCustomFieldValuesChange:e=>{a&&a(e)}})]})]}):(0,Z.jsxs)(`div`,{className:`flex flex-col gap-md`,children:[(0,Z.jsx)(Me,{markdown:t,disableContextMenu:!0,attachments:u}),(0,Z.jsxs)(`div`,{children:[(0,Z.jsx)(z,{renderAs:F.H2,children:`Attachments`}),(0,Z.jsx)(_t,{reportIntentId:e?.id,attachments:u,readOnly:!0})]}),d.length>0&&(0,Z.jsxs)(`div`,{children:[(0,Z.jsx)(z,{renderAs:F.H2,children:`Additional Information`}),(0,Z.jsx)(dn,{customFieldAttributes:d,customFieldValues:f})]})]})})})},pn=({open:e,onClose:t,missingFields:n,hasValidationErrors:r=!1,invalidFields:i=[]})=>(0,Z.jsx)(xe,{size:`large`,open:e,title:`Validation Errors`,confirmationButtonProps:{children:`Close`,onClick:t},onClose:t,children:(0,Z.jsxs)(`div`,{className:`flex flex-col gap-md`,children:[n.length>0&&(0,Z.jsxs)(`div`,{children:[(0,Z.jsxs)(`p`,{className:`mb-sm`,children:[(0,Z.jsx)(`strong`,{children:`Missing Required Fields:`}),` The following fields must be filled out before submitting:`]}),(0,Z.jsx)(`ul`,{className:`list-disc pl-md`,children:n.map((e,t)=>(0,Z.jsx)(`li`,{className:`mb-xs`,children:e},t))})]}),i.length>0&&(0,Z.jsxs)(`div`,{children:[(0,Z.jsxs)(`p`,{className:`mb-sm`,children:[(0,Z.jsx)(`strong`,{children:`Invalid Field Values:`}),` The following fields contain invalid values:`]}),(0,Z.jsx)(`ul`,{className:`list-disc pl-md`,children:i.map((e,t)=>(0,Z.jsxs)(`li`,{className:`mb-xs`,children:[(0,Z.jsx)(`span`,{className:`font-medium`,children:e.field}),`:`,` `,e.error]},t))})]}),r&&i.length===0&&(0,Z.jsx)(`div`,{children:(0,Z.jsxs)(`p`,{className:`mb-sm`,children:[(0,Z.jsx)(`strong`,{children:`Format Errors:`}),` Some fields contain invalid values. Please check the form for validation errors.`]})}),(n.length>0||r||i.length>0)&&(0,Z.jsx)(`p`,{className:`mt-md`,children:`Please correct these issues before submitting your report.`})]})}),mn=({open:e,onClose:t,reasons:n})=>(0,Z.jsx)(xe,{size:`large`,open:e,title:`Cannot submit report`,confirmationButtonProps:{children:`Close`,onClick:t},onClose:t,children:(0,Z.jsxs)(`div`,{className:`flex flex-col gap-md`,children:[(0,Z.jsx)(`p`,{className:`mb-sm`,children:`Your report cannot be submitted at this time due to the following reasons:`}),(0,Z.jsx)(`ul`,{className:`list-disc pl-md`,children:n.map((e,t)=>(0,Z.jsx)(`li`,{className:`mb-xs`,children:e.message},t))}),(0,Z.jsx)(`p`,{className:`mt-md`,children:`Please address these issues before attempting to submit your report.`})]})}),hn=({open:e,onConfirmation:t,onCancel:n})=>(0,Z.jsx)(xe,{size:`large`,open:e,title:`Confirm Submission`,confirmationButtonProps:{children:`Submit anyway`,onClick:t},cancelButtonProps:{onClick:n},onClose:n,children:(0,Z.jsx)(`div`,{children:`Some issues were detected with your submission. Continuing may negatively impact your signal and reputation. Are you sure you want to submit?`})}),gn=({reportIntent:e,onSubmit:t})=>{let[n,r]=Q(),i=Y(nn,e?.team),{required:a}=Xe(i?.handle),[o,s]=(0,X.useState)(e?.description??``),[c,l]=(0,X.useState)(!1),[u,d]=(0,X.useState)(!1),[p,{loading:m}]=M(Ft),[h]=M(ht,{refetchQueries:[`ReportIntentHaiQuery`],onCompleted:e=>{if(!e.uploadReportIntentAttachments?.was_successful){let t=e.uploadReportIntentAttachments?.errors?.edges?.map(e=>e?.node?.message).filter(Boolean).join(`, `);q(`error`,`Failed to upload attachments: ${t}`)}},onError:e=>{q(`error`,`Error uploading attachments: ${e.message}`)}});(0,X.useEffect)(()=>{typeof e?.description==`string`&&s(e.description)},[e?.description]);let g=e?.metadata?.custom_field_values??[],_=Y(Te,((e?.team?Y(Je,e.team):null)?.custom_field_attributes?.nodes??[]).filter(e=>e!=null)),{values:v,updateValues:y,validationState:b,showValidationModal:x,setShowValidationModal:S,validateAndUpdate:ee,prepareForMutation:C}=un({customFieldAttributes:_,initialValues:g}),w=()=>{n.isManuallyEditingReportIntent&&T(),r({type:`SET_MANUALLY_EDITING_REPORT_INTENT`,payload:!n.isManuallyEditingReportIntent})},T=()=>{s(e?.description??``),y(g.map(e=>({id:e.custom_field_attribute_id,value:e.value}))),r({type:`SET_MANUALLY_EDITING_REPORT_INTENT`,payload:!1})},E=(0,X.useCallback)(()=>{if(m||!e?.id)return;r({type:`SET_UPDATING_REPORT_INTENT`,payload:!0});let t=C();p({variables:{reportIntentId:e.id,content:o??``,customFieldValues:t},refetchQueries:[`ReportIntentHaiQuery`],onCompleted:e=>{if(r({type:`SET_UPDATING_REPORT_INTENT`,payload:!1}),e.updateReportIntent.was_successful)r({type:`SET_MANUALLY_EDITING_REPORT_INTENT`,payload:!1});else{let t=e.updateReportIntent.errors?.edges?.map(e=>e?.node?.message??``).join(`, `);q(`error`,t)}},onError:()=>{r({type:`SET_UPDATING_REPORT_INTENT`,payload:!1}),q(`error`,`Error updating report content.`)}})},[m,e?.id,r,C,p,o]),D=()=>{if(_.length>0){let e=ee();if(e.missingFields.length>0||e.invalidFields.length>0){S(!0);return}}n.isManuallyEditingReportIntent?E():de?l(!0):fe?d(!0):t()},O=vt(h,e?.id??null),te=ot({onFilesProcessed:O,currentText:o??``,setText:s}),{handleDrop:ne,handleDragOver:re}=st({onFilesProcessed:O,currentText:o??``,setText:s,disabled:m}),A=n.isAgentThinking||n.isUpdatingReportIntent||n.isSubmittingReportIntent,j=e?.revisions.filter(e=>!!e)??[],ie=j.some(e=>Y(Ue,e.last_pipeline_run?.job_runs??[]).some(e=>e.job_type===`revise_intent`)),N=null,ae=null,P=null,F=null,I=e=>{let t=[];for(let n of j)if(n?.last_pipeline_run){let r=Y(Ue,n.last_pipeline_run.job_runs??[]).filter(t=>t.job_type===e&&t.output);t.push(...r)}return t.sort((e,t)=>parseInt(t._id)-parseInt(e._id))[0]},oe=I(`determine_asset`),ce=I(`analyze_cif`),le=I(`analyze_bug_class_completeness`),ue=I(`analyze_bug_type`);oe?.output&&(N=oe.output),ce?.output&&(ae=ce.output),le?.output&&(P=le.output),ue?.output&&(F=ue.output);let de=N?.structured_scope_asset_identifier&&N?.eligible_for_submission===!1,fe=e?.has_failing_pipelines??e?.has_canceled_pipelines,me=[];return N?.structured_scope_asset_identifier&&N?.eligible_for_submission===!1&&me.push({type:`out_of_scope`,message:`The identified asset "${N.structured_scope_asset_identifier}" is out of scope for this program.`}),(0,Z.jsxs)(`div`,{className:`flex flex-1 mb-lg mx-xl`,"data-testid":`report-panel`,children:[(0,Z.jsx)(pn,{open:x,onClose:()=>{S(!1)},missingFields:b.missingFields,hasValidationErrors:b.hasRegexErrors,invalidFields:b.invalidFields}),(0,Z.jsx)(mn,{open:c,onClose:()=>{l(!1)},reasons:me}),(0,Z.jsx)(hn,{open:u,onConfirmation:()=>{d(!1),t()},onCancel:()=>{d(!1)}}),(0,Z.jsx)(se,{fill:!0,children:(0,Z.jsxs)(`div`,{className:`relative flex flex-col gap-md overflow-hidden h-full`,children:[n.isAgentThinking&&(0,Z.jsxs)(ye,{appear:!0,show:!0,enter:`transition-opacity duration-150`,enterFrom:`opacity-0`,enterTo:`opacity-100`,leave:`transition-opacity duration-150`,leaveFrom:`opacity-100`,leaveTo:`opacity-0`,children:[(0,Z.jsx)(`div`,{className:`absolute w-full h-full z-10 report-panel__shimmer pointer-events-none`}),(0,Z.jsx)(`div`,{className:`absolute w-full h-full report-panel__gradient-border pointer-events-none`})]}),ie&&e?(0,Z.jsxs)(`div`,{className:(0,xt.default)(`overflow-y-auto scrollbar-hide`,n.isAgentThinking&&`opacity-70`),children:[(0,Z.jsxs)(`div`,{className:`sticky top-0 z-higher rounded-t-md bg-white dark:bg-neutral-50 flex p-md items-center justify-between border-b border-solid border-neutral-700 dark:border-neutral-200`,children:[(0,Z.jsx)(z,{size:U.Scale300,children:e.title}),(0,Z.jsxs)(`div`,{className:`flex gap-sm`,children:[n.isManuallyEditingReportIntent?(0,Z.jsx)(k,{onClick:w,variation:W.Ghost,disabled:A,children:`Cancel`}):(0,Z.jsx)(k,{testId:`edit-button`,onClick:w,variation:W.Tertiary,disabled:A,children:`Edit`}),(0,Z.jsx)(k,{variation:W.Primary,onClick:D,testId:`submit-report-button`,disabled:!n.isManuallyEditingReportIntent&&(!e.title||!e.description||e.state!==`ready_to_submit`)||A||m||a,children:n.isManuallyEditingReportIntent?`Save changes`:`Submit`})]})]}),(0,Z.jsxs)(`div`,{className:`flex flex-col gap-md p-md`,children:[(0,Z.jsx)(Ee,{teamHandle:i?.handle}),(0,Z.jsx)(an,{program:i,impactedAsset:N?.structured_scope_asset_identifier?{name:N.structured_scope_asset_identifier,inScope:N.eligible_for_submission}:void 0,vulnerabilityType:F?.bug_class,cifRecommendation:ae?.recommendation,isIncompleteReport:P?.is_incomplete_report}),(0,Z.jsx)(fn,{reportIntent:e,description:o,setDescription:s,isUpdatingReportIntentContent:m,customFieldValues:v,onCustomFieldValuesChange:y,onPaste:te,onDrop:ne,onDragOver:re}),(0,Z.jsx)(V,{variation:L.Subtle,children:`Hai can make mistakes. Make sure to verify its outputs.`})]})]}):(0,Z.jsx)(`div`,{className:`flex flex-col h-full items-center justify-center`,children:(0,Z.jsxs)(`div`,{className:`flex flex-col items-center gap-lg mb-[20%]`,children:[(0,Z.jsx)(f,{illustration:`nothing_here_2`}),(0,Z.jsx)(z,{size:U.Scale200,children:`It's quiet here without any reports.`}),(0,Z.jsx)(`div`,{className:`max-w-prose`,children:(0,Z.jsx)(V,{renderAs:Se.Paragraph,align:pe.Center,children:`Tell Hai Report Assistant about your vulnerability to start one now!`})})]})})]})})]})},_n=1e3,vn=()=>{let[e,t]=Q(),r=S(),a=n(),[o,s]=(0,X.useState)(!1);(0,X.useEffect)(()=>{t({type:`RESET`})},[t]);let{data:c,loading:l}=A(We,{variables:{id:r.id?parseInt(r.id,10):0},pollInterval:o?0:_n}),u=(c?.report_intent?.revisions.filter(e=>!!e)??[]).some(e=>[`running`,`pending`].includes(e.last_pipeline_run?.state??``));(0,X.useEffect)(()=>{s(!e.isAgentThinking)},[e.isAgentThinking]),(0,X.useEffect)(()=>{t({type:`SET_AGENT_THINKING`,payload:u})},[t,u]);let[d]=M(It,{onCompleted:e=>{if(t({type:`SET_SUBMITTING_REPORT_INTENT`,payload:!1}),!e.submitReportIntent?.was_successful){let t=e.submitReportIntent?.errors?.edges?.map(e=>e?.node?.message??``).join(`, `);q(`error`,t);return}let n=e.submitReportIntent?.report_intent?.report?._id;a.push(`/reports/${n}`)},onError:e=>{t({type:`SET_SUBMITTING_REPORT_INTENT`,payload:!1}),q(`error`,e.message)}}),f=()=>{c?.report_intent?.id&&(t({type:`SET_SUBMITTING_REPORT_INTENT`,payload:!0}),d({variables:{input:{report_intent_id:c?.report_intent?.id}}}))};return l&&!c?(0,Z.jsx)(Z.Fragment,{children:(0,Z.jsx)(Le,{})}):c?.report_intent?.state===`submitted`?(0,Z.jsx)(Z.Fragment,{children:(0,Z.jsx)($t,{reportId:c?.report_intent?.report?._id??``})}):(0,Z.jsx)(ae,{children:(0,Z.jsx)(`div`,{className:`flex gap-md overflow-hidden w-full`,children:(0,Z.jsxs)(p,{__className:`w-full h-[calc(100vh-var(--dynamic-topbar-height))]`,children:[(0,Z.jsxs)(`div`,{className:`col-span-full px-md pt-md mr-xl flex items-center h-[48px]`,children:[(0,Z.jsx)(J,{to:`/hai/report_assistant/`,className:`hover:no-underline`,"data-testid":`back-button`,children:(0,Z.jsxs)(`div`,{className:`flex text-neutral-400 dark:text-neutral-900 hover:no-underline flex-row gap-2xs items-center`,children:[(0,Z.jsx)(R,{src:dt,size:B.Medium}),`All reports`]})}),(0,Z.jsxs)(`div`,{className:`ml-auto flex items-center gap-xs`,children:[(0,Z.jsx)(`div`,{className:`mr-md`,children:(0,Z.jsx)(b,{variation:i.Warning,contentPrimary:`This report will become inaccessible as of June 2026`,actionOnClick:()=>{a.push(`/hai/report_assistant`)},actionText:`Learn more`})}),(0,Z.jsxs)(`div`,{className:`text-md text-neutral-600 dark:text-neutral-600`,children:[`Updated`,` `,c?.report_intent?.updated_at?ke({date:new Date(c.report_intent.updated_at)}):null]}),(0,Z.jsx)(`div`,{className:`inline-block`,children:(0,Z.jsx)(k,{iconOnly:!0,icons:{center:{accessibilityLabel:`Chat`,src:it}},onClick:()=>{window.Intercom?.(`startSurvey`,49979815)},variation:W.Ghost,small:!0})})]})]}),(0,Z.jsxs)(`div`,{className:`col-span-full flex flex-row -mt-xs`,style:{height:`calc(100vh - var(--dynamic-topbar-height) - 48px - 16px)`},children:[(0,Z.jsx)(Qt,{reportIntent:c?.report_intent}),(0,Z.jsx)(gn,{reportIntent:c?.report_intent,onSubmit:()=>{f()}})]})]})})})},yn=G(`
  query V1ReportIntentCount {
    me {
      id
      report_intents(version: 1) {
        total_count
      }
    }
  }
`),bn=()=>{let{data:e,loading:t}=A(yn),n=e?.me?.report_intents?.total_count??0;return t&&!e||n===0?null:(0,Z.jsx)(`div`,{className:`mb-md`,children:(0,Z.jsx)(b,{contentPrimary:`Report Assistant deprecation notice`,contentSecondary:(0,Z.jsxs)(`div`,{children:[`We have introduced a new version of Report Assistant with an improved editing experience. As part of this transition,`,` `,n,` of your older reports will no longer be accessible as of June 2026. Affected reports are indicated below with a deprecation label. Please submit or recreate them to avoid losing your work.`]}),variation:i.Warning})})},xn=G(`
  fragment ProgramOption on Team {
    id
    handle
    name
    signal_requirements_setting {
      id
      target_signal
    }
  }
`),Sn=G(`
  query SubmittablePrograms($search: String, $after: String, $first: Int) {
    me {
      id
      teams_that_i_can_submit_reports_to(
        search: $search
        after: $after
        first: $first
      ) {
        edges {
          node {
            ...ProgramOption
          }
        }
        pageInfo {
          hasNextPage
          endCursor
        }
      }
    }
  }
`),Cn=G(`
  mutation CreateReportIntentV2($input: CreateReportIntentV2Input!) {
    createReportIntentV2(input: $input) {
      was_successful
      report_intent {
        id
        _id
      }
      errors {
        edges {
          node {
            message
          }
        }
      }
    }
  }
`),wn=({selectedProgram:e})=>{let t=n(),[r,{loading:i}]=M(Cn,{onCompleted:e=>{let n=e.createReportIntentV2;n?.was_successful&&n.report_intent?._id?t.push(`/hai/report_assistant/${n.report_intent._id}?v2=1`):q(`error`,n?.errors?.edges?.[0]?.node?.message??`Failed to create report`)},onError:e=>{l(e),q(`error`,`Failed to create report: ${e.message}`)}});return(0,Z.jsx)(k,{onClick:()=>{if(!e){q(`error`,`Please select a program first`);return}r({variables:{input:{team_id:e.id}}})},disabled:!e||i,children:`Start`})},Tn=20,En=e=>{let t=me(),n=new URLSearchParams(t.search).get(`programHandle`),[r,i]=(0,X.useState)(null),[a,o]=(0,X.useState)(``),s=(0,X.useRef)(``),c=(0,X.useRef)(!1),{data:l,loading:u,fetchMore:d}=A(Sn,{variables:{search:(n??a)||null,after:null,first:Tn},fetchPolicy:`cache-first`,notifyOnNetworkStatusChange:!0}),f=l?.me?.teams_that_i_can_submit_reports_to?.edges??[],p=l?.me?.teams_that_i_can_submit_reports_to?.pageInfo,m=p?.hasNextPage??!1,h=p?.endCursor??null,g=f.map(e=>Y(xn,e?.node)).filter(e=>e!==null);(0,X.useEffect)(()=>{if(n??r??c.current)return;let e=g.find(e=>e.handle===n);e&&(i(e),c.current=!0)},[n,g,r]);let _=he((0,X.useCallback)(e=>{e!==s.current&&(s.current=e,o(e))},[]),300),v=(0,X.useCallback)(e=>{_(e)},[_]),y=(0,X.useCallback)(()=>{!m||u||d({variables:{search:(n??a)||null,after:h,first:Tn},updateQuery:(e,{fetchMoreResult:t})=>{if(!t?.me?.teams_that_i_can_submit_reports_to)return e;let n=e.me?.teams_that_i_can_submit_reports_to?.edges??[],r=t.me.teams_that_i_can_submit_reports_to.edges??[];return{...t,me:{...t.me,teams_that_i_can_submit_reports_to:{...t.me.teams_that_i_can_submit_reports_to,edges:[...n,...r]}}}}}).catch(()=>{})},[m,u,d,n,a,h]);return{programs:g,selectedProgram:r,isLoading:u,hasNextPage:m,selectProgram:(0,X.useCallback)(t=>{i(t),e?.(t)},[e]),clearSelection:(0,X.useCallback)(()=>{i(null),e?.(null)},[e]),onSearchChange:v,onLoadMore:y}},Dn=(0,X.forwardRef)(({onProgramChange:e},n)=>{let{programs:r,selectedProgram:i,isLoading:a,hasNextPage:o,selectProgram:s,clearSelection:c,onSearchChange:l,onLoadMore:u}=En(e);(0,X.useImperativeHandle)(n,()=>({clearSelection:c}));let d=r.map(e=>({...e,label:`${e.name} (${e.handle})`,value:e.id})),f=d.find(e=>e.id===i?.id);return(0,Z.jsxs)(`div`,{className:`flex flex-col gap-2xs`,children:[(0,Z.jsx)(t,{text:`Submit a new report to:`,htmlFor:`team-dropdown`}),(0,Z.jsxs)(`div`,{className:`flex gap-xs`,children:[(0,Z.jsx)(`div`,{className:`grow`,children:(0,Z.jsx)(H,{id:`team-dropdown`,options:d,selectedOption:f,onChange:e=>{s(e)},onInputChange:l,onReachMenuBottom:()=>{o&&!a&&u()},isSearchable:!0,isLoading:a,placeholder:`Search programs by name or handle`,testId:`spec-program-selector`})}),(0,Z.jsx)(wn,{selectedProgram:i})]})]})});Dn.displayName=`ProgramSelector`;var On=({value:e,onChange:t})=>(0,Z.jsx)(a,{value:e,onChange:e=>{t(e.target.value)},placeholder:`Search reports`,icons:{left:{src:ve,accessibilityLabel:`Search report history`}}}),kn=G(`
  fragment ReportIntentHistoryItem on ReportIntent {
    id
    _id
    title
    agent_version
    updated_at
    team {
      name
      profile_picture(size: small)
    }
  }
`),An=G(`
  query ReportIntentsHistoryV2(
    $search: String
    $first: Int
    $last: Int
    $after: String
    $before: String
  ) {
    me {
      report_intents(
        search: $search
        first: $first
        last: $last
        after: $after
        before: $before
      ) {
        total_count
        pageInfo {
          hasNextPage
          hasPreviousPage
          startCursor
          endCursor
        }
        edges {
          cursor
          node {
            ...ReportIntentHistoryItem
          }
        }
      }
    }
  }
`),jn=G(`
  mutation DeleteReportIntentV2($report_intent_id: ID!) {
    deleteReportIntent(input: { report_intent_id: $report_intent_id }) {
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
`),Mn=10,Nn=()=>{let[e,t]=(0,X.useState)(``),[n]=Ce(e,500),[r,i]=(0,X.useState)({first:Mn,last:null,after:``,before:``}),{data:a,loading:o}=A(An,{variables:{search:n||null,first:r.first,last:r.last,after:r.after||null,before:r.before||null}}),[s,{loading:c}]=M(jn,{refetchQueries:[An],onError:e=>{q(`error`,`Failed to delete: ${e.message}`),l(e,{tags:{product_area:`hai`,product_feature:`report_assistant`}})},onCompleted:e=>{if(!e.deleteReportIntent?.was_successful){let t=e.deleteReportIntent?.errors?.edges?.[0]?.node?.message;q(`error`,t??`Failed to delete report`),h(t??`Failed to delete report intent`,{tags:{product_area:`hai`,product_feature:`report_assistant`}})}}}),u=a?.me?.report_intents?.edges??[],d=a?.me?.report_intents?.total_count??0;return{reportIntents:u.map(e=>Y(kn,e?.node)).filter(e=>!!e),totalCount:d,isLoading:o,isDeleting:c,searchQuery:e,setSearchQuery:t,debouncedSearch:n,onTableChange:({pagination:e})=>{let t=at(u.map(e=>e?.cursor).filter(e=>!!e),e,Mn);i(t)},onDelete:e=>{s({variables:{report_intent_id:e}})},pageSize:Mn}},Pn=()=>{let{reportIntents:e,totalCount:t,isLoading:n,searchQuery:i,setSearchQuery:a,debouncedSearch:o,onTableChange:s,onDelete:c,pageSize:l}=Nn(),[u,d]=(0,X.useState)(null),f=()=>{u&&(c(u.id),d(null))},p=(0,X.useMemo)(()=>[new E().setLabel(`Report title`).setCellComponent(({_id:e,title:t})=>(0,Z.jsx)(J,{to:`/hai/report_assistant/${e}`,className:`text-blue-600 hover:underline line-clamp-1`,children:t??`Untitled report`})).create(),new E().setLabel(``).setWidth(`min-content`).setCellComponent(({agent_version:e})=>e===1?(0,Z.jsx)(T,{color:x.Yellow,rounded:!1,children:`Outdated version`}):null).create(),new E().setLabel(`Program`).setWidth(`15dvw`).setCellComponent(({team:e})=>(0,Z.jsxs)(`div`,{className:`flex items-center gap-xs whitespace-nowrap`,children:[(0,Z.jsx)(oe,{size:ge.Small,identifier:e?.name??``,src:e?.profile_picture}),(0,Z.jsx)(`span`,{className:`truncate`,children:e?.name??`No program`})]})).create(),new E().setLabel(`Updated`).setWidth(`min-content`).setCellComponent(({updated_at:e})=>(0,Z.jsx)(`span`,{className:`whitespace-nowrap`,children:Ne({date:e})})).create(),new E().setLabel(``).setWidth(`min-content`).setCellComponent(({id:e,title:t})=>(0,Z.jsx)(k,{variation:W.GhostSecondary,iconOnly:!0,icons:{center:{accessibilityLabel:`Delete`,src:I}},onClick:()=>{d({id:e,title:t})}})).create()],[]);return(0,Z.jsxs)(`div`,{className:`flex flex-col gap-md w-[80dvw] max-w-full`,children:[(0,Z.jsxs)(`span`,{className:`flex items-center justify-between`,children:[(0,Z.jsx)(z,{size:300,renderAs:F.H2,children:`History`}),(0,Z.jsx)(On,{value:i,onChange:a})]}),(0,Z.jsx)(v,{columns:p,data:e,isAsync:!0,isPaginated:!0,isLoading:n,pageSize:l,totalRowCount:t,onTableChange:s,externalFilterParams:{search:o},verticalAlignment:r.Center}),u&&(0,Z.jsx)(xe,{title:`Delete Draft Report`,variation:`destructive`,open:!!u,onClose:()=>{d(null)},confirmationButtonProps:{onClick:f,children:`Delete`},cancelButtonProps:{onClick:()=>{d(null)}},children:(0,Z.jsxs)(`div`,{className:`p-lg`,children:[(0,Z.jsx)(V,{children:`Are you sure you want to delete this draft report?`}),(0,Z.jsx)(`p`,{}),(0,Z.jsx)(V,{variation:L.Subtle,children:u.title??`Untitled report`})]})})]})},Fn=()=>{let e=(0,X.useRef)(null),[t,n]=(0,X.useState)(null),[r,{eligibility:i}]=bt(),[a,o]=(0,X.useState)(!0),s=(0,X.useCallback)(e=>{n(e),e&&r({program:{id:e.id,handle:e.handle,name:e.name}})},[r]),c=(0,X.useCallback)(()=>{e.current?.clearSelection(),n(null)},[]),l=i&&t&&i.reachedTrialLimit&&i.underSignalMinimum,u=i&&t&&!i.reachedTrialLimit&&i.underSignalMinimum;return(0,Z.jsxs)(ae,{children:[(0,Z.jsx)(y,{children:(0,Z.jsx)(`title`,{children:`Report Assistant | HackerOne`})}),(0,Z.jsxs)(`div`,{className:`flex flex-col mx-auto pt-3xl gap-3xl w-[80dvw] max-w-full`,children:[(0,Z.jsxs)(`div`,{className:`flex flex-col gap-lg`,children:[(0,Z.jsxs)(`div`,{className:`flex flex-col`,children:[(0,Z.jsx)(bn,{}),(0,Z.jsx)(z,{size:600,children:(0,Z.jsx)(`span`,{className:`bg-gradient-to-r from-[#3F3AFC] to-[#F922A3] bg-clip-text text-transparent`,children:`Report Assistant`})}),(0,Z.jsx)(V,{variation:L.Subtle,children:(0,Z.jsx)(`span`,{className:`text-neutral-600`,children:`Powered by Hai`})})]}),(0,Z.jsx)(Dn,{ref:e,onProgramChange:s}),u&&(0,Z.jsxs)(`div`,{className:`rounded border`,children:[(0,Z.jsxs)(`button`,{type:`button`,className:`flex w-full items-center justify-between px-sm py-xs text-left`,onClick:()=>{o(!a)},children:[(0,Z.jsx)(`span`,{className:`font-semibold`,children:`Caution: Signal Requirement`}),(0,Z.jsx)(R,{src:a?`data:image/svg+xml,%3csvg%20xmlns='http://www.w3.org/2000/svg'%20width='48'%20height='48'%20viewBox='0%20-960%20960%20960'%3e%3cpath%20d='M480-554%20304-378q-9%209-21%208.5t-21-9.5q-9-9-9-21.5t9-21.5l197-197q9-9%2021-9t21%209l198%20198q9%209%209%2021t-9%2021q-9%209-21.5%209t-21.5-9L480-554Z'/%3e%3c/svg%3e`:`data:image/svg+xml,%3csvg%20xmlns='http://www.w3.org/2000/svg'%20width='48'%20height='48'%20viewBox='0%20-960%20960%20960'%3e%3cpath%20d='M469-358q-5-2-10-7L261-563q-9-9-8.5-21.5T262-606q9-9%2021.5-9t21.5%209l175%20176%20176-176q9-9%2021-8.5t21%209.5q9%209%209%2021.5t-9%2021.5L501-365q-5%205-10%207t-11%202q-6%200-11-2Z'/%3e%3c/svg%3e`,size:B.Medium})]}),a&&(0,Z.jsx)(`div`,{className:`px-sm pb-sm`,children:(0,Z.jsx)(lt,{me:i.me??{statistics_snapshot:null},team:t})})]})]}),(0,Z.jsx)(Pn,{})]}),l&&(0,Z.jsx)(ct,{team:t,teamHandle:t?.handle??``,me:i.me,showModal:!0,onClose:c})]})},In=`data:image/svg+xml,%3csvg%20xmlns='http://www.w3.org/2000/svg'%20width='48'%20height='48'%20viewBox='0%20-960%20960%20960'%3e%3cpath%20d='M180-120q-24%200-42-18t-18-42v-600q0-24%2018-42t42-18h279v60H180v600h600v-279h60v279q0%2024-18%2042t-42%2018H180Zm202-219-42-43%20398-398H519v-60h321v321h-60v-218L382-339Z'/%3e%3c/svg%3e`,Ln=e=>{let{toolCallStatus:t,blockingFailureCount:n,nonBlockingFailureCount:r}=e;if(t===K.PROCESSING)return null;if(t===K.FAILED||n>0){let e=n+r;return{color:x.Red,icon:_e,accessibilityLabel:`Checks failed`,label:t===K.FAILED?`Checks failed`:`${e} issue${e===1?``:`s`}`}}return r>0?{color:x.Yellow,icon:_e,accessibilityLabel:`Checks have warnings`,label:`${r} issue${r===1?``:`s`}`}:{color:x.Green,icon:c,accessibilityLabel:`Checks passed`,label:`No issues`}},Rn=({onRerunChecks:e,onSubmit:t,disabled:n,submitDisabled:r,latestChecksSummary:i})=>{let a=i?Ln(i):null,o=(0,Z.jsx)(k,{disabled:n||r,onClick:t,children:`Submit`});return(0,Z.jsxs)(`div`,{className:`flex gap-xs items-center`,children:[a&&(0,Z.jsx)(T,{color:a.color,size:C.Small,icons:{left:{src:a.icon,accessibilityLabel:a.accessibilityLabel}},rounded:!1,onClick:()=>{document.querySelector(`#latest-status-tag`)?.scrollIntoView({behavior:g()?`instant`:`smooth`,block:`center`})},children:a.label}),(0,Z.jsx)(k,{disabled:n,onClick:e,variation:W.Secondary,children:`Run checks`}),r?(0,Z.jsx)(ue,{text:`You must run the pre submission checks before submitting the report`,children:o}):o]})},zn=G(`
  fragment CustomFieldAttributesV2 on CustomFieldAttributeInterface {
    _id
    id
    label
    helper_text
    required
    __typename
    ... on CustomFieldAttributesText {
      regex
      error_message
    }
    ... on CustomFieldAttributesList {
      items
    }
    ... on CustomFieldAttributesCheckbox {
      checkbox_text
    }
  }
`),Bn=G(`
  fragment SeverityV2 on Severity {
    _id
    id
    rating
    score
    calculation_method
    attack_vector
    attack_complexity
    privileges_required
    user_interaction
    scope
    confidentiality
    integrity
    availability
    cvss_4_point_0_metrics {
      id
      attack_vector
      attack_complexity
      attack_requirements
      privileges_required
      user_interaction
      vulnerable_confidentiality
      vulnerable_integrity
      vulnerable_availability
      subsequent_confidentiality
      subsequent_integrity
      subsequent_availability
    }
  }
`),Vn=G(`
  fragment ReportIntentV2 on ReportIntent {
    id
    _id
    agent_version
    title
    description
    impact
    state
    updated_at
    custom_fields
    pentest {
      id
      database_id: _id
    }
    pentest_check {
      id
      database_id: _id
      title
    }
    conversation {
      id
    }
    team {
      id
      name
      handle
      report_submission_form_intro
      custom_field_attributes(
        where: { internal: { _eq: false }, archived_at: { _eq: null } }
      ) {
        nodes {
          ...CustomFieldAttributesV2
        }
      }
      submission_requirements {
        severity_calculation_methods
      }
      signal_requirements_setting {
        id
        target_signal
      }
    }
    structured_scope {
      id
      database_id: _id
      asset_identifier
      asset_type
    }
    weakness {
      id
      name
      external_id
    }
    severity {
      ...SeverityV2
    }
    attachments {
      id
      ...ReportIntentAttachment
    }
  }
`),Hn=G(`
  query ReportIntentV2Query($id: Int!) {
    report_intent(id: $id) {
      ...ReportIntentV2
    }
  }
`),Un=G(`
  subscription ReportIntentV2Subscription($reportIntentId: ID!) {
    report_intent(report_intent_id: $reportIntentId) {
      ...ReportIntentV2
    }
  }
`),Wn=G(`
  mutation MessageReportAssistant($input: MessageReportAssistantInput!) {
    messageReportAssistant(input: $input) {
      was_successful
      report_intent {
        ...ReportIntentV2
      }
      errors {
        edges {
          node {
            message
          }
        }
      }
    }
  }
`),Gn=G(`
  query ReportIntentWeaknessDropdownQuery(
    $teamHandle: String!
    $first: Int
    $after: String
    $search: String
  ) {
    team(handle: $teamHandle) {
      id
      team_weaknesses(
        first: $first
        after: $after
        where: { states: [enabled] }
        search: $search
      ) {
        edges {
          node {
            id
            weakness {
              id
              name
              external_id
            }
          }
        }
        pageInfo {
          hasNextPage
          endCursor
        }
      }
    }
  }
`),Kn=G(`
  query ReportIntentAssetDropdownQuery(
    $teamHandle: String!
    $first: Int
    $after: String
    $search: String
  ) {
    team(handle: $teamHandle) {
      id
      structured_scopes(
        first: $first
        after: $after
        archived: false
        eligible_for_submission: true
        search: $search
        order_by: { field: asset_identifier, direction: ASC }
      ) {
        edges {
          node {
            id
            asset_type
            asset_identifier
          }
        }
        pageInfo {
          hasNextPage
          endCursor
        }
      }
    }
  }
`),qn=G(`
  mutation SubmitReportIntentV2Mutation($input: SubmitReportIntentInput!) {
    submitReportIntent(input: $input) {
      was_successful
      report_intent {
        id
        _id
        report {
          id
          _id
        }
      }
      errors {
        edges {
          node {
            message
          }
        }
      }
    }
  }
`),Jn=G(`
  mutation SaveReportIntent(
    $reportIntentId: ID!
    $title: String
    $description: String
    $impact: String
    $structuredScopeId: ID
    $weaknessId: ID
    $pentestCheckId: Int
    $customFieldValues: [CustomFieldValueInput!]
    $severityHash: JSON
  ) {
    saveReportIntent(
      input: {
        report_intent_id: $reportIntentId
        title: $title
        description: $description
        impact: $impact
        structured_scope_id: $structuredScopeId
        weakness_id: $weaknessId
        pentest_check_id: $pentestCheckId
        custom_field_values: $customFieldValues
        severity_hash: $severityHash
      }
    ) {
      was_successful
      report_intent {
        ...ReportIntentV2
      }
      errors {
        edges {
          node {
            message
          }
        }
      }
    }
  }
`),Yn=e(be());function Xn(e){let t={calculation_method:e.type};for(let n of Object.keys(e))t[(0,Yn.default)(n)]=e[n];return t}function Zn(e){return{rating:e.rating,score:`score`in e?e.score:void 0}}var Qn=({reportIntent:e})=>{let{updateField:t}=$(),n=Y(Bn,e?.severity),r=(0,X.useMemo)(()=>Ze(n),[n]),i=n?`with`:`without`,[a,o]=(0,X.useState)(i),[s,c]=(0,X.useState)(null);(0,X.useEffect)(()=>{o(i)},[i]),(0,X.useEffect)(()=>{n&&c(null)},[n]);let l=e?.team?.submission_requirements?.severity_calculation_methods,u=e?.team?.id??null,d=e?.structured_scope?.id??null,f=(0,X.useCallback)(e=>{c(Zn(e)),t(`severityHash`,JSON.stringify(Xn(e)))},[t]),p=(0,X.useCallback)(e=>{o(e),e===`without`&&(c(null),t(`severityHash`,``))},[t]);return{severityOption:a,severityRating:a===`without`?null:s?.rating??n?.rating,severityScore:a===`without`?null:s?.score??n?.score,calculatorSeverity:r,severityCalculationMethods:l,teamId:u,structuredScopeId:d,handleSeverityOptionChange:p,handleSeverityChange:f}},$n=(e,t)=>{let[n,r]=(0,X.useState)(!1),i=(0,X.useRef)(!1),a=(0,X.useRef)(e.length),o=e.some(e=>e.type===`ConversationEntries::AgentRunning`&&e.data.finished===!1),s=n||o;i.current=s,(0,X.useEffect)(()=>{e.length!==a.current&&r(!1),a.current=e.length},[e.length]);let[c]=M(Wn,{onError:e=>{r(!1),q(`error`,`Failed to send message: ${e.message}`)}});return{isAgentBusy:s,sendMessage:(0,X.useCallback)(e=>{!t||i.current||(r(!0),c({variables:{input:{report_intent_id:t,message:e}}}))},[t,c])}},er=`customField.`,tr=(0,X.createContext)(null),nr=1e3;function rr(e){let t=[];for(let n of Object.keys(e))if(n.startsWith(er)){let r=n.slice(12),i=n;t.push({custom_field_attribute_id:r,value:e[i]})}return t}function ir(e,t){let n={title:e?.title??``,description:e?.description??``,impact:e?.impact??``,severityHash:t?JSON.stringify(t):``},r=e?.custom_fields;if(Array.isArray(r))for(let e of r)n[`customField.${e.custom_field_attribute_id}`]=e.value;return n}var ar=({databaseId:e,children:t})=>{let{isConnected:r}=Re(),{data:i,loading:a,refetch:o,subscribeToMore:s}=A(Hn,{variables:{id:e?parseInt(e,10):0},skip:!e}),c=Y(Vn,i?.report_intent)??null,u=Y(zn,(c?.team?.custom_field_attributes?.nodes??[]).filter(e=>e!=null)),d=Y(mt,c?.attachments??[]),f=Y(Bn,c?.severity),p=(0,X.useMemo)(()=>{let e=Ze(f);return e?Xn(e):void 0},[f]);De(5e3,!r&&e?()=>{o()}:null,{fireImmediately:!0}),(0,X.useEffect)(()=>{if(c?.id)return s({document:Un,variables:{reportIntentId:c.id},updateQuery:(e,{subscriptionData:t})=>t.data?.report_intent?{report_intent:t.data.report_intent}:e})},[c?.id,s]);let{entries:m}=rt(c?.conversation?.id??null),{isAgentBusy:h,sendMessage:g}=$n(m,c?.id),[_,{eligibility:v}]=bt();(0,X.useEffect)(()=>{c?.team?.handle&&_({program:{handle:c.team.handle,id:c.team.id,name:c.team.name}})},[c?.team,_]);let[y,b]=(0,X.useState)({title:``,description:``,impact:``,severityHash:``}),x=(0,X.useRef)(!1),S=(0,X.useRef)(null),[ee,C]=(0,X.useState)(!1),w=c?.updated_at??null;(0,X.useEffect)(()=>{c&&(S.current!==c.id&&(S.current=c.id,x.current=!1),(!x.current||h)&&(b(ir(c,p)),x.current=!0))},[c,h,p]);let[T,{loading:E}]=M(Jn,{onCompleted:()=>{C(!1)},onError:e=>{C(!1),l(e),q(`error`,`Failed to save: ${e.message}`)}}),D=he((0,X.useCallback)(e=>{if(!c?.id)return;let t=ir(c,p);if(e.title===t.title&&e.description===t.description&&e.impact===t.impact&&e.severityHash===t.severityHash&&JSON.stringify(rr(e))===JSON.stringify(rr(t))){C(!1);return}let n=rr(e),r=e.severityHash?JSON.parse(e.severityHash):{};T({variables:{reportIntentId:c.id,title:e.title,description:e.description,impact:e.impact,...n.length>0?{customFieldValues:n}:{},severityHash:r}})},[c,p,T]),nr),O=(0,X.useCallback)(()=>{D.isPending()&&D.flush()},[D]),k=(0,X.useCallback)((e,t)=>{b(n=>{if(n[e]===t)return n;let r={...n,[e]:t};return C(!0),D(r),r})},[D]),te=(0,X.useCallback)(e=>{if(!c?.id)return;let{pentestCheckId:t,...n}=e;C(!0),T({variables:{reportIntentId:c.id,...n,...t===void 0?{}:{pentestCheckId:t?parseInt(t,10):null}}})},[c?.id,T]),ne=n(),[re,{loading:j}]=M(qn,{onCompleted:e=>{if(!e.submitReportIntent?.was_successful){let t=e.submitReportIntent?.errors?.edges?.map(e=>e?.node?.message??``).join(`, `);q(`error`,t);return}let t=e.submitReportIntent?.report_intent?.report?._id;ne.push(`/reports/${t}`)},onError:e=>{q(`error`,e.message)}}),ie=(0,X.useCallback)(()=>{c?.id&&(O(),re({variables:{input:{report_intent_id:c.id}}}))},[c?.id,O,re]);return(0,Z.jsx)(tr.Provider,{value:{reportIntent:c,loading:a,editState:y,updateField:k,saveFields:te,flushSave:O,isSaving:E,isSavePending:ee,lastSavedAt:w,isAgentBusy:h,sendMessage:g,submitReport:ie,isSubmitting:j,customFieldAttributes:u,attachments:d,eligibility:v,conversationEntries:m},children:t})},$=()=>{let e=(0,X.useContext)(tr);if(!e)throw Error(`useReportIntent must be used within a ReportIntentProvider`);return e},or=50,sr=(e,t)=>`${e} (${t??`Unknown`})`,cr=({disabled:e})=>{let{reportIntent:n,saveFields:r}=$(),i=n?.structured_scope,a=n?.team?.handle,[o,s]=(0,X.useState)(null),[c,l]=(0,X.useState)(``),u=he(e=>{l(e)},250),{data:d,loading:f,fetchMore:p}=A(Kn,{variables:{teamHandle:a??``,first:or,after:null,search:c||null},skip:!a}),m=d?.team?.structured_scopes?.pageInfo?.hasNextPage??!1,h=d?.team?.structured_scopes?.pageInfo?.endCursor,g=(0,X.useCallback)(()=>{p({variables:{after:h,first:or},updateQuery:(e,{fetchMoreResult:t})=>{if(!t?.team?.structured_scopes)return e;let n=e.team?.structured_scopes?.edges??[],r=t.team.structured_scopes.edges??[];return{...t,team:{...t.team,structured_scopes:{...t.team.structured_scopes,edges:[...n,...r]}}}}}).catch(()=>{})},[p,h]),_=(0,X.useMemo)(()=>{let e=d?.team?.structured_scopes?.edges;return e?e.map(e=>e?.node).filter(e=>e!=null).map(e=>({label:sr(e.asset_identifier,e.asset_type),value:e.id})):[]},[d]),v=i?{label:sr(i.asset_identifier,i.asset_type),value:i.id}:void 0,y=o&&o.value!==v?.value?o:v,b=(0,X.useCallback)(e=>{let t=e;t&&(s(t),r({structuredScopeId:t.value}))},[r]);return(0,Z.jsxs)(`div`,{className:`grow flex flex-col`,children:[(0,Z.jsx)(t,{text:`Asset`,htmlFor:`asset-dropdown`}),(0,Z.jsx)(H,{id:`asset-dropdown`,options:_,selectedOption:y,onChange:b,disabled:e,isLoading:f,onReachMenuBottom:()=>{m&&!f&&g()},onInputChange:u,filterOption:()=>!0})]})},lr=G(`
  mutation DeleteReportIntentAttachmentsV2(
    $input: DeleteReportIntentAttachmentsInput!
  ) {
    deleteReportIntentAttachments(input: $input) {
      was_successful
      report_intent {
        id
        attachments {
          id
          ...ReportIntentAttachment
        }
      }
    }
  }
`);function ur(e){let[t]=M(ht),[n]=M(lr);return{handleFilesAdded:(0,X.useCallback)(n=>{n.length&&t({variables:{input:{files:n,report_intent_id:e}}})},[e,t]),handleFilesRemoved:(0,X.useCallback)(t=>{!t.length||!e||n({variables:{input:{report_intent_id:e,attachment_ids:t.map(e=>e.id)}}})},[e,n]),processFiles:(0,X.useCallback)(async n=>{let r=await t({variables:{input:{files:n,report_intent_id:e}}});if(!r.data?.uploadReportIntentAttachments?.was_successful)throw Error(`Failed to upload files`);let i=Y(mt,r.data.uploadReportIntentAttachments.attachments??[]);return Array.isArray(i)?i:[]},[e,t])}}var dr=()=>{let{reportIntent:e,attachments:t,isAgentBusy:n}=$(),{handleFilesAdded:r,handleFilesRemoved:i}=ur(e?.id);return(0,Z.jsxs)(`div`,{className:`flex flex-col gap-xs`,children:[(0,Z.jsx)(z,{renderAs:F.H2,size:U.Scale300,children:`Attachments`}),(0,Z.jsx)(Ve,{maxFileSizeMB:250,onFilesAdded:r,onFilesRemoved:i,attachments:t,disabled:n,showHaiAnalysisStatus:!0})]})},fr=`customField.`;function pr(e,t){if(t===void 0||t===``)return null;switch(e.__typename){case`CustomFieldAttributesCheckbox`:return t===`true`;case`CustomFieldAttributesList`:return{label:t,value:t};case`CustomFieldAttributesText`:case`CustomFieldAttributesDatetime`:return t}}function mr(e,t){if(t===null)return``;switch(e.__typename){case`CustomFieldAttributesCheckbox`:return t?`true`:`false`;case`CustomFieldAttributesList`:return typeof t==`object`&&t&&`value`in t?t.value:``;case`CustomFieldAttributesText`:case`CustomFieldAttributesDatetime`:return typeof t==`string`?t:``}}function hr(e,t){if(e.required&&(t===null||t===``||typeof t==`string`&&t.trim()===``||e.__typename===`CustomFieldAttributesCheckbox`&&t!==!0))return{isValid:!1,errorMessage:`${e.label} is required`};if(e.__typename===`CustomFieldAttributesText`&&e.regex&&typeof t==`string`&&t.length>0)try{if(!new RegExp(e.regex).test(t))return{isValid:!1,errorMessage:e.error_message??`${e.label} has an invalid format`}}catch{}return{isValid:!0}}function gr(e,t,n){let r=(0,X.useMemo)(()=>{let t=new Map;for(let n of e)t.set(Number(n._id),n);return t},[e]);return{getFieldValue:(0,X.useCallback)(e=>{let n=r.get(e);return n?pr(n,t[`${fr}${e}`]):null},[r,t]),getFieldValidation:(0,X.useCallback)(e=>{let n=r.get(e);return n?hr(n,pr(n,t[`${fr}${e}`])):{isValid:!0}},[r,t]),updateField:(0,X.useCallback)((e,t)=>{let i=r.get(e);i&&n(`${fr}${e}`,mr(i,t))},[r,n]),isValid:(0,X.useMemo)(()=>e.every(e=>hr(e,pr(e,t[`${fr}${e._id}`])).isValid),[e,t])}}var _r=({attributes:e,editState:n,updateField:r,disabled:i=!1})=>{let{getFieldValue:o,getFieldValidation:s,updateField:c}=gr(e,n,r);if(e.length===0)return null;let l=e=>{let n=Number(e._id),r=o(n),l=s(n),u=e.label.toLowerCase().replace(/\s+/g,`-`);switch(e.__typename){case`CustomFieldAttributesText`:return(0,Z.jsx)(a,{labelText:e.label,descriptionText:e.helper_text??void 0,optional:!e.required,invalid:e.regex!=null&&!l.isValid,validationChildren:!l.isValid&&l.errorMessage?l.errorMessage:void 0,value:typeof r==`string`?r:``,onChange:({target:e})=>{c(n,e.value)},disabled:i,testId:u});case`CustomFieldAttributesCheckbox`:return(0,Z.jsx)(we,{label:e.label,description:e.helper_text??void 0,options:[{id:`accept`,label:e.checkbox_text??`Accept`}],value:r===!0?[`accept`]:[],onChange:e=>{c(n,e.includes(`accept`))},optional:!e.required,disabled:i,testId:u});case`CustomFieldAttributesList`:return(0,Z.jsxs)(`span`,{children:[(0,Z.jsx)(t,{htmlFor:e._id,text:e.label,optional:!e.required}),e.helper_text!=null&&(0,Z.jsx)(O,{text:e.helper_text}),(0,Z.jsx)(H,{id:e._id,options:e.items.filter(e=>e!=null).map(e=>({label:e,value:e})),selectedOption:typeof r==`object`&&r&&`value`in r?r:null,onChange:e=>{typeof e==`object`&&e&&`value`in e&&`label`in e&&c(n,e)},disabled:i,testId:u})]});case`CustomFieldAttributesDatetime`:return(0,Z.jsxs)(`span`,{children:[(0,Z.jsx)(t,{htmlFor:e._id,text:e.label,optional:!e.required}),e.helper_text!=null&&(0,Z.jsx)(O,{text:e.helper_text}),(0,Z.jsx)(P,{id:e._id,type:`datetime-local`,value:typeof r==`string`?r:``,onChange:e=>{c(n,e.target.value)},disabled:i,testId:u})]});default:return null}};return(0,Z.jsx)(`div`,{className:`flex flex-col gap-md`,children:e.map(e=>(0,Z.jsx)(`div`,{children:l(e)},e.id))})},vr=({disabled:e})=>{let{editState:t,updateField:n,flushSave:r}=$(),[i,o]=(0,X.useState)(!1);(0,X.useEffect)(()=>{e&&i&&o(!1)},[e,i]);let s=(0,X.useCallback)(e=>{n(`title`,e.target.value)},[n]),c=(0,X.useCallback)(()=>{r(),o(!1)},[r]),l=(0,X.useCallback)(e=>{e.key===`Enter`&&(r(),o(!1))},[r]);return i?(0,Z.jsx)(`span`,{className:`grow`,children:(0,Z.jsx)(a,{value:t.title,onChange:s,onBlur:c,onKeyDown:l,placeholder:`Report Title`,autoFocus:!0,maxLength:150})}):(0,Z.jsxs)(`div`,{className:`flex items-center gap-xs`,children:[(0,Z.jsx)(z,{size:U.Scale300,children:(0,Z.jsx)(`span`,{className:`line-clamp-1`,children:t.title||`Untitled report`})}),(0,Z.jsx)(`button`,{className:`flex items-center cursor-pointer text-black dark:text-white dark:hover:text-neutral-700 hover:text-neutral-200 disabled:opacity-50 disabled:cursor-not-allowed`,onClick:()=>{o(!0)},"aria-label":`Edit title`,disabled:e,children:(0,Z.jsx)(R,{src:pt,size:B.Medium})})]})},yr=Ae,br=({label:e,name:t,value:n,onChange:r,processFiles:i,attachments:a,disabled:o=!1,minimumHeight:s})=>{let c=(0,X.useCallback)(e=>{r(e)},[r]),l=ot({onFilesProcessed:i,currentText:n,setText:c,disabled:o}),{handleDrop:u,handleDragOver:d}=st({onFilesProcessed:i,currentText:n,setText:c,disabled:o});return(0,Z.jsx)(`div`,{onPaste:l,onDrop:u,onDragOver:d,children:(0,Z.jsx)(yr,{label:e,name:t,textareaId:t,minimumHeight:s,showPreview:!0,value:n,onChange:r,disabled:o,attachments:a,showHaiParaphraser:!1})})},xr=G(`
  query PentestCheckSelectorQueryV2($pentestId: ID!, $structuredScopeId: ID!) {
    pentest(id: $pentestId) {
      id
      team {
        id
        handle
      }
      pentest_structured_scope(structured_scope_id: $structuredScopeId) {
        id
        pentest_checks {
          edges {
            node {
              id
              database_id: _id
              title
              description
            }
          }
        }
      }
    }
  }
`),Sr=({onChange:e,disabled:t,pentestId:n,structuredScopeId:r,selectedPentestCheckId:a})=>{let[o,s]=(0,X.useState)(null),{data:c,loading:l,error:u}=A(xr,{variables:{pentestId:n,structuredScopeId:r??`-1`}});(0,X.useEffect)(()=>{a!==void 0&&s(a)},[a]);let d=(0,X.useRef)(r);if((0,X.useEffect)(()=>{d.current!==r&&(d.current=r,s(null),e?.(null))},[r]),l&&!c)return(0,Z.jsx)(Le,{centered:!1,overlay:!1,size:`small`});let f=c?.pentest?.pentest_structured_scope?.pentest_checks?.edges?.filter(e=>!!e).map(({node:e})=>e).filter(e=>!!e)??[],p=f.find(e=>e.database_id===o);return(0,Z.jsx)(`div`,{children:(()=>{if(u)return(0,Z.jsx)(b,{variation:i.Error,contentPrimary:`Failed to load pentest checks. Please try again`});if(!r)return(0,Z.jsx)(b,{variation:i.Warning,contentPrimary:`You need to select the asset before you can assign the pentest check`});if(!c?.pentest)return(0,Z.jsx)(b,{variation:i.Error,contentPrimary:`Pentest not found`});if(!c?.pentest?.pentest_structured_scope)return(0,Z.jsx)(b,{variation:i.Error,contentPrimary:`Selected structured scope is not part of a pentest`});if(!f.length)return(0,Z.jsx)(b,{variation:i.Warning,contentPrimary:`Selected structured scope does not have checks associated with it`})})()??(0,Z.jsxs)(Z.Fragment,{children:[(0,Z.jsx)(`div`,{className:`spec-pentest-checks type-selector`,children:(0,Z.jsx)(qe,{className:`type-selector__assets type-selector__padding_1`,children:f.map(n=>(0,Z.jsx)(`a`,{className:(0,xt.default)(`text-truncate`,`spec-pentest-check-suggestion`,`type-selector__suggestion`,{"type-selector__suggestion--selected":o===n.database_id}),href:`#`,onClick:r=>{r.preventDefault(),!t&&(s(n.database_id),e?.(n.database_id))},children:(0,Z.jsxs)(`div`,{children:[n.title,` `,(0,Z.jsx)(`div`,{className:`meta-text text-truncate`,children:n.description})]})},n.id))})}),(0,Z.jsx)(`div`,{className:`type-selector__active-asset spec-active-pentest-check`,children:o?(0,Z.jsxs)(`div`,{className:`type-selector__description`,children:[(0,Z.jsxs)(`p`,{className:`margin-10--bottom`,children:[(0,Z.jsx)(`span`,{className:`text-muted`,children:`Currently selected:`}),` (`,(0,Z.jsx)(`a`,{href:`#`,onClick:n=>{n.preventDefault(),!t&&(s(null),e?.(null))},children:`Deselect`}),`)`]}),(0,Z.jsx)(`h3`,{className:`no-margin--bottom text-truncate break-word`,children:p?.title})]}):(0,Z.jsxs)(`div`,{children:[(0,Z.jsx)(`span`,{className:`text-muted`,children:`Currently selected:`}),` None`]})})]})})},Cr=e=>{let{reportIntent:t,saveFields:n}=$(),r=t?.pentest_check?.database_id??null,[i,a]=(0,X.useState)(void 0),o=i!==void 0&&i!==r?i:r,s=e=>{a(e),n({pentestCheckId:e})};return(0,Z.jsxs)(`div`,{children:[(0,Z.jsx)(z,{renderAs:F.H2,size:U.Scale200,children:`Pentest Check`}),(0,Z.jsx)(Sr,{...e,structuredScopeId:t?.structured_scope?.database_id??null,selectedPentestCheckId:o,onChange:e=>{s(e)}})]})},wr=`data:image/svg+xml,%3csvg%20xmlns='http://www.w3.org/2000/svg'%20width='48'%20height='48'%20viewBox='0%20-960%20960%20960'%3e%3cpath%20d='m413-360-80-80q-8-8-20.5-7.5T292-439q-8%208-8%2020.5t8%2020.5l99%2098q9%209%2021%209t21-9l189-189q8-8%208-20t-8-20q-8-8-20-8t-20%208L413-360ZM251-160q-88%200-149.5-61.5T40-371q0-78%2050-137t127-71q20-97%2094-158.5T482-799q112%200%20189%2081.5T748-522v24q72-2%20122%2046.5T920-329q0%2069-50%20119t-119%2050H251Zm0-60h500q45%200%2077-32t32-77q0-45-32-77t-77-32h-63v-84q0-91-61-154t-149-63q-88%200-149.5%2063T267-522h-19q-62%200-105%2043.5T100-371q0%2063%2044%20107t107%2044Zm229-260Z'/%3e%3c/svg%3e`,Tr=e=>new Date(e).toLocaleTimeString([],{hour:`2-digit`,minute:`2-digit`}),Er=()=>{let{isSavePending:e,isSaving:t,lastSavedAt:n}=$();return e||t?(0,Z.jsx)(V,{variation:L.Subtle,children:(0,Z.jsxs)(`span`,{className:`flex items-center gap-2xs text-neutral-400 dark:text-neutral-900`,children:[(0,Z.jsx)(`span`,{className:`inline-flex animate-spin [animation-direction:reverse]`,children:(0,Z.jsx)(R,{src:w,size:B.Small})}),`Saving...`]})}):n?(0,Z.jsx)(V,{variation:L.Subtle,children:(0,Z.jsxs)(`span`,{className:`flex items-center gap-2xs text-neutral-400 dark:text-neutral-900 text-nowrap`,children:[(0,Z.jsx)(R,{src:wr,size:B.Small}),`Last saved at `,Tr(n)]})}):null},Dr=({expanded:e,onToggleExpanded:t,rating:n,score:r})=>(0,Z.jsxs)(`div`,{className:`flex items-center justify-between`,children:[(0,Z.jsx)(V,{children:(0,Z.jsx)(`strong`,{children:`Severity`})}),(0,Z.jsxs)(`div`,{className:`flex items-center gap-xs`,children:[n?(0,Z.jsx)(Ye,{severityRating:n,score:r??void 0}):(0,Z.jsx)(V,{children:(0,Z.jsx)(`span`,{className:`text-neutral-500 dark:text-neutral-400`,children:`Not set`})}),(0,Z.jsx)(`button`,{className:`flex items-center text-neutral-400 dark:text-neutral-800 enabled:hover:text-neutral-200 enabled:dark:hover:text-neutral-600 cursor-pointer`,onClick:t,"aria-label":e?`Collapse severity`:`Expand severity`,children:(0,Z.jsx)(R,{src:e?j:u,size:B.Small})})]})]}),Or=[{id:`without`,label:`Submit without severity`},{id:`with`,label:`Submit with severity`}],kr=({severityOption:e,onSeverityOptionChange:t,onSeverityChange:n,calculatorSeverity:r,severityCalculationMethods:i,teamId:a,structuredScopeId:o})=>(0,Z.jsxs)(`div`,{className:`flex flex-col gap-md`,children:[(0,Z.jsx)(_,{label:``,options:Or,value:e,onChange:e=>{t(e)}}),e===`with`&&a&&(0,Z.jsx)(ut,{teamId:a,structuredScopeId:o,severityCalculationMethods:i,severity:r,onChange:n,compact:!0})]}),Ar=()=>{let{reportIntent:e}=$(),{severityOption:t,severityRating:n,severityScore:r,calculatorSeverity:i,severityCalculationMethods:a,teamId:o,structuredScopeId:s,handleSeverityOptionChange:c,handleSeverityChange:l}=Qn({reportIntent:e}),[u,d]=(0,X.useState)(!1),[f,p]=(0,X.useState)(!1),m=(0,X.useCallback)(()=>{d(e=>(e||p(!0),!e))},[]);return(0,Z.jsxs)(`div`,{className:`border rounded-md border-solid border-neutral-700 dark:border-neutral-200 dark:bg-black bg-white`,children:[(0,Z.jsx)(`div`,{className:`flex flex-col gap-xs p-md ${u?`border-b border-solid border-neutral-700 dark:border-neutral-200`:``}`,children:(0,Z.jsx)(Dr,{expanded:u,onToggleExpanded:m,rating:n,score:r})}),f&&(0,Z.jsx)(`div`,{className:u?`p-md`:`hidden`,children:(0,Z.jsx)(kr,{severityOption:t,onSeverityOptionChange:c,onSeverityChange:l,calculatorSeverity:i,severityCalculationMethods:a,teamId:o,structuredScopeId:s})})]})},jr=50,Mr=(e,t)=>`${e}${t?` (${t})`:``}`,Nr=({disabled:e})=>{let{reportIntent:n,saveFields:r}=$(),i=n?.weakness,a=n?.team?.handle,[o,s]=(0,X.useState)(null),[c,l]=(0,X.useState)(``),u=he(e=>{l(e)},250),{data:d,loading:f,fetchMore:p}=A(Gn,{variables:{teamHandle:a??``,first:jr,after:null,search:c||null},skip:!a}),m=d?.team?.team_weaknesses?.pageInfo?.hasNextPage??!1,h=d?.team?.team_weaknesses?.pageInfo?.endCursor??null,g=(0,X.useCallback)(()=>{p({variables:{after:h,first:jr},updateQuery:(e,{fetchMoreResult:t})=>{if(!t?.team?.team_weaknesses)return e;let n=e.team?.team_weaknesses?.edges??[],r=t.team.team_weaknesses.edges??[];return{...t,team:{...t.team,team_weaknesses:{...t.team.team_weaknesses,edges:[...n,...r]}}}}}).catch(()=>{})},[p,h]),_=(0,X.useMemo)(()=>{let e=d?.team?.team_weaknesses?.edges;return e?e.map(e=>e?.node?.weakness).filter(e=>e!=null).map(e=>({label:Mr(e.name,e.external_id),value:e.id})):[]},[d]),v=i?{label:Mr(i.name,i.external_id),value:i.id}:void 0,y=o&&o.value!==v?.value?o:v,b=(0,X.useCallback)(e=>{let t=e;t&&(s(t),r({weaknessId:t.value}))},[r]);return(0,Z.jsxs)(`div`,{className:`grow flex flex-col`,children:[(0,Z.jsx)(t,{text:`Weakness`,htmlFor:`weakness-dropdown`}),(0,Z.jsx)(H,{id:`weakness-dropdown`,options:_,selectedOption:y,onChange:b,disabled:e,isLoading:f,onReachMenuBottom:()=>{m&&!f&&g()},onInputChange:u,filterOption:()=>!0})]})},Pr=()=>{let{editState:e,updateField:t,isAgentBusy:n,customFieldAttributes:r,attachments:i,reportIntent:a}=$(),{processFiles:o}=ur(a?.id),s=(0,X.useCallback)(e=>{t(`description`,e)},[t]),c=(0,X.useCallback)(e=>{t(`impact`,e)},[t]);return(0,Z.jsxs)(`div`,{children:[n&&(0,Z.jsxs)(`div`,{className:`fixed overflow-hidden rolling-square-container py-[45vh] px-[29vw] z-50 pointer-events-none`,children:[(0,Z.jsx)(`div`,{className:`square`}),(0,Z.jsx)(`div`,{className:`infinite-scroll`})]}),(0,Z.jsxs)(`div`,{className:`w-full min-h-0 pb-lg z-10`+(n?` pointer-events-none opacity-15`:``),children:[typeof a?.team?.report_submission_form_intro==`string`&&(0,Z.jsx)(`div`,{className:`mb-md`,children:(0,Z.jsx)(se,{children:(0,Z.jsx)(`div`,{className:`px-md pt-md`,children:(0,Z.jsx)(Me,{className:`markdownable mb-md spec-form-intro`,markdown:a.team.report_submission_form_intro})})})}),(0,Z.jsxs)(`div`,{className:`relative`,children:[(0,Z.jsx)(`div`,{className:`sticky top-0 bg-white dark:bg-black z-above`,children:(0,Z.jsxs)(`div`,{className:`p-md border rounded-t-md border-solid border-neutral-700 dark:border-neutral-200 flex items-center justify-between`,children:[(0,Z.jsx)(vr,{disabled:n}),(0,Z.jsx)(Er,{})]})}),(0,Z.jsxs)(`div`,{className:`flex flex-col p-md gap-lg border border-solid border-neutral-700 dark:border-neutral-200 border-t-0 rounded-b-md`,children:[(0,Z.jsxs)(`div`,{className:`grid grid-cols-2 gap-sm w-full`,children:[(0,Z.jsx)(cr,{disabled:n}),(0,Z.jsx)(Nr,{disabled:n})]}),(0,Z.jsx)(Ar,{}),a?.pentest?.database_id&&(0,Z.jsx)(Cr,{pentestId:a.pentest.database_id,disabled:n}),(0,Z.jsx)(`div`,{className:`-mt-xs`,children:(0,Z.jsx)(br,{label:`Description`,name:`report-intent-description`,minimumHeight:200,value:e.description,onChange:s,processFiles:o,attachments:i,disabled:n})}),(0,Z.jsx)(`div`,{className:`-mt-xs`,children:(0,Z.jsx)(br,{label:`Impact`,name:`report-intent-impact`,value:e.impact,onChange:c,processFiles:o,attachments:i,disabled:n})}),(0,Z.jsx)(dr,{}),r.length>0&&(0,Z.jsxs)(`div`,{className:`flex flex-col gap-xs`,children:[(0,Z.jsx)(z,{renderAs:F.H2,size:U.Scale300,children:`Additional information`}),(0,Z.jsx)(_r,{attributes:r,editState:e,updateField:t,disabled:n})]})]})]})]})]})},Fr=(0,X.createContext)({register:()=>{},isLatestEntry:()=>!1,updateLatestSummary:()=>{},latestSummary:null}),Ir=({children:e})=>{let t=(0,X.useRef)(null),[n,r]=(0,X.useState)(null),i=(0,X.useCallback)(e=>{t.current=e},[]),a=(0,X.useCallback)(e=>t.current===e,[]),o=(0,X.useCallback)(e=>{r(e)},[]);return(0,Z.jsx)(Fr.Provider,{value:{register:i,isLatestEntry:a,updateLatestSummary:o,latestSummary:n},children:e})},Lr=()=>(0,X.useContext)(Fr),Rr=(0,X.createContext)(()=>{}),zr=({sendMessage:e,children:t})=>(0,Z.jsx)(Rr.Provider,{value:e,children:t}),Br=()=>(0,X.useContext)(Rr),Vr=({check:e})=>(0,Z.jsxs)(`div`,{className:`flex flex-col gap-2xs`,children:[(0,Z.jsxs)(`div`,{className:`flex items-center gap-xs`,children:[e.status!==`passed`&&(0,Z.jsx)(T,{color:e.blocking?x.Red:x.Yellow,size:C.ExtraSmall,rounded:!1,iconOnly:!0,icons:{center:{src:`data:image/svg+xml,%3csvg%20xmlns='http://www.w3.org/2000/svg'%20width='48'%20height='48'%20viewBox='0%20-960%20960%20960'%3e%3cpath%20d='M92-120q-9%200-15.5-4T66-135q-4-7-4.5-14.5T66-165l388-670q5-8%2011.5-11.5T480-850q8%200%2014.5%203.5T506-835l388%20670q5%208%204.5%2015.5T894-135q-4%207-10.5%2011t-15.5%204H92Zm52-60h672L480-760%20144-180Zm361.5-65.5Q514-254%20514-267t-8.5-21.5Q497-297%20484-297t-21.5%208.5Q454-280%20454-267t8.5%2021.5Q471-237%20484-237t21.5-8.5Zm0-111Q514-365%20514-378v-164q0-13-8.5-21.5T484-572q-13%200-21.5%208.5T454-542v164q0%2013%208.5%2021.5T484-348q13%200%2021.5-8.5ZM480-470Z'/%3e%3c/svg%3e`,accessibilityLabel:e.blocking?`Blocking issue`:`Warning`}},children:e.blocking?`Blocking issue`:`Warning`}),(0,Z.jsx)(V,{children:(0,Z.jsx)(`strong`,{children:e.label})})]}),e.description&&(0,Z.jsx)(V,{children:(0,Z.jsx)(`span`,{children:e.description})})]}),Hr=`data:image/svg+xml,%3csvg%20xmlns='http://www.w3.org/2000/svg'%20width='48'%20height='48'%20viewBox='0%20-960%20960%20960'%3e%3cpath%20d='M339.5-108Q274-136%20225-185t-77-114.5Q120-365%20120-440q0-13%208.5-21.5T150-470q13%200%2021.5%208.5T180-440q0%20125%2087.5%20212.5T480-140q125%200%20212.5-87.5T780-440q0-125-85-212.5T485-740h-22l52%2052q9%209%209%2021t-9%2021q-9%209-21%209t-21-9L368-751q-9-9-9-21t9-21l106-106q8-8%2020.5-8t20.5%208q8%208%208%2020.5t-8%2020.5l-58%2058h23q75%200%20140.5%2028T735-695q49%2049%2077%20114.5T840-440q0%2075-28%20140.5T735-185q-49%2049-114.5%2077T480-80q-75%200-140.5-28Z'/%3e%3c/svg%3e`,Ur=({expanded:e,expandedDisabled:t,onToggleExpanded:n,onRerunChecks:r,rerunDisabled:i})=>(0,Z.jsxs)(`div`,{className:`flex items-center justify-between`,children:[(0,Z.jsx)(V,{children:(0,Z.jsx)(`strong`,{children:`Pre-submission checks`})}),(0,Z.jsxs)(`div`,{className:`flex items-center gap-xs`,children:[(0,Z.jsx)(`button`,{className:`flex items-center text-neutral-400 dark:text-neutral-800 enabled:hover:text-neutral-200 enabled:dark:hover:text-neutral-600 cursor-pointer disabled:cursor-default disabled:text-neutral-700 dark:disabled:text-neutral-200`,"aria-label":`Rerun checks`,onClick:r,disabled:i,children:(0,Z.jsx)(R,{src:Hr,size:B.Small})}),(0,Z.jsx)(`button`,{disabled:t,className:`flex items-center text-neutral-400 dark:text-neutral-800 enabled:hover:text-neutral-200 enabled:dark:hover:text-neutral-600 cursor-pointer disabled:cursor-default disabled:text-neutral-700 dark:disabled:text-neutral-200`,onClick:n,"aria-label":e?`Collapse checks`:`Expand checks`,children:(0,Z.jsx)(R,{src:e?j:u,size:B.Small})})]})]}),Wr=[`Checking report quality`,`Checking the assigned severity`,`Checking the assigned weakness`,`Checking if the report falls under core ineligible findings`,`Checking if the report describes a vulnerability`,`Checking the required fields`,`Checking if the asset is correct`],Gr=({reviewStartedAt:e})=>{let[t,n]=(0,X.useState)(0),[,r]=(0,X.useState)(0),i=e?Date.now()-new Date(e).getTime():0,a=Math.min(i/68e3*100,99);return(0,X.useEffect)(()=>{let e=setInterval(()=>{n(e=>(e+1)%Wr.length)},3e3),t=setInterval(()=>{r(e=>e+1)},1e3);return()=>{clearInterval(e),clearInterval(t)}},[]),(0,Z.jsxs)(`div`,{className:`flex items-center gap-sm p-md`,children:[(0,Z.jsx)(et,{}),(0,Z.jsxs)(V,{variation:L.Subtle,children:[`[`,Math.round(a),`%]\xA0`,Wr[t]]})]})},Kr=(e,t,n)=>{if(e===K.FAILED||t>0){let r=t+n;return{color:x.Red,icon:fe,accessibilityLabel:`Failed`,label:e===K.FAILED?`Could not run checks. Try again.`:`${r} issue${r===1?``:`s`} found`}}return n>0?{color:x.Yellow,icon:_e,accessibilityLabel:`Warning`,label:`${n} issue${n===1?``:`s`} found`}:{color:x.Green,icon:c,accessibilityLabel:`Passed`,label:`No issues found`}},qr=({toolCallStatus:e,blockingFailureCount:t,nonBlockingFailureCount:n,stale:r})=>{let{color:i,icon:a,accessibilityLabel:o,label:s}=Kr(e,t,n);return(0,Z.jsxs)(`div`,{className:`flex flex-col gap-xs`,children:[(0,Z.jsx)(T,{color:r?x.Gray:i,id:r?void 0:`latest-status-tag`,size:C.Small,icons:{left:{src:a,accessibilityLabel:o}},rounded:!1,children:s}),r&&(0,Z.jsx)(V,{children:(0,Z.jsx)(`span`,{className:`text-neutral-400 dark:text-neutral-900`,children:`Newer results available`})})]})},Jr=({toolCallStatus:e,checks:t,stale:n,onRerunChecks:r,reviewStartedAt:i})=>{let{loading:a,isAgentBusy:o}=$(),s=t.filter(e=>e.status!==`passed`&&e.blocking).length,c=t.filter(e=>e.status!==`passed`&&!e.blocking).length,[l,u]=(0,X.useState)(s+c>=0&&!n);return(0,Z.jsx)(`div`,{className:`border rounded-md border-solid border-neutral-700 dark:border-neutral-200 dark:bg-black bg-white`,children:e===K.PROCESSING?(0,Z.jsx)(Gr,{reviewStartedAt:i??null}):(0,Z.jsxs)(Z.Fragment,{children:[(0,Z.jsxs)(`div`,{className:`flex flex-col gap-xs p-md ${l?`border-b border-solid border-neutral-700 dark:border-neutral-200`:``}`,children:[(0,Z.jsx)(Ur,{expandedDisabled:t.length===0,expanded:l,onToggleExpanded:()=>{u(!l)},rerunDisabled:a||o,onRerunChecks:r}),(0,Z.jsx)(qr,{toolCallStatus:e,blockingFailureCount:s,nonBlockingFailureCount:c,stale:n})]}),l&&(0,Z.jsx)(`div`,{className:`flex flex-col gap-md p-md`,children:t.map(e=>(0,Z.jsx)(Vr,{check:e},e.name))})]})})},Yr=e=>e.type!==`ConversationEntries::ToolCall`||typeof e.data!=`object`||e.data===null?!1:e.data.tool_name===`run_pre_submission_review`,Xr=e=>typeof e.data==`object`&&e.data!==null&&typeof e.data.status==`string`&&Object.values(K).includes(e.data.status)?e.data.status:K.PROCESSING,Zr=e=>typeof e.data==`object`&&e.data!==null&&typeof e.data.tool_output==`object`&&e.data.tool_output!==null&&Array.isArray(e.data.tool_output.checks)?e.data.tool_output.checks:[],Qr={predicate:Yr,Component:({entry:e})=>{let{register:t,isLatestEntry:n,updateLatestSummary:r}=Lr(),i=Br(),a=Xr(e),o=(0,X.useMemo)(()=>Zr(e),[JSON.stringify(e.data?.tool_output?.checks??[])]);(0,X.useEffect)(()=>{t(e.id)},[e.id,t]);let s=n(e.id),c=o.filter(e=>e.status!==`passed`&&e.blocking).length,l=o.filter(e=>e.status!==`passed`&&!e.blocking).length;return(0,X.useEffect)(()=>{s&&r({toolCallStatus:a,blockingFailureCount:c,nonBlockingFailureCount:l})},[s,a,c,l,r]),(0,Z.jsx)(`div`,{className:`mb-md`,children:(0,Z.jsx)(Jr,{toolCallStatus:a,checks:o,stale:!s,onRerunChecks:()=>{i(`Run checks`)},reviewStartedAt:e.created_at})})}},$r=()=>{let{reportIntent:e,loading:t,isAgentBusy:n,sendMessage:r,submitReport:i,isSubmitting:a,eligibility:o,conversationEntries:s}=$(),c=e?.conversation?.id??null,l=(0,X.useRef)(null),u=(0,X.useCallback)(e=>{l.current?.sendMessage(e)},[]),{latestSummary:d}=Lr(),[f,p]=(0,X.useState)(!0),{required:m}=Xe(e?.team?.handle);return(0,Z.jsxs)(`div`,{className:`grid grid-cols-12 grid-rows-[auto_1fr] p-lg pb-0 gap-md w-full h-[calc(100vh-var(--dynamic-topbar-height))] overflow-hidden relative`,children:[(0,Z.jsx)(`div`,{className:`col-span-4 flex items-center`,children:(0,Z.jsx)(J,{to:`/hai/report_assistant?v2=1`,className:`hover:no-underline`,"data-testid":`back-button`,children:(0,Z.jsxs)(`div`,{className:`flex text-neutral-400 dark:text-neutral-900 hover:no-underline flex-row gap-2xs items-center`,children:[(0,Z.jsx)(R,{src:dt,size:B.Medium}),`All reports`]})})}),(0,Z.jsxs)(`div`,{className:`col-span-8 flex justify-between items-center`,children:[(0,Z.jsxs)(`div`,{className:`flex items-center gap-xs`,children:[(0,Z.jsxs)(V,{variation:L.Subtle,children:[(0,Z.jsxs)(`span`,{className:`text-neutral-400 dark:text-neutral-900`,children:[`You are submitting a report to`,` `]}),(0,Z.jsx)(J,{to:`/${e?.team?.handle}?type=team`,newTab:!0,children:(0,Z.jsxs)(`div`,{className:`inline-flex items-center gap-2xs`,children:[e?.team?.name,` `,(0,Z.jsx)(R,{src:In})]})})]}),o?.underSignalMinimum&&(0,Z.jsx)(`span`,{title:`This program requires a Signal of ${e?.team?.signal_requirements_setting?.target_signal??`N/A`}. You have limited trial reports remaining.`,children:(0,Z.jsx)(T,{color:x.Yellow,size:C.ExtraSmall,rounded:!1,icons:{left:{src:`data:image/svg+xml,%3csvg%20xmlns='http://www.w3.org/2000/svg'%20width='48'%20height='48'%20viewBox='0%20-960%20960%20960'%3e%3cpath%20d='M92-120q-9%200-15.5-4T66-135q-4-7-4.5-14.5T66-165l388-670q5-8%2011.5-11.5T480-850q8%200%2014.5%203.5T506-835l388%20670q5%208%204.5%2015.5T894-135q-4%207-10.5%2011t-15.5%204H92Zm52-60h672L480-760%20144-180Zm361.5-65.5Q514-254%20514-267t-8.5-21.5Q497-297%20484-297t-21.5%208.5Q454-280%20454-267t8.5%2021.5Q471-237%20484-237t21.5-8.5Zm0-111Q514-365%20514-378v-164q0-13-8.5-21.5T484-572q-13%200-21.5%208.5T454-542v164q0%2013%208.5%2021.5T484-348q13%200%2021.5-8.5ZM480-470Z'/%3e%3c/svg%3e`,accessibilityLabel:`Warning`}},children:`Signal Requirement`})})]}),(0,Z.jsx)(Rn,{onRerunChecks:()=>{u(`Run checks`)},onSubmit:i,disabled:t||n||a||m,submitDisabled:e?.state!==`ready_to_submit`,latestChecksSummary:d})]}),(0,Z.jsxs)(`div`,{className:`col-span-4 min-h-0 flex flex-col gap-xs pb-lg`,children:[o&&!o.reachedTrialLimit&&o.underSignalMinimum&&(0,Z.jsxs)(`div`,{className:`shrink-0 rounded border`,children:[(0,Z.jsxs)(`button`,{type:`button`,className:`flex w-full items-center justify-between px-sm py-xs text-left`,onClick:()=>{p(!f)},children:[(0,Z.jsx)(`span`,{className:`font-semibold`,children:`Caution: Signal Requirement`}),(0,Z.jsx)(R,{src:f?`data:image/svg+xml,%3csvg%20xmlns='http://www.w3.org/2000/svg'%20width='48'%20height='48'%20viewBox='0%20-960%20960%20960'%3e%3cpath%20d='M480-554%20304-378q-9%209-21%208.5t-21-9.5q-9-9-9-21.5t9-21.5l197-197q9-9%2021-9t21%209l198%20198q9%209%209%2021t-9%2021q-9%209-21.5%209t-21.5-9L480-554Z'/%3e%3c/svg%3e`:`data:image/svg+xml,%3csvg%20xmlns='http://www.w3.org/2000/svg'%20width='48'%20height='48'%20viewBox='0%20-960%20960%20960'%3e%3cpath%20d='M469-358q-5-2-10-7L261-563q-9-9-8.5-21.5T262-606q9-9%2021.5-9t21.5%209l175%20176%20176-176q9-9%2021-8.5t21%209.5q9%209%209%2021.5t-9%2021.5L501-365q-5%205-10%207t-11%202q-6%200-11-2Z'/%3e%3c/svg%3e`,size:B.Medium})]}),f&&(0,Z.jsx)(`div`,{className:`px-sm pb-sm`,children:(0,Z.jsx)(lt,{me:o.me??{statistics_snapshot:null},team:e?.team})})]}),(0,Z.jsx)(zr,{sendMessage:u,children:(0,Z.jsx)(`div`,{className:`grow min-h-0`,children:(0,Z.jsx)(Ie,{ref:l,id:c,handleSubmitMessage:r,entryComponents:[Qr],disabled:t||n,entries:s})})}),(0,Z.jsxs)(`div`,{className:`flex flex-row justify-between items-center`,children:[(0,Z.jsx)(V,{variation:L.Subtle,children:(0,Z.jsx)(`p`,{className:`text-neutral-400 dark:text-neutral-900`,children:`Hai can make mistakes. Make sure to verify its outputs.`})}),(0,Z.jsx)(`button`,{className:`text-blue-400 dark:text-blue-600`,onClick:()=>{window?.Intercom?.(`startSurvey`,59894482)},children:`Give feedback`})]})]}),o&&(0,Z.jsx)(ct,{team:e?.team,teamHandle:e?.team?.handle??``,me:o.me,showModal:(o.reachedTrialLimit&&o.underSignalMinimum)??!1}),(0,Z.jsxs)(`div`,{className:`col-start-5 col-span-8 w-full h-full relative overflow-y-scroll`,children:[(0,Z.jsx)(Ee,{teamHandle:e?.team?.handle}),(0,Z.jsx)(Pr,{})]})]})},ei=()=>(0,Z.jsx)(Ir,{children:(0,Z.jsx)($r,{})}),ti=()=>{let{id:e}=S();return(0,Z.jsx)(ae,{children:(0,Z.jsx)(ar,{databaseId:e,children:(0,Z.jsx)(ei,{})})})},ni=()=>{let{id:e}=S(),{data:t,loading:n}=A(Fe,{variables:{id:parseInt(e||`0`,10)}});return n?null:(t?.report_intent?.agent_version??1)===2?(0,Z.jsx)(ti,{}):(0,Z.jsx)(vn,{})},ri=()=>{let{enabled:e}=$e(window.constants.featureToggles.REPORT_ASSISTANT_V2);return(0,Z.jsx)(Z.Fragment,{children:(0,Z.jsx)(Ke,{children:(0,Z.jsx)(Vt,{children:(0,Z.jsxs)(o,{children:[(0,Z.jsx)(nt,{exact:!0,path:`/hai/report_assistant`,component:e?Fn:Nt}),(0,Z.jsx)(nt,{exact:!0,path:`/hai/report_assistant/:id`,component:e?ni:vn})]})})})})};export{ri as ReportAssistantAgentRouter,ri as default};
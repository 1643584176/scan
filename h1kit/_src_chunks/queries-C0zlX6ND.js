import{o as e}from"./rolldown-runtime-DAXXjFlN.js";import{Fw as t,Ln as n,Rn as r,Rw as i,Vx as a,db as o}from"./vendor-_WdvpBLr.js";import{Cp as s,Sh as c,Sm as l,cm as u}from"./app-5pKgUmmm.js";import{v as d}from"./constants-KKBS4o7v.js";var f=e(i()),p=`bounty insights interest selected`,m=e=>{let[t,n]=(0,f.useState)(e.bounty_insights_requested),r=(0,f.useMemo)(()=>({...e,bounty_insights_requested:t}),[e,t]),[i]=a(d,{variables:{organization_id:e._id},awaitRefetchQueries:!0,onCompleted:e=>{e.requestBountyInsights.was_successful?(l(`notice`,`Your customer success manager will be in touch soon.`),n(!0)):l(`error`,`Something went wrong. Please try again.`)}});return{children:r.bounty_insights_requested?`Request received`:`I'm interested`,onClick:()=>{c.track(p,{organization_id:r._id,hai_enabled:r.hai_enabled}),i().then(()=>{}).catch(()=>{})},disabled:r.bounty_insights_requested??!1}},h=t(),g=(e,t)=>e/t*100||0,_=(e,t)=>Math.round(e*100/t)||0,v=({totalSpent:e,totalPurchased:t,maxDaysRemaining:i,daysPassedPercentage:a,progressBarTitle:o,hideDescriptiveText:s})=>(0,h.jsxs)(`div`,{"data-testid":`spec-bounty-spending-progress`,className:`flex flex-col gap-xs`,children:[(0,h.jsxs)(`div`,{className:`flex justify-between items-center`,children:[(0,h.jsx)(`h2`,{className:`mb-0 font-bold`,children:o}),(0,h.jsxs)(`div`,{className:`flex flex-row items-center gap-2xs`,children:[(0,h.jsx)(`span`,{className:`text-lg font-bold`,children:(0,h.jsx)(u,{amount:e})}),(0,h.jsxs)(`span`,{className:`text-neutral-200 dark:text-neutral-950`,children:[!s&&`spent`,` of`]}),(0,h.jsx)(`span`,{className:`text-neutral-200 text-lg font-bold dark:text-neutral-950`,children:(0,h.jsx)(u,{amount:t})}),!s&&(0,h.jsxs)(h.Fragment,{children:[(0,h.jsx)(`span`,{className:`text-neutral-200 dark:text-neutral-950`,children:`purchased \xA0`}),(0,h.jsxs)(`span`,{className:`text-neutral-200 text-sm dark:text-neutral-950`,children:[`(`,_(e,t),`% of total purchased)`]})]})]})]}),(0,h.jsxs)(`div`,{className:`flex flex-col gap-2xs`,children:[(0,h.jsx)(r,{color:n.Blue,progress:g(e,t)}),(0,h.jsxs)(`span`,{className:`text-neutral-200 text-sm dark:text-neutral-950`,children:[`Active contract expires in `,i,` days (`,a,`% elapsed)`]})]})]}),y=(e,t,n=!1)=>e.map(e=>e?.entitlement_consumption_overview).filter(e=>n?e?.object_type===t&&e?.challenge:e?.object_type===t&&!e?.challenge),b={BOUNTY:`bug_bounty`,PENTEST:`pentest`,CHALLENGE:`challenge`},x=e=>({totalEntitlementSpent:e.reduce((e,t)=>e+(t.max_object_consumption_amount_acc??0),0),totalEntitlementPurchased:Array.from(new Set(e.map(e=>e.entitlement_number))).map(t=>e.find(e=>e.entitlement_number===t)).reduce((e,t)=>e+(t?.entitlement_total_purchased??0),0),activeEntitlementWithMaxDaysRemaining:e.reduce((e,t)=>(e?.days_remaining??0)>(t?.days_remaining??0)?e:t,null)}),S=({segmentList:e})=>{let t=(0,f.useRef)(null);return(0,h.jsx)(`div`,{className:`flex h-xs w-full rounded-full bg-neutral-700 dark:bg-neutral-200`,children:e.filter(e=>e.width!==void 0&&e.width>0).map(e=>(0,h.jsxs)(f.Fragment,{children:[(0,h.jsx)(`div`,{className:`h-xs rounded-full ${e.color}`,ref:t,style:{width:`${e.width}%`}}),(0,h.jsx)(o,{text:e.tooltipMessage,attachToRef:t})]},e.id_key))})},C=(e,t)=>e/t*100||0,w=e=>{let t=[`Jan`,`Feb`,`Mar`,`Apr`,`May`,`Jun`,`Jul`,`Aug`,`Sep`,`Oct`,`Nov`,`Dec`],[n,r,i]=e.split(`-`);return`${i} ${t[Number(r)-1]} ${n}`},T=(e,t)=>e===`Essential`?t<=0?`bg-orange-300`:`bg-orange-800`:e===`Premium`?t<=0?`bg-blue-300`:`bg-blue-800`:null,E=({hoursSpent:e,hoursPurchased:t,hoursInScoping:n,subscriptionName:r,subscriptionExpiresAt:i,subscriptionType:a,progressBarTitle:o,hideDescriptiveText:s})=>{let c=e+n,l=`${e} hours spent · ${Math.max(0,t-e)} hours remaining · ${n} hours in scoping phase`;return(0,h.jsx)(h.Fragment,{children:(0,h.jsxs)(`div`,{className:`flex flex-col gap-xs`,"data-testid":`spec-pentest-progress-bar-${r.toLowerCase()}`,children:[(0,h.jsxs)(`div`,{className:`flex flex-row justify-between items-center gap-2xs`,children:[(0,h.jsx)(`h2`,{className:`mb-0 font-bold`,children:o}),(0,h.jsxs)(`div`,{className:`flex justify-between items-center`,children:[(0,h.jsxs)(`span`,{className:`text-lg font-bold`,children:[e,`\xA0`]}),(0,h.jsxs)(`span`,{className:`text-neutral-200 dark:text-neutral-950`,children:[`hrs `,!s&&`spent `,`of \xA0`]}),(0,h.jsxs)(`span`,{className:`text-neutral-200 text-lg font-bold dark:text-neutral-950`,children:[t,`\xA0`]}),(0,h.jsxs)(`span`,{className:`text-neutral-200 dark:text-neutral-950`,children:[`hrs `,!s&&`purchased`,` \xA0`]})]})]}),(0,h.jsx)(S,{segmentList:[{color:T(a,0),width:C(e,t),tooltipMessage:l,id_key:`${a}_spent`},{width:C(n,t),color:T(a,n),tooltipMessage:l,id_key:`${a}_not_spent`}],totalProgress:C(c,t)}),i&&(0,h.jsxs)(`span`,{className:`text-neutral-200 text-sm dark:text-neutral-950`,children:[`Expires on `,w(i)]})]})})},D=s(`
  query OrganizationSpendTrackerSettings($handle: String!) {
    organizations(where: { handle: { _eq: $handle } }) {
      nodes {
        id
        pentest_sales_entitlements_data
        skus_alert_banner
        derived_pentest_opportunities_hours
        teams {
          nodes {
            id
            handle
            name
            submission_state
            entitlement_consumption_overview {
              id
              entitlement_name
              entitlement_number
              last_pentest_status
              programs_handle
              programs_name
              programs_status
              entitlement_tier
              entitlement_total_purchased
              max_object_consumption_amount_acc
              consumption_start_date
              consumption_end_date
              entitlement_remaining
              days_remaining
              days_remaining_percentage
              entitlement_total_spent_in_percentage
              object_type
              product_code
              pentest_type
              challenge
              challenge_tier
              challenge_starts_at
              challenge_stops_at
            }
          }
        }
      }
    }
  }
`),O=s(`
  query AssetTagCategoriesForSpendTracker($handle: String!) {
    organizations(where: { handle: { _eq: $handle } }) {
      nodes {
        id
        asm_tag_categories {
          nodes {
            id
            _id
            name
            unique_tag_per_asset
            asm_tags_count
          }
        }
      }
    }
  }
`),k=s(`
  query SpendTrackerByCategory(
    $organizationId: ID!
    $categoryId: ID!
    $startDate: ISO8601DateTime
    $endDate: ISO8601DateTime
  ) {
    spend_tracker_by_category(
      organization_id: $organizationId
      category_id: $categoryId
      start_date: $startDate
      end_date: $endDate
    ) {
      category_id
      category_name
      is_unique
      total_spend
      spend_by_tag {
        tag_id
        tag_name
        bounty_spend
        challenge_spend
        total_spend
        asset_count
      }
    }
  }
`),A=s(`
  query AgenticCreditUsageQuery($organizationHandle: String!) {
    me {
      id
      organizations(first: 1, where: { handle: { _eq: $organizationHandle } }) {
        nodes {
          id
          handle
          name
          i_can_view_agentic_credit_usage
          remediation_enabled
          continuous_testing_enabled
          asset_intelligence_enabled
          features {
            key
          }
          ces_organization {
            id
            ces_customer_id
            stigg_widget_config {
              client_api_key
              customer_id
              customer_token
              resource_id
            }
          }
          credit_balances_and_rates {
            credit_balances {
              currency_id
              current_usage
              remaining_balance
              usage_period_end
              resource_id
            }
            feature_credit_rates {
              feature_ref_id
              display_name
              credit_rate
              credit_formula
            }
          }
        }
      }
    }
  }
`);export{E as a,y as c,D as i,v as l,O as n,b as o,k as r,x as s,A as t,m as u};
import{Kx as e,qx as t}from"./vendor-_WdvpBLr.js";import{ui as n}from"./app-5pKgUmmm.js";t();var r=e`
  fragment HackerReportTemplateFragment on HackerReportTemplate {
    id
    _id
    title
    report_title
    body
    impact
    cwe
    attack_vector
    attack_complexity
    privileges_required
    user_interaction
    scope
    confidentiality
    integrity
    availability
    rating
    score
    severity
  }
`,i=e`
  query HackerTemplates {
    me {
      id
      hacker_report_templates {
        ...HackerReportTemplateFragment
      }
    }
  }
  ${r}
`,a=e`
  query HackerAndVulnerabilityTemplates {
    me {
      id
      hacker_report_templates {
        ...HackerReportTemplateFragment
      }
    }
    vulnerability_templates {
      ...HackerReportTemplateFragment
      weaknesses {
        id
        _id
        external_id
      }
    }
  }
  ${r}
`,o=`add hacker report template clicked`,s=`save hacker report template clicked`,c=`edit hacker report template clicked`,l=`delete hacker report template clicked`,u=`cancel delete hacker report template clicked`,d=`confirm delete hacker report template clicked`,f=`hacker report template form closed`,p=`hacker report template selected`,m=`apply hacker report template clicked`,h=`cancel hacker report template clicked`,g=async()=>{await n(o,{})},_=async(e,t=null)=>{await n(s,{template_id:t,form_contains_errors:e})},v=async e=>{await n(c,{template_id:e})},y=async e=>{await n(l,{template_id:e})},b=async e=>{await n(u,{template_id:e})},x=async e=>{await n(d,{template_id:e})},S=async(e=null)=>{await n(f,{template_id:e})},C=async(e,t,r,i)=>{await n(p,{template_id:e,confirmation_prompt_displayed:t,is_vulnerability_template:r,vulnerability_templates_enabled:i})},w=async(e,t,r)=>{await n(m,{template_id:e,is_vulnerability_template:t,vulnerability_templates_enabled:r})},T=async(e,t,r)=>{await n(h,{template_id:e,is_vulnerability_template:t,vulnerability_templates_enabled:r})};export{v as a,T as c,a as d,r as f,y as i,S as l,b as n,_ as o,i as p,x as r,w as s,g as t,C as u};
import{o as e}from"./rolldown-runtime-DAXXjFlN.js";import{$d as t,$y as n,Fw as r,Iw as i,Qy as a,Rw as o,Ux as s,Vx as c,av as l,df as u,ff as d,ov as f,rv as p,sv as m,tb as h,tv as g}from"./vendor-_WdvpBLr.js";import{Cp as _,Th as v,ap as y,vm as b,ym as x}from"./app-5pKgUmmm.js";import{a as S}from"./step_options_mutations-3QVc-MLh.js";var C=e(i()),w=e(o()),T=r(),E=({hackerSkillsByName:e,setHackerSkillsByName:n})=>(0,T.jsxs)(`div`,{className:`mb-[56px]`,children:[(0,T.jsx)(u,{variation:d.Light}),Object.keys(e).map((r,i)=>{let{proficiency:a,skill_id:o}=e[r];return(0,T.jsxs)(`div`,{"data-testid":`spec-skill-recommendation-${r}`,children:[(0,T.jsx)(`div`,{className:`flex p-md`,children:(0,T.jsxs)(`div`,{className:(0,C.default)(`md:w-full`,`flex flex-col md:flex-row gap-y-xs`,`items-start md:items-center justify-center md:justify-between`),children:[(0,T.jsx)(p,{children:r}),(0,T.jsx)(t,{items:[{id:`NONE`,label:`None`},{id:`BEGINNER`,label:`Beginner`},{id:`NOVICE`,label:`Novice`},{id:`INTERMEDIATE`,label:`Intermediate`},{id:`EXPERT`,label:`Expert`}],onClick:t=>{let i=structuredClone(e);i[r]={skill_id:o,proficiency:t},n(i)},selectedId:String(a),testId:`spec-proficiencies`})]})}),(0,T.jsx)(u,{variation:d.Light})]},i)})]}),D=_(`
  query RecommendedSkillsFromPentests {
    recommended_skills: skills(
      exclude_my_skills: true
      where: { recommended_skills_for_user: true }
    ) {
      total_count
      nodes {
        id
        __typename
        name
      }
    }
    me {
      id
      __typename
      hacker_skills(where: { skill: { database_id: { _in: [] } } }) {
        nodes {
          id
          __typename
          skill {
            id
            __typename
            name
          }
          proficiency
        }
      }
    }
  }
`),O=_(`
  query SpecificRecommendedSkills($skill_ids: [Int]) {
    recommended_skills: skills(where: { database_id: { _in: $skill_ids } }) {
      nodes {
        id
        __typename
        name
      }
    }
    me {
      id
      __typename
      hacker_skills(where: { skill: { database_id: { _in: $skill_ids } } }) {
        nodes {
          id
          __typename
          skill {
            id
            __typename
            name
          }
          proficiency
        }
      }
    }
  }
`),k={skills_and_interests:`Tell us more about you`,application:`Application submitted!`,skills_request:`Tell us more about you`},A={skills_and_interests:`Recommended skills`,application:`These are the preferred skills for this pentest.`,skills_request:`These are the skills needed for upcoming pentests.`},j={skills_and_interests:`These are the skills we recommend based on pentests you have previously completed and applied to. Please choose your level of skill in the following technologies below.`,application:`Please choose your level of skill in the following technologies below. You will not be automatically disqualified for missing some.`,skills_request:`Please choose your level of skill in the following technologies below. You will not be automatically disqualified for missing some.`},M={skills_and_interests:`/settings/skills_and_interests/skills`,application:`/opportunities/pentests`,skills_request:`/settings/skills_and_interests/skills`},N=()=>{let e=new URLSearchParams(window.location.search),t=(e.get(`skill-ids`)??``).split(`,`).filter(e=>e).map(e=>parseInt(e)),r=e.get(`from`)??`skills_and_interests`,{data:i,loading:o}=s(t.length>0?O:D,{variables:t.length>0?{skill_ids:t}:{}}),[u,d]=(0,w.useState)(),[_]=c(S,{onCompleted:({updateHackerSkills:e})=>{e.was_successful?(x(),P()):b()},onError:()=>{b()}}),N=()=>{if(u){let e=Object.keys(u);if(e){let t=e.map(e=>u[e]).filter(e=>e.proficiency!==`NONE`);_({variables:{skills:t}})}}};(0,w.useEffect)(()=>{if(i&&!o){let e={};i.recommended_skills.nodes.forEach(t=>{let n={skill_id:t.id,proficiency:`NONE`};if(i.me?.hacker_skills){let e=i.me.hacker_skills?.nodes?.find(e=>e.skill.name===t.name);e&&(n.proficiency=e.proficiency)}e[t.name]=n}),d(e)}},[o,i]);let P=()=>{y(M[r])};return o||!u?(0,T.jsx)(v,{}):(0,T.jsx)(`div`,{className:`flex justify-center p-md`,children:(0,T.jsxs)(`div`,{className:`flex flex-col gap-y-lg`,children:[(0,T.jsxs)(`div`,{children:[(0,T.jsx)(f,{renderAs:l.H1,size:m.Scale600,children:k[r]}),(0,T.jsx)(p,{renderAs:g.Paragraph,children:`Help us ensure you are matched to the pentest programs that align with your goals and preferences.`})]}),(0,T.jsxs)(`div`,{children:[(0,T.jsx)(f,{renderAs:l.H2,size:m.Scale400,children:A[r]}),(0,T.jsx)(p,{renderAs:g.Paragraph,children:j[r]})]}),(0,T.jsx)(`div`,{"data-testid":`recommended-skills`,children:(0,T.jsx)(E,{hackerSkillsByName:u,setHackerSkillsByName:d})}),(0,T.jsx)(`div`,{className:`fixed bottom-0 left-0 right-0 z-10`,children:(0,T.jsxs)(`div`,{className:(0,C.default)(`bg-white dark:bg-black`,`border-solid border-t border-neutral-700 dark:border-neutral-300`,`w-full flex justify-end px-md py-[16px]`),children:[(0,T.jsx)(`div`,{className:`mr-[16px]`,children:(0,T.jsx)(a,{variation:h.Secondary,onClick:P,testId:`submit-skill-wizard-skills`,children:`Skip`})}),(0,T.jsx)(a,{variation:h.Primary,onClick:N,type:n.Submit,testId:`submit-skill-wizard-skills`,children:`Update`})]})})]})})};export{D as RECOMMENDED_SKILLS_FROM_PENTESTS_QUERY,E as RecommendedSkills,O as SPECIFIC_SKILLS_TO_ADD_QUERY,N as default};
import{o as e}from"./rolldown-runtime-DAXXjFlN.js";import{Fw as t,Kx as n,Nb as r,Qy as i,Rw as a,Vx as o,Y_ as s,df as c,ff as l,nb as u,qx as d,rb as f,rv as p,tb as m}from"./vendor-_WdvpBLr.js";import{Cp as h,If as g,Ju as _,Sm as v,ep as y,vm as b}from"./app-5pKgUmmm.js";import{n as x}from"./mutations-Bb25djee.js";d();var S=n`
  mutation StartIdVerification {
    startIdVerification(input: {}) {
      url
      was_successful
      errors {
        edges {
          node {
            type
          }
        }
      }
    }
  }
`,C=async()=>{try{return(await x(`id_verification`,`start_application`,S,`startIdVerification`)).url}catch(e){throw console.error(e),e}},w=`/assets/static/example-identity-card-D46u_bYb.svg`,T=t(),E=({terms:e,signed:t,sign:n})=>e?(0,T.jsxs)(T.Fragment,{children:[(0,T.jsx)(r,{vertical:`16`}),(0,T.jsxs)(`div`,{className:`flex`,children:[(0,T.jsx)(s,{testId:`spec-consent-checkbox`,checked:t,accessibilityLabel:`sign`,onChange:n}),(0,T.jsx)(_,{markdown:e,disableContextMenu:!0})]})]}):(0,T.jsx)(`p`,{className:`text-red-400 text-sm`,children:`Failed to retrieve terms and conditions, please try again later.`}),D=e(a()),O=({handleButtonClick:e,isStartingIdVerification:t,showModal:n,handleCloseModal:i,terms:a})=>{let[o,s]=(0,D.useState)(!1);return(0,T.jsx)(y,{title:`Welcome to ID verification`,buttonText:t?`Starting...`:`Start the process`,cancelLinkText:`Cancel`,size:`large`,buttonDisabled:t||!o,showModal:n,handleButtonClick:e,handleCloseModal:i,children:(0,T.jsxs)(`div`,{className:`py-md`,children:[(0,T.jsx)(`div`,{className:`flex my-xl justify-center`,children:(0,T.jsx)(`img`,{className:`w-3/5`,src:w})}),(0,T.jsxs)(`div`,{className:`flex mb-xs`,children:[(0,T.jsx)(`span`,{className:`mr-sm align-text-top`,children:(0,T.jsx)(u,{src:g,size:f.ExtraLarge})}),(0,T.jsx)(`h2`,{className:`m-0 text-2xl sm:text-3xl`,children:`ID verification - General Information`})]}),(0,T.jsx)(r,{vertical:`12`}),(0,T.jsxs)(`div`,{children:[(0,T.jsx)(p,{children:`Let's start the ID verification process.`}),(0,T.jsx)(`br`,{}),(0,T.jsx)(`br`,{}),(0,T.jsx)(`h2`,{className:`text-md m-0`,children:(0,T.jsx)(`b`,{children:`How does it work?`})}),(0,T.jsx)(p,{children:`Some private programs require identity verification. Veriff, our trusted third party, takes care of the checks. Upload an approved ID and a clear photo of your face in their portal. For the best experience, check out the tips before you begin.`}),(0,T.jsx)(`br`,{}),(0,T.jsx)(`br`,{}),(0,T.jsx)(`h2`,{className:`text-md m-0`,children:(0,T.jsx)(`b`,{children:`What do you need to get it done?`})}),(0,T.jsx)(p,{children:(0,T.jsxs)(`ul`,{className:`list-disc list-inside`,children:[(0,T.jsx)(`li`,{children:`Have your ID ready (Passport, Identity Card, Residence Permit, or Driver's License)`}),(0,T.jsx)(`li`,{children:`Capture the ID image`}),(0,T.jsx)(`li`,{children:`Take a selfie (use a good quality image)`})]})}),(0,T.jsx)(`br`,{}),(0,T.jsx)(`h2`,{className:`text-md m-0`,children:(0,T.jsx)(`b`,{children:`What not to do?`})}),(0,T.jsx)(p,{children:(0,T.jsxs)(`ul`,{className:`list-disc list-inside`,children:[(0,T.jsx)(`li`,{children:`Do not use a VPN`}),(0,T.jsx)(`li`,{children:`Do not use the private reply function if using an iOS device`}),(0,T.jsx)(`li`,{children:`Do not use an SDK emulator`}),(0,T.jsx)(`li`,{children:`Do not use a Jailbroken device`}),(0,T.jsx)(`li`,{children:`Do not use a traffic anonymizer`})]})}),(0,T.jsx)(`br`,{}),(0,T.jsx)(`h2`,{className:`text-md m-0`,children:(0,T.jsx)(`b`,{children:`How long does it take?`})}),(0,T.jsx)(p,{children:`The process typically takes 2–5 minutes. You can track your data collection status directly on the platform. HackerOne will email you within 3 business days to confirm your ID verification status. If your application is unsuccessful, the email will explain the issues and provide guidance on how to reapply.`})]}),(0,T.jsx)(E,{terms:a,signed:o,sign:()=>{s(!o)}})]})})},k=h(`
  mutation SignRulesOfEngagement($input: SignRulesOfEngagementInput!) {
    signRulesOfEngagement(input: $input) {
      was_successful
      user_identity {
        id
        rules_of_engagement_status
        __typename
      }
      errors {
        edges {
          node {
            type
          }
        }
      }
    }
  }
`),A=h(`
  mutation StartBackgroundCheck($input: StartBackgroundCheckInput!) {
    startBackgroundCheck(input: $input) {
      was_successful
      url
      errors {
        edges {
          node {
            type
            message
          }
        }
      }
    }
  }
`),j=({disabled:e,completed:t})=>{let[n,r]=(0,D.useState)(!1),[a,u]=(0,D.useState)(!1),[d]=o(k,{onCompleted:({signRulesOfEngagement:{was_successful:e}})=>{e?v(`notice`,`The rules of engagement were signed successfully`):b()},onError:()=>{b()}}),f=()=>{r(!1)},h=async()=>{await d({variables:{input:{}}})};return(0,T.jsxs)(p,{children:[t?(0,T.jsxs)(`div`,{className:`flex flex-col gap-xs`,children:[(0,T.jsx)(i,{disabled:!0,children:`Sign the Rules of Engagement`}),(0,T.jsx)(`div`,{className:`text-green-300`,children:`Rules of Engagement signed`})]}):(0,T.jsx)(i,{disabled:e,onClick:()=>{r(!0)},children:`Sign the Rules of Engagement`}),(0,T.jsx)(y,{title:`Rules of Engagement`,shouldCloseOnEsc:!0,showModal:n,size:`large`,handleCloseModal:f,children:(0,T.jsxs)(`div`,{className:`flex flex-col gap-lg`,children:[(0,T.jsx)(c,{variation:l.Light}),(0,T.jsxs)(p,{children:[`Hackers participating in Clear Programs often have increased levels of internal access, credentials, or additional parameters. This document describes the`,` `,(0,T.jsx)(`a`,{href:`https://www.hackerone.com/policies/clear-rules-of-engagement`,rel:`noreferrer noopener`,target:`_blank`,children:`Rules of Engagement and Additional Terms`}),` `,`(“RoEs”) for being part of HackerOne Clear and participating in HackerOne Clear Programs. The same rules apply for ID Verification and ID Verified Programs.`]}),(0,T.jsxs)(p,{children:[`By being a part of HackerOne Clear or ID Verified, you must accept and abide by these Rules of Engagement. Additionally, by participating in any programs on HackerOne, all hackers agree to help empower our community by following the`,` `,(0,T.jsx)(`a`,{href:`https://www.hackerone.com/policies/code-of-conduct`,rel:`noreferrer noopener`,target:`_blank`,children:`HackerOne Code of Conduct (CoC).`}),` `,`The CoC is in addition to the`,` `,(0,T.jsx)(`a`,{href:`https://www.hackerone.com/terms/general`,rel:`noreferrer noopener`,target:`_blank`,children:`General Terms and Conditions`}),` `,`and`,` `,(0,T.jsx)(`a`,{href:`https://www.hackerone.com/terms/community`,rel:`noreferrer noopener`,target:`_blank`,children:`Hacker Terms and Conditions`}),` `,`all Clear and ID Verified hackers agree to when creating an account.`]}),(0,T.jsx)(`div`,{className:`flex flex-col gap-lg md:gap-sm grow`,children:(0,T.jsx)(s,{label:`I agree with the Rules of Engagement`,accessibilityLabel:`Agree with terms and conditions of the Rules of Engagement checkbox`,checked:a,onChange:()=>{u(e=>!e)}})}),(0,T.jsx)(c,{variation:l.Light}),(0,T.jsxs)(`div`,{className:`flex gap-xs justify-end`,children:[(0,T.jsx)(i,{small:!0,variation:m.Secondary,onClick:f,children:`Cancel`}),(0,T.jsx)(i,{small:!0,disabled:!a,onClick:()=>{h(),f()},testId:`spec-roe-save-button`,children:`Save`})]})]})})]})},M=[{code:`AL`,name:`Alabama`},{code:`AK`,name:`Alaska`},{code:`AZ`,name:`Arizona`},{code:`AR`,name:`Arkansas`},{code:`CA`,name:`California`},{code:`CO`,name:`Colorado`},{code:`CT`,name:`Connecticut`},{code:`DE`,name:`Delaware`},{code:`FL`,name:`Florida`},{code:`GA`,name:`Georgia`},{code:`HI`,name:`Hawaii`},{code:`ID`,name:`Idaho`},{code:`IL`,name:`Illinois`},{code:`IN`,name:`Indiana`},{code:`IA`,name:`Iowa`},{code:`KS`,name:`Kansas`},{code:`KY`,name:`Kentucky`},{code:`LA`,name:`Louisiana`},{code:`ME`,name:`Maine`},{code:`MD`,name:`Maryland`},{code:`MA`,name:`Massachusetts`},{code:`MI`,name:`Michigan`},{code:`MN`,name:`Minnesota`},{code:`MS`,name:`Mississippi`},{code:`MO`,name:`Missouri`},{code:`MT`,name:`Montana`},{code:`NE`,name:`Nebraska`},{code:`NV`,name:`Nevada`},{code:`NH`,name:`New Hampshire`},{code:`NJ`,name:`New Jersey`},{code:`NM`,name:`New Mexico`},{code:`NY`,name:`New York`},{code:`NC`,name:`North Carolina`},{code:`ND`,name:`North Dakota`},{code:`OH`,name:`Ohio`},{code:`OK`,name:`Oklahoma`},{code:`OR`,name:`Oregon`},{code:`PA`,name:`Pennsylvania`},{code:`RI`,name:`Rhode Island`},{code:`SC`,name:`South Carolina`},{code:`SD`,name:`South Dakota`},{code:`TN`,name:`Tennessee`},{code:`TX`,name:`Texas`},{code:`UT`,name:`Utah`},{code:`VT`,name:`Vermont`},{code:`VA`,name:`Virginia`},{code:`WA`,name:`Washington`},{code:`WV`,name:`West Virginia`},{code:`WI`,name:`Wisconsin`},{code:`WY`,name:`Wyoming`}];export{E as a,O as i,j as n,C as o,A as r,M as t};
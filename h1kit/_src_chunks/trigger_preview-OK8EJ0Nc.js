import{o as e}from"./rolldown-runtime-DAXXjFlN.js";import{Fw as t,Kx as n,qx as r,zx as i}from"./vendor-_WdvpBLr.js";import{Ju as a,wm as o}from"./app-5pKgUmmm.js";var s=e(i());r();var c=t(),l=({actionType:e})=>{switch(e){case`request_more_information`:return(0,c.jsxs)(`span`,{children:[`change state to `,(0,c.jsx)(`strong`,{children:`needs more info`})]});case`post_public_comment`:return(0,c.jsx)(`span`,{children:`add a public comment`});case`show_message`:return(0,c.jsx)(`span`,{children:`ask for submission confirmation`});default:return``}};l.propTypes={actionType:s.default.string};var u=({expressions:e,operator:t,actionType:n,actionMessage:r,percolated_query_string:i})=>i?(0,c.jsxs)(c.Fragment,{children:[(0,c.jsx)(a,{markdown:`\`\`\`json\n${i}\n\`\`\``,enableCodeWorkbench:!0,enableMediaWorkbench:!0}),(0,c.jsxs)(`span`,{className:`text-neutral-200 dark:text-neutral-950`,children:[`Action: `,(0,c.jsx)(l,{actionType:n})]}),(0,c.jsx)(`br`,{}),(0,c.jsx)(`br`,{}),(0,c.jsxs)(`span`,{className:`text-neutral-200 dark:text-neutral-950`,children:[`Message: `,r]})]}):(0,c.jsxs)(`span`,{className:`spec-preview-trigger`,children:[(0,c.jsx)(o,{className:`margin-4--right`,children:`IF`}),e.map((e,t)=>(0,c.jsxs)(`span`,{children:[(0,c.jsx)(`span`,{className:`spec-trigger-field`,children:e.left_value.replace(/_/g,` `).toLowerCase()}),` `,(0,c.jsx)(`span`,{className:`spec-trigger-rule`,children:e.operand.replace(/_/g,` `).toLowerCase()}),` `,(0,c.jsxs)(`span`,{className:`markdownable`,children:[`"`,(0,c.jsx)(`strong`,{children:e.right_value}),`"`]})]},t)).reduce((e,n,r)=>[e,(0,c.jsxs)(`span`,{children:[`\xA0`,(0,c.jsx)(o,{className:`margin-4--right`,children:t.toUpperCase()})]},`operator--${r}`),n],[]),`\xA0`,(0,c.jsx)(o,{className:`margin-4--right`,children:`THEN`}),(0,c.jsx)(`span`,{children:(0,c.jsx)(l,{actionType:n})})]});u.propTypes={percolated_query_string:s.default.string,expressions:s.default.array.isRequired,operator:s.default.string,actionType:s.default.string.isRequired,actionMessage:s.default.string.isRequired},u.fragments={trigger:n`
    fragment TriggerPreviewTrigger on Trigger {
      id
      team {
        id
        handle
      }
      action_message
      action_type
      expression_operator
      expressions(first: 100) {
        edges {
          node {
            id
            left_value
            operand
            right_value
          }
        }
      }
    }
  `};export{u as t};
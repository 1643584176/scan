import{Cp as e}from"./app-5pKgUmmm.js";var t=`data:image/svg+xml,%3c?xml%20version='1.0'?%3e%3csvg%20xmlns='http://www.w3.org/2000/svg'%20viewBox='0%200%2016%2016'%3e%3cpath%20fill-rule='evenodd'%20clip-rule='evenodd'%20d='M2%203.33332L8%200.666656L14%203.33332V7.33332C14%2011.0333%2011.44%2014.4933%208%2015.3333C4.56%2014.4933%202%2011.0333%202%207.33332V3.33332ZM12.6667%207.99335H8.00004V2.12668L3.33337%204.20001V8.00001H8.00004V13.9533C10.48%2013.1867%2012.3134%2010.74%2012.6667%207.99335Z'/%3e%3c/svg%3e`,n=e(`
  mutation CreatePentestStructuredScopeOverview(
    $pentest_id: ID!
    $structured_scope_id: ID!
  ) {
    createPentestStructuredScope(
      input: {
        pentest_id: $pentest_id
        structured_scope_id: $structured_scope_id
      }
    ) {
      was_successful
      pentest_structured_scope {
        ...MutatePentestStructuredScopeItem
      }
      errors {
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
`),r=e(`
  mutation DestroyPentestStructuredScope($pentest_structured_scope_id: ID!) {
    destroyPentestStructuredScope(
      input: { pentest_structured_scope_id: $pentest_structured_scope_id }
    ) {
      was_successful
      errors {
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
`),i=e(`
  mutation UpdatePentestScope(
    $structured_scope_id: ID!
    $eligible_for_submission: Boolean
  ) {
    updateStructuredScope(
      input: {
        structured_scope_id: $structured_scope_id
        eligible_for_submission: $eligible_for_submission
      }
    ) {
      errors {
        edges {
          node {
            id
            field
            message
          }
        }
      }
      was_successful
    }
  }
`),a=e(`
  mutation ModalUpdatePentestStructuredScope(
    $pentest_structured_scope_id: ID!
    $asset_identifier: String
    $credential_instruction: String
    $instruction: String
  ) {
    updatePentestStructuredScope(
      input: {
        pentest_structured_scope_id: $pentest_structured_scope_id
        asset_identifier: $asset_identifier
        credential_instruction: $credential_instruction
        instruction: $instruction
      }
    ) {
      was_successful
      pentest_structured_scope {
        ...MutatePentestStructuredScopeItem
      }
      errors {
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
`),o=e(`
  mutation UpdatePentestStructuredScopeWithMethodologies(
    $pentest_structured_scope_id: ID!
    $asset_identifier: String
    $credential_instruction: String
    $instruction: String
    $methodologies: [String!]!
    $pentest_checklist_template_ids: [String!]!
  ) {
    updatePentestStructuredScopeWithMethodologies(
      input: {
        pentest_structured_scope_id: $pentest_structured_scope_id
        asset_identifier: $asset_identifier
        credential_instruction: $credential_instruction
        instruction: $instruction
        methodologies: $methodologies
        pentest_checklist_template_ids: $pentest_checklist_template_ids
      }
    ) {
      was_successful
      pentest_structured_scope {
        ...MutatePentestStructuredScopeItem
      }
      errors {
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
`),s=e(`
  mutation reviewBitRecommendations(
    $bounty_informed_generator_run_id: ID!
    $engagement_interests: [String!]!
    $pentest_check_template_ids: [Int!]!
  ) {
    reviewBitRecommendations(
      input: {
        bounty_informed_generator_run_id: $bounty_informed_generator_run_id
        engagement_interests: $engagement_interests
        pentest_check_template_ids: $pentest_check_template_ids
      }
    ) {
      was_successful
      errors {
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
`);export{o as a,a as i,r as n,i as o,s as r,t as s,n as t};
import{Kx as e,qx as t}from"./vendor-_WdvpBLr.js";import"./app-5pKgUmmm.js";t();var n=e`
  mutation UpdateHackerPreferenceMutation(
    $level: String
    $opportunity_types: [String!]
    $availability: String
    $collaboration: String
    $has_asset_type_preferences: Boolean
    $has_weakness_preferences: Boolean
  ) {
    updateHackerPreference(
      input: {
        level: $level
        availability: $availability
        opportunity_types: $opportunity_types
        collaboration: $collaboration
        has_asset_type_preferences: $has_asset_type_preferences
        has_weakness_preferences: $has_weakness_preferences
      }
    ) {
      was_successful
      __typename
      hacker_preference {
        id
        level
        opportunity_types
        availability
        collaboration
        has_asset_type_preferences
        has_weakness_preferences
        __typename
      }
    }
  }
`,r=e`
  mutation UpdateHackerPreferencesAssetTypes(
    $asset_types: [HackerPreferencesAssetTypeInputType!]!
  ) {
    updateHackerPreferencesAssetTypes(input: { asset_types: $asset_types }) {
      was_successful
      __typename
    }
  }
`,i=e`
  mutation UpdateHackerPreferencesWeaknesses($weaknesses: [String!]!) {
    updateHackerPreferencesWeaknesses(input: { weaknesses: $weaknesses }) {
      was_successful
      __typename
    }
  }
`,a=e`
  mutation UpdateHackerSkills($skills: [HackerSkillInputType!]!) {
    updateHackerSkills(input: { skills: $skills }) {
      __typename
      was_successful
      me {
        id
        __typename
        hacker_skills {
          nodes {
            id
            __typename
            proficiency
            skill {
              id
              __typename
              name
            }
          }
        }
      }
      errors {
        edges {
          node {
            id
            type
            field
            message
          }
        }
      }
    }
  }
`,o=e`
  mutation DeleteHackerSkill($id: ID!) {
    deleteHackerSkill(input: { hacker_skill_id: $id }) {
      __typename
      was_successful
      me {
        id
        __typename
        hacker_skills {
          nodes {
            id
            __typename
            proficiency
            skill {
              id
              __typename
              name
            }
          }
        }
      }
      errors {
        edges {
          node {
            id
            type
            field
            message
          }
        }
      }
    }
  }
`;export{a,i,r as n,n as r,o as t};
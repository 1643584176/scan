import{Kx as e,qx as t}from"./vendor-_WdvpBLr.js";import"./app-5pKgUmmm.js";t();var n=e`
  fragment AllEvents on IntegrationEventsConfiguration {
    id
    ${window.constants.configurable_webhook_events.join(`
`)}
  }
`,r=e`
  query TeamWebhooksQuery($handle: String!) {
    team(handle: $handle) {
      id
      i_can_manage_webhooks
      webhooks_delivery_paused
      webhooks {
        edges {
          node {
            _id
            id
            name
            url
            integration_events_configuration {
              id
              ...AllEvents
            }
            last_response_success
          }
        }
      }
    }
  }
  ${n}
`,i=e`
  query WebhookQuery($id: ID!, $handle: String!) {
    webhook(id: $id) {
      id
      _id
      name
      url
      secret
      created_by {
        id
        _id
        membership(team_handle: $handle) {
          id
          _id
        }
        name
        username
      }
      integration_events_configuration {
        id
        ...AllEvents
      }
      webhook_requests {
        edges {
          node {
            _id
            id
            uuid
            created_at
            last_webhook_response: webhook_responses(
              first: 1
              order_by: { created_at: { _direction: DESC } }
            ) {
              edges {
                node {
                  id
                  success
                  execution_time
                  response_headers
                  response_body
                  response_code
                }
              }
            }
          }
        }
      }
    }
  }
  ${n}
`,a=e`
  mutation CreateWebhook($input: CreateWebhookInput!) {
    createWebhook(input: $input) {
      webhook {
        id
        _id
      }
      team {
        id
        webhooks {
          edges {
            node {
              id
              name
              url
              deleted_at
              integration_events_configuration {
                id
                ...AllEvents
              }
            }
          }
        }
      }
      was_successful
      errors {
        edges {
          node {
            id
            type
            message
            field
          }
        }
      }
    }
  }
  ${n}
`,o=e`
  mutation updateWebhook($input: UpdateWebhookInput!) {
    updateWebhook(input: $input) {
      webhook {
        id
        _id
        name
        url
        secret
        integration_events_configuration {
          id
          ...AllEvents
        }
      }
      team {
        id
        webhooks {
          edges {
            node {
              id
              name
              url
              deleted_at
              integration_events_configuration {
                id
                ...AllEvents
              }
            }
          }
        }
      }
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
  ${n}
`,s=e`
  mutation testWebhook($input: TestWebhookRequestInput!) {
    testWebhook(input: $input) {
      webhook {
        id
      }
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
`,c=e`
  mutation DeleteWebhook($webhook_id: ID!) {
    deleteWebhook(input: { webhook_id: $webhook_id }) {
      team {
        id
        webhooks {
          edges {
            node {
              id
              url
              deleted_at
            }
          }
        }
      }
      was_successful
      errors(first: 100) {
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
`,l=e`
  query IntegrationEventsQuery {
    __type(name: "IntegrationEventsEnum") {
      enumValues {
        name
        description
      }
    }
  }
`;export{o as a,s as i,c as n,r as o,l as r,i as s,a as t};
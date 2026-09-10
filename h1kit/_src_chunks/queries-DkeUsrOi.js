import{Cp as e}from"./app-5pKgUmmm.js";var t=e(`
  query PentestOverviewScopePage(
    $pentest_id: ID!
    $order_by: ReportOrderInput
  ) {
    pentest(id: $pentest_id) {
      ...PentestItem
    }
  }
`),n=e(`
  query PentestChecklistTemplates($organization_id: ID) {
    pentest_checklist_templates(organization_id: $organization_id) {
      edges {
        node {
          ...PentestChecklistTemplateItem
        }
      }
    }
  }
`),r=e(`
  query OrganizationBountyInformedPentestGeneratorRuns($organization_id: ID) {
    organization_bounty_informed_pentest_generator_runs(
      organization_id: $organization_id
    ) {
      edges {
        node {
          ...BountyInformedPentestGeneratorRunItem
        }
      }
    }
  }
`),i=e(`
    query OrganizationBountyInformedPentestGeneratorRunsByRunId($run_id: ID) {
      organization_bounty_informed_pentest_generator_runs(run_id: $run_id) {
        edges {
          node {
            ...BountyInformedPentestGeneratorRunItem
          }
        }
      }
    }
  `);export{t as i,i as n,n as r,r as t};
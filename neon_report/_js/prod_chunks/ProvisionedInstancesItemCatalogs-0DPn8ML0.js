import{r as p,j as s}from"./client-CJWnElJ8.js";import{a0 as P,ag as f,Z as T,c as w,m as M,bq as U,h as y,f as j,d7 as D,br as S,d8 as k,ah as Q,ak as N,aj as B,al as K,ai as G,cn as $,ce as H,c9 as V,aN as W,bl as v,F as I,eb as Y,bs as Z,aQ as z,cf as J,ca as X,k as ee,L as ae,n as se,M as te,P as ne,N as oe,cj as ie,ar as re,as as le,T as de,B as ce,Q as ue}from"./index-LpJ7SKi1.js";import{u as pe}from"./useCurrentProvisionedInstance-BkyxKEkQ.js";import{P as E}from"./ProvisionedInstanceBreadcrumbs-CnB8cdNq.js";import{am as me,an as ge,ao as _,ac as x}from"./app-CcBRprEu.js";import{P as A}from"./PageHeader-DhONzvbJ.js";import{a as be}from"./DataTableV2-B3xJMmGN.js";import"./types-CrgfaYBw.js";import"./PageBreadcrumbs-CgE_ElqT.js";import"./index-BaCL4lmF.js";import"./app-DhvLx_7T.js";import"./updateLastAccount-CSSs55Mv.js";import"./_createAggregator-Cs40TtXa.js";import"./useSpendingLimit-BOfur3zg.js";import"./IntegrationsDrawersContext-oO8erN8V.js";import"./isArrayLikeObject-Bf875Hlt.js";import"./_setToString-FuidWOqj.js";import"./useInfiniteQuery-BiuUWIvM.js";import"./ReactQueryProvider-L_CY4zDe.js";import"./CreateProjectFormFields-BZ5igvYy.js";import"./identity-urls-DHWY89pI.js";import"./identity-events-DyNPdmAY.js";import"./index-CBRZeV4m.js";/* empty css              */import"./Table-DQWS6EOt.js";import"./useGridSelectionCheckbox-iwSv-wSJ.js";const h=a=>["provisioned-instance-catalogs",a],fe=(a,e)=>P({queryKey:h(a),queryFn:async()=>(await f.listProvisionedInstanceCatalogs()).data.catalogs.filter(o=>o.securable_kind==="CATALOG_MANAGED_POSTGRESQL"&&o.properties?.endpoint_id===e).map(o=>({name:o.name,uid:o.id,database_name:o?.options?.database??"",database_instance_name:a,owner:o.owner})),enabled:!!e}),ye=a=>{const e=T();return w({mutationFn:t=>f.deleteProvisionedInstanceCatalog(t),onSuccess:()=>{e.invalidateQueries({queryKey:h(a)})}})},ve=a=>{const{trackUiInteraction:e}=M(),{confirm:t}=U(),{formatMessage:n}=y(),{mutateAsync:i}=ye(a),o=p.useCallback(async r=>{if(!await t({appearance:"danger",header:n({id:"pC8x3q",defaultMessage:[{type:0,value:"Do you want to delete this catalog?"}]}),text:s.jsx(j,{appearance:"warning",children:n({id:"pV/8n0",defaultMessage:[{type:0,value:"This action cannot be undone. This will permanently delete the catalog "},{type:1,value:"catalogName"},{type:0,value:"."}]},{catalogName:r.name})}),confirmButtonText:n({id:"InSM2d",defaultMessage:[{type:0,value:"Delete"}]}),declineButtonText:n({id:"/65VAo",defaultMessage:[{type:0,value:"Cancel"}]})})){e("provisioned_instance_delete_catalog_confirmation_dismissed");return}e("provisioned_instance_delete_catalog_confirmation_confirmed"),await D("sev2",k.P999,"Provisioned instance catalog: Delete catalog failed").runWithErrorToast(async()=>{await i(r.name),S(n({id:"Z2fvah",defaultMessage:[{type:0,value:"Successfully deleted catalog "},{type:1,value:"catalogName"}]},{catalogName:r.name}))})},[e,n,t,i]);return p.useCallback(r=>({label:n({id:"J2dAor",defaultMessage:[{type:0,value:"Delete"}]}),icon:"trash",appearance:"danger",onClick(){e("provisioned_instance_catalog_delete_clicked"),o(r)}}),[n,e,o])},_e=N`
  fragment PipelineApiErrorFields on ApiError {
    code
    message
    helpUrl
    traceId
    errorDetails {
      ... on ErrorDetailErrorInfo {
        reason
        domain
        metadata
      }
      ... on ErrorDetailRequestInfo {
        requestId
        servingData
      }
    }
  }
`,Ce=B(N`
  query PipelineListQuery($input: DeltapipelinesListPipelinesInput!) @component(name: "Workflows.Observability.Lists") {
    deltapipelinesList: jobsListPipelines(input: $input) {
      nextPageToken
      prevPageToken
      statuses {
        runAsUserName
        permissionLevel
        latestUpdates {
          creationTime
          state
          updateId
        }
        name
        pipelineId
        state
        ownerPrincipal @includeSafex(name: "databricks.fe.enrichPrincipalUi", defaultValue: false) {
          id
          uniqueName
          kind
          displayName
        }
        userActivityInfo
          @includeSafex(name: "databricks.fe.pipelines.enablePipelinesTableFavoriteIndicator", defaultValue: false) {
          assetType
          assetId
          isFavorite
        }
      }
      apiError {
        ...PipelineApiErrorFields
      }
    }
  }
  ${_e}
`);function Pe({filter:a,limit:e=100,skip:t}={}){const n=Q().data?.csrfToken;return P({queryKey:["pipelines",n],enabled:!t,queryFn:K("PipelineListQuery",async i=>{const o=await i.request(Ce,{input:{filter:a,maxResults:e}});if(!o.deltapipelinesList)return[];const{statuses:r,apiError:c}=o.deltapipelinesList;if(c)throw new Error(c.message??c.code??c.__typename??"Unknown error");return r??[]})})}const Me=(a,e)=>{let t={};return e?t={pipelineId:e,sourceCatalog:a.name,sourceCatalogId:a.uid}:t={sourceCatalog:a.name,sourceCatalogId:a.uid,sourceType:"MANAGED_POSTGRESQL",step:"brickstore_source"},`${window.location.origin}/ingestion/pipelines/setup?${new URLSearchParams(t)}`};function he(){return G("managed_pg_connector",!1)&&!0}const Ie=({catalog:a,children:e})=>{const{trackUiInteraction:t}=M(),{formatMessage:n}=y(),{data:i,isLoading:o}=Pe({filter:`name LIKE 'database_catalog_ingestion_pipeline_${a.uid}'`,limit:1}),r=i?.[0];return e({label:n(r?{id:"Q0L4f8",defaultMessage:[{type:0,value:"Manage streaming tables"}]}:{id:"b4Tc1P",defaultMessage:[{type:0,value:"Create streaming tables"}]}),icon:"edit",href:Me(a,r?.pipelineId??void 0),disabled:o,openInNewTab:!0,onClick(){t("provisioned_instance_catalog_streaming_tables_clicked")}})},Ee=()=>{const a=he();return p.useCallback(e=>{if(a)return(({renderWrapper:t})=>s.jsx(Ie,{catalog:e,children:t}))},[a])},xe=a=>{const e=ve(a),t=Ee();return p.useCallback(n=>$([t(n),e(n)]),[e,t])},Ae=a=>["provisioned-instance-databases",a],Te=a=>P({queryKey:Ae(a),queryFn:async()=>(await f.listProvisionedInstanceDatabases(a)).data.databases.filter(t=>t.is_usable_by_customer).map(t=>t.name)}),we=a=>{const e=T();return w({mutationFn:t=>f.createProvisionedInstanceCatalog(t),onSuccess:()=>{e.invalidateQueries({queryKey:h(a)})}})},C="__CREATE_NEW_DATABASE_OPTION__",je=({provisionedInstanceName:a,databasesWithCatalogs:e,onSuccess:t,onRequestClose:n})=>{const{formatMessage:i}=y(),o=H(),{mutateAsync:r}=we(a),c=async l=>{await D("sev2",k.P999,"Provisioned instance catalog: Create catalog failed").runWithErrorToast(async()=>{await r({name:l.name,create_database_if_not_exists:!0,database_instance_name:a,database_name:l.databaseName===C?l.newDatabaseName:l.databaseName}),t?.({name:l.name})})},{data:u}=Te(a),m=p.useMemo(()=>[...u?.map(l=>({value:l,label:l,disabled:e.includes(l),disabledTooltip:i({id:"xpNlZb",defaultMessage:[{type:0,value:"Already has a catalog"}]})}))??[],{value:C,label:i({id:"90P6G0",defaultMessage:[{type:0,value:"Create new database"}]})}],[u,e,i]),g=o.watch("databaseName");return s.jsxs(V,{providerProps:o,onSubmit:c,modalProps:{title:i({id:"OslGx0",defaultMessage:[{type:0,value:"Add catalog"}]}),isOpen:!0,onRequestClose:n},children:[s.jsxs(W,{gaps:!0,children:[s.jsx(v,{label:i({id:"Qp6KHw",defaultMessage:[{type:0,value:"Catalog name"}]}),error:o.formState.errors.name?.message,children:s.jsx(I,{...o.register("name",{required:{value:!0,message:"This field is required"}})})}),s.jsx(v,{label:i({id:"AhHdof",defaultMessage:[{type:0,value:"Postgres database"}]}),error:o.formState.errors.databaseName?.message,children:s.jsx(Y,{name:"databaseName",control:o.control,render:({field:l})=>s.jsx(Z,{options:m,value:l.value,onChange:l.onChange})})}),g===C&&s.jsx(v,{label:i({id:"NmYHqi",defaultMessage:[{type:0,value:"New database name"}]}),error:o.formState.errors.newDatabaseName?.message,children:s.jsx(I,{...o.register("newDatabaseName",{required:{value:!0,message:"This field is required"},shouldUnregister:!0})})})]}),s.jsxs(z,{children:[s.jsx(J,{}),s.jsx(X,{children:i({id:"K+9lTV",defaultMessage:[{type:0,value:"Create"}]})})]})]})},De="_subtitle_6pi4u_1",Se={subtitle:De},oa=()=>{const{trackUiInteraction:a}=M(),{formatMessage:e}=y(),t=ee(),{data:n,isError:i,isPending:o,provisionedInstanceName:r}=pe(),c=n?me(n):!1,{data:u}=ge(r),m=u!=null&&u.state!=null&&u.state!==_.NOT_UPGRADED&&u.state!==_.STATE_UNSPECIFIED,g=m&&u?.state===_.UPGRADE_SUCCEEDED||!m&&c,{data:l,isError:L,isPending:R}=fe(r,g?void 0:n?.uid),F=xe(r),q=p.useMemo(()=>l?.map(d=>d.database_name)??[],[l]),O=p.useMemo(()=>[{id:"name",header:e({id:"ZKkwYF",defaultMessage:[{type:0,value:"Name"}]}),enableSorting:!0,accessorKey:"name",rowHeader:!0,render:d=>s.jsx(ae,{href:`${window.location.origin}/explore/data/${d.name}`,openInNewTab:!0,children:d.name})},{id:"database",header:e({id:"gC7dWg",defaultMessage:[{type:0,value:"Database"}]}),enableSorting:!0,accessorKey:"database_name"},{id:"owner",header:e({id:"AslgG0",defaultMessage:[{type:0,value:"Owner"}]}),accessorKey:"owner",render:d=>d.owner??"-"}],[e]),b=se(te.AddCatalogModal);return i||L?s.jsx(ne,{}):g?s.jsxs(s.Fragment,{children:[s.jsx(A,{breadcrumbs:s.jsx(E,{}),title:e({id:"OHFABD",defaultMessage:[{type:0,value:"Catalogs"}]})}),s.jsx(j,{appearance:"info",children:s.jsx(oe,{id:"wkSu9j",defaultMessage:[{type:0,value:"Catalogs are not available for upgraded instances. "},{type:8,value:"link",children:[{type:0,value:"Open in Lakebase"}]},{type:0,value:" to explore your data."}],values:{link:d=>s.jsx(ie,{href:re(le.ProjectsList),children:d})}})})]}):s.jsxs(s.Fragment,{children:[b.isModalOpen&&s.jsx(je,{provisionedInstanceName:r,databasesWithCatalogs:q,onSuccess:d=>{a("provisioned_instance_add_catalog_modal_confirmed"),b.closeModal(),S(e({id:"ODD4mO",defaultMessage:[{type:0,value:"Successfully created catalog "},{type:1,value:"catalogName"}]},{catalogName:d.name}))},onRequestClose:()=>{a("provisioned_instance_add_catalog_modal_dismissed"),b.closeModal()}}),s.jsx(A,{breadcrumbs:s.jsx(E,{}),title:e({id:"OHFABD",defaultMessage:[{type:0,value:"Catalogs"}]}),actions:s.jsx(de,{content:e({id:"E6yuUf",defaultMessage:[{type:0,value:"Catalogs can only be created when the database is available"}]}),disabled:!n||x(n.state),children:s.jsx("div",{children:s.jsx(ce,{icon:"add","aria-label":e({id:"rO+v9n",defaultMessage:[{type:0,value:"Add catalog"}]}),onClick:()=>b.openModal(),disabled:!n||!x(n.state),children:t?null:e({id:"rO+v9n",defaultMessage:[{type:0,value:"Add catalog"}]})})})})}),s.jsx(ue,{appearance:"secondary",className:Se.subtitle,children:e({id:"cY1mRj",defaultMessage:[{type:0,value:"Catalogs enable you to connect your Lakebase database directly to your Lakehouse."}]})}),s.jsx(be,{"aria-label":e({id:"3yzuFs",defaultMessage:[{type:0,value:"Database roles"}]}),columns:O,rows:l??[],isLoading:o||R,rowActions:F})]})};export{oa as ProvisionedInstancesItemCatalogs};

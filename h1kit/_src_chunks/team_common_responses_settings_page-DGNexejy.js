import{o as e}from"./rolldown-runtime-DAXXjFlN.js";import{Fw as t,Hi as n,Kx as r,Lr as i,Mr as a,Rw as o,Vw as s,eb as c,qx as l,zd as u,zx as d}from"./vendor-_WdvpBLr.js";import{Ah as f,Nn as p,Pn as m,Sm as h,T as g,Th as _,_h as v,ba as y,dh as b,k as x,lh as S,qr as C,rp as w,uh as T,vh as E}from"./app-5pKgUmmm.js";import{t as D}from"./assign-KNTwIu30.js";var O=e(D()),k=e(n()),A=e(d()),j=e(o()),M=e(s()),N=t(),{common_response_triggers:P}=window.constants,F=class extends j.Component{static displayName=`EditTriggerModal`;static propTypes={handle:A.default.string.isRequired,closeModal:A.default.func.isRequired,commonResponses:A.default.arrayOf(A.default.shape({title:A.default.string.isRequired,id:A.default.number.isRequired}))};state={loading:!1,triggers:{}};UNSAFE_componentWillMount(){let{handle:e}=this.props;this.setState({loading:!0}),M.default.ajax({url:`/${e}/common_responses/triggers.json`}).done(e=>this.setState({loading:!1,triggers:(0,k.default)(e,e=>e.id)})).fail(()=>this.setState({loading:!1}))}handleSubmit=e=>{let{triggers:t}=this.state,{handle:n,closeModal:r}=this.props;e.preventDefault(),this.setState({loading:!0}),M.default.ajax({url:`/${n}/common_responses/triggers.json`,method:`POST`,data:{triggers:t}}).done(()=>this.setState({loading:!1},()=>r())).fail(()=>this.setState({loading:!1}))};handleSelectChangeFactory=e=>t=>{t.preventDefault();let n=(0,O.default)({},this.state.triggers);n[e]=t.target.value,this.setState({triggers:n})};render(){let{commonResponses:e}=this.props,{loading:t,triggers:n}=this.state;return(0,N.jsxs)(w,{size:`large`,onCloseModal:this.props.closeModal,children:[t?(0,N.jsx)(_,{}):null,(0,N.jsx)(p.Context,{name:constants.gates.all.common_responses,teamHandle:this.props.handle,children:(0,N.jsxs)(`form`,{onSubmit:this.handleSubmit,children:[(0,N.jsx)(`div`,{className:`settings-title-container`,children:(0,N.jsx)(`h2`,{children:`Default Common Responses`})}),(0,N.jsx)(p.Closed,{children:(0,N.jsx)(m,{})}),(0,N.jsx)(`p`,{children:`You can use the form below to choose a default Common Response that will be used when you select an action for a report.`}),P.map(r=>(0,N.jsxs)(`table`,{className:`table table--layout-auto`,children:[(0,N.jsx)(`thead`,{children:(0,N.jsx)(`tr`,{children:(0,N.jsx)(`td`,{colSpan:`2`,children:(0,N.jsx)(`strong`,{children:r.name})})})}),(0,N.jsx)(`tbody`,{children:r.events.map(r=>(0,N.jsxs)(`tr`,{children:[(0,N.jsx)(`td`,{className:`table__cell--width-3-10`,children:r.title}),(0,N.jsx)(`td`,{children:(0,N.jsxs)(p.select,{disabled:t,name:`trigger[${r.name}]`,className:`input`,value:n[r.name]||``,onChange:this.handleSelectChangeFactory(r.name),children:[(0,N.jsx)(`option`,{value:``,children:`none`}),e.map(e=>(0,N.jsx)(`option`,{value:e.id,children:e.title},e.id))]})})]},r.name))})]},r.action)),(0,N.jsx)(`div`,{className:`content-footer`,children:(0,N.jsx)(`div`,{className:`content-footer-wrapper`,children:(0,N.jsx)(`div`,{className:`content-footer-right`,children:(0,N.jsx)(p.Button,{disabled:t,type:`submit`,variation:`success`,children:`Save`})})})})]})})]})}};l();var I=r`
  fragment CommonResponseFragment on CommonResponse {
    id
    databaseId: _id
    title
    message
  }
`,L=r`
  query CommonResponses($handle: String!) {
    teams(where: { handle: { _eq: $handle } }) {
      nodes {
        id
        common_responses(order_by: { title: { _direction: ASC } }) {
          nodes {
            id
            ...CommonResponseFragment
          }
        }
      }
    }
  }

  ${I}
`,R=r`
  mutation DestroyCommonResponse($id: ID!) {
    destroyCommonResponse(input: { common_response_id: $id }) {
      was_successful
      team {
        id
        common_responses {
          nodes {
            id
            ...CommonResponseFragment
          }
        }
      }
    }
  }

  ${I}
`,z=({handle:e})=>{let{data:t,loading:n,error:r}=E(L,{variables:{handle:e}}),[i]=v(R),[o,s]=(0,j.useState)(!1);if(n)return(0,N.jsx)(`span`,{children:`Loading...`});if(r)return(0,N.jsx)(`span`,{children:`An error occurred`});let l=t.teams.nodes[0].common_responses.nodes,d=e=>{confirm(`Are you sure that you want to remove this common response?`)&&i({variables:{id:e},onCompleted:({destroyCommonResponse:{was_successful:e}})=>{e&&h(`notice`,`Common Response successfully removed.`)},refetchQueries:[L]})};return(0,N.jsxs)(p.Context,{name:constants.gates.all.common_responses,teamHandle:e,children:[l.length===0?(0,N.jsx)(a,{icon:`campaigns`,header:`No common responses created yet`,description:`Common responses help keep messaging consistent and save you from typing the same thing repeatedly. When you take action on a report, you can have a response pre-populate for that specific action.`,primaryButton:{children:`Add common response`,to:`/${e}/common_responses/new`,renderAs:c.Link},secondaryButton:{children:`Learn more`,renderAs:c.Link,external:!0,openNewTab:!0,to:`https://docs.hackerone.com/en/articles/8541465-common-responses`,icons:{right:{src:u}}}}):(0,N.jsxs)(N.Fragment,{children:[(0,N.jsxs)(S,{justifyContent:`flex-end`,children:[(0,N.jsx)(T,{size:`small`,children:l.length>0?(0,N.jsx)(`a`,{className:`button button--small margin-5--right`,href:``,onClick:e=>{e.preventDefault(),s(!0)},children:`Set default Common Responses`}):null}),(0,N.jsx)(T,{size:`small`,children:(0,N.jsx)(b,{to:`/${e}/common_responses/new`,className:`button button--small js-create-common-responses`,children:`Add Common Response`})})]}),(0,N.jsx)(`table`,{className:`table table--layout-auto`,children:(0,N.jsx)(`tbody`,{children:l.map((t,n)=>(0,N.jsxs)(`tr`,{className:`spec-common-response`,children:[(0,N.jsx)(`td`,{children:(0,N.jsx)(b,{to:`/${e}/common_responses/${t.databaseId}/edit`,children:t.title})}),(0,N.jsx)(`td`,{children:(0,N.jsx)(p.Open,{children:(0,N.jsx)(`a`,{href:``,onClick:e=>{e.preventDefault(),d(t.id)},className:`link red spec-remove-common-response pull-right`,children:`Remove`})})})]},n))})})]}),o?(0,N.jsx)(F,{handle:e,closeModal:()=>s(!1),commonResponses:l.map(e=>({id:e.databaseId,title:e.title}))}):null]})};z.propTypes={handle:A.default.string.isRequired};var B=e=>{let{match:{params:{handle:t}}}=e;return(0,N.jsx)(C,{children:(0,N.jsx)(g,{header:(0,N.jsx)(x,{...e}),tertiaryHeader:`Common Responses`,content:(0,N.jsxs)(`div`,{children:[(0,N.jsx)(i,{children:(0,N.jsx)(`title`,{children:y(`Common Responses`)})}),(0,N.jsx)(`div`,{children:(0,N.jsx)(z,{handle:t})})]}),footer:(0,N.jsx)(f,{})})})};B.propTypes={match:A.default.shape({params:A.default.shape({handle:A.default.string.isRequired}).isRequired}).isRequired};export{B as default};
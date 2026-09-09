import{o as e}from"./rolldown-runtime-DAXXjFlN.js";import{Fw as t,Kx as n,Lr as r,Rw as i,qx as a,zx as o}from"./vendor-_WdvpBLr.js";import{Th as s,ba as c,vh as l}from"./app-5pKgUmmm.js";var u=e(i()),d=e(o());a();var f=t(),p=n`
  query WebHacking101DownloadPage {
    session {
      id
      csrf_token
    }
  }
`,m=class extends u.Component{static propTypes={csrf_token:d.default.string.isRequired};componentDidMount(){this.refs.download_web_hacking_101.submit()}render(){let{csrf_token:e}=this.props;return(0,f.jsxs)(`div`,{children:[(0,f.jsxs)(r,{children:[(0,f.jsx)(`title`,{children:c(`Download your free copy of Web Hacking 101`)}),(0,f.jsx)(`meta`,{name:`description`,content:`Download your free copy of Web Hacking 101`})]}),(0,f.jsxs)(`form`,{method:`post`,action:`/resources/download-web-hacking-101`,ref:`download_web_hacking_101`,children:[(0,f.jsx)(`input`,{name:`authenticity_token`,type:`hidden`,value:e}),`Redirecting you to the download..."`]})]})}},h=()=>{let{data:e,loading:t}=l(p,{fetchPolicy:`no-cache`});return t?(0,f.jsx)(s,{size:`small`}):(0,f.jsx)(m,{csrf_token:e.session.csrf_token})};export{h as default};
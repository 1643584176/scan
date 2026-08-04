"use strict";(self.webpackChunk_N_E=self.webpackChunk_N_E||[]).push([[1918],{71918:function(e,t,n){Object.defineProperties(t,{__esModule:{value:!0},[Symbol.toStringTag]:{value:"Module"}});let r=n(85893),i=n(89854),a=n(35232),o=n(84183),l=n(25585),s=n(67294),u=n(24346),c=n(38123),d=n(50066),f=e=>e&&e.__esModule?e:{default:e},m=f(l),p=f(s),g=f(d);function h(e){return"number"==typeof e}function v(e){return"string"==typeof e}function x(e){return"[object Object]"===Object.prototype.toString.call(e)}function b(e){var t;return x(e)||Array.isArray(e)}function S(e){return Math.abs(e)}function y(e){return e?e/S(e):0}function M(e){return E(e).map(Number)}function w(e){return e[k(e)]}function k(e){return Math.max(0,e.length-1)}function E(e){return Object.keys(e)}function T(e,t){var n=S(e-t);function r(t){return t<e}function i(e){return e>t}function a(n){var r,i;return n<e||n>t}return{length:n,max:t,min:e,constrain:function(n){var r;return a(n)?n<e?e:t:n},reachedAny:a,reachedMax:i,reachedMin:r,removeOffset:function(e){return n?e-n*Math.ceil((e-t)/n):e}}}function L(){var e=[],t={add:function(n,r,i,a){return void 0===a&&(a={passive:!0}),n.addEventListener(r,i,a),e.push(function(){return n.removeEventListener(r,i,a)}),t},removeAll:function(){return e=e.filter(function(e){return e()}),t}};return t}function C(e){var t=e;function n(){return t}function r(e){return t/=e,a}function i(e){return h(e)?e:e.get()}var a={add:function(e){return t+=i(e),a},divide:r,get:n,multiply:function(e){return t*=e,a},normalize:function(){return 0!==t&&r(t),a},set:function(e){return t=i(e),a},subtract:function(e){return t-=i(e),a}};return a}function j(e,t,n){var r="x"===e.scroll?function(e){return"translate3d(".concat(e,"px,0px,0px)")}:function(e){return"translate3d(0px,".concat(e,"px,0px)")},i=n.style,a=!1;function o(e){a=!e}return{clear:function(){a||(i.transform="",n.getAttribute("style")||n.removeAttribute("style"))},to:function(e){a||(i.transform=r(t.apply(e.get())))},toggleActive:o}}var A={align:"center",axis:"x",container:null,slides:null,containScroll:"",direction:"ltr",slidesToScroll:1,breakpoints:{},dragFree:!1,draggable:!0,inViewThreshold:0,loop:!1,skipSnaps:!1,speed:10,startIndex:0,active:!0};function B(){function e(e,t){return function e(t,n){return[t,n].reduce(function(t,n){return E(n).forEach(function(r){var i=t[r],a=n[r],o=x(i)&&x(a);t[r]=o?e(i,a):a}),t},{})}(e,t||{})}return{merge:e,areEqual:function(e,t){var n=JSON.stringify(E(e.breakpoints||{})),r=JSON.stringify(E(t.breakpoints||{}));return n===r&&function e(t,n){var r=E(t),i=E(n);return r.length===i.length&&r.every(function(r){var i=t[r],a=n[r];return"function"==typeof i?"".concat(i)==="".concat(a):b(i)&&b(a)?e(i,a):i===a})}(e,t)},atMedia:function(t){var n=t.breakpoints||{},r=E(n).filter(function(e){return window.matchMedia(e).matches}).map(function(e){return n[e]}).reduce(function(t,n){return e(t,n)},{});return e(t,r)}}}function D(e,t,n){var r,i,a,o,l=L(),s=B(),u=function(){var e=B(),t=e.atMedia,n=e.areEqual,r=[],i=[];function a(e){var r=t(e.options);return function(){return!n(r,t(e.options))}}return{init:function(e,n){return i=e.map(a),(r=e.filter(function(e){return t(e.options).active})).forEach(function(e){return e.init(n)}),e.reduce(function(e,t){var n;return Object.assign(e,((n={})[t.name]=t,n))},{})},destroy:function(){r=r.filter(function(e){return e.destroy()})},haveChanged:function(){return i.some(function(e){return e()})}}}(),c=function(){var e={};function t(t){return e[t]||[]}var n={emit:function(e){return t(e).forEach(function(t){return t(e)}),n},off:function(r,i){return e[r]=t(r).filter(function(e){return e!==i}),n},on:function(r,i){return e[r]=t(r).concat([i]),n}};return n}(),d=c.on,f=c.off,m=!1,p=s.merge(A,D.globalOptions),g=s.merge(p),x=[],b=0;function E(t,n){if(!m){var l,d,f,A,B,D,P,$,V,O,I,W,H,z,F,R,_,q,X,Y,U,G,J,Z,K,ee,et,en,er,ei,ea,eo,el,es,eu,ec,ed,ef,em,ep,eg,eh,ev,ex,eb,eS,ey,eM,ew,ek,eE,eT,eL,eC,ej,eA,eB,eD,eP,eN,e$,eV,eO,eI,eW,eH,ez,eF,eQ,eR,e_,eq,eX,eY,eU,eG,eJ,eZ,eK,e0,e1,e2,e4,e5,e3,e6,e8,e9,e7,te,tt,tn,tr,ti,ta,to,tl,ts,tu,tc,td,tf,tm,tp,tg,th,tv,tx,tb,tS,ty,tM;if(p=s.merge(p,t),l=(g=s.atMedia(p)).container,d=g.slides,a=(v(l)?e.querySelector(l):l)||e.children[0],f=v(d)?a.querySelectorAll(d):d,o=[].slice.call(f||a.children),B=a,D=o,ez=(P=g).align,eF=P.axis,eQ=P.direction,eR=P.startIndex,e_=P.inViewThreshold,eq=P.loop,eX=P.speed,eY=P.dragFree,eU=P.slidesToScroll,eG=P.skipSnaps,eJ=P.containScroll,eZ=B.getBoundingClientRect(),eK=D.map(function(e){return e.getBoundingClientRect()}),e0=function(e){var t="rtl"===e?-1:1;function n(e){return e*t}return{apply:n}}(eQ),z=e2=(W="y"==(I="y"===eF?"y":"x")?"top":"rtl"===eQ?"right":"left",H="y"===I?"bottom":"rtl"===eQ?"left":"right",e1={scroll:I,cross:"y"===eF?"x":"y",startEdge:W,endEdge:H,measureSize:function(e){var t=e.width,n=e.height;return"x"===I?t:n}}).measureSize(eZ),e4={measure:function(e){return z*(e/100)}},e5=function(e,t){var n={start:r,center:function(e){var n;return n=e,(t-n)/2},end:i};function r(){return 0}function i(e){return t-e}return{measure:function(r){return h(e)?t*Number(e):n[e](r)}}}(ez,e2),e3=!eq&&""!==eJ,e8=(X=eq||""!==eJ,Y=e1.measureSize,U=e1.startEdge,G=e1.endEdge,J=eK[0]&&X,Z=function(){if(!J)return 0;var e=eK[0];return S(eZ[U]-e[U])}(),K=function(){if(!J)return 0;var e=window.getComputedStyle(w(D));return parseFloat(e.getPropertyValue("margin-".concat(G)))}(),ee=eK.map(Y),et=eK.map(function(e,t,n){var r=t===k(n);return t?r?ee[t]+K:n[t+1][U]-e[U]:ee[t]+Z}).map(S),e6={slideSizes:ee,slideSizesWithGaps:et}).slideSizes,e9=e6.slideSizesWithGaps,ea=h(eU),e7={groupSlides:function(e){var t,n,r;return ea?M(e).filter(function(e){return e%eU==0}).map(function(t){return e.slice(t,t+eU)}):M(e).reduce(function(e,t){var n=e9.slice(w(e),t+1).reduce(function(e,t){return e+t},0);return!t||n>e2?e.concat(t):e},[]).map(function(t,n,r){return e.slice(t,r[n+1])})}},tt=(em=e1.startEdge,ep=e1.endEdge,eh=(eg=e7.groupSlides)(eK).map(function(e){return w(e)[ep]-e[0][em]}).map(S).map(e5.measure),ev=eK.map(function(e){return eZ[em]-e[em]}).map(function(e){return-S(e)}),tS=w(ev)-w(e9),ex=eg(ev).map(function(e){return e[0]}).map(function(e,t,n){var r=t===k(n);return e3&&!t?0:e3&&r?tS:e+eh[t]}),te={snaps:ev,snapsAligned:ex}).snaps,tn=te.snapsAligned,tr=-w(tt)+w(e9),ti=(ew=T(-tr+e2,tn[0]),ek=tn.map(ew.constrain),{snapsContained:eE=function(){if(tr<=e2)return[ew.max];if("keepSnaps"===eJ)return ek;var e,t,n,r,i=(e=ek[0],t=w(ek),n=ek.lastIndexOf(e),r=ek.indexOf(t)+1,T(n,r)),a=i.min,o=i.max;return ek.slice(a,o)}()}).snapsContained,to=(ty=(ta=e3?ti:tn)[0],tM=w(ta),{limit:ej=T(eq?ty-tr:tM,ty)}).limit,ts=(tl=function e(t,n,r){var i=T(0,t),a=i.min,o=i.constrain,l=t+1,s=u(n);function u(e){return r?S((l+e)%l):o(e)}function c(){return s}function d(e){return s=u(e),f}var f={add:function(e){return d(s+e)},clone:function(){return e(t,s,r)},get:c,set:d,min:a,max:t};return f}(k(ta),eR,eq)).clone(),tu=M(D),tc=function(e){var t=0;function n(e,n){return function(){!!t===e&&n()}}function r(){t=window.requestAnimationFrame(e)}return{proceed:n(!0,r),start:n(!1,r),stop:n(!0,function(){window.cancelAnimationFrame(t),t=0})}}(function(){eq||tb.scrollBounds.constrain(tb.dragHandler.pointerDown()),tb.scrollBody.seek(tm).update();var e=tb.scrollBody.settle(tm);e&&!tb.dragHandler.pointerDown()&&(tb.animation.stop(),c.emit("settle")),e||c.emit("scroll"),eq&&(tb.scrollLooper.loop(tb.scrollBody.direction()),tb.slideLooper.loop()),tb.translate.to(tf),tb.animation.proceed()}),tf=C(td=ta[tl.get()]),tm=C(td),tp=function(e,t,n){var r,i=C(0),a=C(0),o=C(0),l=0,s=t,u=n;function c(){return l}function d(e){return s=e,m}function f(e){return u=e,m}var m={direction:c,seek:function(t){o.set(t).subtract(e);var n,r,c,d,f,p=(n=o.get(),0+((d=s)-0)*((n-0)/100));return l=y(o.get()),o.normalize().multiply(p).subtract(i),o.divide(u),a.add(o),m},settle:function(t){var n,r=(n=t.get()-e.get(),!(Math.round(100*n)/100));return r&&e.set(t),r},update:function(){i.add(a),e.add(i),a.multiply(0)},useBaseMass:function(){return f(n)},useBaseSpeed:function(){return d(t)},useMass:f,useSpeed:d};return m}(tf,eX,1),tg=function(e,t,n,r,i){var a=r.reachedAny,o=r.removeOffset,l=r.constrain;function s(e){return e.concat().sort(function(e,t){return S(e)-S(t)})[0]}function u(t,r){var i=[t,t+n,t-n];if(!e)return i[0];if(!r)return s(i);var a=i.filter(function(e){return y(e)===r});return s(a)}return{byDistance:function(n,r){var s,c,d=i.get()+n,f=(c=e?o(d):l(d),{index:t.map(function(e){return e-c}).map(function(e){return u(e,0)}).map(function(e,t){return{diff:e,index:t}}).sort(function(e,t){return S(e.diff)-S(t.diff)})[0].index,distance:c}),m=f.index,p=f.distance,g=!e&&a(d);if(!r||g)return{index:m,distance:n};var h=n+u(t[m]-p,0);return{index:m,distance:h}},byIndex:function(e,n){var r=u(t[e]-i.get(),n);return{index:e,distance:r}},shortcut:u}}(eq,ta,tr,to,tm),th=function(e,t,n,r,i,a){function o(r){var o=r.distance,l=r.index!==t.get();o&&(e.start(),i.add(o)),l&&(n.set(t.get()),t.set(r.index),a.emit("select"))}return{distance:function(e,t){o(r.byDistance(e,t))},index:function(e,n){var i=t.clone().set(e);o(r.byIndex(i.get(),n))}}}(tc,tl,ts,tg,tm,c),tv=function(e,t,n,r,i,a,o){var l=i.removeOffset,s=i.constrain,u=a?[0,t,-t]:[0],c=d(u,o);function d(t,i){var a,o,l=(o=i||0,n.map(function(e){return T(.5,e-.5).constrain(e*o)}));return(t||u).reduce(function(t,i){var a=r.map(function(t,r){return{start:t-n[r]+l[r]+i,end:t+e-l[r]+i,index:r}});return t.concat(a)},[])}return{check:function(e,t){var n=a?l(e):s(e);return(t||c).reduce(function(e,t){var r=t.index,i=t.start,a=t.end;return!(-1!==e.indexOf(r))&&i<n&&a>n?e.concat([r]):e},[])},findSlideBounds:d}}(e2,tr,e8,tt,to,eq,e_),tx=function(e,t,n,r,i,a,o,l,s,u,c,d,f,m,p,g){var h=e.cross,v=["INPUT","SELECT","TEXTAREA"],x={passive:!1},b=C(0),M=L(),w=L(),k=f.measure(20),E={mouse:300,touch:400},T={mouse:500,touch:600},j=p?5:16,A=0,B=0,D=!1,P=!1,N=!1,$=!1;function V(e){var t,o;if(!(($=!i.isTouchEvent(e))&&0!==e.button)&&(o=(t=e.target).nodeName||"",!(v.indexOf(o)>-1))){var l,u,c,f=(l=r.get(),S(l-(u=a.get()))>=2),m=$||!f;D=!0,i.pointerDown(e),b.set(r),r.set(a),s.useBaseMass().useSpeed(80),c=$?document:n,w.add(c,"touchmove",O,x).add(c,"touchend",I).add(c,"mousemove",O,x).add(c,"mouseup",I),A=i.readPoint(e),B=i.readPoint(e,h),d.emit("pointerDown"),m&&(N=!1)}}function O(e){if(!P&&!$){if(!e.cancelable)return I(e);var n,a,l,s,u=i.readPoint(e),c=i.readPoint(e,h),d=(a=A,S(u-a)),f=(s=B,S(c-s));if(!(P=d>f)&&!N)return I(e)}var m=i.pointerMove(e);!N&&m&&(N=!0),o.start(),r.add(t.apply(m)),e.preventDefault()}function I(e){var n,a,o,f,h,v,x,M=u.byDistance(0,!1).index!==c.get(),L=i.pointerUp(e)*(p?T:E)[$?"mouse":"touch"],C=(n=t.apply(L),f=(o=c.clone().add(-1*y(n))).get()===c.min||o.get()===c.max,h=u.byDistance(n,!p).distance,p||S(n)<k?h:!m&&f?.4*h:g&&M?.5*h:u.byIndex(o.get(),0).distance),A=function(e,t){if(0===e||0===t||S(e)<=S(t))return 0;var n,r,i=(n=S(e),r=S(t),S(n-r));return S(i/e)}(L,C),B=(v=r.get(),S(v-(x=b.get()))>=.5),V=M&&A>.75,O=S(L)<k;B&&!$&&(N=!0),P=!1,D=!1,w.removeAll(),s.useSpeed(O?9:V?10:j).useMass(V?1+2.5*A:1),l.distance(C,!p),$=!1,d.emit("pointerUp")}function W(e){N&&(e.stopPropagation(),e.preventDefault())}function H(){return!N}function z(){return D}return{addActivationEvents:function(){M.add(n,"dragstart",function(e){return e.preventDefault()},x).add(n,"touchmove",function(){},x).add(n,"touchend",function(){}).add(n,"touchstart",V).add(n,"mousedown",V).add(n,"touchcancel",I).add(n,"contextmenu",I).add(n,"click",W,!0)},clickAllowed:H,pointerDown:z,removeAllEvents:function(){M.removeAll(),w.removeAll()}}}(e1,e0,e,tm,function(e){var t,n;function r(e){return"u">typeof TouchEvent&&e instanceof TouchEvent}function i(e){return e.timeStamp}function a(t,n){var i=n||e.scroll,a="client".concat("x"===i?"X":"Y");return(r(t)?t.touches[0]:t)[a]}return{isTouchEvent:r,pointerDown:function(e){return t=e,n=e,a(e)},pointerMove:function(e){var r=a(e)-a(n),o=i(e)-i(t)>170;return n=e,o&&(t=e),r},pointerUp:function(e){if(!t||!n)return 0;var r=a(n)-a(t),o=i(e)-i(t),l=i(e)-i(n)>170,s=r/o;return o&&!l&&S(s)>.1?s:0},readPoint:a}}(e1),tf,tc,th,tp,tg,tl,c,e4,eq,eY,eG),b=(r=tb={containerRect:eZ,slideRects:eK,animation:tc,axis:e1,direction:e0,dragHandler:tx,eventStore:L(),percentOfView:e4,index:tl,indexPrevious:ts,limit:to,location:tf,options:P,scrollBody:tp,scrollBounds:function(e,t,n,r,i){var a=i.measure(10),o=i.measure(50),l=!1;function s(e){l=!e}return{constrain:function(i){if(!(l||!e.reachedAny(n.get())||!e.reachedAny(t.get()))){var s=S(e[e.reachedMin(t.get())?"min":"max"]-t.get()),u=n.get()-t.get();n.subtract(u*Math.min(s/o,.85)),!i&&S(u)<a&&(n.set(e.constrain(n.get())),r.useSpeed(10).useMass(3))}},toggleActive:s}}(to,tf,tm,tp,e4),scrollLooper:(eD=tf,eP=[tf,tm],eV=(e$=T(eN=to.min+.1,to.max+.1)).reachedMin,eO=e$.reachedMax,{loop:function(e){var t;if(1===e?eO(eD.get()):-1===e&&eV(eD.get())){var n=tr*(-1*e);eP.forEach(function(e){return e.add(n)})}}}),scrollProgress:(eW=to.max,eH=to.length,{get:function(e){return-((e-eW)/eH)}}),scrollSnaps:ta,scrollTarget:tg,scrollTo:th,slideLooper:function(e,t,n,r,i,a,o,l,s){var u,c,d=M(i),f=M(i).reverse(),m=(u=g(f,a[0]-1),h(u,"end")).concat((c=g(d,n-a[0]-1),h(c,"start")));function p(e,t){return e.reduce(function(e,t){return e-i[t]},t)}function g(e,t){return e.reduce(function(e,n){return p(e,t)>0?e.concat([n]):e},[])}function h(n,i){var a="start"===i,u=o.findSlideBounds([a?-r:r]);return n.map(function(n){var i=a?0:-r,o=a?r:0,c=u.filter(function(e){return e.index===n})[0][a?"end":"start"],d=C(-1),f=C(-1),m=j(e,t,s[n]);return{index:n,location:f,translate:m,target:function(){return d.set(l.get()>c?i:o)}}})}return{canLoop:function(){return m.every(function(e){var t=e.index;return .1>=p(d.filter(function(e){return e!==t}),n)})},clear:function(){m.forEach(function(e){return e.translate.clear()})},loop:function(){m.forEach(function(e){var t=e.target,n=e.translate,r=e.location,i=t();i.get()!==r.get()&&(0===i.get()?n.clear():n.to(i),r.set(i))})},loopPoints:m}}(e1,e0,e2,tr,e9,ta,tv,tf,D),slidesToScroll:e7,slidesInView:tv,slideIndexes:tu,target:tm,translate:j(e1,e0,B)}).axis.measureSize(e.getBoundingClientRect()),!g.active)return N();if(r.translate.to(r.location),x=n||x,i=u.init(x,Q),g.loop){if(!r.slideLooper.canLoop()){N(),E({loop:!1},n),p=s.merge(p,{loop:!0});return}r.slideLooper.loop()}g.draggable&&a.offsetParent&&o.length&&r.dragHandler.addActivationEvents()}}function P(e,t){var n=O();N(),E(s.merge({startIndex:n},e),t),c.emit("reInit")}function N(){r.dragHandler.removeAllEvents(),r.animation.stop(),r.eventStore.removeAll(),r.translate.clear(),r.slideLooper.clear(),u.destroy()}function $(e){var t=r[e?"target":"location"].get(),n=g.loop?"removeOffset":"constrain";return r.slidesInView.check(r.limit[n](t))}function V(e,t,n){!g.active||m||(r.scrollBody.useBaseMass().useSpeed(t?100:g.speed),r.scrollTo.index(e,n||0))}function O(){return r.index.get()}function I(){return i}function W(){return r}function H(){return e}function z(){return a}function F(){return o}var Q={canScrollNext:function(){return r.index.clone().add(1).get()!==O()},canScrollPrev:function(){return r.index.clone().add(-1).get()!==O()},clickAllowed:function(){return r.dragHandler.clickAllowed()},containerNode:z,internalEngine:W,destroy:function(){m||(m=!0,l.removeAll(),N(),c.emit("destroy"))},off:f,on:d,plugins:I,previousScrollSnap:function(){return r.indexPrevious.get()},reInit:P,rootNode:H,scrollNext:function(e){V(r.index.clone().add(1).get(),!0===e,-1)},scrollPrev:function(e){V(r.index.clone().add(-1).get(),!0===e,1)},scrollProgress:function(){return r.scrollProgress.get(r.location.get())},scrollSnapList:function(){return r.scrollSnaps.map(r.scrollProgress.get)},scrollTo:V,selectedScrollSnap:O,slideNodes:F,slidesInView:$,slidesNotInView:function(e){var t=$(e);return r.slideIndexes.filter(function(e){return -1===t.indexOf(e)})}};return E(t,n),l.add(window,"resize",function(){var t=s.atMedia(p),n=!s.areEqual(t,g),i=b!==r.axis.measureSize(e.getBoundingClientRect()),a=u.haveChanged();(i||n||a)&&P(),c.emit("resize")}),setTimeout(function(){return c.emit("init")},0),Q}function P(){return(P=Object.assign||function(e){for(var t=1;t<arguments.length;t++){var n=arguments[t];for(var r in n)Object.prototype.hasOwnProperty.call(n,r)&&(e[r]=n[r])}return e}).apply(this,arguments)}function N(e,t){if(e.length!==t.length)throw Error("vectors must be same length");return e.map(function(e,n){return e+t[n]})}function $(e){return Math.max.apply(Math,e.map(Math.abs))}function V(e){return Object.freeze(e),Object.values(e).forEach(function(e){null===e||"object"!=typeof e||Object.isFrozen(e)||V(e)}),e}D.globalOptions=void 0,D.optionsHandler=B;var O=[1,18,"u">typeof window&&window.innerHeight||800],I=[-1,-1,-1],W=V({preventWheelAction:!0,reverseSign:[!0,!0,!1]});function H(){return{isStarted:!1,isStartPublished:!1,isMomentum:!1,startTime:0,lastAbsDelta:1/0,axisMovement:[0,0,0],axisVelocity:[0,0,0],accelerationFactors:[],scrollPoints:[],scrollPointsToMerge:[],willEndTimeout:400}}var z={active:!0,breakpoints:{},wheelDraggingClass:"is-wheel-dragging",forceWheelAxis:void 0,target:void 0};function F(e){var t,n=D.optionsHandler(),r=n.merge(z,F.globalOptions),i=function(){},a={name:"wheelGestures",options:n.merge(r,e),init:function(e){t=n.atMedia(a.options);var r,o,l,s,u,c,d,f,m,p,g,h,v,x,b,S,y,M,w,k,E,T,L,C,j,A,B,D,z,F,Q,R,_,q,X,Y,U,G=e.internalEngine(),J=null!=(X=t.target)?X:e.containerNode().parentNode,Z=null!=(Y=t.forceWheelAxis)?Y:G.options.axis,K=(r={preventWheelAction:Z,reverseSign:[!0,!0,!1]},p=(m=function(){var e={};function t(t,n){e[t]=(e[t]||[]).filter(function(e){return e!==n})}return V({on:function(n,r){return e[n]=(e[n]||[]).concat(r),function(){return t(n,r)}},off:t,dispatch:function(t,n){t in e&&e[t].forEach(function(e){return e(n)})}})}()).on,g=m.off,h=m.dispatch,v=W,x=H(),b=!1,S=function(e){Array.isArray(e)?e.forEach(function(e){return k(e)}):k(e)},y=function(e){return void 0===e&&(e={}),Object.values(e).some(function(e){return null==e})?v:v=V(P({},W,v,e))},M=function(e){var t=P({event:d,isStart:!1,isEnding:!1,isMomentumCancel:!1,isMomentum:x.isMomentum,axisDelta:[0,0,0],axisVelocity:x.axisVelocity,axisMovement:x.axisMovement,get axisMovementProjection(){return N(t.axisMovement,t.axisVelocity.map(function(e){var t,n;return void 0===n&&(n=.996),e*n/(1-n)}))}},e);h("wheel",P({},t,{previous:f})),f=t},w=function(e,t){var n=v.preventWheelAction,r=t[0],i=t[1],a=t[2];if("boolean"==typeof n)return n;switch(n){case"x":return Math.abs(r)>=e;case"y":return Math.abs(i)>=e;case"z":return Math.abs(a)>=e;default:return!1}},k=function(e){var t,n,r,i,a,o=(a=function(e,t){if(!t)return e;var n=!0===t?I:t.map(function(e){return e?-1:1});return P({},e,{axisDelta:e.axisDelta.map(function(e,t){return e*n[t]})})}((n=e.deltaX*O[e.deltaMode],r=e.deltaY*O[e.deltaMode],i=(e.deltaZ||0)*O[e.deltaMode],{timeStamp:e.timeStamp,axisDelta:[n,r,i]}),v.reverseSign),P({},a,{axisDelta:a.axisDelta.map(function(e){var t,n;return Math.min(Math.max(-700,e),700)})})),l=o.axisDelta,s=o.timeStamp,u=$(l);if(e.preventDefault&&w(u,l)&&e.preventDefault(),x.isStarted?x.isMomentum&&u>Math.max(2,2*x.lastAbsDelta)&&(F(!0),D()):D(),0===u&&Object.is&&Object.is(e.deltaX,-0)){b=!0;return}d=e,x.axisMovement=N(x.axisMovement,l),x.lastAbsDelta=u,x.scrollPointsToMerge.push({axisDelta:l,timeStamp:s}),E(),M({axisDelta:l,isStart:!x.isStartPublished}),x.isStartPublished=!0,z()},E=function(){var e;2===x.scrollPointsToMerge.length?(x.scrollPoints.unshift({axisDeltaSum:x.scrollPointsToMerge.map(function(e){return e.axisDelta}).reduce(N),timeStamp:(e=x.scrollPointsToMerge.map(function(e){return e.timeStamp})).reduce(function(e,t){return e+t})/e.length}),L(),x.scrollPointsToMerge.length=0,x.scrollPoints.length=1,x.isMomentum||A()):x.isStartPublished||T()},T=function(){var e;x.axisVelocity=(e=x.scrollPointsToMerge)[e.length-1].axisDelta.map(function(e){return e/x.willEndTimeout})},L=function(){var e=x.scrollPoints,t=e[0],n=e[1];if(!(!n||!t)){var r=t.timeStamp-n.timeStamp;if(r<=0)return;var i=t.axisDeltaSum.map(function(e){return e/r}),a=i.map(function(e,t){return e/(x.axisVelocity[t]||1)});x.axisVelocity=i,x.accelerationFactors.push(a),C(r)}},C=function(e){var t=12*Math.ceil(e/10);x.isMomentum||(t=Math.max(100,2*t)),x.willEndTimeout=Math.min(1e3,Math.round(t))},j=function(e){return 0===e||e<=.96&&e>=.6},A=function(){if(x.accelerationFactors.length>=5){if(b&&(b=!1,$(x.axisVelocity)>=.2)){B();return}var e=x.accelerationFactors.slice(-5);e.every(function(e){var t=!!e.reduce(function(e,t){return e&&e<1&&e===t?1:0}),n=e.filter(j).length===e.length;return t||n})&&B(),x.accelerationFactors=e}},B=function(){x.isMomentum=!0},D=function(){(x=H()).isStarted=!0,x.startTime=Date.now(),f=void 0,b=!1},z=function(){clearTimeout(o),o=setTimeout(F,x.willEndTimeout)},F=function(e){void 0===e&&(e=!1),x.isStarted&&(x.isMomentum&&e?M({isEnding:!0,isMomentumCancel:!0}):M({isEnding:!0}),x.isMomentum=!1,x.isStarted=!1)},s=[],u=function(e){e.removeEventListener("wheel",S),s=s.filter(function(t){return t!==e})},c=function(){s.forEach(u)},R=(Q=V({observe:function(e){return e.addEventListener("wheel",S,{passive:!1}),s.push(e),function(){return u(e)}},unobserve:u,disconnect:c})).observe,_=Q.unobserve,q=Q.disconnect,y(r),V({on:p,off:g,observe:R,unobserve:_,disconnect:q,feedWheel:S,updateOptions:y})),ee=K.observe(J),et=K.on("wheel",function(e){var n,r=e.axisDelta,a=r[0],o=r[1],l=e.isMomentum&&e.previous&&!e.previous.isMomentum,s=e.isEnding&&!e.isMomentum||l;!(Math.abs("x"===Z?a:o)>Math.abs("x"===Z?o:a))||en||e.isMomentum||function(e){try{U=new MouseEvent("mousedown",e.event),eo(U)}catch{return i()}en=!0,document.documentElement.addEventListener("mousemove",ei,!0),document.documentElement.addEventListener("mouseup",ei,!0),document.documentElement.addEventListener("mousedown",ei,!0),t.wheelDraggingClass&&J.classList.add(t.wheelDraggingClass)}(e),en&&(s?(en=!1,eo(ea("mouseup",e)),er(),t.wheelDraggingClass&&J.classList.remove(t.wheelDraggingClass)):eo(ea("mousemove",e)))}),en=!1;function er(){document.documentElement.removeEventListener("mousemove",ei,!0),document.documentElement.removeEventListener("mouseup",ei,!0),document.documentElement.removeEventListener("mousedown",ei,!0)}function ei(e){en&&e.isTrusted&&e.stopImmediatePropagation()}function ea(e,t){var n,r;if(Z===G.options.axis){var i=t.axisMovement;n=i[0],r=i[1]}else{var a=t.axisMovement;r=a[0],n=a[1]}return new MouseEvent(e,{clientX:U.clientX+n,clientY:U.clientY+r,screenX:U.screenX+n,screenY:U.screenY+r,movementX:n,movementY:r,button:0,bubbles:!0,cancelable:!0,composed:!0})}function eo(t){e.containerNode().dispatchEvent(t)}i=function(){ee(),et(),er()}},destroy:function(){return i()}};return a}F.globalOptions=void 0;let Q=g.default.div`
  user-select: none;

  &.sliderMobile {
    display: none;
  }

  &.sliderDesktop,
  &.sliderBigTitle {
    display: none;

    @media ${({theme:e})=>e.mediaQueries.tabletL} {
      display: flex;
    }
  }

  &.sliderBigTitle {
    padding-right: 0;
    justify-content: center;
    margin-top: 20px;
    width: 95%;
  }

  div {
    display: flex;
    justify-content: center;
    align-items: center;
  }
`,R=d.css`
  cursor: initial;

  path {
    fill: ${({theme:e})=>e.palette.graya40};
  }
`,_=d.css`
  width: 28px;
  height: 28px;
  flex-grow: 0;
  flex-shrink: 0;
  cursor: pointer;
  margin-right: 20px;
  border-radius: 50%;

  &:not(.disabled):hover {
    background-color: ${({theme:e})=>e.palette.graya20};
  }

  &.disabled {
    ${R}
  }
`,q=g.default(u.SvgArrowBackIosBlack)`
  ${_}
  padding-right: 4px;
`,X=g.default(c.SvgArrowForwardIosBlack)`
  ${_}
  padding-left: 4px;
`,Y={SliderControls:Q,SliderBackButton:q,SliderNextButton:X},U=({disabledControls:e,sliderVariant:t,onNext:n,onPrev:i})=>{let{beginning:a,end:o}=e;return r.jsxs(Y.SliderControls,{className:t,children:[r.jsx(Y.SliderBackButton,{className:a?void 0:"disabled",disabled:!a,onClick:i,role:"button"}),r.jsx(Y.SliderNextButton,{className:o?void 0:"disabled",disabled:!o,onClick:n,role:"button"})]})};var G,J,Z,K=((G=K||{}).SliderMobile="sliderMobile",G.SliderDesktop="sliderDesktop",G.SliderBigTitle="sliderBigTitle",G.SliderFullSpacing="sliderFullSpacing",G.SliderWithCustomHeader="sliderWithCustomHeader",G),ee=((J=ee||{}).LinkRight="linkRight",J.LinkLeft="linkLeft",J),et=((Z=et||{}).Big="Big",Z.Small="Small",Z);let en=g.default.div`
  &.sliderMobile {
    padding: 20px 0;
  }

  &.sliderDesktop {
    padding: 20px 0;
  }

  &.sliderBigTitle {
    padding: 20px 0;

    @media ${({theme:e})=>e.mediaQueries.tabletL} {
      padding: 54px 0 54px 40px;
      display: flex;
      align-items: center;
    }
  }

  &.sliderFullSpacing {
    padding: 0;
  }
`,er=g.default.div`
  display: flex;
  justify-content: space-between;
  align-items: center;

  &.sliderMobile {
    margin: 0px 0 20px 0;
  }

  &.sliderDesktop,
  &.sliderBigTitle {
    margin: 0px 0 30px 0;

    @media ${({theme:e})=>e.mediaQueries.tabletL} {
      margin: 0 0 20px 0;
    }
  }
`,ei=g.default.div`
  width: 100%;
  @media ${({theme:e})=>e.mediaQueries.tabletL} {
    margin-right: 16px;
  }
`,ea=g.default.div`
  width: 100%;
  padding-right: 16px;
  padding-left: 20px;

  display: flex;
  justify-content: space-between;
  align-items: center;

  @media ${({theme:e})=>e.mediaQueries.tabletL} {
    padding-left: 40px;
  }

  & > a > span.quantity,
  & > span > span.quantity {
    margin-left: 10px;
  }

  & > a > h1,
  & > a > h2,
  & > a > h3,
  & > a > h4,
  & > a > h5,
  & > a > h6,
  & > a > p {
    display: contents;
  }
`,eo=g.default.span`
  &.sliderMobile {
    float: right;
    margin-top: 6px;

    &.linkLeft,
    &.linkRight {
      margin-right: 0px;
      margin-left: 0px;
      float: right;
    }
  }

  &.sliderDesktop {
    float: right;
    margin-top: 6px;

    @media ${({theme:e})=>e.mediaQueries.tabletL} {
      margin-top: 8px;
    }
  }

  &.sliderBigTitle {
    float: right;
    margin-top: 6px;

    @media ${({theme:e})=>e.mediaQueries.tabletL} {
      text-align: center;
      margin-top: 15px;
      margin-right: 40px;
    }
  }

  &.sliderBigTitle,
  &.sliderDesktop {
    &.linkLeft,
    &.linkRight {
      margin-right: 0px;
      margin-left: 0px;
      float: right;
    }

    @media ${({theme:e})=>e.mediaQueries.tabletL} {
      &.linkRight {
        margin-right: 40px;
        float: right;
      }

      &.linkLeft {
        margin-left: 40px;
        float: none;
      }
    }
  }
`,el=g.default.div`
  float: left;
  display: none;
  flex-direction: column;
  justify-content: center;

  @media ${({theme:e})=>e.mediaQueries.tabletL} {
    display: flex;
  }
`,es=g.default.div`
  display: block;

  @media ${({theme:e})=>e.mediaQueries.tabletL} {
    display: none;
  }
`,eu=g.default.img`
  object-fit: cover;
  margin-right: 10px;
  border-radius: 50%;
  vertical-align: middle;
  &.sliderMobile {
    height: 24px;
    width: 24px;
  }

  &.sliderDesktop {
    height: 24px;
    width: 24px;

    @media ${({theme:e})=>e.mediaQueries.tabletL} {
      height: 34px;
      width: 34px;
    }
  }
`,ec=g.default.div`
  display: flex;
  margin-bottom: 20px;
  justify-content: space-between;

  .sliderWithCustomHeader {
    display: none;
    margin-left: 12px;

    svg:not(:last-child) {
      margin-right: 12px;
    }

    svg:last-child {
      margin-right: 0;
    }

    @media ${({theme:e})=>e.mediaQueries.tablet} {
      display: flex;
      align-items: center;
    }
  }
`,ed=g.default(a.Typography)`
  width: 343px;
  text-align: center;
  margin-right: 40px;
`,ef=g.default.div`
  width: 100%;
  overflow-y: hidden;
  overflow-x: auto;

  ::-webkit-scrollbar {
    width: 0;
    height: 0;
    background: transparent;
  }
`,em=g.default.div`
  width: 100%;
  display: flex;

  .embla__slide {
    margin-right: ${({gap:e})=>`${e}px`};

    @media ${({theme:e})=>e.mediaQueries.tablet} {
      margin-right: ${({gap:e})=>`${2*e}px`};
    }
  }

  .start-item {
    margin-right: 20px;

    @media ${({theme:e})=>e.mediaQueries.tablet} {
      margin-right: 40px;
    }
  }

  .last-item {
    width: 6px;

    @media ${({theme:e})=>e.mediaQueries.tablet} {
      width: 16px;
    }
  }
`,ep=g.default.a`
  background-color: ${({theme:e})=>e.palette.secondary3100};
  color: ${({theme:e})=>e.palette.white};
  border-radius: 8px;
  display: flex !important;
  justify-content: center;
  align-items: center;
  width: 142px !important;
  height: 116px !important;
  text-decoration: none;

  @media ${({theme:e})=>e.mediaQueries.tabletL} {
    ${({variant:e})=>"Big"===e?`
          width: 200px !important;
          height: 164px !important;
        `:null}
  }
`,eg={BigTitle:ed,SeeAllLink:eo,ShowMore:ep,SliderWithCustomHeaderStyle:ec,SliderBigTitleWrapper:el,SliderBigTitleMobileWrapper:es,SliderContainer:en,SliderHeader:er,SliderName:ea,Carousel:em,CarouselContainer:ef,TitleImage:eu,CustomHeaderWrapper:ei},eh=F({forceWheelAxis:"x"}),ev={dragFree:!0,containScroll:"trimSnaps",slidesToScroll:3,align:"start"},ex=({children:e,activePrev:t=!0,activeNext:n=!0,title:l,withTitle:u=!0,withControls:c=!0,titleTagAs:d="span",gap:f=5,titleImage:g,titleLinkUrl:h,linkText:v,linkUrl:x,customHeader:b,modal:S,setModal:y,withModal:M,sliderVariant:w=K.SliderMobile,keyName:k,onClickAction:E,showMoreLink:T,showMoreText:L,showMoreVariant:C,totalItems:j,isLoading:A,customLoading:B,showCustomShowMore:D=!1,customShowMore:P,showMoreLinkVariants:N=ee.LinkRight,titleVariant:$=o.Variants.L220,dataQaPrefix:V="",className:O="",titleImageAlt:I})=>{let[W,H]=m.default(ev,[eh]),[z,F]=s.useState(t),[Q,R]=s.useState(n),_=`${V}${V?"-":""}slider`,q=`${V}${V?"-":""}title-slider`,X=p.default.Children.toArray(e).concat((()=>{let e=[];return A&&B&&e.push(r.jsx("div",{children:B},"customLoading")),D&&P&&e.push(r.jsx("div",{children:P},"customShowMore")),T&&L&&e.push(r.jsx(eg.ShowMore,{href:T,variant:C,children:r.jsx(a.Typography,{variant:o.Variants.Base216,color:o.Colors.White,children:L})},"ShowMore")),e})()).map(e=>p.default.isValidElement(e)?r.jsx("div",{className:"embla__slide",children:e}):e),Y=p.default.Children.map(X,e=>{if(!p.default.isValidElement(e))return e;let t=(t,n)=>{null!=H&&H.clickAllowed()&&e.props.onClick&&e.props.onClick(t,n)};return p.default.cloneElement(e,{onClick:t})}),G=()=>{H&&(F(t&&H.canScrollPrev()),R(n&&H.canScrollNext()))};s.useEffect(()=>{if(H)return G(),H.on("select",G),H.on("resize",G),()=>{H.off("select",G),H.off("resize",G)}},[H]),s.useEffect(()=>{null==H||H.reInit(),G()},[null==Y?void 0:Y.length]);let J=()=>c?r.jsx(U,{disabledControls:{beginning:z,end:Q},sliderVariant:w,onNext:null==H?void 0:H.scrollNext,onPrev:null==H?void 0:H.scrollPrev}):null,Z=()=>r.jsx(eg.SeeAllLink,{className:`${N} ${w}`,onClick:M?y:E,children:r.jsx(i.Link,{linkVariant:i.LinkVariants.Primary,href:x,preventRedirect:M,children:v})}),et=()=>{let e=r.jsxs(a.Typography,{variant:$,tagAs:d,"data-qa":q,children:[g&&r.jsx(eg.TitleImage,{className:w,src:g,alt:I}),l||"",j&&r.jsxs(a.Typography,{variant:o.Variants.L120,color:o.Colors.Graya80,className:"quantity",children:["(",j,")"]})]});return h?r.jsx(i.Link,{linkVariant:i.LinkVariants.Primary,href:h,preventRedirect:M,children:e}):e},en=()=>r.jsxs(eg.SliderHeader,{className:w,children:[r.jsxs(eg.SliderName,{children:[et(),v&&Z()]}),J()]});return r.jsxs(eg.SliderContainer,{className:`${w} ${O}`,"data-qa":_,children:[r.jsxs("div",{"data-qa":"slider-header",children:[u&&![K.SliderBigTitle,K.SliderWithCustomHeader].includes(w)&&en(),u&&w===K.SliderBigTitle&&r.jsxs(r.Fragment,{children:[r.jsxs(eg.SliderBigTitleWrapper,{children:[r.jsx(eg.BigTitle,{variant:o.Variants.XL232,tagAs:d,children:l||""}),v&&Z(),J()]}),r.jsx(eg.SliderBigTitleMobileWrapper,{children:en()})]}),w===K.SliderWithCustomHeader&&r.jsxs(eg.SliderWithCustomHeaderStyle,{children:[r.jsx(eg.CustomHeaderWrapper,{children:b}),J()]})]}),r.jsx(eg.CarouselContainer,{ref:W,children:r.jsx(eg.Carousel,{className:"Carousel__items_container","data-qa":"carousel-list","data-testid":"carousel-list",gap:f,children:[r.jsx("div",{className:"start-item"},"start-item"),...Y,r.jsx("div",{className:"last-item"},"last-item")]})}),M&&S]},k)};t.ShowMoreLinkVariants=ee,t.ShowMoreVariants=et,t.SliderVariants=K,t.default=ex}}]);
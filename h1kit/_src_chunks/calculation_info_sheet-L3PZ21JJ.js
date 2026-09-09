import{o as e,r as t}from"./rolldown-runtime-DAXXjFlN.js";import{Fw as n,Fy as r,Iw as i,Py as a,Qy as o,Rw as s,Wl as c,Xd as l,Yf as u,Za as d,Zd as f,df as p,dp as m,ff as h,hf as g,iv as _,jw as v,mf as y,nb as b,nv as x,ov as S,pf as C,rv as w,sv as T,tb as E}from"./vendor-_WdvpBLr.js";import{Sh as D}from"./app-5pKgUmmm.js";import{t as ee}from"./addYears-CM_qCPMk.js";var O=`data:image/svg+xml,%3csvg%20xmlns='http://www.w3.org/2000/svg'%20viewBox='0%200%2024%2024'%20width='24px'%20height='24px'%3e%3cpath%20d='M%205%203%20C%203.9069372%203%203%203.9069372%203%205%20L%203%2019%20C%203%2020.093063%203.9069372%2021%205%2021%20L%2019%2021%20C%2020.093063%2021%2021%2020.093063%2021%2019%20L%2021%2012%20L%2019%2012%20L%2019%2019%20L%205%2019%20L%205%205%20L%2012%205%20L%2012%203%20L%205%203%20z%20M%2014%203%20L%2014%205%20L%2017.585938%205%20L%208.2929688%2014.292969%20L%209.7070312%2015.707031%20L%2019%206.4140625%20L%2019%2010%20L%2021%2010%20L%2021%203%20L%2014%203%20z'/%3e%3c/svg%3e`;function te(e,t){return a(2,arguments),ee(e,-r(t))}var k=e(c()),A=d(),j=e(v()),M={value:`in`,label:`equals`},N={value:`not_in`,label:`not equals`},P={value:`any`,label:`any of`},F={value:`not_any`,label:`none of`},I={value:`eq`,label:`equals`},ne={value:`not_eq`,label:`not equals`},re={value:`lt`,label:`less than`},ie={value:`lteq`,label:`less than or equals`},L={value:`gt`,label:`greater than`},ae={value:`gteq`,label:`greater than or equals`},oe=`NULL`,se=`(not set)`,R={string:[M,N],number:[I,ne,re,ie,L,ae],numbers:[P,F],boolean:[M,N]},ce={[M.value]:M.label,[N.value]:N.label,[I.value]:I.label,[ne.value]:ne.label,[re.value]:re.label,[ie.value]:ie.label,[L.value]:L.label,[ae.value]:ae.label,[P.value]:P.label,[F.value]:F.label},le=[{value:!0,label:`Yes`},{value:!1,label:`No`}],ue=[M.value,N.value,P.value,F.value],de=(e,t,n)=>{let r=n[e];if(!r)return R.string;let i=r.columns[t];return(0,j.default)(((r.meta||{})[t]||{}).values?.[0])&&i!==`numbers`?R.string:R[i]},fe=(e,t)=>{if(!e?.startsWith(`bounty_`))return e;let n=e.split(`_`);return n.length!==3||t===void 0?e:`${n[0]}_${n[1]}_${t}`},pe=(e,t)=>`${e}-${t}`,me=(e,t,n,r)=>{let i=new A.CsvBuilder(e);i.addRow(t),n.forEach(e=>{let t=r.map(t=>String(e[t]??``));i.addRow(t)}),i.exportFile()},he=()=>{D.track(`dashboard explore csv downloaded`)},ge=(e,t,n,r,i=null)=>({sort:a})=>{if(!(0,k.default)(a)){let[o]=Object.entries(a)[0],s=e===o&&t===`ASC`?`DESC`:`ASC`;r(s),n(o),i&&i(o===`reporter`?{reporter:{username:{_direction:s}}}:{})}},_e=(e,t,n,r)=>({sort:i})=>{if((0,k.default)(i))return;let a={title:`report_id`,reporter:`reporter_username`,collaborators:`collaborator_count`},o=Object.entries(i)[0][0],s=o in a?a[o]:o;r(e===s&&t===`asc`?`desc`:`asc`),n(s)},ve=(e,t)=>{let n=(t[e]?.meta??{}).sfdc_account_regions??{values:[]};return new Set((n.values??[]).map(e=>(0,j.default)(e)?e[0]:e))},ye=(e,t,n)=>{let r=t.value||[],i=t.compareFunction,a=ve(e,n),o=r.filter(e=>a.has(e)),s=r.filter(e=>!a.has(e)&&e!==`NULL`);if(o.length===0&&s.length===0)return[{left:{ref:`${e}__sfdc_account_regions`},function:i,right:{strings:[]}}];if(o.length>0&&s.length===0)return[{left:{ref:`${e}__sfdc_account_regions`},function:i,right:{strings:o}}];if(o.length===0&&s.length>0)return[{left:{ref:`${e}__sfdc_billing_country`},function:i,right:{strings:s}}];let c={left:{ref:`${e}__sfdc_account_regions`},function:i,right:{strings:o}},l={left:{ref:`${e}__sfdc_billing_country`},function:i,right:{strings:s}};return i===`not_in`?[c,l]:(c.or=[l],[c])},be=(e,t,n)=>{let r=e.split(`__`)[0],i=e.split(`__`)[1];if(i===`sfdc_country_region`)return ye(r,t,n);let a=n[r];if(!a)return[];let o=a.columns[i]||`string`,s=ue.includes(t.compareFunction),c={left:{ref:e},function:t.compareFunction,right:{[`${o}${s?`s`:``}`]:s&&[`string`].includes(o)?t.value.filter(e=>e!==oe):t.value}};return[`string`].includes(o)&&t.value.includes(`NULL`)&&(c.or={left:{ref:e},function:t.compareFunction===N.value?ne.value:I.value,right:{nil:!0}}),[c]},z=e(s()),xe=`data:image/svg+xml,%3csvg%20xmlns='http://www.w3.org/2000/svg'%20width='48'%20height='48'%20viewBox='0%20-960%20960%20960'%3e%3cpath%20d='M480-356q-6%200-11-2t-10-7L261-563q-9-9-8.5-21.5T262-606q9-9%2021.5-9t21.5%209l175%20176%20176-176q9-9%2021-8.5t21%209.5q9%209%209%2021.5t-9%2021.5L501-365q-5%205-10%207t-11%202Z'/%3e%3c/svg%3e`,B;(function(e){e.Root=`root`,e.Chevron=`chevron`,e.Day=`day`,e.DayButton=`day_button`,e.CaptionLabel=`caption_label`,e.Dropdowns=`dropdowns`,e.Dropdown=`dropdown`,e.DropdownRoot=`dropdown_root`,e.Footer=`footer`,e.MonthGrid=`month_grid`,e.MonthCaption=`month_caption`,e.MonthsDropdown=`months_dropdown`,e.Month=`month`,e.Months=`months`,e.Nav=`nav`,e.NextMonthButton=`button_next`,e.PreviousMonthButton=`button_previous`,e.Week=`week`,e.Weeks=`weeks`,e.Weekday=`weekday`,e.Weekdays=`weekdays`,e.WeekNumber=`week_number`,e.WeekNumberHeader=`week_number_header`,e.YearsDropdown=`years_dropdown`})(B||={});var V;(function(e){e.disabled=`disabled`,e.hidden=`hidden`,e.outside=`outside`,e.focused=`focused`,e.today=`today`})(V||={});var H;(function(e){e.range_end=`range_end`,e.range_middle=`range_middle`,e.range_start=`range_start`,e.selected=`selected`})(H||={});var Se=365.2425,Ce=6048e5,we=864e5,Te=3600*24;Te*7,Te*Se/12*3;var Ee=Symbol.for(`constructDateFrom`);function U(e,t){return typeof e==`function`?e(t):e&&typeof e==`object`&&Ee in e?e[Ee](t):e instanceof Date?new e.constructor(t):new Date(t)}function W(e,t){return U(t||e,e)}function De(e,t,n){let r=W(e,n?.in);return isNaN(t)?U(n?.in||e,NaN):(t&&r.setDate(r.getDate()+t),r)}function Oe(e,t,n){let r=W(e,n?.in);if(isNaN(t))return U(n?.in||e,NaN);if(!t)return r;let i=r.getDate(),a=U(n?.in||e,r.getTime());return a.setMonth(r.getMonth()+t+1,0),i>=a.getDate()?a:(r.setFullYear(a.getFullYear(),a.getMonth(),i),r)}var ke={};function Ae(){return ke}function je(e,t){let n=Ae(),r=t?.weekStartsOn??t?.locale?.options?.weekStartsOn??n.weekStartsOn??n.locale?.options?.weekStartsOn??0,i=W(e,t?.in),a=i.getDay(),o=(a<r?7:0)+a-r;return i.setDate(i.getDate()-o),i.setHours(0,0,0,0),i}function Me(e,t){return je(e,{...t,weekStartsOn:1})}function Ne(e,t){let n=W(e,t?.in),r=n.getFullYear(),i=U(n,0);i.setFullYear(r+1,0,4),i.setHours(0,0,0,0);let a=Me(i),o=U(n,0);o.setFullYear(r,0,4),o.setHours(0,0,0,0);let s=Me(o);return n.getTime()>=a.getTime()?r+1:n.getTime()>=s.getTime()?r:r-1}function Pe(e){let t=W(e),n=new Date(Date.UTC(t.getFullYear(),t.getMonth(),t.getDate(),t.getHours(),t.getMinutes(),t.getSeconds(),t.getMilliseconds()));return n.setUTCFullYear(t.getFullYear()),e-+n}function Fe(e,...t){let n=U.bind(null,e||t.find(e=>typeof e==`object`));return t.map(n)}function Ie(e,t){let n=W(e,t?.in);return n.setHours(0,0,0,0),n}function Le(e,t,n){let[r,i]=Fe(n?.in,e,t),a=Ie(r),o=Ie(i),s=+a-Pe(a),c=+o-Pe(o);return Math.round((s-c)/we)}function Re(e,t){let n=Ne(e,t),r=U(t?.in||e,0);return r.setFullYear(n,0,4),r.setHours(0,0,0,0),Me(r)}function ze(e,t,n){return De(e,t*7,n)}function Be(e,t,n){return Oe(e,t*12,n)}function Ve(e,t){let n,r=t?.in;return e.forEach(e=>{!r&&typeof e==`object`&&(r=U.bind(null,e));let t=W(e,r);(!n||n<t||isNaN(+t))&&(n=t)}),U(r,n||NaN)}function He(e,t){let n,r=t?.in;return e.forEach(e=>{!r&&typeof e==`object`&&(r=U.bind(null,e));let t=W(e,r);(!n||n>t||isNaN(+t))&&(n=t)}),U(r,n||NaN)}function Ue(e,t,n){let[r,i]=Fe(n?.in,e,t);return+Ie(r)==+Ie(i)}function We(e){return e instanceof Date||typeof e==`object`&&Object.prototype.toString.call(e)===`[object Date]`}function Ge(e){return!(!We(e)&&typeof e!=`number`||isNaN(+W(e)))}function Ke(e,t,n){let[r,i]=Fe(n?.in,e,t),a=r.getFullYear()-i.getFullYear(),o=r.getMonth()-i.getMonth();return a*12+o}function qe(e,t){let n=W(e,t?.in),r=n.getMonth();return n.setFullYear(n.getFullYear(),r+1,0),n.setHours(23,59,59,999),n}function Je(e,t){let n=W(e,t?.in);return n.setDate(1),n.setHours(0,0,0,0),n}function Ye(e,t){let n=W(e,t?.in),r=n.getFullYear();return n.setFullYear(r+1,0,0),n.setHours(23,59,59,999),n}function Xe(e,t){let n=W(e,t?.in);return n.setFullYear(n.getFullYear(),0,1),n.setHours(0,0,0,0),n}function Ze(e,t){let n=Ae(),r=t?.weekStartsOn??t?.locale?.options?.weekStartsOn??n.weekStartsOn??n.locale?.options?.weekStartsOn??0,i=W(e,t?.in),a=i.getDay(),o=(a<r?-7:0)+6-(a-r);return i.setDate(i.getDate()+o),i.setHours(23,59,59,999),i}function Qe(e,t){return Ze(e,{...t,weekStartsOn:1})}var $e={lessThanXSeconds:{one:`less than a second`,other:`less than {{count}} seconds`},xSeconds:{one:`1 second`,other:`{{count}} seconds`},halfAMinute:`half a minute`,lessThanXMinutes:{one:`less than a minute`,other:`less than {{count}} minutes`},xMinutes:{one:`1 minute`,other:`{{count}} minutes`},aboutXHours:{one:`about 1 hour`,other:`about {{count}} hours`},xHours:{one:`1 hour`,other:`{{count}} hours`},xDays:{one:`1 day`,other:`{{count}} days`},aboutXWeeks:{one:`about 1 week`,other:`about {{count}} weeks`},xWeeks:{one:`1 week`,other:`{{count}} weeks`},aboutXMonths:{one:`about 1 month`,other:`about {{count}} months`},xMonths:{one:`1 month`,other:`{{count}} months`},aboutXYears:{one:`about 1 year`,other:`about {{count}} years`},xYears:{one:`1 year`,other:`{{count}} years`},overXYears:{one:`over 1 year`,other:`over {{count}} years`},almostXYears:{one:`almost 1 year`,other:`almost {{count}} years`}},et=(e,t,n)=>{let r,i=$e[e];return r=typeof i==`string`?i:t===1?i.one:i.other.replace(`{{count}}`,t.toString()),n?.addSuffix?n.comparison&&n.comparison>0?`in `+r:r+` ago`:r};function tt(e){return(t={})=>{let n=t.width?String(t.width):e.defaultWidth;return e.formats[n]||e.formats[e.defaultWidth]}}var nt={date:tt({formats:{full:`EEEE, MMMM do, y`,long:`MMMM do, y`,medium:`MMM d, y`,short:`MM/dd/yyyy`},defaultWidth:`full`}),time:tt({formats:{full:`h:mm:ss a zzzz`,long:`h:mm:ss a z`,medium:`h:mm:ss a`,short:`h:mm a`},defaultWidth:`full`}),dateTime:tt({formats:{full:`{{date}} 'at' {{time}}`,long:`{{date}} 'at' {{time}}`,medium:`{{date}}, {{time}}`,short:`{{date}}, {{time}}`},defaultWidth:`full`})},rt={lastWeek:`'last' eeee 'at' p`,yesterday:`'yesterday at' p`,today:`'today at' p`,tomorrow:`'tomorrow at' p`,nextWeek:`eeee 'at' p`,other:`P`},it=(e,t,n,r)=>rt[e];function at(e){return(t,n)=>{let r=n?.context?String(n.context):`standalone`,i;if(r===`formatting`&&e.formattingValues){let t=e.defaultFormattingWidth||e.defaultWidth,r=n?.width?String(n.width):t;i=e.formattingValues[r]||e.formattingValues[t]}else{let t=e.defaultWidth,r=n?.width?String(n.width):e.defaultWidth;i=e.values[r]||e.values[t]}let a=e.argumentCallback?e.argumentCallback(t):t;return i[a]}}var ot={ordinalNumber:(e,t)=>{let n=Number(e),r=n%100;if(r>20||r<10)switch(r%10){case 1:return n+`st`;case 2:return n+`nd`;case 3:return n+`rd`}return n+`th`},era:at({values:{narrow:[`B`,`A`],abbreviated:[`BC`,`AD`],wide:[`Before Christ`,`Anno Domini`]},defaultWidth:`wide`}),quarter:at({values:{narrow:[`1`,`2`,`3`,`4`],abbreviated:[`Q1`,`Q2`,`Q3`,`Q4`],wide:[`1st quarter`,`2nd quarter`,`3rd quarter`,`4th quarter`]},defaultWidth:`wide`,argumentCallback:e=>e-1}),month:at({values:{narrow:[`J`,`F`,`M`,`A`,`M`,`J`,`J`,`A`,`S`,`O`,`N`,`D`],abbreviated:[`Jan`,`Feb`,`Mar`,`Apr`,`May`,`Jun`,`Jul`,`Aug`,`Sep`,`Oct`,`Nov`,`Dec`],wide:[`January`,`February`,`March`,`April`,`May`,`June`,`July`,`August`,`September`,`October`,`November`,`December`]},defaultWidth:`wide`}),day:at({values:{narrow:[`S`,`M`,`T`,`W`,`T`,`F`,`S`],short:[`Su`,`Mo`,`Tu`,`We`,`Th`,`Fr`,`Sa`],abbreviated:[`Sun`,`Mon`,`Tue`,`Wed`,`Thu`,`Fri`,`Sat`],wide:[`Sunday`,`Monday`,`Tuesday`,`Wednesday`,`Thursday`,`Friday`,`Saturday`]},defaultWidth:`wide`}),dayPeriod:at({values:{narrow:{am:`a`,pm:`p`,midnight:`mi`,noon:`n`,morning:`morning`,afternoon:`afternoon`,evening:`evening`,night:`night`},abbreviated:{am:`AM`,pm:`PM`,midnight:`midnight`,noon:`noon`,morning:`morning`,afternoon:`afternoon`,evening:`evening`,night:`night`},wide:{am:`a.m.`,pm:`p.m.`,midnight:`midnight`,noon:`noon`,morning:`morning`,afternoon:`afternoon`,evening:`evening`,night:`night`}},defaultWidth:`wide`,formattingValues:{narrow:{am:`a`,pm:`p`,midnight:`mi`,noon:`n`,morning:`in the morning`,afternoon:`in the afternoon`,evening:`in the evening`,night:`at night`},abbreviated:{am:`AM`,pm:`PM`,midnight:`midnight`,noon:`noon`,morning:`in the morning`,afternoon:`in the afternoon`,evening:`in the evening`,night:`at night`},wide:{am:`a.m.`,pm:`p.m.`,midnight:`midnight`,noon:`noon`,morning:`in the morning`,afternoon:`in the afternoon`,evening:`in the evening`,night:`at night`}},defaultFormattingWidth:`wide`})};function st(e){return(t,n={})=>{let r=n.width,i=r&&e.matchPatterns[r]||e.matchPatterns[e.defaultMatchWidth],a=t.match(i);if(!a)return null;let o=a[0],s=r&&e.parsePatterns[r]||e.parsePatterns[e.defaultParseWidth],c=Array.isArray(s)?lt(s,e=>e.test(o)):ct(s,e=>e.test(o)),l;l=e.valueCallback?e.valueCallback(c):c,l=n.valueCallback?n.valueCallback(l):l;let u=t.slice(o.length);return{value:l,rest:u}}}function ct(e,t){for(let n in e)if(Object.prototype.hasOwnProperty.call(e,n)&&t(e[n]))return n}function lt(e,t){for(let n=0;n<e.length;n++)if(t(e[n]))return n}function ut(e){return(t,n={})=>{let r=t.match(e.matchPattern);if(!r)return null;let i=r[0],a=t.match(e.parsePattern);if(!a)return null;let o=e.valueCallback?e.valueCallback(a[0]):a[0];o=n.valueCallback?n.valueCallback(o):o;let s=t.slice(i.length);return{value:o,rest:s}}}var dt={code:`en-US`,formatDistance:et,formatLong:nt,formatRelative:it,localize:ot,match:{ordinalNumber:ut({matchPattern:/^(\d+)(th|st|nd|rd)?/i,parsePattern:/\d+/i,valueCallback:e=>parseInt(e,10)}),era:st({matchPatterns:{narrow:/^(b|a)/i,abbreviated:/^(b\.?\s?c\.?|b\.?\s?c\.?\s?e\.?|a\.?\s?d\.?|c\.?\s?e\.?)/i,wide:/^(before christ|before common era|anno domini|common era)/i},defaultMatchWidth:`wide`,parsePatterns:{any:[/^b/i,/^(a|c)/i]},defaultParseWidth:`any`}),quarter:st({matchPatterns:{narrow:/^[1234]/i,abbreviated:/^q[1234]/i,wide:/^[1234](th|st|nd|rd)? quarter/i},defaultMatchWidth:`wide`,parsePatterns:{any:[/1/i,/2/i,/3/i,/4/i]},defaultParseWidth:`any`,valueCallback:e=>e+1}),month:st({matchPatterns:{narrow:/^[jfmasond]/i,abbreviated:/^(jan|feb|mar|apr|may|jun|jul|aug|sep|oct|nov|dec)/i,wide:/^(january|february|march|april|may|june|july|august|september|october|november|december)/i},defaultMatchWidth:`wide`,parsePatterns:{narrow:[/^j/i,/^f/i,/^m/i,/^a/i,/^m/i,/^j/i,/^j/i,/^a/i,/^s/i,/^o/i,/^n/i,/^d/i],any:[/^ja/i,/^f/i,/^mar/i,/^ap/i,/^may/i,/^jun/i,/^jul/i,/^au/i,/^s/i,/^o/i,/^n/i,/^d/i]},defaultParseWidth:`any`}),day:st({matchPatterns:{narrow:/^[smtwf]/i,short:/^(su|mo|tu|we|th|fr|sa)/i,abbreviated:/^(sun|mon|tue|wed|thu|fri|sat)/i,wide:/^(sunday|monday|tuesday|wednesday|thursday|friday|saturday)/i},defaultMatchWidth:`wide`,parsePatterns:{narrow:[/^s/i,/^m/i,/^t/i,/^w/i,/^t/i,/^f/i,/^s/i],any:[/^su/i,/^m/i,/^tu/i,/^w/i,/^th/i,/^f/i,/^sa/i]},defaultParseWidth:`any`}),dayPeriod:st({matchPatterns:{narrow:/^(a|p|mi|n|(in the|at) (morning|afternoon|evening|night))/i,any:/^([ap]\.?\s?m\.?|midnight|noon|(in the|at) (morning|afternoon|evening|night))/i},defaultMatchWidth:`any`,parsePatterns:{any:{am:/^a/i,pm:/^p/i,midnight:/^mi/i,noon:/^no/i,morning:/morning/i,afternoon:/afternoon/i,evening:/evening/i,night:/night/i}},defaultParseWidth:`any`})},options:{weekStartsOn:0,firstWeekContainsDate:1}};function ft(e,t){let n=W(e,t?.in);return Le(n,Xe(n))+1}function pt(e,t){let n=W(e,t?.in),r=Me(n)-+Re(n);return Math.round(r/Ce)+1}function mt(e,t){let n=W(e,t?.in),r=n.getFullYear(),i=Ae(),a=t?.firstWeekContainsDate??t?.locale?.options?.firstWeekContainsDate??i.firstWeekContainsDate??i.locale?.options?.firstWeekContainsDate??1,o=U(t?.in||e,0);o.setFullYear(r+1,0,a),o.setHours(0,0,0,0);let s=je(o,t),c=U(t?.in||e,0);c.setFullYear(r,0,a),c.setHours(0,0,0,0);let l=je(c,t);return+n>=+s?r+1:+n>=+l?r:r-1}function ht(e,t){let n=Ae(),r=t?.firstWeekContainsDate??t?.locale?.options?.firstWeekContainsDate??n.firstWeekContainsDate??n.locale?.options?.firstWeekContainsDate??1,i=mt(e,t),a=U(t?.in||e,0);return a.setFullYear(i,0,r),a.setHours(0,0,0,0),je(a,t)}function gt(e,t){let n=W(e,t?.in),r=je(n,t)-+ht(n,t);return Math.round(r/Ce)+1}function G(e,t){return(e<0?`-`:``)+Math.abs(e).toString().padStart(t,`0`)}var K={y(e,t){let n=e.getFullYear(),r=n>0?n:1-n;return G(t===`yy`?r%100:r,t.length)},M(e,t){let n=e.getMonth();return t===`M`?String(n+1):G(n+1,2)},d(e,t){return G(e.getDate(),t.length)},a(e,t){let n=e.getHours()/12>=1?`pm`:`am`;switch(t){case`a`:case`aa`:return n.toUpperCase();case`aaa`:return n;case`aaaaa`:return n[0];default:return n===`am`?`a.m.`:`p.m.`}},h(e,t){return G(e.getHours()%12||12,t.length)},H(e,t){return G(e.getHours(),t.length)},m(e,t){return G(e.getMinutes(),t.length)},s(e,t){return G(e.getSeconds(),t.length)},S(e,t){let n=t.length,r=e.getMilliseconds();return G(Math.trunc(r*10**(n-3)),t.length)}},_t={am:`am`,pm:`pm`,midnight:`midnight`,noon:`noon`,morning:`morning`,afternoon:`afternoon`,evening:`evening`,night:`night`},vt={G:function(e,t,n){let r=+(e.getFullYear()>0);switch(t){case`G`:case`GG`:case`GGG`:return n.era(r,{width:`abbreviated`});case`GGGGG`:return n.era(r,{width:`narrow`});default:return n.era(r,{width:`wide`})}},y:function(e,t,n){if(t===`yo`){let t=e.getFullYear(),r=t>0?t:1-t;return n.ordinalNumber(r,{unit:`year`})}return K.y(e,t)},Y:function(e,t,n,r){let i=mt(e,r),a=i>0?i:1-i;return t===`YY`?G(a%100,2):t===`Yo`?n.ordinalNumber(a,{unit:`year`}):G(a,t.length)},R:function(e,t){return G(Ne(e),t.length)},u:function(e,t){return G(e.getFullYear(),t.length)},Q:function(e,t,n){let r=Math.ceil((e.getMonth()+1)/3);switch(t){case`Q`:return String(r);case`QQ`:return G(r,2);case`Qo`:return n.ordinalNumber(r,{unit:`quarter`});case`QQQ`:return n.quarter(r,{width:`abbreviated`,context:`formatting`});case`QQQQQ`:return n.quarter(r,{width:`narrow`,context:`formatting`});default:return n.quarter(r,{width:`wide`,context:`formatting`})}},q:function(e,t,n){let r=Math.ceil((e.getMonth()+1)/3);switch(t){case`q`:return String(r);case`qq`:return G(r,2);case`qo`:return n.ordinalNumber(r,{unit:`quarter`});case`qqq`:return n.quarter(r,{width:`abbreviated`,context:`standalone`});case`qqqqq`:return n.quarter(r,{width:`narrow`,context:`standalone`});default:return n.quarter(r,{width:`wide`,context:`standalone`})}},M:function(e,t,n){let r=e.getMonth();switch(t){case`M`:case`MM`:return K.M(e,t);case`Mo`:return n.ordinalNumber(r+1,{unit:`month`});case`MMM`:return n.month(r,{width:`abbreviated`,context:`formatting`});case`MMMMM`:return n.month(r,{width:`narrow`,context:`formatting`});default:return n.month(r,{width:`wide`,context:`formatting`})}},L:function(e,t,n){let r=e.getMonth();switch(t){case`L`:return String(r+1);case`LL`:return G(r+1,2);case`Lo`:return n.ordinalNumber(r+1,{unit:`month`});case`LLL`:return n.month(r,{width:`abbreviated`,context:`standalone`});case`LLLLL`:return n.month(r,{width:`narrow`,context:`standalone`});default:return n.month(r,{width:`wide`,context:`standalone`})}},w:function(e,t,n,r){let i=gt(e,r);return t===`wo`?n.ordinalNumber(i,{unit:`week`}):G(i,t.length)},I:function(e,t,n){let r=pt(e);return t===`Io`?n.ordinalNumber(r,{unit:`week`}):G(r,t.length)},d:function(e,t,n){return t===`do`?n.ordinalNumber(e.getDate(),{unit:`date`}):K.d(e,t)},D:function(e,t,n){let r=ft(e);return t===`Do`?n.ordinalNumber(r,{unit:`dayOfYear`}):G(r,t.length)},E:function(e,t,n){let r=e.getDay();switch(t){case`E`:case`EE`:case`EEE`:return n.day(r,{width:`abbreviated`,context:`formatting`});case`EEEEE`:return n.day(r,{width:`narrow`,context:`formatting`});case`EEEEEE`:return n.day(r,{width:`short`,context:`formatting`});default:return n.day(r,{width:`wide`,context:`formatting`})}},e:function(e,t,n,r){let i=e.getDay(),a=(i-r.weekStartsOn+8)%7||7;switch(t){case`e`:return String(a);case`ee`:return G(a,2);case`eo`:return n.ordinalNumber(a,{unit:`day`});case`eee`:return n.day(i,{width:`abbreviated`,context:`formatting`});case`eeeee`:return n.day(i,{width:`narrow`,context:`formatting`});case`eeeeee`:return n.day(i,{width:`short`,context:`formatting`});default:return n.day(i,{width:`wide`,context:`formatting`})}},c:function(e,t,n,r){let i=e.getDay(),a=(i-r.weekStartsOn+8)%7||7;switch(t){case`c`:return String(a);case`cc`:return G(a,t.length);case`co`:return n.ordinalNumber(a,{unit:`day`});case`ccc`:return n.day(i,{width:`abbreviated`,context:`standalone`});case`ccccc`:return n.day(i,{width:`narrow`,context:`standalone`});case`cccccc`:return n.day(i,{width:`short`,context:`standalone`});default:return n.day(i,{width:`wide`,context:`standalone`})}},i:function(e,t,n){let r=e.getDay(),i=r===0?7:r;switch(t){case`i`:return String(i);case`ii`:return G(i,t.length);case`io`:return n.ordinalNumber(i,{unit:`day`});case`iii`:return n.day(r,{width:`abbreviated`,context:`formatting`});case`iiiii`:return n.day(r,{width:`narrow`,context:`formatting`});case`iiiiii`:return n.day(r,{width:`short`,context:`formatting`});default:return n.day(r,{width:`wide`,context:`formatting`})}},a:function(e,t,n){let r=e.getHours()/12>=1?`pm`:`am`;switch(t){case`a`:case`aa`:return n.dayPeriod(r,{width:`abbreviated`,context:`formatting`});case`aaa`:return n.dayPeriod(r,{width:`abbreviated`,context:`formatting`}).toLowerCase();case`aaaaa`:return n.dayPeriod(r,{width:`narrow`,context:`formatting`});default:return n.dayPeriod(r,{width:`wide`,context:`formatting`})}},b:function(e,t,n){let r=e.getHours(),i;switch(i=r===12?_t.noon:r===0?_t.midnight:r/12>=1?`pm`:`am`,t){case`b`:case`bb`:return n.dayPeriod(i,{width:`abbreviated`,context:`formatting`});case`bbb`:return n.dayPeriod(i,{width:`abbreviated`,context:`formatting`}).toLowerCase();case`bbbbb`:return n.dayPeriod(i,{width:`narrow`,context:`formatting`});default:return n.dayPeriod(i,{width:`wide`,context:`formatting`})}},B:function(e,t,n){let r=e.getHours(),i;switch(i=r>=17?_t.evening:r>=12?_t.afternoon:r>=4?_t.morning:_t.night,t){case`B`:case`BB`:case`BBB`:return n.dayPeriod(i,{width:`abbreviated`,context:`formatting`});case`BBBBB`:return n.dayPeriod(i,{width:`narrow`,context:`formatting`});default:return n.dayPeriod(i,{width:`wide`,context:`formatting`})}},h:function(e,t,n){if(t===`ho`){let t=e.getHours()%12;return t===0&&(t=12),n.ordinalNumber(t,{unit:`hour`})}return K.h(e,t)},H:function(e,t,n){return t===`Ho`?n.ordinalNumber(e.getHours(),{unit:`hour`}):K.H(e,t)},K:function(e,t,n){let r=e.getHours()%12;return t===`Ko`?n.ordinalNumber(r,{unit:`hour`}):G(r,t.length)},k:function(e,t,n){let r=e.getHours();return r===0&&(r=24),t===`ko`?n.ordinalNumber(r,{unit:`hour`}):G(r,t.length)},m:function(e,t,n){return t===`mo`?n.ordinalNumber(e.getMinutes(),{unit:`minute`}):K.m(e,t)},s:function(e,t,n){return t===`so`?n.ordinalNumber(e.getSeconds(),{unit:`second`}):K.s(e,t)},S:function(e,t){return K.S(e,t)},X:function(e,t,n){let r=e.getTimezoneOffset();if(r===0)return`Z`;switch(t){case`X`:return bt(r);case`XXXX`:case`XX`:return q(r);default:return q(r,`:`)}},x:function(e,t,n){let r=e.getTimezoneOffset();switch(t){case`x`:return bt(r);case`xxxx`:case`xx`:return q(r);default:return q(r,`:`)}},O:function(e,t,n){let r=e.getTimezoneOffset();switch(t){case`O`:case`OO`:case`OOO`:return`GMT`+yt(r,`:`);default:return`GMT`+q(r,`:`)}},z:function(e,t,n){let r=e.getTimezoneOffset();switch(t){case`z`:case`zz`:case`zzz`:return`GMT`+yt(r,`:`);default:return`GMT`+q(r,`:`)}},t:function(e,t,n){return G(Math.trunc(e/1e3),t.length)},T:function(e,t,n){return G(+e,t.length)}};function yt(e,t=``){let n=e>0?`-`:`+`,r=Math.abs(e),i=Math.trunc(r/60),a=r%60;return a===0?n+String(i):n+String(i)+t+G(a,2)}function bt(e,t){return e%60==0?(e>0?`-`:`+`)+G(Math.abs(e)/60,2):q(e,t)}function q(e,t=``){let n=e>0?`-`:`+`,r=Math.abs(e),i=G(Math.trunc(r/60),2),a=G(r%60,2);return n+i+t+a}var xt=(e,t)=>{switch(e){case`P`:return t.date({width:`short`});case`PP`:return t.date({width:`medium`});case`PPP`:return t.date({width:`long`});default:return t.date({width:`full`})}},St=(e,t)=>{switch(e){case`p`:return t.time({width:`short`});case`pp`:return t.time({width:`medium`});case`ppp`:return t.time({width:`long`});default:return t.time({width:`full`})}},Ct={p:St,P:(e,t)=>{let n=e.match(/(P+)(p+)?/)||[],r=n[1],i=n[2];if(!i)return xt(e,t);let a;switch(r){case`P`:a=t.dateTime({width:`short`});break;case`PP`:a=t.dateTime({width:`medium`});break;case`PPP`:a=t.dateTime({width:`long`});break;default:a=t.dateTime({width:`full`});break}return a.replace(`{{date}}`,xt(r,t)).replace(`{{time}}`,St(i,t))}},wt=/^D+$/,Tt=/^Y+$/,Et=[`D`,`DD`,`YY`,`YYYY`];function Dt(e){return wt.test(e)}function Ot(e){return Tt.test(e)}function kt(e,t,n){let r=At(e,t,n);if(console.warn(r),Et.includes(e))throw RangeError(r)}function At(e,t,n){let r=e[0]===`Y`?`years`:`days of the month`;return`Use \`${e.toLowerCase()}\` instead of \`${e}\` (in \`${t}\`) for formatting ${r} to the input \`${n}\`; see: https://github.com/date-fns/date-fns/blob/master/docs/unicodeTokens.md`}var jt=/[yYQqMLwIdDecihHKkms]o|(\w)\1*|''|'(''|[^'])+('|$)|./g,Mt=/P+p+|P+|p+|''|'(''|[^'])+('|$)|./g,Nt=/^'([^]*?)'?$/,Pt=/''/g,Ft=/[a-zA-Z]/;function It(e,t,n){let r=Ae(),i=n?.locale??r.locale??dt,a=n?.firstWeekContainsDate??n?.locale?.options?.firstWeekContainsDate??r.firstWeekContainsDate??r.locale?.options?.firstWeekContainsDate??1,o=n?.weekStartsOn??n?.locale?.options?.weekStartsOn??r.weekStartsOn??r.locale?.options?.weekStartsOn??0,s=W(e,n?.in);if(!Ge(s))throw RangeError(`Invalid time value`);let c=t.match(Mt).map(e=>{let t=e[0];if(t===`p`||t===`P`){let n=Ct[t];return n(e,i.formatLong)}return e}).join(``).match(jt).map(e=>{if(e===`''`)return{isToken:!1,value:`'`};let t=e[0];if(t===`'`)return{isToken:!1,value:Lt(e)};if(vt[t])return{isToken:!0,value:e};if(t.match(Ft))throw RangeError("Format string contains an unescaped latin alphabet character `"+t+"`");return{isToken:!1,value:e}});i.localize.preprocessor&&(c=i.localize.preprocessor(s,c));let l={firstWeekContainsDate:a,weekStartsOn:o,locale:i};return c.map(r=>{if(!r.isToken)return r.value;let a=r.value;(!n?.useAdditionalWeekYearTokens&&Ot(a)||!n?.useAdditionalDayOfYearTokens&&Dt(a))&&kt(a,t,String(e));let o=vt[a[0]];return o(s,a,i.localize,l)}).join(``)}function Lt(e){let t=e.match(Nt);return t?t[1].replace(Pt,`'`):e}function Rt(e,t){let n=W(e,t?.in),r=n.getFullYear(),i=n.getMonth(),a=U(n,0);return a.setFullYear(r,i+1,0),a.setHours(0,0,0,0),a.getDate()}function zt(e,t){return+W(e)>+W(t)}function Bt(e,t){return+W(e)<+W(t)}function Vt(e,t,n){let[r,i]=Fe(n?.in,e,t);return r.getFullYear()===i.getFullYear()&&r.getMonth()===i.getMonth()}function Ht(e,t,n){let[r,i]=Fe(n?.in,e,t);return r.getFullYear()===i.getFullYear()}function Ut(e,t,n){let r=W(e,n?.in),i=r.getFullYear(),a=r.getDate(),o=U(n?.in||e,0);o.setFullYear(i,t,15),o.setHours(0,0,0,0);let s=Rt(o);return r.setMonth(t,Math.min(a,s)),r}function Wt(e,t,n){let r=W(e,n?.in);return isNaN(+r)?U(n?.in||e,NaN):(r.setFullYear(t),r)}var Gt=5,Kt=4;function qt(e,t){let n=t.startOfMonth(e),r=n.getDay()>0?n.getDay():7,i=t.addDays(e,-r+1),a=t.addDays(i,Gt*7-1);return e.getMonth()===a.getMonth()?Gt:Kt}function Jt(e,t){let n=t.startOfMonth(e),r=n.getDay();return r===1?n:r===0?t.addDays(n,-6):t.addDays(n,-1*(r-1))}function Yt(e,t){let n=Jt(e,t),r=qt(e,t);return t.addDays(n,r*7-1)}var J=class{constructor(e,t){this.Date=Date,this.addDays=(e,t)=>this.overrides?.addDays?this.overrides.addDays(e,t):De(e,t),this.addMonths=(e,t)=>this.overrides?.addMonths?this.overrides.addMonths(e,t):Oe(e,t),this.addWeeks=(e,t)=>this.overrides?.addWeeks?this.overrides.addWeeks(e,t):ze(e,t),this.addYears=(e,t)=>this.overrides?.addYears?this.overrides.addYears(e,t):Be(e,t),this.differenceInCalendarDays=(e,t)=>this.overrides?.differenceInCalendarDays?this.overrides.differenceInCalendarDays(e,t):Le(e,t),this.differenceInCalendarMonths=(e,t)=>this.overrides?.differenceInCalendarMonths?this.overrides.differenceInCalendarMonths(e,t):Ke(e,t),this.endOfBroadcastWeek=e=>this.overrides?.endOfBroadcastWeek?this.overrides.endOfBroadcastWeek(e,this):Yt(e,this),this.endOfISOWeek=e=>this.overrides?.endOfISOWeek?this.overrides.endOfISOWeek(e):Qe(e),this.endOfMonth=e=>this.overrides?.endOfMonth?this.overrides.endOfMonth(e):qe(e),this.endOfWeek=e=>this.overrides?.endOfWeek?this.overrides.endOfWeek(e,this.options):Ze(e,this.options),this.endOfYear=e=>this.overrides?.endOfYear?this.overrides.endOfYear(e):Ye(e),this.format=(e,t)=>this.overrides?.format?this.overrides.format(e,t,this.options):It(e,t,this.options),this.getISOWeek=e=>this.overrides?.getISOWeek?this.overrides.getISOWeek(e):pt(e),this.getWeek=e=>this.overrides?.getWeek?this.overrides.getWeek(e,this.options):gt(e,this.options),this.isAfter=(e,t)=>this.overrides?.isAfter?this.overrides.isAfter(e,t):zt(e,t),this.isBefore=(e,t)=>this.overrides?.isBefore?this.overrides.isBefore(e,t):Bt(e,t),this.isDate=e=>this.overrides?.isDate?this.overrides.isDate(e):We(e),this.isSameDay=(e,t)=>this.overrides?.isSameDay?this.overrides.isSameDay(e,t):Ue(e,t),this.isSameMonth=(e,t)=>this.overrides?.isSameMonth?this.overrides.isSameMonth(e,t):Vt(e,t),this.isSameYear=(e,t)=>this.overrides?.isSameYear?this.overrides.isSameYear(e,t):Ht(e,t),this.max=e=>this.overrides?.max?this.overrides.max(e):Ve(e),this.min=e=>this.overrides?.min?this.overrides.min(e):He(e),this.setMonth=(e,t)=>this.overrides?.setMonth?this.overrides.setMonth(e,t):Ut(e,t),this.setYear=(e,t)=>this.overrides?.setYear?this.overrides.setYear(e,t):Wt(e,t),this.startOfBroadcastWeek=e=>this.overrides?.startOfBroadcastWeek?this.overrides.startOfBroadcastWeek(e,this):Jt(e,this),this.startOfDay=e=>this.overrides?.startOfDay?this.overrides.startOfDay(e):Ie(e),this.startOfISOWeek=e=>this.overrides?.startOfISOWeek?this.overrides.startOfISOWeek(e):Me(e),this.startOfMonth=e=>this.overrides?.startOfMonth?this.overrides.startOfMonth(e):Je(e),this.startOfWeek=e=>this.overrides?.startOfWeek?this.overrides.startOfWeek(e,this.options):je(e,this.options),this.startOfYear=e=>this.overrides?.startOfYear?this.overrides.startOfYear(e):Xe(e),this.options={locale:dt,...e},this.overrides=t}},Y=new J;function Xt(e,t,n={}){return Object.entries(e).filter(([,e])=>e===!0).reduce((e,[r])=>(n[r]?e.push(n[r]):t[V[r]]?e.push(t[V[r]]):t[H[r]]&&e.push(t[H[r]]),e),[t[B.Day]])}function Zt(e){return z.createElement(`button`,{...e})}function Qt(e){return z.createElement(`span`,{...e})}function $t(e){let{size:t=24,orientation:n=`left`,className:r}=e;return z.createElement(`svg`,{className:r,width:t,height:t,viewBox:`0 0 24 24`},n===`up`&&z.createElement(`polygon`,{points:`6.77 17 12.5 11.43 18.24 17 20 15.28 12.5 8 5 15.28`}),n===`down`&&z.createElement(`polygon`,{points:`6.77 8 12.5 13.57 18.24 8 20 9.72 12.5 17 5 9.72`}),n===`left`&&z.createElement(`polygon`,{points:`16 18.112 9.81111111 12 16 5.87733333 14.0888889 4 6 12 14.0888889 20`}),n===`right`&&z.createElement(`polygon`,{points:`8 18.612 14.1888889 12.5 8 6.37733333 9.91111111 4.5 18 12.5 9.91111111 20.5`}))}function en(e){let{day:t,modifiers:n,...r}=e;return z.createElement(`td`,{...r})}function tn(e){let{day:t,modifiers:n,...r}=e,i=z.useRef(null);return z.useEffect(()=>{n.focused&&i.current?.focus()},[n.focused]),z.createElement(`button`,{ref:i,...r})}function nn(e){let{options:t,className:n,components:r,classNames:i,...a}=e,o=[i[B.Dropdown],n].join(` `),s=t?.find(({value:e})=>e===a.value);return z.createElement(`span`,{"data-disabled":a.disabled,className:i[B.DropdownRoot]},z.createElement(r.Select,{className:o,...a},t?.map(({value:e,label:t,disabled:n})=>z.createElement(r.Option,{key:e,value:e,disabled:n},t))),z.createElement(`span`,{className:i[B.CaptionLabel],"aria-hidden":!0},s?.label,z.createElement(r.Chevron,{orientation:`down`,size:18,className:i[B.Chevron]})))}function rn(e){return z.createElement(`div`,{...e})}function an(e){return z.createElement(`div`,{...e})}function on(e){let{calendarMonth:t,displayIndex:n,...r}=e;return z.createElement(`div`,{...r},e.children)}function sn(e){let{calendarMonth:t,displayIndex:n,...r}=e;return z.createElement(`div`,{...r})}function cn(e){return z.createElement(`table`,{...e})}function ln(e){return z.createElement(`div`,{...e})}var un=(0,z.createContext)(void 0);function dn(){let e=(0,z.useContext)(un);if(e===void 0)throw Error(`useDayPicker() must be used within a custom component.`);return e}function fn(e){let{components:t}=dn();return z.createElement(t.Dropdown,{...e})}function pn(e){let{onPreviousClick:t,onNextClick:n,previousMonth:r,nextMonth:i,...a}=e,{components:o,classNames:s,labels:{labelPrevious:c,labelNext:l}}=dn();return z.createElement(`nav`,{...a},z.createElement(o.PreviousMonthButton,{type:`button`,className:s[B.PreviousMonthButton],tabIndex:r?void 0:-1,disabled:!r||void 0,"aria-label":c(r),onClick:e.onPreviousClick},z.createElement(o.Chevron,{disabled:!r||void 0,className:s[B.Chevron],orientation:`left`})),z.createElement(o.NextMonthButton,{type:`button`,className:s[B.NextMonthButton],tabIndex:i?void 0:-1,disabled:!i||void 0,"aria-label":l(i),onClick:e.onNextClick},z.createElement(o.Chevron,{disabled:!i||void 0,orientation:`right`,className:s[B.Chevron]})))}function mn(e){let{components:t}=dn();return z.createElement(t.Button,{...e})}function hn(e){return z.createElement(`option`,{...e})}function gn(e){let{components:t}=dn();return z.createElement(t.Button,{...e})}function _n(e){return z.createElement(`div`,{...e})}function vn(e){return z.createElement(`select`,{...e})}function yn(e){let{week:t,...n}=e;return z.createElement(`tr`,{...n})}function bn(e){return z.createElement(`th`,{...e})}function xn(e){return z.createElement(`thead`,{"aria-hidden":!0},z.createElement(`tr`,{...e}))}function Sn(e){let{week:t,...n}=e;return z.createElement(`th`,{...n})}function Cn(e){return z.createElement(`th`,{...e})}function wn(e){return z.createElement(`tbody`,{...e})}function Tn(e){let{components:t}=dn();return z.createElement(t.Dropdown,{...e})}var En=t({Button:()=>Zt,CaptionLabel:()=>Qt,Chevron:()=>$t,Day:()=>en,DayButton:()=>tn,Dropdown:()=>nn,DropdownNav:()=>rn,Footer:()=>an,Month:()=>on,MonthCaption:()=>sn,MonthGrid:()=>cn,Months:()=>ln,MonthsDropdown:()=>fn,Nav:()=>pn,NextMonthButton:()=>mn,Option:()=>hn,PreviousMonthButton:()=>gn,Root:()=>_n,Select:()=>vn,Week:()=>yn,WeekNumber:()=>Sn,WeekNumberHeader:()=>Cn,Weekday:()=>bn,Weekdays:()=>xn,Weeks:()=>wn,YearsDropdown:()=>Tn});function Dn(e){return{...En,...e}}function On(e){let t={"data-mode":e.mode??void 0,"data-required":`required`in e?e.required:void 0,"data-multiple-months":e.numberOfMonths&&e.numberOfMonths>1||void 0,"data-week-numbers":e.showWeekNumber||void 0,"data-broadcast-calendar":e.broadcastCalendar||void 0};return Object.entries(e).forEach(([e,n])=>{e.startsWith(`data-`)&&(t[e]=n)}),t}function kn(){let e={};for(let t in B)e[B[t]]=`rdp-${B[t]}`;for(let t in V)e[V[t]]=`rdp-${V[t]}`;for(let t in H)e[H[t]]=`rdp-${H[t]}`;return e}function An(e,t,n){return(n??new J(t)).format(e,`LLLL y`)}var jn=An;function Mn(e,t,n){return(n??new J(t)).format(e,`d`)}function Nn(e,t){return t.localize?.month(e)}function Pn(e){return e<10?`0${e.toLocaleString()}`:`${e.toLocaleString()}`}function Fn(){return``}function In(e,t,n){return(n??new J(t)).format(e,`cccccc`)}function Ln(e){return e.toString()}var Rn=Ln,zn=t({formatCaption:()=>An,formatDay:()=>Mn,formatMonthCaption:()=>jn,formatMonthDropdown:()=>Nn,formatWeekNumber:()=>Pn,formatWeekNumberHeader:()=>Fn,formatWeekdayName:()=>In,formatYearCaption:()=>Rn,formatYearDropdown:()=>Ln});function Bn(e){return e?.formatMonthCaption&&!e.formatCaption&&(e.formatCaption=e.formatMonthCaption),e?.formatYearCaption&&!e.formatYearDropdown&&(e.formatYearDropdown=e.formatYearCaption),{...zn,...e}}function Vn(e,t,n,r,i){if(!t||!n)return;let{addMonths:a,startOfMonth:o}=i,s=e.getFullYear(),c=[],l=t;for(;c.length<12;)c.push(l.getMonth()),l=a(l,1);return c.sort((e,t)=>e-t).map(e=>{let a=r.formatMonthDropdown(e,i.options.locale??dt),c=i.Date?new i.Date(s,e):new Date(s,e);return{value:e,label:a,disabled:t&&c<o(t)||n&&c>o(n)||!1}})}function Hn(e,t={},n={}){let r={...t?.[B.Day]};return Object.entries(e).filter(([,e])=>e===!0).forEach(([e])=>{r={...r,...n?.[e]}}),r}function Un(e,t,n=`long`){return new Intl.DateTimeFormat(`en-US`,{hour:`numeric`,timeZone:e,timeZoneName:n}).format(t).split(/\s/g).slice(2).join(` `)}var Wn={},Gn={};function Kn(e,t){try{let n=(Wn[e]||=new Intl.DateTimeFormat(`en-US`,{timeZone:e,timeZoneName:`longOffset`}).format)(t).split(`GMT`)[1];return n in Gn?Gn[n]:Jn(n,n.split(`:`))}catch{if(e in Gn)return Gn[e];let t=e?.match(qn);return t?Jn(e,t.slice(1)):NaN}}var qn=/([+-]\d\d):?(\d\d)?/;function Jn(e,t){let n=+(t[0]||0),r=+(t[1]||0),i=(t[2]||0)/60;return Gn[e]=n*60+r>0?n*60+r+i:n*60-r-i}var Yn=class e extends Date{constructor(...e){super(),e.length>1&&typeof e[e.length-1]==`string`&&(this.timeZone=e.pop()),this.internal=new Date,isNaN(Kn(this.timeZone,this))?this.setTime(NaN):e.length?typeof e[0]==`number`&&(e.length===1||e.length===2&&typeof e[1]!=`number`)?this.setTime(e[0]):typeof e[0]==`string`?this.setTime(+new Date(e[0])):e[0]instanceof Date?this.setTime(+e[0]):(this.setTime(+new Date(...e)),$n(this,NaN),Zn(this)):this.setTime(Date.now())}static tz(t,...n){return n.length?new e(...n,t):new e(Date.now(),t)}withTimeZone(t){return new e(+this,t)}getTimezoneOffset(){let e=-Kn(this.timeZone,this);return e>0?Math.floor(e):Math.ceil(e)}setTime(e){return Date.prototype.setTime.apply(this,arguments),Zn(this),+this}[Symbol.for(`constructDateFrom`)](t){return new e(+new Date(t),this.timeZone)}},Xn=/^(get|set)(?!UTC)/;Object.getOwnPropertyNames(Date.prototype).forEach(e=>{if(!Xn.test(e))return;let t=e.replace(Xn,`$1UTC`);Yn.prototype[t]&&(e.startsWith(`get`)?Yn.prototype[e]=function(){return this.internal[t]()}:(Yn.prototype[e]=function(){return Date.prototype[t].apply(this.internal,arguments),Qn(this),+this},Yn.prototype[t]=function(){return Date.prototype[t].apply(this,arguments),Zn(this),+this}))});function Zn(e){e.internal.setTime(+e),e.internal.setUTCSeconds(e.internal.getUTCSeconds()-Math.round(-Kn(e.timeZone,e)*60))}function Qn(e){Date.prototype.setFullYear.call(e,e.internal.getUTCFullYear(),e.internal.getUTCMonth(),e.internal.getUTCDate()),Date.prototype.setHours.call(e,e.internal.getUTCHours(),e.internal.getUTCMinutes(),e.internal.getUTCSeconds(),e.internal.getUTCMilliseconds()),$n(e)}function $n(e){let t=Kn(e.timeZone,e),n=t>0?Math.floor(t):Math.ceil(t),r=new Date(+e);r.setUTCHours(r.getUTCHours()-1);let i=-new Date(+e).getTimezoneOffset(),a=i- -new Date(+r).getTimezoneOffset(),o=Date.prototype.getHours.apply(e)!==e.internal.getUTCHours();a&&o&&e.internal.setUTCMinutes(e.internal.getUTCMinutes()+a);let s=i-n;s&&Date.prototype.setUTCMinutes.call(e,Date.prototype.getUTCMinutes.call(e)+s);let c=new Date(+e);c.setUTCSeconds(0);let l=i>0?c.getSeconds():(c.getSeconds()-60)%60,u=Math.round(-(Kn(e.timeZone,e)*60))%60;(u||l)&&(e.internal.setUTCSeconds(e.internal.getUTCSeconds()+u),Date.prototype.setUTCSeconds.call(e,Date.prototype.getUTCSeconds.call(e)+u+l));let d=Kn(e.timeZone,e),f=d>0?Math.floor(d):Math.ceil(d),p=-new Date(+e).getTimezoneOffset()-f,m=f!==n,h=p-s;if(m&&h){Date.prototype.setUTCMinutes.call(e,Date.prototype.getUTCMinutes.call(e)+h);let t=Kn(e.timeZone,e),n=f-(t>0?Math.floor(t):Math.ceil(t));n&&(e.internal.setUTCMinutes(e.internal.getUTCMinutes()+n),Date.prototype.setUTCMinutes.call(e,Date.prototype.getUTCMinutes.call(e)+n))}}var er=class e extends Yn{static tz(t,...n){return n.length?new e(...n,t):new e(Date.now(),t)}toISOString(){let[e,t,n]=this.tzComponents(),r=`${e}${t}:${n}`;return this.internal.toISOString().slice(0,-1)+r}toString(){return`${this.toDateString()} ${this.toTimeString()}`}toDateString(){let[e,t,n,r]=this.internal.toUTCString().split(` `);return`${e?.slice(0,-1)} ${n} ${t} ${r}`}toTimeString(){let e=this.internal.toUTCString().split(` `)[4],[t,n,r]=this.tzComponents();return`${e} GMT${t}${n}${r} (${Un(this.timeZone,this)})`}toLocaleString(e,t){return Date.prototype.toLocaleString.call(this,e,{...t,timeZone:t?.timeZone||this.timeZone})}toLocaleDateString(e,t){return Date.prototype.toLocaleDateString.call(this,e,{...t,timeZone:t?.timeZone||this.timeZone})}toLocaleTimeString(e,t){return Date.prototype.toLocaleTimeString.call(this,e,{...t,timeZone:t?.timeZone||this.timeZone})}tzComponents(){let e=this.getTimezoneOffset();return[e>0?`-`:`+`,String(Math.floor(Math.abs(e)/60)).padStart(2,`0`),String(Math.abs(e)%60).padStart(2,`0`)]}withTimeZone(t){return new e(+this,t)}[Symbol.for(`constructDateFrom`)](t){return new e(+new Date(t),this.timeZone)}};function tr(e,t,n,r){let i=n?er.tz(n):e.Date?new e.Date:new Date,a=r?e.startOfBroadcastWeek(i,e):t?e.startOfISOWeek(i):e.startOfWeek(i),o=[];for(let t=0;t<7;t++){let n=e.addDays(a,t);o.push(n)}return o}function nr(e,t,n,r){if(!e||!t)return;let{startOfYear:i,endOfYear:a,addYears:o,isBefore:s,isSameYear:c}=r,l=i(e),u=a(t),d=[],f=l;for(;s(f,u)||c(f,u);)d.push(f.getFullYear()),f=o(f,1);return d.map(e=>({value:e,label:n.formatYearDropdown(e),disabled:!1}))}function rr(e,t,n){return(n??new J(t)).format(e,`LLLL y`)}var ir=rr;function ar(e,t,n,r){let i=(r??new J(n)).format(e,`PPPP`);return t?.today&&(i=`Today, ${i}`),i}function or(e,t,n,r){let i=(r??new J(n)).format(e,`PPPP`);return t.today&&(i=`Today, ${i}`),t.selected&&(i=`${i}, selected`),i}var sr=or;function cr(){return``}function lr(e){return`Choose the Month`}function ur(e){return`Go to the Next Month`}function dr(e){return`Go to the Previous Month`}function fr(e,t,n){return(n??new J(t)).format(e,`cccc`)}function pr(e,t){return`Week ${e}`}function mr(e){return`Week Number`}function hr(e){return`Choose the Year`}var gr=t({labelCaption:()=>ir,labelDay:()=>sr,labelDayButton:()=>or,labelGrid:()=>rr,labelGridcell:()=>ar,labelMonthDropdown:()=>lr,labelNav:()=>cr,labelNext:()=>ur,labelPrevious:()=>dr,labelWeekNumber:()=>pr,labelWeekNumberHeader:()=>mr,labelWeekday:()=>fr,labelYearDropdown:()=>hr});function _r(e,t,n,r){let i=e[0],a=e[e.length-1],{ISOWeek:o,fixedWeeks:s,broadcastCalendar:c}=n??{},{addDays:l,differenceInCalendarDays:u,differenceInCalendarMonths:d,endOfBroadcastWeek:f,endOfISOWeek:p,endOfMonth:m,endOfWeek:h,isAfter:g,startOfBroadcastWeek:_,startOfISOWeek:v,startOfWeek:y}=r,b=c?_(i,r):o?v(i):y(i),x=u(c?f(a,r):o?p(m(a)):h(m(a)),b),S=d(a,i)+1,C=[];for(let e=0;e<=x;e++){let n=l(b,e);if(t&&g(n,t))break;C.push(n)}let w=(c?35:42)*S;if(s&&C.length<w){let e=w-C.length;for(let t=0;t<e;t++){let e=l(C[C.length-1],1);C.push(e)}}return C}function vr(e){return e.reduce((e,t)=>{let n=t.weeks.reduce((e,t)=>[...e,...t.days],[]);return[...e,...n]},[])}function yr(e,t,n,r){let{numberOfMonths:i=1}=n,a=[];for(let n=0;n<i;n++){let i=r.addMonths(e,n);if(t&&i>t)break;a.push(i)}return a}function br(e,t){let{month:n,defaultMonth:r,today:i=e.timeZone?er.tz(e.timeZone):t.Date?new t.Date:new Date,numberOfMonths:a=1,endMonth:o,startMonth:s}=e,c=n||r||i,{differenceInCalendarMonths:l,addMonths:u,startOfMonth:d}=t;return o&&l(o,c)<0&&(c=u(o,-1*(a-1))),s&&l(c,s)<0&&(c=s),d(c)}var xr=class{constructor(e,t,n=Y){this.date=e,this.displayMonth=t,this.outside=!!(t&&!n.isSameMonth(e,t)),this.dateLib=n}isEqualTo(e){return this.dateLib.isSameDay(e.date,this.date)&&this.dateLib.isSameMonth(e.displayMonth,this.displayMonth)}},Sr=class{constructor(e,t){this.date=e,this.weeks=t}},Cr=class{constructor(e,t){this.days=t,this.weekNumber=e}};function wr(e,t,n,r){let{addDays:i,endOfBroadcastWeek:a,endOfISOWeek:o,endOfMonth:s,endOfWeek:c,getISOWeek:l,getWeek:u,startOfBroadcastWeek:d,startOfISOWeek:f,startOfWeek:p}=r,m=e.reduce((e,m)=>{let h=n.broadcastCalendar?d(m,r):n.ISOWeek?f(m):p(m),g=n.broadcastCalendar?a(m,r):n.ISOWeek?o(s(m)):c(s(m)),_=t.filter(e=>e>=h&&e<=g),v=n.broadcastCalendar?35:42;if(n.fixedWeeks&&_.length<v){let e=t.filter(e=>{let t=v-_.length;return e>g&&e<=i(g,t)});_.push(...e)}let y=new Sr(m,_.reduce((e,t)=>{let i=n.ISOWeek?l(t):u(t),a=e.find(e=>e.weekNumber===i),o=new xr(t,m,r);return a?a.days.push(o):e.push(new Cr(i,[o])),e},[]));return e.push(y),e},[]);return n.reverseMonths?m.reverse():m}function Tr(e,t){let{startMonth:n,endMonth:r}=e,{startOfYear:i,startOfDay:a,startOfMonth:o,endOfMonth:s,addYears:c,endOfYear:l}=t,{fromYear:u,toYear:d,fromMonth:f,toMonth:p}=e;!n&&f&&(n=f),!n&&u&&(n=new Date(u,0,1)),!r&&p&&(r=p),!r&&d&&(r=new Date(d,11,31));let m=e.captionLayout?.startsWith(`dropdown`);return n?n=o(n):u?n=new Date(u,0,1):!n&&m&&(n=i(c(e.today??(e.timeZone?er.tz(e.timeZone):t.Date?new t.Date:new Date),-100))),r?r=s(r):d?r=new Date(d,11,31):!r&&m&&(r=l(e.today??(e.timeZone?er.tz(e.timeZone):t.Date?new t.Date:new Date))),[n&&a(n),r&&a(r)]}function Er(e,t,n,r){if(n.disableNavigation)return;let{pagedNavigation:i,numberOfMonths:a=1}=n,{startOfMonth:o,addMonths:s,differenceInCalendarMonths:c}=r,l=i?a:1,u=o(e);if(!t||!(c(t,e)<a))return s(u,l)}function Dr(e,t,n,r){if(n.disableNavigation)return;let{pagedNavigation:i,numberOfMonths:a}=n,{startOfMonth:o,addMonths:s,differenceInCalendarMonths:c}=r,l=i?a??1:1,u=o(e);if(!t||!(c(u,t)<=0))return s(u,-l)}function Or(e){return e.reduce((e,t)=>[...e,...t.weeks],[])}function kr(e,t){let[n,r]=(0,z.useState)(e);return[t===void 0?n:t,r]}function Ar(e,t){let[n,r]=Tr(e,t),{startOfMonth:i,endOfMonth:a}=t,[o,s]=kr(br(e,t),e.month?i(e.month):void 0);(0,z.useEffect)(()=>{let n=br(e,t);s(n)},[e.timeZone]);let c=yr(o,r,e,t),l=wr(c,_r(c,e.endMonth?a(e.endMonth):void 0,e,t),e,t),u=Or(l),d=vr(l),f=Dr(o,n,e,t),p=Er(o,r,e,t),{disableNavigation:m,onMonthChange:h}=e,g=e=>u.some(t=>t.days.some(t=>t.isEqualTo(e))),_=e=>{if(m)return;let t=i(e);n&&t<i(n)&&(t=i(n)),r&&t>i(r)&&(t=i(r)),s(t),h?.(t)};return{months:l,weeks:u,days:d,navStart:n,navEnd:r,previousMonth:f,nextMonth:p,goToMonth:_,goToDay:e=>{g(e)||_(e.date)}}}function jr(e,t,n,r){let i,a=0,o=!1;for(;a<e.length&&!o;){let s=e[a],c=t(s);!c[V.disabled]&&!c[V.hidden]&&!c[V.outside]&&(c[V.focused]||r?.isEqualTo(s)||n(s.date)||c[V.today])&&(i=s,o=!0),a++}return i||=e.find(e=>{let n=t(e);return!n[V.disabled]&&!n[V.hidden]&&!n[V.outside]}),i}function X(e,t,n=!1,r=Y){let{from:i,to:a}=e,{differenceInCalendarDays:o,isSameDay:s}=r;return i&&a?(o(a,i)<0&&([i,a]=[a,i]),o(t,i)>=+!!n&&o(a,t)>=+!!n):!n&&a?s(a,t):!n&&i?s(i,t):!1}function Mr(e){return!!(e&&typeof e==`object`&&`before`in e&&`after`in e)}function Nr(e){return!!(e&&typeof e==`object`&&`from`in e)}function Pr(e){return!!(e&&typeof e==`object`&&`after`in e)}function Fr(e){return!!(e&&typeof e==`object`&&`before`in e)}function Ir(e){return!!(e&&typeof e==`object`&&`dayOfWeek`in e)}function Lr(e,t){return Array.isArray(e)&&e.every(t.isDate)}function Z(e,t,n=Y){let r=Array.isArray(t)?t:[t],{isSameDay:i,differenceInCalendarDays:a,isAfter:o}=n;return r.some(t=>{if(typeof t==`boolean`)return t;if(n.isDate(t))return i(e,t);if(Lr(t,n))return t.includes(e);if(Nr(t))return X(t,e,!1,n);if(Ir(t))return Array.isArray(t.dayOfWeek)?t.dayOfWeek.includes(e.getDay()):t.dayOfWeek===e.getDay();if(Mr(t)){let n=a(t.before,e),r=a(t.after,e),i=n>0,s=r<0;return o(t.before,t.after)?s&&i:i||s}return Pr(t)?a(e,t.after)>0:Fr(t)?a(t.before,e)>0:typeof t==`function`&&t(e)})}function Rr(e,t,n,r,i,a,o){let{ISOWeek:s,broadcastCalendar:c}=a,{addDays:l,addMonths:u,addWeeks:d,addYears:f,endOfBroadcastWeek:p,endOfISOWeek:m,endOfWeek:h,max:g,min:_,startOfBroadcastWeek:v,startOfISOWeek:y,startOfWeek:b}=o,x={day:l,week:d,month:u,year:f,startOfWeek:e=>c?v(e,o):s?y(e):b(e),endOfWeek:e=>c?p(e,o):s?m(e):h(e)}[e](n,t===`after`?1:-1);return t===`before`&&r?x=g([r,x]):t===`after`&&i&&(x=_([i,x])),x}function zr(e,t,n,r,i,a,o,s=0){if(s>365)return;let c=Rr(e,t,n.date,r,i,a,o),l=!!(a.disabled&&Z(c,a.disabled,o)),u=!!(a.hidden&&Z(c,a.hidden,o)),d=new xr(c,c,o);return!l&&!u?d:zr(e,t,d,r,i,a,o,s+1)}function Br(e,t,n,r,i){let{autoFocus:a}=e,[o,s]=(0,z.useState)(),c=jr(t.days,n,r||(()=>!1),o),[l,u]=(0,z.useState)(a?c:void 0);return{isFocusTarget:e=>!!c?.isEqualTo(e),setFocused:u,focused:l,blur:()=>{s(l),u(void 0)},moveFocus:(n,r)=>{if(!l)return;let a=zr(n,r,l,t.navStart,t.navEnd,e,i);a&&(t.goToDay(a),u(a))}}}function Vr(e,t,n){let{disabled:r,hidden:i,modifiers:a,showOutsideDays:o,broadcastCalendar:s,today:c}=t,{isSameDay:l,isSameMonth:u,startOfMonth:d,isBefore:f,endOfMonth:p,isAfter:m}=n,h=t.startMonth&&d(t.startMonth),g=t.endMonth&&p(t.endMonth),_={[V.focused]:[],[V.outside]:[],[V.disabled]:[],[V.hidden]:[],[V.today]:[]},v={};for(let d of e){let{date:e,displayMonth:p}=d,y=!!(p&&!u(e,p)),b=!!(h&&f(e,h)),x=!!(g&&m(e,g)),S=!!(r&&Z(e,r,n)),C=!!(i&&Z(e,i,n))||b||x||!s&&!o&&y||s&&o===!1&&y,w=l(e,c??(t.timeZone?er.tz(t.timeZone):n.Date?new n.Date:new Date));y&&_.outside.push(d),S&&_.disabled.push(d),C&&_.hidden.push(d),w&&_.today.push(d),a&&Object.keys(a).forEach(t=>{let r=a?.[t];r&&Z(e,r,n)&&(v[t]?v[t].push(d):v[t]=[d])})}return e=>{let t={[V.focused]:!1,[V.disabled]:!1,[V.hidden]:!1,[V.outside]:!1,[V.today]:!1},n={};for(let n in _)t[n]=_[n].some(t=>t===e);for(let t in v)n[t]=v[t].some(t=>t===e);return{...t,...n}}}function Hr(e,t){let{selected:n,required:r,onSelect:i}=e,[a,o]=kr(n,i?n:void 0),s=i?n:a,{isSameDay:c}=t,l=e=>s?.some(t=>c(t,e))??!1,{min:u,max:d}=e;return{selected:s,select:(e,t,n)=>{let a=[...s??[]];if(l(e)){if(s?.length===u||r&&s?.length===1)return;a=s?.filter(t=>!c(t,e))}else a=s?.length===d?[e]:[...a,e];return i||o(a),i?.(a,e,t,n),a},isSelected:l}}function Ur(e,t,n=0,r=0,i=!1,a=Y){let{from:o,to:s}=t||{},{isSameDay:c,isAfter:l,isBefore:u}=a,d;if(!o&&!s)d={from:e,to:n>0?void 0:e};else if(o&&!s)d=c(o,e)?i?{from:o,to:void 0}:void 0:u(e,o)?{from:e,to:o}:{from:o,to:e};else if(o&&s)if(c(o,e)&&c(s,e))d=i?{from:o,to:s}:void 0;else if(c(o,e))d={from:o,to:n>0?void 0:e};else if(c(s,e))d={from:e,to:n>0?void 0:e};else if(u(e,o))d={from:e,to:s};else if(l(e,o))d={from:o,to:e};else if(l(e,s))d={from:o,to:e};else throw Error(`Invalid range`);if(d?.from&&d?.to){let t=a.differenceInCalendarDays(d.to,d.from);(r>0&&t>r||n>1&&t<n)&&(d={from:e,to:void 0})}return d}function Wr(e,t,n=Y){let r=Array.isArray(t)?t:[t],i=e.from,a=n.differenceInCalendarDays(e.to,e.from),o=Math.min(a,6);for(let e=0;e<=o;e++){if(r.includes(i.getDay()))return!0;i=n.addDays(i,1)}return!1}function Gr(e,t,n=Y){return X(e,t.from,!1,n)||X(e,t.to,!1,n)||X(t,e.from,!1,n)||X(t,e.to,!1,n)}function Kr(e,t,n=Y){let r=Array.isArray(t)?t:[t];if(r.filter(e=>typeof e!=`function`).some(t=>typeof t==`boolean`?t:n.isDate(t)?X(e,t,!1,n):Lr(t,n)?t.some(t=>X(e,t,!1,n)):Nr(t)?t.from&&t.to?Gr(e,{from:t.from,to:t.to},n):!1:Ir(t)?Wr(e,t.dayOfWeek,n):Mr(t)?n.isAfter(t.before,t.after)?Gr(e,{from:n.addDays(t.after,1),to:n.addDays(t.before,-1)},n):Z(e.from,t,n)||Z(e.to,t,n):Pr(t)||Fr(t)?Z(e.from,t,n)||Z(e.to,t,n):!1))return!0;let i=r.filter(e=>typeof e==`function`);if(i.length){let t=e.from,r=n.differenceInCalendarDays(e.to,e.from);for(let e=0;e<=r;e++){if(i.some(e=>e(t)))return!0;t=n.addDays(t,1)}}return!1}function qr(e,t){let{disabled:n,excludeDisabled:r,selected:i,required:a,onSelect:o}=e,[s,c]=kr(i,o?i:void 0),l=o?i:s;return{selected:l,select:(i,s,u)=>{let{min:d,max:f}=e,p=i?Ur(i,l,d,f,a,t):void 0;return r&&n&&p?.from&&p.to&&Kr({from:p.from,to:p.to},n,t)&&(p.from=i,p.to=void 0),o||c(p),o?.(p,i,s,u),p},isSelected:e=>l&&X(l,e,!1,t)}}function Jr(e,t){let{selected:n,required:r,onSelect:i}=e,[a,o]=kr(n,i?n:void 0),s=i?n:a,{isSameDay:c}=t;return{selected:s,select:(e,t,n)=>{let a=e;return!r&&s&&s&&c(e,s)&&(a=void 0),i||o(a),i?.(a,e,t,n),a},isSelected:e=>s?c(s,e):!1}}function Yr(e,t){let n=Jr(e,t),r=Hr(e,t),i=qr(e,t);switch(e.mode){case`single`:return n;case`multiple`:return r;case`range`:return i;default:return}}function Xr(e){let{components:t,formatters:n,labels:r,dateLib:i,locale:a,classNames:o}=(0,z.useMemo)(()=>{let t={...dt,...e.locale};return{dateLib:new J({locale:t,weekStartsOn:e.broadcastCalendar?1:e.weekStartsOn,firstWeekContainsDate:e.firstWeekContainsDate,useAdditionalWeekYearTokens:e.useAdditionalWeekYearTokens,useAdditionalDayOfYearTokens:e.useAdditionalDayOfYearTokens},e.dateLib),components:Dn(e.components),formatters:Bn(e.formatters),labels:{...gr,...e.labels},locale:t,classNames:{...kn(),...e.classNames}}},[e.classNames,e.components,e.dateLib,e.firstWeekContainsDate,e.formatters,e.labels,e.locale,e.useAdditionalDayOfYearTokens,e.useAdditionalWeekYearTokens,e.weekStartsOn,e.broadcastCalendar]),{captionLayout:s,mode:c,onDayBlur:l,onDayClick:u,onDayFocus:d,onDayKeyDown:f,onDayMouseEnter:p,onDayMouseLeave:m,onNextClick:h,onPrevClick:g,showWeekNumber:_,styles:v}=e,{formatCaption:y,formatDay:b,formatMonthDropdown:x,formatWeekNumber:S,formatWeekNumberHeader:C,formatWeekdayName:w,formatYearDropdown:T}=n,E=Ar(e,i),{days:D,months:ee,navStart:O,navEnd:te,previousMonth:k,nextMonth:A,goToMonth:j}=E,M=Vr(D,e,i),{isSelected:N,select:P,selected:F}=Yr(e,i)??{},{blur:I,focused:ne,isFocusTarget:re,moveFocus:ie,setFocused:L}=Br(e,E,M,N??(()=>!1),i),{labelDayButton:ae,labelGridcell:oe,labelGrid:se,labelMonthDropdown:R,labelNav:ce,labelWeekday:le,labelWeekNumber:ue,labelWeekNumberHeader:de,labelYearDropdown:fe}=r,pe=(0,z.useMemo)(()=>tr(i,e.ISOWeek,e.timeZone),[i,e.ISOWeek,e.timeZone]),me=c!==void 0||u!==void 0,he=(0,z.useCallback)(()=>{k&&(j(k),g?.(k))},[k,j,g]),ge=(0,z.useCallback)(()=>{A&&(j(A),h?.(A))},[j,A,h]),_e=(0,z.useCallback)((e,t)=>n=>{n.preventDefault(),n.stopPropagation(),L(e),P?.(e.date,t,n),u?.(e.date,t,n)},[P,u,L]),ve=(0,z.useCallback)((e,t)=>n=>{L(e),d?.(e.date,t,n)},[d,L]),ye=(0,z.useCallback)((e,t)=>n=>{I(),l?.(e.date,t,n)},[I,l]),be=(0,z.useCallback)((t,n)=>r=>{let i={ArrowLeft:[`day`,e.dir===`rtl`?`after`:`before`],ArrowRight:[`day`,e.dir===`rtl`?`before`:`after`],ArrowDown:[`week`,`after`],ArrowUp:[`week`,`before`],PageUp:[r.shiftKey?`year`:`month`,`before`],PageDown:[r.shiftKey?`year`:`month`,`after`],Home:[`startOfWeek`,`before`],End:[`endOfWeek`,`after`]};if(i[r.key]){r.preventDefault(),r.stopPropagation();let[e,t]=i[r.key];ie(e,t)}f?.(t.date,n,r)},[ie,f,e.dir]),xe=(0,z.useCallback)((e,t)=>n=>{p?.(e.date,t,n)},[p]),Se=(0,z.useCallback)((e,t)=>n=>{m?.(e.date,t,n)},[m]),Ce=(0,z.useCallback)(e=>t=>{let n=Number(t.target.value),r=i.setMonth(i.startOfMonth(e),n);j(r)},[i,j]),we=(0,z.useCallback)(e=>t=>{let n=Number(t.target.value),r=i.setYear(i.startOfMonth(e),n);j(r)},[i,j]),{className:Te,style:Ee}=(0,z.useMemo)(()=>({className:[o[B.Root],e.className].filter(Boolean).join(` `),style:{...v?.[B.Root],...e.style}}),[o,e.className,e.style,v]),U=On(e),W={dayPickerProps:e,selected:F,select:P,isSelected:N,months:ee,nextMonth:A,previousMonth:k,goToMonth:j,getModifiers:M,components:t,classNames:o,styles:v,labels:r,formatters:n};return z.createElement(un.Provider,{value:W},z.createElement(t.Root,{className:Te,style:Ee,dir:e.dir,id:e.id,lang:e.lang,nonce:e.nonce,title:e.title,role:e.role,"aria-label":e[`aria-label`],...U},z.createElement(t.Months,{className:o[B.Months],style:v?.[B.Months]},!e.hideNavigation&&z.createElement(t.Nav,{className:o[B.Nav],style:v?.[B.Nav],"aria-label":ce(),onPreviousClick:he,onNextClick:ge,previousMonth:k,nextMonth:A}),ee.map((r,l)=>{let u=Vn(r.date,O,te,n,i),d=nr(O,te,n,i);return z.createElement(t.Month,{className:o[B.Month],style:v?.[B.Month],key:l,displayIndex:l,calendarMonth:r},z.createElement(t.MonthCaption,{className:o[B.MonthCaption],style:v?.[B.MonthCaption],calendarMonth:r,displayIndex:l},s?.startsWith(`dropdown`)?z.createElement(t.DropdownNav,{className:o[B.Dropdowns],style:v?.[B.Dropdowns]},s===`dropdown`||s===`dropdown-months`?z.createElement(t.MonthsDropdown,{className:o[B.MonthsDropdown],"aria-label":R(),classNames:o,components:t,disabled:!!e.disableNavigation,onChange:Ce(r.date),options:u,style:v?.[B.Dropdown],value:r.date.getMonth()}):z.createElement(`span`,{role:`status`,"aria-live":`polite`},x(r.date.getMonth(),a)),s===`dropdown`||s===`dropdown-years`?z.createElement(t.YearsDropdown,{className:o[B.YearsDropdown],"aria-label":fe(i.options),classNames:o,components:t,disabled:!!e.disableNavigation,onChange:we(r.date),options:d,style:v?.[B.Dropdown],value:r.date.getFullYear()}):z.createElement(`span`,{role:`status`,"aria-live":`polite`},T(r.date.getFullYear()))):z.createElement(t.CaptionLabel,{className:o[B.CaptionLabel],role:`status`,"aria-live":`polite`},y(r.date,i.options,i))),z.createElement(t.MonthGrid,{role:`grid`,"aria-multiselectable":c===`multiple`||c===`range`,"aria-label":se(r.date,i.options,i)||void 0,className:o[B.MonthGrid],style:v?.[B.MonthGrid]},!e.hideWeekdays&&z.createElement(t.Weekdays,{className:o[B.Weekdays],style:v?.[B.Weekdays]},_&&z.createElement(t.WeekNumberHeader,{"aria-label":de(i.options),className:o[B.WeekNumberHeader],style:v?.[B.WeekNumberHeader],scope:`col`},C()),pe.map((e,n)=>z.createElement(t.Weekday,{"aria-label":le(e,i.options,i),className:o[B.Weekday],key:n,style:v?.[B.Weekday],scope:`col`},w(e,i.options,i)))),z.createElement(t.Weeks,{className:o[B.Weeks],style:v?.[B.Weeks]},r.weeks.map((n,r)=>z.createElement(t.Week,{className:o[B.Week],key:n.weekNumber,style:v?.[B.Week],week:n},_&&z.createElement(t.WeekNumber,{week:n,style:v?.[B.WeekNumber],"aria-label":ue(n.weekNumber,{locale:a}),className:o[B.WeekNumber],scope:`row`,role:`rowheader`},S(n.weekNumber)),n.days.map(n=>{let{date:r}=n,a=M(n);if(a[V.focused]=!a.hidden&&!!ne?.isEqualTo(n),a[H.selected]=!a.disabled&&(N?.(r)||a.selected),Nr(F)){let{from:e,to:t}=F;a[H.range_start]=!!(e&&t&&i.isSameDay(r,e)),a[H.range_end]=!!(e&&t&&i.isSameDay(r,t)),a[H.range_middle]=X(F,r,!0,i)}let s=Hn(a,v,e.modifiersStyles),c=Xt(a,o,e.modifiersClassNames),l=!me&&!a.hidden?oe(r,a,i.options,i):void 0;return z.createElement(t.Day,{key:`${i.format(r,`yyyy-MM-dd`)}_${i.format(n.displayMonth,`yyyy-MM`)}`,day:n,modifiers:a,className:c.join(` `),style:s,role:`gridcell`,"aria-selected":a.selected||void 0,"aria-label":l,"data-day":i.format(r,`yyyy-MM-dd`),"data-month":n.outside?i.format(r,`yyyy-MM`):void 0,"data-selected":a.selected||void 0,"data-disabled":a.disabled||void 0,"data-hidden":a.hidden||void 0,"data-outside":n.outside||void 0,"data-focused":a.focused||void 0,"data-today":a.today||void 0},!a.hidden&&me?z.createElement(t.DayButton,{className:o[B.DayButton],style:v?.[B.DayButton],type:`button`,day:n,modifiers:a,disabled:a.disabled||void 0,tabIndex:re(n)?0:-1,"aria-label":ae(r,a,i.options,i),onClick:_e(n,a),onBlur:ye(n,a),onFocus:ve(n,a),onKeyDown:be(n,a),onMouseEnter:xe(n,a),onMouseLeave:Se(n,a)},b(r,i.options,i)):!a.hidden&&b(n.date,i.options,i))}))))))})),e.footer&&z.createElement(t.Footer,{className:o[B.Footer],style:v?.[B.Footer],role:`status`,"aria-live":`polite`},e.footer)))}function Zr(e){let t=e=>typeof window<`u`&&window.matchMedia(e).matches,[n,r]=(0,z.useState)(t(e));function i(){r(t(e))}return(0,z.useEffect)(()=>{let t=window.matchMedia(e);return i(),t.addListener?t.addListener(i):t.addEventListener(`change`,i),()=>{t.removeListener?t.removeListener(i):t.removeEventListener(`change`,i)}},[e]),n}var Qr=`data:image/svg+xml,%3csvg%20xmlns='http://www.w3.org/2000/svg'%20width='48'%20height='48'%20viewBox='0%20-960%20960%20960'%3e%3cpath%20d='M686-450H190q-13%200-21.5-8.5T160-480q0-13%208.5-21.5T190-510h496L459-737q-9-9-9-21t9-21q9-9%2021-9t21%209l278%20278q5%205%207%2010t2%2011q0%206-2%2011t-7%2010L501-181q-9%209-21%209t-21-9q-9-9-9-21t9-21l227-227Z'/%3e%3c/svg%3e`;function $r(e,t){t===void 0&&(t={});var n=t.insertAt;if(!(!e||typeof document>`u`)){var r=document.head||document.getElementsByTagName(`head`)[0],i=document.createElement(`style`);i.type=`text/css`,n===`top`&&r.firstChild?r.insertBefore(i,r.firstChild):r.appendChild(i),i.styleSheet?i.styleSheet.cssText=e:i.appendChild(document.createTextNode(e))}}var ei=`.DatePicker-module_u1-date-picker__Lxr6q {
  position: relative;
  display: inline-block;
}

.DatePicker-module_u1-date-picker__button__0BZ4u {
  display: flex;
  align-items: center;
  gap: 0.25rem;
}

.DatePicker-module_u1-date-picker__button__0BZ4u>button>div {
  padding-top: 0.125rem;
}

.DatePicker-module_u1-date-picker__desktop-wrapper__ewWDn {
  display: none;
  max-width: 95vw;
}

@media (min-width: 640px) {

  .DatePicker-module_u1-date-picker__desktop-wrapper__ewWDn {
    display: block;
  }
}

.DatePicker-module_u1-date-picker__mobile-wrapper__CTZvB {
  display: block;
}

@media (min-width: 640px) {

  .DatePicker-module_u1-date-picker__mobile-wrapper__CTZvB {
    display: none;
  }
}

.DatePicker-module_u1-date-picker__modal__no0K6 {
  display: flex;
  width: fit-content;
  border-radius: 0.5rem;
  --tw-bg-opacity: 1;
  background-color: rgb(255 255 255 / var(--tw-bg-opacity));
  --tw-shadow: 0 20px 25px -5px rgb(0 0 0 / 0.1), 0 8px 10px -6px rgb(0 0 0 / 0.1);
  --tw-shadow-colored: 0 20px 25px -5px var(--tw-shadow-color), 0 8px 10px -6px var(--tw-shadow-color);
  box-shadow: var(--tw-ring-offset-shadow, 0 0 #0000), var(--tw-ring-shadow, 0 0 #0000), var(--tw-shadow);
}
.dark .DatePicker-module_u1-date-picker__modal__no0K6 {
  --tw-bg-opacity: 1;
  background-color: rgb(38 43 68 / var(--tw-bg-opacity));
  --tw-text-opacity: 1;
  color: rgb(255 255 255 / var(--tw-text-opacity));
}

.DatePicker-module_u1-date-picker__mobile-modal__Bn-vK {
  position: fixed;
  inset: 0rem;
  z-index: 50;
  display: flex;
  height: 100%;
  width: 100%;
  flex-direction: column;
  --tw-bg-opacity: 1;
  background-color: rgb(255 255 255 / var(--tw-bg-opacity));
}
.dark .DatePicker-module_u1-date-picker__mobile-modal__Bn-vK {
  --tw-bg-opacity: 1;
  background-color: rgb(38 43 68 / var(--tw-bg-opacity));
  --tw-text-opacity: 1;
  color: rgb(255 255 255 / var(--tw-text-opacity));
}

.DatePicker-module_u1-date-picker__mobile-content__6Efkr {
  display: flex;
  min-height: 0rem;
  flex: 1 1 0%;
  flex-direction: column;
  overflow: hidden;
}

.DatePicker-module_u1-date-picker__mobile-sidebar-wrapper__epZ5I {
  display: flex;
  flex-shrink: 0;
  flex-direction: column;
  gap: 0.5rem;
  border-top-width: 1px;
  border-style: solid;
  --tw-border-opacity: 1;
  border-color: rgb(208 213 221 / var(--tw-border-opacity));
  padding: 1rem;
  padding-bottom: 0.75rem;
}

.DatePicker-module_u1-date-picker__mobile-quick-select__ka1-1 {
  display: flex;
  flex-direction: row;
  gap: 0.5rem;
  overflow-x: auto;
  padding-bottom: 0.25rem;
  scrollbar-color: lightgrey transparent;
}
.dark .DatePicker-module_u1-date-picker__mobile-quick-select__ka1-1 {
  --tw-border-opacity: 1;
  border-color: rgb(73 76 93 / var(--tw-border-opacity));
}

.DatePicker-module_u1-date-picker__mobile-calendar__BmIbk {
  display: flex;
  min-height: 0rem;
  flex: 1 1 0%;
  align-items: flex-start;
  justify-content: center;
  overflow-y: auto;
  padding-left: 0.5rem;
  padding-right: 0.5rem;
}

.DatePicker-module_u1-date-picker__mobile-actions__0BWvV {
  display: flex;
  flex-direction: row;
  gap: 0.75rem;
  border-top-width: 1px;
  border-style: solid;
  --tw-border-opacity: 1;
  border-color: rgb(208 213 221 / var(--tw-border-opacity));
  padding-left: 1rem;
  padding-right: 1rem;
  padding-top: 1rem;
  padding-bottom: 1rem;
}
.dark .DatePicker-module_u1-date-picker__mobile-actions__0BWvV {
  --tw-border-opacity: 1;
  border-color: rgb(73 76 93 / var(--tw-border-opacity));
}

.DatePicker-module_u1-date-picker__header__FtoBv {
  display: flex;
  align-items: center;
  justify-content: space-between;
  border-bottom-width: 1px;
  border-style: solid;
  --tw-border-opacity: 1;
  border-color: rgb(208 213 221 / var(--tw-border-opacity));
  padding-left: 1.5rem;
  padding-right: 1.5rem;
  padding-top: 1rem;
  padding-bottom: 1rem;
}
.dark .DatePicker-module_u1-date-picker__header__FtoBv {
  --tw-border-opacity: 1;
  border-color: rgb(73 76 93 / var(--tw-border-opacity));
}

.DatePicker-module_u1-date-picker__title__VZLK5 {
  margin: 0rem;
  font-size: 1.125rem;
  line-height: 1.75rem;
  font-weight: 600;
}

.DatePicker-module_u1-date-picker__footer__iFZNn {
  width: 100%;
  border-top-width: 1px;
  border-style: solid;
  --tw-border-opacity: 1;
  border-color: rgb(208 213 221 / var(--tw-border-opacity));
  grid-column: span 12 / span 12;
  grid-column-start: 1;
  grid-row-start: 2;
}
.dark .DatePicker-module_u1-date-picker__footer__iFZNn {
  --tw-border-opacity: 1;
  border-color: rgb(73 76 93 / var(--tw-border-opacity));
}
.DatePicker-module_u1-date-picker__content__U4t3w:has(.DatePicker-module_u1-date-picker__sidebar__LgGKM) .DatePicker-module_u1-date-picker__footer__iFZNn {
  grid-column: span 9 / span 9;
  grid-column-start: 4;
}

.DatePicker-module_u1-date-picker__footer-content__gPpX0 {
  display: flex;
  flex-direction: column;
  gap: 0.75rem;
  padding-left: 1.5rem;
  padding-right: 1.5rem;
  padding-top: 1rem;
  padding-bottom: 1rem;
}

@media (min-width: 768px) {

  .DatePicker-module_u1-date-picker__footer-content__gPpX0 {
    flex-direction: row;
    align-items: center;
    justify-content: space-between;
  }
}

.DatePicker-module_u1-date-picker__content__U4t3w {
  display: grid;
  min-height: fit-content;
  min-width: fit-content;
  grid-template-columns: repeat(12, minmax(0, 1fr));
  grid-template-rows: 1fr auto;
}

@media (min-width: 768px) {

  .DatePicker-module_u1-date-picker__apply-button-wrapper__Ejzwi {
    max-width: 32rem;
  }
}

.DatePicker-module_u1-date-picker__sidebar__LgGKM {
  display: none;
  max-width: 200px;
  flex-direction: column;
  gap: 0.5rem;
  border-right-width: 1px;
  border-style: solid;
  --tw-border-opacity: 1;
  border-color: rgb(208 213 221 / var(--tw-border-opacity));
  padding-left: 1rem;
  padding-right: 1rem;
  padding-top: 1rem;
  padding-bottom: 1rem;
}

@media (min-width: 640px) {

  .DatePicker-module_u1-date-picker__sidebar__LgGKM {
    display: flex;
  }
}

.DatePicker-module_u1-date-picker__sidebar__LgGKM {
  grid-column: span 3 / span 3;
  grid-column-start: 1;
  grid-row: span 2 / span 2;
}
.dark .DatePicker-module_u1-date-picker__sidebar__LgGKM {
  --tw-border-opacity: 1;
  border-color: rgb(73 76 93 / var(--tw-border-opacity));
}
.DatePicker-module_u1-date-picker__sidebar__LgGKM button {
  max-width: 100%;
  overflow: hidden;
  text-overflow: ellipsis;
  white-space: nowrap;
}

.DatePicker-module_u1-date-picker__custom-button__SHiJ6 {
  display: flex;
  flex-direction: column;
  gap: 0.25rem;
}

.DatePicker-module_u1-date-picker__button-subtext__WDt6G {
  font-size: 0.75rem;
  line-height: 1rem;
  --tw-text-opacity: 1;
  color: rgb(113 122 136 / var(--tw-text-opacity));
}
.dark .DatePicker-module_u1-date-picker__button-subtext__WDt6G {
  --tw-text-opacity: 1;
  color: rgb(160 166 177 / var(--tw-text-opacity));
}

.DatePicker-module_u1-date-picker__calendar-wrapper__E-xwT {
  display: flex;
  width: 100%;
  flex-direction: column;
  align-items: center;
  justify-content: flex-start;
  grid-column: span 12 / span 12;
  grid-column-start: 1;
  grid-row-start: 1;
}
.DatePicker-module_u1-date-picker__content__U4t3w:has(.DatePicker-module_u1-date-picker__sidebar__LgGKM) .DatePicker-module_u1-date-picker__calendar-wrapper__E-xwT {
  grid-column: span 9 / span 9;
  grid-column-start: 4;
}

.DatePicker-module_u1-date-picker__calendar__z5uiD {
  position: relative;
  width: 100%;
  padding: 0.75rem;
}

@media (min-width: 640px) {

  .DatePicker-module_u1-date-picker__calendar__z5uiD {
    padding: 1rem;
  }
}
@media (max-width: 640px) {
  .DatePicker-module_u1-date-picker__calendar__z5uiD {
    padding: 1rem 0.5rem;
  }
}

.DatePicker-module_u1-date-picker__input-group__T8qTX {
  display: flex;
  flex-direction: row;
  align-items: center;
  justify-content: center;
  gap: 0.25rem;
}

.DatePicker-module_u1-date-picker__input-separator__IEEs2 {
  display: flex;
  align-items: center;
  justify-content: center;
  --tw-text-opacity: 1;
  color: rgb(28 31 53 / var(--tw-text-opacity));
}
.dark .DatePicker-module_u1-date-picker__input-separator__IEEs2 {
  --tw-text-opacity: 1;
  color: rgb(160 166 177 / var(--tw-text-opacity));
}

.DatePicker-module_u1-date-picker__error__RIdfV {
  grid-column: span 5 / span 5;
  margin-top: 0.5rem;
  text-align: center;
  font-size: 0.875rem;
  line-height: 1.25rem;
  --tw-text-opacity: 1;
  color: rgb(249 45 79 / var(--tw-text-opacity));
}
.dark .DatePicker-module_u1-date-picker__error__RIdfV {
  --tw-text-opacity: 1;
  color: rgb(250 133 152 / var(--tw-text-opacity));
}

.DatePicker-module_u1-date-picker__root__YUCGw {
  position: relative;
  width: 100%;
}

.DatePicker-module_u1-date-picker__months__XJ--B {
  position: relative;
  display: flex;
  justify-content: center;
  gap: 1rem;
}

.DatePicker-module_u1-date-picker__month__kli0l {
  position: relative;
  display: flex;
  flex: 1 1 0%;
  flex-direction: column;
  min-width: 0;
}

.DatePicker-module_u1-date-picker__month-caption__0-D8L {
  margin-bottom: 1rem;
  display: flex;
  align-items: center;
  justify-content: center;
  font-size: 1.125rem;
  line-height: 1.75rem;
  font-weight: 500;
  --tw-text-opacity: 1;
  color: rgb(28 31 53 / var(--tw-text-opacity));
  height: var(--cell-size);
  padding-left: var(--cell-size);
  padding-right: var(--cell-size);
}
.dark .DatePicker-module_u1-date-picker__month-caption__0-D8L {
  --tw-text-opacity: 1;
  color: rgb(255 255 255 / var(--tw-text-opacity));
}
@media (max-width: 640px) {
  .DatePicker-module_u1-date-picker__month-caption__0-D8L {
    margin-bottom: 1rem;
    font-size: 1.125rem;
  }
}

.DatePicker-module_u1-date-picker__nav__f11d- {
  position: absolute;
  left: 0rem;
  right: 0rem;
  top: 0rem;
  z-index: 10;
  display: flex;
  width: 100%;
  align-items: center;
  justify-content: space-between;
}

.DatePicker-module_u1-date-picker__nav-button__JVRC4 {
  fill: #1C1F35;
  padding: 0rem;
  height: var(--cell-size);
  width: var(--cell-size);
}
.dark .DatePicker-module_u1-date-picker__nav-button__JVRC4 {
  fill: #FFFFFF;
}
.DatePicker-module_u1-date-picker__nav-button__JVRC4:disabled {
  cursor: not-allowed;
  fill: #888F9D;
}
.dark .DatePicker-module_u1-date-picker__nav-button__JVRC4:disabled {
  fill: #A0A6B1;
}

.DatePicker-module_u1-date-picker__weeks__CmFr9 {
  display: flex;
  flex-direction: column;
  gap: 0.75rem;
  padding-top: 0.25rem;
}

.DatePicker-module_u1-date-picker__weekdays__PaJDU {
  display: flex;
  width: 100%;
  --tw-text-opacity: 1;
  color: rgb(92 95 111 / var(--tw-text-opacity));
}

.DatePicker-module_u1-date-picker__weekday__SxfdM {
  display: flex;
  flex: 1 1 0%;
  align-items: center;
  justify-content: center;
  text-align: center;
  font-size: 0.875rem;
  line-height: 1.25rem;
  font-weight: 500;
  --tw-text-opacity: 1;
  color: rgb(113 122 136 / var(--tw-text-opacity));
}
.dark .DatePicker-module_u1-date-picker__weekday__SxfdM {
  --tw-text-opacity: 1;
  color: rgb(160 166 177 / var(--tw-text-opacity));
}

.DatePicker-module_u1-date-picker__week__drTI3 {
  display: flex;
  width: 100%;
}

.DatePicker-module_u1-date-picker__day__8v1DG {
  position: relative;
  flex: 1 1 0%;
  padding: 0rem;
  text-align: center;
  aspect-ratio: 1;
}

.DatePicker-module_u1-date-picker__day-button__1mrd2 {
  display: flex;
  height: 100%;
  width: 100%;
  align-items: center;
  justify-content: center;
  font-size: 0.875rem;
  line-height: 1.25rem;
  font-weight: 400;
  border-radius: 0.375rem;
  border-width: 1px;
  border-style: solid;
  border-color: transparent;
  transition-property: color, background-color, border-color, text-decoration-color, fill, stroke;
  transition-timing-function: cubic-bezier(0.4, 0, 0.2, 1);
  transition-duration: 150ms;
}

.DatePicker-module_u1-date-picker__day-button__1mrd2:hover {
  --tw-border-opacity: 1;
  border-color: rgb(28 31 53 / var(--tw-border-opacity));
}

.DatePicker-module_u1-date-picker__day-button__1mrd2:focus {
  outline: 2px solid transparent;
  outline-offset: 2px;
  --tw-ring-offset-shadow: var(--tw-ring-inset) 0 0 0 var(--tw-ring-offset-width) var(--tw-ring-offset-color);
  --tw-ring-shadow: var(--tw-ring-inset) 0 0 0 calc(2px + var(--tw-ring-offset-width)) var(--tw-ring-color);
  box-shadow: var(--tw-ring-offset-shadow), var(--tw-ring-shadow), var(--tw-shadow, 0 0 #0000);
  --tw-ring-opacity: 1;
  --tw-ring-color: rgb(134 163 249 / var(--tw-ring-opacity));
  --tw-ring-offset-width: 2px;
}
.dark .DatePicker-module_u1-date-picker__day-button__1mrd2:hover {
  --tw-border-opacity: 1;
  border-color: rgb(255 255 255 / var(--tw-border-opacity));
}

.DatePicker-module_u1-date-picker__today__3Pno2 {
  --tw-text-opacity: 1;
  color: rgb(249 34 163 / var(--tw-text-opacity));
}
.dark .DatePicker-module_u1-date-picker__today__3Pno2 {
  --tw-text-opacity: 1;
  color: rgb(242 140 205 / var(--tw-text-opacity));
}

.DatePicker-module_u1-date-picker__selected__wMDed .DatePicker-module_u1-date-picker__day-button__1mrd2 {
  border-radius: 0.375rem;
  --tw-bg-opacity: 1;
  background-color: rgb(239 243 251 / var(--tw-bg-opacity));
}
.dark .DatePicker-module_u1-date-picker__selected__wMDed .DatePicker-module_u1-date-picker__day-button__1mrd2 {
  --tw-bg-opacity: 1;
  background-color: rgb(134 163 249 / var(--tw-bg-opacity));
}
.DatePicker-module_u1-date-picker__selected__wMDed .DatePicker-module_u1-date-picker__day-button__1mrd2:hover {
  border-radius: 0.375rem;
  --tw-bg-opacity: 1;
  background-color: rgb(24 17 212 / var(--tw-bg-opacity));
}
.dark .DatePicker-module_u1-date-picker__selected__wMDed .DatePicker-module_u1-date-picker__day-button__1mrd2:hover {
  --tw-bg-opacity: 1;
  background-color: rgb(170 193 248 / var(--tw-bg-opacity));
}

.DatePicker-module_u1-date-picker__range-start__ApcYv .DatePicker-module_u1-date-picker__day-button__1mrd2 {
  border-top-left-radius: 0.375rem;
  border-bottom-left-radius: 0.375rem;
  --tw-bg-opacity: 1;
  background-color: rgb(63 58 252 / var(--tw-bg-opacity));
  --tw-text-opacity: 1;
  color: rgb(255 255 255 / var(--tw-text-opacity));
}
.dark .DatePicker-module_u1-date-picker__range-start__ApcYv .DatePicker-module_u1-date-picker__day-button__1mrd2 {
  --tw-bg-opacity: 1;
  background-color: rgb(134 163 249 / var(--tw-bg-opacity));
  --tw-text-opacity: 1;
  color: rgb(28 31 53 / var(--tw-text-opacity));
}
.DatePicker-module_u1-date-picker__range-start__ApcYv .DatePicker-module_u1-date-picker__day-button__1mrd2:hover {
  --tw-bg-opacity: 1;
  background-color: rgb(24 17 212 / var(--tw-bg-opacity));
}
.dark .DatePicker-module_u1-date-picker__range-start__ApcYv .DatePicker-module_u1-date-picker__day-button__1mrd2:hover {
  --tw-bg-opacity: 1;
  background-color: rgb(170 193 248 / var(--tw-bg-opacity));
}

.DatePicker-module_u1-date-picker__range-end__bInzf .DatePicker-module_u1-date-picker__day-button__1mrd2 {
  border-top-right-radius: 0.375rem;
  border-bottom-right-radius: 0.375rem;
  --tw-bg-opacity: 1;
  background-color: rgb(63 58 252 / var(--tw-bg-opacity));
  --tw-text-opacity: 1;
  color: rgb(255 255 255 / var(--tw-text-opacity));
}
.dark .DatePicker-module_u1-date-picker__range-end__bInzf .DatePicker-module_u1-date-picker__day-button__1mrd2 {
  --tw-bg-opacity: 1;
  background-color: rgb(134 163 249 / var(--tw-bg-opacity));
  --tw-text-opacity: 1;
  color: rgb(28 31 53 / var(--tw-text-opacity));
}
.DatePicker-module_u1-date-picker__range-end__bInzf .DatePicker-module_u1-date-picker__day-button__1mrd2:hover {
  --tw-bg-opacity: 1;
  background-color: rgb(24 17 212 / var(--tw-bg-opacity));
}
.dark .DatePicker-module_u1-date-picker__range-end__bInzf .DatePicker-module_u1-date-picker__day-button__1mrd2:hover {
  --tw-bg-opacity: 1;
  background-color: rgb(170 193 248 / var(--tw-bg-opacity));
}

.DatePicker-module_u1-date-picker__range-middle__YRsI1 .DatePicker-module_u1-date-picker__day-button__1mrd2 {
  border-radius: 0px;
  --tw-bg-opacity: 1;
  background-color: rgb(239 243 251 / var(--tw-bg-opacity));
}
.dark .DatePicker-module_u1-date-picker__range-middle__YRsI1 .DatePicker-module_u1-date-picker__day-button__1mrd2 {
  --tw-bg-opacity: 1;
  background-color: rgb(54 54 78 / var(--tw-bg-opacity));
}
.DatePicker-module_u1-date-picker__range-middle__YRsI1 .DatePicker-module_u1-date-picker__day-button__1mrd2:hover {
  --tw-bg-opacity: 1;
  background-color: rgb(184 189 200 / var(--tw-bg-opacity));
}
.dark .DatePicker-module_u1-date-picker__range-middle__YRsI1 .DatePicker-module_u1-date-picker__day-button__1mrd2:hover {
  --tw-bg-opacity: 1;
  background-color: rgb(73 76 93 / var(--tw-bg-opacity));
}

.DatePicker-module_u1-date-picker__disabled__NWaDs .DatePicker-module_u1-date-picker__day-button__1mrd2 {
  --tw-text-opacity: 1;
  color: rgb(136 143 157 / var(--tw-text-opacity));
}

.DatePicker-module_u1-date-picker__disabled__NWaDs .DatePicker-module_u1-date-picker__day-button__1mrd2:hover {
  background-color: transparent;
}

.DatePicker-module_u1-date-picker__disabled__NWaDs .DatePicker-module_u1-date-picker__day-button__1mrd2 {
  cursor: not-allowed;
}
.dark .DatePicker-module_u1-date-picker__disabled__NWaDs .DatePicker-module_u1-date-picker__day-button__1mrd2 {
  --tw-text-opacity: 1;
  color: rgb(92 95 111 / var(--tw-text-opacity));
}

.DatePicker-module_u1-date-picker__outside__34yHJ .DatePicker-module_u1-date-picker__day-button__1mrd2 {
  --tw-text-opacity: 1;
  color: rgb(136 143 157 / var(--tw-text-opacity));
}
.dark .DatePicker-module_u1-date-picker__outside__34yHJ .DatePicker-module_u1-date-picker__day-button__1mrd2 {
  --tw-text-opacity: 1;
  color: rgb(113 122 136 / var(--tw-text-opacity));
}`,Q={"u1-date-picker":`DatePicker-module_u1-date-picker__Lxr6q`,"u1-date-picker__button":`DatePicker-module_u1-date-picker__button__0BZ4u`,"u1-date-picker__desktop-wrapper":`DatePicker-module_u1-date-picker__desktop-wrapper__ewWDn`,"u1-date-picker__mobile-wrapper":`DatePicker-module_u1-date-picker__mobile-wrapper__CTZvB`,"u1-date-picker__modal":`DatePicker-module_u1-date-picker__modal__no0K6`,"u1-date-picker__mobile-modal":`DatePicker-module_u1-date-picker__mobile-modal__Bn-vK`,"u1-date-picker__mobile-content":`DatePicker-module_u1-date-picker__mobile-content__6Efkr`,"u1-date-picker__mobile-sidebar-wrapper":`DatePicker-module_u1-date-picker__mobile-sidebar-wrapper__epZ5I`,"u1-date-picker__mobile-quick-select":`DatePicker-module_u1-date-picker__mobile-quick-select__ka1-1`,"u1-date-picker__mobile-calendar":`DatePicker-module_u1-date-picker__mobile-calendar__BmIbk`,"u1-date-picker__mobile-actions":`DatePicker-module_u1-date-picker__mobile-actions__0BWvV`,"u1-date-picker__header":`DatePicker-module_u1-date-picker__header__FtoBv`,"u1-date-picker__title":`DatePicker-module_u1-date-picker__title__VZLK5`,"u1-date-picker__footer":`DatePicker-module_u1-date-picker__footer__iFZNn`,"u1-date-picker__content":`DatePicker-module_u1-date-picker__content__U4t3w`,"u1-date-picker__sidebar":`DatePicker-module_u1-date-picker__sidebar__LgGKM`,"u1-date-picker__footer-content":`DatePicker-module_u1-date-picker__footer-content__gPpX0`,"u1-date-picker__apply-button-wrapper":`DatePicker-module_u1-date-picker__apply-button-wrapper__Ejzwi`,"u1-date-picker__custom-button":`DatePicker-module_u1-date-picker__custom-button__SHiJ6`,"u1-date-picker__button-subtext":`DatePicker-module_u1-date-picker__button-subtext__WDt6G`,"u1-date-picker__calendar-wrapper":`DatePicker-module_u1-date-picker__calendar-wrapper__E-xwT`,"u1-date-picker__calendar":`DatePicker-module_u1-date-picker__calendar__z5uiD`,"u1-date-picker__input-group":`DatePicker-module_u1-date-picker__input-group__T8qTX`,"u1-date-picker__input-separator":`DatePicker-module_u1-date-picker__input-separator__IEEs2`,"u1-date-picker__error":`DatePicker-module_u1-date-picker__error__RIdfV`,"u1-date-picker__root":`DatePicker-module_u1-date-picker__root__YUCGw`,"u1-date-picker__months":`DatePicker-module_u1-date-picker__months__XJ--B`,"u1-date-picker__month":`DatePicker-module_u1-date-picker__month__kli0l`,"u1-date-picker__month-caption":`DatePicker-module_u1-date-picker__month-caption__0-D8L`,"u1-date-picker__nav":`DatePicker-module_u1-date-picker__nav__f11d-`,"u1-date-picker__nav-button":`DatePicker-module_u1-date-picker__nav-button__JVRC4`,"u1-date-picker__weeks":`DatePicker-module_u1-date-picker__weeks__CmFr9`,"u1-date-picker__weekdays":`DatePicker-module_u1-date-picker__weekdays__PaJDU`,"u1-date-picker__weekday":`DatePicker-module_u1-date-picker__weekday__SxfdM`,"u1-date-picker__week":`DatePicker-module_u1-date-picker__week__drTI3`,"u1-date-picker__day":`DatePicker-module_u1-date-picker__day__8v1DG`,"u1-date-picker__day-button":`DatePicker-module_u1-date-picker__day-button__1mrd2`,"u1-date-picker__today":`DatePicker-module_u1-date-picker__today__3Pno2`,"u1-date-picker__selected":`DatePicker-module_u1-date-picker__selected__wMDed`,"u1-date-picker__range-start":`DatePicker-module_u1-date-picker__range-start__ApcYv`,"u1-date-picker__range-end":`DatePicker-module_u1-date-picker__range-end__bInzf`,"u1-date-picker__range-middle":`DatePicker-module_u1-date-picker__range-middle__YRsI1`,"u1-date-picker__disabled":`DatePicker-module_u1-date-picker__disabled__NWaDs`,"u1-date-picker__outside":`DatePicker-module_u1-date-picker__outside__34yHJ`};$r(ei);var ti=({label:e,isSelected:t,onClick:n,testId:r})=>z.createElement(o,{variation:t?E.Secondary:E.Tertiary,fill:!0,small:!0,onClick:n,testId:r},e),ni=({draftRange:e,onRangeChange:t,month:n,onMonthChange:r,startInput:i,endInput:a,onStartChange:s,onEndChange:c,onQuickSelect:l,quickSelectRanges:d,isRangeSelected:f,showQuickSelect:p,sortedCustomButtons:m,shouldShowSidebar:h,onApply:g,isDateRangeValid:v,isFutureDate:y,hasInvalidFutureDate:S,minDate:C,maxDate:T,testId:D})=>{let ee=Zr(`(min-width: 768px)`),O=[{label:`This month`,range:d.thisMonth,id:`this-month`},{label:`Last month`,range:d.lastFullMonth,id:`last-month`},{label:`Last 3 months`,range:d.last3Months,id:`last-3-months`},{label:`This year`,range:d.thisYear,id:`this-year`},{label:`Last year`,range:d.lastFullYear,id:`last-year`}];return z.createElement(`div`,{className:Q[`u1-date-picker__content`]},h&&z.createElement(`div`,{className:Q[`u1-date-picker__sidebar`]},p&&z.createElement(z.default.Fragment,null,z.createElement(w,{size:x.Scale200,variation:_.Subtle},`QUICK SELECT`),O.map(e=>z.createElement(ti,{key:e.id,label:e.label,isSelected:f(e.range),onClick:()=>l(e.range),testId:`${D}-quick-${e.id}`}))),m.map(e=>z.createElement(`div`,{key:e.id,className:Q[`u1-date-picker__custom-button`]},z.createElement(o,{...e,fill:!0,small:!0,variation:e.variation||E.Tertiary,testId:e.testId||`${D}-custom-${e.id}`}),e.subtext&&z.createElement(`span`,{className:Q[`u1-date-picker__button-subtext`]},e.subtext)))),z.createElement(`div`,{className:Q[`u1-date-picker__calendar-wrapper`],style:{"--cell-size":`2rem`}},z.createElement(Xr,{mode:`range`,selected:e,onSelect:t,month:n,onMonthChange:r,disabled:{after:T},fromMonth:C,toMonth:T,fixedWeeks:!0,captionLayout:`label`,numberOfMonths:ee?2:1,showOutsideDays:!1,formatters:{formatCaption:e=>`${e.toLocaleString(`en-US`,{month:`short`})} ${e.getFullYear()}`},className:Q[`u1-date-picker__calendar`],classNames:{root:Q[`u1-date-picker__root`],months:Q[`u1-date-picker__months`],month:Q[`u1-date-picker__month`],month_caption:Q[`u1-date-picker__month-caption`],nav:Q[`u1-date-picker__nav`],button_previous:Q[`u1-date-picker__nav-button`],button_next:Q[`u1-date-picker__nav-button`],weekdays:Q[`u1-date-picker__weekdays`],weekday:Q[`u1-date-picker__weekday`],week:Q[`u1-date-picker__week`],weeks:Q[`u1-date-picker__weeks`],day:Q[`u1-date-picker__day`],day_button:Q[`u1-date-picker__day-button`],today:Q[`u1-date-picker__today`],selected:Q[`u1-date-picker__selected`],range_start:Q[`u1-date-picker__range-start`],range_end:Q[`u1-date-picker__range-end`],range_middle:Q[`u1-date-picker__range-middle`],disabled:Q[`u1-date-picker__disabled`],outside:Q[`u1-date-picker__outside`]}}),z.createElement(`div`,{className:Q[`u1-date-picker__footer`]},z.createElement(`div`,{className:Q[`u1-date-picker__footer-content`]},z.createElement(`div`,{className:Q[`u1-date-picker__input-group`]},z.createElement(u,{type:`text`,value:i,onChange:s,placeholder:`mm/dd/yyyy`,invalid:!v()||y(e?.from),testId:`${D}-start-input`,small:!0}),z.createElement(`div`,{className:Q[`u1-date-picker__input-separator`]},z.createElement(b,{src:Qr,accessibilityLabel:`to`,scale:1.25})),z.createElement(u,{type:`text`,value:a,onChange:c,placeholder:`mm/dd/yyyy`,invalid:!v()||y(e?.to),testId:`${D}-end-input`,small:!0})),z.createElement(`span`,{className:Q[`u1-date-picker__apply-button-wrapper`]},z.createElement(o,{variation:E.Primary,onClick:g,disabled:!v()||S(),testId:`${D}-apply`,small:!0,fill:!0},`Apply`))))))},ri=({label:e,isSelected:t,onClick:n,testId:r})=>z.createElement(o,{variation:t?E.Secondary:E.Tertiary,fill:!0,small:!0,onClick:n,testId:r},e),ii=({draftRange:e,onRangeChange:t,month:n,onMonthChange:r,onQuickSelect:i,quickSelectRanges:a,isRangeSelected:s,showQuickSelect:c,sortedCustomButtons:l,shouldShowSidebar:u,onApply:d,onCancel:f,isDateRangeValid:p,hasInvalidFutureDate:m,minDate:h,maxDate:g,testId:v})=>{let y=[{label:`This month`,range:a.thisMonth,id:`this-month`},{label:`Last month`,range:a.lastFullMonth,id:`last-month`},{label:`Last 3 months`,range:a.last3Months,id:`last-3-months`},{label:`This year`,range:a.thisYear,id:`this-year`},{label:`Last year`,range:a.lastFullYear,id:`last-year`}];return z.createElement(`div`,{className:Q[`u1-date-picker__mobile-content`]},z.createElement(`div`,{className:Q[`u1-date-picker__mobile-calendar`],style:{"--cell-size":`2rem`}},z.createElement(Xr,{mode:`range`,selected:e,onSelect:t,month:n,onMonthChange:r,disabled:{after:g},fromMonth:h,toMonth:g,fixedWeeks:!0,captionLayout:`label`,numberOfMonths:1,showOutsideDays:!1,formatters:{formatCaption:e=>`${e.toLocaleString(`en-US`,{month:`short`})} ${e.getFullYear()}`},className:Q[`u1-date-picker__calendar`],classNames:{root:Q[`u1-date-picker__root`],months:Q[`u1-date-picker__months`],month:Q[`u1-date-picker__month`],month_caption:Q[`u1-date-picker__month-caption`],nav:Q[`u1-date-picker__nav`],button_previous:Q[`u1-date-picker__nav-button`],button_next:Q[`u1-date-picker__nav-button`],weekdays:Q[`u1-date-picker__weekdays`],weekday:Q[`u1-date-picker__weekday`],week:Q[`u1-date-picker__week`],weeks:Q[`u1-date-picker__weeks`],day:Q[`u1-date-picker__day`],day_button:Q[`u1-date-picker__day-button`],today:Q[`u1-date-picker__today`],selected:Q[`u1-date-picker__selected`],range_start:Q[`u1-date-picker__range-start`],range_end:Q[`u1-date-picker__range-end`],range_middle:Q[`u1-date-picker__range-middle`],disabled:Q[`u1-date-picker__disabled`],outside:Q[`u1-date-picker__outside`]}})),u&&z.createElement(`div`,{className:Q[`u1-date-picker__mobile-sidebar-wrapper`]},z.createElement(w,{size:x.Scale200,variation:_.Subtle},`QUICK SELECT`),z.createElement(`div`,{className:Q[`u1-date-picker__mobile-quick-select`]},c&&y.map(e=>z.createElement(ri,{key:e.id,label:e.label,isSelected:s(e.range),onClick:()=>i(e.range),testId:`${v}-quick-${e.id}`})),l.map(e=>z.createElement(`div`,{key:e.id,className:Q[`u1-date-picker__custom-button`]},z.createElement(o,{...e,fill:!0,small:!0,variation:e.variation||E.Tertiary,testId:e.testId||`${v}-custom-${e.id}`}),e.subtext&&z.createElement(`span`,{className:Q[`u1-date-picker__button-subtext`]},e.subtext))))),z.createElement(`div`,{className:Q[`u1-date-picker__mobile-actions`]},z.createElement(o,{variation:E.Tertiary,onClick:f,testId:`${v}-cancel`,fill:!0,small:!0},`Cancel`),z.createElement(o,{variation:E.Primary,onClick:d,disabled:!p()||m(),testId:`${v}-apply`,fill:!0,small:!0},`Apply`)))},ai=e=>`${e.toLocaleString(`en-US`,{month:`short`})} ${String(e.getDate()).padStart(2,`0`)}, ${e.getFullYear()}`,oi=e=>{let t=e.getFullYear();return`${String(e.getMonth()+1).padStart(2,`0`)}/${String(e.getDate()).padStart(2,`0`)}/${t}`},si=e=>{if(!e||typeof e!=`string`)return;let t=e.trim();if(!t)return;let n=new Date(t);if(!isNaN(n.getTime()))return n.setHours(0,0,0,0),n},ci=()=>{let e=new Date;return e.setHours(0,0,0,0),e},li=()=>{let e=new Date;return e.setHours(23,59,59,999),e},ui=(e=new Date)=>{let t=e.getFullYear(),n=e.getMonth();return{thisMonth:{from:new Date(t,n,1),to:e},lastFullMonth:{from:new Date(t,n-1,1),to:new Date(t,n,0)},last3Months:{from:new Date(t,n-3,1),to:new Date(t,n,0)},thisYear:{from:new Date(t,0,1),to:e},lastFullYear:{from:new Date(t-1,0,1),to:new Date(t-1,11,31)}}},di=({showQuickSelect:e=!0,customButtons:t=[],onApply:n,initialRange:r,minDate:i,maxDate:a,allowedDirections:s=[y.Bottom],alignment:c=C.End,id:l,testId:u=`date-picker`})=>{let d=(0,z.useRef)(ci()),f=a??d.current,p=i,[h,_]=(0,z.useState)(!1),[v,b]=(0,z.useState)(r),[x,S]=(0,z.useState)(r),[w,T]=(0,z.useState)(``),[D,ee]=(0,z.useState)(``),[O,te]=(0,z.useState)((0,z.useCallback)(()=>{if(r?.from)return r.from;let e=new Date;return new Date(e.getFullYear(),e.getMonth()-1,1)},[r])),k=(0,z.useRef)(!1),A=(0,z.useRef)(null),j=(0,z.useRef)(null),M=(0,z.useRef)(null),N=(0,z.useMemo)(()=>ui(d.current),[]),{Popper:P,anchorRef:F,anchorProps:I,context:ne}=g({open:h,allowedDirections:s,alignment:c,renderOverlay:!1}),re=(0,z.useCallback)(()=>{S(v),_(!1)},[v]),ie=(0,z.useCallback)(e=>{j.current=e,F(e)},[F]);(0,z.useEffect)(()=>{if(!h||!window.matchMedia(`(min-width: 640px)`).matches)return;let e=e=>{let t=e.target,n=j.current,r=M.current;n&&!n.contains(t)&&r&&!r.contains(t)&&re()};return document.addEventListener(`mousedown`,e),()=>{document.removeEventListener(`mousedown`,e)}},[h,re]),(0,z.useEffect)(()=>{k.current||(T(x?.from?oi(x.from):``),ee(x?.to?oi(x.to):``)),k.current=!1},[x]),(0,z.useEffect)(()=>{h&&S(v)},[h,v]);let L=(0,z.useCallback)(e=>{let t=window.matchMedia(`(min-width: 768px)`).matches,n=e.getFullYear()===f.getFullYear()&&e.getMonth()===f.getMonth(),r=t&&n,i=new Date(e.getFullYear(),r?e.getMonth()-1:e.getMonth(),1);te(i)},[f]);(0,z.useEffect)(()=>{h&&x?.from&&L(x.from)},[h,x?.from,L]),(0,z.useEffect)(()=>{if(!h||!x?.from)return;let e=()=>{L(x.from)};return window.addEventListener(`resize`,e),()=>window.removeEventListener(`resize`,e)},[h,x?.from,L]);let ae=(0,z.useCallback)(e=>{k.current=!0,T(e.target.value);let t=si(e.target.value);t&&(!p||t>=p)&&t<=f&&(S(e=>({from:t,to:e?.to})),te(t))},[p,f]),oe=(0,z.useCallback)(e=>{k.current=!0,ee(e.target.value);let t=si(e.target.value);t&&(!p||t>=p)&&t<=f&&S(e=>({from:e?.from,to:t}))},[p,f]),se=(0,z.useCallback)(e=>e&&(p&&e<p?p:e>f?f:e),[p,f]),R=(0,z.useCallback)(e=>{S({from:se(e.from),to:se(e.to)})},[se]),ce=(0,z.useCallback)(()=>{b(x),_(!1),n&&n(x)},[x,n]),le=(0,z.useCallback)(e=>x?.from?.toDateString()===e.from?.toDateString()&&x?.to?.toDateString()===e.to?.toDateString(),[x]),ue=(0,z.useCallback)(()=>v?.from&&v?.to?`${ai(v.from)} - ${ai(v.to)}`:v?.from?ai(v.from):`Select dates`,[v]),de=(0,z.useCallback)(()=>!(!x?.from||!x?.to||x.from>x.to||p&&x.from<p||x.to>f),[x,p,f]),fe=(0,z.useMemo)(()=>li(),[]),pe=(0,z.useCallback)(e=>e?e>fe:!1,[fe]),me=(0,z.useCallback)(()=>pe(x?.from)||pe(x?.to),[x,pe]),he=(0,z.useMemo)(()=>[...t.flatMap(e=>e.buttons)].sort((e,t)=>e.position!==void 0&&t.position!==void 0?e.position-t.position:e.position===void 0?t.position===void 0?0:1:-1).map(e=>({...e,onClick:t=>{e.range&&R(e.range),e.onClick&&e.onClick(t)}})),[t,R]),ge=e||he.length>0,_e=(0,z.useMemo)(()=>({draftRange:x,onRangeChange:S,month:O,onMonthChange:te,startInput:w,endInput:D,onStartChange:ae,onEndChange:oe,onQuickSelect:R,quickSelectRanges:N,isRangeSelected:le,showQuickSelect:e,sortedCustomButtons:he,shouldShowSidebar:ge,onApply:ce,isDateRangeValid:de,isFutureDate:pe,hasInvalidFutureDate:me,minDate:p,maxDate:f,testId:u}),[x,O,w,D,ae,oe,R,N,le,e,he,ge,ce,de,pe,me,p,f,u]);return z.createElement(`div`,{className:Q[`u1-date-picker`],id:l,"data-testid":u},z.createElement(`span`,{className:Q[`u1-date-picker__button`]},z.createElement(o,{onClick:()=>_(!0),variation:E.Tertiary,icons:{right:{src:xe,accessibilityLabel:`Open date picker`,scale:1.5}},testId:`${u}-trigger`,ref:ie,...I},ue())),h&&z.createElement(z.default.Fragment,null,z.createElement(P,{context:ne,testId:`${u}-popover`,noPadding:!0},z.createElement(`div`,{className:Q[`u1-date-picker__desktop-wrapper`],ref:M},z.createElement(`div`,{className:Q[`u1-date-picker__modal`],role:`dialog`,"aria-modal":`false`,"data-testid":`${u}-modal`},z.createElement(ni,{..._e})))),z.createElement(m,null,z.createElement(`div`,{className:Q[`u1-date-picker__mobile-wrapper`]},z.createElement(`div`,{ref:A,className:Q[`u1-date-picker__mobile-modal`],role:`dialog`,"aria-modal":`true`,"aria-label":`Select date range`,"data-testid":`${u}-modal`},z.createElement(ii,{..._e,onCancel:re}))))))};di.displayName=`DatePicker`;var fi=window.constants?.organization_settings?.max_assets_search_size,pi=window.constants?.organization_settings?.industries||[],mi=window.constants?.organization_settings?.revenue_cohorts||[],hi=window.constants?.organization_settings.subscription_periods||[],gi=window.constants?.organization_settings?.annual_rates_of_occurrence||[],_i=`STANDARD ARO OPTIONS`,vi=`null`,yi=()=>`Industry baseline ARO`,bi=()=>({value:vi,label:yi()}),xi=Object.fromEntries(pi.map(e=>[e.value,e.label])),Si=Object.fromEntries(mi.map(e=>[e.value,e.label])),Ci=Object.fromEntries(hi.map(e=>[e.value,e.label.replace(/_/g,` `).replace(/\b\w/g,(e,t)=>t===0?e.toUpperCase():e.toLowerCase())])),wi=hi.map(e=>({value:e.value,label:Ci[e.value]})),Ti=(e,t)=>e==null||t==null||isNaN(e)||isNaN(t)?0:e/100*t,Ei=(e,t)=>e==null||isNaN(e)?bi():t.find(t=>Number(t.value)===e)||(t.flatMap(e=>e.options??[]).find(t=>Number(t.value)===e)??null),Di={confidentiality_single_loss_expectancy_high:null,confidentiality_single_loss_expectancy_low:null,integrity_single_loss_expectancy_high:null,integrity_single_loss_expectancy_low:null,availability_single_loss_expectancy_high:null,availability_single_loss_expectancy_low:null,confidentiality_annual_rate_of_occurrence:null,integrity_annual_rate_of_occurrence:null,availability_annual_rate_of_occurrence:null},Oi=(e=Di)=>({confidentiality:{high_impact_sle:e?.confidentiality_single_loss_expectancy_high??null,low_impact_sle:e?.confidentiality_single_loss_expectancy_low??null,annual_rate_of_occurrence:e?.confidentiality_annual_rate_of_occurrence??null},integrity:{high_impact_sle:e?.integrity_single_loss_expectancy_high??null,low_impact_sle:e?.integrity_single_loss_expectancy_low??null,annual_rate_of_occurrence:e?.integrity_annual_rate_of_occurrence??null},availability:{high_impact_sle:e?.availability_single_loss_expectancy_high??null,low_impact_sle:e?.availability_single_loss_expectancy_low??null,annual_rate_of_occurrence:e?.availability_annual_rate_of_occurrence??null}}),ki=e=>({confidentiality:{high_impact_sle:e?.confidentiality_single_loss_expectancy_high??0,low_impact_sle:e?.confidentiality_single_loss_expectancy_low??0,annual_rate_of_occurrence:null},integrity:{high_impact_sle:e?.integrity_single_loss_expectancy_high??0,low_impact_sle:e?.integrity_single_loss_expectancy_low??0,annual_rate_of_occurrence:null},availability:{high_impact_sle:e?.availability_single_loss_expectancy_high??0,low_impact_sle:e?.availability_single_loss_expectancy_low??0,annual_rate_of_occurrence:null}}),Ai=(e,t)=>t==null||isNaN(t)||t===0?0:e/t*100,ji=(e,t)=>t>e,Mi=e=>ji(e.high_impact_sle,e.low_impact_sle),Ni=(e,t,n,r)=>{let{high_impact_sle:i,low_impact_sle:a,annual_rate_of_occurrence:o}=e,{high_impact_sle:s,low_impact_sle:c,annual_rate_of_occurrence:l}=t;return{high_impact_sle:Ti(i??s,n),low_impact_sle:Ti(a??c,n),annual_rate_of_occurrence:Ei(o??l,r.options)}},Pi=(e,t)=>{let{high_impact_sle:n,low_impact_sle:r}=e;return{high_impact_sle:Ti(n,t),low_impact_sle:Ti(r,t),annual_rate_of_occurrence:bi()}},Fi=(e,t,n)=>{let{high_impact_sle:r,low_impact_sle:i,annual_rate_of_occurrence:a}=e,{high_impact_sle:o,low_impact_sle:s,annual_rate_of_occurrence:c}=t,l=a,u=l?.value===vi?null:l?.value?Number(l.value):null;return{high_impact_sle:Ii(o,Ai(r,n)),low_impact_sle:Ii(s,Ai(i,n)),annual_rate_of_occurrence:Ii(c,u)}},Ii=(e,t)=>t===e?null:t,Li=(e,t)=>{let n=e?e*2:0,r=Math.max(Math.round(n/200),1),i=t?.confidentiality?Pi(t.confidentiality,e):void 0,a=t?.integrity?Pi(t.integrity,e):void 0,o=t?.availability?Pi(t.availability,e):void 0;return{confidentialityCardSettings:{title:`Confidentiality incident`,sliderProps:{min:0,max:n,step:r},high_slider_settings:{id:`high_impact_sle`,type:`slider`,label:`Single loss expectancy (high impact incident)`,labelTooltipText:`High impact confidentiality incident: The attacker gains full access to the system, including highly sensitive data like encryption keys.`,valueFormat:{style:`currency`,currency:`USD`,currencyDisplay:`narrowSymbol`,minimumFractionDigits:0,maximumFractionDigits:0},defaultValue:i?.high_impact_sle??n},low_slider_settings:{id:`low_impact_sle`,type:`slider`,label:`Single loss expectancy (low impact incident)`,labelTooltipText:`Low impact confidentiality incident: The attacker has limited access to information and cannot control information they can access.`,valueFormat:{style:`currency`,currency:`USD`,currencyDisplay:`narrowSymbol`,minimumFractionDigits:0,maximumFractionDigits:0},defaultValue:i?.low_impact_sle??n},aro_dropdown_settings:{id:`annual_rate_of_occurrence`,type:`dropdown`,label:`Annual rate of occurrence`,labelTooltipText:`The rate at which you expect to experience a threat event.`,options:[i?.annual_rate_of_occurrence,{label:_i,options:gi}]}},integrityCardSettings:{title:`Integrity incident`,sliderProps:{min:0,max:n,step:r},high_slider_settings:{id:`high_impact_sle`,type:`slider`,label:`Single loss expectancy (high impact incident)`,labelTooltipText:`High impact integrity incident: The attacker can modify all data on the system, resulting in a total loss of integrity.`,valueFormat:{style:`currency`,currency:`USD`,currencyDisplay:`narrowSymbol`,minimumFractionDigits:0,maximumFractionDigits:0},defaultValue:a?.high_impact_sle??n},low_slider_settings:{id:`low_impact_sle`,type:`slider`,label:`Single loss expectancy (low impact incident)`,labelTooltipText:`Low impact integrity incident: A limited amount of data may be altered, but the system experiences no significant impact.`,valueFormat:{style:`currency`,currency:`USD`,currencyDisplay:`narrowSymbol`,minimumFractionDigits:0,maximumFractionDigits:0},defaultValue:a?.low_impact_sle??n},aro_dropdown_settings:{id:`annual_rate_of_occurrence`,type:`dropdown`,label:`Annual rate of occurrence`,labelTooltipText:`The rate at which you expect to experience a threat event.`,options:[a?.annual_rate_of_occurrence,{label:_i,options:gi}]}},availabilityCardSettings:{title:`Availability incident`,sliderProps:{min:0,max:n,step:r},high_slider_settings:{id:`high_impact_sle`,type:`slider`,label:`Single loss expectancy (high impact incident)`,labelTooltipText:`High impact availability incident: The system or data becomes completely unavailable to authorized users.`,valueFormat:{style:`currency`,currency:`USD`,currencyDisplay:`narrowSymbol`,minimumFractionDigits:0,maximumFractionDigits:0},defaultValue:o?.high_impact_sle??n},low_slider_settings:{id:`low_impact_sle`,type:`slider`,label:`Single loss expectancy (low impact incident)`,labelTooltipText:`Low impact availability incident: Access may be intermittently limited or system performance degraded.`,valueFormat:{style:`currency`,currency:`USD`,currencyDisplay:`narrowSymbol`,minimumFractionDigits:0,maximumFractionDigits:0},defaultValue:o?.low_impact_sle??n},aro_dropdown_settings:{id:`annual_rate_of_occurrence`,type:`dropdown`,label:`Annual rate of occurrence`,labelTooltipText:`The rate at which you expect to experience a threat event.`,options:[o?.annual_rate_of_occurrence,{label:_i,options:gi}]}}}},Ri=e=>{if(!e)return``;try{let t=new URL(e,window.location.origin);return t.search=``,t.toString()}catch{return``}},zi=e(i()),$=n(),Bi=({bgColor:e,title:t,content:n})=>(0,$.jsxs)(`div`,{className:(0,zi.default)(`items-center p-md rounded gap-sm justify-center flex`,e),children:[(0,$.jsx)(`span`,{className:`font-bold`,children:t}),(0,$.jsx)(`div`,{className:`flex flex-col items-center flex-1 max-w-fit`,children:n})]}),Vi=({title:e,description:t})=>(0,$.jsxs)(`div`,{children:[(0,$.jsx)(`span`,{className:`font-semibold`,children:e}),(0,$.jsx)(`span`,{children:t})]}),Hi=({title:e,impacts:t})=>(0,$.jsxs)(`div`,{className:`flex flex-col gap-2xs`,children:[(0,$.jsx)(`div`,{children:(0,$.jsx)(`span`,{className:`font-semibold`,children:e})}),(0,$.jsx)(`div`,{className:`pl-md`,children:(0,$.jsx)(`ul`,{className:`list-disc pl-sm`,children:t.map((e,t)=>(0,$.jsxs)(`li`,{children:[(0,$.jsxs)(`span`,{className:`font-semibold`,children:[e.label,`:`]}),` `,e.description]},t))})})]}),Ui=({calculationSheetOpen:e,setCalculationSheetOpen:t})=>(0,$.jsx)(l,{open:e,title:`How RoM is calculated`,size:{default:f[`4/12`]},onClose:()=>{t(!1)},footer:(0,$.jsxs)(`div`,{className:`flex flex-row justify-between items-center`,children:[(0,$.jsxs)(`a`,{href:`https://docs.hackerone.com/en/articles/11759633-return-on-mitigation`,target:`_blank`,rel:`noopener noreferrer`,children:[`View docs `,(0,$.jsx)(b,{src:O})]}),(0,$.jsx)(o,{onClick:()=>{t(!1)},variation:E.Tertiary,children:`Close`})]}),children:(0,$.jsxs)(`div`,{className:`flex flex-col gap-lg`,children:[(0,$.jsxs)(`section`,{className:`flex flex-col gap-xs`,children:[(0,$.jsx)(S,{size:T.Scale300,children:`Calculations`}),(0,$.jsxs)(`div`,{className:`flex flex-col gap-sm`,children:[(0,$.jsx)(Bi,{bgColor:`bg-blue-900 dark:bg-blue-200`,title:`RoM =`,content:(0,$.jsxs)($.Fragment,{children:[(0,$.jsx)(`span`,{children:`(Mitigated losses/year - Amount invested)`}),(0,$.jsx)(`div`,{className:`h-[1px] bg-neutral-50 w-full dark:bg-neutral-900`}),(0,$.jsx)(`span`,{children:`Amount invested`})]})}),(0,$.jsx)(Bi,{bgColor:`bg-neutral-900 dark:bg-neutral-300`,title:`Mitigated losses/year =`,content:(0,$.jsx)(`span`,{children:`SLE * ARO * vulnerabilities found`})}),(0,$.jsx)(Bi,{bgColor:`bg-neutral-900 dark:bg-neutral-300`,title:`Amount invested =`,content:(0,$.jsx)(`span`,{children:`Platform fees + Cost of rewards`})})]})]}),(0,$.jsxs)(`section`,{className:`flex flex-col gap-xs`,children:[(0,$.jsx)(S,{size:T.Scale300,children:`Definitions`}),(0,$.jsxs)(`div`,{className:`flex flex-col gap-md`,children:[(0,$.jsx)(Vi,{title:`Mitigated losses/year: `,description:`cost to the organization if vulnerabilities remain unremediated for the next year.`}),(0,$.jsx)(Vi,{title:`Single loss expectancy (SLE) = `,description:`The estimated monetary loss when a threat event occurs. The baseline comes from IBM's Cost of a Breach report. You can modify this value by updating your industry and adjusting the percentage of the baseline SLE for each incident type.`}),(0,$.jsx)(Vi,{title:`Annual rate of occurrence (ARO) = `,description:`The rate at which you expect to experience a threat event. Comes from the CVSS scores utilizing the Verizon DBIR Report and is scaled using HackerOne industry benchmarks. You can override this value by updating your revenue size and changing the ARO for each incident type.`}),(0,$.jsx)(p,{variation:h.Light}),(0,$.jsx)(Vi,{title:`Platform fees = `,description:`Includes prorated HackerOne subscription fees and other applicable services like Triage, Security Advisory Services (SAS), etc. Each subscription fee is adjusted to reflect the portion of time covered by your selected date range and is allocated evenly across the date range.`}),(0,$.jsx)(Vi,{title:`Hacker rewards = `,description:`Includes valid, paid, non-duplicate submissions. Based on actual payments made (not reports submitted) within the date range.`}),(0,$.jsx)(p,{variation:h.Light}),(0,$.jsx)(Hi,{title:`Confidentiality = `,impacts:[{label:`High impact`,description:`The attacker gains full access to the system, and can notably manipulate the encryption keys.`},{label:`Low impact`,description:`The attacker has limited access to information and cannot control information they can access.`}]}),(0,$.jsx)(Hi,{title:`Integrity = `,impacts:[{label:`High impact`,description:`The attacker can modify all data on the system, resulting in a total loss of integrity.`},{label:`Low impact`,description:`A limited amount of data may be altered, but the system experiences no significant impact.`}]}),(0,$.jsx)(Hi,{title:`Availability = `,impacts:[{label:`High impact`,description:`The system or data becomes completely unavailable to authorized users.`},{label:`Low impact`,description:`Access may be intermittently limited or system performance degraded.`}]})]})]})]})});export{oe as A,he as C,I as D,R as E,de as M,te as N,ce as O,O as P,ge as S,le as T,di as _,Oi as a,pe as b,ki as c,xi as d,pi as f,mi as g,Si as h,wi as i,ue as j,se as k,ji as l,Ii as m,Ni as n,Li as o,fi as p,Fi as r,Ri as s,Ui as t,Mi as u,fe as v,be as w,_e as x,me as y};
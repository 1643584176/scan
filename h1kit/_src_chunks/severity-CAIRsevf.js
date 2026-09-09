import{o as e}from"./rolldown-runtime-DAXXjFlN.js";import{Cf as t,Hb as n,Pb as r,Sn as i,ab as a,ow as o,wi as s}from"./vendor-_WdvpBLr.js";var c=e(o()),l=e(n()),u=e(a()),d=e(t()),f=e(s()),p=e(i());function m(e){return e.replace(/_([a-z])/g,e=>e[1].toUpperCase())}function h(e){return e.replace(/([A-Z])/g,e=>`_${e[0].toLowerCase()}`)}var g=e(r()),_=class extends u.default.Model{get name(){return`Severity`}url(){return this.url}validate(e,t){if(this.noneSelected())return`must select either rating or metrics`;if(!this.get(`rating`)&&this.metricsPartiallySelected())return`must select all metrics`;if(t.prev&&this.isEqual(t.prev))return`severity is not changed`}noneSelected(){return!this.get(`rating`)&&(0,f.default)((0,c.default)(this.get(`metrics`)),function(e){return!e})}metricsPartiallySelected(){let e=(0,d.default)((0,c.default)(this.get(`metrics`)),function(e){return!e}).length;return e>0&&e<(0,p.default)(this.get(`metrics`))}isEqual(e){return e.rating===this.get(`rating`)&&(0,l.default)((0,c.default)(e.metrics),(0,c.default)(this.get(`metrics`)))}ratingDisabled(e){return this.get(`max_severity`)&&this.eligibleRatings().indexOf(e)>this.eligibleRatings().indexOf(this.get(`max_severity`))}isNew(){return!0}canCalculate(){return!(this.noneSelected()||this.metricsPartiallySelected())&&this.get(`withMetrics`)}resetRating(){(this.get(`rating`)||this.ratingDisabled(this.get(`rating`)))&&this.set(`rating`,null)}calculate(e,t,n,r){this.url=this.get(`calculateUrl`),this.save(e,t).fail(n).done(r),this.url=this.get(`saveUrl`)}fetchDraft(e,t,n,r,i){this.url=this.get(`calculateUrl`),this.fetch(e,t).fail(n).done(r).done(()=>{g.default.existy(this.get(`score`))&&(this.set({withMetrics:!0}),this.trigger(`change`))}).always(i),this.url=this.get(`saveUrl`)}toJSON(){return this.noneSelected()?{}:{tracer:this.get(`tracer`),rating:this.get(`rating`),with_metrics:this.get(`withMetrics`),structured_scope_id:this.get(`scope_id`),metrics:this.get(`withMetrics`)?this.translate(this.get(`metrics`)):{}}}initialize(e,t,n=`severities`,r=-1){this.set({calculateUrl:`/${t}/${n}`,saveUrl:`/reports/${r}/${n}`}),this.url=this.get(`saveUrl`),this.tracer=e&&e.tracer,e&&(e.metrics?this.set({withMetrics:!0,metrics:this.translate(e.metrics)}):this.set(`withMetrics`,!1))}translate(e){let t={};return Object.keys(e).forEach(n=>{/_([a-z])/.test(n)?t[m(n)]=e[n]:t[h(n)]=e[n]}),t}defaults(){return{withMetrics:!1,rating:`none`,metrics:{attackVector:`network`,attackComplexity:`low`,privilegesRequired:`none`,userInteraction:`none`,scope:`unchanged`,integrity:`none`,confidentiality:`none`,availability:`none`}}}eligibleMetrics(){return[{id:1,metric:`attackVector`,label:`Attack Vector`,choices:constants.report.severity.metrics.attackVector},{id:2,metric:`attackComplexity`,label:`Attack Complexity`,choices:constants.report.severity.metrics.attackComplexity},{id:3,metric:`privilegesRequired`,label:`Privileges Required`,choices:constants.report.severity.metrics.privilegesRequired},{id:4,metric:`userInteraction`,label:`User Interaction`,choices:constants.report.severity.metrics.userInteraction},{id:5,metric:`scope`,label:`Scope`,choices:constants.report.severity.metrics.scope},{id:6,metric:`confidentiality`,label:`Confidentiality`,choices:constants.report.severity.metrics.confidentiality},{id:7,metric:`integrity`,label:`Integrity`,choices:constants.report.severity.metrics.integrity},{id:8,metric:`availability`,label:`Availability`,choices:constants.report.severity.metrics.availability}]}eligibleRatings(){return constants.report.severity.all}metricsExplanations(){return{attackVector:{name:`Attack Vector`,explanation:`This metric reflects the context by which vulnerability exploitation is
        possible. The Score increases the more remote (logically, and physically) an attacker
        can be in order to exploit the vulnerable component.`,choices:[{value:`network`,explanation:`A vulnerability exploitable with network access means the vulnerable
            component is bound to the network stack and the attacker's path is through OSI layer 3
            (the network layer). Such a vulnerability is often termed "remotely exploitable" and
            can be thought of as an attack being exploitable one or more network hops away.`},{value:`adjacent`,explanation:`A vulnerability exploitable with adjacent network access means the
            vulnerable component is bound to the network stack, however the attack is limited to
            the same shared physical (e.g. Bluetooth, IEEE 802.11), or logical (e.g. local IP
            subnet) network, and cannot be performed across an OSI layer 3 boundary (e.g. a router
            ).`},{value:`local`,explanation:`A vulnerability exploitable with local access means that the vulnerable
            component is not bound to the network stack, and the attacker's path is via
            read/write/execute capabilities. In some cases, the attacker may be logged in locally
            in order to exploit the vulnerability, otherwise, the attacker may rely on User
            Interaction to execute a malicious file.`},{value:`physical`,explanation:`A vulnerability exploitable with physical access requires the attacker to
            physically touch or manipulate the vulnerable component. Physical interaction may be
            brief or persistent.`}]},attackComplexity:{name:`Attack Complexity`,explanation:`This metric describes the conditions beyond the attacker's control that must
        exist in order to exploit the vulnerability. Such conditions may require the collection of
        more information about the target, the presence of certain system configuration settings, or
        computational exceptions.`,choices:[{value:`low`,explanation:`Specialized access conditions or extenuating circumstances do not exist.
            An attacker can expect repeatable success against the vulnerable component.`},{value:`high`,explanation:`A successful attack depends on conditions beyond the attacker's control.
            That is, a successful attack cannot be accomplished at will, but requires the attacker
            to invest in some measurable amount of effort in preparation or execution against the
            vulnerable component before a successful attack can be expected. For example, a
            successful attack may require the attacker: to perform target-specific reconnaissance;
            to prepare the target environment to improve exploit reliability; or to inject herself
            into the logical network path between the target and the resource requested by the
            victim in order to read and/or modify network communications (e.g. a man in the middle
            attack).`}]},privilegesRequired:{name:`Privileges Required`,explanation:`This metric describes the level of privileges an attacker must possess before
        successfully exploiting the vulnerability. This Score increases as fewer privileges are
        required.`,choices:[{value:`none`,explanation:`The attacker is unauthorized prior to attack, and therefore does not
            require any access to settings or files to carry out an attack.`},{value:`low`,explanation:`The attacker is authorized with (i.e. requires) privileges that provide
            basic user capabilities that could normally affect only settings and files owned by a
            user. Alternatively, an attacker with low privileges may have the ability to cause an
            impact only to non-sensitive resources.`},{value:`high`,explanation:`The attacker is authorized with (i.e. requires) privileges that provide
            significant (e.g. administrative) control over the vulnerable component that could
            affect component-wide settings and files.`}]},userInteraction:{name:`User Interaction`,explanation:`This metric captures the requirement for a user, other than the attacker, to
        participate in the successful compromise the vulnerable component. This metric determines
        whether the vulnerability can be exploited solely at the will of the attacker, or whether a
        separate user (or user-initiated process) must participate in some manner. The Score is
        highest when no user interaction is required.`,choices:[{value:`none`,explanation:`The vulnerable system can be exploited without any interaction
            from any user.`},{value:`required`,explanation:`Successful exploitation of this vulnerability requires a user to take some
            action before the vulnerability can be exploited.`}]},scope:{name:`Scope`,explanation:`Does a successful attack impact a component other than the vulnerable
        component? If so, the Score increases and the Confidentiality, Integrity and
        Authentication metrics should be scored relative to the impacted component.`,choices:[{value:`unchanged`,explanation:`An exploited vulnerability can only affect resources managed by the
            same authority. In this case the vulnerable component and the impacted component
            are the same.`},{value:`changed`,explanation:`An exploited vulnerability can affect resources beyond the authorization
            privileges intended by the vulnerable component. In this case the vulnerable component
            and the impacted component are different.`}]},confidentiality:{name:`Confidentiality`,explanation:`This metric measures the impact to the confidentiality of the information
        resources managed by a software component due to a successfully exploited vulnerability.
        Confidentiality refers to limiting information access and disclosure to only authorized
        users, as well as preventing access by, or disclosure to, unauthorized ones.`,choices:[{value:`none`,explanation:`There is no loss of confidentiality within the impacted component.`},{value:`low`,explanation:`There is some loss of confidentiality. Access to some restricted
            information is obtained, but the attacker does not have control over what information
            is obtained, or the amount or kind of loss is constrained. The information disclosure
            does not cause a direct, serious loss to the impacted component.`},{value:`high`,explanation:`There is total loss of confidentiality, resulting in all resources within
            the impacted component being divulged to the attacker. Alternatively, access to only
            some restricted information is obtained, but the disclosed information presents a
            direct, serious impact.`}]},integrity:{name:`Integrity`,explanation:`This metric measures the impact to integrity of a successfully exploited
        vulnerability. Integrity refers to the trustworthiness and veracity of information.`,choices:[{value:`none`,explanation:`There is no loss of integrity within the impacted component.`},{value:`low`,explanation:`Modification of data is possible, but the attacker does not have
            control over the consequence of a modification, or the amount of modification is
            constrained. The data modification does not have a direct, serious impact on the
            impacted component.`},{value:`high`,explanation:`There is a total loss of integrity, or a complete loss of protection. For
            example, the attacker is able to modify any/all files protected by the impacted
            component. Alternatively, only some files can be modified, but malicious modification
            would present a direct, serious consequence to the impacted component.`}]},availability:{name:`Availability`,explanation:`This metric measures the impact to the availability of the impacted component
        resulting from a successfully exploited vulnerability. It refers to the loss of availability
        of the impacted component itself, such as a networked service (e.g., web, database, email).
        Since availability refers to the accessibility of information resources, attacks that
        consume network bandwidth, processor cycles, or disk space all impact the availability of an
        impacted component.`,choices:[{value:`none`,explanation:`There is no impact to availability within the impacted component.`},{value:`low`,explanation:`There is reduced performance or interruptions in resource availability.
            Even if repeated exploitation of the vulnerability is possible, the attacker does not
            have the ability to completely deny service to legitimate users. The resources in the
            impacted component are either partially available all of the time, or fully available
            only some of the time, but overall there is no direct, serious consequence to the
            impacted component.`},{value:`high`,explanation:`There is total loss of availability, resulting in the attacker being able
            to fully deny access to resources in the impacted component; this loss is either
            sustained (while the attacker continues to deliver the attack) or persistent (the
            condition persists even after the attack has completed). Alternatively, the attacker has
            the ability to deny some availability, but the loss of availability presents a direct,
            serious consequence to the impacted component (e.g., the attacker cannot disrupt
            existing connections, but can prevent new connections; the attacker can repeatedly
            exploit a vulnerability that, in each instance of a successful attack, leaks a only
            small amount of memory, but after repeated exploitation causes a service to become
            completely unavailable).`}]}}}};export{_ as t};
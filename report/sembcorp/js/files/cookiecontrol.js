/*jslint browser: true, fudge: true, long: true */
/*global blacksunplc, decodeURIComponent, dialogPolyfill, document, encodeURIComponent, ga, GA_MEASUREMENT_ID, self */

(function (globalThis) {
    "use strict";

    var arrays = blacksunplc.arrays;   // import * as arrays  from "module:blacksunplc/arrays"
    var dates = blacksunplc.dates;     // import * as dates   from "module:blacksunplc/dates"
    var events = blacksunplc.events;   // import * as events  from "module:blacksunplc/events"
    var jsonml = blacksunplc.jsonml;   // import * as jsonml  from "module:blacksunplc/jsonml"
    var urls = blacksunplc.urls;       // import * as urls    from "module:blacksunplc/urls"
    var storage = blacksunplc.storage; // import * as storage from "module:blacksunplc/storage"
    var ajax = blacksunplc.ajax;       // import * as ajax    from "module:blacksunplc/ajax"

    /**
     * Enable for logging.
     * @const {boolean}
     */
    var DEBUG = false;

    /* Must match the name used by the CookieControlServlet. */
    var COOKIE_NAME = "CookieControl";

    /* Maximum age is a period of 90 days, expressed in seconds. */
    var COOKIE_OPTIONS = {maxAge: 90 * 24 * 60 * 60};

    /* The known Google Analytics cookies (last checked on 2020-04-01). */
    var GANALYTICS_NAMES = [/^_ga/, "_gid"];
     /* dataLayer variable that tracks user's consent.
     * MUST match the name used in the GTM exception rules to prevent GTM tags from firing.
     */
    var COOKIE_CONSENT_LIST = "cookieConsentList";
    /* dataLayer event that fires when the user accepts the use of cookies. */
    var CONSENT_GRANTED_EVENT = "cookieConsentGranted";
    /* dataLayer event that fires when the user revokes consent to the use of cookies. */
    var CONSENT_REVOKED_EVENT = "cookieConsentRevoked";
    /* dataLayer variable that tracks the date/time when consent was granted or revoked. */
    var COOKIE_CONTROL_DATE = "cookieControlDate";

    /* Initialise the dataLayer before GTM loads. */
    /* The optional "meta[name='gtm-dl']" element must precede the script element. */
    var metaDataLayer = /** @type {?HTMLMetaElement} */ (document.querySelector("meta[name='gtm-dl']"));

    /* The name of the data layer. */
    var dataLayerName = (metaDataLayer && metaDataLayer.content) || "dataLayer";

    /* Initialise the data layer. */
    globalThis[dataLayerName] = globalThis[dataLayerName] || [];

    /* Implements the Web Storage API for cookies. */
    var cookieStorage = storage.cookieStorage();

    /** @return {!blacksunplc.CookieControl} */
    function getCookieControl() {
        var cookieItem = cookieStorage.getItem(COOKIE_NAME);
        if (cookieItem) {
            return /** @type {!blacksunplc.CookieControl} */ (JSON.parse(decodeURIComponent(cookieItem.value)));
        }
        return {modified: 0, consent: {}};
    }

    /** @param {!blacksunplc.CookieControl} cookieControl */
    function setCookieControl(cookieControl) {
        cookieControl.modified = dates.now();
        var value = encodeURIComponent(JSON.stringify(cookieControl));
        cookieStorage.setItem(COOKIE_NAME, value, COOKIE_OPTIONS);
    }

    /** @param {!Object} data */
    function dataLayerPush(data) {
        globalThis[dataLayerName].push(data);
    }

    storage.installFilter();
    storage.certifyLawfulBasis([COOKIE_NAME]);

    if (getCookieControl().consent.ganalytics) {
        storage.certifyLawfulBasis(GANALYTICS_NAMES);

        var cookieConsentListUpdatedEvent  = {};
        cookieConsentListUpdatedEvent[COOKIE_CONSENT_LIST] = GANALYTICS_NAMES;
        dataLayerPush(cookieConsentListUpdatedEvent);
    } else {
        var cookieConsentListUpdatedEvent  = {};
        cookieConsentListUpdatedEvent[COOKIE_CONSENT_LIST] = [];
        dataLayerPush(cookieConsentListUpdatedEvent);
    }

    /* Register the "dialog" tagName in old browsers so CSS is applied. */
    if (!globalThis.HTMLDialogElement) {
        document.createElement("dialog");
    }

    /* Make AJAX call to the "CookieControlServlet" before waiting for DOMContentLoaded. */
    ajax.getText("/umbraco/api/cookiecontrol/get").then(function (showNotification) {
        if (DEBUG) {
            console.debug("Initialising cookie control dialog. Show notification:", showNotification);
        }

        /* Wait for DOMContentLoaded before accessing the DOM. */
        events.ready(function () {
            var dialog = /** @type {?HTMLDialogElement} */ (document.querySelector(".cookiecontrol"));
            if (!dialog) {
                if (DEBUG) {
                    console.debug("Couldn't find '.cookiecontrol' dialog.");
                }
                return;
            }

            if (!dialog.showModal) {
                /* Initialisation of `dialogPolyfill` may fail in old browsers. */
                if (!dialogPolyfill) {
                    console.error("'dialogPolyfill' is unavailable.");
                    return;
                }
                if (DEBUG) {
                    console.debug("Registering dialog using polyfill.", dialog, dialogPolyfill);
                }
                dialogPolyfill.registerDialog(dialog);
            }

            var checkbox = /** @type {!HTMLInputElement} */ (document.querySelector("#give-consent-ganalytics"));
            checkbox.checked = Boolean(getCookieControl().consent.ganalytics);

            function saveAndClose() {
                var cookieControl = getCookieControl();
                if (DEBUG) {
                    console.debug("Saving and closing cookie control dialog.", dialog, cookieControl);
                }
                if (checkbox.checked) {
                    storage.certifyLawfulBasis(GANALYTICS_NAMES);
                    cookieControl.consent.ganalytics = dates.now();

                    var consentGrantedEvent = {"event": CONSENT_GRANTED_EVENT};
                    consentGrantedEvent[COOKIE_CONTROL_DATE] = cookieControl.modified;
                    dataLayerPush(consentGrantedEvent);

                    var cookieConsentListUpdatedEvent  = {};
                    cookieConsentListUpdatedEvent[COOKIE_CONSENT_LIST] = GANALYTICS_NAMES;
                    dataLayerPush(cookieConsentListUpdatedEvent);

                    if (typeof ga !== "undefined" && ga) {
                        ga("send", "pageview");  // Fire pageview to collect current page view.
                    }
                } else {
                    storage.revokeLawfulBasis(GANALYTICS_NAMES);
                    delete cookieControl.consent.ganalytics;

                    var consentRevokedEvent = {"event": CONSENT_REVOKED_EVENT};
                    consentRevokedEvent[COOKIE_CONTROL_DATE] = cookieControl.modified;
                    dataLayerPush(consentRevokedEvent);

                    var cookieConsentListUpdatedEvent  = {};
                    cookieConsentListUpdatedEvent[COOKIE_CONSENT_LIST] = [];
                    dataLayerPush(cookieConsentListUpdatedEvent);
                }
                setCookieControl(cookieControl);
                dialog.close();
            }

            function showModal() {
                dialog.showModal();
            }

            arrays.forEach(dialog.querySelectorAll("input[type='image'],button"), function (button) {
                events.add(button, "click", saveAndClose);
            });

            arrays.forEach(document.querySelectorAll(".cookiecontrolbutton"), function (button) {
                events.add(button, "click", function (event) {
                    event.preventDefault();
                    showModal();
                });
            });

            if (showNotification === "true") {
                showModal();
            }


            const button = document.querySelector('.js-manage-cookies');
            const hiddenSection = document.querySelector('.js-hidden-section');
            const firstPart = document.querySelector('.js-first-line');
            button.addEventListener('click', () => {
                if (hiddenSection.classList.contains('js-show-cookie')) {
                  if (checkbox.checked) {
                    saveAndClose();
                  } else {
                    if (!checkbox.checked) {
                      saveAndClose();
                    }
                  }
                } else {
                  hiddenSection.classList.add('js-show-cookie');
                  firstPart.classList.add('first-line-hidden');
                }
              });
              
            const acceptAll = document.querySelector('.js-accept-all');
            acceptAll.addEventListener('click', () => {
                checkbox.checked = true;
                saveAndClose();
            });
            const onlyRequired = document.querySelector('.js-only-required-cookies');
            onlyRequired.addEventListener('click', () => {
                if (checkbox.checked) {
                checkbox.checked = false;
                    saveAndClose();
                } else {
                    saveAndClose();
                }
            });
        });
        
        const helpers = {
            body: document.querySelector('body'),
            topScroll: 0,
            isScrollDisabled: false,
            disabledScrollClass: 'scroll-disabled',
    
            disableScroll: function() {
                if (!this.isScrollDisabled) {
                    this.topScroll = document.documentElement.scrollTop;
                    this.body.style.top = `-${this.topScroll}px`;
                    this.body.classList.add(this.disabledScrollClass);
                    this.isScrollDisabled = true;
                }
            },

            enableScroll: function() {
                this.body.removeAttribute('style');
                this.body.classList.remove(this.disabledScrollClass);
                document.documentElement.scrollTop = this.topScroll;
                this.isScrollDisabled = false;
            },
        };
        
        const dialogs = document.querySelectorAll('dialog');

        function checkDialogOpen() {
            let isDialogOpen = false;
            dialogs.forEach((dialog) => {
                if (dialog.hasAttribute('open')) {
                    isDialogOpen = true;
                }
            });
            return isDialogOpen;
        }
    
        function updateBodyClass() {
            if (checkDialogOpen()) {
                helpers.disableScroll();
            } else {
                helpers.enableScroll();
            }
        }
    
        dialogs.forEach((dialog) => {
            const observer = new MutationObserver(updateBodyClass);
            observer.observe(dialog, { attributes: true });
        });
    });

}(self));

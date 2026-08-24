"use strict";var t=require("electron/renderer"),r=require("electron/common");var n=`(function () {
  if (typeof window === 'undefined') return
  if (
    Object.prototype.hasOwnProperty.call(window, '__REACT_DEVTOOLS_GLOBAL_HOOK__') &&
    window.__REACT_DEVTOOLS_GLOBAL_HOOK__
  ) {
    return
  }

  var renderers = new Map()
  var listeners = {}
  var uidCounter = 0
  var commitWaiterRoot = typeof globalThis !== 'undefined' ? globalThis : window

  function getCommitWaitersArray() {
    if (!Array.isArray(commitWaiterRoot.__figmaHtmlDevtoolsCommitWaiters__)) {
      commitWaiterRoot.__figmaHtmlDevtoolsCommitWaiters__ = []
    }
    return commitWaiterRoot.__figmaHtmlDevtoolsCommitWaiters__
  }

  function flushCommitWaiters() {
    var commitWaiters = getCommitWaitersArray()
    if (!commitWaiters.length) return
    var copy = commitWaiters.slice()
    commitWaiters.length = 0
    for (var i = 0; i < copy.length; i++) {
      var waiter = copy[i]
      if (waiter && typeof waiter.resolve === 'function') {
        if (waiter.timer) clearTimeout(waiter.timer)
        waiter.resolve()
      }
    }
  }

  function inject(renderer) {
    var id = ++uidCounter
    renderers.set(id, renderer)
    return id
  }

  function on(event, fn) {
    if (!listeners[event]) listeners[event] = []
    listeners[event].push(fn)
  }

  function off(event, fn) {
    var handlers = listeners[event]
    if (!handlers) return
    var index = handlers.indexOf(fn)
    if (index !== -1) handlers.splice(index, 1)
    if (handlers.length === 0) delete listeners[event]
  }

  function sub(event, fn) {
    on(event, fn)
    return function () { off(event, fn) }
  }

  function emit(event, data) {
    var handlers = listeners[event]
    if (!handlers) return
    var copy = handlers.slice()
    for (var i = 0; i < copy.length; i++) copy[i](data)
  }

  var hook = {
    supportsFiber: true,
    renderers: renderers,
    listeners: listeners,
    inject: inject,
    onCommitFiberRoot: function () {
      flushCommitWaiters()
    },
    onCommitFiberUnmount: function () {},
    onPostCommitFiberRoot: function () {},
    setStrictMode: function () {},
    checkDCE: function () {},
    getInternalModuleRanges: function () { return null },
    registerInternalModuleStart: function () {},
    registerInternalModuleStop: function () {},
    on: on,
    off: off,
    sub: sub,
    emit: emit,
  }

  commitWaiterRoot.__figmaHtmlDevtoolsCommitHookFlushesWaiters__ = true

  Object.defineProperty(window, '__REACT_DEVTOOLS_GLOBAL_HOOK__', {
    configurable: true,
    enumerable: false,
    get: function () { return hook },
  })
})();
`;function o(){return["/* Devtools installer */",n].join(`
`)}function i(e){return`makeLocalBrowserPreview:${e}`}t.contextBridge.exposeInMainWorld("__figmaPreviewIpc",{send(e,s){typeof e!="string"||e.length===0||t.ipcRenderer.send(i("message"),{type:e,data:s})}});r.crashReporter.addExtraParameter("sentry[tags][process]","renderer");r.crashReporter.addExtraParameter("sentry[tags][crash_source]","make_local_browser_preview");var a={async loadComponentDescriptor(e){return await t.ipcRenderer.invoke(i("loadComponentDescriptor"),e)}};t.contextBridge.exposeInMainWorld("__figmaCodeConnect",a);t.webFrame.executeJavaScriptInIsolatedWorld(0,[{code:o()}]);

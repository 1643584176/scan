;(function () {
  var ROOT_ID = 'figma-community-published-banner'
  var HIDDEN_CLASS = 'figma-community-published-banner-hidden'
  var DETAILS_URL = '/__figma__/api/community_published_banner_details'
  var SVG_NAMESPACE = 'http://www.w3.org/2000/svg'
  var FIGMA_MAKE_ICON_PATH =
    'M13.992 12a.5.5 0 0 1 .5.507l-.002.172c-.049 1.564-.265 2.983-.598 4.064-.189.615-.425 1.149-.71 1.54-.276.38-.67.717-1.182.717-.513 0-.906-.337-1.183-.717-.284-.391-.52-.925-.71-1.54l-.055-.185c-.09-.322.175-.626.508-.605a.52.52 0 0 1 .467.375l.036.121c.173.561.369.98.563 1.246.2.276.333.305.374.305s.172-.028.374-.305c.194-.266.39-.685.562-1.246.3-.977.507-2.304.554-3.799l.002-.158a.5.5 0 0 1 .5-.492M7.44 10.054c.322-.091.625.173.606.506a.52.52 0 0 1-.374.467l-.122.037c-.56.172-.98.368-1.246.562-.277.202-.304.335-.304.374 0 .04.027.172.304.374.267.194.685.39 1.246.563.977.3 2.304.506 3.8.553l.157.002a.5.5 0 0 1-.015 1l-.171-.003c-1.564-.049-2.983-.264-4.065-.596-.614-.19-1.148-.426-1.54-.71C5.336 12.906 5 12.513 5 12s.336-.906.716-1.183c.392-.284.926-.52 1.54-.71zm5.238-.543c1.564.048 2.983.264 4.065.596.615.19 1.149.426 1.54.71.38.277.717.67.717 1.183s-.337.906-.717 1.183c-.391.284-.925.52-1.54.71q-.09.027-.185.053c-.322.09-.625-.174-.605-.508a.52.52 0 0 1 .374-.465l.122-.037c.561-.172.98-.368 1.246-.562.277-.202.305-.335.305-.374 0-.04-.028-.172-.305-.374-.267-.194-.685-.39-1.246-.562-.977-.301-2.304-.508-3.799-.554l-.158-.002a.5.5 0 0 1 .015-1zM12 5c.512 0 .906.337 1.182.717.285.391.521.925.71 1.54q.028.09.054.183a.484.484 0 0 1-.508.606.52.52 0 0 1-.467-.375l-.035-.12c-.172-.561-.368-.98-.562-1.246C12.172 6.028 12.039 6 12 6c-.04 0-.174.029-.374.305-.194.266-.39.685-.563 1.246-.31 1.01-.52 2.393-.558 3.949A.51.51 0 0 1 10 12a.49.49 0 0 1-.495-.5c.038-1.634.257-3.12.602-4.243.19-.615.426-1.149.71-1.54.277-.38.67-.717 1.183-.717'
  var MORE_ICON_PATH =
    'M6 10.5C6.82843 10.5 7.5 11.1716 7.5 12C7.5 12.8284 6.82843 13.5 6 13.5C5.17157 13.5 4.5 12.8284 4.5 12C4.5 11.1716 5.17157 10.5 6 10.5ZM12 10.5C12.8284 10.5 13.5 11.1716 13.5 12C13.5 12.8284 12.8284 13.5 12 13.5C11.1716 13.5 10.5 12.8284 10.5 12C10.5 11.1716 11.1716 10.5 12 10.5ZM18 10.5C18.8284 10.5 19.5 11.1716 19.5 12C19.5 12.8284 18.8284 13.5 18 13.5C17.1716 13.5 16.5 12.8284 16.5 12C16.5 11.1716 17.1716 10.5 18 10.5Z'
  var CLOSE_ICON_PATH =
    'M16.6465 6.64648C16.8417 6.45122 17.1583 6.45122 17.3535 6.64648C17.5488 6.84175 17.5488 7.15825 17.3535 7.35352L12.707 12L17.3535 16.6465C17.5488 16.8417 17.5488 17.1583 17.3535 17.3535C17.1583 17.5488 16.8417 17.5488 16.6465 17.3535L12 12.707L7.35352 17.3535C7.15825 17.5488 6.84175 17.5488 6.64648 17.3535C6.45122 17.1583 6.45122 16.8417 6.64648 16.6465L11.293 12L6.64648 7.35352C6.45127 7.15825 6.45124 6.84173 6.64648 6.64648C6.84173 6.45129 7.15827 6.45129 7.35352 6.64648L12 11.293L16.6465 6.64648Z'
  var REPORT_ICON_PATH =
    'M6.5 6a.5.5 0 0 1 .5.5V7h10a1 1 0 0 1 1 1v7a1 1 0 0 1-1 1H7v2.5a.5.5 0 0 1-1 0v-12a.5.5 0 0 1 .5-.5M7 8v7h10V8zm6.854 1.446a.5.5 0 0 1 0 .707L12.707 11.3l1.147 1.146a.5.5 0 0 1-.708.707L12 12.007l-1.146 1.146a.5.5 0 0 1-.708-.707l1.147-1.146-1.147-1.147a.5.5 0 0 1 .708-.707L12 10.593l1.146-1.147a.5.5 0 0 1 .708 0'

  function appendText(parent, text) {
    parent.appendChild(document.createTextNode(text || ''))
  }

  function safeUrl(value) {
    if (typeof value !== 'string' || value.length === 0) {
      return '#'
    }

    try {
      var url = new URL(value, window.location.origin)
      if (url.protocol === 'http:' || url.protocol === 'https:') {
        return url.href
      }
    } catch (_error) {
      return '#'
    }

    return '#'
  }

  function createElement(tagName, options) {
    var element = document.createElement(tagName)
    options = options || {}

    if (options.className) {
      element.className = options.className
    }
    if (options.text) {
      appendText(element, options.text)
    }
    if (options.href) {
      element.href = safeUrl(options.href)
      element.target = '_blank'
      element.rel = 'noreferrer'
    }
    if (options.title) {
      element.title = options.title
      element.setAttribute('aria-label', options.title)
    }
    if (options.type) {
      element.type = options.type
    }

    return element
  }

  function createStyles() {
    var style = document.createElement('style')
    style.textContent =
      ':host{all:initial!important;display:block!important}' +
      ':host(.' +
      HIDDEN_CLASS +
      '){display:none!important}' +
      '.figma-community-banner{box-sizing:border-box;font-family:Inter,sans-serif;font-size:11px;line-height:16px;letter-spacing:.055px;color:rgba(0,0,0,.9)}' +
      '.figma-community-banner *{box-sizing:border-box}' +
      '.figma-community-banner svg{display:block;width:24px;height:24px;flex-shrink:0}' +
      '.figma-community-banner a{color:inherit;text-decoration:none}' +
      '.figma-community-banner-remix{display:flex;align-items:center;min-height:32px;padding:4px 12px;border-radius:5px;background:#1e1e1e;color:#fff;font:inherit;font-weight:450;white-space:nowrap}' +
      '.figma-community-banner-v2{position:fixed;right:40px;bottom:20px;z-index:999;display:flex;align-items:center;gap:8px;overflow:visible;width:fit-content;height:40px;padding:0 0 0 8px;border-radius:13px;background:#fff;box-shadow:0 0 .5px 0 rgba(0,0,0,.3),0 1px 3px 0 rgba(0,0,0,.15)}' +
      '.figma-community-banner-make-icon{display:block;width:24px;height:24px;color:rgba(0,0,0,.9);flex-shrink:0}' +
      '.figma-community-banner-v2-text{display:flex;align-items:center;height:32px;padding:8px 4px;color:rgba(0,0,0,.9);font-weight:550;white-space:nowrap}' +
      '.figma-community-banner-v2-cta{display:flex;flex-direction:row;align-self:stretch;align-items:center;justify-content:flex-end;position:relative;height:100%;flex-shrink:0}' +
      '.figma-community-banner-v2 .figma-community-banner-remix{min-height:24px;margin-right:8px;padding:0 8px;border:1px solid rgba(0,0,0,.1);background:#4d49fc;color:#fff}' +
      '.figma-community-banner-divider{display:flex;align-self:stretch;align-items:center;height:100%;border-left:1px solid rgba(0,0,0,.1);position:relative;flex-shrink:0}' +
      '.figma-community-banner-icon-button{display:flex;align-items:center;justify-content:center;width:40px;height:40px;padding:8px;border:0;border-radius:4px;background:transparent;color:rgba(0,0,0,.5);cursor:pointer;font:inherit;line-height:0}' +
      '.figma-community-banner-menu{position:absolute;right:0;bottom:100%;z-index:2147483001;margin-bottom:8px;padding:8px;border-radius:11px;background:#fff;box-shadow:0 0 .5px rgba(0,0,0,.3),0 1px 3px rgba(0,0,0,.15);white-space:nowrap}' +
      '.figma-community-banner-menu a{display:flex;align-items:center;gap:4px;font:inherit;font-weight:400;line-height:20px}'
    return style
  }

  function createBannerHost() {
    var root = document.createElement('div')
    root.id = ROOT_ID
    root.style.setProperty('all', 'initial', 'important')
    root.style.setProperty('display', 'block', 'important')

    if (typeof root.attachShadow !== 'function') {
      return null
    }

    var shadowRoot = root.attachShadow({ mode: 'closed' })
    shadowRoot.appendChild(createStyles())
    return {
      root: root,
      shadowRoot: shadowRoot,
    }
  }

  function createIcon(pathData) {
    var svg = document.createElementNS(SVG_NAMESPACE, 'svg')
    var path = document.createElementNS(SVG_NAMESPACE, 'path')
    svg.setAttribute('width', '24')
    svg.setAttribute('height', '24')
    svg.setAttribute('fill', 'none')
    svg.setAttribute('viewBox', '0 0 24 24')
    path.setAttribute('fill', 'currentColor')
    path.setAttribute('d', pathData)
    svg.appendChild(path)
    return svg
  }

  function renderBannerContent(meta, root) {
    var banner = createElement('div', {
      className: 'figma-community-banner figma-community-banner-v2',
    })
    var icon = createElement('div', { className: 'figma-community-banner-make-icon' })
    var text = createElement('div', {
      className: 'figma-community-banner-v2-text',
      text: meta.banner_v2_text,
    })
    var ctaRail = createElement('div', { className: 'figma-community-banner-v2-cta' })
    var remix = createElement('a', {
      className: 'figma-community-banner-remix',
      href: meta.hub_file_url,
      text: meta.remix_button_text,
    })
    var menuDivider = createElement('div', { className: 'figma-community-banner-divider' })
    var moreButton = createElement('button', {
      className: 'figma-community-banner-icon-button',
      title: meta.more_options_text,
      type: 'button',
    })
    var menu = createElement('div', { className: 'figma-community-banner-menu' })
    var report = createElement('a', {
      href: meta.report_abuse_url,
      title: meta.report_button_text,
      text: meta.report_button_text,
    })
    var closeDivider = createElement('div', { className: 'figma-community-banner-divider' })
    var closeButton = createElement('button', {
      className: 'figma-community-banner-icon-button',
      title: meta.close_text,
      type: 'button',
    })

    icon.appendChild(createIcon(FIGMA_MAKE_ICON_PATH))
    moreButton.appendChild(createIcon(MORE_ICON_PATH))
    report.prepend(createIcon(REPORT_ICON_PATH))
    closeButton.appendChild(createIcon(CLOSE_ICON_PATH))

    menu.hidden = true
    menu.appendChild(report)
    moreButton.addEventListener('click', function (event) {
      event.stopPropagation()
      menu.hidden = !menu.hidden
    })
    closeButton.addEventListener('click', function () {
      root.classList.add(HIDDEN_CLASS)
      root.style.setProperty('display', 'none', 'important')
    })

    menuDivider.appendChild(moreButton)
    menuDivider.appendChild(menu)
    closeDivider.appendChild(closeButton)
    ctaRail.appendChild(remix)
    ctaRail.appendChild(menuDivider)
    ctaRail.appendChild(closeDivider)
    banner.appendChild(icon)
    banner.appendChild(text)
    banner.appendChild(ctaRail)
    return banner
  }

  function renderBanner(meta) {
    if (!document.body || document.getElementById(ROOT_ID)) {
      return
    }

    var bannerHost = createBannerHost()
    if (!bannerHost) {
      return
    }

    bannerHost.shadowRoot.appendChild(renderBannerContent(meta, bannerHost.root))
    document.body.prepend(bannerHost.root)
  }

  function hasRenderableMetadata(meta) {
    return (
      meta &&
      typeof meta.hub_file_url === 'string' &&
      typeof meta.report_abuse_url === 'string' &&
      typeof meta.remix_button_text === 'string' &&
      typeof meta.report_button_text === 'string'
    )
  }

  function fetchAndRender() {
    fetch(DETAILS_URL, { redirect: 'follow' })
      .then(function (response) {
        if (!response.ok) {
          return null
        }
        return response.json()
      })
      .then(function (data) {
        if (data && hasRenderableMetadata(data.meta)) {
          renderBanner(data.meta)
        }
      })
      .catch(function (error) {
        console.warn('Unable to render Figma Make community banner', error)
      })
  }

  if (document.readyState === 'loading') {
    document.addEventListener('DOMContentLoaded', fetchAndRender, { once: true })
  } else {
    fetchAndRender()
  }
})()

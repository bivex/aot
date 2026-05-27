var DAEMON = 'http://localhost:8089?dummy=1';

chrome.runtime.onInstalled.addListener(() => {
  chrome.contextMenus.create({
    id: 'aot-analyze',
    title: 'Analyze with AOT (new tab)',
    contexts: ['selection']
  });
  chrome.contextMenus.create({
    id: 'aot-render-page',
    title: 'Render Subj-Pred on Page',
    contexts: ['page', 'selection']
  });
});

// ── Message handler ─────────────────────────────────────────

chrome.runtime.onMessage.addListener((msg, sender, sendResponse) => {
  if (msg.action === 'analyze') {
    fetchAndOpenTab(msg.text, msg.lang, sendResponse);
    return true;
  }

  if (msg.action === 'render-page') {
    fetchAndRenderOnPage(msg.text, msg.lang, sendResponse);
    return true;
  }
});

// ── Context menu ────────────────────────────────────────────

chrome.contextMenus.onClicked.addListener((info, tab) => {
  if (info.menuItemId === 'aot-analyze' && info.selectionText) {
    fetchAndOpenTab(info.selectionText, null);
  }

  if (info.menuItemId === 'aot-render-page') {
    extractAndRenderOnPage(info, tab);
  }
});

// ── Shared logic ────────────────────────────────────────────

function detectLang(text) {
  var cyrillic = (text.match(/[Ѐ-ӿ]/g) || []).length;
  var latin = (text.match(/[a-zA-Z]/g) || []).length;
  if (cyrillic > latin * 0.5) {
    var ukr = (text.match(/[іїєґ]/gi) || []).length;
    return ukr > 0 ? 'Ukrainian' : 'Russian';
  }
  return 'English';
}

function fetchDaemon(text, lang) {
  return fetch(DAEMON + '&action=syntax&langua=' + lang, { method: 'POST', body: text })
    .then(r => { if (!r.ok) throw new Error('Server ' + r.status); return r.json(); });
}

// ── Analyze in new tab ──────────────────────────────────────

function fetchAndOpenTab(text, lang, sendResponse) {
  lang = lang || detectLang(text);
  fetchDaemon(text, lang)
    .then(json => {
      chrome.storage.local.set({ aotResult: JSON.stringify(json), aotLang: lang }, () => {
        chrome.tabs.create({ url: chrome.runtime.getURL('result.html') });
        if (sendResponse) sendResponse({ ok: true });
      });
    })
    .catch(err => { if (sendResponse) sendResponse({ ok: false, error: err.message }); });
}

// ── Render overlay on page ──────────────────────────────────

function fetchAndRenderOnPage(text, lang, sendResponse) {
  lang = lang || detectLang(text);
  fetchDaemon(text, lang)
    .then(json => {
      chrome.tabs.query({ active: true, lastFocusedWindow: true }, (tabs) => {
        if (!tabs[0]) {
          if (sendResponse) sendResponse({ ok: false, error: 'No active tab' });
          return;
        }
        injectOverlay(tabs[0].id, json, lang);
        if (sendResponse) sendResponse({ ok: true });
      });
    })
    .catch(err => { if (sendResponse) sendResponse({ ok: false, error: err.message }); });
}

function extractAndRenderOnPage(info, tab) {
  chrome.scripting.executeScript({
    target: { tabId: tab.id },
    func: (hasSel, selText) => {
      if (hasSel && selText && selText.trim().length > 20) return selText.trim();
      var sel = window.getSelection().toString().trim();
      if (sel.length > 20) return sel;
      var main = document.querySelector('main, article, [role="main"], .post-content, .entry-content, .article-body');
      return ((main || document.body).innerText || '').trim();
    },
    args: [!!info.selectionText, info.selectionText]
  }, (results) => {
    if (chrome.runtime.lastError || !results || !results[0]) return;
    var text = results[0].result.substring(0, 10000);
    if (!text) return;
    var lang = detectLang(text);
    fetchDaemon(text, lang).then(json => injectOverlay(tab.id, json, lang));
  });
}

// ── Inject overlay into page ────────────────────────────────

function injectOverlay(tabId, json, lang) {
  // Step 1: Create overlay DOM
  chrome.scripting.executeScript({
    target: { tabId: tabId },
    func: (langStr) => {
      var existing = document.getElementById('aot-overlay');
      if (existing) existing.remove();

      var overlay = document.createElement('div');
      overlay.id = 'aot-overlay';
      overlay.style.cssText = 'position:fixed;top:0;right:0;width:55vw;height:100vh;z-index:2147483647;' +
        'background:#fff;border-left:2px solid #1a252f;box-shadow:-4px 0 24px rgba(0,0,0,0.25);' +
        'display:flex;flex-direction:column;font-family:-apple-system,BlinkMacSystemFont,system-ui,sans-serif;' +
        'animation:aotSlideIn .25s ease-out;';

      var style = document.createElement('style');
      style.textContent = '@keyframes aotSlideIn{from{transform:translateX(100%)}to{transform:translateX(0)}}' +
        '@keyframes aotSpin{to{transform:rotate(360deg)}}';
      overlay.appendChild(style);

      var header = document.createElement('div');
      header.style.cssText = 'display:flex;align-items:center;gap:12px;padding:10px 16px;' +
        'background:#1a252f;color:#fff;flex-shrink:0;';
      header.innerHTML =
        '<span style="font-weight:700;font-size:15px">AOT<span style="color:#c98">.</span> Syntax</span>' +
        '<span style="font-size:11px;padding:2px 8px;border-radius:4px;background:rgba(255,255,255,0.15);font-weight:600">' + langStr + '</span>' +
        '<span style="flex:1"></span>' +
        '<button id="aot-save" style="background:rgba(255,255,255,0.1);border:1px solid rgba(255,255,255,0.2);color:#fff;padding:4px 12px;border-radius:4px;cursor:pointer;font-size:12px;font-weight:600">Save SVG</button>' +
        '<button id="aot-close" style="background:none;border:none;color:#fff;font-size:22px;cursor:pointer;line-height:1">&times;</button>';
      overlay.appendChild(header);

      var loading = document.createElement('div');
      loading.id = 'aot-loading';
      loading.style.cssText = 'text-align:center;padding:60px 20px;color:#888;flex:1;';
      loading.innerHTML = '<div style="width:28px;height:28px;border:3px solid #ddd;border-top-color:#1a252f;border-radius:50%;animation:aotSpin .7s linear infinite;margin:0 auto 12px"></div>' +
        '<div>Rendering syntax tree...</div>';
      overlay.appendChild(loading);

      var container = document.createElement('div');
      container.id = 'svgContainer';
      container.style.cssText = 'width:100%;flex:1;overflow:auto;background:#fff;min-height:300px;';
      overlay.appendChild(container);

      document.body.appendChild(overlay);
      header.querySelector('#aot-close').onclick = function() { overlay.remove(); };
    },
    args: [lang]
  }, () => {
    // Step 2: Inject D3
    chrome.scripting.executeScript({
      target: { tabId: tabId },
      files: ['libs/d3.min.js']
    }, () => {
      // Step 3: Inject synan_viz
      chrome.scripting.executeScript({
        target: { tabId: tabId },
        files: ['synan_viz.js']
      }, () => {
        // Step 4: Render
        chrome.scripting.executeScript({
          target: { tabId: tabId },
          func: (dataStr, langStr) => {
            var ld = document.getElementById('aot-loading');
            if (ld) ld.remove();

            CURRENT_LANG = langStr;
            try {
              var json = JSON.parse(dataStr);
              initCanvas();
              parseSynanJson(json);
              drawAll();
            } catch (e) {
              var c = document.getElementById('svgContainer');
              if (c) c.innerHTML = '<div style="padding:40px;color:#c00">Error: ' + e.message + '</div>';
            }

            var saveBtn = document.getElementById('aot-save');
            if (saveBtn) saveBtn.onclick = function() { saveSvg(); };
          },
          args: [JSON.stringify(json), lang]
        });
      });
    });
  });
}

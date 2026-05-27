var DAEMON = 'http://localhost:8089?dummy=1';

document.addEventListener('DOMContentLoaded', () => {
  checkServer();
  document.getElementById('btnExtract').onclick = extractFull;
  document.getElementById('btnSelection').onclick = extractSelection;
  document.getElementById('btnAnalyze').onclick = analyze;
  document.getElementById('btnRenderPage').onclick = renderOnPage;
});

function checkServer() {
  var dot = document.getElementById('serverDot');
  fetch(DAEMON, { method: 'GET', mode: 'no-cors' })
    .then(() => dot.className = 'server-status server-ok')
    .catch(() => dot.className = 'server-status server-err');
}

function detectLang(text) {
  var cyrillic = (text.match(/[Ѐ-ӿ]/g) || []).length;
  var latin = (text.match(/[a-zA-Z]/g) || []).length;
  if (cyrillic > latin * 0.5) {
    var ukr = (text.match(/[іїєґ]/gi) || []).length;
    return ukr > 0 ? 'Ukrainian' : 'Russian';
  }
  return 'English';
}

function getLang() {
  var v = document.getElementById('lang').value;
  return v === 'auto' ? null : v;
}

function isSupportedPage(url) {
  if (!url) return false;
  return url.startsWith('http://') || url.startsWith('https://');
}

function extractFull() {
  chrome.tabs.query({ active: true, currentWindow: true }, (tabs) => {
    if (!tabs[0] || !isSupportedPage(tabs[0].url)) {
      status('Cannot extract from this page', true);
      return;
    }

    // Try content script first, fall back to scripting API
    chrome.tabs.sendMessage(tabs[0].id, { action: 'extract' }, (resp) => {
      if (chrome.runtime.lastError || !resp) {
        // Content script not loaded — inject on the fly
        chrome.scripting.executeScript({
          target: { tabId: tabs[0].id },
          files: ['content.js']
        }, () => {
          if (chrome.runtime.lastError) {
            status('Cannot access this page', true);
            return;
          }
          chrome.tabs.sendMessage(tabs[0].id, { action: 'extract' }, (resp2) => {
            if (chrome.runtime.lastError || !resp2 || !resp2.text) {
              status('Failed to extract text', true);
              return;
            }
            fillText(resp2.text, resp2.lang);
          });
        });
        return;
      }
      if (resp.text) {
        fillText(resp.text, resp.lang);
      }
    });
  });
}

function fillText(text, lang) {
  document.getElementById('text').value = text.substring(0, 10000);
  if (!getLang() && lang) {
    document.getElementById('lang').value = lang;
  }
  status('Extracted ' + text.length + ' characters');
}

function extractSelection() {
  chrome.tabs.query({ active: true, currentWindow: true }, (tabs) => {
    if (!tabs[0] || !isSupportedPage(tabs[0].url)) {
      status('Cannot access this page', true);
      return;
    }
    chrome.scripting.executeScript({
      target: { tabId: tabs[0].id },
      func: () => window.getSelection().toString()
    }, (results) => {
      var sel = results && results[0] && results[0].result;
      if (sel && sel.trim().length > 0) {
        fillText(sel.trim(), null);
        if (!getLang()) {
          document.getElementById('lang').value = detectLang(sel);
        }
      } else {
        status('No text selected on page', true);
      }
    });
  });
}

function analyze() {
  var text = document.getElementById('text').value.trim();
  if (!text) { status('Paste or extract text first', true); return; }

  var lang = getLang() || detectLang(text);
  status('Analyzing (' + lang + ')...');

  chrome.runtime.sendMessage({ action: 'analyze', text: text, lang: lang }, (resp) => {
    if (chrome.runtime.lastError) {
      status('Error: ' + chrome.runtime.lastError.message, true);
      return;
    }
    if (resp && resp.ok) {
      status('Opening result...');
    } else if (resp && resp.error) {
      status('Error: ' + resp.error, true);
    }
  });
}

function status(msg, isErr) {
  var el = document.getElementById('status');
  el.textContent = msg;
  el.className = isErr ? 'status error' : 'status';
}

function renderOnPage() {
  var text = document.getElementById('text').value.trim();
  if (!text) { status('Paste or extract text first', true); return; }

  var lang = getLang() || detectLang(text);
  status('Rendering on page...');

  chrome.runtime.sendMessage({ action: 'render-page', text: text, lang: lang }, (resp) => {
    if (chrome.runtime.lastError) {
      status('Error: ' + chrome.runtime.lastError.message, true);
      return;
    }
    if (resp && resp.ok) {
      status('Rendered on page');
    } else if (resp && resp.error) {
      status('Error: ' + resp.error, true);
    }
  });
}

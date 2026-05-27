var DAEMON = 'http://localhost:8089?dummy=1';

document.addEventListener('DOMContentLoaded', () => {
  checkServer();
  document.getElementById('btnExtract').onclick = extractFull;
  document.getElementById('btnSelection').onclick = extractSelection;
  document.getElementById('btnAnalyze').onclick = analyze;
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

function extractFull() {
  chrome.tabs.query({ active: true, currentWindow: true }, (tabs) => {
    chrome.tabs.sendMessage(tabs[0].id, { action: 'extract' }, (resp) => {
      if (chrome.runtime.lastError) {
        status('Error: cannot access page', true);
        return;
      }
      if (resp && resp.text) {
        document.getElementById('text').value = resp.text.substring(0, 10000);
        if (!getLang() && resp.lang) {
          document.getElementById('lang').value = resp.lang;
        }
        status('Extracted ' + resp.text.length + ' characters');
      }
    });
  });
}

function extractSelection() {
  chrome.tabs.query({ active: true, currentWindow: true }, (tabs) => {
    chrome.scripting.executeScript({
      target: { tabId: tabs[0].id },
      func: () => window.getSelection().toString()
    }, (results) => {
      var sel = results && results[0] && results[0].result;
      if (sel && sel.trim().length > 0) {
        document.getElementById('text').value = sel.trim().substring(0, 10000);
        if (!getLang()) {
          document.getElementById('lang').value = detectLang(sel);
        }
        status('Extracted selection: ' + sel.length + ' chars');
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

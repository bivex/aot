chrome.runtime.onInstalled.addListener(() => {
  chrome.contextMenus.create({
    id: 'aot-analyze',
    title: 'Analyze with AOT',
    contexts: ['selection']
  });
});

chrome.runtime.onMessage.addListener((msg, sender, sendResponse) => {
  if (msg.action === 'analyze') {
    var lang = msg.lang || 'English';
    var text = msg.text;
    var daemonUrl = 'http://localhost:8089?dummy=1&action=syntax&langua=' + lang;

    fetch(daemonUrl, { method: 'POST', body: text })
      .then(r => {
        if (!r.ok) throw new Error('Server returned ' + r.status);
        return r.json();
      })
      .then(json => {
        chrome.storage.local.set({
          aotResult: JSON.stringify(json),
          aotLang: lang
        }, () => {
          chrome.tabs.create({ url: chrome.runtime.getURL('result.html') });
          sendResponse({ ok: true });
        });
      })
      .catch(err => {
        sendResponse({ ok: false, error: err.message });
      });

    return true; // keep message channel open for async response
  }
});

chrome.contextMenus.onClicked.addListener((info, tab) => {
  if (info.menuItemId === 'aot-analyze' && info.selectionText) {
    var text = info.selectionText;
    var cyrillic = (text.match(/[Ѐ-ӿ]/g) || []).length;
    var latin = (text.match(/[a-zA-Z]/g) || []).length;
    var lang = 'English';
    if (cyrillic > latin * 0.5) {
      var ukr = (text.match(/[іїєґ]/gi) || []).length;
      lang = ukr > 0 ? 'Ukrainian' : 'Russian';
    }

    var daemonUrl = 'http://localhost:8089?dummy=1&action=syntax&langua=' + lang;
    fetch(daemonUrl, { method: 'POST', body: text })
      .then(r => {
        if (!r.ok) throw new Error('Server returned ' + r.status);
        return r.json();
      })
      .then(json => {
        chrome.storage.local.set({
          aotResult: JSON.stringify(json),
          aotLang: lang
        }, () => {
          chrome.tabs.create({ url: chrome.runtime.getURL('result.html') });
        });
      })
      .catch(err => {
        console.error('AOT analysis failed:', err);
      });
  }
});

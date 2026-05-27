chrome.runtime.onInstalled.addListener(() => {
  chrome.contextMenus.create({
    id: 'aot-analyze',
    title: 'Analyze with AOT',
    contexts: ['selection']
  });
});

chrome.contextMenus.onClicked.addListener((info, tab) => {
  if (info.menuItemId === 'aot-analyze' && info.selectionText) {
    chrome.tabs.sendMessage(tab.id, {
      action: 'analyze',
      text: info.selectionText,
      lang: detectLang(info.selectionText)
    });
  }
});

function detectLang(text) {
  var cyrillic = (text.match(/[Ѐ-ӿ]/g) || []).length;
  var latin = (text.match(/[a-zA-Z]/g) || []).length;
  if (cyrillic > latin * 0.5) {
    var ukrLetters = (text.match(/[іїєїґі]/g) || []).length;
    return ukrLetters > 0 ? 'Ukrainian' : 'Russian';
  }
  return 'English';
}

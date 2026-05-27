chrome.runtime.onMessage.addListener((msg, sender, sendResponse) => {
  if (msg.action === 'extract') {
    var text = extractPageText();
    sendResponse({ text: text, lang: detectPageLang() });
  }
  if (msg.action === 'analyze') {
    showOverlay(msg.text, msg.lang);
  }
});

function extractPageText() {
  var sel = window.getSelection().toString().trim();
  if (sel && sel.length > 20) return sel;

  var main = document.querySelector('main, article, [role="main"], .post-content, .entry-content, .article-body');
  if (main) return main.innerText.trim();

  return document.body.innerText.trim();
}

function detectPageLang() {
  var lang = document.documentElement.lang || '';
  lang = lang.toLowerCase();
  if (lang.startsWith('uk')) return 'Ukrainian';
  if (lang.startsWith('ru')) return 'Russian';
  if (lang.startsWith('en')) return 'English';

  var text = (document.body.innerText || '').substring(0, 500);
  var cyrillic = (text.match(/[Ѐ-ӿ]/g) || []).length;
  var latin = (text.match(/[a-zA-Z]/g) || []).length;
  if (cyrillic > latin * 0.5) {
    var ukr = (text.match(/[іїєґ]/gi) || []).length;
    return ukr > 0 ? 'Ukrainian' : 'Russian';
  }
  return 'English';
}

function showOverlay(text, lang) {
  var existing = document.getElementById('aot-overlay');
  if (existing) existing.remove();

  var overlay = document.createElement('div');
  overlay.id = 'aot-overlay';
  overlay.style.cssText = 'position:fixed;top:0;right:0;width:50%;height:100%;z-index:999999;background:#fff;border-left:2px solid #1a252f;box-shadow:-4px 0 20px rgba(0,0,0,0.2);overflow:auto;font-family:system-ui,sans-serif;';

  var header = document.createElement('div');
  header.style.cssText = 'display:flex;justify-content:space-between;align-items:center;padding:12px 16px;background:#1a252f;color:#fff;';
  header.innerHTML = '<span style="font-weight:bold;font-size:16px">AOT Syntax Analysis</span><button style="background:none;border:none;color:#fff;font-size:20px;cursor:pointer">&times;</button>';
  header.querySelector('button').onclick = () => overlay.remove();

  var container = document.createElement('div');
  container.id = 'svgContainer';
  container.style.cssText = 'width:100%;min-height:400px;padding:8px;';

  overlay.appendChild(header);
  overlay.appendChild(container);
  document.body.appendChild(overlay);

  window.dispatchEvent(new CustomEvent('aot-analyze', { detail: { text, lang } }));
}

chrome.storage.local.get(['aotResult', 'aotLang'], function(data) {
  if (!data.aotResult) {
    document.getElementById('svgContainer').innerHTML =
      '<div style="text-align:center;padding:80px;color:#888">No analysis data. Open the extension popup and analyze text first.</div>';
    return;
  }

  var lang = data.aotLang || 'English';
  CURRENT_LANG = lang;
  document.getElementById('langBadge').textContent = lang;

  try {
    var json = JSON.parse(data.aotResult);
    initCanvas();
    parseSynanJson(json);
    drawAll();
  } catch (e) {
    document.getElementById('svgContainer').innerHTML =
      '<div style="text-align:center;padding:80px;color:#c00">Parse error: ' + e.message + '</div>';
  }

  chrome.storage.local.remove(['aotResult', 'aotLang']);
});

var _resizeTimer;
window.addEventListener('resize', function() {
  clearTimeout(_resizeTimer);
  _resizeTimer = setTimeout(function() { if (TopClauses.length > 0) drawAll(); }, 250);
});

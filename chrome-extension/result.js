function clearLoading() {
  var container = document.getElementById('svgContainer');
  var loading = container.querySelector('.loading');
  if (loading) loading.remove();
}

function showError(msg) {
  clearLoading();
  document.getElementById('svgContainer').innerHTML =
    '<div style="text-align:center;padding:80px;color:#c00">' + msg + '</div>';
}

chrome.storage.local.get(['aotResult', 'aotLang'], function(data) {
  if (chrome.runtime.lastError) {
    showError('Storage error: ' + chrome.runtime.lastError.message);
    return;
  }

  if (!data.aotResult) {
    showError('No analysis data. Open the extension popup and analyze text first.');
    return;
  }

  var lang = data.aotLang || 'English';
  CURRENT_LANG = lang;
  document.getElementById('langBadge').textContent = lang;

  try {
    var json = JSON.parse(data.aotResult);
    clearLoading();
    initCanvas();
    parseSynanJson(json);
    drawAll();
  } catch (e) {
    showError('Parse error: ' + e.message);
  }

  chrome.storage.local.remove(['aotResult', 'aotLang']);
});

var _resizeTimer;
window.addEventListener('resize', function() {
  clearTimeout(_resizeTimer);
  _resizeTimer = setTimeout(function() { if (TopClauses.length > 0) drawAll(); }, 250);
});

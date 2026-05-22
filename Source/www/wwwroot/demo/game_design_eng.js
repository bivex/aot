// ═════════════════════════════════════════════════════════════════════
//  game_design_eng.js — Narrative Skeleton Extractor for Game Design
// ═════════════════════════════════════════════════════════════════════

var SynanDaemonUrl = 'http://localhost:8089?dummy=1';
var extractedScenes = [];

// ── POS helpers ──────────────────────────────────────────────────────

function getPos(g) {
    if (!g) return 'UNK';
    var p = (g.split(/[\s;,]/)[0] || '').trim().replace(/[\x00-\x1f\x7f-\x9f\xa0]/g, '').toUpperCase();
    var map = {
        'N':'NOUN','A':'ADJ','V':'VERB','ADV':'ADV',
        'PRON':'PRON','PREP':'PREP','CONJ':'CONJ',
        'PART':'PART','INT':'INT','NUM':'NUM',
        'MOD':'MOD','ARTICLE':'ART','PN':'PN',
        'INFINITIVE':'VERB','PARTICIPLE':'ADJ','VBE':'VERB',
        'ADJ_SHORT':'ADJ','PUNC':'UNK','PUNCT':'UNK','SENT':'UNK'
    };
    return map[p] || 'UNK';
}

function isVerb(pos) { return pos === 'VERB' || pos === 'MOD'; }
function isNoun(pos) { return pos === 'NOUN' || pos === 'PN' || pos === 'PRON'; }

// ── Scene extraction ─────────────────────────────────────────────────

function parseScenes(json) {
    var scenes = [];
    var idx = 0;

    json.forEach(function(sentence) {
        sentence.forEach(function(clause) {
            var words = clause.words || [];
            var variants = clause.variants || [];
            if (!words.length) return;

            var fullText = words.map(function(w) { return w.str; }).join(' ');

            // Collect all words with POS
            var wordData = [];
            var v = variants[0];
            if (v) {
                (v.units || []).forEach(function(u, i) {
                    if (!words[i]) return;
                    wordData.push({
                        word: words[i].str,
                        lemma: (words[i].homonyms || [])[u.homNo || 0] || words[i].str,
                        pos: getPos(u.grm),
                        idx: i
                    });
                });
            }
            // Fallback: no variant, just words
            if (!wordData.length) {
                words.forEach(function(w, i) {
                    wordData.push({ word: w.str, lemma: w.str, pos: 'UNK', idx: i });
                });
            }

            var subjects = [];
            var predicates = [];
            var objects = [];
            var settings = [];

            if (v) {
                (v.groups || []).forEach(function(g) {
                    var desc = (g.descr || '').replace(/\0/g, '').trim().toUpperCase();
                    var s = g.start, e = g.last;
                    if (s == null || e == null || !words[s]) return;
                    var phrase = words.slice(s, e + 1).map(function(w) { return w.str; }).join(' ');

                    if (g.isSubj) {
                        // Subject at start, predicate at last
                        var subjWords = [];
                        for (var i = s; i <= Math.min(s + 3, e - 1); i++) {
                            if (words[i]) subjWords.push(words[i].str);
                        }
                        subjects.push({ phrase: subjWords.join(' ') || phrase, startIdx: s });
                        if (words[e]) predicates.push({ phrase: words[e].str, startIdx: e });
                    } else if (desc.indexOf('ПОДЛЕЖ') >= 0 || desc === 'SUBJECT') {
                        subjects.push({ phrase: phrase, startIdx: s });
                    } else if (desc.indexOf('СКАЗ') >= 0 || desc.indexOf('ГЛ_ЛИЧН') >= 0 || desc.indexOf('PREDICATE') >= 0) {
                        predicates.push({ phrase: phrase, startIdx: s });
                    } else if (desc.indexOf('ПРЯМ_ДОП') >= 0 || desc.indexOf('ДОП') >= 0 || desc.indexOf('OBJECT') >= 0) {
                        objects.push({ phrase: phrase, startIdx: s });
                    } else if (desc.indexOf('ОБСТ') >= 0 || desc.indexOf('ADVERBIAL') >= 0) {
                        settings.push({ phrase: phrase, startIdx: s });
                    }
                });
            }

            // Fallback: extract verbs as actions, first noun as character
            if (predicates.length === 0) {
                wordData.forEach(function(wd) {
                    if (isVerb(wd.pos)) predicates.push({ phrase: wd.word, startIdx: wd.idx });
                });
            }
            if (subjects.length === 0 && predicates.length > 0) {
                // Try to find a noun before the first verb
                var firstPredIdx = predicates[0].startIdx;
                for (var i = 0; i < wordData.length; i++) {
                    if (wordData[i].startIdx != null && wordData[i].idx >= firstPredIdx) break;
                    if (isNoun(wordData[i].pos)) {
                        subjects.push({ phrase: wordData[i].word, startIdx: wordData[i].idx });
                        break;
                    }
                }
            }

            if (subjects.length > 0 || predicates.length > 0) {
                idx++;
                scenes.push({
                    index: idx,
                    text: fullText,
                    characters: subjects.map(function(s) { return s.phrase; }),
                    actions: predicates.map(function(p) { return p.phrase; }),
                    targets: objects.map(function(o) { return o.phrase; }),
                    settings: settings.map(function(s) { return s.phrase; })
                });
            }
        });
    });

    return scenes;
}

// ── Rendering ────────────────────────────────────────────────────────

function renderResults() {
    var scenes = extractedScenes;
    if (!scenes.length) {
        document.getElementById('results').innerHTML = '<div class="gd-empty">No narrative elements found. Try different text.</div>';
        return;
    }

    // Stats
    var charMap = {}, actionMap = {};
    scenes.forEach(function(s) {
        s.characters.forEach(function(c) { charMap[c] = (charMap[c] || 0) + 1; });
        s.actions.forEach(function(a) { actionMap[a] = (actionMap[a] || 0) + 1; });
    });
    var chars = Object.keys(charMap).sort(function(a, b) { return charMap[b] - charMap[a]; });
    var acts = Object.keys(actionMap).sort(function(a, b) { return actionMap[b] - actionMap[a]; });

    var html = '';

    // Stats cards
    html += '<div class="gd-stats">';
    html += '<div class="gd-stat-card"><span class="gd-stat-num">' + scenes.length + '</span><span class="gd-stat-label">Scenes</span></div>';
    html += '<div class="gd-stat-card"><span class="gd-stat-num">' + chars.length + '</span><span class="gd-stat-label">Characters</span></div>';
    html += '<div class="gd-stat-card"><span class="gd-stat-num">' + acts.length + '</span><span class="gd-stat-label">Actions</span></div>';
    html += '</div>';

    // Scene table
    html += '<div class="gd-table-wrap"><table class="gd-table">';
    html += '<thead><tr><th>#</th><th>Character</th><th>Action</th><th>Target</th><th>Setting</th><th>Sentence</th></tr></thead><tbody>';
    scenes.forEach(function(s) {
        html += '<tr>';
        html += '<td class="gd-num">' + s.index + '</td>';
        html += '<td class="gd-char">' + (s.characters.join(', ') || '—') + '</td>';
        html += '<td class="gd-act">' + (s.actions.join(', ') || '—') + '</td>';
        html += '<td class="gd-target">' + (s.targets.join(', ') || '—') + '</td>';
        html += '<td class="gd-set">' + (s.settings.join(', ') || '—') + '</td>';
        html += '<td class="gd-text">' + escapeHtml(s.text) + '</td>';
        html += '</tr>';
    });
    html += '</tbody></table></div>';

    // Character register
    if (chars.length) {
        html += '<div class="gd-section"><h3 class="gd-h3">Character Register</h3>';
        html += '<div class="gd-chips">';
        chars.forEach(function(c) {
            html += '<span class="gd-chip gd-chip-char">' + escapeHtml(c) + ' <small>' + charMap[c] + 'x</small></span>';
        });
        html += '</div></div>';
    }

    // Action register
    if (acts.length) {
        html += '<div class="gd-section"><h3 class="gd-h3">Action Register</h3>';
        html += '<div class="gd-chips">';
        acts.forEach(function(a) {
            html += '<span class="gd-chip gd-chip-act">' + escapeHtml(a) + ' <small>' + actionMap[a] + 'x</small></span>';
        });
        html += '</div></div>';
    }

    document.getElementById('results').innerHTML = html;
    document.getElementById('btnExport').style.display = 'inline-block';
}

function escapeHtml(s) {
    return s.replace(/&/g, '&amp;').replace(/</g, '&lt;').replace(/>/g, '&gt;');
}

// ── Export TXT ───────────────────────────────────────────────────────

function exportTxt() {
    if (!extractedScenes.length) return;

    var charMap = {}, actionMap = {};
    extractedScenes.forEach(function(s) {
        s.characters.forEach(function(c) { charMap[c] = (charMap[c] || 0) + 1; });
        s.actions.forEach(function(a) { actionMap[a] = (actionMap[a] || 0) + 1; });
    });
    var chars = Object.keys(charMap).sort(function(a, b) { return charMap[b] - charMap[a]; });
    var acts = Object.keys(actionMap).sort(function(a, b) { return actionMap[b] - actionMap[a]; });

    var lines = [];
    lines.push('NARRATIVE SKELETON');
    lines.push('='.repeat(50));
    lines.push('Extracted: ' + new Date().toLocaleString());
    lines.push('Scenes: ' + extractedScenes.length + '  Characters: ' + chars.length + '  Actions: ' + acts.length);
    lines.push('');

    extractedScenes.forEach(function(s) {
        lines.push('--- SCENE ' + s.index + ' ---');
        if (s.characters.length) lines.push('Character: ' + s.characters.join(', '));
        if (s.actions.length)    lines.push('Action:    ' + s.actions.join(', '));
        if (s.targets.length)    lines.push('Target:    ' + s.targets.join(', '));
        if (s.settings.length)   lines.push('Setting:   ' + s.settings.join(', '));
        lines.push('Sentence:  ' + s.text);
        lines.push('');
    });

    lines.push('');
    lines.push('='.repeat(50));
    lines.push('CHARACTER REGISTER');
    lines.push('-'.repeat(30));
    chars.forEach(function(c, i) {
        lines.push((i + 1) + '. ' + c + ' (' + charMap[c] + ' scenes)');
    });

    lines.push('');
    lines.push('ACTION REGISTER');
    lines.push('-'.repeat(30));
    acts.forEach(function(a, i) {
        lines.push((i + 1) + '. ' + a + ' (' + actionMap[a] + 'x)');
    });

    var blob = new Blob([lines.join('\n')], { type: 'text/plain;charset=utf-8' });
    var url = URL.createObjectURL(blob);
    var a = document.createElement('a');
    a.href = url;
    a.download = 'narrative_skeleton.txt';
    document.body.appendChild(a);
    a.click();
    document.body.removeChild(a);
    URL.revokeObjectURL(url);
}

// ── Main ─────────────────────────────────────────────────────────────

function runExtract() {
    var text = document.getElementById('InputText').value.trim();
    if (!text) return;

    var btn = document.getElementById('btnExtract');
    btn.classList.add('loading');
    document.getElementById('results').innerHTML = '<div class="gd-loading">Analyzing text...</div>';

    fetch(SynanDaemonUrl + '&action=syntax&langua=English', { method: 'POST', body: text })
        .then(function(r) {
            if (!r.ok) throw new Error('Server returned ' + r.status);
            return r.json();
        })
        .then(function(json) {
            extractedScenes = parseScenes(json);
            renderResults();
            btn.classList.remove('loading');
        })
        .catch(function(err) {
            document.getElementById('results').innerHTML =
                '<div class="gd-error">Analysis failed: ' + escapeHtml(err.message) +
                '<br><small>Make sure SynanDaemon is running on port 8089</small></div>';
            btn.classList.remove('loading');
        });
}

window.runExtract = runExtract;
window.exportTxt = exportTxt;

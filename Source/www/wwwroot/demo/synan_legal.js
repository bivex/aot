// ═════════════════════════════════════════════════════════════════════
//  synan_legal.js — Specialized visualization for Legal Documents
// ═════════════════════════════════════════════════════════════════════

var SynanDaemonUrl = 'http://localhost:8089?dummy=1';
var TopClauses = [];
var cursor;
var CURRENT_LANG = 'Ukrainian'; 

// ── Colours ──────────────────────────────────────────────────────────
var GROUP_COLOR  = '#6366f1';
var LINK_COLOR   = '#f43f5e';
var SUBJ_COLOR   = '#059669'; // Deeper emerald
var PREDIC_COLOR = '#d97706'; // Deeper amber
var FONT = 'Arial';

// ── Layout ───────────────────────────────────────────────────────────
var FONT_SIZE     = 19;       // Slightly larger for legal text
var SMALL_FONT    = 11;
var SPACE_SIZE    = 15;
var LEFT_SPACE    = 20;
var WORD_Y        = 50;       
var POS_BELOW_UKR = 28;       
var BRACKET_BASE  = 35;       
var BRACKET_ROW   = 24;       
var TICK          = 10;       

var POS_COLORS = {
    NOUN:'#1e40af', PN:'#1d4ed8', PRON:'#3b82f6',
    VERB:'#b91c1c', VBE:'#be123c', MOD:'#ea580c',
    ADJECTIVE:'#15803d', PN_ADJ:'#16a34a', ORDNUM:'#22c55e',
    ADVERB:'#6d28d9',
    ARTICLE:'#4b5563', PREP:'#0f766e', CONJ:'#92400e',
    PART:'#c026d3', INT:'#e11d48', NUMERAL:'#a16207',
    POSS:'#0d9488',
    UNKNOWN:'#6b7280'
};

function getPosFromGram(g) { 
    if (!g) return 'UNKNOWN';
    var p = (g.split(/[\s;,]/)[0] || 'UNKNOWN').trim().replace(/[\u0000-\u001F\u007F-\u009F\u00A0]/g, "").toUpperCase();
    if (p.length === 1) {
        var c = p.charCodeAt(0);
        if (c === 0x0421 || c === 0x0043 || c === 0x0053) return 'NOUN';
        if (c === 0x041F || c === 0x0050) return 'ADJECTIVE';
        if (c === 0x0413 || c === 0x0047) return 'VERB';
        if (c === 0x041D || c === 0x0048) return 'ADVERB';
    }
    var map = {
        '\u0421': 'NOUN', '\u041F': 'ADJECTIVE', '\u0413': 'VERB', '\u041D': 'ADVERB',
        'N': 'NOUN', 'A': 'ADJECTIVE', 'V': 'VERB', 'ADV': 'ADVERB'
    };
    return map[p] || 'UNKNOWN';
}

function getPosColor(p) { return POS_COLORS[p] || POS_COLORS.UNKNOWN; }

var mainCanvas, ctxMain;
var ROW_HEIGHT = 200;

function initCanvas() {
    mainCanvas = document.getElementById("synanCanvas");
    if (!mainCanvas) return;
    ctxMain = mainCanvas.getContext("2d");
}

class CMorphVariant {
    constructor(synUnits, arcs, subjArcs) {
        this.synUnits = synUnits;
        this.arcs = arcs;
        this.subjArcs = subjArcs;
        this.equals = function(Var2) {
            for (var i = 0; i < Var2.synUnits.length; i++)
                if (this.synUnits[i].homonymNo !== Var2.synUnits[i].homonymNo) return false;
            return true;
        };
    }
}

class CSynUnit {
    constructor(str) {
        if (str !== 'empty') {
            this.homonymNo = str.homNo;
            this.strGram = str.grm;
        }
    }
}

class Homonym {
    constructor(str) { this.lemma = str; this.strCurrentGram = ''; }
}

class WordPanel {
    constructor(word) {
        this.x = 0; this.y = 0; this.width = 0; this.centerX = 0;
        this.activeHomonym = 0;
        this.word = word.str;
        this.homonyms = [];
        for (var i in word.homonyms)
            this.homonyms.push(new Homonym(word.homonyms[i]));
    }
}

function translateDescriptor(d, lang) {
    if (!d || lang !== 'Ukrainian') return d;
    var upper = d.toUpperCase().replace(/[-\s]/g, '_');
    var map = {
        'ОТР_ФОРМА': 'заперечна форма', 'ПРИЛ_СУЩ': 'визначення',
        'ГЕНИТ_ИГ': 'род. група', 'ПРЯМ_ДОП': 'об\'єкт',
        'ИНСТР_ДОП': 'оруд. група', 'ПГ': 'прийм. група',
        'ГЛ_ЛИЧН': 'дія', 'ИМ_СКАЗ': 'стан/визначення',
        'ПОДЛЕЖ': 'суб\'єкт', 'СКАЗ': 'предикат'
    };
    return map[upper] || d;
}

class WordArc {
    constructor(group) {
        this.firstWord = group.start;
        this.lastWord  = group.last;
        this.strName   = translateDescriptor((group.descr || '').replace(/\0/g,'').trim(), CURRENT_LANG);
        this.groupArc  = group.isGroup;
        this.isSubj    = group.isSubj;
        this.depth     = 0;

        this.draw = function(Clause) {
            var lp = Clause.WordPanels[this.firstWord];
            var rp = Clause.WordPanels[this.lastWord];
            if (!lp || !rp) return;
            if (lp._row !== rp._row) return;

            var yBase = lp._row * ROW_HEIGHT;
            var x1 = lp.centerX;
            var x2 = rp.centerX;
            var y  = yBase + WORD_Y + POS_BELOW_UKR + SMALL_FONT + BRACKET_BASE + this.depth * BRACKET_ROW;

            var color = this.groupArc ? GROUP_COLOR : LINK_COLOR;
            ctxMain.strokeStyle = color;
            ctxMain.lineWidth   = this.groupArc ? 2.5 : 1.5;

            if (!this.groupArc) ctxMain.setLineDash([4,3]);

            ctxMain.beginPath();
            ctxMain.moveTo(x1, y);
            ctxMain.lineTo(x2, y);
            ctxMain.stroke();

            ctxMain.beginPath(); ctxMain.moveTo(x1, y); ctxMain.lineTo(x1, y - TICK); ctxMain.stroke();
            ctxMain.beginPath(); ctxMain.moveTo(x2, y); ctxMain.lineTo(x2, y - TICK); ctxMain.stroke();
            ctxMain.setLineDash([]);

            if (this.strName) {
                ctxMain.font = 'bold ' + SMALL_FONT + 'px ' + FONT;
                var tw = ctxMain.measureText(this.strName).width;
                var mid = (x1 + x2) / 2;
                var lx = mid - tw/2;
                var ly = y + SMALL_FONT * 0.35;

                ctxMain.fillStyle = '#fff';
                ctxMain.fillRect(lx-4, ly-SMALL_FONT, tw+8, SMALL_FONT+4);
                ctxMain.strokeStyle = color;
                ctxMain.strokeRect(lx-4, ly-SMALL_FONT, tw+8, SMALL_FONT+4);

                ctxMain.fillStyle = color;
                ctxMain.fillText(this.strName, lx, ly);
            }
        };
    }
}

class TopClause {
    constructor(Info) {
        this.currentMorphVariant = 0;
        this.WordPanels = [];
        this.MorphVariants = [];
        for (var i in Info.words) this.WordPanels.push(new WordPanel(Info.words[i]));
        for (var i in Info.variants) this.parseOneVariant(Info.variants[i]);
        if (this.MorphVariants.length > 0) this.setActiveHomonyms(0);
    }
}

var protoClause = TopClause.prototype;

protoClause.setActiveHomonyms = function(VarNo) {
    var hom = this.MorphVariants[VarNo];
    for (var i = 0; i < hom.synUnits.length; i++) {
        var panel = this.WordPanels[i];
        panel.activeHomonym = hom.synUnits[i].homonymNo;
        panel.homonyms[panel.activeHomonym].strCurrentGram = hom.synUnits[i].strGram;
    }
};

protoClause.parseOneVariant = function(variant) {
    var homs = [];
    for (var i = 0; i < this.WordPanels.length; i++) 
        if (variant.units[i]) homs.push(new CSynUnit(variant.units[i]));
    
    var arcs = [], subjArcs = [];
    for (var i in variant.groups) {
        var arc = new WordArc(variant.groups[i]);
        if (arc.isSubj) subjArcs.push(arc);
        else            arcs.push(arc);
    }
    this.assignDepths(arcs);
    this.MorphVariants.push(new CMorphVariant(homs, arcs, subjArcs));
};

protoClause.assignDepths = function(arcs) {
    if (!arcs || arcs.length === 0) return;
    arcs.sort((a, b) => a.firstWord - b.firstWord || b.lastWord - a.lastWord);
    var levels = [];
    for (var i = 0; i < arcs.length; i++) {
        var a = arcs[i], assigned = false;
        for (var l = 0; l < levels.length; l++) {
            var canFit = true;
            for (var j = 0; j < levels[l].length; j++) {
                var interval = levels[l][j];
                if (!(a.lastWord < interval.start || a.firstWord > interval.end)) {
                    canFit = false; break;
                }
            }
            if (canFit) { a.depth = l; levels[l].push({start: a.firstWord, end: a.lastWord}); assigned = true; break; }
        }
        if (!assigned) { a.depth = levels.length; levels.push([{start: a.firstWord, end: a.lastWord}]); }
    }
};

protoClause.drawWordPanels = function() {
    for (var i in this.WordPanels) {
        var panel = this.WordPanels[i];
        var pos = getPosFromGram(panel.homonyms[panel.activeHomonym].strCurrentGram);
        var col = getPosColor(pos);

        var isCore = (pos === 'NOUN' || pos === 'VERB' || pos === 'VBE');
        var yBase = panel._row * ROW_HEIGHT;

        ctxMain.font = (isCore ? 'bold ' : '') + FONT_SIZE + 'px ' + FONT;
        ctxMain.fillStyle = col;
        ctxMain.fillText(panel.word, panel.x, yBase + WORD_Y);

        var label = pos === 'NOUN' ? 'іменник' : pos === 'VERB' ? 'дія' : pos === 'VBE' ? 'зв\'язка' : '';
        if (label) {
            ctxMain.font = 'bold 9px ' + FONT;
            ctxMain.fillStyle = col + 'aa';
            ctxMain.fillText(label, panel.x + (panel.width - ctxMain.measureText(label).width)/2, yBase + WORD_Y + 14);
        }
    }
};

protoClause.drawSubjPredic = function() {
    var v = this.MorphVariants[this.currentMorphVariant];
    if (!v) return;
    for (var i = 0; i < v.subjArcs.length; i++) {
        var arc = v.subjArcs[i];
        var p1 = this.WordPanels[arc.firstWord];
        var p2 = this.WordPanels[arc.lastWord];
        if (!p1 || !p2) continue;
        if (p1._row !== p2._row) continue;

        var yBase = p1._row * ROW_HEIGHT;
        var yPos = yBase + WORD_Y + POS_BELOW_UKR + 15;
        ctxMain.strokeStyle = SUBJ_COLOR;
        ctxMain.lineWidth = 4;
        ctxMain.lineCap = 'round';
        ctxMain.beginPath();
        ctxMain.moveTo(p1.centerX, yPos);
        ctxMain.bezierCurveTo(p1.centerX, yPos + 60, p2.centerX, yPos + 60, p2.centerX, yPos);
        ctxMain.stroke();

        ctxMain.fillStyle = SUBJ_COLOR;
        ctxMain.beginPath();
        ctxMain.arc(p2.centerX, yPos, 4, 0, Math.PI*2);
        ctxMain.fill();

        ctxMain.font = 'bold 11px ' + FONT;
        var sTxt = "СУБ'ЄКТ (Party)", pTxt = "ПРЕДИКАТ (Action)";
        var sw = ctxMain.measureText(sTxt).width, pw = ctxMain.measureText(pTxt).width;

        ctxMain.fillStyle = 'rgba(5, 150, 105, 0.1)';
        ctxMain.fillRect(p1.centerX - sw/2 - 5, yPos + 25, sw + 10, 18);
        ctxMain.fillStyle = SUBJ_COLOR;
        ctxMain.fillText(sTxt, p1.centerX - sw/2, yPos + 38);

        ctxMain.fillStyle = 'rgba(217, 119, 6, 0.1)';
        ctxMain.fillRect(p2.centerX - pw/2 - 5, yPos + 25, pw + 10, 18);
        ctxMain.fillStyle = PREDIC_COLOR;
        ctxMain.fillText(pTxt, p2.centerX - pw/2, yPos + 38);
    }
};

protoClause.drawArcs = function() {
    var v = this.MorphVariants[this.currentMorphVariant];
    if (v) v.arcs.forEach(a => a.draw(this));
};

function parseSynanJson(json) {
    TopClauses = [];
    json.forEach(s => s.forEach(c => TopClauses.push(new TopClause(c))));
}

function drawAll() {
    var wrapper = document.getElementById('canvasWrapper');
    if (!wrapper) return;
    var viewW = wrapper.clientWidth - 40;
    if (viewW < 100) viewW = 100;
    ctxMain.canvas.width = viewW;

    // Pass 1: layout — assign x, _row to every panel
    var x = LEFT_SPACE;
    var curRow = 0;
    for (var ci = 0; ci < TopClauses.length; ci++) {
        var clause = TopClauses[ci];
        for (var wi = 0; wi < clause.WordPanels.length; wi++) {
            var panel = clause.WordPanels[wi];
            var pos = getPosFromGram(panel.homonyms[panel.activeHomonym].strCurrentGram);
            var isCore = (pos === 'NOUN' || pos === 'VERB' || pos === 'VBE');
            ctxMain.font = (isCore ? 'bold ' : '') + FONT_SIZE + 'px ' + FONT;
            panel.width = ctxMain.measureText(panel.word).width;

            if (x + panel.width > viewW && x > LEFT_SPACE) {
                curRow++;
                x = LEFT_SPACE;
            }
            panel.x = x;
            panel.centerX = x + panel.width / 2;
            panel._row = curRow;
            x += panel.width + SPACE_SIZE;
        }
    }

    ctxMain.canvas.height = (curRow + 1) * ROW_HEIGHT;
    ctxMain.clearRect(0, 0, viewW, ctxMain.canvas.height);

    // Pass 2: draw
    TopClauses.forEach(c => {
        c.drawWordPanels();
        c.drawArcs();
        c.drawSubjPredic();
    });
}

function syntax_request() {
    var query = document.getElementById("InputText").value.trim();
    if (!query) return;
    fetch(SynanDaemonUrl + "&action=syntax&langua=Ukrainian", { method: 'POST', body: query })
        .then(r => r.json()).then(json => { parseSynanJson(json); drawAll(); });
}

window.syntax_request = syntax_request;
initCanvas();

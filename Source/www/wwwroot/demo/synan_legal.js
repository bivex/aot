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

var mainCanvas, longCanvas, ctx, ctxMain;

function initCanvas() {
    mainCanvas = document.getElementById("synanCanvas");
    if (!mainCanvas) return;
    longCanvas = document.createElement('canvas');
    ctx = longCanvas.getContext("2d");
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

            var x1 = lp.centerX;
            var x2 = rp.centerX;
            var y  = WORD_Y + POS_BELOW_UKR + SMALL_FONT + BRACKET_BASE + this.depth * BRACKET_ROW;

            var color = this.groupArc ? GROUP_COLOR : LINK_COLOR;
            ctx.strokeStyle = color;
            ctx.lineWidth   = this.groupArc ? 2.5 : 1.5;

            if (!this.groupArc) ctx.setLineDash([4,3]);

            ctx.beginPath();
            ctx.moveTo(x1, y);
            ctx.lineTo(x2, y);
            ctx.stroke();

            ctx.beginPath(); ctx.moveTo(x1, y); ctx.lineTo(x1, y - TICK); ctx.stroke();
            ctx.beginPath(); ctx.moveTo(x2, y); ctx.lineTo(x2, y - TICK); ctx.stroke();
            ctx.setLineDash([]);

            if (this.strName) {
                ctx.font = 'bold ' + SMALL_FONT + 'px ' + FONT;
                var tw = ctx.measureText(this.strName).width;
                var mid = (x1 + x2) / 2;
                var lx = mid - tw/2;
                var ly = y + SMALL_FONT * 0.35;

                ctx.fillStyle = '#fff';
                ctx.fillRect(lx-4, ly-SMALL_FONT, tw+8, SMALL_FONT+4);
                ctx.strokeStyle = color;
                ctx.strokeRect(lx-4, ly-SMALL_FONT, tw+8, SMALL_FONT+4);

                ctx.fillStyle = color;
                ctx.fillText(this.strName, lx, ly);
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

        // Bold for nouns/verbs in legal view
        var isCore = (pos === 'NOUN' || pos === 'VERB' || pos === 'VBE');
        ctx.font = (isCore ? 'bold ' : '') + FONT_SIZE + 'px ' + FONT;
        panel.width = ctx.measureText(panel.word).width;

        var prevLineNo = Math.floor(cursor / ctxMain.canvas.width);
        var lineNo     = Math.floor((panel.width + cursor) / ctxMain.canvas.width);
        if (lineNo > prevLineNo) cursor = ctxMain.canvas.width * lineNo + LEFT_SPACE;

        panel.x = cursor;
        panel.y = WORD_Y;
        panel.centerX = cursor + panel.width / 2;

        ctx.fillStyle = col;
        ctx.fillText(panel.word, panel.x, panel.y);

        var label = pos === 'NOUN' ? 'іменник' : pos === 'VERB' ? 'дія' : pos === 'VBE' ? 'зв\'язка' : '';
        if (label) {
            ctx.font = 'bold 9px ' + FONT;
            ctx.fillStyle = col + 'aa';
            ctx.fillText(label, panel.x + (panel.width - ctx.measureText(label).width)/2, panel.y + 14);
        }

        cursor += panel.width + SPACE_SIZE;
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

        var yPos = WORD_Y + POS_BELOW_UKR + 15;
        ctx.strokeStyle = SUBJ_COLOR;
        ctx.lineWidth = 4;
        ctx.lineCap = 'round';
        ctx.beginPath();
        ctx.moveTo(p1.centerX, yPos);
        ctx.bezierCurveTo(p1.centerX, yPos + 60, p2.centerX, yPos + 60, p2.centerX, yPos);
        ctx.stroke();

        ctx.fillStyle = SUBJ_COLOR;
        ctx.beginPath();
        ctx.arc(p2.centerX, yPos, 4, 0, Math.PI*2);
        ctx.fill();

        ctx.font = 'bold 11px ' + FONT;
        var sTxt = "СУБ'ЄКТ (Party)", pTxt = "ПРЕДИКАТ (Action)";
        var sw = ctx.measureText(sTxt).width, pw = ctx.measureText(pTxt).width;

        ctx.fillStyle = 'rgba(5, 150, 105, 0.1)';
        ctx.fillRect(p1.centerX - sw/2 - 5, yPos + 25, sw + 10, 18);
        ctx.fillStyle = SUBJ_COLOR;
        ctx.fillText(sTxt, p1.centerX - sw/2, yPos + 38);

        ctx.fillStyle = 'rgba(217, 119, 6, 0.1)';
        ctx.fillRect(p2.centerX - pw/2 - 5, yPos + 25, pw + 10, 18);
        ctx.fillStyle = PREDIC_COLOR;
        ctx.fillText(pTxt, p2.centerX - pw/2, yPos + 38);
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

function calcWordsLength() {
    var length = LEFT_SPACE;
    for (var i in TopClauses) {
        var Clause = TopClauses[i];
        for (var j in Clause.WordPanels) {
            var panel = Clause.WordPanels[j];
            var pos = getPosFromGram(panel.homonyms[panel.activeHomonym].strCurrentGram);
            var isCore = (pos === 'NOUN' || pos === 'VERB' || pos === 'VBE');
            ctx.font = (isCore ? 'bold ' : '') + FONT_SIZE + 'px ' + FONT;
            var prevLineNo = Math.floor(length / ctxMain.canvas.width);
            var lineNo     = Math.floor((ctx.measureText(panel.word).width + length) / ctxMain.canvas.width);
            if (lineNo > prevLineNo)
                length = ctxMain.canvas.width * lineNo + LEFT_SPACE;
            length += ctx.measureText(panel.word).width + SPACE_SIZE;
        }
    }
    return length;
}

function drawAll() {
    var wrapper = document.getElementById('canvasWrapper');
    if (!wrapper) return;
    ctxMain.canvas.width = wrapper.clientWidth - 40;
    
    var canvasH = 450, canvasW = calcWordsLength(); 
    ctx.canvas.height = canvasH; ctx.canvas.width  = canvasW;
    ctx.clearRect(0, 0, canvasW, canvasH);
    cursor = LEFT_SPACE;

    TopClauses.forEach(c => {
        c.drawWordPanels();
        c.drawArcs();
        c.drawSubjPredic();
    });

    var linesNo = Math.ceil(canvasW / ctxMain.canvas.width);
    ctxMain.canvas.height = linesNo * 220;
    ctxMain.clearRect(0, 0, ctxMain.canvas.width, ctxMain.canvas.height);
    for (var i = 0; i < linesNo; i++) {
        ctxMain.drawImage(ctx.canvas, ctxMain.canvas.width*i, 0, ctxMain.canvas.width, 220, 0, 220*i, ctxMain.canvas.width, 220);
    }
}

function syntax_request() {
    var query = document.getElementById("InputText").value.trim();
    if (!query) return;
    fetch(SynanDaemonUrl + "&action=syntax&langua=Ukrainian", { method: 'POST', body: query })
        .then(r => r.json()).then(json => { parseSynanJson(json); drawAll(); });
}

window.syntax_request = syntax_request;
initCanvas();

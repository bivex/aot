import { SynanDaemonUrl } from './common.js';

var TopClauses = [];
var cursor;

// ── Colours ──────────────────────────────────────────────────────────
var GROUP_COLOR  = '#6366f1';
var LINK_COLOR   = '#f43f5e';
var SUBJ_COLOR   = '#10b981';
var PREDIC_COLOR = '#f59e0b';
var FONT = 'Arial';

// ── Layout ───────────────────────────────────────────────────────────
var FONT_SIZE     = 18;
var SMALL_FONT    = 10;
var SPACE_SIZE    = 14;
var LEFT_SPACE    = 16;
var WORD_Y        = 36;       // baseline for words
var POS_BELOW     = 16;       // POS text offset below word baseline
var BRACKET_BASE  = 20;       // first bracket row below POS text
var BRACKET_ROW   = 26;       // vertical spacing per bracket level
var TICK          = 8;        // bracket end-tick height

var POS_COLORS = {
    NOUN:'#2563eb', PN:'#3b82f6', PRON:'#60a5fa',
    VERB:'#dc2626', VBE:'#e11d48', MOD:'#f97316',
    ADJECTIVE:'#16a34a', PN_ADJ:'#22c55e', ORDNUM:'#4ade80',
    ADVERB:'#7c3aed',
    ARTICLE:'#6b7280', PREP:'#0d9488', CONJ:'#a16207',
    PART:'#d946ef', INT:'#f43f5e', NUMERAL:'#ca8a04',
    POSS:'#14b8a6',
    UNKNOWN:'#9ca3af'
};

function getPosFromGram(g) { return g ? (g.split(/[\s;,]/)[0] || 'UNKNOWN') : 'UNKNOWN'; }
function getPosColor(p)    { return POS_COLORS[p] || POS_COLORS.UNKNOWN; }

function roundRect(c, x, y, w, h, r) {
    c.beginPath();
    c.moveTo(x+r,y); c.lineTo(x+w-r,y);
    c.quadraticCurveTo(x+w,y,x+w,y+r); c.lineTo(x+w,y+h-r);
    c.quadraticCurveTo(x+w,y+h,x+w-r,y+h); c.lineTo(x+r,y+h);
    c.quadraticCurveTo(x,y+h,x,y+h-r); c.lineTo(x,y+r);
    c.quadraticCurveTo(x,y,x+r,y); c.closePath();
}

// ── Canvas ───────────────────────────────────────────────────────────
var mainCanvas, longCanvas, ctx, ctxMain;

function initCanvas() {
    mainCanvas = document.getElementById("synanCanvas");
    longCanvas = document.createElement('canvas');
    ctx = longCanvas.getContext("2d");
    ctxMain = mainCanvas.getContext("2d");
}
initCanvas();

// ═════════════════════════════════════════════════════════════════════
//  Data classes
// ═════════════════════════════════════════════════════════════════════

class CMorphVariant {
    constructor(synUnits, arcs, subjArcs) {
        this.synUnits = synUnits;
        this.arcs = arcs;
        this.subjArcs = subjArcs;
        this.compareTo = function(var2){
            for (var i = 0; i < var2.synUnits.length; i++) {
                if (this.synUnits[i].homonymNo < var2.synUnits[i].homonymNo) return -1;
                if (this.synUnits[i].homonymNo > var2.synUnits[i].homonymNo) return 1;
            }
            return 0;
        };
        this.equals = function(Var) { return this.compareTo(Var) == 0; };
    }
}

class CSynUnit {
    constructor(str) {
        if (str != 'emtpy') {
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
        this.outerX = 0; this.outerY = 0;
        this.activeHomonym = 0;
        this.word = word.str;
        this.homonyms = [];
        for (var i in word.homonyms)
            this.homonyms.push(new Homonym(word.homonyms[i]));
    }
}

// ── WordArc (bracket-style) ──────────────────────────────────────────

class WordArc {
    constructor(group) {
        this.childArcs = [];
        this.firstWord = group.start;
        this.lastWord  = group.last;
        this.strName   = (group.descr || '').replace(/\0/g,'').trim();
        this.groupArc  = group.isGroup;
        this.isSubj    = group.isSubj;
        this.depth     = 0;

        this.calcDepths = function(d) {
            this.depth = d;
            for (var i in this.childArcs)
                this.childArcs[i].calcDepths(d + 1);
        };

        this.getMaxDepth = function() {
            var m = this.depth;
            for (var i in this.childArcs) {
                var c = this.childArcs[i].getMaxDepth();
                if (c > m) m = c;
            }
            return m;
        };

        this.getHeight = function() {
            var h = 0;
            for (var i in this.childArcs) {
                var ch = this.childArcs[i].getHeight();
                if (ch > h) h = ch;
            }
            return h + BRACKET_ROW;
        };

        this.draw = function(Clause) {
            // draw children first (closer to words)
            for (var i in this.childArcs)
                this.childArcs[i].draw(Clause);

            var lp = Clause.WordPanels[this.firstWord];
            var rp = Clause.WordPanels[this.lastWord];
            if (!lp || !rp) return;

            var x1 = lp.centerX;
            var x2 = rp.centerX;
            var y  = WORD_Y + POS_BELOW + SMALL_FONT + BRACKET_BASE + this.depth * BRACKET_ROW;

            var color = this.groupArc ? GROUP_COLOR : LINK_COLOR;
            ctx.strokeStyle = color;
            ctx.lineWidth   = this.groupArc ? 2 : 1.5;

            if (!this.groupArc) ctx.setLineDash([4,3]);

            // horizontal span
            ctx.beginPath();
            ctx.moveTo(x1, y);
            ctx.lineTo(x2, y);
            ctx.stroke();

            // left tick
            ctx.beginPath();
            ctx.moveTo(x1, y);
            ctx.lineTo(x1, y - TICK);
            ctx.stroke();

            // right tick
            ctx.beginPath();
            ctx.moveTo(x2, y);
            ctx.lineTo(x2, y - TICK);
            ctx.stroke();

            ctx.setLineDash([]);

            // dots at tick tops
            ctx.fillStyle = color;
            [x1, x2].forEach(function(px) {
                ctx.beginPath();
                ctx.arc(px, y - TICK, 2.5, 0, Math.PI*2);
                ctx.fill();
            });

            // label pill
            if (this.strName) {
                ctx.font = 'bold ' + SMALL_FONT + 'px ' + FONT;
                var tw = ctx.measureText(this.strName).width;
                var mid = (x1 + x2) / 2;
                var lx = mid - tw/2;
                var ly = y + SMALL_FONT * 0.35;
                var px = 6, py = 2;

                ctx.fillStyle = this.groupArc
                    ? 'rgba(99,102,241,0.10)'
                    : 'rgba(244,63,94,0.10)';
                roundRect(ctx, lx-px, ly-SMALL_FONT-py, tw+px*2, SMALL_FONT+py*2, 4);
                ctx.fill();
                ctx.strokeStyle = color + '44';
                ctx.lineWidth = 1;
                ctx.stroke();

                ctx.fillStyle = color;
                ctx.font = 'bold ' + SMALL_FONT + 'px ' + FONT;
                ctx.fillText(this.strName, lx, ly);
            }

            ctx.lineWidth = 1;
        };
    }
}

// ═════════════════════════════════════════════════════════════════════
//  TopClause
// ═════════════════════════════════════════════════════════════════════

class TopClause {
    constructor(Info) {
        this.currentMorphVariant = 0;
        this.WordPanels = [];
        this.MorphVariants = [];
        this.parseWords(Info.words);
        this.parseVariants(Info.variants);

        this.getCurArcs = function() {
            var CurrVar = this.getActiveHomonymNumbers();
            for (var i = 0; i < this.MorphVariants.length; i++) {
                if (this.MorphVariants[i].equals(CurrVar)) {
                    this.currentMorphVariant = i;
                    this.setActiveHomonyms(i);
                    return this.MorphVariants[i].arcs;
                }
            }
            this.currentMorphVariant = -1;
            return [];
        };

        this.getActiveHomonymNumbers = function() {
            var arr = [];
            for (var i = 0; i < this.WordPanels.length; i++) {
                var U = new CSynUnit('empty');
                U.homonymNo = this.WordPanels[i].activeHomonym;
                arr.push(U);
            }
            return new CMorphVariant(arr, [], []);
        };
    }
}

var protoClause = TopClause.prototype;

protoClause.parseWords = function(words) {
    for (var i in words)
        this.WordPanels.push(new WordPanel(words[i]));
};

protoClause.parseVariants = function(variants) {
    for (var i in variants)
        this.parseOneVariant(variants[i]);
    if (this.MorphVariants.length > 0)
        this.setActiveHomonyms(0);
};

protoClause.setActiveHomonyms = function(VarNo) {
    var hom = this.MorphVariants[VarNo];
    for (var i = 0; i < hom.synUnits.length; i++) {
        var panel = this.WordPanels[i];
        panel.activeHomonym = hom.synUnits[i].homonymNo;
        panel.homonyms[panel.activeHomonym].strCurrentGram = hom.synUnits[i].strGram;
    }
};

protoClause.parseOneVariant = function(variant) {
    var homs = this.readUnits(variant.units),
        arcs = [],
        subjArcs = [];
    for (var i in variant.groups) {
        var arc = new WordArc(variant.groups[i]);
        if (arc.isSubj) subjArcs.push(arc);
        else            arcs.push(arc);
    }
    arcs = this.orderArcs(arcs);
    // assign depths
    for (var i in arcs) arcs[i].calcDepths(0);
    for (var i in subjArcs) subjArcs[i].calcDepths(0);
    this.MorphVariants.push(new CMorphVariant(homs, arcs, subjArcs));
};

protoClause.readUnits = function(str) {
    var wordsCount = this.WordPanels.length, ii = 0, arr = [];
    while ((ii < wordsCount) && (str[ii])) {
        arr.push(new CSynUnit(str[ii]));
        ii++;
    }
    return arr;
};

protoClause.orderArcsRec = function(arcs, parentArc, iCur) {
    for (var i = iCur; i < arcs.length;) {
        var arc = arcs[i];
        if (+arc.firstWord > +parentArc.lastWord) return i;
        i = this.orderArcsRec(arcs, arc, i + 1);
        parentArc.childArcs.push(arc);
    }
    return arcs.length;
};

protoClause.orderArcs = function(arcs) {
    var ordered = [];
    for (var i = 0; i < arcs.length;) {
        var arc = arcs[i];
        i = this.orderArcsRec(arcs, arc, i + 1);
        ordered.push(arc);
    }
    return ordered;
};

// ── Drawing ──────────────────────────────────────────────────────────

protoClause.drawWordPanels = function() {
    for (var i in this.WordPanels) {
        var panel = this.WordPanels[i];
        var pos = getPosFromGram(panel.homonyms[panel.activeHomonym].strCurrentGram);
        var col = getPosColor(pos);

        ctx.font = (panel.homonyms.length > 1 ? 'bold ' : '') + FONT_SIZE + 'px ' + FONT;
        panel.width = ctx.measureText(panel.word).width;

        var prevLineNo = Math.floor(cursor / ctxMain.canvas.width);
        var lineNo     = Math.floor((panel.width + cursor) / ctxMain.canvas.width);
        if (lineNo > prevLineNo) cursor = ctxMain.canvas.width * lineNo + LEFT_SPACE;

        panel.x = cursor;
        panel.y = WORD_Y;
        panel.centerX = cursor + panel.width / 2;
        panel.outerX = cursor - ctxMain.canvas.width * lineNo;
        panel.outerY = WORD_Y + ctx.canvas.height * lineNo;

        // word
        ctx.fillStyle = col;
        ctx.fillText(panel.word, panel.x, panel.y);



        // restore font
        ctx.font = (panel.homonyms.length > 1 ? 'bold ' : '') + FONT_SIZE + 'px ' + FONT;

        cursor += panel.width + SPACE_SIZE;
    }
};

protoClause.drawSubjPredic = function() {
    if (this.currentMorphVariant < 0) return;
    var homs = this.MorphVariants[this.currentMorphVariant];
    for (var i = 0; i < homs.subjArcs.length; i++) {
        var arc = homs.subjArcs[i];
        var p1 = this.WordPanels[arc.firstWord];
        var p2 = this.WordPanels[arc.lastWord];
        if (!p1 || !p2) continue;

        // subject badge
        var sy = p1.y - FONT_SIZE * 0.3;
        ctx.font = 'bold 9px ' + FONT;
        ctx.fillStyle = SUBJ_COLOR;
        ctx.beginPath();
        ctx.arc(p1.centerX, sy, 6, 0, Math.PI*2);
        ctx.fill();
        ctx.fillStyle = '#fff';
        ctx.fillText('S', p1.centerX - 3, sy + 3);

        // predicate badge
        var py2 = p2.y - FONT_SIZE * 0.3;
        ctx.fillStyle = PREDIC_COLOR;
        ctx.beginPath();
        ctx.arc(p2.centerX, py2, 6, 0, Math.PI*2);
        ctx.fill();
        ctx.fillStyle = '#fff';
        ctx.font = 'bold 9px ' + FONT;
        ctx.fillText('P', p2.centerX - 3, py2 + 3);

        // arrow from subject to predicate
        var arrowY = WORD_Y + POS_BELOW + SMALL_FONT + 4;
        var ax1 = p1.centerX + 8;
        var ax2 = p2.centerX - 8;

        ctx.strokeStyle = SUBJ_COLOR + '88';
        ctx.lineWidth = 1.5;
        ctx.setLineDash([3,3]);
        ctx.beginPath();
        ctx.moveTo(ax1, arrowY);
        ctx.lineTo(ax2, arrowY);
        ctx.stroke();
        ctx.setLineDash([]);

        // arrowhead
        ctx.fillStyle = SUBJ_COLOR + '88';
        ctx.beginPath();
        ctx.moveTo(ax2, arrowY);
        ctx.lineTo(ax2 - 5, arrowY - 3);
        ctx.lineTo(ax2 - 5, arrowY + 3);
        ctx.closePath();
        ctx.fill();

        ctx.lineWidth = 1;
    }
};

protoClause.drawArcs = function() {
    var arcs = this.getCurArcs();
    for (var i in arcs)
        arcs[i].draw(this);
};

protoClause.addPopups = function() {
    for (var i in this.WordPanels) {
        var panel = this.WordPanels[i];
        var popDiv = document.createElement("div");
        popDiv.style.position = 'absolute';
        popDiv.style.top  = panel.outerY - FONT_SIZE;
        popDiv.style.left = panel.outerX;
        popDiv.style.height = FONT_SIZE*1.2 + 'px';
        popDiv.style.width  = panel.width + 'px';
        popDiv.title = panel.word + ' → ' +
            panel.homonyms[panel.activeHomonym].lemma + ' ' +
            panel.homonyms[panel.activeHomonym].strCurrentGram;
        popDiv.className = 'synanWordPanel';
        if (panel.homonyms.length > 1) {
            var menuDiv = document.createElement("div");
            menuDiv.className = 'synanDropdownContent';
            for (var j in panel.homonyms) {
                var menuEl = document.createElement("a");
                menuEl.innerHTML = panel.homonyms[j].lemma;
                menuEl.setAttribute('ActionCommand', j);
                menuEl.setAttribute('wordPanelNo', i);
                var Clause = this;
                menuEl.addEventListener("click", function(){
                    var homNum = this.getAttribute('ActionCommand');
                    var panelNo = this.getAttribute('wordPanelNo');
                    Clause.WordPanels[panelNo].activeHomonym = homNum;
                    drawAll();
                });
                menuDiv.appendChild(menuEl);
            }
            popDiv.appendChild(menuDiv);
            popDiv.style.cursor = 'pointer';
            popDiv.addEventListener("click", function(){
                this.getElementsByClassName('synanDropdownContent')[0].style.display = 'block';
            });
            popDiv.className += ' panelDroppable';
        }
        document.getElementById('canvasWrapper').appendChild(popDiv);
    }
};

// ═════════════════════════════════════════════════════════════════════
//  Layout helpers
// ═════════════════════════════════════════════════════════════════════

function parseSynanJson(synanJson) {
    TopClauses = [];
    for (var s in synanJson)
        for (var c in synanJson[s])
            TopClauses.push(new TopClause(synanJson[s][c]));
}

function calcMaxDepth() {
    var max = 0;
    for (var i in TopClauses) {
        var arcs = TopClauses[i].getCurArcs();
        for (var j in arcs) {
            var d = arcs[j].getMaxDepth();
            if (d > max) max = d;
        }
    }
    return max;
}

function calcWordsLength() {
    var length = LEFT_SPACE;
    for (var i in TopClauses) {
        var Clause = TopClauses[i];
        for (var j in Clause.WordPanels) {
            ctx.font = (Clause.WordPanels[j].homonyms.length > 1 ? 'bold ' : '') + FONT_SIZE + 'px ' + FONT;
            var prevLineNo = Math.floor(length / ctxMain.canvas.width);
            var lineNo     = Math.floor((ctx.measureText(Clause.WordPanels[j].word).width + length) / ctxMain.canvas.width);
            if (lineNo > prevLineNo)
                length = ctxMain.canvas.width * lineNo + LEFT_SPACE;
            length += ctx.measureText(Clause.WordPanels[j].word).width + SPACE_SIZE;
        }
    }
    return length;
}

function wrapAll() {
    var linesNo = Math.ceil(ctx.canvas.width / ctxMain.canvas.width);
    ctxMain.canvas.height = linesNo * ctx.canvas.height;
    ctxMain.clearRect(0, 0, ctxMain.canvas.width, ctxMain.canvas.height);
    for (var i = 0; i < linesNo; i++) {
        ctxMain.drawImage(ctx.canvas,
            ctxMain.canvas.width*i, 0, ctxMain.canvas.width, ctx.canvas.height,
            0, ctx.canvas.height * i, ctxMain.canvas.width, ctx.canvas.height);
    }
}

function removePopups() {
    var wrapper = document.getElementById('canvasWrapper');
    var popDiv = wrapper.getElementsByClassName("synanWordPanel");
    while (popDiv.length > 0) {
        for (var i = 0; i < popDiv.length; i++)
            popDiv[i].parentNode.removeChild(popDiv[i]);
        popDiv = wrapper.getElementsByClassName("synanWordPanel");
    }
}

function addPopups() {
    for (var i in TopClauses)
        TopClauses[i].addPopups();
    window.onclick = function(event) {
        if (!event.target.matches('.panelDroppable')) {
            var dropdowns = document.getElementsByClassName("synanDropdownContent");
            for (var i = 0; i < dropdowns.length; i++)
                dropdowns[i].style.display = 'none';
        }
    };
}

// ═════════════════════════════════════════════════════════════════════
//  Main draw
// ═════════════════════════════════════════════════════════════════════

function drawAll() {
    removePopups();

    var wrapper = document.getElementById('canvasWrapper');
    if (wrapper) {
        var style = getComputedStyle(wrapper);
        var paddingX = (parseFloat(style.paddingLeft)||0) + (parseFloat(style.paddingRight)||0);
        var w = wrapper.clientWidth - paddingX;
        if (w > 0) ctxMain.canvas.width = w;
    }

    var maxDepth = calcMaxDepth();
    var canvasH = WORD_Y + POS_BELOW + SMALL_FONT + BRACKET_BASE + (maxDepth + 1) * BRACKET_ROW + 16;
    var canvasW = calcWordsLength();

    ctx.canvas.height = canvasH;
    ctx.canvas.width  = canvasW;
    ctx.clearRect(0, 0, canvasW, canvasH);
    cursor = LEFT_SPACE;

    for (var i in TopClauses) {
        TopClauses[i].drawWordPanels();
        TopClauses[i].drawArcs();
        TopClauses[i].drawSubjPredic();
    }

    wrapAll();
    addPopups();
    drawLegend();
}

// ═════════════════════════════════════════════════════════════════════
//  Legend
// ═════════════════════════════════════════════════════════════════════

function drawLegend() {
    var langua = document.getElementById("Language").value;
    var x = 12, y = ctxMain.canvas.height - 8;
    var lineLen = 20, gap = 18, lineH = 16;

    ctxMain.font = '11px ' + FONT;
    ctxMain.lineWidth = 1;

    var labels;
    if (langua === 'English')
        labels = { group:'— group', link:'- - link', subj:'S subject', predic:'P predicate' };
    else if (langua === 'German')
        labels = { group:'— Gruppe', link:'- - Verbindung', subj:'S Subjekt', predic:'P Prädikat' };
    else if (langua === 'Ukrainian')
        labels = { group:'— група', link:'- - зв\'язок', subj:'S підмет', predic:'P присудок' };
    else
        labels = { group:'— группа', link:'- - связь', subj:'S подлежащее', predic:'P сказуемое' };

    // ── POS colour row ──
    var posOrder = ['NOUN','PN','PRON','VERB','VBE','MOD','ADJECTIVE','ADVERB','ARTICLE','PREP','CONJ','PART'];
    var posRowY = y;
    var posRowX = x;
    for (var pi = 0; pi < posOrder.length; pi++) {
        var pp = posOrder[pi];
        var pc = getPosColor(pp);
        ctxMain.font = 'bold 10px ' + FONT;
        var tw = ctxMain.measureText(pp).width + 8;
        if (posRowX + tw > ctxMain.canvas.width - 10) break;
        ctxMain.fillStyle = pc;
        ctxMain.beginPath();
        ctxMain.arc(posRowX + 4, posRowY - 4, 4, 0, Math.PI*2);
        ctxMain.fill();
        ctxMain.fillText(pp, posRowX + 12, posRowY);
        posRowX += tw + 10;
    }

    y -= lineH + 4;

    // group
    y -= lineH;
    ctxMain.strokeStyle = GROUP_COLOR; ctxMain.setLineDash([]);
    ctxMain.beginPath(); ctxMain.moveTo(x,y+6); ctxMain.lineTo(x+lineLen,y+6); ctxMain.stroke();
    ctxMain.fillStyle = GROUP_COLOR; ctxMain.font = '11px '+FONT;
    ctxMain.fillText(labels.group, x+lineLen+4, y+10);

    // link
    y -= lineH;
    ctxMain.strokeStyle = LINK_COLOR; ctxMain.setLineDash([4,3]);
    ctxMain.beginPath(); ctxMain.moveTo(x,y+6); ctxMain.lineTo(x+lineLen,y+6); ctxMain.stroke();
    ctxMain.fillStyle = LINK_COLOR;
    ctxMain.fillText(labels.link, x+lineLen+4, y+10);

    // subject
    y -= lineH;
    ctxMain.strokeStyle = SUBJ_COLOR; ctxMain.setLineDash([]); ctxMain.lineWidth = 2.5;
    ctxMain.beginPath(); ctxMain.moveTo(x,y+6); ctxMain.lineTo(x+lineLen,y+6); ctxMain.stroke();
    ctxMain.fillStyle = SUBJ_COLOR; ctxMain.font = '11px '+FONT;
    ctxMain.fillText(labels.subj, x+lineLen+4, y+10);

    // predicate
    y -= lineH;
    ctxMain.strokeStyle = PREDIC_COLOR;
    ctxMain.beginPath(); ctxMain.moveTo(x,y+4); ctxMain.lineTo(x+lineLen,y+4); ctxMain.stroke();
    ctxMain.beginPath(); ctxMain.moveTo(x,y+8); ctxMain.lineTo(x+lineLen,y+8); ctxMain.stroke();
    ctxMain.fillStyle = PREDIC_COLOR;
    ctxMain.fillText(labels.predic, x+lineLen+4, y+10);

    ctxMain.setLineDash([]); ctxMain.lineWidth = 1;
}

// ═════════════════════════════════════════════════════════════════════
//  Request
// ═════════════════════════════════════════════════════════════════════

function syntax_request() {
    var langua = document.getElementById("Language").value;
    var query  = document.getElementById("InputText").value.trim();
    if (!query || query.length === 0) { alert('Please enter text to analyze'); return; }

    var url = SynanDaemonUrl + "&action=syntax&langua=" + encodeURIComponent(langua);
    fetch(url, { method: 'POST', body: query })
        .then(function(r) {
            if (!r.ok) throw new Error('Server returned ' + r.status);
            return r.json();
        })
        .then(function(json) { parseSynanJson(json); drawAll(); })
        .catch(function(e) { console.error('Syntax request failed:', e); alert('Error: ' + e.message); });
}

window.syntax_request = syntax_request;
window.reinitCanvas = function() { initCanvas(); TopClauses = []; };

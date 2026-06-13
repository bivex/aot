// ═════════════════════════════════════════════════════════════════════
//  synan_hun_legal.js — D3.js SVG visualization for Hungarian Legal Documents
// ═════════════════════════════════════════════════════════════════════

var SynanDaemonUrl = 'http://localhost:8089?dummy=1';
var TopClauses = [];
var CURRENT_LANG = 'Hungarian';

// ── Colours (Legal palette: navy / burgundy / antique gold) ────────────
var GROUP_COLOR  = '#2C3E5A';    // navy — NP/VP/PP groups
var LINK_COLOR   = '#6B2737';    // burgundy — non-group links (verb_t etc.)
var SUBJ_COLOR   = '#2E7D32';    // green — subject
var PREDIC_COLOR = '#8B1A1A';    // dark red — predicate
var SP_ARC_COLOR = '#5C6BC0';    // indigo — S-P arc
var FONT = '-apple-system, BlinkMacSystemFont, system-ui, sans-serif';

var SENTENCE_COLORS = [
    'rgba(27, 42, 74, 0.06)',
    'rgba(107, 39, 55, 0.06)',
    'rgba(139, 105, 20, 0.06)',
    'rgba(74, 100, 128, 0.06)',
    'rgba(139, 26, 26, 0.06)',
];

// ── Layout ───────────────────────────────────────────────────────────
var FONT_SIZE    = 18;
var SMALL_FONT   = 10;
var WORD_PAD     = 8;
var SPACE_SIZE   = 12;
var LEFT_SPACE   = 20;
var WORD_Y       = 45;
var POS_BELOW    = 16;
var BRACKET_BASE = 12;
var BRACKET_ROW  = 18;
var TICK         = 6;
var SP_ARC_EXTRA = 14;

var POS_COLORS = {
    NOUN:'#1B2A4A', ADJ:'#7B5800', VERB:'#6B2737',
    ADV:'#4A5568', DET:'#718096', PRON:'#4A6480',
    PREP:'#276749', CONJ:'#744210', INT:'#8B1A1A',
    NUM:'#5F370E', PART:'#6B4226', ADP:'#5B6B4A', PROPN:'#4A3A6A', UNKNOWN:'#9E9E9E'
};

function getPosFromGram(g) {
    if (!g) return 'UNKNOWN';
    var p = (g.split(/[\s;,]/)[0] || 'UNKNOWN').trim().replace(/[ - ]/g, '').toUpperCase();
    var map = {
        'NOUN':'NOUN','ADJ':'ADJ','VERB':'VERB','ADV':'ADV',
        'DET':'DET','PRON':'PRON','PREP':'PREP','CONJ':'CONJ',
        'INT':'INT','NUM':'NUM','PART':'PART','ADP':'ADP','PROPN':'PROPN',
        'PUNC':'UNKNOWN','PUNCT':'UNKNOWN','SENT':'UNKNOWN'
    };
    return map[p] || 'UNKNOWN';
}
function getPosColor(p) { return POS_COLORS[p] || POS_COLORS.UNKNOWN; }
function getPosLabel(pos) {
    var labels = { NOUN:'főnév', ADJ:'mn.', VERB:'ige', ADV:'hat.',
        DET:'det.', PRON:'nm.', PREP:'elöl.', CONJ:'köt.',
        INT:'interj.', NUM:'szám', PART:'part.' };
    return labels[pos] || '';
}
function translateDescriptor(d) {
    if (!d) return d;
    var upper = d.toUpperCase().replace(/[-\s]/g,'_');
    var map = {
        'NP':'név.csoport','VP':'ige.csoport','PP':'elöl.csoport',
        'SP':'alany-állítmány','VERB_T':'ige-t',
        'ROOT':'gyökér','ADJ_NP':'mód.'
    };
    return map[upper] || d.toLowerCase();
}

// ── Data Classes ─────────────────────────────────────────────────────
class CMorphVariant {
    constructor(synUnits, arcs, subjArcs) {
        this.synUnits = synUnits;
        this.arcs = arcs;
        this.subjArcs = subjArcs;
    }
}
class CSynUnit {
    constructor(str) {
        this.homonymNo = str.homNo;
        this.strGram   = str.grm;
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
        this.homonyms = word.homonyms.map(h => new Homonym(h));
    }
}
class WordArc {
    constructor(group) {
        this.firstWord = group.start;
        this.lastWord  = group.last;
        this.span      = group.last - group.start;
        this.strName   = translateDescriptor((group.descr || '').replace(/\0/g,'').trim());
        this.groupArc  = group.isGroup;
        this.isSubj    = group.isSubj;
        this.depth     = 0;
    }
}

class TopClause {
    constructor(Info) {
        this.currentMorphVariant = 0;
        this.WordPanels = [];
        this.MorphVariants = [];
        for (var i in Info.words)    this.WordPanels.push(new WordPanel(Info.words[i]));
        for (var i in Info.variants) this.parseOneVariant(Info.variants[i]);
        if (this.MorphVariants.length > 0) this.setActiveHomonyms(0);
    }

    setActiveHomonyms(VarNo) {
        var hom = this.MorphVariants[VarNo];
        for (var i = 0; i < hom.synUnits.length && i < this.WordPanels.length; i++) {
            var panel = this.WordPanels[i];
            panel.activeHomonym = hom.synUnits[i].homonymNo;
            if (panel.homonyms[panel.activeHomonym])
                panel.homonyms[panel.activeHomonym].strCurrentGram = hom.synUnits[i].strGram;
        }
    }

    parseOneVariant(variant) {
        var homs = [];
        for (var i = 0; i < this.WordPanels.length; i++)
            if (variant.units[i]) homs.push(new CSynUnit(variant.units[i]));
        var arcs = [], subjArcs = [];
        for (var i in variant.groups) {
            var arc = new WordArc(variant.groups[i]);
            if (arc.isSubj) subjArcs.push(arc);
            else            arcs.push(arc);
        }
        arcs = this._dedup(arcs);
        this.assignDepths(arcs);
        this.MorphVariants.push(new CMorphVariant(homs, arcs, subjArcs));
    }

    _dedup(arcs) {
        var seen = new Map();
        var out = [];
        for (var a of arcs) {
            var key = a.firstWord + ':' + a.lastWord + ':' + a.strName;
            if (!seen.has(key)) { seen.set(key, true); out.push(a); }
        }
        return out;
    }

    assignDepths(arcs) {
        if (!arcs || arcs.length === 0) return;
        arcs.sort((a, b) => (a.span - b.span) || a.firstWord - b.firstWord);
        for (var i = 0; i < arcs.length; i++) {
            var a = arcs[i];
            var maxChildDepth = -1;
            for (var j = 0; j < i; j++) {
                var c = arcs[j];
                if (c.firstWord >= a.firstWord && c.lastWord <= a.lastWord) {
                    if (c.depth > maxChildDepth) maxChildDepth = c.depth;
                }
            }
            a.depth = maxChildDepth + 1;
        }
    }
}

function parseSynanJson(json) {
    TopClauses = [];
    json.forEach(s => s.forEach(c => TopClauses.push(new TopClause(c))));
}

// ── D3 SVG Setup ─────────────────────────────────────────────────────
var svg, zoomGroup, zoomBehavior;
var _measureSvg, _measureText;

function initCanvas() {
    var container = document.getElementById('svgContainer');
    if (!container) return;
    d3.select(container).selectAll('svg').remove();
    if (_measureSvg) _measureSvg.remove();

    _measureSvg = d3.select(document.body)
        .append('svg').attr('class','measure-svg')
        .style('position','absolute').style('visibility','hidden').style('pointer-events','none');
    _measureText = _measureSvg.append('text');

    svg = d3.select(container).append('svg')
        .attr('width','100%').attr('height','100%').style('min-height','400px');

    zoomBehavior = d3.zoom().scaleExtent([0.25, 4])
        .on('zoom', function(event) { zoomGroup.attr('transform', event.transform); });

    svg.call(zoomBehavior);
    zoomGroup = svg.append('g').attr('class','zoom-root');
}

function measureText(str, size, weight) {
    _measureText.attr('font-family', FONT).attr('font-size', size+'px')
        .attr('font-weight', weight || 'normal').text(str);
    return _measureText.node().getComputedTextLength();
}

// ── Rendering ────────────────────────────────────────────────────────
function drawAll() {
    if (!zoomGroup) return;

    var allWords = [], allArcs = [], allSubjArcs = [];
    TopClauses.forEach(function(clause, ci) {
        clause.WordPanels.forEach(function(panel, wi) {
            var activeHom = panel.homonyms[panel.activeHomonym] || panel.homonyms[0] || {strCurrentGram:''};
            var pos = getPosFromGram(activeHom.strCurrentGram);
            allWords.push({ ci, wi, panel, pos, color: getPosColor(pos),
                isCore: pos === 'NOUN' || pos === 'VERB', _realW: 0 });
        });
        var v = clause.MorphVariants[clause.currentMorphVariant];
        if (v) {
            v.arcs.forEach(a => allArcs.push({ arc: a, clause }));
            v.subjArcs.forEach(a => allSubjArcs.push({ arc: a, clause }));
        }
    });

    zoomGroup.selectAll('*').remove();

    // Pass 1: measure word widths
    var probeG = zoomGroup.append('g');
    probeG.selectAll('text').data(allWords).enter().append('text')
        .attr('font-size', FONT_SIZE+'px').attr('font-family', FONT)
        .attr('font-weight', d => d.isCore ? 'bold' : 'normal')
        .text(d => d.panel.word);
    probeG.selectAll('text').nodes().forEach((n, i) => { allWords[i]._realW = n.getComputedTextLength(); });
    probeG.remove();

    // Layout words into rows
    var container = document.getElementById('svgContainer');
    if (!container) return;
    var viewW = Math.max(container.clientWidth - 30, 800);
    var x = LEFT_SPACE, curRow = 0;
    allWords.forEach(function(w) {
        var slotW = w._realW + WORD_PAD * 2;
        if (x + slotW > viewW && x > LEFT_SPACE) { curRow++; x = LEFT_SPACE; }
        w.panel.x = x + WORD_PAD;
        w.panel.width = w._realW;
        w.panel.centerX = x + slotW / 2;
        w.panel._row = curRow;
        x += slotW + SPACE_SIZE;
    });
    var totalRows = curRow + 1;

    // Compute max bracket depth per row
    var rowMaxDepth = {};
    allArcs.forEach(function(d) {
        var lp = d.clause.WordPanels[d.arc.firstWord];
        var rp = d.clause.WordPanels[d.arc.lastWord];
        if (!lp || !rp || lp._row !== rp._row) return;
        var row = lp._row;
        if (rowMaxDepth[row] === undefined || d.arc.depth > rowMaxDepth[row])
            rowMaxDepth[row] = d.arc.depth;
    });

    var rowHasSubj = {};
    allSubjArcs.forEach(function(d) {
        var lp = d.clause.WordPanels[d.arc.firstWord];
        var rp = d.clause.WordPanels[d.arc.lastWord];
        if (!lp || !rp || lp._row !== rp._row) return;
        rowHasSubj[lp._row] = true;
    });

    // Compute row tops
    var rowTop = [];
    var acc = 0;
    for (var r = 0; r < totalRows; r++) {
        rowTop.push(acc);
        var maxDepth = rowMaxDepth[r] !== undefined ? rowMaxDepth[r] : 0;
        var rowH = WORD_Y + POS_BELOW + BRACKET_BASE + (maxDepth + 1) * BRACKET_ROW + 30;
        if (rowHasSubj[r]) rowH += SP_ARC_EXTRA + 60;
        acc += rowH;
    }
    var svgH = Math.max(acc + 20, 400);
    svg.style('height', svgH + 'px');
    svg.call(zoomBehavior.transform, d3.zoomIdentity);

    allWords.forEach(function(w) {
        w.panel._rowTop = rowTop[w.panel._row];
        w.y = rowTop[w.panel._row] + WORD_Y;
    });

    // -- Sentence background highlights --
    var sentG = zoomGroup.append('g').attr('class','sentence-bg');
    var rowGroups = {};
    allWords.forEach(function(w) {
        var key = w.ci + '_' + w.panel._row;
        if (!rowGroups[key]) rowGroups[key] = [];
        rowGroups[key].push(w);
    });
    Object.keys(rowGroups).forEach(function(key) {
        var ws = rowGroups[key];
        var minX = d3.min(ws, w => w.panel.x - WORD_PAD);
        var maxX = d3.max(ws, w => w.panel.x + w._realW + WORD_PAD);
        var row  = ws[0].panel._row;
        var yTop = rowTop[row] + 4;
        var yBot = rowTop[row] + WORD_Y + POS_BELOW + 10;
        sentG.append('rect')
            .attr('x', minX - 4).attr('y', yTop)
            .attr('width', maxX - minX + 8).attr('height', yBot - yTop)
            .attr('fill', SENTENCE_COLORS[ws[0].ci % SENTENCE_COLORS.length])
            .attr('rx', 8).attr('ry', 8);
    });

    // -- Words --
    var wordG = zoomGroup.append('g').attr('class','words');
    var wordItems = wordG.selectAll('.w').data(allWords).enter().append('g').attr('class','w');

    wordItems.append('text').attr('class','word-text')
        .attr('x', d => d.panel.x).attr('y', d => d.y)
        .attr('fill', d => d.color)
        .attr('font-weight', d => d.isCore ? 'bold' : 'normal')
        .attr('font-size', FONT_SIZE+'px').attr('font-family', FONT)
        .text(d => d.panel.word);

    wordItems.append('text').attr('class','pos-label')
        .attr('x', d => d.panel.centerX).attr('y', d => d.y + POS_BELOW)
        .attr('text-anchor','middle')
        .attr('fill', d => d.color + 'bb')
        .attr('font-size', SMALL_FONT+'px').attr('font-family', FONT).attr('font-weight','bold')
        .text(d => getPosLabel(d.pos));

    wordItems.append('title')
        .text(d => {
            var h = d.panel.homonyms[d.panel.activeHomonym] || d.panel.homonyms[0] || {};
            return d.panel.word + ' → ' + (h.lemma||'') +
                (h.strCurrentGram ? ' [' + h.strCurrentGram.split(';')[0] + ']' : '');
        });

    // -- Bracket groups --
    function bracketY(row, depth) {
        return rowTop[row] + WORD_Y + POS_BELOW + BRACKET_BASE + depth * BRACKET_ROW;
    }

    var bracketG = zoomGroup.append('g').attr('class','brackets');
    allArcs.forEach(function(d) {
        var arc = d.arc, clause = d.clause;
        var lp = clause.WordPanels[arc.firstWord], rp = clause.WordPanels[arc.lastWord];
        if (!lp || !rp || lp._row !== rp._row) return;
        var row = lp._row;
        var x1 = lp.centerX, x2 = rp.centerX;
        var y  = bracketY(row, arc.depth);
        var color = arc.groupArc ? GROUP_COLOR : LINK_COLOR;
        var sw = arc.groupArc ? 2 : 1.5;
        var dash = arc.groupArc ? null : '5,3';
        var g = bracketG.append('g');

        g.append('line').attr('x1', x1).attr('y1', y).attr('x2', x2).attr('y2', y)
            .attr('stroke', color).attr('stroke-width', sw)
            .attr('stroke-dasharray', dash);
        g.append('line').attr('x1', x1).attr('y1', y).attr('x2', x1).attr('y2', y - TICK)
            .attr('stroke', color).attr('stroke-width', sw);
        g.append('line').attr('x1', x2).attr('y1', y).attr('x2', x2).attr('y2', y - TICK)
            .attr('stroke', color).attr('stroke-width', sw);

        [x1, x2].forEach(px => {
            g.append('circle').attr('cx', px).attr('cy', y - TICK).attr('r', 2).attr('fill', color);
        });

        if (arc.strName && x2 > x1) {
            var mid = (x1 + x2) / 2;
            var tw  = measureText(arc.strName, SMALL_FONT, 'bold');
            var lx  = mid - tw / 2;
            var ly  = y + SMALL_FONT * 1.1;
            g.append('rect')
                .attr('x', lx - 4).attr('y', ly - SMALL_FONT - 1)
                .attr('width', tw + 8).attr('height', SMALL_FONT + 3)
                .attr('fill', arc.groupArc ? 'rgba(44,62,90,0.09)' : 'rgba(107,39,55,0.09)')
                .attr('stroke', color + '55').attr('stroke-width', 0.8)
                .attr('rx', 3).attr('ry', 3);
            g.append('text').attr('x', lx).attr('y', ly)
                .attr('fill', color)
                .attr('font-size', SMALL_FONT+'px').attr('font-family', FONT).attr('font-weight','bold')
                .text(arc.strName);
        }
    });

    // -- Subject-Predicate Arcs --
    var subjG = zoomGroup.append('g').attr('class','subj-arcs');
    allSubjArcs.forEach(function(d) {
        var arc = d.arc, clause = d.clause;
        var p1 = clause.WordPanels[arc.firstWord], p2 = clause.WordPanels[arc.lastWord];
        if (!p1 || !p2 || p1._row !== p2._row) return;
        var row = p1._row;

        var maxDepth = rowMaxDepth[row] !== undefined ? rowMaxDepth[row] : 0;
        var yBase = bracketY(row, maxDepth) + BRACKET_ROW + SP_ARC_EXTRA;

        var cx1 = p1.centerX, cx2 = p2.centerX;
        var arcH = Math.min(Math.abs(cx2 - cx1) * 0.35 + 20, 55);
        var g = subjG.append('g');

        g.append('path')
            .attr('d', `M${cx1},${yBase} C${cx1},${yBase+arcH} ${cx2},${yBase+arcH} ${cx2},${yBase}`)
            .attr('fill','none').attr('stroke', SP_ARC_COLOR)
            .attr('stroke-width', 2.5).attr('stroke-linecap','round');

        g.append('circle').attr('cx', cx2).attr('cy', yBase).attr('r', 3.5)
            .attr('fill', PREDIC_COLOR);
        g.append('circle').attr('cx', cx1).attr('cy', yBase).attr('r', 3.5)
            .attr('fill', SUBJ_COLOR);

        var sTxt = 'ALANY', pTxt = 'ÁLLÍTMÁNY';
        var sw2 = measureText(sTxt, SMALL_FONT, 'bold');
        var pw  = measureText(pTxt, SMALL_FONT, 'bold');
        var labelY = yBase + arcH * 0.6 + SMALL_FONT + 2;

        g.append('rect').attr('x', cx1 - sw2/2 - 3).attr('y', labelY - SMALL_FONT)
            .attr('width', sw2 + 6).attr('height', SMALL_FONT + 3)
            .attr('fill', 'rgba(46,125,50,0.12)').attr('rx', 2);
        g.append('text').attr('x', cx1 - sw2/2).attr('y', labelY)
            .attr('fill', SUBJ_COLOR).attr('font-size', SMALL_FONT+'px')
            .attr('font-family', FONT).attr('font-weight','bold').text(sTxt);

        g.append('rect').attr('x', cx2 - pw/2 - 3).attr('y', labelY - SMALL_FONT)
            .attr('width', pw + 6).attr('height', SMALL_FONT + 3)
            .attr('fill', 'rgba(139,26,26,0.12)').attr('rx', 2);
        g.append('text').attr('x', cx2 - pw/2).attr('y', labelY)
            .attr('fill', PREDIC_COLOR).attr('font-size', SMALL_FONT+'px')
            .attr('font-family', FONT).attr('font-weight','bold').text(pTxt);
    });

    // -- Legend --
    svg.selectAll('.legend').remove();
    var legend = svg.append('g').attr('class','legend').attr('transform','translate(14,12)');
    [
        { c: GROUP_COLOR,  d: null,  l: '— szintaktikai csoport', w: 2 },
        { c: LINK_COLOR,   d: '5,3', l: '- - kapcsolat',           w: 1.5 },
        { c: SP_ARC_COLOR, d: null,  l: '⌢ alany-állítmány', w: 2.5 },
    ].forEach(function(item, i) {
        var lg = legend.append('g').attr('transform','translate(0,'+(i*16)+')');
        lg.append('line').attr('x1',0).attr('y1',5).attr('x2',22).attr('y2',5)
            .attr('stroke', item.c).attr('stroke-width', item.w)
            .attr('stroke-dasharray', item.d || null);
        lg.append('text').attr('x',28).attr('y',9).attr('fill', item.c)
            .attr('font-size', SMALL_FONT+'px').attr('font-family', FONT).text(item.l);
    });
}

// ── API ──────────────────────────────────────────────────────────────
function syntax_request() {
    var query = document.getElementById('InputText').value.trim();
    if (!query) return;
    fetch(SynanDaemonUrl + '&action=syntax&langua=Hungarian', { method:'POST', body:query })
        .then(r => r.json())
        .then(json => { parseSynanJson(json); drawAll(); })
        .catch(err => { console.error('Syntax request failed:', err); });
}

window.syntax_request = syntax_request;
window.reinitCanvas   = function() { initCanvas(); TopClauses = []; };

var _resizeTimer;
window.addEventListener('resize', function() {
    clearTimeout(_resizeTimer);
    _resizeTimer = setTimeout(function() { if (TopClauses.length > 0) drawAll(); }, 250);
});

initCanvas();

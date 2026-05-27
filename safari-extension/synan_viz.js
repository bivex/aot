// ═══════════════════════════════════════════════════════════════
//  synan_viz.js — Multi-language D3 SVG syntax visualization
// ═══════════════════════════════════════════════════════════════

var TopClauses = [];
var CURRENT_LANG = 'English';

var LANG_CONFIG = {
  English: {
    langua: 'English',
    posMap: {
      'N':'NOUN','A':'ADJECTIVE','V':'VERB','ADV':'ADVERB',
      'PRON':'PRON','PREP':'PREP','CONJ':'CONJ',
      'PART':'PART','INT':'INT','NUM':'NUMERAL',
      'MOD':'MOD','ARTICLE':'ARTICLE','PN':'PN',
      'ADJ_SHORT':'ADJECTIVE','PARTICIPLE':'ADJECTIVE',
      'INFINITIVE':'VERB','VBE':'VBE',
      'PUNC':'UNKNOWN','PUNCT':'UNKNOWN','SENT':'UNKNOWN'
    },
    posLabels: {
      NOUN:'noun', VERB:'verb', VBE:'aux', ADJECTIVE:'adj.',
      ADVERB:'adv.', PRON:'pron.', NUMERAL:'num.', PREP:'prep.',
      CONJ:'conj.', PART:'part.', ARTICLE:'art.', MOD:'modal'
    },
    descriptors: {
      'NP':'noun phrase','VP':'verb phrase','PP':'prep phrase',
      'SP':'subject-predicate','VERB_T':'finite verb',
      'ROOT':'root','SYN_GROUP':'group','ADJ_NP':'modifier',
      'INF':'infinitive','PARTICIPLE_P':'participle phrase'
    },
    subjLabel: 'SUBJECT', predLabel: 'PREDICATE'
  },
  Russian: {
    langua: 'Russian',
    posMap: {
      'С':'NOUN','Г':'VERB','П':'PREP','А':'ADJECTIVE',
      'М':'MOD','Н':'PRON','Ч':'NUMERAL','НАР':'ADVERB',
      'К':'CONJ','ЧА':'PART','И':'INT',
      'N':'NOUN','A':'ADJECTIVE','V':'VERB','ADV':'ADVERB',
      'PRON':'PRON','PREP':'PREP','CONJ':'CONJ',
      'PART':'PART','INT':'INT','NUM':'NUMERAL',
      'MOD':'MOD','PN':'PN',
      'ADJ_SHORT':'ADJECTIVE','PARTICIPLE':'ADJECTIVE',
      'INFINITIVE':'VERB','VBE':'VBE',
      'PUNC':'UNKNOWN','PUNCT':'UNKNOWN','SENT':'UNKNOWN'
    },
    posLabels: {
      NOUN:'сущ.', VERB:'глаг.', VBE:'всп.', ADJECTIVE:'прил.',
      ADVERB:'нар.', PRON:'мест.', NUMERAL:'числ.', PREP:'предл.',
      CONJ:'союз', PART:'част.', MOD:'мод.'
    },
    descriptors: {
      'ИГ':'игра','ГП':'глаг. группа','ПП':'предл. группа',
      'NP':'именная группа','VP':'глаг. группа','PP':'предл. группа',
      'SP':'подлежащее-сказуемое','ROOT':'root','SYN_GROUP':'группа'
    },
    subjLabel: 'ПОДЛЕЖАЩЕЕ', predLabel: 'СКАЗУЕМОЕ'
  },
  Ukrainian: {
    langua: 'Ukrainian',
    posMap: {
      'С':'NOUN','Г':'VERB','П':'PREP','А':'ADJECTIVE',
      'М':'MOD','Н':'PRON','Ч':'NUMERAL','НАР':'ADVERB',
      'К':'CONJ','ЧА':'PART','И':'INT',
      'N':'NOUN','A':'ADJECTIVE','V':'VERB','ADV':'ADVERB',
      'PRON':'PRON','PREP':'PREP','CONJ':'CONJ',
      'PART':'PART','INT':'INT','NUM':'NUMERAL',
      'MOD':'MOD','PN':'PN',
      'ADJ_SHORT':'ADJECTIVE','PARTICIPLE':'ADJECTIVE',
      'INFINITIVE':'VERB','VBE':'VBE',
      'PUNC':'UNKNOWN','PUNCT':'UNKNOWN','SENT':'UNKNOWN'
    },
    posLabels: {
      NOUN:'ім.', VERB:'дієсл.', VBE:'доп.', ADJECTIVE:'прикм.',
      ADVERB:'присл.', PRON:'займ.', NUMERAL:'числ.', PREP:'прийм.',
      CONJ:'сполуч.', PART:'частка', MOD:'мод.'
    },
    descriptors: {
      'ІГ':'імен. группа','ГГ':'дієсл. группа','ПГ':'прийм. группа',
      'NP':'імен. группа','VP':'дієсл. группа','PP':'прийм. группа',
      'SP':'підмет-присудок','ROOT':'root','SYN_GROUP':'група'
    },
    subjLabel: 'ПІДМЕТ', predLabel: 'ПРИСУДОК'
  }
};

function cfg() { return LANG_CONFIG[CURRENT_LANG] || LANG_CONFIG.English; }

// ── Colors ──────────────────────────────────────────────────
var GROUP_COLOR  = '#2C3E5A';
var LINK_COLOR   = '#6B2737';
var SUBJ_COLOR   = '#8B6914';
var PREDIC_COLOR = '#8B1A1A';
var FONT = '-apple-system, BlinkMacSystemFont, system-ui, sans-serif';

var SENTENCE_COLORS = [
  'rgba(27,42,74,0.07)','rgba(107,39,55,0.07)','rgba(139,105,20,0.07)',
  'rgba(74,100,128,0.07)','rgba(139,26,26,0.07)','rgba(107,90,58,0.07)',
  'rgba(44,62,90,0.07)','rgba(125,48,66,0.07)','rgba(160,125,32,0.07)',
  'rgba(90,107,92,0.07)'
];

var POS_COLORS = {
  NOUN:'#1B2A4A', PN:'#2C3E5A', PRON:'#4A6480',
  VERB:'#6B2737', VBE:'#7D3042', MOD:'#954050',
  ADJECTIVE:'#8B6914', PN_ADJ:'#A07D20', ORDNUM:'#B8942C',
  ADVERB:'#5C5C5C',
  ARTICLE:'#787878', PREP:'#4A6B5C', CONJ:'#6B5A3A',
  PART:'#7A4A6B', INT:'#8B1A1A', NUMERAL:'#6B5A14',
  POSS:'#4A7A6A', UNKNOWN:'#8A8A8A'
};

// ── Layout constants ────────────────────────────────────────
var FONT_SIZE=19, SMALL_FONT=11, WORD_PAD=6, SPACE_SIZE=14;
var LEFT_SPACE=20, WORD_Y=50, POS_BELOW=28;
var BRACKET_BASE=35, BRACKET_ROW=22, TICK=8, ROW_HEIGHT=200;

// ── POS helpers ─────────────────────────────────────────────

function getPosFromGram(g) {
  if (!g) return 'UNKNOWN';
  var cleaned = g.split(/[\s;,]/)[0] || 'UNKNOWN';
  cleaned = cleaned.replace(/[\x00-\x1f\x7f-\x9f\xa0]/g, '').toUpperCase();
  var map = cfg().posMap;
  return map[cleaned] || 'UNKNOWN';
}

function getPosColor(p) { return POS_COLORS[p] || POS_COLORS.UNKNOWN; }

function getPosLabel(pos) { return (cfg().posLabels)[pos] || ''; }

function translateDescriptor(d) {
  if (!d) return d;
  var upper = d.toUpperCase().replace(/[-\s]/g, '_');
  return (cfg().descriptors)[upper] || d;
}

// ── Data Classes ────────────────────────────────────────────

class CMorphVariant {
  constructor(synUnits, arcs, subjArcs) {
    this.synUnits = synUnits;
    this.arcs = arcs;
    this.subjArcs = subjArcs;
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

class WordArc {
  constructor(group) {
    this.firstWord = group.start;
    this.lastWord  = group.last;
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
    for (var i in Info.words) this.WordPanels.push(new WordPanel(Info.words[i]));
    for (var i in Info.variants) this.parseOneVariant(Info.variants[i]);
    if (this.MorphVariants.length > 0) this.setActiveHomonyms(0);
  }

  setActiveHomonyms(VarNo) {
    var hom = this.MorphVariants[VarNo];
    for (var i = 0; i < hom.synUnits.length; i++) {
      var panel = this.WordPanels[i];
      panel.activeHomonym = hom.synUnits[i].homonymNo;
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
    this.assignDepths(arcs);
    this.MorphVariants.push(new CMorphVariant(homs, arcs, subjArcs));
  }

  assignDepths(arcs) {
    if (!arcs || arcs.length === 0) return;
    arcs.sort((a, b) => a.firstWord - b.firstWord || b.lastWord - a.lastWord);
    var levels = [];
    for (var i = 0; i < arcs.length; i++) {
      var a = arcs[i], assigned = false;
      for (var l = 0; l < levels.length; l++) {
        var canFit = true;
        for (var j = 0; j < levels[l].length; j++) {
          var iv = levels[l][j];
          if (!(a.lastWord < iv.start || a.firstWord > iv.end)) { canFit = false; break; }
        }
        if (canFit) { a.depth = l; levels[l].push({start:a.firstWord, end:a.lastWord}); assigned = true; break; }
      }
      if (!assigned) { a.depth = levels.length; levels.push([{start:a.firstWord, end:a.lastWord}]); }
    }
  }
}

function parseSynanJson(json) {
  TopClauses = [];
  json.forEach(s => s.forEach(c => TopClauses.push(new TopClause(c))));
}

// ── D3 SVG Setup ────────────────────────────────────────────

var svg, zoomGroup, zoomBehavior;
var _measureSvg, _measureText;

function initCanvas() {
  var container = document.getElementById('svgContainer');
  if (!container) return;
  d3.select(container).selectAll('svg').remove();

  _measureSvg = d3.select(document.body)
    .append('svg').attr('class','measure-svg')
    .style('position','absolute').style('visibility','hidden').style('pointer-events','none');
  _measureText = _measureSvg.append('text');

  svg = d3.select(container)
    .append('svg')
    .attr('width','100%')
    .attr('height','100%')
    .style('min-height','400px');

  zoomBehavior = d3.zoom()
    .scaleExtent([0.3, 3])
    .on('zoom', function(event) { zoomGroup.attr('transform', event.transform); });

  svg.call(zoomBehavior);
  zoomGroup = svg.append('g').attr('class','zoom-root');
}

function measureText(str, size, weight) {
  _measureText
    .attr('font-family', FONT)
    .attr('font-size', size + 'px')
    .attr('font-weight', weight || 'normal')
    .text(str);
  return _measureText.node().getComputedTextLength();
}

// ── Rendering ───────────────────────────────────────────────

function drawAll() {
  if (!zoomGroup) return;

  var allWords = [], allArcs = [], allSubjArcs = [];
  TopClauses.forEach(function(clause, ci) {
    clause.WordPanels.forEach(function(panel, wi) {
      var pos = getPosFromGram(panel.homonyms[panel.activeHomonym].strCurrentGram);
      allWords.push({ ci:ci, wi:wi, panel:panel, pos:pos, color:getPosColor(pos),
        isCore: pos==='NOUN'||pos==='VERB'||pos==='VBE' });
    });
    var v = clause.MorphVariants[clause.currentMorphVariant];
    if (v) {
      v.arcs.forEach(function(a) { allArcs.push({arc:a, clause:clause}); });
      v.subjArcs.forEach(function(a) { allSubjArcs.push({arc:a, clause:clause}); });
    }
  });

  zoomGroup.selectAll('*').remove();

  // Pass 1: measure widths
  var probeG = zoomGroup.append('g');
  probeG.selectAll('text')
    .data(allWords).enter()
    .append('text')
    .attr('font-size', FONT_SIZE+'px').attr('font-family', FONT)
    .attr('font-weight', d => d.isCore?'bold':'normal')
    .text(d => d.panel.word);

  var nodes = probeG.selectAll('text').nodes();
  allWords.forEach(function(w,i) { w._realW = nodes[i].getComputedTextLength(); });
  probeG.remove();

  // Layout
  var container = document.getElementById('svgContainer');
  if (!container) return;
  var viewW = Math.max(container.clientWidth - 20, 900);
  var x = LEFT_SPACE, curRow = 0;
  for (var i = 0; i < allWords.length; i++) {
    var w = allWords[i], panel = w.panel;
    var slotW = w._realW + WORD_PAD * 2;
    if (x + slotW > viewW && x > LEFT_SPACE) { curRow++; x = LEFT_SPACE; }
    panel.x = x + WORD_PAD;
    panel.width = w._realW;
    panel.centerX = x + slotW / 2;
    panel._row = curRow;
    w.y = curRow * ROW_HEIGHT + WORD_Y;
    x += slotW + SPACE_SIZE;
  }

  var svgH = Math.max((curRow+1) * ROW_HEIGHT + 60, 400);
  d3.select(svg.node()).style('height', svgH+'px');
  svg.call(zoomBehavior.transform, d3.zoomIdentity);

  // Sentence backgrounds
  var sentIdx = 0;
  var ciToSentIdx = {};
  allWords.forEach(function(w) {
    if (ciToSentIdx[w.ci] === undefined) {
      ciToSentIdx[w.ci] = sentIdx;
      var clauseWords = allWords.filter(function(ww) { return ww.ci === w.ci; });
      var lastWord = clauseWords[clauseWords.length - 1];
      if (lastWord && lastWord.panel.word === '.') sentIdx++;
    }
  });

  var sentG = zoomGroup.append('g').attr('class','sentence-bg');
  var sentGroups = {};
  allWords.forEach(function(w) {
    var key = ciToSentIdx[w.ci]+'_'+w.panel._row;
    if (!sentGroups[key]) sentGroups[key] = [];
    sentGroups[key].push(w);
  });

  Object.keys(sentGroups).forEach(function(key) {
    var ws = sentGroups[key];
    var si = ciToSentIdx[ws[0].ci];
    var minX = d3.min(ws, function(w){return w.panel.x-WORD_PAD;});
    var maxX = d3.max(ws, function(w){return w.panel.x+w._realW+WORD_PAD;});
    var row = ws[0].panel._row;
    var yTop = row*ROW_HEIGHT+4;
    var yBot = row*ROW_HEIGHT+WORD_Y+POS_BELOW+14;

    sentG.append('rect')
      .attr('x',minX-6).attr('y',yTop).attr('width',maxX-minX+12).attr('height',yBot-yTop)
      .attr('fill',SENTENCE_COLORS[si%SENTENCE_COLORS.length]).attr('rx',10).attr('ry',10);
  });

  // Pass 2: render words
  var wordG = zoomGroup.append('g').attr('class','words');
  var wordItems = wordG.selectAll('.w').data(allWords).enter().append('g').attr('class','w');

  wordItems.append('text')
    .attr('class','word-text')
    .attr('x',d=>d.panel.x).attr('y',d=>d.y)
    .attr('fill',d=>d.color)
    .attr('font-weight',d=>d.isCore?'bold':'normal')
    .attr('font-size',FONT_SIZE+'px').attr('font-family',FONT)
    .text(d=>d.panel.word);

  wordItems.append('text')
    .attr('class','pos-label')
    .attr('x',d=>d.panel.centerX).attr('y',d=>d.y+POS_BELOW)
    .attr('text-anchor','middle')
    .attr('fill',d=>d.color+'aa')
    .attr('font-size',SMALL_FONT+'px').attr('font-family',FONT).attr('font-weight','bold')
    .text(d=>getPosLabel(d.pos));

  wordItems.append('title')
    .text(d=>d.panel.word+' → '+d.panel.homonyms[d.panel.activeHomonym].lemma+
      (d.panel.homonyms[d.panel.activeHomonym].strCurrentGram ?
        ' ['+d.panel.homonyms[d.panel.activeHomonym].strCurrentGram.split(';')[0]+']' : ''));

  // Group/link brackets
  var bracketG = zoomGroup.append('g').attr('class','brackets');
  var bracketItems = bracketG.selectAll('.br')
    .data(allArcs.filter(d=>{
      var lp=d.clause.WordPanels[d.arc.firstWord], rp=d.clause.WordPanels[d.arc.lastWord];
      return lp&&rp&&lp._row===rp._row;
    })).enter().append('g').attr('class','br');

  bracketItems.each(function(d) {
    var arc=d.arc, clause=d.clause;
    var lp=clause.WordPanels[arc.firstWord], rp=clause.WordPanels[arc.lastWord];
    var yBase=lp._row*ROW_HEIGHT;
    var x1=lp.centerX, x2=rp.centerX;
    var y=yBase+WORD_Y+POS_BELOW+SMALL_FONT+BRACKET_BASE+arc.depth*BRACKET_ROW;
    var color=arc.groupArc?GROUP_COLOR:LINK_COLOR;
    var sw=arc.groupArc?2.5:1.5;
    var g=d3.select(this);

    g.append('line').attr('x1',x1).attr('y1',y).attr('x2',x2).attr('y2',y)
      .attr('stroke',color).attr('stroke-width',sw)
      .attr('stroke-dasharray',arc.groupArc?null:'4,3');
    g.append('line').attr('x1',x1).attr('y1',y).attr('x2',x1).attr('y2',y-TICK)
      .attr('stroke',color).attr('stroke-width',sw);
    g.append('line').attr('x1',x2).attr('y1',y).attr('x2',x2).attr('y2',y-TICK)
      .attr('stroke',color).attr('stroke-width',sw);
    [x1,x2].forEach(function(px){
      g.append('circle').attr('cx',px).attr('cy',y-TICK).attr('r',2.5).attr('fill',color);
    });

    if (arc.strName) {
      var tw=measureText(arc.strName,SMALL_FONT,'bold');
      var mid=(x1+x2)/2, lx=mid-tw/2, ly=y+SMALL_FONT*0.35;
      g.append('rect').attr('x',lx-6).attr('y',ly-SMALL_FONT-2)
        .attr('width',tw+12).attr('height',SMALL_FONT+4)
        .attr('fill',arc.groupArc?'rgba(99,102,241,0.10)':'rgba(244,63,94,0.10)')
        .attr('stroke',color+'44').attr('stroke-width',1).attr('rx',4).attr('ry',4);
      g.append('text').attr('x',lx).attr('y',ly)
        .attr('fill',color).attr('font-size',SMALL_FONT+'px')
        .attr('font-family',FONT).attr('font-weight','bold').text(arc.strName);
    }
  });

  // Subject-predicate arcs
  var subjG = zoomGroup.append('g').attr('class','subj-arcs');
  var subjItems = subjG.selectAll('.sa')
    .data(allSubjArcs.filter(d=>{
      var p1=d.clause.WordPanels[d.arc.firstWord], p2=d.clause.WordPanels[d.arc.lastWord];
      return p1&&p2&&p1._row===p2._row;
    })).enter().append('g').attr('class','sa');

  var sTxt = cfg().subjLabel, pTxt = cfg().predLabel;

  subjItems.each(function(d) {
    var arc=d.arc, clause=d.clause;
    var p1=clause.WordPanels[arc.firstWord], p2=clause.WordPanels[arc.lastWord];
    var yBase=p1._row*ROW_HEIGHT, yPos=yBase+WORD_Y+POS_BELOW+15;
    var g=d3.select(this);

    g.append('path')
      .attr('d','M'+p1.centerX+','+yPos+' C'+p1.centerX+','+(yPos+50)+' '+p2.centerX+','+(yPos+50)+' '+p2.centerX+','+yPos)
      .attr('fill','none').attr('stroke',SUBJ_COLOR).attr('stroke-width',3).attr('stroke-linecap','round');
    g.append('circle').attr('cx',p2.centerX).attr('cy',yPos).attr('r',3.5).attr('fill',SUBJ_COLOR);

    var sw2=measureText(sTxt,SMALL_FONT,'bold'), pw=measureText(pTxt,SMALL_FONT,'bold');

    g.append('rect').attr('x',p1.centerX-sw2/2-4).attr('y',yPos+20).attr('width',sw2+8).attr('height',16)
      .attr('fill','rgba(5,150,105,0.1)').attr('rx',2);
    g.append('text').attr('x',p1.centerX-sw2/2).attr('y',yPos+32)
      .attr('fill',SUBJ_COLOR).attr('font-size',SMALL_FONT+'px').attr('font-family',FONT).attr('font-weight','bold').text(sTxt);

    g.append('rect').attr('x',p2.centerX-pw/2-4).attr('y',yPos+20).attr('width',pw+8).attr('height',16)
      .attr('fill','rgba(217,119,6,0.1)').attr('rx',2);
    g.append('text').attr('x',p2.centerX-pw/2).attr('y',yPos+32)
      .attr('fill',PREDIC_COLOR).attr('font-size',SMALL_FONT+'px').attr('font-family',FONT).attr('font-weight','bold').text(pTxt);
  });

  // Legend
  svg.selectAll('.legend').remove();
  var legend = svg.append('g').attr('class','legend').attr('transform','translate(12,16)');
  [
    {c:GROUP_COLOR, d:'', l:'— group', w:2},
    {c:LINK_COLOR, d:'4,3', l:'- - link', w:1.5},
    {c:SUBJ_COLOR, d:'', l:'● subject', w:2.5},
    {c:PREDIC_COLOR, d:'', l:'● predicate', w:2}
  ].forEach(function(item,i){
    var lg = legend.append('g').attr('transform','translate(0,'+(i*17)+')');
    lg.append('line').attr('x1',0).attr('y1',5).attr('x2',20).attr('y2',5)
      .attr('stroke',item.c).attr('stroke-width',item.w).attr('stroke-dasharray',item.d||null);
    lg.append('text').attr('x',26).attr('y',9).attr('fill',item.c)
      .attr('font-size',SMALL_FONT+'px').attr('font-family',FONT).text(item.l);
  });
}

// ── Save SVG ────────────────────────────────────────────────

function saveSvg() {
  var svgEl = document.querySelector('#svgContainer svg');
  if (!svgEl) return;
  var clone = svgEl.cloneNode(true);
  clone.setAttribute('xmlns','http://www.w3.org/2000/svg');
  var svgStr = new XMLSerializer().serializeToString(clone);
  var blob = new Blob([svgStr], {type:'image/svg+xml;charset=utf-8'});
  var url = URL.createObjectURL(blob);
  var a = document.createElement('a');
  a.href = url;
  a.download = 'aot_syntax.svg';
  document.body.appendChild(a);
  a.click();
  document.body.removeChild(a);
  URL.revokeObjectURL(url);
}

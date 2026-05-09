import { SynanDaemonUrl } from './common.js';

var TopClauses = [];
var cursor;

var FONT_COLOR = '#1e293b',
    BG_COLOR = 'white',
    GROUP_ARC_COLOR = '#6366f1',
    NONGROUP_ARC_COLOR = '#f43f5e',
    SUBJ_COLOR = '#10b981',
    PREDIC_COLOR = '#f59e0b',
    FONT = 'Arial',
    ARC_FONT = 'Arial',
    FONT_SIZE = 20,
    ARC_FONT_SIZE = 12,
    SPACE_SIZE = 10,
    LEFT_SPACE = 2,
    TOP_SPACE = 30,
    ARC_HEIGHT = 40;

var mainCanvas, longCanvas, ctx, ctxMain;

function initCanvas() {
    mainCanvas = document.getElementById("synanCanvas");
    longCanvas = document.createElement('canvas');
    ctx = longCanvas.getContext("2d");
    ctxMain = mainCanvas.getContext("2d");
}

initCanvas();

class CMorphVariant {
    constructor(synUnits, arcs, subjArcs) {
        this.synUnits = synUnits;
        this.arcs = arcs;
        this.subjArcs = subjArcs;
        this.compareTo = function(var2){
            for (var i = 0; i < var2.synUnits.length; i++) {
                if (this.synUnits[i].homonymNo < var2.synUnits[i].homonymNo)
                    return -1;
                if (this.synUnits[i].homonymNo > var2.synUnits[i].homonymNo)
                    return 1;
            }
            return 0;
        };

        this.equals = function(Var) {
            return (this.compareTo(Var) == 0);
        };
    };
}

class WordArc {
    constructor(group) {
        this.childArcs = [];
        this.firstWord = 0;
        this.lastWord = 0;
        this.height = 0;
        this.groupArc = true;
        this.isSubj = false;
        this.parentGroupLeg = {};
        this.firstWord = group.start;
        this.lastWord = group.last;
        this.strName = group.descr;
        this.groupArc = group.isGroup;
        this.isSubj = group.isSubj;
        this.getHeight = function() {
            if(this.height == 0)
                this.height = this.calculateHeight();
            return this.height;
        };

        this.calculateHeight = function() {
            var height = 0;
            for(var i in this.childArcs) {
                var ii = this.childArcs[i].calculateHeight();
                if(ii > height)
                    height = ii;
            }
            return height + ARC_HEIGHT;
        };

        this.drawOneLineArc = function(Clause, leftPoint, rightPoint) {
            var WordPannelLeft = Clause.WordPanels[this.firstWord];
            var x1 = leftPoint.x;
            var y1 = leftPoint.y;
            var x2 = rightPoint.x;
            var y2 = rightPoint.y;
            var yTop = WordPannelLeft.y - this.height;
            var midX = (x1 + x2) / 2;
            var cpOffset = this.height * 0.6;

            ctx.beginPath();
            ctx.moveTo(x1, y1);
            ctx.bezierCurveTo(x1, y1 - cpOffset, midX, yTop - cpOffset * 0.3, midX, yTop);
            ctx.bezierCurveTo(midX, yTop - cpOffset * 0.3, x2, y2 - cpOffset, x2, y2);
            ctx.stroke();

            this.parentGroupLeg.x = midX;
            this.parentGroupLeg.y = yTop;
        };

        this.draw = function(Clause) {
            for (var i in this.childArcs)
                this.childArcs[i].draw(Clause);

            this.height = this.getHeight();
            var leftPoint = this.getLeftLegPoint(Clause);
            var rightPoint = this.getRightLegPoint(Clause);

            var arcColor = this.groupArc ? GROUP_ARC_COLOR : NONGROUP_ARC_COLOR;
            ctx.strokeStyle = arcColor;
            ctx.lineWidth = this.groupArc ? 2 : 1.5;

            if (!this.groupArc) {
                ctx.setLineDash([4, 3]);
            } else {
                ctx.setLineDash([]);
            }

            this.drawOneLineArc(Clause, leftPoint, rightPoint);
            ctx.setLineDash([]);

            // Connection dots at endpoints
            var dotRadius = 3;
            ctx.fillStyle = arcColor;
            ctx.beginPath();
            ctx.arc(leftPoint.x, leftPoint.y, dotRadius, 0, Math.PI * 2);
            ctx.fill();
            ctx.beginPath();
            ctx.arc(rightPoint.x, rightPoint.y, dotRadius, 0, Math.PI * 2);
            ctx.fill();

            // Label with background pill
            var label = this.strName.replace(/\0/g, '').trim();
            if (label) {
                ctx.font = ARC_FONT_SIZE + 'px ' + ARC_FONT;
                var textWidth = ctx.measureText(label).width;
                var padX = 5, padY = 3;
                var lx = this.parentGroupLeg.x - textWidth / 2;
                var ly = this.parentGroupLeg.y - ARC_FONT_SIZE * 0.3;

                ctx.fillStyle = this.groupArc ? 'rgba(99,102,241,0.12)' : 'rgba(244,63,94,0.12)';
                ctx.beginPath();
                var rx = lx - padX, ry = ly - ARC_FONT_SIZE - padY;
                var rw = textWidth + padX * 2, rh = ARC_FONT_SIZE + padY * 2;
                var r = 4;
                ctx.moveTo(rx + r, ry);
                ctx.lineTo(rx + rw - r, ry);
                ctx.quadraticCurveTo(rx + rw, ry, rx + rw, ry + r);
                ctx.lineTo(rx + rw, ry + rh - r);
                ctx.quadraticCurveTo(rx + rw, ry + rh, rx + rw - r, ry + rh);
                ctx.lineTo(rx + r, ry + rh);
                ctx.quadraticCurveTo(rx, ry + rh, rx, ry + rh - r);
                ctx.lineTo(rx, ry + r);
                ctx.quadraticCurveTo(rx, ry, rx + r, ry);
                ctx.closePath();
                ctx.fill();

                ctx.strokeStyle = arcColor;
                ctx.lineWidth = 1;
                ctx.stroke();

                ctx.fillStyle = arcColor;
                ctx.font = 'bold ' + ARC_FONT_SIZE + 'px ' + ARC_FONT;
                ctx.fillText(label, lx, ly);
            }

            // Reset
            ctx.lineWidth = 1;
        };

        this.getLeftLegPoint = function(Clause) {
            var WordPannelLeft = Clause.WordPanels[this.firstWord];

            var leftPoint = {};
            var bSet = false;
            if(this.childArcs.length > 0) {
                var wordArcLeft = this.childArcs[0];
                //���������� �����-�� �������
                if ( (wordArcLeft.firstWord == this.firstWord) &&
                    ((wordArcLeft.groupArc && this.groupArc) ||
                    (!wordArcLeft.groupArc && !this.groupArc)||
                    (!wordArcLeft.groupArc && this.groupArc)))
                {
                    leftPoint = wordArcLeft.parentGroupLeg;
                    bSet = true;
                }
            }

            if (!bSet) {
                if(this.groupArc) {
                    leftPoint.x = WordPannelLeft.x + WordPannelLeft.width/2;
                    leftPoint.y = WordPannelLeft.y;
                } else {
                    leftPoint.x = WordPannelLeft.x;
                    leftPoint.y = WordPannelLeft.y;
                }
            }
            return leftPoint;
        };

        this.getRightLegPoint = function(Clause) {
            var rightPoint = {};

            var WordPannelRight = Clause.WordPanels[this.lastWord];

            var bSet = false;
            if(this.childArcs.length >= 1) {
                var wordArcRight = this.childArcs[this.childArcs.length - 1];
                if ( (wordArcRight.lastWord == this.lastWord) &&
                    ((wordArcRight.groupArc && this.groupArc) ||
                    (!wordArcRight.groupArc && !this.groupArc)||
                    ( !wordArcRight.groupArc && this.groupArc)))
                {
                    rightPoint = wordArcRight.parentGroupLeg;
                    bSet = true;
                }
            }

            if(!bSet) {
                if(this.groupArc) {
                    rightPoint.x = WordPannelRight.x + WordPannelRight.width/2;
                    rightPoint.y = WordPannelRight.y;
                } else {
                    rightPoint.x = WordPannelRight.x + WordPannelRight.width;
                    rightPoint.y = WordPannelRight.y;
                }
            }
            return rightPoint;
        }
    };
};

class CSynUnit {
    constructor (str) {
        if (str != 'emtpy'){
            this.homonymNo = str.homNo;
            this.strGram = str.grm;
        }
    };
}

class Homonym {
    constructor(str) {
        this.lemma = str;
        this.strCurrentGram = '';
    };
};

class WordPanel {
    constructor(word) {
        this.x = 0;
        this.y = 0;
        this.width = 0;
        this.activeHomonym = 0;
        this.word = word.str;
        this.homonyms = [];
        for (var i in word.homonyms) {
            this.homonyms.push(new Homonym(word.homonyms[i]));
        }
    };
}  

class TopClause {
    constructor(Info) {
        this.currentMorphVariant = 0;
        this.WordPanels = [];
        this.MorphVariants = [];
        this.parseWords(Info.words);
        this.parseVariants(Info.variants);

        this.getCurArcs = function() {
            var CurrVar = this.getActiveHomonymNumbers();
            for(var i = 0; i < this.MorphVariants.length; i++) {
                var Var = this.MorphVariants[i];
                if( Var.equals(CurrVar) ) {
                    this.currentMorphVariant = i;
                    this.setActiveHomonyms(i);
                    return Var.arcs;
                }
            }
            this.currentMorphVariant = -1;
            return [];
        };

        this.getActiveHomonymNumbers = function() {
            var WordsCount = this.WordPanels.length;
            var arr = [];
            for (var i = 0; i < WordsCount; i++) {
                var Panel = this.WordPanels[i];
                var U = new CSynUnit('empty');
                U.homonymNo = Panel.activeHomonym;
                arr.push(U);
            }
            return new CMorphVariant(arr, [], []);
        };

        this.drawWordPanels = function(height) {
            ctx.fillStyle = FONT_COLOR;
            for (var i in this.WordPanels) {
                var panel = this.WordPanels[i];
                if (panel.homonyms.length > 1)  ctx.font = 'bold ' + FONT_SIZE + 'px ' + FONT;
                else                            ctx.font = FONT_SIZE + 'px ' + FONT;
                panel.width = ctx.measureText(panel.word).width;
                var prevLineNo = Math.floor(cursor / ctxMain.canvas.width);
                var lineNo = Math.floor((panel.width + cursor) / ctxMain.canvas.width);
                if (lineNo > prevLineNo) {
                    cursor = ctxMain.canvas.width * lineNo + LEFT_SPACE;
                }
                panel.x = cursor;
                panel.y = height;
                panel.outerX = cursor - ctxMain.canvas.width * lineNo;
                panel.outerY = height + ctx.canvas.height * lineNo;
                ctx.fillText(panel.word, panel.x, panel.y + FONT_SIZE);
                cursor += panel.width + SPACE_SIZE;
            }
        };

        this.drawSubjPredic = function () {
            if (this.currentMorphVariant < 0) return;
            var homs = this.MorphVariants[this.currentMorphVariant];
            for(var i = 0; i < homs.subjArcs.length; i++) {
                var arc = homs.subjArcs[i];
                var panel1 = this.WordPanels[arc.firstWord];
                var panel2 = this.WordPanels[arc.lastWord];
                this.drawSubj(panel1);
                this.drawPredic(panel2);
            }
        };

        this.drawSubj = function(panel) {
            var y = panel.y + FONT_SIZE * 1.2;
            ctx.strokeStyle = SUBJ_COLOR;
            ctx.lineWidth = 2.5;
            ctx.beginPath();
            ctx.moveTo(panel.x - 2, y);
            ctx.lineTo(panel.x + panel.width + 2, y);
            ctx.stroke();
            // Small "S" label
            ctx.font = 'bold 10px ' + ARC_FONT;
            ctx.fillStyle = SUBJ_COLOR;
            ctx.fillText('S', panel.x + panel.width + 5, y + 4);
            ctx.lineWidth = 1;
        };

        this.drawPredic = function(panel) {
            var y1 = panel.y + FONT_SIZE * 1.2;
            var y2 = panel.y + FONT_SIZE * 1.45;
            ctx.strokeStyle = PREDIC_COLOR;
            ctx.lineWidth = 2.5;
            ctx.beginPath();
            ctx.moveTo(panel.x - 2, y1);
            ctx.lineTo(panel.x + panel.width + 2, y1);
            ctx.stroke();
            ctx.beginPath();
            ctx.moveTo(panel.x - 2, y2);
            ctx.lineTo(panel.x + panel.width + 2, y2);
            ctx.stroke();
            // Small "P" label
            ctx.font = 'bold 10px ' + ARC_FONT;
            ctx.fillStyle = PREDIC_COLOR;
            ctx.fillText('P', panel.x + panel.width + 5, y2 + 4);
            ctx.lineWidth = 1;
        };

        this.drawArcs = function() {
            var arcs = this.getCurArcs();
            for (var i in arcs) {
                arcs[i].draw(this);
            }
        };

        this.addPopups = function() {
            for (var i in this.WordPanels) {
                var panel = this.WordPanels[i];
                var popDiv = document.createElement("div");
                popDiv.style.position = 'absolute';
                popDiv.style.top = panel.outerY;
                popDiv.style.left = panel.outerX;
                popDiv.style.height = FONT_SIZE*1.2 + 'px';
                popDiv.style.width = panel.width + 'px';
                popDiv.title = panel.homonyms[panel.activeHomonym].lemma + ' ' + panel.homonyms[panel.activeHomonym].strCurrentGram;
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
                var canWrap = document.getElementById('canvasWrapper');
                canWrap.appendChild(popDiv);
            }
        };
    };
}

var protoClause = TopClause.prototype;

protoClause.parseWords = function(words) {
    for (var i in words) {
        this.WordPanels.push(new WordPanel(words[i]));
    }
};

protoClause.parseVariants = function(variants) {
    for (var i in variants) {
        this.parseOneVariant(variants[i]);
    }
    if( this.MorphVariants.length > 0 )
        this.setActiveHomonyms(0);
};

protoClause.setActiveHomonyms = function(VarNo) {
    var hom = this.MorphVariants[VarNo];
    for(var i = 0 ; i < hom.synUnits.length ; i++ )
    {
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
        if (arc.isSubj) {
            subjArcs.push(arc);
        } else {
            arcs.push(arc);
        }
    }
    arcs = this.orderArcs(arcs);
    this.MorphVariants.push(new CMorphVariant(homs, arcs, subjArcs));
};

protoClause.readUnits = function(str) {
    var wordsCount = this.WordPanels.length,
        ii = 0,
        arr = [];
    while ((ii < wordsCount) && (str[ii])) {
        arr.push(new CSynUnit(str[ii]));
        ii++;
    }
    return arr;
};

protoClause.orderArcsRec = function(arcs, parentArc, iCur) {
    for(var i = iCur; i < arcs.length;) {
        var arc = arcs[i];
        if(+arc.firstWord > +parentArc.lastWord)
            return i;
        i = this.orderArcsRec(arcs, arc, i + 1);
        parentArc.childArcs.push(arc);
    }
    return arcs.length;
};

protoClause.orderArcs = function(arcs) {
    var ordered = [];
    for(var i = 0; i < arcs.length;) {
        var arc = arcs[i];
        i = this.orderArcsRec(arcs, arc, i + 1);
        ordered.push(arc);
    }
    return ordered;
};

function parseSynanJson(synanJson) {
    TopClauses = []
    for (var s in synanJson) {
        for (var c in synanJson[s]) {
            TopClauses.push(new TopClause(synanJson[s][c]));
        }
    }
}


function calcMaxArcHeight() {
    var height = 0;
    for (var ClauseNo in TopClauses) {
        var arcs = TopClauses[ClauseNo].getCurArcs();
        arcs = arcs.sort(function(a,b){return b.childArcs.length - a.childArcs.length});
        for(var i in arcs) {
            var curHeight = arcs[i].getHeight();
            if(curHeight > height)
                height = curHeight;
        }
    }
    return height;
};

function calcWordsLength() {
    var length = LEFT_SPACE;
    for (var i in TopClauses) {
        var Clause = TopClauses[i];
        for (var j in Clause.WordPanels) {
            if (Clause.WordPanels[j].homonyms.length > 1)  ctx.font = 'bold ' + FONT_SIZE + 'px ' + FONT;
            else                                            ctx.font = FONT_SIZE + 'px ' + FONT;
            var prevLineNo = Math.floor(length / ctxMain.canvas.width);
            var lineNo = Math.floor((ctx.measureText(Clause.WordPanels[j].word).width + length) / ctxMain.canvas.width);
            if (lineNo > prevLineNo) {
                length = ctxMain.canvas.width * lineNo + LEFT_SPACE;
            }
            length += ctx.measureText(Clause.WordPanels[j].word).width + SPACE_SIZE;
        }
    }
    return length;
};

function wrapAll() {
    var linesNo = Math.ceil(ctx.canvas.width / ctxMain.canvas.width);
    ctxMain.canvas.height = linesNo * ctx.canvas.height;
    ctxMain.clearRect(0,0,ctxMain.canvas.width,ctxMain.canvas.height);
    for (var i = 0; i < linesNo; i++) {
        ctxMain.drawImage(ctx.canvas, ctxMain.canvas.width*i, 0, ctxMain.canvas.width, ctx.canvas.height, 0, ctx.canvas.height * i, ctxMain.canvas.width, ctx.canvas.height);
    }
};

function removePopups() {
    var wrapper = document.getElementById('canvasWrapper');
    var popDiv = wrapper.getElementsByClassName("synanWordPanel");
    while (popDiv.length > 0){                                      //������ ���, ����� �� ��������
        for (var i = 0; i < popDiv.length; i++)
            popDiv[i].parentNode.removeChild(popDiv[i]);
        popDiv = wrapper.getElementsByClassName("synanWordPanel");
    }
};

function addPopups() {
    for (var i in TopClauses)
        TopClauses[i].addPopups();
    window.onclick = function(event) {
        if (!event.target.matches('.panelDroppable')) {
            var dropdowns = document.getElementsByClassName("synanDropdownContent");
            for (var i = 0; i < dropdowns.length; i++)
                dropdowns[i].style.display = 'none';
        }
    }
};

function drawAll() {
    removePopups();

    var wrapper = document.getElementById('canvasWrapper');
    if (wrapper) {
        var style = getComputedStyle(wrapper);
        var paddingX = (parseFloat(style.paddingLeft) || 0) + (parseFloat(style.paddingRight) || 0);
        var availableWidth = wrapper.clientWidth - paddingX;
        if (availableWidth > 0) {
            ctxMain.canvas.width = availableWidth;
        }
    }

    var height = calcMaxArcHeight() + TOP_SPACE;
    var width = calcWordsLength();
    ctx.canvas.height = height + FONT_SIZE*1.6;
    ctx.canvas.width = width;
    ctx.clearRect(0,0,ctx.canvas.width,ctx.canvas.height);
    cursor = LEFT_SPACE;
    for (var i in TopClauses) {
        TopClauses[i].drawWordPanels(height);
        TopClauses[i].drawArcs();
        TopClauses[i].drawSubjPredic();
    }
    wrapAll();
    addPopups();
    drawLegend();
}

function drawLegend() {
    var langua = document.getElementById("Language").value;
    var x = 12, y = ctxMain.canvas.height - 10;
    var lineLen = 20, gap = 18, lineH = 16;
    ctxMain.font = '11px Arial';
    ctxMain.lineWidth = 1;

    var labels = {
        group: '— группа',
        link: '- - связь',
        subj: 'S подлежащее',
        predic: 'P сказуемое'
    };

    if (langua === 'English') {
        labels = {
            group: '— group',
            link: '- - link',
            subj: 'S subject',
            predic: 'P predicate'
        };
    } else if (langua === 'German') {
        labels = {
            group: '— Gruppe',
            link: '- - Verbindung',
            subj: 'S Subjekt',
            predic: 'P Prädikat'
        };
    } else if (langua === 'Ukrainian') {
        labels = {
            group: '— група',
            link: '- - зв\'язок',
            subj: 'S підмет',
            predic: 'P присудок'
        };
    }

    // Group arc
    y -= lineH;
    ctxMain.strokeStyle = GROUP_ARC_COLOR;
    ctxMain.setLineDash([]);
    ctxMain.beginPath();
    ctxMain.moveTo(x, y + 6);
    ctxMain.lineTo(x + lineLen, y + 6);
    ctxMain.stroke();
    ctxMain.fillStyle = GROUP_ARC_COLOR;
    ctxMain.fillText(labels.group, x + lineLen + 4, y + 10);

    // Non-group arc
    y -= lineH;
    ctxMain.strokeStyle = NONGROUP_ARC_COLOR;
    ctxMain.setLineDash([4, 3]);
    ctxMain.beginPath();
    ctxMain.moveTo(x, y + 6);
    ctxMain.lineTo(x + lineLen, y + 6);
    ctxMain.stroke();
    ctxMain.fillStyle = NONGROUP_ARC_COLOR;
    ctxMain.fillText(labels.link, x + lineLen + 4, y + 10);

    // Subject
    y -= lineH;
    ctxMain.strokeStyle = SUBJ_COLOR;
    ctxMain.setLineDash([]);
    ctxMain.lineWidth = 2.5;
    ctxMain.beginPath();
    ctxMain.moveTo(x, y + 6);
    ctxMain.lineTo(x + lineLen, y + 6);
    ctxMain.stroke();
    ctxMain.fillStyle = SUBJ_COLOR;
    ctxMain.fillText(labels.subj, x + lineLen + 4, y + 10);

    // Predicate
    y -= lineH;
    ctxMain.strokeStyle = PREDIC_COLOR;
    ctxMain.beginPath();
    ctxMain.moveTo(x, y + 4);
    ctxMain.lineTo(x + lineLen, y + 4);
    ctxMain.stroke();
    ctxMain.beginPath();
    ctxMain.moveTo(x, y + 8);
    ctxMain.lineTo(x + lineLen, y + 8);
    ctxMain.stroke();
    ctxMain.fillStyle = PREDIC_COLOR;
    ctxMain.fillText(labels.predic, x + lineLen + 4, y + 10);

    ctxMain.setLineDash([]);
    ctxMain.lineWidth = 1;
}



function syntax_request() {
    var langua = document.getElementById("Language").value;
    var query = document.getElementById("InputText").value.trim();
    
    if (!query || query.length === 0) {
        alert('Please enter text to analyze');
        return;
    }

    var url = SynanDaemonUrl + "&action=syntax&langua=" + encodeURIComponent(langua);

    fetch(url, {
        method: 'POST',
        body: query
    })
        .then(function(response) {
            if (!response.ok) {
                throw new Error('Server returned ' + response.status);
            }
            return response.json();
        })
        .then(function(synanJson) {
            parseSynanJson(synanJson);
            drawAll();
        })
        .catch(function(err) {
            console.error('Syntax request failed:', err);
            alert('Error: ' + err.message);
        });
}

window.syntax_request = syntax_request;
window.reinitCanvas = function() {
    initCanvas();
    TopClauses = [];
};

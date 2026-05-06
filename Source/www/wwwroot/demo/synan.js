import { SynanDaemonUrl } from './common.js';

console.log('[synan.js] loaded - version with full-width canvas fix');

/**
 * Configuration constants for rendering
 */
const CONFIG = {
    FONT_COLOR: 'black',
    BG_COLOR: 'white',
    GROUP_ARC_COLOR: 'blue',
    NONGROUP_ARC_COLOR: 'red',
    FONT: 'Arial',
    ARC_FONT: 'Arial',
    FONT_SIZE: 20,
    ARC_FONT_SIZE: 14,
    SPACE_SIZE: 10,
    LEFT_SPACE: 2,
    TOP_SPACE: 30,
    ARC_HEIGHT: 40
};

/**
 * State management
 */
let TopClauses = [];
let cursor = 0;

/**
 * Canvas setup
 */
const mainCanvas = document.getElementById("synanCanvas");
const longCanvas = document.createElement('canvas');
const ctx = longCanvas.getContext("2d");
const ctxMain = mainCanvas.getContext("2d");

/**
 * Morphological variant class - represents a grammatical interpretation
 */
class CMorphVariant {
    constructor(synUnits, arcs, subjArcs) {
        this.synUnits = synUnits;
        this.arcs = arcs;
        this.subjArcs = subjArcs;
    }

    compareTo(var2) {
        for (let i = 0; i < var2.synUnits.length; i++) {
            if (this.synUnits[i].homonymNo < var2.synUnits[i].homonymNo) return -1;
            if (this.synUnits[i].homonymNo > var2.synUnits[i].homonymNo) return 1;
        }
        return 0;
    }

    equals(Var) {
        return this.compareTo(Var) === 0;
    }
}

/**
 * Word arc class - represents syntactic relationships
 */
class WordArc {
    constructor(group) {
        this.childArcs = [];
        this.groupArc = group.isGroup;
        this.isSubj = group.isSubj;
        this.firstWord = group.start;
        this.lastWord = group.last;
        this.strName = group.descr;
        this.parentGroupLeg = {};
    }

    getHeight() {
        if (this.height === 0) this.height = this.calculateHeight();
        return this.height;
    }

    calculateHeight() {
        let height = 0;
        for (const childArc of this.childArcs) {
            const childHeight = childArc.calculateHeight();
            if (childHeight > height) height = childHeight;
        }
        return height + CONFIG.ARC_HEIGHT;
    }

    drawOneLineArc(Clause, leftPoint, rightPoint) {
        const WordPannelLeft = Clause.WordPanels[this.firstWord];
        ctx.beginPath();
        ctx.moveTo(leftPoint.x, leftPoint.y);
        ctx.lineTo(leftPoint.x, WordPannelLeft.y - this.height);
        ctx.lineTo(rightPoint.x, WordPannelLeft.y - this.height);
        ctx.lineTo(rightPoint.x, rightPoint.y);
        ctx.stroke();
        this.parentGroupLeg = {
            x: leftPoint.x + (rightPoint.x - leftPoint.x) / 2,
            y: WordPannelLeft.y - this.height
        };
    }

    draw(Clause) {
        for (const childArc of this.childArcs) childArc.draw(Clause);
        this.height = this.getHeight();
        const leftPoint = this.getLeftLegPoint(Clause);
        const rightPoint = this.getRightLegPoint(Clause);
        
        ctx.strokeStyle = this.groupArc ? CONFIG.GROUP_ARC_COLOR : CONFIG.NONGROUP_ARC_COLOR;
        this.drawOneLineArc(Clause, leftPoint, rightPoint);
        
        ctx.font = `${CONFIG.ARC_FONT_SIZE}px ${CONFIG.ARC_FONT}`;
        ctx.fillText(this.strName, this.parentGroupLeg.x - ctx.measureText(this.strName).width / 2, this.parentGroupLeg.y - CONFIG.ARC_FONT_SIZE * 0.3);
    }

    getLeftLegPoint(Clause) {
        const WordPannelLeft = Clause.WordPanels[this.firstWord];
        let leftPoint = {};
        let bSet = false;
        
        if (this.childArcs.length > 0) {
            const wordArcLeft = this.childArcs[0];
            if ((wordArcLeft.firstWord === this.firstWord) && 
                ((wordArcLeft.groupArc && this.groupArc) ||
                 (!wordArcLeft.groupArc && !this.groupArc) ||
                 (!wordArcLeft.groupArc && this.groupArc))) {
                leftPoint = wordArcLeft.parentGroupLeg;
                bSet = true;
            }
        }
        
        if (!bSet) {
            leftPoint = {
                x: this.groupArc ? WordPannelLeft.x + WordPannelLeft.width / 2 : WordPannelLeft.x,
                y: WordPannelLeft.y
            };
        }
        return leftPoint;
    }

    getRightLegPoint(Clause) {
        const WordPannelRight = Clause.WordPanels[this.lastWord];
        let rightPoint = {};
        let bSet = false;
        
        if (this.childArcs.length >= 1) {
            const wordArcRight = this.childArcs[this.childArcs.length - 1];
            if ((wordArcRight.lastWord === this.lastWord) &&
                ((wordArcRight.groupArc && this.groupArc) ||
                 (!wordArcRight.groupArc && !this.groupArc) ||
                 (!wordArcRight.groupArc && this.groupArc))) {
                rightPoint = wordArcRight.parentGroupLeg;
                bSet = true;
            }
        }
        
        if (!bSet) {
            rightPoint = {
                x: this.groupArc ? WordPannelRight.x + WordPannelRight.width / 2 : WordPannelRight.x + WordPannelRight.width,
                y: WordPannelRight.y
            };
        }
        return rightPoint;
    }
}

/**
 * Syntactic unit class
 */
class CSynUnit {
    constructor(str) {
        if (str !== 'empty') {
            this.homonymNo = str.homNo;
            this.strGram = str.grm;
        }
    }
}

/**
 * Homonym class
 */
class Homonym {
    constructor(str) {
        this.lemma = str;
        this.strCurrentGram = '';
    }
}

/**
 * Word panel class - represents a word in the visualization
 */
class WordPanel {
    constructor(word) {
        this.x = 0;
        this.y = 0;
        this.width = 0;
        this.activeHomonym = 0;
        this.word = word.str;
        this.homonyms = word.homonyms.map(h => new Homonym(h));
    }
}

/**
 * Top clause class - main syntactic structure
 */
class TopClause {
    constructor(Info) {
        this.currentMorphVariant = 0;
        this.WordPanels = [];
        this.MorphVariants = [];
        this.parseWords(Info.words);
        this.parseVariants(Info.variants);
    }

    parseWords(words) {
        for (const word of words) {
            this.WordPanels.push(new WordPanel(word));
        }
    }

    parseVariants(variants) {
        for (const variant of variants) {
            this.parseOneVariant(variant);
        }
        if (this.MorphVariants.length > 0) {
            this.setActiveHomonyms(0);
        }
    }

    getCurArcs() {
        const CurrVar = this.getActiveHomonymNumbers();
        for (let i = 0; i < this.MorphVariants.length; i++) {
            const Var = this.MorphVariants[i];
            if (Var.equals(CurrVar)) {
                this.currentMorphVariant = i;
                this.setActiveHomonyms(i);
                return Var.arcs;
            }
        }
        this.currentMorphVariant = -1;
        return [];
    }

    getActiveHomonymNumbers() {
        return this.WordPanels.map(panel => {
            const u = new CSynUnit('empty');
            u.homonymNo = panel.activeHomonym;
            return u;
        });
    }

    drawWordPanels(height) {
        ctx.fillStyle = CONFIG.FONT_COLOR;
        for (const panel of this.WordPanels) {
            ctx.font = (panel.homonyms.length > 1 ? 'bold ' : '') + `${CONFIG.FONT_SIZE}px ${CONFIG.FONT}`;
            panel.width = ctx.measureText(panel.word).width;
            
            const prevLineNo = Math.floor(cursor / ctxMain.canvas.width);
            const lineNo = Math.floor((panel.width + cursor) / ctxMain.canvas.width);
            
            if (lineNo > prevLineNo) {
                cursor = ctxMain.canvas.width * lineNo + CONFIG.LEFT_SPACE;
            }
            
            panel.x = cursor;
            panel.y = height;
            panel.outerX = cursor - ctxMain.canvas.width * lineNo;
            panel.outerY = height + ctx.canvas.height * lineNo;
            
            ctx.fillText(panel.word, panel.x, panel.y + CONFIG.FONT_SIZE);
            cursor += panel.width + CONFIG.SPACE_SIZE;
        }
    }

    drawSubjPredic() {
        if (this.currentMorphVariant < 0) return;
        const homs = this.MorphVariants[this.currentMorphVariant];
        ctx.strokeStyle = CONFIG.FONT_COLOR;
        
        for (const arc of homs.subjArcs) {
            const panel1 = this.WordPanels[arc.firstWord];
            const panel2 = this.WordPanels[arc.lastWord];
            this.drawSubj(panel1);
            this.drawPredic(panel2);
        }
    }

    drawSubj(panel) {
        ctx.beginPath();
        ctx.moveTo(panel.x, panel.y + CONFIG.FONT_SIZE * 1.2);
        ctx.lineTo(panel.x + panel.width, panel.y + CONFIG.FONT_SIZE * 1.2);
        ctx.stroke();
    }

    drawPredic(panel) {
        ctx.beginPath();
        ctx.moveTo(panel.x, panel.y + CONFIG.FONT_SIZE * 1.2);
        ctx.lineTo(panel.x + panel.width, panel.y + CONFIG.FONT_SIZE * 1.2);
        ctx.stroke();
        ctx.beginPath();
        ctx.moveTo(panel.x, panel.y + CONFIG.FONT_SIZE * 1.4);
        ctx.lineTo(panel.x + panel.width, panel.y + CONFIG.FONT_SIZE * 1.4);
        ctx.stroke();
    }

    drawArcs() {
        const arcs = this.getCurArcs();
        for (const arc of arcs) {
            arc.draw(this);
        }
    }

    addPopups() {
        for (let i = 0; i < this.WordPanels.length; i++) {
            const panel = this.WordPanels[i];
            const popDiv = document.createElement("div");
            
            popDiv.style.position = 'absolute';
            popDiv.style.top = panel.outerY + 'px';
            popDiv.style.left = panel.outerX + 'px';
            popDiv.style.height = CONFIG.FONT_SIZE * 1.2 + 'px';
            popDiv.style.width = panel.width + 'px';
            popDiv.title = panel.homonyms[panel.activeHomonym].lemma + ' ' + panel.homonyms[panel.activeHomonym].strCurrentGram;
            popDiv.className = 'synanWordPanel';
            
            if (panel.homonyms.length > 1) {
                const menuDiv = document.createElement("div");
                menuDiv.className = 'synanDropdownContent';
                
                for (let j = 0; j < panel.homonyms.length; j++) {
                    const menuEl = document.createElement("a");
                    menuEl.innerHTML = panel.homonyms[j].lemma;
                    menuEl.setAttribute('ActionCommand', j);
                    menuEl.setAttribute('wordPanelNo', i);
                    
                    menuEl.addEventListener("click", function() {
                        const homNum = this.getAttribute('ActionCommand');
                        const panelNo = this.getAttribute('wordPanelNo');
                        TopClauses[Math.floor(panelNo / TopClauses[0].WordPanels.length)].WordPanels[panelNo % TopClauses[0].WordPanels.length].activeHomonym = homNum;
                        drawAll();
                    });
                    menuDiv.appendChild(menuEl);
                }
                
                popDiv.appendChild(menuDiv);
                popDiv.style.cursor = 'pointer';
                popDiv.addEventListener("click", function() {
                    const dropdown = this.getElementsByClassName('synanDropdownContent')[0];
                    dropdown.style.display = dropdown.style.display === 'block' ? 'none' : 'block';
                });
                popDiv.classList.add('panelDroppable');
            }
            
            document.getElementById('canvasWrapper').appendChild(popDiv);
        }
    }

    setActiveHomonyms(VarNo) {
        const hom = this.MorphVariants[VarNo];
        for (let i = 0; i < hom.synUnits.length; i++) {
            const panel = this.WordPanels[i];
            panel.activeHomonym = hom.synUnits[i].homonymNo;
            panel.homonyms[panel.activeHomonym].strCurrentGram = hom.synUnits[i].strGram;
        }
    }
}

/**
 * Parse one variant into morphological variant
 */
function parseOneVariant(variant, WordPanelsCount) {
    const homs = readUnits(variant.units, WordPanelsCount);
    const arcs = [];
    const subjArcs = [];
    
    for (const group of variant.groups) {
        const arc = new WordArc({
            start: group.start,
            last: group.last,
            isGroup: group.isGroup,
            isSubj: group.isSubj,
            descr: group.descr
        });
        if (arc.isSubj) {
            subjArcs.push(arc);
        } else {
            arcs.push(arc);
        }
    }
    
    return new CMorphVariant(homs, orderArcs(arcs), subjArcs);
}

function readUnits(str, wordsCount) {
    const arr = [];
    let ii = 0;
    while ((ii < wordsCount) && (str[ii])) {
        arr.push(new CSynUnit(str[ii]));
        ii++;
    }
    return arr;
}

function orderArcsRec(arcs, parentArc, iCur) {
    for (let i = iCur; i < arcs.length;) {
        const arc = arcs[i];
        if (+arc.firstWord > +parentArc.lastWord) return i;
        i = orderArcsRec(arcs, arc, i + 1);
        parentArc.childArcs.push(arc);
    }
    return arcs.length;
}

function orderArcs(arcs) {
    const ordered = [];
    for (let i = 0; i < arcs.length;) {
        const arc = arcs[i];
        i = orderArcsRec(arcs, arc, i + 1);
        ordered.push(arc);
    }
    return ordered;
}

/* ========== Parsing and Drawing Functions ========== */

function parseSynanJson(synanJson) {
    TopClauses = [];
    for (const s in synanJson) {
        for (const c in synanJson[s]) {
            TopClauses.push(new TopClause(synanJson[s][c]));
        }
    }
}

function calcMaxArcHeight() {
    let height = 0;
    for (const Clause of TopClauses) {
        const arcs = Clause.getCurArcs();
        arcs.sort((a, b) => b.childArcs.length - a.childArcs.length);
        for (const arc of arcs) {
            const curHeight = arc.getHeight();
            if (curHeight > height) height = curHeight;
        }
    }
    return height;
}

function calcWordsLength() {
    let length = CONFIG.LEFT_SPACE;
    for (const Clause of TopClauses) {
        for (const panel of Clause.WordPanels) {
            ctx.font = (panel.homonyms.length > 1 ? 'bold ' : '') + `${CONFIG.FONT_SIZE}px ${CONFIG.FONT}`;
            const prevLineNo = Math.floor(length / ctxMain.canvas.width);
            const lineNo = Math.floor((ctx.measureText(panel.word).width + length) / ctxMain.canvas.width);
            if (lineNo > prevLineNo) {
                length = ctxMain.canvas.width * lineNo + CONFIG.LEFT_SPACE;
            }
            length += ctx.measureText(panel.word).width + CONFIG.SPACE_SIZE;
        }
    }
    return length;
}

function wrapAll() {
    const linesNo = Math.ceil(ctx.canvas.width / ctxMain.canvas.width);
    ctxMain.canvas.height = linesNo * ctx.canvas.height;
    ctxMain.clearRect(0, 0, ctxMain.canvas.width, ctxMain.canvas.height);
    
    for (let i = 0; i < linesNo; i++) {
        ctxMain.drawImage(ctx.canvas, ctxMain.canvas.width * i, 0, ctxMain.canvas.width, ctx.canvas.height, 0, ctx.canvas.height * i, ctxMain.canvas.width, ctx.canvas.height);
    }
}

function removePopups() {
    const wrapper = document.getElementById('canvasWrapper');
    const popDivs = wrapper.getElementsByClassName("synanWordPanel");
    while (popDivs.length > 0) {
        for (let i = 0; i < popDivs.length; i++) {
            popDivs[i].parentNode.removeChild(popDivs[i]);
        }
    }
}

function addPopups() {
    for (const Clause of TopClauses) {
        Clause.addPopups();
    }
    
    window.onclick = function(event) {
        if (!event.target.matches('.panelDroppable')) {
            const dropdowns = document.getElementsByClassName("synanDropdownContent");
            for (const dropdown of dropdowns) {
                dropdown.style.display = 'none';
            }
        }
    };
}

function drawAll() {
    console.log('[drawAll] called');
    removePopups();
    
    const wrapper = document.getElementById('canvasWrapper');
    if (wrapper) {
        const style = getComputedStyle(wrapper);
        const paddingX = (parseFloat(style.paddingLeft) || 0) + (parseFloat(style.paddingRight) || 0);
        const availableWidth = wrapper.clientWidth - paddingX;
        console.log(`[drawAll] wrapper w=${wrapper.clientWidth} padding=${paddingX} available=${availableWidth} canvasBefore=${ctxMain.canvas.width}`);
        
        if (availableWidth > 0 && availableWidth !== ctxMain.canvas.width) {
            ctxMain.canvas.width = availableWidth;
            console.log(`[drawAll] SET ctxMain.canvas.width = ${availableWidth}`);
        }
    }
    
    const height = calcMaxArcHeight() + CONFIG.TOP_SPACE;
    const width = calcWordsLength();
    console.log(`[drawAll] total content width=${width} height=${height}`);
    
    ctx.canvas.height = height + CONFIG.FONT_SIZE * 1.6;
    ctx.canvas.width = width;
    ctx.clearRect(0, 0, ctx.canvas.width, ctx.canvas.height);
    
    cursor = CONFIG.LEFT_SPACE;
    for (const Clause of TopClauses) {
        Clause.drawWordPanels(height);
        Clause.drawArcs();
        Clause.drawSubjPredic();
    }
    
    wrapAll();
    addPopups();
    
    console.log(`[drawAll] DONE: main canvas w=${ctxMain.canvas.width} h=${ctxMain.canvas.height}`);
}

/* ========== API Request Functions ========== */

async function syntax_request() {
    const langua = document.getElementById("Language").value;
    const query = document.getElementById("InputText").value.trim();
    
    if (!query || query.length === 0) {
        alert('Please enter text to analyze');
        return;
    }

    const submitBtn = document.querySelector('#syntax-form button[type="button"]');
    const originalText = submitBtn.textContent;
    submitBtn.textContent = 'Processing...';
    submitBtn.disabled = true;
    
    try {
        const url = `${SynanDaemonUrl}&action=syntax&langua=${encodeURIComponent(langua)}&query=${encodeURIComponent(query)}`;
        
        const response = await fetch(url);
        if (!response.ok) {
            throw new Error(`Server returned ${response.status}`);
        }
        
        const synanJson = await response.json();
        console.log(JSON.stringify(synanJson, null));
        parseSynanJson(synanJson);
        drawAll();
    } catch (err) {
        console.error('Syntax request failed:', err);
        alert('Error: ' + err.message);
    } finally {
        submitBtn.textContent = originalText;
        submitBtn.disabled = false;
    }
}

window.syntax_request = syntax_request;
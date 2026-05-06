export class SyntaxVisualizer {
    constructor(canvasId, wrapperId) {
        this.canvas = document.getElementById(canvasId);
        this.ctx = this.canvas.getContext('2d');
        this.wrapper = document.getElementById(wrapperId);
        
        // Settings
        this.colors = {
            font: '#f8fafc',
            groupArc: '#818cf8',
            nonGroupArc: '#f472b6',
            subj: '#10b981',
            predic: '#f59e0b'
        };
        this.font = 'Inter, system-ui, sans-serif';
        this.fontSize = 16;
        this.arcHeight = 35;
        this.spaceSize = 15;
        this.leftSpace = 20;
        this.topSpace = 50;
        
        this.clauses = [];
        this.cursor = this.leftSpace;
        this.maxWidth = 1000; // Default max width before wrapping
    }

    clear() {
        this.ctx.clearRect(0, 0, this.canvas.width, this.canvas.height);
        this.cursor = this.leftSpace;
        // Clear popups if any
        const popups = this.wrapper.querySelectorAll('.synan-popup');
        popups.forEach(p => p.remove());
    }

    draw(data) {
        console.log('Visualizer drawing with data:', data);
        if (!data || !data.clauses) return;

        // Set maxWidth based on wrapper size if possible, but at least 800px
        this.maxWidth = Math.max(this.wrapper.clientWidth - 100, 800);

        this.clauses = data.clauses.map(c => new TopClause(c, this));

        // 1. First pass: Calculate needed dimensions with wrapping
        let totalHeight = this.topSpace;

        this.clauses.forEach(clause => {
            const clauseHeight = clause.calculateLayout(this.maxWidth);
            totalHeight += clauseHeight + 150; // Spacing between sentences
        });

        // 2. Resize canvas
        this.canvas.width = this.maxWidth + this.leftSpace * 2;
        this.canvas.height = Math.max(totalHeight + 100, 400);

        // 3. Second pass: Actual drawing
        this.clear();
        let currentY = this.topSpace;
        this.clauses.forEach(clause => {
            const clauseHeight = clause.draw(currentY);
            currentY += clauseHeight + 150;
        });
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
    constructor(str) {
        this.lemma = str;
        this.strCurrentGram = '';
    }
}

class CMorphVariant {
    constructor(synUnits, arcs, subjArcs) {
        this.synUnits = synUnits;
        this.arcs = arcs;
        this.subjArcs = subjArcs;
    }
    equals(var2) {
        if (!var2 || !var2.synUnits) return false;
        for (let i = 0; i < var2.synUnits.length; i++) {
            if (this.synUnits[i].homonymNo !== var2.synUnits[i].homonymNo) return false;
        }
        return true;
    }
}

class WordArc {
    constructor(group, visualizer) {
        this.vis = visualizer;
        this.childArcs = [];
        this.firstWord = group.start;
        this.lastWord = group.last;
        this.strName = group.descr ? group.descr.replace(/\0/g, '').trim() : '';
        this.groupArc = group.isGroup;
        this.isSubj = group.isSubj;
        this.height = 0;
    }

    calculateHeight() {
        let maxChildHeight = 0;
        this.childArcs.forEach(child => {
            const h = child.calculateHeight();
            if (h > maxChildHeight) maxChildHeight = h;
        });
        this.height = maxChildHeight + this.vis.arcHeight;
        return this.height;
    }

    draw(clause) {
        this.childArcs.forEach(child => child.draw(clause));

        const ctx = this.vis.ctx;
        const leftPanel = clause.wordPanels[this.firstWord];
        const rightPanel = clause.wordPanels[this.lastWord];

        const x1 = leftPanel.x + leftPanel.width / 2;
        const x2 = rightPanel.x + rightPanel.width / 2;
        const y1 = leftPanel.y - 15;
        const y2 = rightPanel.y - 15;
        
        // Calculate dynamic height based on distance to avoid overlaps
        const distance = Math.abs(x2 - x1) + Math.abs(y2 - y1);
        const dynamicHeight = this.height + (distance * 0.05); 
        
        // Peak of the arc should be higher than both words
        const yTop = Math.min(y1, y2) - dynamicHeight;

        ctx.beginPath();
        ctx.strokeStyle = this.groupArc ? this.vis.colors.groupArc : this.vis.colors.nonGroupArc;
        ctx.lineWidth = 2;
        
        const midX = (x1 + x2) / 2;
        ctx.moveTo(x1, y1);
        ctx.quadraticCurveTo(x1, yTop, midX, yTop);
        ctx.quadraticCurveTo(x2, yTop, x2, y2);
        ctx.stroke();

        // Arrow head at the destination
        ctx.beginPath();
        ctx.arc(x2, y2, 3, 0, Math.PI * 2);
        ctx.fillStyle = ctx.strokeStyle;
        ctx.fill();

        // Label with background
        if (this.strName) {
            ctx.font = `italic 11px ${this.vis.font}`;
            const labelWidth = ctx.measureText(this.strName).width;
            ctx.fillStyle = 'rgba(15, 23, 42, 0.9)';
            ctx.roundRect(midX - labelWidth/2 - 4, yTop - 12, labelWidth + 8, 14, 4);
            ctx.fill();
            
            ctx.fillStyle = this.vis.colors.font;
            ctx.textAlign = 'center';
            ctx.fillText(this.strName, midX, yTop - 2);
        }
    }
}

class WordPanel {
    constructor(word) {
        this.word = word.str;
        this.homonyms = word.homonyms.map(h => new Homonym(h));
        this.activeHomonym = 0;
        this.x = 0;
        this.y = 0;
        this.width = 0;
    }
}

class TopClause {
    constructor(info, visualizer) {
        this.vis = visualizer;
        this.wordPanels = info.words.map(w => new WordPanel(w));
        this.morphVariants = [];
        this.currentVariantIdx = 0;
        this.clauseHeight = 0;
        
        this.parseVariants(info.variants);
    }

    parseVariants(variants) {
        variants.forEach(v => {
            const synUnits = v.units.map(u => new CSynUnit(u));
            const arcs = [];
            const subjArcs = [];
            
            v.groups.forEach(g => {
                const arc = new WordArc(g, this.vis);
                if (arc.isSubj) subjArcs.push(arc);
                else arcs.push(arc);
            });

            this.morphVariants.push(new CMorphVariant(synUnits, this.orderArcs(arcs), subjArcs));
        });
        
        if (this.morphVariants.length > 0) this.setActiveHomonyms(0);
    }

    orderArcs(arcs) {
        const root = { lastWord: 1000, childArcs: [] };
        this.orderArcsRec(arcs, root, 0);
        return root.childArcs;
    }

    orderArcsRec(arcs, parent, idx) {
        let i = idx;
        while (i < arcs.length) {
            const arc = arcs[i];
            if (parseInt(arc.firstWord) > parseInt(parent.lastWord)) return i;
            i = this.orderArcsRec(arcs, arc, i + 1);
            parent.childArcs.push(arc);
        }
        return arcs.length;
    }

    setActiveHomonyms(idx) {
        this.currentVariantIdx = idx;
        const variant = this.morphVariants[idx];
        variant.synUnits.forEach((unit, i) => {
            if (this.wordPanels[i]) {
                this.wordPanels[i].activeHomonym = unit.homonymNo;
                this.wordPanels[i].homonyms[unit.homonymNo].strCurrentGram = unit.strGram;
            }
        });
    }

    calculateLayout(maxWidth) {
        const ctx = this.vis.ctx;
        ctx.font = `600 ${this.vis.fontSize}px ${this.vis.font}`;
        
        let cursorX = this.vis.leftSpace;
        let lineNo = 0;
        const padding = 10;
        const lineSpacing = 150; // Space for arcs between lines

        this.wordPanels.forEach(panel => {
            panel.width = ctx.measureText(panel.word).width;
            const totalWordWidth = panel.width + this.vis.spaceSize + padding * 2;
            
            if (cursorX + totalWordWidth > maxWidth && cursorX > this.vis.leftSpace) {
                lineNo++;
                cursorX = this.vis.leftSpace;
            }
            
            panel.relativeX = cursorX;
            panel.lineNo = lineNo;
            cursorX += totalWordWidth;
        });

        // Height of arcs
        let maxArcHeight = 60;
        if (this.morphVariants[this.currentVariantIdx]) {
            this.morphVariants[this.currentVariantIdx].arcs.forEach(arc => {
                const h = arc.calculateHeight();
                if (h > maxArcHeight) maxArcHeight = h;
            });
        }

        this.baseLineHeight = maxArcHeight + 60;
        this.clauseHeight = (lineNo + 1) * this.baseLineHeight;
        return this.clauseHeight;
    }

    draw(startY) {
        const ctx = this.vis.ctx;
        
        this.wordPanels.forEach(panel => {
            panel.x = panel.relativeX;
            panel.y = startY + (panel.lineNo * this.baseLineHeight) + this.baseLineHeight - 40;

            // Draw word background pill
            ctx.fillStyle = 'rgba(99, 102, 241, 0.15)';
            ctx.strokeStyle = 'rgba(99, 102, 241, 0.3)';
            ctx.lineWidth = 1;
            const padding = 10;
            ctx.beginPath();
            if (ctx.roundRect) {
                ctx.roundRect(panel.x - padding, panel.y - this.vis.fontSize - 5, panel.width + padding * 2, this.vis.fontSize + 15, 8);
            } else {
                ctx.rect(panel.x - padding, panel.y - this.vis.fontSize - 5, panel.width + padding * 2, this.vis.fontSize + 15);
            }
            ctx.fill();
            ctx.stroke();

            // Draw Text
            ctx.fillStyle = this.vis.colors.font;
            ctx.font = `600 ${this.vis.fontSize}px ${this.vis.font}`;
            ctx.fillText(panel.word, panel.x, panel.y);
        });

        // Draw Arcs
        const variant = this.morphVariants[this.currentVariantIdx];
        if (variant) {
            variant.arcs.forEach(arc => arc.draw(this));
        }
        
        return this.clauseHeight;
    }
}

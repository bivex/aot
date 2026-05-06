import { SynanDaemonUrl } from '../demo/common.js';
import { SyntaxVisualizer } from './syntax-visualizer.js';

// Section Switching Logic
const navLinks = document.querySelectorAll('.nav-link');
const sections = document.querySelectorAll('.content-section');

navLinks.forEach(link => {
    link.addEventListener('click', (e) => {
        e.preventDefault();
        const targetSection = link.getAttribute('data-section');
        
        // Update active nav link
        navLinks.forEach(nl => nl.classList.remove('active'));
        link.classList.add('active');
        
        // Update active section
        sections.forEach(sec => {
            if (sec.id === targetSection) {
                sec.classList.add('active');
            } else {
                sec.classList.remove('active');
            }
        });
    });
});

// Morphology Logic
const morphInput = document.getElementById('morphInput');
const morphSubmitBtn = document.getElementById('morphSubmitBtn');
const morphResults = document.getElementById('morphResults');

morphSubmitBtn.addEventListener('click', async () => {
    const text = morphInput.value.trim();
    if (!text) return;

    const langua = document.querySelector('input[name="morphLangua"]:checked').value;
    const withParadigms = document.getElementById('withParadigms').checked;

    morphSubmitBtn.classList.add('loading');
    morphResults.innerHTML = '';

    try {
        const url = `${SynanDaemonUrl}&action=morph&langua=${langua}&query=${encodeURIComponent(text)}${withParadigms ? '&withparadigms=1' : ''}`;
        const response = await fetch(url);
        const data = await response.json();
        
        renderMorphResults(data);
    } catch (error) {
        console.error('Morphology request failed:', error);
        morphResults.innerHTML = `<div class="card" style="color: var(--accent-error)">Error: ${error.message}</div>`;
    } finally {
        morphSubmitBtn.classList.remove('loading');
    }
});

function renderMorphResults(data) {
    if (!data || data.length === 0) {
        morphResults.innerHTML = '<div class="card">No results found.</div>';
        return;
    }

    // Grid of word cards
    const grid = document.createElement('div');
    grid.style.display = 'grid';
    grid.style.gridTemplateColumns = 'repeat(auto-fill, minmax(300px, 1fr))';
    grid.style.gap = '1rem';
    morphResults.appendChild(grid);

    data.forEach(item => {
        const card = document.createElement('div');
        card.className = 'card';
        card.style.margin = '0';
        
        card.innerHTML = `
            <div style="display: flex; justify-content: space-between; align-items: start; margin-bottom: 1rem;">
                <h3 style="font-size: 1.25rem; font-weight: 700; color: var(--text-main);">${item.wordForm}</h3>
                <span style="font-size: 0.75rem; padding: 0.25rem 0.5rem; border-radius: 9999px; background: ${item.found ? 'rgba(16, 185, 129, 0.1)' : 'rgba(239, 68, 68, 0.1)'}; color: ${item.found ? 'var(--accent-success)' : 'var(--accent-error)'}; border: 1px solid ${item.found ? 'var(--accent-success)' : 'var(--accent-error)'};">
                    ${item.found ? 'Found' : 'Unknown'}
                </span>
            </div>
            <div style="color: var(--text-muted); font-size: 0.875rem; margin-bottom: 1rem;">
                ${item.commonGrammems || item.morphInfo || 'No grammatical info'}
            </div>
        `;

        if (item.paradigm && item.paradigm.length > 0) {
            const pBtn = document.createElement('button');
            pBtn.className = 'nav-link';
            pBtn.style.padding = '0.5rem';
            pBtn.style.width = '100%';
            pBtn.style.justifyContent = 'center';
            pBtn.style.fontSize = '0.75rem';
            pBtn.innerHTML = '<i class="fas fa-list"></i> View Full Paradigm';
            
            const pContent = document.createElement('div');
            pContent.style.display = 'none';
            pContent.style.marginTop = '1rem';
            pContent.style.maxHeight = '200px';
            pContent.style.overflowY = 'auto';
            pContent.style.fontSize = '0.8rem';
            pContent.style.background = 'rgba(0,0,0,0.2)';
            pContent.style.padding = '0.5rem';
            pContent.style.borderRadius = '0.5rem';

            let formsHtml = '';
            item.paradigm.forEach(p => {
                p.formsGroups.forEach(group => {
                    group.forms.forEach(form => {
                        formsHtml += `<div style="padding: 0.25rem 0; border-bottom: 1px solid var(--border-color); display: flex; justify-content: space-between;">
                            <span style="font-weight: 600;">${form.f}</span>
                            <span style="color: var(--text-muted); font-size: 0.7rem;">${form.grm}</span>
                        </div>`;
                    });
                });
            });
            pContent.innerHTML = formsHtml;

            pBtn.onclick = () => {
                pContent.style.display = pContent.style.display === 'none' ? 'block' : 'none';
            };

            card.appendChild(pBtn);
            card.appendChild(pContent);
        }

        grid.appendChild(card);
    });
}

// Syntax logic
const syntaxInput = document.getElementById('syntaxInput');
const syntaxSubmitBtn = document.getElementById('syntaxSubmitBtn');
const syntaxLangua = document.getElementById('syntaxLangua');
const visualizer = new SyntaxVisualizer('synanCanvas', 'syntaxCanvasWrapper');

syntaxSubmitBtn.addEventListener('click', async () => {
    const text = syntaxInput.value.trim();
    if (!text) return;

    const langua = syntaxLangua.value;

    syntaxSubmitBtn.classList.add('loading');
    visualizer.clear();

    try {
        const url = `${SynanDaemonUrl}&action=syntax&langua=${langua}&query=${encodeURIComponent(text)}`;
        const response = await fetch(url);
        const data = await response.json();
        
        console.log('Syntax Data:', data);

        // Normalize data structure: the API returns [[clause1, clause2, ...]]
        let clauses = [];
        if (Array.isArray(data)) {
            if (Array.isArray(data[0])) {
                clauses = data[0];
            } else {
                clauses = data;
            }
        }

        if (clauses.length === 0) {
            alert('No syntactic structure found for this sentence.');
            return;
        }

        visualizer.draw({ clauses });
    } catch (error) {
        console.error('Syntax request failed:', error);
        alert('Error: ' + error.message);
    } finally {
        syntaxSubmitBtn.classList.remove('loading');
    }
});

import json
import os
import sys
import re
from collections import defaultdict

# Mapping UniMorph/AGID English POS to AOT Latin POS names
POS_MAP = {
    'N': 'NOUN', 'V': 'VERB', 'ADJ': 'ADJECTIVE', 'ADV': 'ADVERB',
    'A': 'ADJECTIVE', 'AV': 'ADJECTIVE',
    'NOUN': 'NOUN', 'VERB': 'VERB', 'ADJECTIVE': 'ADJECTIVE', 'ADVERB': 'ADVERB',
}

# Mapping tags
TAG_MAP = {'PL': 'pl', 'SG': 'sg', 'PRS': 'prsa', 'PST': 'pasa', '3': '3', 'CMPR': 'comp', 'SPRL': 'sup', 'NFIN': 'inf'}

def get_stem(lemma, forms):
    if not forms: return lemma
    stem = lemma
    for word, tags in forms:
        while not word.startswith(stem) and stem: stem = stem[:-1]
    return stem

def clean_text(t):
    allowed = "ABCDEFGHIJKLMNOPQRSTUVWXYZ-'"
    t = t.upper().strip()
    t = re.sub(r'[!?~<>\s123]+$', '', t)
    if all(c in allowed for c in t): return t
    return None

def convert():
    data = defaultdict(lambda: defaultdict(list))
    high_freq = set()
    if os.path.exists('high_freq_lemmas.txt'):
        with open('high_freq_lemmas.txt', 'r') as f:
            high_freq = {line.strip() for line in f}
    
    # 1. Load AGID (only high freq)
    print("Loading AGID...")
    with open('Dicts/Morph/English/agid-infl.txt', 'r', encoding='utf-8', errors='replace') as f:
        for line in f:
            line = line.strip()
            if not line or line.startswith("#"): continue
            m = re.match(r'^(\S+)\s+([A-Z]+)\??\s*:\s*(.+)$', line)
            if not m: continue
            lemma, pos_raw, forms_str = clean_text(m.group(1)), m.group(2), m.group(3)
            if not lemma or lemma not in high_freq: continue
            aot_pos = POS_MAP.get(pos_raw, 'NOUN')
            data[lemma][aot_pos].append((lemma, ()))
            slots = [s.strip() for s in forms_str.split('|')]
            for i, slot in enumerate(slots):
                for f_part in slot.split(','):
                    f = clean_text(f_part)
                    if not f: continue
                    tags = []
                    if pos_raw == 'V':
                        mapping = {0: ('PST',), 1: ('PRS', 'V.PTCP'), 2: ('PRS', '3', 'SG')} if len(slots)==3 else {0: ('PST',), 1: ('PST', 'V.PTCP'), 2: ('PRS', 'V.PTCP'), 3: ('PRS', '3', 'SG')}
                        tags = mapping.get(i, ())
                    data[lemma][aot_pos].append((f, tags))

    # 2. Load UniMorph (only high freq, skip buggy rin/run)
    print("Loading UniMorph...")
    with open('Dicts/Morph/English/unimorph/eng', 'r', encoding='utf-8') as f:
        for line in f:
            parts = line.strip().split('\t')
            if len(parts) < 3: continue
            lemma, word, tags = clean_text(parts[0]), clean_text(parts[1]), parts[2].split(';')
            if not lemma or not word or lemma not in high_freq: continue
            if lemma == 'RIN' and word in ('RUN', 'RUNS', 'RAN', 'RUNNING'): continue
            data[lemma][POS_MAP.get(tags[0], 'NOUN')].append((word, tuple(tags[1:])))

    # 3. Convert to AOT
    gramtab = {"gramcodes": {}}
    gram_to_code = {}
    next_code_idx = 0
    
    def get_gramcode(pos, tags):
        nonlocal next_code_idx
        aot_pos = POS_MAP.get(pos, 'NOUN')
        aot_tags = []
        if 'V.PTCP' in tags:
            if 'PRS' in tags: aot_tags.append('ing')
            if 'PST' in tags: aot_tags.append('pp')
        else:
            for t in tags: aot_tags.append(TAG_MAP.get(t, t))
        if aot_pos == 'NOUN' and 'pl' not in aot_tags and 'sg' not in aot_tags: aot_tags.append('sg')
        
        key = (aot_pos, tuple(sorted(list(set(aot_tags)))))
        if key not in gram_to_code:
            c1, c2 = chr(ord('a') + (next_code_idx // 26)), chr(ord('a') + (next_code_idx % 26))
            gram_to_code[key] = c1 + c2
            gramtab["gramcodes"][c1 + c2] = {"p": aot_pos, "g": list(key[1]), "l": ""}
            next_code_idx += 1
        return gram_to_code[key]

    flexia_models = []
    paradigm_to_id = {}
    lemmas_list = []
    
    for lemma, pos_data in sorted(data.items()):
        for pos, forms in pos_data.items():
            unique_forms = {}
            for w, t in forms:
                gc = get_gramcode(pos, t)
                if w not in unique_forms or unique_forms[w] != gc:
                    unique_forms[w] = gc
            
            sorted_forms = sorted(unique_forms.items())
            stem = get_stem(lemma, sorted_forms)
            paradigm = []
            for w, gcode in sorted_forms:
                paradigm.append({"flexia": w[len(stem):], "gramcode": gcode})
            
            p_key = json.dumps(paradigm, sort_keys=True)
            if p_key not in paradigm_to_id:
                p_id = len(flexia_models)
                paradigm_to_id[p_key] = p_id
                flexia_models.append({"endings": paradigm})
            else:
                p_id = paradigm_to_id[p_key]
            
            lemmas_list.append({"l": lemma, "f": p_id, "a": 0, "s": 0})
            
    gramtab["plug_noun_gram_code"] = next(k for k, v in gramtab["gramcodes"].items() if v['p'] == 'NOUN')
    with open('Dicts/Morph/English/morphs.json', 'w', encoding='utf-8') as f: json.dump({"flexia_models": flexia_models, "accent_models": [[]], "sessions": [], "prefix_sets": [], "lemmas": lemmas_list}, f, indent=1)
    with open('Dicts/Morph/English/gramtab.json', 'w', encoding='utf-8') as f: json.dump(gramtab, f, indent=1)

if __name__ == "__main__": convert()

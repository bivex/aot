import json
import os
import sys
import re
from collections import defaultdict

# Mapping UniMorph/AGID English POS to AOT Latin POS names
POS_MAP = {
    'N': 'NOUN',
    'V': 'VERB',
    'ADJ': 'ADJECTIVE',
    'ADV': 'ADVERB',
    'A': 'ADJECTIVE',
    'AV': 'ADJECTIVE',
    'NOUN': 'NOUN',
    'VERB': 'VERB',
    'ADJECTIVE': 'ADJECTIVE',
    'ADVERB': 'ADVERB',
    'PREP': 'PREP',
    'CONJ': 'CONJ',
    'PART': 'PART',
    'INT': 'INT',
    'ART': 'ARTICLE',
    'ARTICLE': 'ARTICLE',
    'PRON': 'PRON',
    'PN': 'PN',
    'ORDNUM': 'ORDNUM',
    'VBE': 'VBE',
    'MOD': 'MOD',
    'POSS': 'POSS',
    'PN_ADJ': 'PN_ADJ'
}

# Mapping UniMorph tags to AOT English grammems
TAG_MAP = {
    'PL': 'pl',
    'SG': 'sg',
    'PRS': 'prsa',
    'PST': 'pasa',
    '3': '3',
    'CMPR': 'comp',
    'SPRL': 'sup',
    'NFIN': 'inf',
}

# POS-specific allowed tags to filter out noise
POS_ALLOWED_TAGS = {
    'NOUN': ['sg', 'pl', 'prop'],
    'VERB': ['inf', 'prsa', 'pasa', 'pp', 'ing', '3', '1', '2'],
    'VBE': ['inf', 'prsa', 'pasa', 'pp', 'ing', '3', '1', '2'],
    'ADJECTIVE': ['comp', 'sup'],
}

def get_stem(lemma, forms):
    """Find longest common prefix between lemma and all forms."""
    if not forms: return lemma, False
    stem = lemma
    for word, _ in forms:
        while not word.startswith(stem) and stem:
            stem = stem[:-1]
    is_irregular = len(stem) < 2
    return stem, is_irregular

def clean_text(t):
    # Allowed: A-Z, '-', "'"
    allowed = "ABCDEFGHIJKLMNOPQRSTUVWXYZ-'"
    t = t.upper().strip()
    # Strip trailing quality markers from AGID
    t = re.sub(r'[!?~<>\s123]+$', '', t)
    if all(c in allowed for c in t):
        return t
    return None

def get_gramcode(pos, tags, gram_to_code, gramtab, next_code_idx_ref):
    aot_pos = POS_MAP.get(pos, 'NOUN')
    aot_tags = []
    
    # Handle PTCP combinations
    if 'V.PTCP' in tags:
        if 'PRS' in tags: aot_tags.append('ing')
        if 'PST' in tags: aot_tags.append('pp')
    else:
        for t in tags:
            if t in TAG_MAP and TAG_MAP[t]:
                aot_tags.append(TAG_MAP[t])
    
    # Filter tags by POS
    if aot_pos in POS_ALLOWED_TAGS:
        allowed = POS_ALLOWED_TAGS[aot_pos]
        aot_tags = [t for t in aot_tags if t in allowed]
    else:
        aot_tags = []
    
    # Special case for nouns: ensure sg/pl
    if aot_pos == 'NOUN' and 'pl' not in aot_tags and 'sg' not in aot_tags:
        aot_tags.append('sg')
            
    key = (aot_pos, tuple(sorted(list(set(aot_tags)))))
    if key not in gram_to_code:
        idx = next_code_idx_ref[0]
        if idx >= 676:
            code = f"x{idx}"
        else:
            c1 = chr(ord('a') + (idx // 26))
            c2 = chr(ord('a') + (idx % 26))
            code = c1 + c2
        next_code_idx_ref[0] += 1
        gram_to_code[key] = code
        gramtab["gramcodes"][code] = {
            "p": aot_pos,
            "g": list(key[1]),
            "l": "" 
        }
    return gram_to_code[key]

CLOSED_CLASS_VERBS = {
    ('BE', 'VBE'): [
        ('BE', ('NFIN',)),
        ('AM', ('PRS', '1', 'SG')),
        ('IS', ('PRS', '3', 'SG')),
        ('ARE', ('PRS', 'PL')),
        ('WAS', ('PST', 'SG')),
        ('WERE', ('PST', 'PL')),
        ('BEEN', ('PST;V.PTCP',)),
        ('BEING', ('PRS;V.PTCP',)),
    ],
    ('HAVE', 'VBE'): [
        ('HAVE', ('PRS',)),
        ('HAS', ('PRS', '3', 'SG')),
        ('HAD', ('PST',)),
        ('HAVING', ('PRS;V.PTCP',)),
    ],
    ('DO', 'VBE'): [
        ('DO', ('PRS',)),
        ('DOES', ('PRS', '3', 'SG')),
        ('DID', ('PST',)),
        ('DONE', ('PST;V.PTCP',)),
        ('DOING', ('PRS;V.PTCP',)),
    ],
}

CLOSED_CLASS_PARTICLES = {
    ('NOT', 'PART'): [('NOT', ())],
    ('NEVER', 'PART'): [('NEVER', ())],
}

def load_agid(path, lemmas_data):
    if not os.path.exists(path):
        print(f"AGID file not found at {path}")
        return
    print(f"Loading AGID from {path}...")
    with open(path, 'r', encoding='utf-8', errors='replace') as f:
        for line in f:
            line = line.strip()
            if not line or line.startswith("#"): continue
            m = re.match(r'^(\S+)\s+([A-Z]+)\??\s*:\s*(.+)$', line)
            if not m: continue
            lemma_raw, pos_raw, forms_str = m.group(1), m.group(2), m.group(3)
            lemma = clean_text(lemma_raw)
            if not lemma: continue
            aot_pos = POS_MAP.get(pos_raw, 'NOUN')
            key = (lemma, aot_pos)
            if key not in lemmas_data: lemmas_data[key] = set()
            
            # Base form
            lemmas_data[key].add((lemma, ()))
            
            slots = [s.strip() for s in forms_str.split('|')]
            for i, slot in enumerate(slots):
                forms = [clean_text(f.strip()) for f in slot.split(',')]
                forms = [f for f in forms if f]
                
                tags = []
                if pos_raw == 'V':
                    if len(slots) == 4:
                        mapping = {0: ('PST',), 1: ('PST', 'V.PTCP'), 2: ('PRS', 'V.PTCP'), 3: ('PRS', '3', 'SG')}
                    else: # usually 3 slots
                        mapping = {0: ('PST',), 1: ('PRS', 'V.PTCP'), 2: ('PRS', '3', 'SG')}
                    tags = mapping.get(i, ())
                elif pos_raw in ('A', 'AV'):
                    mapping = {0: ('CMPR',), 1: ('SPRL',)}
                    tags = mapping.get(i, ())
                elif pos_raw == 'N':
                    tags = ('PL',)
                
                for f in forms:
                    lemmas_data[key].add((f, tags))

def convert():
    lemmas_data = {} 

    # 0. Inject closed-class
    for (lemma, aot_pos), forms in CLOSED_CLASS_VERBS.items():
        key = (lemma, aot_pos)
        lemmas_data[key] = set()
        for word, tags in forms:
            lemmas_data[key].add((word, tags))

    for (lemma, aot_pos), forms in CLOSED_CLASS_PARTICLES.items():
        key = (lemma, aot_pos)
        lemmas_data[key] = set()
        for word, tags in forms:
            lemmas_data[key].add((word, tags))

    # 1. Load original all.eng
    if os.path.exists('Dicts/SrcBinDict/all.eng'):
        print("Loading all.eng...")
        with open('Dicts/SrcBinDict/all.eng', 'r', encoding='latin-1') as f:
            for line in f:
                parts = line.strip().split('\t')
                if len(parts) < 2: continue
                pos = parts[0]
                lemma = clean_text(parts[1])
                if not lemma: continue
                aot_pos = POS_MAP.get(pos, pos)
                key = (lemma, aot_pos)
                if key not in lemmas_data:
                    lemmas_data[key] = set()
                lemmas_data[key].add((lemma, ()))

    # 2. Load AGID (prioritized)
    # load_agid('Dicts/Morph/English/agid-infl.txt', lemmas_data)

    # 3. Load UniMorph
    # print("Loading UniMorph...")
    # input_file = 'Dicts/Morph/English/unimorph/eng'
    # if os.path.exists(input_file):
    #     with open(input_file, 'r', encoding='utf-8') as f:
    #         for line in f:
    #             line = line.strip()
    #             if not line: continue
    #             parts = line.split('\t')
    #             if len(parts) < 3: continue
    #             
    #             lemma = clean_text(parts[0])
    #             word = clean_text(parts[1])
    #             if not lemma or not word: continue
    #             
    #             # Bug fix for rin -> run
    #             if lemma == 'RIN' and word in ('RUN', 'RUNS', 'RAN', 'RUNNING'):
    #                 continue
    #
    #             tags_raw = parts[2].split(';')
    #             pos = tags_raw[0]
    #             tags = tuple(tags_raw[1:])
    #             aot_pos = POS_MAP.get(pos, 'NOUN')
    #             
    #             key = (lemma, aot_pos)
    #             if key not in lemmas_data:
    #                 lemmas_data[key] = set()
    #             lemmas_data[key].add((word, tags))

    print("Processing paradigms...")
    gramtab = {"gramcodes": {}}
    gram_to_code = {}
    next_code_idx = [0]
    
    flexia_models = []
    paradigm_to_id = {}
    lemmas_list = []
    for (lemma, aot_pos), forms in sorted(lemmas_data.items()):
        current_pairs = set()
        for word, tags in forms:
            gcode = get_gramcode(aot_pos, tags, gram_to_code, gramtab, next_code_idx)
            current_pairs.add((word, gcode))

        # Convert to list and sort: (is_not_lemma, word, gcode)
        sorted_forms = sorted(list(current_pairs), key=lambda x: (x[0] != lemma, x[0], x[1]))

        stem, is_irregular = get_stem(lemma, sorted_forms)
        paradigm = []
        for w, gcode in sorted_forms:
            paradigm.append({
                "flexia": w[len(stem):] if len(w) >= len(stem) else w if not is_irregular else w,
                "gramcode": gcode
            })


        p_key = json.dumps(paradigm, sort_keys=True)
        if p_key not in paradigm_to_id:
            p_id = len(flexia_models)
            paradigm_to_id[p_key] = p_id
            flexia_models.append({"endings": paradigm})
        else:
            p_id = paradigm_to_id[p_key]

        if is_irregular:
            full_lemma = lemma
        else:
            first_flexia = paradigm[0]['flexia'] if paradigm else ''
            full_lemma = stem + first_flexia
        lemmas_list.append({
            "l": full_lemma,
            "f": p_id,
            "a": 0,
            "s": 0
        })
        
        for _, gcode in sorted_forms:
            if not gramtab["gramcodes"][gcode]["l"]:
                gramtab["gramcodes"][gcode]["l"] = full_lemma

    morphs = {
        "flexia_models": flexia_models,
        "accent_models": [[]],
        "sessions": [{"user": "guest", "start": "09.05.2026", "last_save": "09.05.2026"}],
        "prefix_sets": [],
        "lemmas": lemmas_list
    }
    
    print("Saving...")
    output_morphs = 'Dicts/Morph/English/morphs.json'
    output_gramtab = 'Dicts/Morph/English/gramtab.json'
    os.makedirs(os.path.dirname(output_morphs), exist_ok=True)
    with open(output_morphs, 'w', encoding='utf-8') as f:
        json.dump(morphs, f, ensure_ascii=False)
    with open(output_gramtab, 'w', encoding='utf-8') as f:
        json.dump(gramtab, f, ensure_ascii=False)
    
    print(f"Total unique gramcodes: {next_code_idx[0]}")
    print(f"Total flexia models: {len(flexia_models)}")
    print(f"Total lemmas: {len(lemmas_list)}")

if __name__ == "__main__":
    convert()

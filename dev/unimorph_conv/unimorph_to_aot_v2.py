import json
import os
import sys

# Mapping UniMorph English POS to AOT Latin POS names
POS_MAP = {
    'N': 'NOUN',
    'V': 'VERB',
    'ADJ': 'ADJECTIVE',
    'ADV': 'ADVERB',
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
    """Find longest common prefix between lemma and all forms.
    Returns (stem, is_irregular) where is_irregular=True if stem is empty
    or shorter than 2 chars (indicating suppletive paradigm like go/went)."""
    if not forms: return lemma, False
    stem = lemma
    for word, _ in forms:
        while not word.startswith(stem) and stem:
            stem = stem[:-1]
    is_irregular = len(stem) < 2
    return stem, is_irregular

def clean_text(t):
    # Filter out any character not in the allowed alphabet for English
    # Allowed: A-Z, '-', "'"
    allowed = "ABCDEFGHIJKLMNOPQRSTUVWXYZ-'"
    t = t.upper().strip()
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
        aot_tags = [] # Default for PREP, CONJ etc.
    
    # Special case for nouns: ensure sg/pl
    if aot_pos == 'NOUN' and 'pl' not in aot_tags and 'sg' not in aot_tags:
        aot_tags.append('sg')
            
    key = (aot_pos, tuple(sorted(list(set(aot_tags)))))
    if key not in gram_to_code:
        # Generate 2-letter gramcode (lowercase for English 'aa')
        idx = next_code_idx_ref[0]
        if idx >= 676:
            print(f"WARNING: gramcode space exhausted at {idx} entries", file=sys.stderr)
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

def convert():
    lemmas_data = {} # (lemma, aot_pos) -> set of (word, tags_tuple)
    
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

    # 2. Load UniMorph
    print("Loading UniMorph...")
    input_file = 'Dicts/Morph/English/unimorph/eng'
    with open(input_file, 'r', encoding='utf-8') as f:
        for line in f:
            line = line.strip()
            if not line: continue
            parts = line.split('\t')
            if len(parts) < 3: continue
            
            lemma = clean_text(parts[0])
            word = clean_text(parts[1])
            if not lemma or not word: continue
            
            tags_raw = parts[2].split(';')
            pos = tags_raw[0]
            tags = tuple(tags_raw[1:])
            aot_pos = POS_MAP.get(pos, 'NOUN')
            
            key = (lemma, aot_pos)
            if key not in lemmas_data:
                lemmas_data[key] = set()
            lemmas_data[key].add((word, tags))

    # 3. Process into AOT format
    print("Processing paradigms...")
    gramtab = {"gramcodes": {}}
    gram_to_code = {}
    next_code_idx = [0]
    
    flexia_models = []
    paradigm_to_id = {}
    lemmas_list = []
    
    # Sort to ensure stable output
    for (lemma, aot_pos), forms in sorted(lemmas_data.items()):
        current_forms_processed = []
        for word, tags in forms:
            gcode = get_gramcode(aot_pos, tags, gram_to_code, gramtab, next_code_idx)
            current_forms_processed.append((word, gcode))
        
        # Ensure the first form is the lemma if possible
        current_forms_processed.sort(key=lambda x: (x[0] != lemma, x[0]))

        stem, is_irregular = get_stem(lemma, current_forms_processed)
        paradigm = []
        for w, gcode in current_forms_processed:
            paradigm.append({
                "flexia": w[len(stem):] if not is_irregular else w,
                "gramcode": gcode
            })

        p_key = json.dumps(paradigm, sort_keys=True)
        if p_key not in paradigm_to_id:
            p_id = len(flexia_models)
            paradigm_to_id[p_key] = p_id
            flexia_models.append({"endings": paradigm})
        else:
            p_id = paradigm_to_id[p_key]

        # For irregular paradigms, stem is the lemma itself with empty prefix
        # For regular paradigms, reconstruct lemma from stem + first flexia
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
        
        # Update representative lemma in gramtab
        for _, gcode in current_forms_processed:
            if not gramtab["gramcodes"][gcode]["l"]:
                gramtab["gramcodes"][gcode]["l"] = full_lemma

    # Finalize plug noun
    plug_code = None
    for code, info in gramtab["gramcodes"].items():
        if info["p"] == "NOUN" and "sg" in info["g"]:
            plug_code = code
            if not info["l"]: info["l"] = "CAT"
            break
    if not plug_code:
        plug_code = list(gramtab["gramcodes"].keys())[0]
    gramtab["plug_noun_gram_code"] = plug_code

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
        json.dump(morphs, f, ensure_ascii=False, indent=1)
    with open(output_gramtab, 'w', encoding='utf-8') as f:
        json.dump(gramtab, f, ensure_ascii=False, indent=1)
    
    print(f"Total unique gramcodes: {next_code_idx[0]}")
    print(f"Total flexia models: {len(flexia_models)}")
    print(f"Total lemmas: {len(lemmas_list)}")

if __name__ == "__main__":
    convert()

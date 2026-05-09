import json
import os
import sys

# Mapping UniMorph English POS to AOT Latin POS names
POS_MAP = {
    'N': 'NOUN',
    'V': 'VERB',
    'ADJ': 'ADJECTIVE',
    'ADV': 'ADVERB',
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

def get_stem(lemma, forms):
    if not forms: return lemma
    stem = lemma
    for word, tags in forms:
        while not word.startswith(stem) and stem:
            stem = stem[:-1]
    return stem

def convert():
    input_file = 'Dicts/Morph/English/unimorph/eng'
    output_morphs = 'Dicts/Morph/English/morphs.json'
    output_gramtab = 'Dicts/Morph/English/gramtab.json'
    
    gramtab = {"gramcodes": {}}
    gram_to_code = {}
    next_code_idx = 0
    
    def get_gramcode(pos, tags, lemma=None):
        nonlocal next_code_idx
        aot_pos = POS_MAP.get(pos, 'NOUN')
        aot_tags = []
        
        # Handle PTCP combinations
        if 'V.PTCP' in tags:
            if 'PRS' in tags: aot_tags.append('ing')
            if 'PST' in tags: aot_tags.append('pp')
        else:
            for t in tags:
                if t in TAG_MAP:
                    aot_tags.append(TAG_MAP[t])
        
        # Special case for nouns: ensure sg/pl
        if aot_pos == 'NOUN' and 'pl' not in aot_tags and 'sg' not in aot_tags:
            aot_tags.append('sg')
            
        key = (aot_pos, tuple(sorted(list(set(aot_tags)))))
        if key not in gram_to_code:
            # Generate 2-letter gramcode (lowercase for English 'aa')
            c1 = chr(ord('a') + (next_code_idx // 26))
            c2 = chr(ord('a') + (next_code_idx % 26))
            code = c1 + c2
            next_code_idx += 1
            gram_to_code[key] = code
            gramtab["gramcodes"][code] = {
                "p": aot_pos,
                "g": list(key[1]),
                "l": lemma or "" 
            }
        return gram_to_code[key]

    flexia_models = []
    paradigm_to_id = {}
    lemmas_list = []
    
    current_lemma = None
    current_forms = []
    
    count = 0
    
    with open(input_file, 'r', encoding='utf-8') as f:
        for line in f:
            line = line.strip()
            if not line: continue
            
            parts = line.split('\t')
            if len(parts) < 3: continue
            
            lemma = parts[0].strip().upper()
            word = parts[1].strip().upper()
            
            def clean_text(t):
                # Filter out any character not in the allowed alphabet for English
                # Allowed: A-Z, '-', "'"
                allowed = "ABCDEFGHIJKLMNOPQRSTUVWXYZ-'"
                if all(c in allowed for c in t):
                    return t
                return None

            lemma = clean_text(lemma)
            word = clean_text(word)

            if not word or not lemma: continue
            
            tags_raw = parts[2].split(';')
            pos = tags_raw[0]
            tags = tags_raw[1:]
            
            if lemma != current_lemma:
                if current_lemma:
                    stem = get_stem(current_lemma, current_forms)
                    paradigm = []
                    for w, gcode in current_forms:
                        paradigm.append({
                            "flexia": w[len(stem):],
                            "gramcode": gcode
                        })
                    
                    p_key = json.dumps(paradigm, sort_keys=True)
                    if p_key not in paradigm_to_id:
                        p_id = len(flexia_models)
                        paradigm_to_id[p_key] = p_id
                        flexia_models.append({"endings": paradigm})
                    else:
                        p_id = paradigm_to_id[p_key]
                        
                    first_flexia = paradigm[0]['flexia'] if paradigm else ''
                    full_lemma = stem + first_flexia
                    lemmas_list.append({
                        "l": full_lemma,
                        "f": p_id,
                        "a": 0,
                        "s": 0
                    })
                
                current_lemma = lemma
                current_forms = []
            
            gcode = get_gramcode(pos, tags, lemma)
            current_forms.append((word, gcode))
            count += 1

    # Finalize last lemma
    if current_lemma:
        stem = get_stem(current_lemma, current_forms)
        paradigm = []
        for w, gcode in current_forms:
            paradigm.append({
                "flexia": w[len(stem):],
                "gramcode": gcode
            })
        p_key = json.dumps(paradigm, sort_keys=True)
        if p_key not in paradigm_to_id:
            p_id = len(flexia_models)
            flexia_models.append({"endings": paradigm})
        else:
            p_id = paradigm_to_id[p_key]
        first_flexia = paradigm[0]['flexia'] if paradigm else ''
        lemmas_list.append({
            "l": stem + first_flexia,
            "f": p_id,
            "a": 0,
            "s": 0
        })

    plug_code = None
    for code, info in gramtab["gramcodes"].items():
        if info["p"] == "NOUN" and "sg" in info["g"]:
            plug_code = code
            break
    
    if not plug_code:
        # Fallback to any noun or first available
        for code, info in gramtab["gramcodes"].items():
            if info["p"] == "NOUN":
                plug_code = code
                break
    
    if not plug_code:
        plug_code = list(gramtab["gramcodes"].keys())[0]

    gramtab["plug_noun_gram_code"] = plug_code

    morphs = {
        "flexia_models": flexia_models,
        "accent_models": [[]],
        "sessions": [{
            "user": "guest", 
            "start": "09.05.2026", 
            "last_save": "09.05.2026"
        }],
        "prefix_sets": [],
        "lemmas": lemmas_list
    }
    
    os.makedirs(os.path.dirname(output_morphs), exist_ok=True)
    with open(output_morphs, 'w', encoding='utf-8') as f:
        json.dump(morphs, f, ensure_ascii=False, indent=1)
        
    with open(output_gramtab, 'w', encoding='utf-8') as f:
        json.dump(gramtab, f, ensure_ascii=False, indent=1)
    
    print(f"Converted {count} forms. Created {len(flexia_models)} flexia models and {len(lemmas_list)} lemmas.")

if __name__ == "__main__":
    convert()

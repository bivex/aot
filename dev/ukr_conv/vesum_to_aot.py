import json
import os
import sys

# Mapping VESUM POS to AOT CRusGramTab Latin names
POS_MAP = {
    'noun': 'N',
    'adj': 'A',
    'verb': 'V',
    'adv': 'ADV',
    'pron': 'PRON',
    'num': 'NUM',
    'prep': 'PREP',
    'conj': 'CONJ',
    'part': 'PARTICLE',
    'intj': 'INT',
}

# Mapping VESUM tags to AOT CRusGramTab Latin grammems
TAG_MAP = {
    'm': 'mas',
    'f': 'fem',
    'n': 'neu',
    'p': 'pl', 
    's': 'sg', 
    'v_naz': 'nom',
    'v_rod': 'gen',
    'v_dav': 'dat',
    'v_zna': 'acc',
    'v_oru': 'ins',
    'v_mis': 'loc', 
    'v_kly': 'voc',
    'anim': 'anim',
    'inanim': 'inanim',
    'perf': 'perf',
    'imp': 'imp',
}

def get_stem(lemma, forms):
    if not forms: return lemma
    stem = lemma
    for word, tags in forms:
        while not word.startswith(stem) and stem:
            stem = stem[:-1]
    return stem

def convert():
    input_file = 'Source/dict_uk/out/dict_corp_lt.txt'
    output_morphs = 'Source/morph_dict/data/Ukrainian/morphs.json'
    output_gramtab = 'Source/morph_dict/data/Ukrainian/gramtab.json'
    
    gramtab = {"gramcodes": {}}
    gram_to_code = {}
    next_code_idx = 0
    
    def get_gramcode(pos, tags, lemma=None):
        nonlocal next_code_idx
        aot_pos = POS_MAP.get(pos, 'N')
        aot_tags = []
        for t in tags:
            if t in TAG_MAP:
                aot_tags.append(TAG_MAP[t])
        
        if aot_pos in ['N', 'A'] and 'pl' not in aot_tags:
            aot_tags.append('sg')
            
        key = (aot_pos, tuple(sorted(aot_tags)))
        if key not in gram_to_code:
            c1 = chr(ord('A') + (next_code_idx // 26))
            c2 = chr(ord('A') + (next_code_idx % 26))
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
    max_lines = 100000 
    
    with open(input_file, 'r', encoding='utf-8') as f:
        for line in f:
            count += 1
            if count > max_lines: break
            
            parts = line.strip().split(' ')
            if len(parts) < 3: continue
            
            word = parts[0].upper()
            lemma = parts[1].upper()
            
            # Unify apostrophes and filter invalid characters
            def clean_text(t):
                # Replace various apostrophes with the standard one
                t = t.replace('’', "'").replace('ʼ', "'").replace('`', "'")
                # Filter out any character not in the allowed alphabet
                # Allowed: А-Я, Ґ, Є, І, Ї, '-', "'"
                allowed = "АБВГҐДЕЄЖЗИІЇЙКЛМНОПРСТУФХЦЧШЩЬЮЯ-'"
                return "".join(c for c in t if c in allowed)

            word = clean_text(word)
            lemma = clean_text(lemma)

            if not word or not lemma: continue
            
            tags_raw = parts[2].split(':')
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
                        
                    lemmas_list.append({
                        "l": stem,
                        "f": p_id,
                        "a": 0,
                        "s": 0 
                    })
                
                current_lemma = lemma
                current_forms = []
            
            gcode = get_gramcode(pos, tags, lemma)
            current_forms.append((word, gcode))

    plug_code = None
    for code, info in gramtab["gramcodes"].items():
        if info["p"] == "N" and info["l"]:
            plug_code = code
            break
    
    if not plug_code:
        plug_code = list(gramtab["gramcodes"].keys())[0]
        gramtab["gramcodes"][plug_code]["l"] = "DUMMY"

    gramtab["plug_noun_gram_code"] = plug_code

    morphs = {
        "flexia_models": flexia_models,
        "accent_models": [[]], # Correct format: array of arrays
        "sessions": [{
            "user": "guest", 
            "start": "06.05.2026", 
            "last_save": "06.05.2026"
        }],
        "prefix_sets": [],
        "lemmas": lemmas_list
    }
    
    os.makedirs(os.path.dirname(output_morphs), exist_ok=True)
    with open(output_morphs, 'w', encoding='utf-8') as f:
        json.dump(morphs, f, ensure_ascii=False, indent=1)
        
    with open(output_gramtab, 'w', encoding='utf-8') as f:
        json.dump(gramtab, f, ensure_ascii=False, indent=1)
    
    print(f"Converted {count} lines. Created {len(flexia_models)} flexia models and {len(lemmas_list)} lemmas.")

if __name__ == "__main__":
    convert()

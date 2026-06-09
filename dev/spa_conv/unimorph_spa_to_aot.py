import json
import os
import sys
import unicodedata
from collections import defaultdict
from datetime import datetime

def strip_accents(text):
    nfkd = unicodedata.normalize('NFKD', text)
    return ''.join(c for c in nfkd if not unicodedata.combining(c))

POS_MAP = {
    'N': 'NOUN',
    'V': 'VERB',
    'ADJ': 'ADJ',
    'ADV': 'ADV',
    'DET': 'DET',
    'PRON': 'PRON',
    'PREP': 'PREP',
    'CONJ': 'CONJ',
    'INTJ': 'INT',
    'NUM': 'NUM',
}

TAG_MAP = {
    # number
    'SG': 'sg', 'PL': 'pl',
    # gender
    'MASC': 'masc', 'FEM': 'fem', 'NEUT': 'neut',
    # case
    'NOM': 'nom', 'ACC': 'acc', 'DAT': 'dat', 'GEN': 'gen', 'VOC': 'voc',
    # tense
    'PRS': 'pres', 'PST': 'past', 'FUT': 'fut', 'IPFV': 'impf', 'PFV': 'pfv',
    'COND': 'cond',
    # mood
    'IND': 'ind', 'SBJV': 'sbjv', 'IMP': 'impv',
    # person
    '1': 'p1', '2': 'p2', '3': 'p3',
    # degree
    'CMPR': 'comp', 'SPRL': 'sup', 'POS': 'pos',
    # politeness
    'FORM': 'form', 'INFM': 'infm',
    # negation
    'NEG': 'neg',
    # other
    'PRO': 'pro',
}

# Tags to skip (not useful for morphology)
SKIP_TAGS = {'LGSPEC1', 'LGSPEC2', 'NFIN', 'V.CVB', 'V.PTCP',
             'MASC+FEM', 'FEM+MASC', 'MASC+MASC'}

def get_stem(lemma, forms):
    if not forms:
        return lemma
    stem = lemma
    for word in forms:
        while not word.startswith(stem) and stem:
            stem = stem[:-1]
    return stem


def convert():
    input_file = 'Dicts/Morph/Spanish/unimorph/spa'
    output_morphs = 'Source/morph_dict/data/Spanish/morphs.json'
    output_gramtab = 'Source/morph_dict/data/Spanish/gramtab.json'

    gramtab = {"gramcodes": {}}
    gram_to_code = {}
    next_code_idx = 0

    def get_gramcode(pos, tags, lemma=None):
        nonlocal next_code_idx
        aot_pos = POS_MAP.get(pos)
        if not aot_pos:
            return None

        aot_tags = []
        has_ptcp = 'V.PTCP' in tags
        has_ger = 'V.CVB' in tags

        if has_ptcp:
            aot_tags.append('ptcp')
        if has_ger:
            aot_tags.append('ger')

        for t in tags:
            if t in SKIP_TAGS:
                continue
            if t in TAG_MAP:
                aot_tags.append(TAG_MAP[t])

        # defaults
        if aot_pos == 'NOUN':
            if 'sg' not in aot_tags and 'pl' not in aot_tags:
                aot_tags.append('sg')
            if 'masc' not in aot_tags and 'fem' not in aot_tags:
                aot_tags.append('masc')

        if aot_pos == 'ADJ':
            if 'sg' not in aot_tags and 'pl' not in aot_tags:
                aot_tags.append('sg')

        key = (aot_pos, tuple(sorted(set(aot_tags))))
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

    # Group by (lemma, pos) to collect full paradigm
    data = defaultdict(lambda: defaultdict(list))  # lemma -> pos -> [(word, tags_raw)]

    print(f"Reading {input_file}...")
    total_lines = 0
    skipped = 0
    with open(input_file, 'r', encoding='utf-8') as f:
        for line in f:
            total_lines += 1
            line = line.strip()
            if not line:
                continue
            parts = line.split('\t')
            if len(parts) < 3:
                continue

            lemma_raw = parts[0].strip().upper()
            word_raw = parts[1].strip().upper()

            # Spanish: allow A-Z, accented chars, ñ, ü, -
            def clean_text(t):
                allowed = "ABCDEFGHIJKLMNOPQRSTUVWXYZ"
                t2 = ''.join(c for c in t if c in allowed)
                return t2 if t2 else None

            lemma_clean = clean_text(lemma_raw)
            word_clean = clean_text(word_raw)
            if not lemma_clean or not word_clean:
                skipped += 1
                continue

            lemma = strip_accents(lemma_clean)
            word = strip_accents(word_clean)

            tags_raw = parts[2].split(';')
            pos = tags_raw[0]
            if pos not in POS_MAP:
                skipped += 1
                continue

            data[lemma][pos].append((word, tags_raw))

    print(f"Read {total_lines} lines, {len(data)} lemmas, skipped {skipped}")

    flexia_models = []
    paradigm_to_id = {}
    lemmas_list = []
    today = datetime.now().strftime("%d.%m.%Y")

    count = 0
    for lemma in sorted(data.keys()):
        for pos in data[lemma]:
            forms = data[lemma][pos]
            if not forms:
                continue

            # Build (word, gramcode) pairs
            word_codes = []
            for word, tags_raw in forms:
                tags = tags_raw[1:]
                gcode = get_gramcode(pos, tags, lemma)
                if gcode:
                    word_codes.append((word, gcode))

            if not word_codes:
                continue

            # Deduplicate same (word, gramcode) pairs
            seen = set()
            unique_wc = []
            for wc in word_codes:
                if wc not in seen:
                    seen.add(wc)
                    unique_wc.append(wc)
            word_codes = unique_wc

            stem = get_stem(lemma, [w for w, _ in word_codes])

            paradigm = []
            for w, gcode in word_codes:
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
            lemmas_list.append({
                "l": stem + first_flexia,
                "f": p_id,
                "a": 0,
                "s": 0
            })
            count += len(word_codes)

    # Find plug_noun_gram_code
    plug_code = None
    for code, info in gramtab["gramcodes"].items():
        if info["p"] == "NOUN" and "sg" in info["g"] and "masc" in info["g"]:
            plug_code = code
            break
    if not plug_code:
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
        "sessions": [{"user": "guest", "start": today, "last_save": today}],
        "prefix_sets": [],
        "lemmas": lemmas_list
    }

    os.makedirs(os.path.dirname(output_morphs), exist_ok=True)
    with open(output_morphs, 'w', encoding='utf-8') as f:
        json.dump(morphs, f, ensure_ascii=False, indent=1)

    with open(output_gramtab, 'w', encoding='utf-8') as f:
        json.dump(gramtab, f, ensure_ascii=False, indent=1)

    print(f"Wrote {output_morphs}: {len(flexia_models)} flexia models, {len(lemmas_list)} lemmas, {count} total forms")
    print(f"Wrote {output_gramtab}: {len(gramtab['gramcodes'])} gramcodes")


if __name__ == "__main__":
    convert()

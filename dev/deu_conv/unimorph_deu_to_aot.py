import json
import os
import sys
import unicodedata
from collections import defaultdict
from datetime import datetime


def strip_accents(text):
    nfkd = unicodedata.normalize('NFKD', text)
    return ''.join(c for c in nfkd if not unicodedata.combining(c))


def strip_german_umlauts(text):
    return text.replace('Ä', 'AE').replace('Ö', 'OE').replace('Ü', 'UE') \
               .replace('ä', 'AE').replace('ö', 'OE').replace('ü', 'UE') \
               .replace('ß', 'SS')


POS_MAP = {
    'N': 'SUB',
    'V': 'VER',
    'ADJ': 'ADJ',
    'V.PTCP': 'VER',  # participles mapped to VER
}

TAG_MAP = {
    # number
    'SG': 'sin', 'PL': 'plu',
    # gender
    'MASC': 'mas', 'FEM': 'fem', 'NEUT': 'neu',
    # case
    'NOM': 'nom', 'GEN': 'gen', 'DAT': 'dat', 'ACC': 'akk',
    # tense
    'PRS': 'prae', 'PST': 'prt',
    # mood
    'IND': 'ind', 'SBJV': 'kj1', 'IMP': 'imp',
    # person
    '1': '1', '2': '2', '3': '3',
    # degree
    'CMPR': 'kom', 'SPRL': 'sup',
    # verb form
    'NFIN': 'eiz',
}

SKIP_TAGS = {'LGSPEC01', 'LGSPEC02'}

VERB_FORM_MAP = {
    'V': 'eiz',
    'V.PTCP;PRS': 'pa1',
    'V.PTCP;PST': 'pa2',
}


def get_stem(lemma, forms):
    if not forms:
        return lemma
    stem = lemma
    for word in forms:
        while not word.startswith(stem) and stem:
            stem = stem[:-1]
    return stem


def convert():
    input_file = 'Dicts/Morph/German/unimorph/deu'
    output_morphs = 'Source/morph_dict/data/German/morphs.json'
    output_gramtab = 'Source/morph_dict/data/German/gramtab.json'

    gramtab = {"gramcodes": {}}
    gram_to_code = {}
    next_code_idx = 0

    def get_gramcode(pos_raw, tags, is_ptcp_prs=False, is_ptcp_pst=False):
        nonlocal next_code_idx
        aot_pos = POS_MAP.get(pos_raw)
        if not aot_pos:
            return None

        aot_tags = []

        if is_ptcp_prs:
            aot_tags.append('pa1')
        if is_ptcp_pst:
            aot_tags.append('pa2')

        for t in tags:
            if t in SKIP_TAGS:
                continue
            if t in TAG_MAP:
                aot_tags.append(TAG_MAP[t])

        # strip duplicates while preserving order
        seen = set()
        unique_tags = []
        for t in aot_tags:
            if t not in seen:
                seen.add(t)
                unique_tags.append(t)
        aot_tags = unique_tags

        # defaults for nouns
        if aot_pos == 'SUB':
            if 'sin' not in aot_tags and 'plu' not in aot_tags:
                aot_tags.append('sin')
            if 'mas' not in aot_tags and 'fem' not in aot_tags and 'neu' not in aot_tags:
                aot_tags.append('mas')
            if 'nom' not in aot_tags and 'gen' not in aot_tags and 'dat' not in aot_tags and 'akk' not in aot_tags:
                aot_tags.append('nom')

        # defaults for adjectives
        if aot_pos == 'ADJ':
            if 'sin' not in aot_tags and 'plu' not in aot_tags:
                aot_tags.append('sin')
            if 'mas' not in aot_tags and 'fem' not in aot_tags and 'neu' not in aot_tags:
                aot_tags.append('mas')
            if 'nom' not in aot_tags and 'gen' not in aot_tags and 'dat' not in aot_tags and 'akk' not in aot_tags:
                aot_tags.append('nom')
            if 'gru' not in aot_tags and 'kom' not in aot_tags and 'sup' not in aot_tags:
                aot_tags.append('gru')

        # defaults for verbs
        if aot_pos == 'VER':
            if 'eiz' not in aot_tags and 'pa1' not in aot_tags and 'pa2' not in aot_tags \
               and 'prae' not in aot_tags and 'prt' not in aot_tags:
                aot_tags.append('eiz')

        key = (aot_pos, tuple(aot_tags))
        if key not in gram_to_code:
            c1 = chr(ord('A') + (next_code_idx // 26))
            c2 = chr(ord('A') + (next_code_idx % 26))
            code = c1 + c2
            next_code_idx += 1
            gram_to_code[key] = code
            gramtab["gramcodes"][code] = {
                "p": aot_pos,
                "g": list(key[1]),
            }
        return gram_to_code[key]

    # Group by (lemma, pos)
    data = defaultdict(lambda: defaultdict(list))

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

            lemma_raw = parts[0].strip()
            word_raw = parts[1].strip()

            # skip multi-word forms (separable verbs, compounds)
            if ' ' in lemma_raw or ' ' in word_raw:
                skipped += 1
                continue

            # convert umlauts then strip remaining accents, uppercase
            lemma_clean = strip_german_umlauts(lemma_raw).upper()
            word_clean = strip_german_umlauts(word_raw).upper()

            # keep only A-Z
            def clean_text(t):
                t2 = ''.join(c for c in t if c in 'ABCDEFGHIJKLMNOPQRSTUVWXYZ')
                return t2 if t2 else None

            lemma_final = clean_text(strip_accents(lemma_clean))
            word_final = clean_text(strip_accents(word_clean))
            if not lemma_final or not word_final:
                skipped += 1
                continue

            tags_raw = parts[2].split(';')
            pos_raw = tags_raw[0]
            rest_tags = tags_raw[1:]

            if pos_raw not in POS_MAP:
                skipped += 1
                continue

            data[lemma_final][pos_raw].append((word_final, rest_tags))

    print(f"Read {total_lines} lines, {len(data)} lemmas, skipped {skipped}")

    flexia_models = []
    paradigm_to_id = {}
    lemmas_list = []
    today = datetime.now().strftime("%d.%m.%Y")

    count = 0
    for lemma in sorted(data.keys()):
        for pos_raw in data[lemma]:
            forms = data[lemma][pos_raw]
            if not forms:
                continue

            word_codes = []
            for word, tags in forms:
                is_ptcp_prs = (pos_raw == 'V.PTCP' and 'PRS' in tags)
                is_ptcp_pst = (pos_raw == 'V.PTCP' and 'PST' in tags)
                effective_pos = 'V.PTCP' if pos_raw == 'V.PTCP' else pos_raw
                gcode = get_gramcode(effective_pos, tags, is_ptcp_prs, is_ptcp_pst)
                if gcode:
                    word_codes.append((word, gcode))

            if not word_codes:
                continue

            # deduplicate
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
                flexia = w[len(stem):]
                paradigm.append({
                    "flexia": flexia,
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

    # plug_noun_gram_code
    plug_code = None
    for code, info in gramtab["gramcodes"].items():
        if info["p"] == "SUB" and "sin" in info["g"] and "mas" in info["g"] and "nom" in info["g"]:
            plug_code = code
            break
    if not plug_code:
        for code, info in gramtab["gramcodes"].items():
            if info["p"] == "SUB":
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

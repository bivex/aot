import json
import os
import sys
import unicodedata
from collections import defaultdict
from datetime import datetime


POS_MAP = {
    'N': 'NOUN',
    'V': 'VERB',
    'V.PTCP': 'VERB',
    'ADJ': 'ADJ',
    'ADV': 'ADV',
    'PRON': 'PRON',
    'PREP': 'PREP',
    'ADP': 'ADP',
    'CONJ': 'CONJ',
    'INTJ': 'INT',
    'NUM': 'NUM',
    'PART': 'PART',
    'PROPN': 'PROPN',
}

TAG_MAP = {
    # number
    'SG': 'sg', 'PL': 'pl',
    # cases
    'NOM': 'nom', 'ACC': 'nom', 'GEN': 'gen', 'PRT': 'par',
    'IN+ESS': 'ine', 'IN+ABL': 'ela', 'IN+ALL': 'ill',
    'AT+ESS': 'ade', 'AT+ABL': 'abl', 'AT+ALL': 'all',
    'ESS': 'ess', 'TRA': 'tra', 'INS': 'ins', 'ABS': 'abs',
    'COM': 'com', 'FRML': 'tra', 'PRIV': 'abs', 'TRANS': 'tra',
    # tense
    'PRS': 'pres', 'PST': 'past',
    # mood
    'IND': 'ind', 'COND': 'cond', 'IMP': 'imp', 'POT': 'pot',
    # person (Finnish has no infinitive person; map 4th/5th inf as INF)
    '1': 'p1', '2': 'p2', '3': 'p3',
    # verb forms
    'NFIN': 'inf', 'INF': 'inf',
    # voice
    'PASS': 'pass', 'ACT': 'act', 'ACT+PASS': 'act',
    # polarity
    'POS': 'pos', 'NEG': 'neg',
    # aspect/perfect
    'PRF': 'prf',
    # possessive suffixes (skip — not in AOT gramtab)
    'PSS1S': None, 'PSS1P': None, 'PSS2S': None, 'PSS2P': None, 'PSS3': None,
    # AG = agent participle → map as active participle
    'AG': 'act',
}

SKIP_TAGS = {'LGSPEC1', 'LGSPEC2'}


def clean_finnish(text):
    t = text.upper()
    t = t.replace('Ä', 'A').replace('Ö', 'O').replace('Å', 'A')
    result = []
    for c in t:
        if c in 'ABCDEFGHIJKLMNOPQRSTUVWXYZ-':
            result.append(c)
    t2 = ''.join(result)
    return t2 if t2 else None


def get_stem(lemma, forms):
    if not forms:
        return lemma
    stem = lemma
    for word in forms:
        while not word.startswith(stem) and stem:
            stem = stem[:-1]
    return stem


def convert():
    input_files = [
        'Dicts/Morph/Finnish/unimorph/fin.1',
        'Dicts/Morph/Finnish/unimorph/fin.2',
    ]
    output_morphs = 'Source/morph_dict/data/Finnish/morphs.json'
    output_gramtab = 'Source/morph_dict/data/Finnish/gramtab.json'

    gramtab = {"gramcodes": {}}
    gram_to_code = {}
    next_code_idx = 0

    def get_gramcode(pos, tags, lemma=None):
        nonlocal next_code_idx

        # Determine AOT POS
        if pos == 'V.PTCP':
            aot_pos = 'VERB'
        else:
            aot_pos = POS_MAP.get(pos)
        if not aot_pos:
            return None

        aot_tags = []
        if pos == 'V.PTCP':
            aot_tags.append('ptcp')

        for t in tags:
            if t in SKIP_TAGS:
                continue
            mapped = TAG_MAP.get(t)
            if mapped is None:
                continue
            if mapped and mapped not in aot_tags:
                aot_tags.append(mapped)

        # Default number for nouns/adjs
        if aot_pos in ('NOUN', 'ADJ', 'PRON'):
            if 'sg' not in aot_tags and 'pl' not in aot_tags:
                aot_tags.append('sg')

        # Default voice for verbs
        if aot_pos == 'VERB' and 'pass' not in aot_tags and 'act' not in aot_tags:
            aot_tags.append('act')

        # Default mood for finite verbs
        if aot_pos == 'VERB' and 'ptcp' not in aot_tags and 'inf' not in aot_tags:
            if 'ind' not in aot_tags and 'cond' not in aot_tags and 'imp' not in aot_tags and 'pot' not in aot_tags:
                aot_tags.append('ind')

        # Default polarity
        if aot_pos == 'VERB' and 'pos' not in aot_tags and 'neg' not in aot_tags:
            aot_tags.append('pos')

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

    data = defaultdict(lambda: defaultdict(list))
    total_lines = 0
    skipped = 0
    multi_word = 0

    for input_file in input_files:
        print(f"Reading {input_file}...")
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

                # Skip multi-word forms (negative/perfect constructions with auxiliaries)
                if ' ' in word_raw:
                    multi_word += 1
                    continue

                lemma_clean = clean_finnish(lemma_raw)
                word_clean = clean_finnish(word_raw)
                if not lemma_clean or not word_clean:
                    skipped += 1
                    continue

                tags_raw = parts[2].split(';')
                pos = tags_raw[0]
                if pos not in POS_MAP:
                    skipped += 1
                    continue

                data[lemma_clean][pos].append((word_clean, tags_raw))

    print(f"Read {total_lines} lines, {len(data)} lemmas, skipped {skipped}, multi-word {multi_word}")

    # Auto-generate base forms if missing
    for lemma in list(data.keys()):
        for pos in list(data[lemma].keys()):
            forms = data[lemma][pos]
            words_in_forms = {w for w, _ in forms}
            if lemma not in words_in_forms:
                if pos in ('N', 'ADJ'):
                    tags = [pos, 'NOM', 'SG']
                elif pos == 'V':
                    tags = [pos, 'NFIN', 'ACT']
                elif pos == 'V.PTCP':
                    tags = [pos, 'ACT', 'PRS']
                else:
                    tags = [pos, 'SG']
                data[lemma][pos].append((lemma, tags))

    # Finnish closed-class words
    CLOSED_CLASS = {
        # Personal pronouns
        'MINA': ('PRON', ['p1', 'sg']),
        'SINA': ('PRON', ['p2', 'sg']),
        'HAN': ('PRON', ['p3', 'sg']),
        'ME': ('PRON', ['p1', 'pl']),
        'TE': ('PRON', ['p2', 'pl']),
        'HE': ('PRON', ['p3', 'pl']),
        # Demonstrative pronouns
        'TAMA': ('PRON', ['sg', 'nom']),
        'TAMAN': ('PRON', ['sg', 'gen']),
        'TASSA': ('PRON', ['sg', 'ine']),
        'TASTA': ('PRON', ['sg', 'ela']),
        'TAHAN': ('PRON', ['sg', 'ill']),
        'TALLA': ('PRON', ['sg', 'ade']),
        'TALTA': ('PRON', ['sg', 'abl']),
        'TALLE': ('PRON', ['sg', 'all']),
        'NAMA': ('PRON', ['pl', 'nom']),
        'NAMA': ('PRON', ['pl', 'nom']),
        'TUO': ('PRON', ['sg', 'nom']),
        'NUO': ('PRON', ['pl', 'nom']),
        'SE': ('PRON', ['sg', 'nom']),
        'NE': ('PRON', ['pl', 'nom']),
        # Interrogative
        'MIKA': ('PRON', ['sg', 'nom']),
        'KUKA': ('PRON', ['sg', 'nom']),
        'MISSA': ('ADV', []),
        'MIHIN': ('ADV', []),
        'MISTÄ': ('ADV', []),
        'MILLA': ('ADV', []),
        'MILLOIN': ('ADV', []),
        'MITEN': ('ADV', []),
        'MIKSI': ('ADV', []),
        # Common adverbs
        'EI': ('ADV', ['neg']),
        'KYLLA': ('ADV', []),
        'EI': ('PART', ['neg']),
        'KYL': ('PART', ['neg']),
        'MYOS': ('ADV', []),
        'VAIN': ('ADV', []),
        'JO': ('ADV', []),
        'MYOHEMIN': ('ADV', []),
        'AINA': ('ADV', []),
        'EI': ('PART', ['neg']),
        'ETA': ('CONJ', []),
        'JA': ('CONJ', []),
        'TAI': ('CONJ', []),
        'VAI': ('CONJ', []),
        'MUTTA': ('CONJ', []),
        'KOSKA': ('CONJ', []),
        'KUN': ('CONJ', []),
        'JOS': ('CONJ', []),
        'ETTA': ('CONJ', []),
        'VAIKKA': ('CONJ', []),
        'JOTTA': ('CONJ', []),
        'KOSKA': ('CONJ', []),
        # Prepositions/postpositions
        'YLI': ('ADP', []),
        'ALLA': ('ADP', []),
        'YLLA': ('ADP', []),
        'PAALLE': ('ADP', []),
        'JALKEEN': ('ADP', []),
        'KANSSA': ('ADP', []),
        'ILMAN': ('ADP', []),
        'KOHTI': ('ADP', []),
        'VIEREEN': ('ADP', []),
        # Numbers
        'YKSI': ('NUM', ['sg', 'nom']),
        'KAKSI': ('NUM', ['sg', 'nom']),
        'KOLME': ('NUM', ['sg', 'nom']),
        'NELJA': ('NUM', ['sg', 'nom']),
        'VIISI': ('NUM', ['sg', 'nom']),
        # Common nouns for testing
        'OIKEUS': ('NOUN', ['sg', 'nom']),
        'LAKI': ('NOUN', ['sg', 'nom']),
        'TUOMIO': ('NOUN', ['sg', 'nom']),
        'SOPIMUS': ('NOUN', ['sg', 'nom']),
        'VIRANOMAINEN': ('NOUN', ['sg', 'nom']),
    }

    for word, (pos, tags) in CLOSED_CLASS.items():
        word_clean = clean_finnish(word)
        if word_clean:
            data[word_clean][pos].append((word_clean, [pos] + tags))

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

            word_codes = []
            for word, tags_raw in forms:
                tags = tags_raw[1:]
                gcode = get_gramcode(pos, tags, lemma)
                if gcode:
                    word_codes.append((word, gcode))

            if not word_codes:
                continue

            seen = set()
            unique_wc = []
            for wc in word_codes:
                if wc not in seen:
                    seen.add(wc)
                    unique_wc.append(wc)
            word_codes = unique_wc

            stem = get_stem(lemma, [w for w, _ in word_codes])
            if not stem:
                stem = lemma

            paradigm = []
            for w, gcode in word_codes:
                flex = w[len(stem):] if w.startswith(stem) else w
                paradigm.append({
                    "flexia": flex,
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

    plug_code = None
    for code, info in gramtab["gramcodes"].items():
        if info["p"] == "NOUN" and "sg" in info["g"] and "nom" in info["g"]:
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

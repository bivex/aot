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
    'NOM': 'nom', 'ACC': 'acc', 'DAT': 'dat', 'GEN': 'gen',
    # tense
    'PRS': 'pres', 'PST': 'past', 'FUT': 'fut', 'IPFV': 'impf', 'PFV': 'pfv',
    'COND': 'cond',
    # mood
    'IND': 'ind', 'SBJV': 'sbjv', 'IMP': 'impv',
    # person
    '1': 'p1', '2': 'p2', '3': 'p3',
    # verb forms
    'INF': 'inf', 'GER': 'ger', 'PTCP': 'ptcp',
    # degree
    'CMPR': 'comp', 'SPRL': 'sup', 'POS': 'pos',
    # other
    'PRO': 'pro',
}

SKIP_TAGS = {'LGSPEC1', 'LGSPEC2', 'NFIN', 'V.CVB', 'V.PTCP',
             'MASC+FEM', 'FEM+MASC'}

def get_stem(lemma, forms):
    if not forms:
        return lemma
    stem = lemma
    for word in forms:
        while not word.startswith(stem) and stem:
            stem = stem[:-1]
    return stem


def convert():
    input_file = 'Dicts/Morph/Portuguese/unimorph/por'
    output_morphs = 'Source/morph_dict/data/Portuguese/morphs.json'
    output_gramtab = 'Source/morph_dict/data/Portuguese/gramtab.json'

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

            lemma_raw = parts[0].strip().upper()
            word_raw = parts[1].strip().upper()

            # Portuguese: A-Z, accented chars, cedilha, -
            def clean_text(t):
                allowed = "ABCDEFGHIJKLMNOPQRSTUVWXYZÁÉÍÓÚÃÕÇÂÊÔÜ-"
                t2 = ''.join(c for c in t if c in allowed)
                return t2 if t2 else None

            lemma_clean = clean_text(lemma_raw)
            word_clean = clean_text(word_raw)
            if not lemma_clean or not word_clean:
                skipped += 1
                continue

            lemma = lemma_clean
            word = word_clean

            tags_raw = parts[2].split(';')
            pos = tags_raw[0]
            if pos not in POS_MAP:
                skipped += 1
                continue

            data[lemma][pos].append((word, tags_raw))

    print(f"Read {total_lines} lines, {len(data)} lemmas, skipped {skipped}")

    # Auto-generate singular base forms
    for lemma in list(data.keys()):
        for pos in list(data[lemma].keys()):
            forms = data[lemma][pos]
            words_in_forms = {w for w, _ in forms}
            if lemma not in words_in_forms:
                if pos == 'ADJ':
                    has_fem = any('FEM' in t for _, t in forms)
                    if has_fem:
                        tags = ['ADJ', 'MASC', 'SG']
                    else:
                        tags = ['ADJ', 'SG']
                elif pos == 'N':
                    has_fem = any('FEM' in t for _, t in forms)
                    if has_fem:
                        tags = ['N', 'FEM', 'SG']
                    else:
                        tags = ['N', 'MASC', 'SG']
                elif pos == 'V':
                    tags = ['V', 'NFIN']
                else:
                    tags = [pos, 'SG']
                data[lemma][pos].append((lemma, tags))

    # Portuguese closed-class words
    CLOSED_CLASS = {
        # Definite articles
        'O': ('DET', ['SG', 'MASC']),
        'A': ('DET', ['SG', 'FEM']),
        'OS': ('DET', ['PL', 'MASC']),
        'AS': ('DET', ['PL', 'FEM']),

        # Indefinite articles
        'UM': ('DET', ['SG', 'MASC']),
        'UMA': ('DET', ['SG', 'FEM']),
        'UNS': ('DET', ['PL', 'MASC']),
        'UMAS': ('DET', ['PL', 'FEM']),

        # Demonstratives
        'ESTE': ('DET', ['SG', 'MASC']),
        'ESTA': ('DET', ['SG', 'FEM']),
        'ESTES': ('DET', ['PL', 'MASC']),
        'ESTAS': ('DET', ['PL', 'FEM']),
        'ESSE': ('DET', ['SG', 'MASC']),
        'ESSA': ('DET', ['SG', 'FEM']),
        'ESSES': ('DET', ['PL', 'MASC']),
        'ESSAS': ('DET', ['PL', 'FEM']),
        'AQUELE': ('DET', ['SG', 'MASC']),
        'AQUELA': ('DET', ['SG', 'FEM']),
        'AQUELES': ('DET', ['PL', 'MASC']),
        'AQUELAS': ('DET', ['PL', 'FEM']),
        'ISTO': ('DET', ['SG', 'NEUT']),
        'ISSO': ('DET', ['SG', 'NEUT']),
        'AQUILO': ('DET', ['SG', 'NEUT']),

        # Possessives
        'MEU': ('DET', ['SG', 'MASC']),
        'MINHA': ('DET', ['SG', 'FEM']),
        'MEUS': ('DET', ['PL', 'MASC']),
        'MINHAS': ('DET', ['PL', 'FEM']),
        'TEU': ('DET', ['SG', 'MASC']),
        'TUA': ('DET', ['SG', 'FEM']),
        'TEUS': ('DET', ['PL', 'MASC']),
        'TUAS': ('DET', ['PL', 'FEM']),
        'SEU': ('DET', ['SG', 'MASC']),
        'SUA': ('DET', ['SG', 'FEM']),
        'SEUS': ('DET', ['PL', 'MASC']),
        'SUAS': ('DET', ['PL', 'FEM']),
        'NOSSO': ('DET', ['SG', 'MASC']),
        'NOSSA': ('DET', ['SG', 'FEM']),
        'NOSSOS': ('DET', ['PL', 'MASC']),
        'NOSSAS': ('DET', ['PL', 'FEM']),
        'VOSSO': ('DET', ['SG', 'MASC']),
        'VOSSA': ('DET', ['SG', 'FEM']),
        'VOSSOS': ('DET', ['PL', 'MASC']),
        'VOSSAS': ('DET', ['PL', 'FEM']),

        # Prepositions
        'DE': ('PREP', []),
        'EM': ('PREP', []),
        'POR': ('PREP', []),
        'PARA': ('PREP', []),
        'COM': ('PREP', []),
        'SEM': ('PREP', []),
        'SOB': ('PREP', []),
        'SOBRE': ('PREP', []),
        'ENTRE': ('PREP', []),
        'CONTRA': ('PREP', []),
        'ATÉ': ('PREP', []),
        'APÓS': ('PREP', []),
        'DESDE': ('PREP', []),
        'DURANTE': ('PREP', []),
        'ANTE': ('PREP', []),
        'PERANTE': ('PREP', []),
        'SEGUNDO': ('PREP', []),
        'MEDIANTE': ('PREP', []),
        'DO': ('PREP', []),
        'DA': ('PREP', []),
        'DOS': ('PREP', []),
        'DAS': ('PREP', []),
        'NO': ('PREP', []),
        'NA': ('PREP', []),
        'NOS': ('PREP', []),
        'NAS': ('PREP', []),
        'PELO': ('PREP', []),
        'PELA': ('PREP', []),
        'PELOS': ('PREP', []),
        'PELAS': ('PREP', []),
        'AO': ('PREP', []),
        'À': ('PREP', []),
        'AOS': ('PREP', []),
        'ÀS': ('PREP', []),

        # Coordinating conjunctions
        'E': ('CONJ', []),
        'OU': ('CONJ', []),
        'MAS': ('CONJ', []),
        'PORÉM': ('CONJ', []),
        'CONTUDO': ('CONJ', []),
        'TODAVIA': ('CONJ', []),
        'ENTRETANTO': ('CONJ', []),
        'PORTANTO': ('CONJ', []),
        'LOGO': ('CONJ', []),
        'POIS': ('CONJ', []),
        'NEM': ('CONJ', []),
        'SEJA': ('CONJ', []),
        'JÁ': ('CONJ', []),

        # Subordinating conjunctions
        'QUE': ('CONJ', []),
        'PORQUE': ('CONJ', []),
        'COMO': ('CONJ', []),
        'SE': ('CONJ', []),
        'QUANDO': ('CONJ', []),
        'ENQUANTO': ('CONJ', []),
        'EMBORA': ('CONJ', []),
        'AINDA': ('CONJ', []),
        'CONFORME': ('CONJ', []),
        'CONSOANTE': ('CONJ', []),
        'DESDE': ('CONJ', []),
        'PARA': ('CONJ', []),
        'SENÃO': ('CONJ', []),
        'CASO': ('CONJ', []),
        'MAL': ('CONJ', []),

        # Personal pronouns
        'EU': ('PRON', ['p1', 'SG']),
        'TU': ('PRON', ['p2', 'SG']),
        'ELE': ('PRON', ['p3', 'SG', 'MASC']),
        'ELA': ('PRON', ['p3', 'SG', 'FEM']),
        'NÓS': ('PRON', ['p1', 'PL']),
        'VÓS': ('PRON', ['p2', 'PL']),
        'ELES': ('PRON', ['p3', 'PL', 'MASC']),
        'ELAS': ('PRON', ['p3', 'PL', 'FEM']),

        # Clitic pronouns
        'ME': ('PRON', ['p1']),
        'TE': ('PRON', ['p2']),
        'SE': ('PRON', ['p3']),
        'NOS': ('PRON', ['p1', 'PL']),
        'VOS': ('PRON', ['p2', 'PL']),
        'O': ('PRON', ['p3', 'SG', 'MASC']),
        'A': ('PRON', ['p3', 'SG', 'FEM']),
        'OS': ('PRON', ['p3', 'PL', 'MASC']),
        'AS': ('PRON', ['p3', 'PL', 'FEM']),
        'LHE': ('PRON', ['p3', 'SG']),
        'LHES': ('PRON', ['p3', 'PL']),

        # Demonstrative pronouns
        'ESTE': ('PRON', ['SG', 'MASC']),
        'ESTA': ('PRON', ['SG', 'FEM']),
        'ESSE': ('PRON', ['SG', 'MASC']),
        'ESSA': ('PRON', ['SG', 'FEM']),
        'AQUELE': ('PRON', ['SG', 'MASC']),
        'AQUELA': ('PRON', ['SG', 'FEM']),
        'ISTO': ('PRON', ['SG', 'NEUT']),
        'ISSO': ('PRON', ['SG', 'NEUT']),
        'AQUILO': ('PRON', ['SG', 'NEUT']),

        # Common adverbs
        'NÃO': ('ADV', []),
        'SIM': ('ADV', []),
        'MUITO': ('ADV', []),
        'POUCO': ('ADV', []),
        'MAIS': ('ADV', []),
        'MENOS': ('ADV', []),
        'BEM': ('ADV', []),
        'MAL': ('ADV', []),
        'SEMPRE': ('ADV', []),
        'NUNCA': ('ADV', []),
        'TAMBÉM': ('ADV', []),
        'JÁ': ('ADV', []),
        'AINDA': ('ADV', []),
        'HOJE': ('ADV', []),
        'ONTEM': ('ADV', []),
        'AMANHÃ': ('ADV', []),
        'AGORA': ('ADV', []),
        'ANTES': ('ADV', []),
        'DEPOIS': ('ADV', []),
        'AQUI': ('ADV', []),
        'ALI': ('ADV', []),
        'LÁ': ('ADV', []),
        'SÓ': ('ADV', []),
        'QUASE': ('ADV', []),
        'TALVEZ': ('ADV', []),
    }

    for word, (pos, tags) in CLOSED_CLASS.items():
        data[word][pos].append((word, [pos] + tags))

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

"""
OpenCorpora morphological dictionary -> AOT format converter.

Input:  dict.opcorpora.xml  (from https://opencorpora.org/?page=downloads)
Output: morphs.json + gramtab.json  (AOT binary dictionary sources)

Usage:
    python3 dev/rus_conv/opencorpora_to_aot.py
"""

import json
import os
import sys
import xml.etree.ElementTree as ET

# ── Valid AOT POS (from CRusGramTab::RussianPartOfSpeech) ────────────────────
POS_MAP = {
    'NOUN':  'N',
    'ADJF':  'A',
    'ADJS':  'ADJ_SHORT',
    'COMP':  'ADV',         # компаратив -> наречие (AOT lacks dedicated COMP POS)
    'VERB':  'V',
    'INFN':  'INFINITIVE',
    'PRTF':  'PARTICIPLE',
    'PRTS':  'PARTICIPLE_SHORT',
    'GRND':  'ADV_PARTICIPLE',
    'NUMR':  'NUM',
    'ADVB':  'ADV',
    'NPRO':  'PRON',
    'PRED':  'PRED',
    'PREP':  'PREP',
    'CONJ':  'CONJ',
    'PRCL':  'PARTICLE',
    'INTJ':  'INT',
}

# ── Valid AOT Latin grammems (from CRusGramTab::Grammems[]) ──────────────────
# Only include tags that exist in the RusGramTab grammem table.
TAG_MAP = {
    # number
    'sing':  'sg',
    'plur':  'pl',
    # case
    'nomn':  'nom',
    'gent':  'gen',
    'datv':  'dat',
    'accs':  'acc',
    'ablt':  'ins',
    'loct':  'prp',         # AOT uses 'prp' not 'loc' for предложный
    'voct':  'voc',
    # gender
    'masc':  'mas',
    'femn':  'fem',
    'neut':  'neu',
    # animacy
    'anim':  'anim',
    'inan':  'inanim',
    # tense
    'pres':  'pres',
    'past':  'past',
    'futr':  'fut',
    # person
    '1per':  '1p',
    '2per':  '2p',
    '3per':  '3p',
    # aspect
    'perf':  'perf',
    'impf':  'imperf',      # AOT uses 'imperf' not 'imp'
    # transitivity
    'tran':  'trans',
    'intr':  'intrans',
    # voice
    'Act':   'act',
    'Pass':  'pass',
    # mood
    'impr':  'imp',         # AOT uses 'imp' for повелительное
    # other
    'Impe':  'impers',
    'Qual':  'qual',
    'Supr':  'superl',      # AOT uses 'superl' not 'sup'
    'Cmp2':  'compar',      # AOT uses 'compar' for сравнительная
    'Fixd':  '0',           # indeclinable
    # name types
    'Name':  'name',
    'Surn':  'surname',
    'Patr':  'patr',
    'Geox':  'loc',         # топоним -> AOT 'loc' tag
    'Orgn':  'org',
    'Abbr':  'abbr',
    # adj types
    'Poss':  'poss',
    'Anum':  'qual',        # порядковое -> approximated
}


def find_paradigm(lemma_text, forms):
    # Try different stems. Prefer longer stems.
    # Stem must be a prefix of the lemma.
    for i in range(len(lemma_text), -1, -1):
        stem = lemma_text[:i]
        paradigm = []
        possible = True
        for w, gcode in forms:
            # Try no prefix
            if w.startswith(stem):
                paradigm.append({"prefix": "", "flexia": w[len(stem):], "gramcode": gcode})
            # Try "ПО" prefix (common for adverbs/comparatives)
            elif w.startswith("ПО") and w[2:].startswith(stem):
                paradigm.append({"prefix": "ПО", "flexia": w[2+len(stem):], "gramcode": gcode})
            else:
                possible = False
                break
        if possible:
            return stem, paradigm
    # Fallback: empty stem, whole words as flexia
    return "", [{"prefix": "", "flexia": w, "gramcode": gcode} for w, gcode in forms]


def convert(input_file, output_dir):
    gramtab = {"gramcodes": {}}
    gram_to_code = {}
    next_code_idx = 0

    def get_gramcode(pos, tags, lemma_text):
        nonlocal next_code_idx
        aot_pos = POS_MAP.get(pos, '')
        if not aot_pos:
            return None
        aot_tags = []
        for t in tags:
            mapped = TAG_MAP.get(t)
            if mapped:
                aot_tags.append(mapped)

        # Infer sg if plur not present for declinable POS
        if aot_pos in ('N', 'A', 'PARTICIPLE', 'PRON', 'NUM') and 'pl' not in aot_tags:
            if 'sg' not in aot_tags:
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
                "l": lemma_text.upper()
            }
        return gram_to_code[key]

    flexia_models = []
    paradigm_to_id = {}
    lemmas_list = []

    # Parse XML with iterative parsing (401 MB file)
    print(f"Parsing {input_file} ...")
    context = ET.iterparse(input_file, events=('end',))

    lemma_count = 0
    skipped = 0

    # Regex for valid AOT Russian words (Cyrillic and hyphen)
    import re
    RUS_RE = re.compile(r'^[А-ЯЁ\-]+$')

    for event, elem in context:
        if elem.tag != 'lemma':
            continue

        lemma_id = elem.get('id', '')

        # Get lemma head (<l t="...">)
        l_elem = elem.find('l')
        if l_elem is None:
            elem.clear()
            continue

        lemma_text = l_elem.get('t', '').strip()
        if not lemma_text or not RUS_RE.match(lemma_text.upper()):
            skipped += 1
            elem.clear()
            continue

        # Get POS and lemma-level tags from <l><g v="..."/>
        l_grams = [g.get('v', '') for g in l_elem.findall('g')]
        pos = None
        l_tags = []
        for g in l_grams:
            if g in POS_MAP:
                pos = g
            elif g in TAG_MAP:
                l_tags.append(g)

        if not pos:
            skipped += 1
            elem.clear()
            continue

        # Collect word forms
        forms = []
        f_elems = elem.findall('f')
        if not f_elems:
            # Uninflected word — single form = lemma itself
            f_elems = [l_elem]  # reuse as self-form

        for f_elem in f_elems:
            word = f_elem.get('t', '').strip()
            if not word:
                continue
            f_grams = [g.get('v', '') for g in f_elem.findall('g')]
            # Form tags override/extend lemma tags for the gramcode
            all_tags = list(l_tags) + [t for t in f_grams if t in TAG_MAP]
            gcode = get_gramcode(pos, all_tags, lemma_text)
            if gcode:
                forms.append((word.upper(), gcode))

        if not forms:
            # Self-form with lemma-level tags only
            gcode = get_gramcode(pos, l_tags, lemma_text)
            if gcode:
                forms.append((lemma_text.upper(), gcode))

        if not forms:
            skipped += 1
            elem.clear()
            continue

        # Compute stem and flexia model
        lemma_upper = lemma_text.upper()
        stem, paradigm = find_paradigm(lemma_upper, forms)

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

        lemma_count += 1
        if lemma_count % 50000 == 0:
            print(f"  ... {lemma_count} lemmas processed")

        elem.clear()

    # Build plug_noun_gram_code for unknown-word prediction
    plug_code = ""
    inanim_indecl_noun = ""
    mas_abbr_noun = ""

    for code, info in gramtab["gramcodes"].items():
        if info["p"] == "N":
            tags = set(info.get("g", []))
            if info.get("l") and not plug_code:
                plug_code = code
            if "inanim" in tags and "0" in tags and not inanim_indecl_noun:
                inanim_indecl_noun = code
            if "mas" in tags and "abbr" in tags and not mas_abbr_noun:
                mas_abbr_noun = code

    if not plug_code:
        plug_code = list(gramtab["gramcodes"].keys())[0]
    if not inanim_indecl_noun:
        inanim_indecl_noun = plug_code
    if not mas_abbr_noun:
        mas_abbr_noun = plug_code

    gramtab["plug_noun_gram_code"] = plug_code
    gramtab["inanim_indecl_noun"] = inanim_indecl_noun
    gramtab["mas_abbr_noun"] = mas_abbr_noun


    morphs = {
        "flexia_models": flexia_models,
        "accent_models": [[]],
        "sessions": [{
            "user": "opencorpora",
            "start": "14.05.2026",
            "last_save": "14.05.2026"
        }],
        "prefix_sets": [],
        "lemmas": lemmas_list
    }

    os.makedirs(output_dir, exist_ok=True)
    morphs_path = os.path.join(output_dir, 'morphs.json')
    gramtab_path = os.path.join(output_dir, 'gramtab.json')

    print(f"Writing {morphs_path} ...")
    with open(morphs_path, 'w', encoding='utf-8') as f:
        json.dump(morphs, f, ensure_ascii=False, indent=1)

    print(f"Writing {gramtab_path} ...")
    with open(gramtab_path, 'w', encoding='utf-8') as f:
        json.dump(gramtab, f, ensure_ascii=False, indent=1)

    print(f"\nDone: {lemma_count} lemmas, {len(flexia_models)} flexia models, {skipped} skipped")


if __name__ == '__main__':
    project_root = os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
    input_file = os.path.join(project_root, 'Source', 'morph_dict', 'data', 'Russian', 'dict.opcorpora.xml')
    output_dir = os.path.join(project_root, 'Source', 'morph_dict', 'data', 'Russian')

    if not os.path.exists(input_file):
        print(f"Input not found: {input_file}", file=sys.stderr)
        sys.exit(1)

    convert(input_file, output_dir)

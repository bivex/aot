import json
import os
import sys
from collections import defaultdict
from datetime import datetime


POS_MAP = {
    'N': 'NOUN',
    'V': 'VERB',
    'V.PTCP': 'VERB',
    'V.CVB': 'VERB',
    'V.MSDR': 'VERB',
    'ADJ': 'ADJ',
}

# UniMorph Polish tag -> AOT grammem
TAG_MAP = {
    # number
    'SG': 'sg', 'PL': 'pl',
    # person
    '1': 'p1', '2': 'p2', '3': 'p3',
    # tense / mood / aspect
    'PRS': 'pres', 'PST': 'past', 'FUT': 'fut',
    'IND': 'ind', 'IMP': 'imp', 'COND': 'cond',
    # non-finite / voice
    'NFIN': 'inf',
    'ACT': 'act', 'PASS': 'pass',
    # gender (singular)
    'MASC': 'masc', 'FEM': 'fem', 'NEUT': 'neut',
    # animacy (affects accusative; HUM=virile in plural)
    'ANIM': 'anim', 'INAN': 'nanim', 'HUM': 'vir',
    # cases — note ESS = Polish locative in UniMorph
    'NOM': 'nom', 'GEN': 'gen', 'DAT': 'dat', 'ACC': 'acc',
    'INS': 'ins', 'ESS': 'loc', 'VOC': 'voc',
    'LOC': 'loc', 'ABL': 'gen', 'ALL': 'dat',
    # degree
    'POS': 'pos', 'CMPR': 'comp', 'SPRL': 'sup',
}

SKIP_TAGS = set()


def clean_polish(text):
    """Uppercase and strip Polish diacritics, keep A-Z and -."""
    t = text.upper()
    replacements = {
        'Ą': 'A', 'Ć': 'C', 'Ę': 'E', 'Ł': 'L', 'Ń': 'N',
        'Ó': 'O', 'Ś': 'S', 'Ź': 'Z', 'Ż': 'Z',
    }
    for k, v in replacements.items():
        t = t.replace(k, v)
    result = []
    for c in t:
        if c in 'ABCDEFGHIJKLMNOPQRSTUVWXYZ-':
            result.append(c)
    t2 = ''.join(result)
    return t2 if t2 else None


def convert():
    input_file = 'Dicts/Morph/Polish/unimorph/pol'
    output_morphs = 'Source/morph_dict/data/Polish/morphs.json'
    output_gramtab = 'Source/morph_dict/data/Polish/gramtab.json'

    gramtab = {"gramcodes": {}}
    gram_to_code = {}
    next_code_idx = 0

    def get_gramcode(pos, tags, lemma=None):
        nonlocal next_code_idx

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
            if mapped and mapped not in aot_tags:
                aot_tags.append(mapped)

        # Nouns: ensure number + case
        if aot_pos == 'NOUN':
            if 'sg' not in aot_tags and 'pl' not in aot_tags:
                aot_tags.append('sg')
            case_tags = {'nom', 'gen', 'dat', 'acc', 'ins', 'loc', 'voc'}
            if not any(t in case_tags for t in aot_tags):
                aot_tags.append('nom')

        # Adjectives: ensure number + case + gender default
        if aot_pos == 'ADJ':
            if 'sg' not in aot_tags and 'pl' not in aot_tags:
                aot_tags.append('sg')
            case_tags = {'nom', 'gen', 'dat', 'acc', 'ins', 'loc', 'voc'}
            if not any(t in case_tags for t in aot_tags):
                aot_tags.append('nom')

        # Finite verbs: ensure mood + tense + person + number
        if aot_pos == 'VERB' and 'ptcp' not in aot_tags and 'inf' not in aot_tags:
            mood_tags = {'ind', 'imp', 'cond'}
            if not any(t in mood_tags for t in aot_tags):
                aot_tags.append('ind')
            tense_tags = {'pres', 'past', 'fut'}
            if not any(t in tense_tags for t in aot_tags):
                aot_tags.append('pres')
            if 'p1' not in aot_tags and 'p2' not in aot_tags and 'p3' not in aot_tags:
                aot_tags.append('p3')
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

    # Read UniMorph data
    data = defaultdict(lambda: defaultdict(list))
    total_lines = 0
    skipped = 0
    multi_word = 0

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

            if ' ' in word_raw or ' ' in lemma_raw:
                multi_word += 1
                continue

            lemma_clean = clean_polish(lemma_raw)
            word_clean = clean_polish(word_raw)
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

    # Closed-class words (not in UniMorph)
    CLOSED_CLASS = {
        # Personal pronouns (nom)
        'JA': [('PRON', ['p1', 'sg', 'nom'])],
        'TY': [('PRON', ['p2', 'sg', 'nom'])],
        'ON': [('PRON', ['p3', 'sg', 'masc', 'nom'])],
        'ONA': [('PRON', ['p3', 'sg', 'fem', 'nom'])],
        'ONO': [('PRON', ['p3', 'sg', 'neut', 'nom'])],
        'MY': [('PRON', ['p1', 'pl', 'nom'])],
        'WY': [('PRON', ['p2', 'pl', 'nom'])],
        'ONI': [('PRON', ['p3', 'pl', 'vir', 'nom'])],
        'ONE': [('PRON', ['p3', 'pl', 'nvir', 'nom'])],
        # Demonstrative
        'TEN': [('PRON', ['sg', 'masc', 'nom']), ('DET', ['sg', 'masc', 'nom'])],
        'TA': [('PRON', ['sg', 'fem', 'nom']), ('DET', ['sg', 'fem', 'nom'])],
        'TO': [('PRON', ['sg', 'neut', 'nom']), ('DET', ['sg', 'neut', 'nom'])],
        'CI': [('PRON', ['pl', 'vir', 'nom'])],
        'TE': [('PRON', ['pl', 'nvir', 'nom'])],
        'TYCH': [('PRON', ['pl', 'gen'])],
        # Interrogative/relative
        'KTO': [('PRON', ['nom'])],
        'CO': [('PRON', ['nom'])],
        'KOGO': [('PRON', ['gen', 'acc'])],
        'CZEGO': [('PRON', ['gen'])],
        'KOMU': [('PRON', ['dat'])],
        'CZEMU': [('PRON', ['dat'])],
        'KIM': [('PRON', ['ins', 'loc'])],
        'CZYM': [('PRON', ['ins', 'loc'])],
        'KTORY': [('PRON', ['sg', 'masc', 'nom'])],
        'JAKI': [('PRON', ['sg', 'masc', 'nom']), ('DET', ['sg', 'masc', 'nom'])],
        'ILE': [('PRON', []), ('NUM', [])],
        'GDZIE': [('ADV', [])],
        'KIEDY': [('ADV', [])],
        'JAK': [('ADV', [])],
        'DLACZEGO': [('ADV', [])],
        'CZY': [('CONJ', []), ('PART', [])],
        # Coordinating conjunctions
        'I': [('CONJ', [])],
        'ORAZ': [('CONJ', [])],
        'A': [('CONJ', [])],
        'ALE': [('CONJ', [])],
        'LUB': [('CONJ', [])],
        'ALBO': [('CONJ', [])],
        'CZY': [('CONJ', [])],
        'NI': [('CONJ', [])],
        'WIEC': [('CONJ', [])],
        'ZATEM': [('CONJ', [])],
        'TOTZE': [('CONJ', [])],
        'NAWET': [('PART', [])],
        # Subordinating conjunctions
        'ZE': [('CONJ', [])],
        'BO': [('CONJ', [])],
        'PONIEWAZ': [('CONJ', [])],
        'PONIEWAZ': [('CONJ', [])],
        'GDY': [('CONJ', [])],
        'GDYBY': [('CONJ', [])],
        'JESLI': [('CONJ', [])],
        'JAKBY': [('CONJ', [])],
        'CHOX': [('CONJ', [])],
        'CHOC': [('CONJ', [])],
        'ZEBY': [('CONJ', [])],
        'ABY': [('CONJ', [])],
        'BY': [('CONJ', []), ('PART', [])],
        'AZ': [('CONJ', []), ('PART', [])],
        # Prepositions
        'W': [('PREP', [])],
        'Z': [('PREP', [])],
        'NA': [('PREP', [])],
        'DO': [('PREP', [])],
        'O': [('PREP', [])],
        'DLA': [('PREP', [])],
        'OD': [('PREP', [])],
        'PO': [('PREP', [])],
        'PRZED': [('PREP', [])],
        'ZA': [('PREP', [])],
        'POPRZEZ': [('PREP', [])],
        'PRZEZ': [('PREP', [])],
        'NAD': [('PREP', [])],
        'POD': [('PREP', [])],
        'PRZY': [('PREP', [])],
        'MIEDZY': [('PREP', [])],
        'WOBEC': [('PREP', [])],
        'WEDLUG': [('PREP', [])],
        'BEZ': [('PREP', [])],
        'U': [('PREP', [])],
        'KU': [('PREP', [])],
        # Particles
        'NIE': [('PART', [])],
        'TAKZE': [('PART', [])],
        'BYLE': [('PART', [])],
        'JEDYNE': [('PART', [])],
        # Adverbs
        'TAK': [('ADV', [])],
        'NIE': [('ADV', [])],
        'BARDZO': [('ADV', [])],
        'TERAZ': [('ADV', [])],
        'JUTRO': [('ADV', [])],
        'WCZORAJ': [('ADV', [])],
        'ZAWSZE': [('ADV', [])],
        'NIGDY': [('ADV', [])],
        'CZESTO': [('ADV', [])],
        'RZADKO': [('ADV', [])],
        'TUTAJ': [('ADV', [])],
        'TAM': [('ADV', [])],
        'DOBRZE': [('ADV', [])],
        'ZLE': [('ADV', [])],
        'SZYBKO': [('ADV', [])],
        'WOLNO': [('ADV', [])],
        'PRAWDOPDOBNIE': [('ADV', [])],
        'MOZE': [('ADV', [])],
        'OCZYWISCIE': [('ADV', [])],
        # Numbers
        'JEDEN': [('NUM', ['sg'])],
        'DWA': [('NUM', [])],
        'TRZY': [('NUM', [])],
        'CZTERY': [('NUM', [])],
        'PIEC': [('NUM', [])],
        'SZESC': [('NUM', [])],
        'SIEDEM': [('NUM', [])],
        'OSIEM': [('NUM', [])],
        'DZIEWIEC': [('NUM', [])],
        'DZIESIEC': [('NUM', [])],
        'STO': [('NUM', [])],
        'TYSIAC': [('NUM', [])],
        # Articles (Polish has none; this is a placeholder for DET-like 'ten')
    }

    for word, entries in CLOSED_CLASS.items():
        word_clean = clean_polish(word)
        if not word_clean:
            continue
        for pos, tags in entries:
            data[word_clean][pos].append((word_clean, [pos] + tags))

    # Common Polish nouns (legal/general vocabulary)
    NOUNS = {
        'PRAWO': ['sg'], 'PRAWA': ['pl'],
        'USTAWA': ['sg'], 'USTAWY': ['pl'],
        'UMOWA': ['sg'], 'UMOWY': ['pl'],
        'KONSTYTUCJA': ['sg'],
        'SAD': ['sg'], 'SADY': ['pl'],
        'SEDMZIAD': ['sg'],
        'SPRAWA': ['sg'], 'SPRAWY': ['pl'],
        'PANSTWO': ['sg'],
        'OSOBA': ['sg'], 'OSOBY': ['pl'],
        'DOKUMENT': ['sg'], 'DOKUMENTY': ['pl'],
        'POSTANOWIENIE': ['sg'], 'POSTANOWIENIA': ['pl'],
        'RZAD': ['sg'],
        'PARLAMENT': ['sg'],
        'POLICJA': ['sg'],
        'PRZESTEPSTWO': ['sg'], 'PRZESTEPSTWA': ['pl'],
        'KARA': ['sg'], 'KARY': ['pl'],
        'OFIARA': ['sg'], 'OFIARY': ['pl'],
        'SWIADEK': ['sg'], 'SWIADKOWIE': ['pl'],
        'ADWOKAT': ['sg'], 'ADWOKACI': ['pl'],
        'URZAD': ['sg'], 'URZEDY': ['pl'],
        'ZAKLAD': ['sg'], 'ZAKLADY': ['pl'],
        'SPOLEKA': ['sg'], 'SPOLEKI': ['pl'],
        'WLASNOSC': ['sg'],
        'PIENIADZ': ['sg'],
        'KREDYT': ['sg'], 'KREDYTY': ['pl'],
        'PODATEK': ['sg'], 'PODATKI': ['pl'],
        'CZLOWIEK': ['sg'], 'LUDZIE': ['pl'],
        'MEZCZYZNA': ['sg'], 'MEZCZYZNI': ['pl'],
        'KOBIETA': ['sg'], 'KOBIETY': ['pl'],
        'DZIECKO': ['sg'], 'DZIECI': ['pl'],
        'RODZINA': ['sg'], 'RODZINY': ['pl'],
        'DOM': ['sg'], 'DOMY': ['pl'],
        'SZKOLA': ['sg'], 'SZKOLY': ['pl'],
        'PRACA': ['sg'],
        'MIASTO': ['sg'], 'MIASTA': ['pl'],
        'KRAJ': ['sg'], 'KRAJE': ['pl'],
        'SWIAT': ['sg'],
        'CZAS': ['sg'], 'CZASY': ['pl'],
        'ROK': ['sg'], 'LATA': ['pl'],
        'DZIEN': ['sg'], 'DNI': ['pl'],
        'WODA': ['sg'],
        'CHLEB': ['sg'],
        'SAMOCHOD': ['sg'], 'SAMOCHODY': ['pl'],
        'KSIAZKA': ['sg'], 'KSIAZKI': ['pl'],
        'PIES': ['sg'], 'PSY': ['pl'],
        'DRZEWO': ['sg'], 'DRZEWA': ['pl'],
        'GORA': ['sg'], 'GORY': ['pl'],
        'RZEKA': ['sg'], 'RZEKI': ['pl'],
        'JEZIORO': ['sg'], 'JEZIORA': ['pl'],
        'IMIE': ['sg'], 'IMIONA': ['pl'],
        'SLOWO': ['sg'], 'SLOWA': ['pl'],
        'JEZYK': ['sg'], 'JEZYKI': ['pl'],
        'PRZYKLAD': ['sg'], 'PRZYKLADY': ['pl'],
        'ODPOWIEDZ': ['sg'], 'ODPOWIEDZI': ['pl'],
        'PYTANIE': ['sg'], 'PYTANIA': ['pl'],
        'POWOD': ['sg'], 'POWODY': ['pl'],
        'WARTOSC': ['sg'], 'WARTOSCI': ['pl'],
        'ZOBOWIAZANIE': ['sg'], 'ZOBOWIAZANIA': ['pl'],
        'PRAWO': ['sg'],
        'ODPOWIEDZIALNOSC': ['sg'],
        'NAUKA': ['sg'], 'NAUKI': ['pl'],
        'TECHNIKA': ['sg'],
        'KULTURA': ['sg'], 'KULTURY': ['pl'],
    }

    for word, tags in NOUNS.items():
        word_clean = clean_polish(word)
        if word_clean:
            data[word_clean]['N'].append((word_clean, ['N', 'NOM'] + tags))

    # Common verbs (including 'być' = to be, with stripped diacritics)
    COMMON_VERBS = {
        'BYC': [  # być
            ('JESTEM', ['V', 'PRS', 'IND', '1', 'SG']),
            ('JESTES', ['V', 'PRS', 'IND', '2', 'SG']),
            ('JEST', ['V', 'PRS', 'IND', '3', 'SG']),
            ('JESTESMY', ['V', 'PRS', 'IND', '1', 'PL']),
            ('JESTESCIE', ['V', 'PRS', 'IND', '2', 'PL']),
            ('SA', ['V', 'PRS', 'IND', '3', 'PL']),
            ('BYLEM', ['V', 'PST', 'IND', '1', 'SG', 'MASC']),
            ('BYLES', ['V', 'PST', 'IND', '2', 'SG', 'MASC']),
            ('BYLAM', ['V', 'PST', 'IND', '1', 'SG', 'FEM']),
            ('BYLAS', ['V', 'PST', 'IND', '2', 'SG', 'FEM']),
            ('BYL', ['V', 'PST', 'IND', '3', 'SG', 'MASC']),
            ('BYLA', ['V', 'PST', 'IND', '3', 'SG', 'FEM']),
            ('BYLO', ['V', 'PST', 'IND', '3', 'SG', 'NEUT']),
            ('BYLISMY', ['V', 'PST', 'IND', '1', 'PL', 'MASC', 'HUM']),
            ('BYLISCIE', ['V', 'PST', 'IND', '2', 'PL', 'MASC', 'HUM']),
            ('BYLI', ['V', 'PST', 'IND', '3', 'PL', 'MASC', 'HUM']),
            ('BYLY', ['V', 'PST', 'IND', '3', 'PL']),
            ('BYC', ['V', 'NFIN']),
        ],
        'MIEC': [
            ('MAM', ['V', 'PRS', 'IND', '1', 'SG']),
            ('MASZ', ['V', 'PRS', 'IND', '2', 'SG']),
            ('MA', ['V', 'PRS', 'IND', '3', 'SG']),
            ('MAMY', ['V', 'PRS', 'IND', '1', 'PL']),
            ('MACIE', ['V', 'PRS', 'IND', '2', 'PL']),
            ('MAJA', ['V', 'PRS', 'IND', '3', 'PL']),
            ('MIEC', ['V', 'NFIN']),
        ],
        'ROBIC': [
            ('ROBIE', ['V', 'PRS', 'IND', '1', 'SG']),
            ('ROBISZ', ['V', 'PRS', 'IND', '2', 'SG']),
            ('ROBI', ['V', 'PRS', 'IND', '3', 'SG']),
            ('ROBIMY', ['V', 'PRS', 'IND', '1', 'PL']),
            ('ROBICIE', ['V', 'PRS', 'IND', '2', 'PL']),
            ('ROBIA', ['V', 'PRS', 'IND', '3', 'PL']),
            ('ROBIC', ['V', 'NFIN']),
        ],
        'MOWIC': [
            ('MOWIE', ['V', 'PRS', 'IND', '1', 'SG']),
            ('MOWISZ', ['V', 'PRS', 'IND', '2', 'SG']),
            ('MOWI', ['V', 'PRS', 'IND', '3', 'SG']),
            ('MOWIMY', ['V', 'PRS', 'IND', '1', 'PL']),
            ('MOWICIE', ['V', 'PRS', 'IND', '2', 'PL']),
            ('MOWIA', ['V', 'PRS', 'IND', '3', 'PL']),
            ('MOWIC', ['V', 'NFIN']),
        ],
        'WIEDZIEC': [
            ('WIEM', ['V', 'PRS', 'IND', '1', 'SG']),
            ('WIESZ', ['V', 'PRS', 'IND', '2', 'SG']),
            ('WIE', ['V', 'PRS', 'IND', '3', 'SG']),
            ('WIEMY', ['V', 'PRS', 'IND', '1', 'PL']),
            ('WIECIE', ['V', 'PRS', 'IND', '2', 'PL']),
            ('WIEDZA', ['V', 'PRS', 'IND', '3', 'PL']),
            ('WIEDZIEC', ['V', 'NFIN']),
        ],
        'CHCIEC': [
            ('CHCE', ['V', 'PRS', 'IND', '1', 'SG']),
            ('CHCESZ', ['V', 'PRS', 'IND', '2', 'SG']),
            ('CHCE', ['V', 'PRS', 'IND', '3', 'SG']),
            ('CHCEMY', ['V', 'PRS', 'IND', '1', 'PL']),
            ('CHCECIE', ['V', 'PRS', 'IND', '2', 'PL']),
            ('CHCA', ['V', 'PRS', 'IND', '3', 'PL']),
            ('CHCIEC', ['V', 'NFIN']),
        ],
        'MUSIEC': [
            ('MUSZE', ['V', 'PRS', 'IND', '1', 'SG']),
            ('MUSISZ', ['V', 'PRS', 'IND', '2', 'SG']),
            ('MUSI', ['V', 'PRS', 'IND', '3', 'SG']),
            ('MUSIMY', ['V', 'PRS', 'IND', '1', 'PL']),
            ('MUSICIE', ['V', 'PRS', 'IND', '2', 'PL']),
            ('MUSZA', ['V', 'PRS', 'IND', '3', 'PL']),
            ('MUSIEC', ['V', 'NFIN']),
        ],
        'ISC': [
            ('IDE', ['V', 'PRS', 'IND', '1', 'SG']),
            ('IDZIESZ', ['V', 'PRS', 'IND', '2', 'SG']),
            ('IDZIE', ['V', 'PRS', 'IND', '3', 'SG']),
            ('IDZIEMY', ['V', 'PRS', 'IND', '1', 'PL']),
            ('IDZIECIE', ['V', 'PRS', 'IND', '2', 'PL']),
            ('IDA', ['V', 'PRS', 'IND', '3', 'PL']),
            ('ISC', ['V', 'NFIN']),
        ],
    }

    for lemma, forms in COMMON_VERBS.items():
        lemma_clean = clean_polish(lemma)
        if not lemma_clean:
            continue
        for form_raw, tags in forms:
            form_clean = clean_polish(form_raw)
            if form_clean:
                data[lemma_clean][tags[0]].append((form_clean, tags))

    # Build morphology
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

            # Sort: prefer exact lemma match, then inf, then nom, then shortest
            def _lemma_sort_key(wc):
                w, gc = wc
                gc_info = gramtab["gramcodes"].get(gc, {})
                gc_tags = gc_info.get("g", [])
                is_exact = 0 if w == lemma else 1
                is_inf = 0 if 'inf' in gc_tags else 1
                is_nom = 0 if 'nom' in gc_tags else 1
                return (is_exact, is_inf, is_nom, len(w))
            word_codes.sort(key=_lemma_sort_key)

            # Find common stem
            stem = lemma
            for w, _ in word_codes:
                while not w.startswith(stem) and stem:
                    stem = stem[:-1]

            # If stem too short (suppletion), individual entries per form
            if len(stem) < 2:
                for w, gcode in word_codes:
                    paradigm = [{"flexia": "", "gramcode": gcode}]
                    p_key = json.dumps(paradigm, sort_keys=True)
                    if p_key not in paradigm_to_id:
                        p_id = len(flexia_models)
                        paradigm_to_id[p_key] = p_id
                        flexia_models.append({"endings": paradigm})
                    else:
                        p_id = paradigm_to_id[p_key]
                    lemmas_list.append({"l": w, "f": p_id, "a": 0, "s": 0})
                    count += 1
            else:
                paradigm = []
                for w, gcode in word_codes:
                    flex = w[len(stem):] if w.startswith(stem) else w
                    paradigm.append({"flexia": flex, "gramcode": gcode})

                p_key = json.dumps(paradigm, sort_keys=True)
                if p_key not in paradigm_to_id:
                    p_id = len(flexia_models)
                    paradigm_to_id[p_key] = p_id
                    flexia_models.append({"endings": paradigm})
                else:
                    p_id = paradigm_to_id[p_key]

                lemmas_list.append({"l": lemma, "f": p_id, "a": 0, "s": 0})
                count += len(word_codes)

    # Plug code for noun
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

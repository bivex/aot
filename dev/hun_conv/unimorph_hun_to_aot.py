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
    'POT': 'VERB',
}

TAG_MAP = {
    'SG': 'sg', 'PL': 'pl',
    '1': 'p1', '2': 'p2', '3': 'p3',
    'PRS': 'pres', 'PST': 'past', 'FUT': 'fut',
    'IND': 'ind', 'COND': 'cond', 'SBJV': 'sbjv',
    'DEF': 'def', 'INDF': 'indef',
    'NFIN': 'inf',
    # Simple cases
    'NOM': 'nom', 'ACC': 'acc', 'DAT': 'dat',
    'INS': 'ins', 'PRP': 'cau', 'TRANS': 'tra',
    'TERM': 'ter', 'FRML': 'ess',
    # Compound directional cases (locative→lative→ablative triples)
    'IN+ESS': 'ine', 'IN+ALL': 'ill', 'IN+ABL': 'ela',
    'ON+ESS': 'sub', 'ON+ALL': 'all', 'ON+ABL': 'del',
    'AT+ESS': 'ade', 'AT+ALL': 'lat', 'AT+ABL': 'abl',
    # Degree
    'POS': 'pos', 'CMPR': 'comp', 'SPRL': 'sup',
}

# Possessive tags → person + number of possessor
POSS_MAP = {
    'PSS1S': ('p1', 'sg'),
    'PSS2S': ('p2', 'sg'),
    'PSS3S': ('p3', 'sg'),
    'PSS1P': ('p1', 'pl'),
    'PSS2P': ('p2', 'pl'),
    'PSS3P': ('p3', 'pl'),
}

SKIP_TAGS = {'LGSPEC1', 'LGSPEC2', 'LGSPEC3', 'BYWAY'}


def clean_hungarian(text):
    t = text.upper()
    replacements = {
        'Á': 'A', 'É': 'E', 'Í': 'I', 'Ó': 'O',
        'Ö': 'O', 'Ő': 'O', 'Ú': 'U', 'Ü': 'U', 'Ű': 'U',
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
    input_file = 'Dicts/Morph/Hungarian/unimorph/hun'
    output_morphs = 'Source/morph_dict/data/Hungarian/morphs.json'
    output_gramtab = 'Source/morph_dict/data/Hungarian/gramtab.json'

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
            if t in POSS_MAP:
                person, pnum = POSS_MAP[t]
                if person not in aot_tags:
                    aot_tags.append(person)
                # Don't add pnum as number — the SG/PL tag covers possessed number
                continue
            mapped = TAG_MAP.get(t)
            if mapped and mapped not in aot_tags:
                aot_tags.append(mapped)

        # Ensure nouns/adjs have number
        if aot_pos in ('NOUN', 'ADJ'):
            if 'sg' not in aot_tags and 'pl' not in aot_tags:
                aot_tags.append('sg')
            # Ensure case — default to nom if none
            case_tags = {'nom', 'acc', 'dat', 'gen', 'ins', 'cau', 'tra', 'ess',
                         'ill', 'ine', 'ela', 'sub', 'del', 'all', 'ade', 'abl', 'ter', 'lat'}
            if not any(t in case_tags for t in aot_tags):
                aot_tags.append('nom')

        # Finite verbs: ensure mood and definiteness
        if aot_pos == 'VERB' and 'ptcp' not in aot_tags:
            mood_tags = {'ind', 'cond', 'sbjv', 'impv'}
            if 'inf' not in aot_tags and not any(t in mood_tags for t in aot_tags):
                aot_tags.append('ind')
            if 'inf' not in aot_tags and 'def' not in aot_tags and 'indef' not in aot_tags:
                aot_tags.append('indef')
            # Ensure tense for finite verbs
            if 'inf' not in aot_tags:
                tense_tags = {'pres', 'past', 'fut'}
                if not any(t in tense_tags for t in aot_tags):
                    aot_tags.append('pres')
            # Ensure number for finite verbs
            if 'inf' not in aot_tags:
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

            if ' ' in word_raw:
                multi_word += 1
                continue

            lemma_clean = clean_hungarian(lemma_raw)
            word_clean = clean_hungarian(word_raw)
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
        # Personal pronouns
        'EN': [('PRON', ['p1', 'sg', 'nom'])],
        'TE': [('PRON', ['p2', 'sg', 'nom'])],
        'O': [('PRON', ['p3', 'sg', 'nom'])],
        'MI': [('PRON', ['p1', 'pl', 'nom'])],
        'TI': [('PRON', ['p2', 'pl', 'nom'])],
        'OK': [('PRON', ['p3', 'pl', 'nom'])],
        # Accusative pronouns
        'ENGEM': [('PRON', ['p1', 'sg', 'acc'])],
        'TEGED': [('PRON', ['p2', 'sg', 'acc'])],
        'OT': [('PRON', ['p3', 'sg', 'acc'])],
        'MINKET': [('PRON', ['p1', 'pl', 'acc'])],
        'TITEKET': [('PRON', ['p2', 'pl', 'acc'])],
        'OKET': [('PRON', ['p3', 'pl', 'acc'])],
        # Demonstrative pronouns
        'EZ': [('PRON', ['sg', 'nom']), ('DET', ['sg'])],
        'AZ': [('PRON', ['sg', 'nom']), ('DET', ['sg'])],
        'EZT': [('PRON', ['sg', 'acc']), ('DET', ['sg'])],
        'AZT': [('PRON', ['sg', 'acc']), ('DET', ['sg'])],
        'EZT-AZT': [('PRON', ['sg', 'acc'])],
        'EZEK': [('PRON', ['pl', 'nom']), ('DET', ['pl'])],
        'AZOK': [('PRON', ['pl', 'nom']), ('DET', ['pl'])],
        # Relative/interrogative pronouns
        'KI': [('PRON', ['nom'])],
        'KIT': [('PRON', ['acc'])],
        'KINEK': [('PRON', ['dat'])],
        'MI': [('PRON', ['nom'])],
        'MIT': [('PRON', ['acc'])],
        'MINEK': [('PRON', ['dat'])],
        'MELYIK': [('PRON', [])],
        'HOL': [('PRON', ['ine']), ('ADV', [])],
        'MIKOR': [('PRON', []), ('ADV', [])],
        'HOGYAN': [('PRON', []), ('ADV', [])],
        'MIERT': [('PRON', []), ('ADV', [])],
        # Coordinating conjunctions
        'ES': [('CONJ', [])],
        'VAGY': [('CONJ', [])],
        'DE': [('CONJ', [])],
        'HANEM': [('CONJ', [])],
        'SE': [('CONJ', [])],
        'SEM': [('CONJ', [])],
        'IS': [('CONJ', [])],
        'MERT': [('CONJ', [])],
        'TEHAT': [('CONJ', [])],
        # Subordinating conjunctions
        'HOGY': [('CONJ', [])],
        'HA': [('CONJ', [])],
        'AMIKOR': [('CONJ', [])],
        'MIELUTT': [('CONJ', [])],
        'UTAN': [('CONJ', [])],
        'BAR': [('CONJ', [])],
        'HABAR': [('CONJ', [])],
        'JOGY': [('CONJ', [])],
        'PEDIG': [('CONJ', [])],
        'VALAMINT': [('CONJ', [])],
        'MINTE': [('CONJ', [])],
        'MIN': [('CONJ', [])],
        'AKKOR': [('CONJ', [])],
        # Prepositions / postpositions
        'BAN': [('PREP', [])],
        'BEN': [('PREP', [])],
        'RA': [('PREP', [])],
        'RE': [('PREP', [])],
        'RA': [('PREP', [])],
        'HOZ': [('PREP', [])],
        'HEZ': [('PREP', [])],
        'NAL': [('PREP', [])],
        'NEL': [('PREP', [])],
        'VELE': [('PREP', [])],
        'ELOTT': [('PREP', [])],
        'UTAN': [('PREP', [])],
        'ALATT': [('PREP', [])],
        'FELETT': [('PREP', [])],
        'KOZOTT': [('PREP', [])],
        'NELKUL': [('PREP', [])],
        'SZERINT': [('PREP', [])],
        'VEZETTEVEL': [('PREP', [])],
        'ALAPJAN': [('PREP', [])],
        'EREDEJERE': [('PREP', [])],
        'KIVUL': [('PREP', [])],
        'AT': [('PREP', [])],
        'FEL': [('PREP', [])],
        'LE': [('PREP', [])],
        'BE': [('PREP', [])],
        'KI': [('PREP', [])],
        # Particles
        'NEM': [('PART', []), ('ADV', [])],
        'NE': [('PART', [])],
        'CSAK': [('PART', [])],
        'IS': [('PART', [])],
        'SEM': [('PART', [])],
        # Adverbs
        'NAGYON': [('ADV', [])],
        'JO': [('ADV', [])],
        'ROSSZUL': [('ADV', [])],
        'GYORSAN': [('ADV', [])],
        'LASAN': [('ADV', [])],
        'ITT': [('ADV', [])],
        'OTT': [('ADV', [])],
        'MOST': [('ADV', [])],
        'MA': [('ADV', [])],
        'TEGNAP': [('ADV', [])],
        'HOLNAP': [('ADV', [])],
        'MINDIG': [('ADV', [])],
        'SOHA': [('ADV', [])],
        'SOKSZOR': [('ADV', [])],
        'EGYSZER': [('ADV', [])],
        'TOBBKEPPE': [('ADV', [])],
        'TOBBET': [('ADV', [])],
        'KEVESEBBET': [('ADV', [])],
        'IGEN': [('ADV', [])],
        'NEM': [('ADV', [])],
        'TALAN': [('ADV', [])],
        'VALOSZINULEG': [('ADV', [])],
        'BIZTOSAN': [('ADV', [])],
        'PONTOSAN': [('ADV', [])],
        # Numbers
        'EGY': [('NUM', ['sg'])],
        'KETTO': [('NUM', ['sg'])],
        'HATROM': [('NUM', ['sg'])],
        'NEGY': [('NUM', ['sg'])],
        'OT': [('NUM', ['sg'])],
        'HAT': [('NUM', ['sg'])],
        'HET': [('NUM', ['sg'])],
        'NYOLC': [('NUM', ['sg'])],
        'KILINC': [('NUM', ['sg'])],
        'TIZ': [('NUM', ['sg'])],
        'SZAZ': [('NUM', ['sg'])],
        'EZER': [('NUM', ['sg'])],
        # Articles
        'A': [('DET', [])],
        'AZ': [('DET', [])],
        'EGY': [('DET', []), ('NUM', ['sg'])],
    }

    for word, entries in CLOSED_CLASS.items():
        word_clean = clean_hungarian(word)
        if not word_clean:
            continue
        for pos, tags in entries:
            data[word_clean][pos].append((word_clean, [pos] + tags))

    # Common Hungarian nouns (legal/general vocabulary)
    NOUNS = {
        'JOG': ['sg'], 'JOGOK': ['pl'],
        'TORVENY': ['sg'], 'TORVENYEK': ['pl'],
        'SZERZODES': ['sg'], 'SZERZODESEK': ['pl'],
        'BIRASAG': ['sg'], 'BIRASAGOK': ['pl'],
        'BIRAS': ['sg'], 'BIRAK': ['pl'],
        'UGY': ['sg'], 'UGYEK': ['pl'],
        'ALLAM': ['sg'], 'ALLAMOK': ['pl'],
        'SZEMELY': ['sg'], 'SZEMELYEK': ['pl'],
        'DOKUMENTUM': ['sg'], 'DOKUMENTUMOK': ['pl'],
        'HATAROZAT': ['sg'], 'HATAROZATOK': ['pl'],
        'BIROTTSG': ['sg'],
        'KORMANY': ['sg'],
        'PARLAMENT': ['sg'],
        'RENDORSG': ['sg'],
        'BUNUGY': ['sg'], 'BUNUGYEK': ['pl'],
        'BUNTETES': ['sg'], 'BUNTETESEK': ['pl'],
        'ALDOZAT': ['sg'], 'ALDOZATOK': ['pl'],
        'TANU': ['sg'], 'TANUK': ['pl'],
        'UGYVED': ['sg'], 'UGYVEDEK': ['pl'],
        'VEDEKEZES': ['sg'],
        'HIVATAL': ['sg'], 'HIVATALOK': ['pl'],
        'INTAZET': ['sg'], 'INTAZETEK': ['pl'],
        'TARSASAG': ['sg'], 'TARSASAGOK': ['pl'],
        'TULAJDON': ['sg'],
        'PENZ': ['sg'],
        'HITEL': ['sg'], 'HITELEK': ['pl'],
        'ADO': ['sg'], 'ADOK': ['pl'],
        'CSEL': ['sg'], 'CSALADOK': ['pl'],
        'EMBER': ['sg'], 'EMBREK': ['pl'],
        'FERFI': ['sg'], 'FERFIAK': ['pl'],
        'NO': ['sg'], 'NOK': ['pl'],
        'GYEREK': ['sg'], 'GYEREKEK': ['pl'],
        'CSALAD': ['sg'], 'CSALADOK': ['pl'],
        'HAZ': ['sg'], 'HAAK': ['pl'],
        'ISKOLA': ['sg'], 'ISKOLAK': ['pl'],
        'MUNKA': ['sg'], 'MUNKAK': ['pl'],
        'KOZSEG': ['sg'], 'KOZSEGEK': ['pl'],
        'VAROS': ['sg'], 'VAROSOK': ['pl'],
        'ORSZAG': ['sg'], 'ORSZAGOK': ['pl'],
        'VILAG': ['sg'],
        'IDO': ['sg'],
        'EV': ['sg'], 'EVEK': ['pl'],
        'NAP': ['sg'], 'NAPOK': ['pl'],
        'VIZ': ['sg'],
        'KENYER': ['sg'],
        'AUTO': ['sg'], 'AUTOK': ['pl'],
        'KONYV': ['sg'], 'KONYVEK': ['pl'],
        'KUTYA': ['sg'], 'KUTYAK': ['pl'],
        'MACSKA': ['sg'], 'MACSKAK': ['pl'],
        'FA': ['sg'], 'FAK': ['pl'],
        'HEGY': ['sg'], 'HEGYEK': ['pl'],
        'FOLYO': ['sg'], 'FOLYOK': ['pl'],
        'TAV': ['sg'], 'TAVAK': ['pl'],
        'NEV': ['sg'], 'NEVEK': ['pl'],
        'SZO': ['sg'], 'SZAVAK': ['pl'],
        'NYELV': ['sg'], 'NYELEK': ['pl'],
        'PELDAT': ['sg'], 'PELDATOK': ['pl'],
        'VALASZ': ['sg'], 'VALASZOK': ['pl'],
        'KERDES': ['sg'], 'KERDESEK': ['pl'],
        'OK': ['sg'], 'OKOK': ['pl'],
        'ERTEK': ['sg'], 'ERTEKEK': ['pl'],
        'JOGSZABALY': ['sg'], 'JOGSZABALYOK': ['pl'],
        'ALKOTMANY': ['sg'],
        'KOTELEZETTSEG': ['sg'], 'KOTELEZETTSEGEK': ['pl'],
        'JOGOSULTSAG': ['sg'], 'JOGOSULTSAGOK': ['pl'],
        'FELELOSSEG': ['sg'],
        'BUNTETO': ['sg'],
        'POLGARI': ['sg'],
        'KOZIGAZGATAS': ['sg'],
        'ALKOTAS': ['sg'], 'ALKOTASOK': ['pl'],
        'TUDOMANY': ['sg'],
        'TECHNIKA': ['sg'],
        'KULTURA': ['sg'], 'KULTURAK': ['pl'],
    }

    for word, tags in NOUNS.items():
        word_clean = clean_hungarian(word)
        if word_clean:
            data[word_clean]['N'].append((word_clean, ['N', 'NOM'] + tags))

    # Common verbs
    COMMON_VERBS = {
        'VAN': [
            ('VAGYOK', ['V', 'IND', 'PRS', 'INDEF', '1', 'SG']),
            ('VAGY', ['V', 'IND', 'PRS', 'INDEF', '2', 'SG']),
            ('VAN', ['V', 'IND', 'PRS', 'INDEF', '3', 'SG']),
            ('VAGYUNK', ['V', 'IND', 'PRS', 'INDEF', '1', 'PL']),
            ('VAGYTOK', ['V', 'IND', 'PRS', 'INDEF', '2', 'PL']),
            ('VANNAK', ['V', 'IND', 'PRS', 'INDEF', '3', 'PL']),
            ('VOLTAM', ['V', 'IND', 'PST', 'INDEF', '1', 'SG']),
            ('VOLTAL', ['V', 'IND', 'PST', 'INDEF', '2', 'SG']),
            ('VOLT', ['V', 'IND', 'PST', 'INDEF', '3', 'SG']),
            ('VOLTUNK', ['V', 'IND', 'PST', 'INDEF', '1', 'PL']),
            ('VOLTATOK', ['V', 'IND', 'PST', 'INDEF', '2', 'PL']),
            ('VOLTAK', ['V', 'IND', 'PST', 'INDEF', '3', 'PL']),
            ('LESZEK', ['V', 'IND', 'FUT', 'INDEF', '1', 'SG']),
            ('LESZEL', ['V', 'IND', 'FUT', 'INDEF', '2', 'SG']),
            ('LESZ', ['V', 'IND', 'FUT', 'INDEF', '3', 'SG']),
            ('LESZUNK', ['V', 'IND', 'FUT', 'INDEF', '1', 'PL']),
            ('LESZTEK', ['V', 'IND', 'FUT', 'INDEF', '2', 'PL']),
            ('LESZNEK', ['V', 'IND', 'FUT', 'INDEF', '3', 'PL']),
            ('LENNI', ['V', 'NFIN']),
        ],
        'TESZ': [
            ('TESZEK', ['V', 'IND', 'PRS', 'INDEF', '1', 'SG']),
            ('TESZEL', ['V', 'IND', 'PRS', 'INDEF', '2', 'SG']),
            ('TESZ', ['V', 'IND', 'PRS', 'INDEF', '3', 'SG']),
            ('TESZUNK', ['V', 'IND', 'PRS', 'INDEF', '1', 'PL']),
            ('TESZTEK', ['V', 'IND', 'PRS', 'INDEF', '2', 'PL']),
            ('TESZNEK', ['V', 'IND', 'PRS', 'INDEF', '3', 'PL']),
            ('TESZEM', ['V', 'IND', 'PRS', 'DEF', '1', 'SG']),
            ('TESZED', ['V', 'IND', 'PRS', 'DEF', '2', 'SG']),
            ('TESZI', ['V', 'IND', 'PRS', 'DEF', '3', 'SG']),
            ('TESZUK', ['V', 'IND', 'PRS', 'DEF', '1', 'PL']),
            ('TESZITEK', ['V', 'IND', 'PRS', 'DEF', '2', 'PL']),
            ('TESZIK', ['V', 'IND', 'PRS', 'DEF', '3', 'PL']),
            ('TETTEM', ['V', 'IND', 'PST', 'INDEF', '1', 'SG']),
            ('TETTEL', ['V', 'IND', 'PST', 'INDEF', '2', 'SG']),
            ('TETT', ['V', 'IND', 'PST', 'INDEF', '3', 'SG']),
            ('TENNI', ['V', 'NFIN']),
        ],
        'JON': [
            ('JOVOK', ['V', 'IND', 'PRS', 'INDEF', '1', 'SG']),
            ('JOSZ', ['V', 'IND', 'PRS', 'INDEF', '2', 'SG']),
            ('JON', ['V', 'IND', 'PRS', 'INDEF', '3', 'SG']),
            ('JOVUNK', ['V', 'IND', 'PRS', 'INDEF', '1', 'PL']),
            ('JOTTEK', ['V', 'IND', 'PST', 'INDEF', '3', 'PL']),
            ('JONNI', ['V', 'NFIN']),
        ],
        'MEGY': [
            ('MEGYEK', ['V', 'IND', 'PRS', 'INDEF', '1', 'SG']),
            ('MENSZ', ['V', 'IND', 'PRS', 'INDEF', '2', 'SG']),
            ('MEGY', ['V', 'IND', 'PRS', 'INDEF', '3', 'SG']),
            ('MEGYUNK', ['V', 'IND', 'PRS', 'INDEF', '1', 'PL']),
            ('MENTEM', ['V', 'IND', 'PST', 'INDEF', '1', 'SG']),
            ('MENT', ['V', 'IND', 'PST', 'INDEF', '3', 'SG']),
            ('MENNI', ['V', 'NFIN']),
        ],
        'MOND': [
            ('MONDOK', ['V', 'IND', 'PRS', 'INDEF', '1', 'SG']),
            ('MONDASZ', ['V', 'IND', 'PRS', 'INDEF', '2', 'SG']),
            ('MOND', ['V', 'IND', 'PRS', 'INDEF', '3', 'SG']),
            ('MONDOM', ['V', 'IND', 'PRS', 'DEF', '1', 'SG']),
            ('MONDOD', ['V', 'IND', 'PRS', 'DEF', '2', 'SG']),
            ('MONDJA', ['V', 'IND', 'PRS', 'DEF', '3', 'SG']),
            ('MONDTAM', ['V', 'IND', 'PST', 'INDEF', '1', 'SG']),
            ('MONDTAM', ['V', 'IND', 'PST', 'DEF', '1', 'SG']),
            ('MONDANI', ['V', 'NFIN']),
        ],
        'TUD': [
            ('TUDOK', ['V', 'IND', 'PRS', 'INDEF', '1', 'SG']),
            ('TUDSZ', ['V', 'IND', 'PRS', 'INDEF', '2', 'SG']),
            ('TUD', ['V', 'IND', 'PRS', 'INDEF', '3', 'SG']),
            ('TUDOM', ['V', 'IND', 'PRS', 'DEF', '1', 'SG']),
            ('TUDOD', ['V', 'IND', 'PRS', 'DEF', '2', 'SG']),
            ('TUDJA', ['V', 'IND', 'PRS', 'DEF', '3', 'SG']),
            ('TUDNI', ['V', 'NFIN']),
        ],
        'AKAR': [
            ('AKAROK', ['V', 'IND', 'PRS', 'INDEF', '1', 'SG']),
            ('AKARSZ', ['V', 'IND', 'PRS', 'INDEF', '2', 'SG']),
            ('AKAR', ['V', 'IND', 'PRS', 'INDEF', '3', 'SG']),
            ('AKAROM', ['V', 'IND', 'PRS', 'DEF', '1', 'SG']),
            ('AKAROD', ['V', 'IND', 'PRS', 'DEF', '2', 'SG']),
            ('AKARJA', ['V', 'IND', 'PRS', 'DEF', '3', 'SG']),
            ('AKARNI', ['V', 'NFIN']),
        ],
        'KELL': [
            ('KELL', ['V', 'IND', 'PRS', 'INDEF', '3', 'SG']),
            ('KELLETT', ['V', 'IND', 'PST', 'INDEF', '3', 'SG']),
            ('KELLNI', ['V', 'NFIN']),
        ],
        'LEHET': [
            ('LEHET', ['V', 'IND', 'PRS', 'INDEF', '3', 'SG']),
            ('LEHETETT', ['V', 'IND', 'PST', 'INDEF', '3', 'SG']),
        ],
    }

    for lemma, forms in COMMON_VERBS.items():
        lemma_clean = clean_hungarian(lemma)
        if not lemma_clean:
            continue
        for form_raw, tags in forms:
            form_clean = clean_hungarian(form_raw)
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

            # Sort: prefer exact lemma match, then inf, then shortest
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

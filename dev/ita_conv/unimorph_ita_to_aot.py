import json
import os
import sys
from collections import defaultdict
from datetime import datetime


POS_MAP = {
    'N': 'NOUN',
    'V': 'VERB',
    'V.CVB': 'VERB',
    'V.PTCP': 'VERB',
    'ADJ': 'ADJ',
    'ADV': 'ADV',
    'PRON': 'PRON',
    'PREP': 'PREP',
    'CONJ': 'CONJ',
    'INTJ': 'INT',
    'NUM': 'NUM',
    'PART': 'PART',
    'PROPN': 'PROPN',
    'DET': 'DET',
}

TAG_MAP = {
    'SG': 'sg', 'PL': 'pl',
    'MASC': 'masc', 'FEM': 'fem',
    'NOM': 'nom', 'ACC': 'acc', 'DAT': 'dat', 'GEN': 'gen',
    'PRS': 'pres', 'PST': 'past', 'FUT': 'fut',
    'IPFV': 'impf', 'PFV': 'pfv',
    'IND': 'ind', 'SBJV': 'sbjv', 'IMP': 'impv', 'COND': 'cond',
    '1': 'p1', '2': 'p2', '3': 'p3',
    'NFIN': 'inf', 'INF': 'inf',
    'POS': 'pos',
    'ACT': 'act', 'PASS': 'pass',
}

SKIP_TAGS = set()


def clean_italian(text):
    t = text.upper()
    replacements = {
        'À': 'A', 'Á': 'A',
        'È': 'E', 'É': 'E',
        'Ì': 'I', 'Í': 'I',
        'Ò': 'O', 'Ó': 'O',
        'Ù': 'U', 'Ú': 'U',
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
    input_file = 'Dicts/Morph/Italian/unimorph/ita'
    output_morphs = 'Source/morph_dict/data/Italian/morphs.json'
    output_gramtab = 'Source/morph_dict/data/Italian/gramtab.json'

    gramtab = {"gramcodes": {}}
    gram_to_code = {}
    next_code_idx = 0

    def get_gramcode(pos, tags, lemma=None):
        nonlocal next_code_idx

        if pos in ('V.PTCP', 'V.CVB'):
            aot_pos = 'VERB'
        else:
            aot_pos = POS_MAP.get(pos)
        if not aot_pos:
            return None

        aot_tags = []
        if pos == 'V.PTCP':
            aot_tags.append('ptcp')
        if pos == 'V.CVB':
            aot_tags.append('ger')

        for t in tags:
            if t in SKIP_TAGS:
                continue
            mapped = TAG_MAP.get(t)
            if mapped is None:
                continue
            if mapped and mapped not in aot_tags:
                aot_tags.append(mapped)

        if aot_pos in ('NOUN', 'ADJ', 'PRON', 'DET', 'NUM'):
            if 'sg' not in aot_tags and 'pl' not in aot_tags:
                aot_tags.append('sg')
            if 'masc' not in aot_tags and 'fem' not in aot_tags:
                aot_tags.append('masc')

        if aot_pos == 'VERB' and 'ptcp' not in aot_tags and 'ger' not in aot_tags and 'inf' not in aot_tags:
            if 'ind' not in aot_tags and 'sbjv' not in aot_tags and 'impv' not in aot_tags and 'cond' not in aot_tags:
                aot_tags.append('ind')

        if aot_pos == 'VERB' and 'pos' not in aot_tags:
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

            lemma_clean = clean_italian(lemma_raw)
            word_clean = clean_italian(word_raw)
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

    # Closed-class words
    CLOSED_CLASS = {
        'IL': [('DET', ['masc', 'sg'])],
        'LO': [('DET', ['masc', 'sg']), ('PRON', ['p3', 'sg', 'masc'])],
        'LA': [('DET', ['fem', 'sg']), ('PRON', ['p3', 'sg', 'fem'])],
        'I': [('DET', ['masc', 'pl'])],
        'GLI': [('DET', ['masc', 'pl']), ('PRON', ['p3', 'pl', 'masc'])],
        'LE': [('DET', ['fem', 'pl']), ('PRON', ['p3', 'pl', 'fem'])],
        'UN': [('DET', ['masc', 'sg'])],
        'UNO': [('DET', ['masc', 'sg']), ('NUM', ['masc', 'sg'])],
        'UNA': [('DET', ['fem', 'sg'])],
        'IO': [('PRON', ['p1', 'sg'])],
        'TU': [('PRON', ['p2', 'sg'])],
        'LUI': [('PRON', ['p3', 'sg', 'masc'])],
        'LEI': [('PRON', ['p3', 'sg', 'fem'])],
        'NOI': [('PRON', ['p1', 'pl'])],
        'VOI': [('PRON', ['p2', 'pl'])],
        'LORO': [('PRON', ['p3', 'pl'])],
        'MI': [('PRON', ['p1', 'sg'])],
        'TI': [('PRON', ['p2', 'sg'])],
        'SI': [('PRON', ['p3']), ('PART', [])],
        'CI': [('PRON', ['p1', 'pl'])],
        'VI': [('PRON', ['p2', 'pl'])],
        'LI': [('PRON', ['p3', 'pl', 'masc'])],
        'QUESTO': [('PRON', ['masc', 'sg']), ('DET', ['masc', 'sg'])],
        'QUESTA': [('PRON', ['fem', 'sg']), ('DET', ['fem', 'sg'])],
        'QUELLO': [('PRON', ['masc', 'sg']), ('DET', ['masc', 'sg'])],
        'QUELLA': [('PRON', ['fem', 'sg']), ('DET', ['fem', 'sg'])],
        'QUEI': [('DET', ['masc', 'pl'])],
        'QUELLE': [('DET', ['fem', 'pl'])],
        'CHE': [('PRON', []), ('CONJ', [])],
        'CHI': [('PRON', [])],
        'CUI': [('PRON', [])],
        'QUALE': [('PRON', ['masc', 'sg'])],
        'QUALI': [('PRON', ['pl'])],
        'E': [('CONJ', [])],
        'ED': [('CONJ', [])],
        'O': [('CONJ', [])],
        'OD': [('CONJ', [])],
        'MA': [('CONJ', [])],
        'PERO': [('CONJ', [])],
        'QUINDI': [('CONJ', [])],
        'PERCHE': [('CONJ', [])],
        'SE': [('CONJ', [])],
        'SEBBENE': [('CONJ', [])],
        'ANCHE': [('CONJ', [])],
        'MENTRE': [('CONJ', [])],
        'POICHE': [('CONJ', [])],
        'BENCHE': [('CONJ', [])],
        'TUTTAVIA': [('CONJ', [])],
        'INOLTRE': [('CONJ', [])],
        'OSSIA': [('CONJ', [])],
        'CIOE': [('CONJ', [])],
        'DUNQUE': [('CONJ', [])],
        'DI': [('PREP', [])],
        'A': [('PREP', [])],
        'DA': [('PREP', [])],
        'IN': [('PREP', [])],
        'CON': [('PREP', [])],
        'SU': [('PREP', [])],
        'PER': [('PREP', [])],
        'TRA': [('PREP', [])],
        'FRA': [('PREP', [])],
        'SENZA': [('PREP', [])],
        'SOPRA': [('PREP', [])],
        'SOTTO': [('PREP', [])],
        'CONTRO': [('PREP', [])],
        'DOPO': [('PREP', [])],
        'PRIMA': [('PREP', [])],
        'DURANTE': [('PREP', [])],
        'VERSO': [('PREP', [])],
        'NON': [('PART', []), ('ADV', [])],
        'PIU': [('ADV', [])],
        'MOLTO': [('ADV', [])],
        'BENE': [('ADV', [])],
        'MALE': [('ADV', [])],
        'ANCORA': [('ADV', [])],
        'SEMPRE': [('ADV', [])],
        'SOLO': [('ADV', [])],
        'FORSE': [('ADV', [])],
        'QUI': [('ADV', [])],
        'ORA': [('ADV', [])],
        'ALLORA': [('ADV', [])],
        'OGGI': [('ADV', [])],
        'IERI': [('ADV', [])],
        'DOMANI': [('ADV', [])],
        'OLTRE': [('ADV', [])],
        'NO': [('ADV', [])],
        'SI-ADV': [('ADV', [])],
        'GIÀ': [('ADV', [])],
    }

    # Common nouns
    NOUNS = {
        'DIRITTO': ('masc', 'sg'), 'DIRITTI': ('masc', 'pl'),
        'LEGGE': ('fem', 'sg'), 'LEGGI': ('fem', 'pl'),
        'CONTRATTO': ('masc', 'sg'), 'CONTRATTI': ('masc', 'pl'),
        'PARTE': ('fem', 'sg'), 'PARTI': ('fem', 'pl'),
        'GIUDICE': ('masc', 'sg'),
        'TRIBUNALE': ('masc', 'sg'), 'TRIBUNALI': ('masc', 'pl'),
        'CITTADINO': ('masc', 'sg'), 'CITTADINI': ('masc', 'pl'),
        'STATO': ('masc', 'sg'), 'STATI': ('masc', 'pl'),
        'PERSONA': ('fem', 'sg'), 'PERSONE': ('fem', 'pl'),
        'CASO': ('masc', 'sg'), 'CASI': ('masc', 'pl'),
        'DOCUMENTO': ('masc', 'sg'), 'DOCUMENTI': ('masc', 'pl'),
        'ARTICOLO': ('masc', 'sg'), 'ARTICOLI': ('masc', 'pl'),
        'OBBLIGO': ('masc', 'sg'),
        'UOMO': ('masc', 'sg'), 'UOMINI': ('masc', 'pl'),
        'DONNA': ('fem', 'sg'), 'DONNE': ('fem', 'pl'),
        'CASA': ('fem', 'sg'), 'CASE': ('fem', 'pl'),
        'LIBRO': ('masc', 'sg'), 'LIBRI': ('masc', 'pl'),
        'NOTA': ('fem', 'sg'), 'NOTE': ('fem', 'pl'),
        'GIORNO': ('masc', 'sg'), 'GIORNI': ('masc', 'pl'),
        'ANNO': ('masc', 'sg'), 'ANNI': ('masc', 'pl'),
        'TEMPO': ('masc', 'sg'), 'TEMPI': ('masc', 'pl'),
        'VITA': ('fem', 'sg'), 'VITE': ('fem', 'pl'),
        'MODI': ('masc', 'pl'), 'MODO': ('masc', 'sg'),
        'LUOGO': ('masc', 'sg'), 'LUOGHI': ('masc', 'pl'),
        'CITTA': ('fem', 'sg'), 'CITTÀ': ('fem', 'sg'),
        'MONDO': ('masc', 'sg'), 'MONDI': ('masc', 'pl'),
        'NOME': ('masc', 'sg'), 'NOMI': ('masc', 'pl'),
        'ACQUA': ('fem', 'sg'), 'ACQUE': ('fem', 'pl'),
        'SCUOLA': ('fem', 'sg'), 'SCUOLE': ('fem', 'pl'),
        'LAVORO': ('masc', 'sg'), 'LAVORI': ('masc', 'pl'),
        'PRESIDENTE': ('masc', 'sg'),
        'MINISTRO': ('masc', 'sg'),
        'GOVERNO': ('masc', 'sg'),
        'CORTO': ('masc', 'sg'),
        'POTERE': ('masc', 'sg'),
        'CAUSA': ('fem', 'sg'), 'CAUSE': ('fem', 'pl'),
        'FATTO': ('masc', 'sg'), 'FATTI': ('masc', 'pl'),
        'RAPPORTO': ('masc', 'sg'),
        'DECISIONE': ('fem', 'sg'),
        'PROVVEDIMENTO': ('masc', 'sg'),
        'SENTENZA': ('fem', 'sg'), 'SENTENZE': ('fem', 'pl'),
        'NORMA': ('fem', 'sg'), 'NORME': ('fem', 'pl'),
        'PRINCIPIO': ('masc', 'sg'),
        'DIRITTO-DIR': ('masc', 'sg'),
        'PESCE': ('masc', 'sg'), 'PESCI': ('masc', 'pl'),
        'GATTO': ('masc', 'sg'), 'GATTI': ('masc', 'pl'),
        'PIZZA': ('fem', 'sg'), 'PIZZE': ('fem', 'pl'),
        'ACQUA': ('fem', 'sg'), 'ACQUE': ('fem', 'pl'),
        'AMICO': ('masc', 'sg'), 'AMICI': ('masc', 'pl'),
        'AMICA': ('fem', 'sg'), 'AMICHE': ('fem', 'pl'),
        'FIGLIO': ('masc', 'sg'), 'FIGLI': ('masc', 'pl'),
        'FIGLIA': ('fem', 'sg'), 'FIGLIE': ('fem', 'pl'),
        'PADRE': ('masc', 'sg'), 'PADRI': ('masc', 'pl'),
        'MADRE': ('fem', 'sg'), 'MADRI': ('fem', 'pl'),
        'FRATELLO': ('masc', 'sg'), 'FRATELLI': ('masc', 'pl'),
        'SORA': ('fem', 'sg'), 'SORELLE': ('fem', 'pl'),
        'SCUOLA': ('fem', 'sg'), 'SCUOLE': ('fem', 'pl'),
        'MAESTRO': ('masc', 'sg'), 'MAESTRI': ('masc', 'pl'),
        'PAESE': ('masc', 'sg'), 'PAESI': ('masc', 'pl'),
        'CIBO': ('masc', 'sg'),
        'VINO': ('masc', 'sg'), 'VINI': ('masc', 'pl'),
        'NOTTE': ('fem', 'sg'), 'NOTTI': ('fem', 'pl'),
        'MATINA': ('fem', 'sg'), 'MATTINE': ('fem', 'pl'),
        'SERATA': ('fem', 'sg'),
        'MACCHINA': ('fem', 'sg'), 'MACCHINE': ('fem', 'pl'),
        'STRADA': ('fem', 'sg'), 'STRADE': ('fem', 'pl'),
        'PIAZZA': ('fem', 'sg'), 'PIAZZE': ('fem', 'pl'),
        'PENSIERO': ('masc', 'sg'), 'PENSIERI': ('masc', 'pl'),
        'PAROLA': ('fem', 'sg'), 'PAROLE': ('fem', 'pl'),
        'LINGUA': ('fem', 'sg'), 'LINGUE': ('fem', 'pl'),
        'SCUOLA': ('fem', 'sg'), 'SCUOLE': ('fem', 'pl'),
        'RAGAZZO': ('masc', 'sg'), 'RAGAZZI': ('masc', 'pl'),
        'RAGAZZA': ('fem', 'sg'), 'RAGAZZE': ('fem', 'pl'),
        'BAMBINO': ('masc', 'sg'), 'BAMBINI': ('masc', 'pl'),
        'BAMBINA': ('fem', 'sg'), 'BAMINE': ('fem', 'pl'),
        'SIGNORE': ('masc', 'sg'),
        'SIGNORA': ('fem', 'sg'), 'SIGNORE': ('fem', 'pl'),
        'DOTTORE': ('masc', 'sg'),
        'PROFESSORE': ('masc', 'sg'), 'PROFESSORI': ('masc', 'pl'),
        'CANZONE': ('fem', 'sg'), 'CANZONI': ('fem', 'pl'),
        'CUORE': ('masc', 'sg'),
        'OCCHIO': ('masc', 'sg'), 'OCCHI': ('masc', 'pl'),
        'MANO': ('fem', 'sg'), 'MANI': ('fem', 'pl'),
        'TESTA': ('fem', 'sg'),
        'FIORE': ('masc', 'sg'), 'FIORI': ('masc', 'pl'),
        'SOLE': ('masc', 'sg'),
        'LUNA': ('fem', 'sg'),
        'CIELO': ('masc', 'sg'), 'CIELI': ('masc', 'pl'),
        'TERRA': ('fem', 'sg'),
        'MARE': ('masc', 'sg'), 'MARI': ('masc', 'pl'),
        'CAMPO': ('masc', 'sg'), 'CAMPI': ('masc', 'pl'),
        'PORTA': ('fem', 'sg'), 'PORTE': ('fem', 'pl'),
        'TAVOLO': ('masc', 'sg'), 'TAVOLI': ('masc', 'pl'),
        'SEDIA': ('fem', 'sg'), 'SEDIE': ('fem', 'pl'),
        'FINISTRA': ('fem', 'sg'), 'FINESTRE': ('fem', 'pl'),
    }

    for word, (gender, number) in NOUNS.items():
        word_clean = clean_italian(word)
        if word_clean:
            data[word_clean]['N'].append((word_clean, ['N', gender.upper(), number.upper()]))

    # Common adjectives
    ADJS = {
        'NUOVO': [('NUOVO', 'masc', 'sg'), ('NUOVA', 'fem', 'sg'), ('NUOVI', 'masc', 'pl'), ('NUOVE', 'fem', 'pl')],
        'PRIMO': [('PRIMO', 'masc', 'sg'), ('PRIMA', 'fem', 'sg'), ('PRIMI', 'masc', 'pl'), ('PRIME', 'fem', 'pl')],
        'ULTIMO': [('ULTIMO', 'masc', 'sg'), ('ULTIMA', 'fem', 'sg'), ('ULTIMI', 'masc', 'pl'), ('ULTIME', 'fem', 'pl')],
        'TUTTO': [('TUTTO', 'masc', 'sg'), ('TUTTA', 'fem', 'sg'), ('TUTTI', 'masc', 'pl'), ('TUTTE', 'fem', 'pl')],
        'GRANDE': [('GRANDE', 'masc', 'sg'), ('GRANDE', 'fem', 'sg'), ('GRANDI', 'masc', 'pl'), ('GRANDI', 'fem', 'pl')],
        'PICCOLO': [('PICCOLO', 'masc', 'sg'), ('PICCOLA', 'fem', 'sg'), ('PICCOLI', 'masc', 'pl'), ('PICCOLE', 'fem', 'pl')],
        'BUONO': [('BUONO', 'masc', 'sg'), ('BUONA', 'fem', 'sg'), ('BUONI', 'masc', 'pl'), ('BUONE', 'fem', 'pl')],
        'ALTO': [('ALTO', 'masc', 'sg'), ('ALTA', 'fem', 'sg'), ('ALTI', 'masc', 'pl'), ('ALTE', 'fem', 'pl')],
        'BASSO': [('BASSO', 'masc', 'sg'), ('BASSA', 'fem', 'sg'), ('BASSI', 'masc', 'pl'), ('BASSE', 'fem', 'pl')],
        'LUNGO': [('LUNGO', 'masc', 'sg'), ('LUNGA', 'fem', 'sg'), ('LUNGHI', 'masc', 'pl'), ('LUNGHE', 'fem', 'pl')],
        'BELLO': [('BELLO', 'masc', 'sg'), ('BELLA', 'fem', 'sg'), ('BELLI', 'masc', 'pl'), ('BELLE', 'fem', 'pl')],
        'ITALIANO': [('ITALIANO', 'masc', 'sg'), ('ITALIANA', 'fem', 'sg'), ('ITALIANI', 'masc', 'pl'), ('ITALIANE', 'fem', 'pl')],
    }

    for lemma, forms in ADJS.items():
        lemma_clean = clean_italian(lemma)
        if not lemma_clean:
            continue
        for form, gender, number in forms:
            form_clean = clean_italian(form)
            if form_clean:
                data[lemma_clean]['ADJ'].append((form_clean, ['ADJ', gender.upper(), number.upper()]))

    for word, entries in CLOSED_CLASS.items():
        word_clean = clean_italian(word)
        if not word_clean:
            continue
        for pos, tags in entries:
            data[word_clean][pos].append((word_clean, [pos] + tags))

    # Italian auxiliary and common verb conjugations (manually added)
    # Format: lemma -> list of (form, tags)
    COMMON_VERBS = {
        'ESSERE': [
            ('SONO', ['V', 'IND', 'PRS', '1', 'SG']),
            ('SEI', ['V', 'IND', 'PRS', '2', 'SG']),
            ('E', ['V', 'IND', 'PRS', '3', 'SG']),
            ('SIAMO', ['V', 'IND', 'PRS', '1', 'PL']),
            ('SIETE', ['V', 'IND', 'PRS', '2', 'PL']),
            ('SONO', ['V', 'IND', 'PRS', '3', 'PL']),
            ('ERO', ['V', 'IND', 'PST', '1', 'SG', 'IPFV']),
            ('ERI', ['V', 'IND', 'PST', '2', 'SG', 'IPFV']),
            ('ERA', ['V', 'IND', 'PST', '3', 'SG', 'IPFV']),
            ('ERAVAMO', ['V', 'IND', 'PST', '1', 'PL', 'IPFV']),
            ('ERAVATE', ['V', 'IND', 'PST', '2', 'PL', 'IPFV']),
            ('ERANO', ['V', 'IND', 'PST', '3', 'PL', 'IPFV']),
            ('FUI', ['V', 'IND', 'PST', '1', 'SG', 'PFV']),
            ('FOSTI', ['V', 'IND', 'PST', '2', 'SG', 'PFV']),
            ('FU', ['V', 'IND', 'PST', '3', 'SG', 'PFV']),
            ('FUMMO', ['V', 'IND', 'PST', '1', 'PL', 'PFV']),
            ('FOSTE', ['V', 'IND', 'PST', '2', 'PL', 'PFV']),
            ('FURONO', ['V', 'IND', 'PST', '3', 'PL', 'PFV']),
            ('SARO', ['V', 'IND', 'FUT', '1', 'SG']),
            ('SARAI', ['V', 'IND', 'FUT', '2', 'SG']),
            ('SARA', ['V', 'IND', 'FUT', '3', 'SG']),
            ('SAREMO', ['V', 'IND', 'FUT', '1', 'PL']),
            ('SARETE', ['V', 'IND', 'FUT', '2', 'PL']),
            ('SARANNO', ['V', 'IND', 'FUT', '3', 'PL']),
            ('SIA', ['V', 'SBJV', 'PRS', '1', 'SG']),
            ('SIA', ['V', 'SBJV', 'PRS', '3', 'SG']),
            ('SIAMO', ['V', 'SBJV', 'PRS', '1', 'PL']),
            ('SIATE', ['V', 'SBJV', 'PRS', '2', 'PL']),
            ('SIANO', ['V', 'SBJV', 'PRS', '3', 'PL']),
            ('SAREI', ['V', 'COND', '1', 'SG']),
            ('SARESTI', ['V', 'COND', '2', 'SG']),
            ('SAREBBE', ['V', 'COND', '3', 'SG']),
            ('SAREMMO', ['V', 'COND', '1', 'PL']),
            ('SARESTE', ['V', 'COND', '2', 'PL']),
            ('SAREBBERO', ['V', 'COND', '3', 'PL']),
            ('ESSERE', ['V', 'NFIN']),
            ('ESSENDO', ['V.CVB', 'PRS']),
            ('STATO', ['V.PTCP', 'PST']),
        ],
        'AVERE': [
            ('HO', ['V', 'IND', 'PRS', '1', 'SG']),
            ('HAI', ['V', 'IND', 'PRS', '2', 'SG']),
            ('HA', ['V', 'IND', 'PRS', '3', 'SG']),
            ('ABBIAMO', ['V', 'IND', 'PRS', '1', 'PL']),
            ('AVETE', ['V', 'IND', 'PRS', '2', 'PL']),
            ('HANNO', ['V', 'IND', 'PRS', '3', 'PL']),
            ('AVEVO', ['V', 'IND', 'PST', '1', 'SG', 'IPFV']),
            ('AVEVI', ['V', 'IND', 'PST', '2', 'SG', 'IPFV']),
            ('AVEVA', ['V', 'IND', 'PST', '3', 'SG', 'IPFV']),
            ('AVEVAMO', ['V', 'IND', 'PST', '1', 'PL', 'IPFV']),
            ('AVEVATE', ['V', 'IND', 'PST', '2', 'PL', 'IPFV']),
            ('AVEVANO', ['V', 'IND', 'PST', '3', 'PL', 'IPFV']),
            ('EBBI', ['V', 'IND', 'PST', '1', 'SG', 'PFV']),
            ('AVESTI', ['V', 'IND', 'PST', '2', 'SG', 'PFV']),
            ('EBBE', ['V', 'IND', 'PST', '3', 'SG', 'PFV']),
            ('AVEMMO', ['V', 'IND', 'PST', '1', 'PL', 'PFV']),
            ('AVESTE', ['V', 'IND', 'PST', '2', 'PL', 'PFV']),
            ('EBBERO', ['V', 'IND', 'PST', '3', 'PL', 'PFV']),
            ('AVRO', ['V', 'IND', 'FUT', '1', 'SG']),
            ('AVRAI', ['V', 'IND', 'FUT', '2', 'SG']),
            ('AVRA', ['V', 'IND', 'FUT', '3', 'SG']),
            ('AVREMO', ['V', 'IND', 'FUT', '1', 'PL']),
            ('AVRETE', ['V', 'IND', 'FUT', '2', 'PL']),
            ('AVRANNO', ['V', 'IND', 'FUT', '3', 'PL']),
            ('ABBIA', ['V', 'SBJV', 'PRS', '1', 'SG']),
            ('ABBIA', ['V', 'SBJV', 'PRS', '3', 'SG']),
            ('ABBIAMO', ['V', 'SBJV', 'PRS', '1', 'PL']),
            ('ABBIATE', ['V', 'SBJV', 'PRS', '2', 'PL']),
            ('ABBIANO', ['V', 'SBJV', 'PRS', '3', 'PL']),
            ('AVREI', ['V', 'COND', '1', 'SG']),
            ('AVRESTI', ['V', 'COND', '2', 'SG']),
            ('AVREBBE', ['V', 'COND', '3', 'SG']),
            ('AVREMMO', ['V', 'COND', '1', 'PL']),
            ('AVRESTE', ['V', 'COND', '2', 'PL']),
            ('AVREBBERO', ['V', 'COND', '3', 'PL']),
            ('AVERE', ['V', 'NFIN']),
            ('AVENDO', ['V.CVB', 'PRS']),
            ('AVUTO', ['V.PTCP', 'PST']),
        ],
        'MANGIARE': [
            ('MANGIO', ['V', 'IND', 'PRS', '1', 'SG']),
            ('MANGI', ['V', 'IND', 'PRS', '2', 'SG']),
            ('MANGIA', ['V', 'IND', 'PRS', '3', 'SG']),
            ('MANGIAMO', ['V', 'IND', 'PRS', '1', 'PL']),
            ('MANGIATE', ['V', 'IND', 'PRS', '2', 'PL']),
            ('MANGIANO', ['V', 'IND', 'PRS', '3', 'PL']),
            ('MANGIAVO', ['V', 'IND', 'PST', '1', 'SG', 'IPFV']),
            ('MANGIAVI', ['V', 'IND', 'PST', '2', 'SG', 'IPFV']),
            ('MANGIAVA', ['V', 'IND', 'PST', '3', 'SG', 'IPFV']),
            ('MANGIAVAMO', ['V', 'IND', 'PST', '1', 'PL', 'IPFV']),
            ('MANGIAVATE', ['V', 'IND', 'PST', '2', 'PL', 'IPFV']),
            ('MANGIAVANO', ['V', 'IND', 'PST', '3', 'PL', 'IPFV']),
            ('MANGIAI', ['V', 'IND', 'PST', '1', 'SG', 'PFV']),
            ('MANGIASTI', ['V', 'IND', 'PST', '2', 'SG', 'PFV']),
            ('MANGIO-PST3SG', ['V', 'IND', 'PST', '3', 'SG', 'PFV']),
            ('MANGIAMMO', ['V', 'IND', 'PST', '1', 'PL', 'PFV']),
            ('MANGIASTE', ['V', 'IND', 'PST', '2', 'PL', 'PFV']),
            ('MANGIARONO', ['V', 'IND', 'PST', '3', 'PL', 'PFV']),
            ('MANGIERO', ['V', 'IND', 'FUT', '1', 'SG']),
            ('MANGIERAI', ['V', 'IND', 'FUT', '2', 'SG']),
            ('MANGIERA', ['V', 'IND', 'FUT', '3', 'SG']),
            ('MANGIEREMO', ['V', 'IND', 'FUT', '1', 'PL']),
            ('MANGIERETE', ['V', 'IND', 'FUT', '2', 'PL']),
            ('MANGIERANNO', ['V', 'IND', 'FUT', '3', 'PL']),
            ('MANGI', ['V', 'SBJV', 'PRS', '1', 'SG']),
            ('MANGI', ['V', 'SBJV', 'PRS', '3', 'SG']),
            ('MANGIAMO', ['V', 'SBJV', 'PRS', '1', 'PL']),
            ('MANGIATE', ['V', 'SBJV', 'PRS', '2', 'PL']),
            ('MANGINO', ['V', 'SBJV', 'PRS', '3', 'PL']),
            ('MANGIAREI', ['V', 'COND', '1', 'SG']),
            ('MANGIERESTI', ['V', 'COND', '2', 'SG']),
            ('MANGIEREBBE', ['V', 'COND', '3', 'SG']),
            ('MANGIEREMMO', ['V', 'COND', '1', 'PL']),
            ('MANGIERESTE', ['V', 'COND', '2', 'PL']),
            ('MANGIEREBBERO', ['V', 'COND', '3', 'PL']),
            ('MANGIARE', ['V', 'NFIN']),
            ('MANGIANDO', ['V.CVB', 'PRS']),
            ('MANGIATO', ['V.PTCP', 'PST']),
        ],
        'FARE': [
            ('FACCIO', ['V', 'IND', 'PRS', '1', 'SG']),
            ('FAI', ['V', 'IND', 'PRS', '2', 'SG']),
            ('FA', ['V', 'IND', 'PRS', '3', 'SG']),
            ('FACCIAMO', ['V', 'IND', 'PRS', '1', 'PL']),
            ('FATE', ['V', 'IND', 'PRS', '2', 'PL']),
            ('FANNO', ['V', 'IND', 'PRS', '3', 'PL']),
            ('FACEVO', ['V', 'IND', 'PST', '1', 'SG', 'IPFV']),
            ('FACEVI', ['V', 'IND', 'PST', '2', 'SG', 'IPFV']),
            ('FACEVA', ['V', 'IND', 'PST', '3', 'SG', 'IPFV']),
            ('FACEVAMO', ['V', 'IND', 'PST', '1', 'PL', 'IPFV']),
            ('FACEVATE', ['V', 'IND', 'PST', '2', 'PL', 'IPFV']),
            ('FACEVANO', ['V', 'IND', 'PST', '3', 'PL', 'IPFV']),
            ('FECI', ['V', 'IND', 'PST', '1', 'SG', 'PFV']),
            ('FACESTI', ['V', 'IND', 'PST', '2', 'SG', 'PFV']),
            ('FECE', ['V', 'IND', 'PST', '3', 'SG', 'PFV']),
            ('FACEMMO', ['V', 'IND', 'PST', '1', 'PL', 'PFV']),
            ('FACESTE', ['V', 'IND', 'PST', '2', 'PL', 'PFV']),
            ('FECERO', ['V', 'IND', 'PST', '3', 'PL', 'PFV']),
            ('FARO', ['V', 'IND', 'FUT', '1', 'SG']),
            ('FARAI', ['V', 'IND', 'FUT', '2', 'SG']),
            ('FARA', ['V', 'IND', 'FUT', '3', 'SG']),
            ('FAREMO', ['V', 'IND', 'FUT', '1', 'PL']),
            ('FARETE', ['V', 'IND', 'FUT', '2', 'PL']),
            ('FARANNO', ['V', 'IND', 'FUT', '3', 'PL']),
            ('FAREI', ['V', 'COND', '1', 'SG']),
            ('FARESTI', ['V', 'COND', '2', 'SG']),
            ('FAREBBE', ['V', 'COND', '3', 'SG']),
            ('FARE', ['V', 'NFIN']),
            ('FACENDO', ['V.CVB', 'PRS']),
            ('FATTO', ['V.PTCP', 'PST']),
        ],
        'DIRE': [
            ('DICO', ['V', 'IND', 'PRS', '1', 'SG']),
            ('DICI', ['V', 'IND', 'PRS', '2', 'SG']),
            ('DICE', ['V', 'IND', 'PRS', '3', 'SG']),
            ('DICIAMO', ['V', 'IND', 'PRS', '1', 'PL']),
            ('DITE', ['V', 'IND', 'PRS', '2', 'PL']),
            ('DICONO', ['V', 'IND', 'PRS', '3', 'PL']),
            ('DICEVO', ['V', 'IND', 'PST', '1', 'SG', 'IPFV']),
            ('DICEVI', ['V', 'IND', 'PST', '2', 'SG', 'IPFV']),
            ('DICEVA', ['V', 'IND', 'PST', '3', 'SG', 'IPFV']),
            ('DISSE', ['V', 'IND', 'PST', '3', 'SG', 'PFV']),
            ('DISSERO', ['V', 'IND', 'PST', '3', 'PL', 'PFV']),
            ('DIRE', ['V', 'NFIN']),
            ('DICENDO', ['V.CVB', 'PRS']),
            ('DETTO', ['V.PTCP', 'PST']),
        ],
        'POTERE': [
            ('POSSO', ['V', 'IND', 'PRS', '1', 'SG']),
            ('PUOI', ['V', 'IND', 'PRS', '2', 'SG']),
            ('PUO', ['V', 'IND', 'PRS', '3', 'SG']),
            ('POTIAMO', ['V', 'IND', 'PRS', '1', 'PL']),
            ('POTETE', ['V', 'IND', 'PRS', '2', 'PL']),
            ('POSSONO', ['V', 'IND', 'PRS', '3', 'PL']),
            ('POTEVO', ['V', 'IND', 'PST', '1', 'SG', 'IPFV']),
            ('POTEVI', ['V', 'IND', 'PST', '2', 'SG', 'IPFV']),
            ('POTEVA', ['V', 'IND', 'PST', '3', 'SG', 'IPFV']),
            ('POTETTI', ['V', 'IND', 'PST', '1', 'SG', 'PFV']),
            ('POTE', ['V', 'IND', 'PST', '3', 'SG', 'PFV']),
            ('POTREI', ['V', 'COND', '1', 'SG']),
            ('POTRESTI', ['V', 'COND', '2', 'SG']),
            ('POTREBBE', ['V', 'COND', '3', 'SG']),
            ('POTRO', ['V', 'IND', 'FUT', '1', 'SG']),
            ('POTRAI', ['V', 'IND', 'FUT', '2', 'SG']),
            ('POTRA', ['V', 'IND', 'FUT', '3', 'SG']),
            ('POTERE', ['V', 'NFIN']),
            ('POTENDO', ['V.CVB', 'PRS']),
            ('POTUTO', ['V.PTCP', 'PST']),
        ],
        'DOVERE': [
            ('DEVO', ['V', 'IND', 'PRS', '1', 'SG']),
            ('DEVI', ['V', 'IND', 'PRS', '2', 'SG']),
            ('DEVE', ['V', 'IND', 'PRS', '3', 'SG']),
            ('DOBBIAMO', ['V', 'IND', 'PRS', '1', 'PL']),
            ('DOVETE', ['V', 'IND', 'PRS', '2', 'PL']),
            ('DEVONO', ['V', 'IND', 'PRS', '3', 'PL']),
            ('DOVEVO', ['V', 'IND', 'PST', '1', 'SG', 'IPFV']),
            ('DOVEVI', ['V', 'IND', 'PST', '2', 'SG', 'IPFV']),
            ('DOVEVA', ['V', 'IND', 'PST', '3', 'SG', 'IPFV']),
            ('DOVETTI', ['V', 'IND', 'PST', '1', 'SG', 'PFV']),
            ('DOVETTE', ['V', 'IND', 'PST', '3', 'SG', 'PFV']),
            ('DOVRO', ['V', 'IND', 'FUT', '1', 'SG']),
            ('DOVRAI', ['V', 'IND', 'FUT', '2', 'SG']),
            ('DOVRA', ['V', 'IND', 'FUT', '3', 'SG']),
            ('DOVREI', ['V', 'COND', '1', 'SG']),
            ('DOVRESTI', ['V', 'COND', '2', 'SG']),
            ('DOVREBBE', ['V', 'COND', '3', 'SG']),
            ('DOVERE', ['V', 'NFIN']),
            ('DOVENDO', ['V.CVB', 'PRS']),
            ('DOVUTO', ['V.PTCP', 'PST']),
        ],
        'VOLERE': [
            ('VOGLIO', ['V', 'IND', 'PRS', '1', 'SG']),
            ('VUOI', ['V', 'IND', 'PRS', '2', 'SG']),
            ('VUOLE', ['V', 'IND', 'PRS', '3', 'SG']),
            ('VOGLIAMO', ['V', 'IND', 'PRS', '1', 'PL']),
            ('VOLETE', ['V', 'IND', 'PRS', '2', 'PL']),
            ('VOGLIONO', ['V', 'IND', 'PRS', '3', 'PL']),
            ('VOLEVO', ['V', 'IND', 'PST', '1', 'SG', 'IPFV']),
            ('VOLEVI', ['V', 'IND', 'PST', '2', 'SG', 'IPFV']),
            ('VOLEVA', ['V', 'IND', 'PST', '3', 'SG', 'IPFV']),
            ('VOLLI', ['V', 'IND', 'PST', '1', 'SG', 'PFV']),
            ('VOLLE', ['V', 'IND', 'PST', '3', 'SG', 'PFV']),
            ('VORRO', ['V', 'IND', 'FUT', '1', 'SG']),
            ('VORRAI', ['V', 'IND', 'FUT', '2', 'SG']),
            ('VORRA', ['V', 'IND', 'FUT', '3', 'SG']),
            ('VORREI', ['V', 'COND', '1', 'SG']),
            ('VORRESTI', ['V', 'COND', '2', 'SG']),
            ('VORREBBE', ['V', 'COND', '3', 'SG']),
            ('VOLERE', ['V', 'NFIN']),
            ('VOLENDO', ['V.CVB', 'PRS']),
            ('VOLUTO', ['V.PTCP', 'PST']),
        ],
        'ANDARE': [
            ('VADO', ['V', 'IND', 'PRS', '1', 'SG']),
            ('VAI', ['V', 'IND', 'PRS', '2', 'SG']),
            ('VA', ['V', 'IND', 'PRS', '3', 'SG']),
            ('ANDIAMO', ['V', 'IND', 'PRS', '1', 'PL']),
            ('ANDATE', ['V', 'IND', 'PRS', '2', 'PL']),
            ('VANNO', ['V', 'IND', 'PRS', '3', 'PL']),
            ('ANDAVO', ['V', 'IND', 'PST', '1', 'SG', 'IPFV']),
            ('ANDAVI', ['V', 'IND', 'PST', '2', 'SG', 'IPFV']),
            ('ANDAVA', ['V', 'IND', 'PST', '3', 'SG', 'IPFV']),
            ('ANDAI', ['V', 'IND', 'PST', '1', 'SG', 'PFV']),
            ('ANDASTI', ['V', 'IND', 'PST', '2', 'SG', 'PFV']),
            ('ANDO', ['V', 'IND', 'PST', '3', 'SG', 'PFV']),
            ('ANDAMMO', ['V', 'IND', 'PST', '1', 'PL', 'PFV']),
            ('ANDASTE', ['V', 'IND', 'PST', '2', 'PL', 'PFV']),
            ('ANDARONO', ['V', 'IND', 'PST', '3', 'PL', 'PFV']),
            ('ANDRO', ['V', 'IND', 'FUT', '1', 'SG']),
            ('ANDRAI', ['V', 'IND', 'FUT', '2', 'SG']),
            ('ANDRA', ['V', 'IND', 'FUT', '3', 'SG']),
            ('ANDREMO', ['V', 'IND', 'FUT', '1', 'PL']),
            ('ANDRETE', ['V', 'IND', 'FUT', '2', 'PL']),
            ('ANDRANNO', ['V', 'IND', 'FUT', '3', 'PL']),
            ('VADA', ['V', 'SBJV', 'PRS', '1', 'SG']),
            ('VADA', ['V', 'SBJV', 'PRS', '3', 'SG']),
            ('ANDIAMO', ['V', 'SBJV', 'PRS', '1', 'PL']),
            ('ANDIATE', ['V', 'SBJV', 'PRS', '2', 'PL']),
            ('VADANO', ['V', 'SBJV', 'PRS', '3', 'PL']),
            ('ANDREI', ['V', 'COND', '1', 'SG']),
            ('ANDRESTI', ['V', 'COND', '2', 'SG']),
            ('ANDREBBE', ['V', 'COND', '3', 'SG']),
            ('ANDARE', ['V', 'NFIN']),
            ('ANDANDO', ['V.CVB', 'PRS']),
            ('ANDATO', ['V.PTCP', 'PST']),
        ],
        'STARE': [
            ('STO', ['V', 'IND', 'PRS', '1', 'SG']),
            ('STAI', ['V', 'IND', 'PRS', '2', 'SG']),
            ('STA', ['V', 'IND', 'PRS', '3', 'SG']),
            ('STIAMO', ['V', 'IND', 'PRS', '1', 'PL']),
            ('STATE', ['V', 'IND', 'PRS', '2', 'PL']),
            ('STANNO', ['V', 'IND', 'PRS', '3', 'PL']),
            ('STAVO', ['V', 'IND', 'PST', '1', 'SG', 'IPFV']),
            ('STAVI', ['V', 'IND', 'PST', '2', 'SG', 'IPFV']),
            ('STAVA', ['V', 'IND', 'PST', '3', 'SG', 'IPFV']),
            ('STETTI', ['V', 'IND', 'PST', '1', 'SG', 'PFV']),
            ('STETTE', ['V', 'IND', 'PST', '3', 'SG', 'PFV']),
            ('STARO', ['V', 'IND', 'FUT', '1', 'SG']),
            ('STARAI', ['V', 'IND', 'FUT', '2', 'SG']),
            ('STARA', ['V', 'IND', 'FUT', '3', 'SG']),
            ('STAREI', ['V', 'COND', '1', 'SG']),
            ('STARESTI', ['V', 'COND', '2', 'SG']),
            ('STAREBBE', ['V', 'COND', '3', 'SG']),
            ('STARE', ['V', 'NFIN']),
            ('STANDO', ['V.CVB', 'PRS']),
            ('STATO', ['V.PTCP', 'PST']),
        ],
        'DARE': [
            ('DO', ['V', 'IND', 'PRS', '1', 'SG']),
            ('DAI', ['V', 'IND', 'PRS', '2', 'SG']),
            ('DA', ['V', 'IND', 'PRS', '3', 'SG']),
            ('DIAMO', ['V', 'IND', 'PRS', '1', 'PL']),
            ('DATE', ['V', 'IND', 'PRS', '2', 'PL']),
            ('DANNO', ['V', 'IND', 'PRS', '3', 'PL']),
            ('DAVO', ['V', 'IND', 'PST', '1', 'SG', 'IPFV']),
            ('DAVI', ['V', 'IND', 'PST', '2', 'SG', 'IPFV']),
            ('DAVA', ['V', 'IND', 'PST', '3', 'SG', 'IPFV']),
            ('DETTI', ['V', 'IND', 'PST', '1', 'SG', 'PFV']),
            ('DETTE', ['V', 'IND', 'PST', '3', 'SG', 'PFV']),
            ('DARO', ['V', 'IND', 'FUT', '1', 'SG']),
            ('DARAI', ['V', 'IND', 'FUT', '2', 'SG']),
            ('DARA', ['V', 'IND', 'FUT', '3', 'SG']),
            ('DAREI', ['V', 'COND', '1', 'SG']),
            ('DARESTI', ['V', 'COND', '2', 'SG']),
            ('DAREBBE', ['V', 'COND', '3', 'SG']),
            ('DARE', ['V', 'NFIN']),
            ('DANDO', ['V.CVB', 'PRS']),
            ('DATO', ['V.PTCP', 'PST']),
        ],
        'VENIRE': [
            ('VENGO', ['V', 'IND', 'PRS', '1', 'SG']),
            ('VIENI', ['V', 'IND', 'PRS', '2', 'SG']),
            ('VIENE', ['V', 'IND', 'PRS', '3', 'SG']),
            ('VENIAMO', ['V', 'IND', 'PRS', '1', 'PL']),
            ('VENITE', ['V', 'IND', 'PRS', '2', 'PL']),
            ('VENGONO', ['V', 'IND', 'PRS', '3', 'PL']),
            ('VENIVO', ['V', 'IND', 'PST', '1', 'SG', 'IPFV']),
            ('VENIVI', ['V', 'IND', 'PST', '2', 'SG', 'IPFV']),
            ('VENIVA', ['V', 'IND', 'PST', '3', 'SG', 'IPFV']),
            ('VENNI', ['V', 'IND', 'PST', '1', 'SG', 'PFV']),
            ('VENNE', ['V', 'IND', 'PST', '3', 'SG', 'PFV']),
            ('VERRA', ['V', 'IND', 'FUT', '3', 'SG']),
            ('VERRANNO', ['V', 'IND', 'FUT', '3', 'PL']),
            ('VERREI', ['V', 'COND', '1', 'SG']),
            ('VERRESTI', ['V', 'COND', '2', 'SG']),
            ('VERREBBE', ['V', 'COND', '3', 'SG']),
            ('VENIRE', ['V', 'NFIN']),
            ('VENENDO', ['V.CVB', 'PRS']),
            ('VENUTO', ['V.PTCP', 'PST']),
        ],
        'LEGGERE': [
            ('LEGGO', ['V', 'IND', 'PRS', '1', 'SG']),
            ('LEGGI', ['V', 'IND', 'PRS', '2', 'SG']),
            ('LEGGE', ['V', 'IND', 'PRS', '3', 'SG']),
            ('LEGGIAMO', ['V', 'IND', 'PRS', '1', 'PL']),
            ('LEGGETE', ['V', 'IND', 'PRS', '2', 'PL']),
            ('LEGGENO', ['V', 'IND', 'PRS', '3', 'PL']),
            ('LEGGEVO', ['V', 'IND', 'PST', '1', 'SG', 'IPFV']),
            ('LEGGEVI', ['V', 'IND', 'PST', '2', 'SG', 'IPFV']),
            ('LEGGEVA', ['V', 'IND', 'PST', '3', 'SG', 'IPFV']),
            ('LESSI', ['V', 'IND', 'PST', '1', 'SG', 'PFV']),
            ('LESSE', ['V', 'IND', 'PST', '3', 'SG', 'PFV']),
            ('LESSERO', ['V', 'IND', 'PST', '3', 'PL', 'PFV']),
            ('LEGRO', ['V', 'IND', 'FUT', '1', 'SG']),
            ('LEGRAI', ['V', 'IND', 'FUT', '2', 'SG']),
            ('LEGRA', ['V', 'IND', 'FUT', '3', 'SG']),
            ('LEGREI', ['V', 'COND', '1', 'SG']),
            ('LEGRESTI', ['V', 'COND', '2', 'SG']),
            ('LEGREBBE', ['V', 'COND', '3', 'SG']),
            ('LEGGERE', ['V', 'NFIN']),
            ('LEGGENDO', ['V.CVB', 'PRS']),
            ('LETTO', ['V.PTCP', 'PST']),
        ],
        'SCRIVERE': [
            ('SCRIVO', ['V', 'IND', 'PRS', '1', 'SG']),
            ('SCRIVI', ['V', 'IND', 'PRS', '2', 'SG']),
            ('SCRIVE', ['V', 'IND', 'PRS', '3', 'SG']),
            ('SCRIVIAMO', ['V', 'IND', 'PRS', '1', 'PL']),
            ('SCRIVETE', ['V', 'IND', 'PRS', '2', 'PL']),
            ('SCRIVONO', ['V', 'IND', 'PRS', '3', 'PL']),
            ('SCRIVEVO', ['V', 'IND', 'PST', '1', 'SG', 'IPFV']),
            ('SCRIVEVI', ['V', 'IND', 'PST', '2', 'SG', 'IPFV']),
            ('SCRIVEVA', ['V', 'IND', 'PST', '3', 'SG', 'IPFV']),
            ('SCRISSE', ['V', 'IND', 'PST', '3', 'SG', 'PFV']),
            ('SCRISSERO', ['V', 'IND', 'PST', '3', 'PL', 'PFV']),
            ('SCRIVERE', ['V', 'NFIN']),
            ('SCRIVENDO', ['V.CVB', 'PRS']),
            ('SCRITTO', ['V.PTCP', 'PST']),
        ],
        'PARLARE': [
            ('PARLO', ['V', 'IND', 'PRS', '1', 'SG']),
            ('PARLI', ['V', 'IND', 'PRS', '2', 'SG']),
            ('PARLA', ['V', 'IND', 'PRS', '3', 'SG']),
            ('PARLIAMO', ['V', 'IND', 'PRS', '1', 'PL']),
            ('PARLATE', ['V', 'IND', 'PRS', '2', 'PL']),
            ('PARLANO', ['V', 'IND', 'PRS', '3', 'PL']),
            ('PARLAVO', ['V', 'IND', 'PST', '1', 'SG', 'IPFV']),
            ('PARLAVI', ['V', 'IND', 'PST', '2', 'SG', 'IPFV']),
            ('PARLAVA', ['V', 'IND', 'PST', '3', 'SG', 'IPFV']),
            ('PARLAI', ['V', 'IND', 'PST', '1', 'SG', 'PFV']),
            ('PARLO-PST', ['V', 'IND', 'PST', '3', 'SG', 'PFV']),
            ('PARLARE', ['V', 'NFIN']),
            ('PARLANDO', ['V.CVB', 'PRS']),
            ('PARLATO', ['V.PTCP', 'PST']),
        ],
        'SAPERE': [
            ('SO', ['V', 'IND', 'PRS', '1', 'SG']),
            ('SAI', ['V', 'IND', 'PRS', '2', 'SG']),
            ('SA', ['V', 'IND', 'PRS', '3', 'SG']),
            ('SAPPIAMO', ['V', 'IND', 'PRS', '1', 'PL']),
            ('SAPETE', ['V', 'IND', 'PRS', '2', 'PL']),
            ('SANNO', ['V', 'IND', 'PRS', '3', 'PL']),
            ('SAPEVO', ['V', 'IND', 'PST', '1', 'SG', 'IPFV']),
            ('SAPEVI', ['V', 'IND', 'PST', '2', 'SG', 'IPFV']),
            ('SAPEVA', ['V', 'IND', 'PST', '3', 'SG', 'IPFV']),
            ('SEPPBI', ['V', 'IND', 'PST', '1', 'SG', 'PFV']),
            ('SEPPE', ['V', 'IND', 'PST', '3', 'SG', 'PFV']),
            ('SAPRO', ['V', 'IND', 'FUT', '1', 'SG']),
            ('SAPRAI', ['V', 'IND', 'FUT', '2', 'SG']),
            ('SAPRA', ['V', 'IND', 'FUT', '3', 'SG']),
            ('SAPREI', ['V', 'COND', '1', 'SG']),
            ('SAPRESTI', ['V', 'COND', '2', 'SG']),
            ('SAPREBBE', ['V', 'COND', '3', 'SG']),
            ('SAPERE', ['V', 'NFIN']),
            ('SAPENDO', ['V.CVB', 'PRS']),
            ('SAPUTO', ['V.PTCP', 'PST']),
        ],
    }

    for lemma, forms in COMMON_VERBS.items():
        lemma_clean = clean_italian(lemma)
        if not lemma_clean:
            continue
        for form_raw, tags in forms:
            form_clean = clean_italian(form_raw)
            if form_clean:
                data[lemma_clean][tags[0]].append((form_clean, tags))

    # Build morphology: use per-form lemma entries for suppletive verbs
    # For non-suppletive forms (common stem), use traditional paradigm approach
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

            # Find common stem
            stem = lemma
            for w, _ in word_codes:
                while not w.startswith(stem) and stem:
                    stem = stem[:-1]

            # If stem is too short (suppletion), create individual entries per form
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

                first_flexia = paradigm[0]['flexia'] if paradigm else ''
                lemmas_list.append({"l": stem + first_flexia, "f": p_id, "a": 0, "s": 0})
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

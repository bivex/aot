import json
import os
import unicodedata
from collections import defaultdict
from datetime import datetime

POS_MAP = {
    "N": "NOUN",
    "NOUN": "NOUN",
    "PROPN": "NOUN",
    "ADJ": "ADJ",
    "ADV": "ADV",
    "DET": "DET",
    "PRON": "PRON",
    "PREP": "PREP",
    "CONJ": "CONJ",
    "INTJ": "INT",
    "NUM": "NUM",
    "V": "VERB",
    "VERB": "VERB",
    "V.PTCP": "VERB",
}

TAG_MAP = {
    "SG": "sg",
    "PL": "pl",
    "MASC": "masc",
    "FEM": "fem",
    "NEUT": "neut",
    "MASC+FEM": "com",
    "MASC+FEM+NEUT": "com",
    "NOM": "nom",
    "ACC": "acc",
    "DAT": "dat",
    "GEN": "gen",
    "ABL": "abl",
    "VOC": "voc",
    "LOC": "loc",
    "GEN+DAT": "dat",
    "ACT": "act",
    "PASS": "pass",
    "IND": "ind",
    "SBJV": "sbjv",
    "IMP": "impv",
    "PRS": "pres",
    "PST": "past",
    "FUT": "fut",
    "IPFV": "impf",
    "PFV": "pfv",
    "PRF": "pfv",
    "1": "p1",
    "2": "p2",
    "3": "p3",
    "NFIN": "inf",
    "V.MSDR": "ger",
}

SKIP_TAGS = {
    "LGSPEC1",
    "MASC+FEM+FEM",
    "FEM+MASC",
    "MASC+MASC",
    "FEM+FEM",
    "FEM+NEUT",
    "MASC+NEUT",
    "NEUT+MASC",
}


def normalize(text):
    nfkd = unicodedata.normalize("NFKD", text.upper())
    return "".join(c for c in nfkd if not unicodedata.combining(c))


def clean_text(text):
    return "".join(c for c in normalize(text) if "A" <= c <= "Z")


def get_stem(lemma, forms):
    if not forms:
        return lemma
    stem = lemma
    for word in forms:
        while not word.startswith(stem) and stem:
            stem = stem[:-1]
    return stem


def convert():
    input_file = "Dicts/Morph/Latin/unimorph/lat"
    output_morphs = "Source/morph_dict/data/Latin/morphs.json"
    output_gramtab = "Source/morph_dict/data/Latin/gramtab.json"

    gramtab = {"gramcodes": {}}
    gram_to_code = {}
    next_code_idx = 0

    def get_gramcode(pos, tags, lemma=None):
        nonlocal next_code_idx
        aot_pos = POS_MAP.get(pos)
        if not aot_pos:
            return None

        aot_tags = []
        has_ptcp = pos == "V.PTCP" or "V.PTCP" in tags
        has_ger = "V.MSDR" in tags
        if has_ptcp:
            aot_tags.append("ptcp")
        if has_ger:
            aot_tags.append("ger")

        for t in tags:
            if t in SKIP_TAGS:
                continue
            if t in TAG_MAP:
                aot_tags.append(TAG_MAP[t])

        if aot_pos == "NOUN":
            if "sg" not in aot_tags and "pl" not in aot_tags:
                aot_tags.append("sg")
            if not ({"masc", "fem", "neut", "com"} & set(aot_tags)):
                aot_tags.append("masc")
            if not ({"nom", "acc", "dat", "gen", "abl", "voc", "loc"} & set(aot_tags)):
                aot_tags.append("nom")

        if aot_pos == "ADJ":
            if "sg" not in aot_tags and "pl" not in aot_tags:
                aot_tags.append("sg")
            if not ({"masc", "fem", "neut", "com"} & set(aot_tags)):
                aot_tags.append("com")
            if not ({"nom", "acc", "dat", "gen", "abl", "voc", "loc"} & set(aot_tags)):
                aot_tags.append("nom")

        if aot_pos == "VERB" and not ({"inf", "pres", "past", "fut"} & set(aot_tags)):
            aot_tags.append("inf")

        key = (aot_pos, tuple(sorted(set(aot_tags))))
        if key not in gram_to_code:
            c1 = chr(ord("A") + (next_code_idx // 26))
            c2 = chr(ord("A") + (next_code_idx % 26))
            code = c1 + c2
            next_code_idx += 1
            gram_to_code[key] = code
            gramtab["gramcodes"][code] = {
                "p": aot_pos,
                "g": list(key[1]),
                "l": lemma or "",
            }
        return gram_to_code[key]

    data = defaultdict(lambda: defaultdict(list))

    print(f"Reading {input_file}...")
    total_lines = 0
    skipped = 0
    with open(input_file, "r", encoding="utf-8") as f:
        for line in f:
            total_lines += 1
            line = line.strip()
            if not line:
                continue
            parts = line.split("\t")
            if len(parts) < 3:
                continue

            lemma_raw = normalize(parts[0].strip())
            word_raw = normalize(parts[1].strip())
            lemma_clean = clean_text(lemma_raw)
            word_clean = clean_text(word_raw)
            if not lemma_clean or not word_clean:
                skipped += 1
                continue

            tags_raw = [normalize(t) for t in parts[2].split(";")]
            pos = tags_raw[0]
            if pos not in POS_MAP:
                skipped += 1
                continue

            data[lemma_clean][pos].append((word_clean, tags_raw))

    print(f"Read {total_lines} lines, {len(data)} lemmas, skipped {skipped}")

    for lemma in list(data.keys()):
        for pos in list(data[lemma].keys()):
            forms = data[lemma][pos]
            words_in_forms = {w for w, _ in forms}
            if lemma not in words_in_forms:
                if pos in {"N", "PROPN"}:
                    tags = ["N", "NOM", "SG", "MASC"]
                elif pos == "ADJ":
                    tags = ["ADJ", "NOM", "SG", "MASC+FEM"]
                elif pos == "V":
                    tags = ["V", "NFIN"]
                elif pos == "V.PTCP":
                    tags = ["V.PTCP", "NOM", "SG", "MASC"]
                else:
                    tags = [pos, "SG"]
                data[lemma][pos].append((lemma, tags))

    closed_class = {
        "EGO": ("PRON", []),
        "MEI": ("PRON", []),
        "MIHI": ("PRON", []),
        "ME": ("PRON", []),
        "NOS": ("PRON", []),
        "NOSTRI": ("PRON", []),
        "NOBIS": ("PRON", []),
        "TU": ("PRON", []),
        "TUI": ("PRON", []),
        "TIBI": ("PRON", []),
        "TE": ("PRON", []),
        "VOS": ("PRON", []),
        "VESTRI": ("PRON", []),
        "VOBIS": ("PRON", []),
        "IS": ("PRON", []),
        "EA": ("PRON", []),
        "ID": ("PRON", []),
        "EUM": ("PRON", []),
        "EAM": ("PRON", []),
        "EIUS": ("PRON", []),
        "EIS": ("PRON", []),
        "EOS": ("PRON", []),
        "EAS": ("PRON", []),
        "HIC": ("PRON", []),
        "HAEC": ("PRON", []),
        "HOC": ("PRON", []),
        "HUNC": ("PRON", []),
        "HUIC": ("PRON", []),
        "ILLE": ("PRON", []),
        "ILLA": ("PRON", []),
        "ILLUD": ("PRON", []),
        "QUI": ("PRON", []),
        "QUAE": ("PRON", []),
        "QUOD": ("PRON", []),
        "QUEM": ("PRON", []),
        "QUAM": ("PRON", []),
        "CUJUS": ("PRON", []),
        "CUI": ("PRON", []),
        "QUO": ("PRON", []),
        "QUA": ("PRON", []),
        "ROSA": ("NOUN", ["NOM", "SG", "FEM"]),
        "ROSAS": ("NOUN", ["ACC", "PL", "FEM"]),
        "AMO": ("VERB", ["IND", "PRS", "1", "SG"]),
        "AMAS": ("VERB", ["IND", "PRS", "2", "SG"]),
        "AMAT": ("VERB", ["IND", "PRS", "3", "SG"]),
        "AMAMUS": ("VERB", ["IND", "PRS", "1", "PL"]),
        "AMATIS": ("VERB", ["IND", "PRS", "2", "PL"]),
        "AMANT": ("VERB", ["IND", "PRS", "3", "PL"]),
        "AMARE": ("VERB", ["NFIN"]),
        "SUM": ("VERB", ["IND", "PRS", "1", "SG"]),
        "ES": ("VERB", ["IND", "PRS", "2", "SG"]),
        "EST": ("VERB", ["IND", "PRS", "3", "SG"]),
        "SUMUS": ("VERB", ["IND", "PRS", "1", "PL"]),
        "ESTIS": ("VERB", ["IND", "PRS", "2", "PL"]),
        "SUNT": ("VERB", ["IND", "PRS", "3", "PL"]),
        "ESSE": ("VERB", ["NFIN"]),
        "ET": ("CONJ", []),
        "AC": ("CONJ", []),
        "ATQUE": ("CONJ", []),
        "SED": ("CONJ", []),
        "AUT": ("CONJ", []),
        "VEL": ("CONJ", []),
        "QUE": ("CONJ", []),
        "NEC": ("CONJ", []),
        "NEQUE": ("CONJ", []),
        "NAM": ("CONJ", []),
        "SI": ("CONJ", []),
        "UT": ("CONJ", []),
        "AN": ("CONJ", []),
        "A": ("PREP", []),
        "AB": ("PREP", []),
        "AD": ("PREP", []),
        "CUM": ("PREP", []),
        "DE": ("PREP", []),
        "EX": ("PREP", []),
        "E": ("PREP", []),
        "IN": ("PREP", []),
        "PER": ("PREP", []),
        "PRO": ("PREP", []),
        "SINE": ("PREP", []),
        "SUB": ("PREP", []),
        "SUPER": ("PREP", []),
        "TRANS": ("PREP", []),
        "INTER": ("PREP", []),
        "CONTRA": ("PREP", []),
        "NON": ("ADV", []),
        "ETIAM": ("ADV", []),
        "QUOQUE": ("ADV", []),
        "TAMEN": ("ADV", []),
        "IAM": ("ADV", []),
        "QUIDEM": ("ADV", []),
        "MAGIS": ("ADV", []),
        "MAXIME": ("ADV", []),
        "MINUS": ("ADV", []),
        "SAEPE": ("ADV", []),
        "UNUS": ("NUM", ["SG", "MASC"]),
        "UNA": ("NUM", ["SG", "FEM"]),
        "UNUM": ("NUM", ["SG", "NEUT"]),
        "DUO": ("NUM", ["PL", "MASC"]),
        "DUAE": ("NUM", ["PL", "FEM"]),
        "DUO": ("NUM", ["PL", "NEUT"]),
        "TRES": ("NUM", ["PL", "MASC"]),
        "TRIA": ("NUM", ["PL", "NEUT"]),
    }

    for word, (pos, tags) in closed_class.items():
        data[word][pos].append((word, [pos] + tags))

    for lemma, word, pos, tags in [
        ("ROSA", "ROSA", "NOUN", ["NOM", "SG", "FEM"]),
        ("ROSA", "ROSAS", "NOUN", ["ACC", "PL", "FEM"]),
        ("LAUDO", "LAUDO", "VERB", ["IND", "PRS", "1", "SG"]),
        ("LAUDO", "LAUDAS", "VERB", ["IND", "PRS", "2", "SG"]),
        ("LAUDO", "LAUDAT", "VERB", ["IND", "PRS", "3", "SG"]),
        ("LAUDO", "LAUDAMUS", "VERB", ["IND", "PRS", "1", "PL"]),
        ("LAUDO", "LAUDATIS", "VERB", ["IND", "PRS", "2", "PL"]),
        ("LAUDO", "LAUDANT", "VERB", ["IND", "PRS", "3", "PL"]),
        ("LAUDO", "LAUDARE", "VERB", ["NFIN"]),
        ("LAUDO", "LAUDANS", "VERB", ["V.PTCP", "NOM", "SG", "MASC"]),
        ("LAUDO", "LAUDANS", "VERB", ["V.PTCP", "NOM", "SG", "FEM"]),
        ("LAUDO", "LAUDANS", "VERB", ["V.PTCP", "NOM", "SG", "NEUT"]),
        ("AMO", "AMO", "VERB", ["IND", "PRS", "1", "SG"]),
        ("AMO", "AMAS", "VERB", ["IND", "PRS", "2", "SG"]),
        ("AMO", "AMAT", "VERB", ["IND", "PRS", "3", "SG"]),
        ("AMO", "AMAMUS", "VERB", ["IND", "PRS", "1", "PL"]),
        ("AMO", "AMATIS", "VERB", ["IND", "PRS", "2", "PL"]),
        ("AMO", "AMANT", "VERB", ["IND", "PRS", "3", "PL"]),
        ("AMO", "AMARE", "VERB", ["NFIN"]),
        ("AMO", "AMANS", "VERB", ["V.PTCP", "NOM", "SG", "MASC"]),
        ("AMO", "AMANS", "VERB", ["V.PTCP", "NOM", "SG", "FEM"]),
        ("AMO", "AMANS", "VERB", ["V.PTCP", "NOM", "SG", "NEUT"]),
    ]:
        data[lemma][pos].append((word, [pos] + tags))

    closed_class_forms = [
        ("AMANS", "VERB", ["V.PTCP", "NOM", "SG", "MASC"]),
        ("AMANS", "VERB", ["V.PTCP", "NOM", "SG", "FEM"]),
        ("AMANS", "VERB", ["V.PTCP", "NOM", "SG", "NEUT"]),
    ]
    for word, pos, tags in closed_class_forms:
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
                paradigm.append({"flexia": w[len(stem) :], "gramcode": gcode})

            p_key = json.dumps(paradigm, sort_keys=True)
            if p_key not in paradigm_to_id:
                paradigm_to_id[p_key] = len(flexia_models)
                flexia_models.append({"endings": paradigm})
            p_id = paradigm_to_id[p_key]

            first_flexia = paradigm[0]["flexia"] if paradigm else ""
            lemmas_list.append({"l": stem + first_flexia, "f": p_id, "a": 0, "s": 0})
            count += len(word_codes)

    plug_code = None
    for code, info in gramtab["gramcodes"].items():
        if (
            info["p"] == "NOUN"
            and "sg" in info["g"]
            and "masc" in info["g"]
            and "nom" in info["g"]
        ):
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
        "lemmas": lemmas_list,
    }

    os.makedirs(os.path.dirname(output_morphs), exist_ok=True)
    with open(output_morphs, "w", encoding="utf-8") as f:
        json.dump(morphs, f, ensure_ascii=False, indent=1)
    with open(output_gramtab, "w", encoding="utf-8") as f:
        json.dump(gramtab, f, ensure_ascii=False, indent=1)

    print(
        f"Wrote {output_morphs}: {len(flexia_models)} flexia models, {len(lemmas_list)} lemmas, {count} total forms"
    )
    print(f"Wrote {output_gramtab}: {len(gramtab['gramcodes'])} gramcodes")


if __name__ == "__main__":
    convert()

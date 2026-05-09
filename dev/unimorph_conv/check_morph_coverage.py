#!/usr/bin/env python3
"""
Morphological Dictionary Coverage Checker
==========================================
Compares coverage of verb/noun/adj forms between:
  - UniMorph eng (current local file)
  - AGID (Automatically Generated Inflection Database)
  - Optionally: fresh UniMorph from GitHub

Usage:
  python3 check_morph_coverage.py --unimorph path/to/eng [--agid path/to/agid.txt] [--download-agid]
"""

import argparse
import sys
import os
import re
import urllib.request
import tarfile
import io
from collections import defaultdict

# ── Colour helpers ──────────────────────────────────────────────────────────
GREEN  = "\033[92m"
RED    = "\033[91m"
YELLOW = "\033[93m"
CYAN   = "\033[96m"
RESET  = "\033[0m"
BOLD   = "\033[1m"

def ok(s):   return f"{GREEN}✓{RESET} {s}"
def bad(s):  return f"{RED}✗{RESET} {s}"
def warn(s): return f"{YELLOW}⚠{RESET} {s}"
def hdr(s):  return f"\n{BOLD}{CYAN}{s}{RESET}"


# ── PROBE WORDS ──────────────────────────────────────────────────────────────
# (surface_form, expected_lemma, pos_hint)
PROBE_WORDS = [
    # The rin→run bug
    ("runs",    "run",   "V"),
    ("ran",     "run",   "V"),
    ("running", "run",   "V"),
    # Normal verbs
    ("walks",   "walk",  "V"),
    ("walked",  "walk",  "V"),
    ("walking", "walk",  "V"),
    ("sees",    "see",   "V"),
    ("saw",     "see",   "V"),
    ("seen",    "see",   "V"),
    ("goes",    "go",    "V"),
    ("went",    "go",    "V"),
    ("gone",    "go",    "V"),
    ("takes",   "take",  "V"),
    ("took",    "take",  "V"),
    ("taken",   "take",  "V"),
    ("makes",   "make",  "V"),
    ("made",    "make",  "V"),
    ("comes",   "come",  "V"),
    ("came",    "come",  "V"),
    ("knows",   "know",  "V"),
    ("knew",    "know",  "V"),
    ("thinks",  "think", "V"),
    ("thought", "think", "V"),
    ("reads",   "read",  "V"),
    ("reading", "read",  "V"),
    # -ing forms (often missing)
    ("having",  "have",  "V"),
    ("doing",   "do",    "V"),
    ("being",   "be",    "V"),
    ("saying",  "say",   "V"),
    # Nouns
    ("dogs",    "dog",   "N"),
    ("cats",    "cat",   "N"),
    ("houses",  "house", "N"),
    ("cities",  "city",  "N"),
    ("men",     "man",   "N"),
    ("women",   "woman", "N"),
    ("children","child", "N"),
    # Adjectives
    ("bigger",  "big",   "ADJ"),
    ("biggest", "big",   "ADJ"),
    ("faster",  "fast",  "ADJ"),
    ("fastest", "fast",  "ADJ"),
    ("better",  "good",  "ADJ"),
    ("best",    "good",  "ADJ"),
]


# ── UniMorph parser ──────────────────────────────────────────────────────────
def parse_unimorph(path: str) -> tuple[dict, dict, set]:
    """
    Returns:
      lemma_to_forms  : {lemma: {surface: tag_string}}
      form_to_lemmas  : {surface: [(lemma, tag_string)]}
      all_surfaces    : set of all surface forms
    """
    lemma_to_forms = defaultdict(dict)
    form_to_lemmas = defaultdict(list)
    all_surfaces   = set()
    errors = 0

    with open(path, encoding="utf-8") as f:
        for lineno, line in enumerate(f, 1):
            line = line.rstrip("\n")
            if not line or line.startswith("#"):
                continue
            parts = line.split("\t")
            if len(parts) < 3:
                errors += 1
                continue
            lemma, surface, tags = parts[0], parts[1], parts[2]
            lemma_to_forms[lemma][surface] = tags
            form_to_lemmas[surface].append((lemma, tags))
            all_surfaces.add(surface)

    print(f"  UniMorph: {len(all_surfaces):>7,} unique surface forms, "
          f"{len(lemma_to_forms):>6,} lemmas  (parse errors: {errors})")
    return dict(lemma_to_forms), dict(form_to_lemmas), all_surfaces


# ── AGID parser ──────────────────────────────────────────────────────────────
# AGID format example:
#   run V: ran | runs | running | run
#   good AV: better Ac | best Ac
def parse_agid(path: str) -> tuple[dict, dict, set]:
    lemma_to_forms = defaultdict(dict)
    form_to_lemmas = defaultdict(list)
    all_surfaces   = set()
    errors = 0

    pos_map = {"V": "V", "N": "N", "A": "ADJ", "AV": "ADJ"}

    with open(path, encoding="utf-8", errors="replace") as f:
        for line in f:
            line = line.strip()
            if not line or line.startswith("#"):
                continue
            # split at first ':'
            m = re.match(r'^(\S+)\s+([A-Z]+)\??\s*:\s*(.+)$', line)
            if not m:
                errors += 1
                continue
            lemma, pos_raw, forms_str = m.group(1), m.group(2), m.group(3)
            pos = pos_map.get(pos_raw, pos_raw)
            # forms may have quality markers: ran | runs! | running
            for token in forms_str.split("|"):
                token = token.strip()
                # strip trailing quality chars like !, ?, ~, <, >
                surface = re.sub(r'[!?~<>\s]+$', '', token).split()[0] if token else ""
                surface = surface.strip("!?~<>")
                if not surface:
                    continue
                tag = pos
                lemma_to_forms[lemma][surface] = tag
                form_to_lemmas[surface].append((lemma, tag))
                all_surfaces.add(surface)
            # also add the lemma itself
            all_surfaces.add(lemma)
            lemma_to_forms[lemma][lemma] = pos + ";BASE"
            form_to_lemmas[lemma].append((lemma, pos + ";BASE"))

    print(f"  AGID:     {len(all_surfaces):>7,} unique surface forms, "
          f"{len(lemma_to_forms):>6,} lemmas  (parse errors: {errors})")
    return dict(lemma_to_forms), dict(form_to_lemmas), all_surfaces


# ── Download helpers ─────────────────────────────────────────────────────────
AGID_URL = "http://wordlist.aspell.net/other/agid-2016.01.19.tar.bz2"

def download_agid(dest_dir: str = ".") -> str:
    out_path = os.path.join(dest_dir, "agid.txt")
    if os.path.exists(out_path):
        print(f"  AGID already exists at {out_path}, skipping download.")
        return out_path
    print(f"  Downloading AGID from {AGID_URL} ...")
    try:
        data = urllib.request.urlopen(AGID_URL, timeout=30).read()
    except Exception as e:
        print(f"  {RED}Download failed: {e}{RESET}")
        print("  Download manually from: http://wordlist.aspell.net/other/")
        sys.exit(1)
    with tarfile.open(fileobj=io.BytesIO(data), mode="r:bz2") as tar:
        for member in tar.getmembers():
            if member.name.endswith("infl.txt"):
                f = tar.extractfile(member)
                content = f.read().decode("utf-8", errors="replace")
                with open(out_path, "w", encoding="utf-8") as out:
                    out.write(content)
                print(f"  Extracted to {out_path}")
                return out_path
    print(f"  {RED}Could not find infl.txt inside archive{RESET}")
    sys.exit(1)


# ── Bug detector: rin→run ────────────────────────────────────────────────────
def detect_rin_bug(lemma_to_forms: dict, form_to_lemmas: dict):
    print(hdr("── Bug check: rin → run ──"))
    suspicious_lemmas = {}
    for lemma, forms in lemma_to_forms.items():
        surfaces = set(forms.keys())
        # if lemma looks like a typo of a common verb but has "wrong" forms
        if lemma == "rin" and any(f in surfaces for f in ("runs", "ran", "running", "run")):
            suspicious_lemmas[lemma] = surfaces

    # Also check: is "run" a lemma at all?
    if "run" in lemma_to_forms:
        run_forms = set(lemma_to_forms["run"].keys())
        print(ok(f"Lemma 'run' found with {len(run_forms)} forms: {sorted(run_forms)[:10]}"))
        for probe in ("runs", "ran", "running"):
            if probe in run_forms:
                print(ok(f"  '{probe}' → run"))
            else:
                print(bad(f"  '{probe}' missing under lemma 'run'"))
    else:
        print(bad("Lemma 'run' NOT found in dictionary"))

    if "rin" in lemma_to_forms:
        rin_forms = set(lemma_to_forms["rin"].keys())
        misplaced = rin_forms & {"runs", "ran", "running", "run"}
        if misplaced:
            print(bad(f"BUG CONFIRMED: lemma 'rin' claims forms: {sorted(misplaced)}"))
        else:
            print(warn(f"Lemma 'rin' exists with forms: {sorted(rin_forms)[:8]} (no run-forms)"))
    else:
        print(ok("Lemma 'rin' not present — bug absent or fixed"))


# ── Probe table ──────────────────────────────────────────────────────────────
def run_probes(label: str, form_to_lemmas: dict):
    print(hdr(f"── Probe words: {label} ──"))
    found = 0
    total = len(PROBE_WORDS)
    wrong_lemma = []
    missing = []

    for surface, expected_lemma, pos in PROBE_WORDS:
        entries = form_to_lemmas.get(surface, [])
        if not entries:
            missing.append(surface)
        else:
            lemmas = [e[0] for e in entries]
            if expected_lemma in lemmas:
                found += 1
            else:
                wrong_lemma.append((surface, expected_lemma, lemmas))
                found += 1  # form exists, just wrong lemma

    print(f"  Surface forms found : {found}/{total} "
          f"({GREEN}{found/total*100:.1f}%{RESET})")
    print(f"  Missing entirely    : {len(missing)}")
    print(f"  Wrong lemma         : {len(wrong_lemma)}")

    if missing:
        print(f"\n  {RED}Missing forms:{RESET}")
        for s in missing:
            exp = next(e for sf,e,_ in PROBE_WORDS if sf==s)
            print(f"    {s:15s} (expected lemma: {exp})")

    if wrong_lemma:
        print(f"\n  {YELLOW}Wrong lemma:{RESET}")
        for surface, expected, got in wrong_lemma:
            print(f"    {surface:15s} expected={expected}, got={got}")

    return set(missing)


# ── Coverage over full UD-EWT word list ──────────────────────────────────────
def coverage_over_wordlist(wordlist_path: str,
                           um_surfaces: set,
                           agid_surfaces: set):
    print(hdr("── Coverage over word list ──"))
    words = []
    with open(wordlist_path, encoding="utf-8") as f:
        for line in f:
            w = line.strip().split()[0].lower() if line.strip() else ""
            if w:
                words.append(w)
    total = len(words)
    um_hit   = sum(1 for w in words if w in um_surfaces)
    agid_hit = sum(1 for w in words if w in agid_surfaces)
    only_agid = [w for w in words if w not in um_surfaces and w in agid_surfaces]
    only_um   = [w for w in words if w in um_surfaces and w not in agid_surfaces]
    neither   = [w for w in words if w not in um_surfaces and w not in agid_surfaces]

    print(f"  Word list size : {total:,}")
    print(f"  UniMorph hits  : {um_hit:,}  ({um_hit/total*100:.1f}%)")
    if agid_surfaces:
        print(f"  AGID hits      : {agid_hit:,}  ({agid_hit/total*100:.1f}%)")
        print(f"  Only in AGID   : {len(only_agid):,}  ← UniMorph is missing these")
        print(f"  Only in UniM   : {len(only_um):,}")
        print(f"  Neither covers : {len(neither):,}")
        if only_agid[:20]:
            print(f"\n  Sample AGID-only (UniMorph gaps): {only_agid[:20]}")


# ── Verb-form completeness audit ─────────────────────────────────────────────
COMMON_VERBS = [
    "run","walk","talk","read","write","eat","drink","sleep","wake",
    "make","take","give","get","go","come","see","know","think","say",
    "do","have","be","want","use","find","tell","ask","seem","feel",
    "try","leave","call","keep","let","begin","show","hear","play","move",
]
EXPECTED_VERB_FORMS = {
    # UniMorph feature strings we want to see
    "3SG": lambda tags: "3;SG;PRS" in tags or "V.PTCP" not in tags and re.search(r'\b3\b.*SG', tags),
    "PST": lambda tags: "PST" in tags,
    "ING": lambda tags: "V.CVB" in tags or "PROG" in tags or "PRESPART" in tags,
}

def audit_verb_coverage(label: str, lemma_to_forms: dict):
    print(hdr(f"── Verb form completeness: {label} ──"))
    total_verbs = 0
    complete = 0
    incomplete = []

    for verb in COMMON_VERBS:
        if verb not in lemma_to_forms:
            incomplete.append((verb, "LEMMA MISSING", []))
            continue
        total_verbs += 1
        forms = lemma_to_forms[verb]  # {surface: tags}
        all_tags = " ".join(forms.values())
        surfaces = list(forms.keys())

        missing_slots = []
        for slot, checker in EXPECTED_VERB_FORMS.items():
            # check if any form satisfies this slot
            slot_found = any(checker(t) for t in forms.values())
            if not slot_found:
                missing_slots.append(slot)

        if not missing_slots:
            complete += 1
        else:
            incomplete.append((verb, missing_slots, surfaces[:6]))

    print(f"  Fully covered verbs : {complete}/{len(COMMON_VERBS)}")
    if incomplete:
        print(f"\n  Incomplete verbs:")
        for verb, missing, sample_forms in incomplete[:20]:
            print(f"    {verb:10s}  missing={missing}  have={sample_forms}")


# ── Main ──────────────────────────────────────────────────────────────────────
def main():
    parser = argparse.ArgumentParser(
        description="Compare morphological dictionary coverage")
    parser.add_argument("--unimorph", required=True,
                        help="Path to UniMorph eng file (TSV: lemma\\tform\\ttags)")
    parser.add_argument("--agid", default=None,
                        help="Path to AGID infl.txt (optional)")
    parser.add_argument("--download-agid", action="store_true",
                        help="Download AGID automatically if --agid not given")
    parser.add_argument("--wordlist", default=None,
                        help="Optional word list (one word per line) for coverage stats")
    args = parser.parse_args()

    print(hdr("════ Morphological Dictionary Coverage Checker ════"))

    # ── Load UniMorph ──
    print(hdr("── Loading dictionaries ──"))
    if not os.path.exists(args.unimorph):
        print(bad(f"UniMorph file not found: {args.unimorph}"))
        sys.exit(1)
    um_lemma, um_forms, um_surfaces = parse_unimorph(args.unimorph)

    # ── Load AGID ──
    agid_lemma, agid_forms, agid_surfaces = {}, {}, set()
    agid_path = args.agid
    if not agid_path and args.download_agid:
        agid_path = download_agid(".")
    if agid_path:
        if not os.path.exists(agid_path):
            print(warn(f"AGID file not found: {agid_path}"))
        else:
            agid_lemma, agid_forms, agid_surfaces = parse_agid(agid_path)

    # ── Bug check ──
    detect_rin_bug(um_lemma, um_forms)
    if agid_lemma:
        print(hdr("── Bug check in AGID ──"))
        detect_rin_bug(agid_lemma, agid_forms)

    # ── Probe table ──
    um_missing   = run_probes("UniMorph", um_forms)
    agid_missing = run_probes("AGID", agid_forms) if agid_forms else set()

    if agid_forms:
        rescued = um_missing - agid_missing
        print(hdr("── Gap analysis ──"))
        if rescued:
            print(ok(f"AGID covers {len(rescued)} forms missing in UniMorph: {sorted(rescued)}"))
        still_missing = um_missing & agid_missing
        if still_missing:
            print(warn(f"Missing in BOTH: {sorted(still_missing)}"))

    # ── Verb audit ──
    audit_verb_coverage("UniMorph", um_lemma)
    if agid_lemma:
        audit_verb_coverage("AGID", agid_lemma)

    # ── Optional wordlist coverage ──
    if args.wordlist and os.path.exists(args.wordlist):
        coverage_over_wordlist(args.wordlist, um_surfaces, agid_surfaces)

    print(hdr("════ Done ════\n"))


if __name__ == "__main__":
    main()

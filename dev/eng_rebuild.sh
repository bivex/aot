#!/bin/bash
#
# eng_rebuild.sh — Rebuild English morph dict + frequency weights + synan daemon
#
# Usage:
#   ./dev/eng_rebuild.sh              # full rebuild (dict + weights + binary)
#   ./dev/eng_rebuild.sh --dict-only   # only regenerate morphs.json
#   ./dev/eng_rebuild.sh --weights-only # only recompile weight binaries
#   ./dev/eng_rebuild.sh --restart      # rebuild daemon + restart
#
# Prerequisites:
#   - Python 3, cmake, ninja
#   - fast_build.sh has been run at least once (build dir exists)
#   - UD-EWT corpus at Dicts/EngSynan/ud-ewt/ (train + dev .conllu files)

set -euo pipefail

# ── paths ──────────────────────────────────────────────────────────────
SCRIPT_DIR="$(cd "$(dirname "$0")" && pwd)"
RML="$(cd "$SCRIPT_DIR/.." && pwd)"
BUILD_DIR="$RML/build_fast"
DICT_DIR="$RML/Dicts/Morph/English"
MORPH_SRC="$RML/Source/morph_dict/data/English"
CONV="$RML/dev/unimorph_conv/unimorph_to_aot_v2.py"
STATDATA="$MORPH_SRC/StatData.txt"
WORDDATA="$MORPH_SRC/WordData.txt"
UDA_EWT="$RML/Dicts/EngSynan/ud-ewt"

# ── colours ────────────────────────────────────────────────────────────
GREEN='\033[0;32m'; YELLOW='\033[1;33m'; RED='\033[0;31m'; NC='\033[0m'
info()  { echo -e "${GREEN}[eng_rebuild]${NC} $*"; }
warn()  { echo -e "${YELLOW}[eng_rebuild]${NC} $*"; }
err()   { echo -e "${RED}[eng_rebuild]${NC} $*" >&2; }

# ── parse args ─────────────────────────────────────────────────────────
MODE="full"
RESTART=false
for arg in "$@"; do
  case "$arg" in
    --dict-only)     MODE="dict" ;;
    --weights-only)  MODE="weights" ;;
    --restart)       RESTART=true ;;
    --help|-h)       echo "Usage: $0 [--dict-only|--weights-only|--restart]"; exit 0 ;;
    *)               err "Unknown arg: $arg"; exit 1 ;;
  esac
done

cd "$RML"

# ── 1. regenerate morphs.json + gramtab.json ──────────────────────────
step_dict() {
  info "Step 1/5: Regenerating morph dictionary (morphs.json + gramtab.json)..."
  if [ ! -f "$CONV" ]; then
    err "Converter not found: $CONV"; exit 1
  fi
  python3 "$CONV"
  info "  morphs.json: $(wc -l < "$DICT_DIR/morphs.json") lines"
  info "  gramtab.json: $(wc -l < "$DICT_DIR/gramtab.json") lines"
}

# ── 2. compile morph dict to binary ──────────────────────────────────
step_morph_bin() {
  info "Step 2/5: Compiling morph dictionary to binary..."
  if [ ! -f "$BUILD_DIR/Source/morph_dict/morph_gen/morph_gen" ]; then
    err "morph_gen binary not found. Run fast_build.sh first."; exit 1
  fi
  "$BUILD_DIR/Source/morph_dict/morph_gen/morph_gen" \
    --input "$DICT_DIR/project.mwz" \
    --output-folder "$DICT_DIR" \
    --log-level info
  info "  Done."
}

# ── 3. generate frequency data from UD-EWT ──────────────────────────
step_gen_freq() {
  info "Step 3/5: Generating frequency data from UD-EWT..."
  python3 - "$UDA_EWT" "$STATDATA" "$WORDDATA" << 'PYEOF'
import os, sys
from collections import defaultdict, Counter

uda_dir, stat_path, word_path = sys.argv[1], sys.argv[2], sys.argv[3]

PERSONAL_PRONOUNS = {
    'I','ME','MY','MINE','MYSELF','YOU','YOUR','YOURS','YOURSELF','YOURSELVES',
    'HE','HIM','HIS','HIMSELF','SHE','HER','HERS','HERSELF',
    'IT','ITS','ITSELF','WE','US','OUR','OURS','OURSELVES',
    'THEY','THEM','THEIR','THEIRS','THEMSELVES',
}
UD_TO_AOT = {
    'NOUN':'NOUN','VERB':'VERB','AUX':'VBE','ADJ':'ADJECTIVE',
    'ADV':'ADVERB','ADP':'PREP','CCONJ':'CONJ','SCONJ':'CONJ',
    'DET':'ARTICLE','NUM':'NUMERAL','PRON':'PRON','INTJ':'INT',
    'PROPN':'PN','PART':'PART','PUNCT':None,'SYM':None,'X':None,
}
MODALS = {'can','could','may','might','must','shall','should','will','would','ought'}

def aot_pos(form, lemma, upos):
    p = UD_TO_AOT.get(upos)
    if p is None: return None
    if upos == 'AUX' and lemma.lower() in MODALS: return 'MOD'
    if form.upper() in PERSONAL_PRONOUNS and upos == 'PRON': return 'PN'
    return p

fpf = Counter(); lpf = Counter()
for fn in ['en_ewt-ud-train.conllu','en_ewt-ud-dev.conllu']:
    p = os.path.join(uda_dir, fn)
    if not os.path.exists(p): continue
    with open(p) as f:
        for line in f:
            line = line.strip()
            if not line or line.startswith('#'): continue
            parts = line.split('\t')
            if len(parts)<10 or '-' in parts[0] or '.' in parts[0]: continue
            form, lemma, upos = parts[1].upper(), parts[2].upper(), parts[3]
            ap = aot_pos(form, lemma, upos)
            if ap is None: continue
            fpf[(form,lemma,ap)] += 1
            lpf[(lemma,ap)] += 1

fg = defaultdict(list)
for (f,l,p),c in fpf.items(): fg[f].append((l,p,c))
with open(stat_path,'w') as out:
    for form in sorted(fg):
        entries = sorted(fg[form], key=lambda x:-x[2])
        first = True
        for l,p,c in entries:
            if first: out.write(f'{form} {l} {p} {c}\n'); first=False
            else:     out.write(f'* {l} {p} {c}\n')

lb = {}
for (l,p),c in lpf.items():
    if l not in lb or c > lb[l][1]: lb[l] = (p,c)
with open(word_path,'w') as out:
    for l in sorted(lb): out.write(f'{l};{lb[l][0]} ;{lb[l][1]}\n')

print(f"  StatData.txt: {len(fg)} word forms")
print(f"  WordData.txt: {len(lb)} lemmas")
PYEOF
}

# ── 4. compile frequency data to binary ──────────────────────────────
step_compile_weights() {
  info "Step 4/5: Compiling frequency data to binary..."

  STAT_BIN="$BUILD_DIR/Source/morph_dict/homon_freq_bin/StatDatBin"
  WORD_BIN="$BUILD_DIR/Source/morph_dict/word_freq_bin/word_freq_bin"
  for bin in "$STAT_BIN" "$WORD_BIN"; do
    if [ ! -f "$bin" ]; then
      err "$bin not found. Run fast_build.sh first."; exit 1
    fi
  done

  # filter StatData to valid words only
  FILTERED=$(mktemp)
  python3 - "$STATDATA" "$FILTERED" << 'PYEOF'
import re, sys
def ok(w):
    if len(w)<=1 and not w.isalpha(): return False
    if not re.search(r'[A-Za-z]',w): return False
    if re.search(r'[0-9]',w): return False
    if w[0] in '#$%&*+-/@': return False
    return sum(1 for c in w if c.isalpha()) >= len(w)*0.5

out = []; valid = False
with open(sys.argv[1]) as f:
    for line in f:
        line = line.strip()
        if not line: continue
        parts = line.split(' ')
        if parts[0] != '*':
            valid = ok(parts[0]) and ok(parts[1])
            if valid: out.append(line)
        else:
            if valid and ok(parts[1]): out.append(line)
with open(sys.argv[2],'w') as f: f.write('\n'.join(out)+'\n')
print(f"  Filtered: {len(out)} lines")
PYEOF

  HW=$(mktemp); WW=$(mktemp)
  "$STAT_BIN" --input "$FILTERED" --output "$HW" \
    --morph-folder "$DICT_DIR" --language English --log-level info
  "$WORD_BIN" --input "$WORDDATA" --output "$WW" \
    --morph-folder "$DICT_DIR" --language English --log-level info
  rm -f "$FILTERED"

  for prefix in l c f; do
    cp "$HW" "$DICT_DIR/${prefix}homoweight.bin"
    cp "$WW" "$DICT_DIR/${prefix}wordweight.bin"
  done
  rm -f "$HW" "$WW"
  info "  Weight binaries installed to $DICT_DIR/{l,c,f}*weight.bin"
}

# ── 5. rebuild daemon + optional restart ─────────────────────────────
step_daemon() {
  info "Step 5/5: Rebuilding SynanDaemon..."
  if [ ! -d "$BUILD_DIR" ]; then
    err "Build dir $BUILD_DIR not found. Run fast_build.sh first."; exit 1
  fi
  cd "$BUILD_DIR"
  cmake --build . --target SynanDaemon -j"$(sysctl -n hw.ncpu 2>/dev/null || echo 4)" \
    2>&1 | tail -3
  cd "$RML"
  info "  SynanDaemon rebuilt."

  if [ "$RESTART" = true ]; then
    info "Restarting SynanDaemon on port 8089..."
    pkill -f SynanDaemon 2>/dev/null || true
    sleep 2
    RML="$RML" "$BUILD_DIR/Source/www/SynanDaemon/SynanDaemon" \
      --host 0.0.0.0 --port 8089 --log-level warning &
    sleep 3
    if curl -s -o /dev/null -w '%{http_code}' \
         'http://localhost:8089?dummy=1&action=syntax&langua=english' \
         -d 'test' 2>/dev/null | grep -q '200'; then
      info "  Daemon is up on port 8089."
    else
      warn "  Daemon may not be responding yet."
    fi
  fi
}

# ── run ───────────────────────────────────────────────────────────────
case "$MODE" in
  full)
    step_dict
    step_morph_bin
    step_gen_freq
    step_compile_weights
    step_daemon
    ;;
  dict)
    step_dict
    step_morph_bin
    ;;
  weights)
    step_gen_freq
    step_compile_weights
    ;;
esac

info "Done ($MODE)."

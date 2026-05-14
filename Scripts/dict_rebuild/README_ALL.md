# RML Dictionary Rebuild Scripts

Complete documentation for rebuilding morphological dictionaries in RML project.

## 📊 Quick Statistics

| Language | Lemmas (from morphs.json) | Word Forms (automaton) | Total Binary Size | WordData Entries |
|----------|---------------------------|----------------------|-------------------|------------------|
| Russian  | ~298,500 models → 298k lemmas | ~4.2 million | **25 MB** (`Dicts/Morph/Russian/`) | 51,084 |
| Ukrainian| ~5,855 models → 419k lemmas | ~4.0 million | **25 MB** (`Dicts/Morph/Ukrainian/`) | 418,983 |
| English  | ~2,639 models → 145k lemmas | ~2.5 million | **94 MB** (`Dicts/Morph/English/`) | 13,933 |
| German   | ~1,319 models → 80k lemmas | ~1.5 million | **12 MB** (`Dicts/Morph/German/`) | 0 (empty) |

**Notes:**
- **Largest binary:** English (94 MB total, mainly `morph.annot` 28 MB)
- **Most lemmas:** Ukrainian (419k) — largest lemma count
- **Most WordData entries:** Ukrainian (418k) — rich frequency corpus
- **Most word forms:** Russian (4.2M) — most comprehensive morphological coverage
- **German:** Has no frequency corpus (WordData.txt empty), so `*wordweight.bin` files are minimal (expected)

## Quick Start

```bash
cd Scripts/dict_rebuild

# Rebuild all language dictionaries
./rebuild_all_dicts.sh

# Or individual languages
./rebuild_russian_dicts.sh
./rebuild_ukrainian_dicts.sh

# Verify only
./verify_russian_dicts.sh
./verify_ukrainian_dicts.sh

# Full cycle with API test
./rebuild_and_test.sh          # Russian
./rebuild_and_test_ukrainian.sh  # Ukrainian
```

## Scripts Overview

| Script | Language | Purpose |
|--------|----------|---------|
| `rebuild_russian_dicts.sh` | Russian | Rebuild Russian dictionaries |
| `verify_russian_dicts.sh` | Russian | Verify Russian dictionaries |
| `rebuild_and_test.sh` | Russian | Rebuild + verify + API test |
| `rebuild_ukrainian_dicts.sh` | Ukrainian | Rebuild Ukrainian dictionaries |
| `verify_ukrainian_dicts.sh` | Ukrainian | Verify Ukrainian dictionaries |
| `rebuild_and_test_ukrainian.sh` | Ukrainian | Rebuild + verify + API test |
| `rebuild_all_dicts.sh` | All | Rebuild all languages at once |
| `README.md` | RU | Detailed documentation (Russian) |
| `README_EN.md` | EN | Quick reference (English) |

## Usage

### Full rebuild (clean build)
```bash
./rebuild_russian_dicts.sh --clean      # Clean + rebuild Russian
./rebuild_ukrainian_dicts.sh --clean    # Clean + rebuild Ukrainian
```

### Quick rebuild (morph_gen already built)
```bash
./rebuild_russian_dicts.sh --skip-build
./rebuild_ukrainian_dicts.sh --skip-build
```

### Verification only
```bash
./verify_russian_dicts.sh
./verify_ukrainian_dicts.sh
```

### All languages at once
```bash
./rebuild_all_dicts.sh            # Rebuild all (Russian, Ukrainian, English, German)
./rebuild_all_dicts.sh --clean    # Clean rebuild all
```

### Full test cycle (includes SynanDaemon API check)
```bash
./rebuild_and_test.sh
./rebuild_and_test_ukrainian.sh
```

## What Gets Built

The scripts rebuild binary dictionary files from source JSON/TXT data:

**Source (edit these):**
- `Source/morph_dict/data/<Language>/morphs.json` — morphological models (33 MB RU, 39 MB UK)
- `Source/morph_dict/data/<Language>/WordData.txt` — words with frequency
- `Source/morph_dict/data/<Language>/gramtab.json` — grammatical codes

**Output (used by daemons):**
- `Dicts/Morph/<Language>/morph.bases` — lemmas base (2–4 MB)
- `Dicts/Morph/<Language>/morph.annot` — annotations (5–8 MB)
- `Dicts/Morph/<Language>/morph.forms_autom` — morphological automaton (6–9 MB)
- `Dicts/Morph/<Language>/gramtab.json` — grammar codes copy
- `Dicts/Morph/<Language>/morph.options` — options
- `Dicts/Morph/<Language>/npredict.bin` — unknown word predictor
- `Dicts/Morph/<Language>/*wordweight.bin` — frequency tables (lemma/homonym)
- `Dicts/Morph/<Language>/*homoweight.bin` — homonym weights

## Language-Specific Notes

### Russian
Largest dictionary (~298k lemmas, 4.2M word forms). Includes all rebuild-related verbs: перестроить, відновити, реконструювати.

### Ukrainian
~418k lemmas, 4.0M word forms. Uses both `відбудувати` and `відновити` for rebuild semantics.

### English / German
Also supported via same scripts. Use `rebuild_<language>_dicts.sh` pattern (e.g., `rebuild_english_dicts.sh`).

## Prerequisites

- CMake ≥ 3.24
- C++17 compiler (gcc ≥ 9, clang ≥ 10, MSVC ≥ 2019)
- Flex and Bison
- zlib
- (Optional) Python3 for JSON validation
- (Optional) curl for API testing

### macOS (Homebrew)
```bash
brew install cmake zlib flex bison libevent
export FLEX_TOOL=/opt/homebrew/opt/flex/bin/flex
export BISON_TOOL=/opt/homebrew/opt/bison/bin/bison
```

### Ubuntu/Debian
```bash
sudo apt-get install build-essential cmake zlib1g-dev flex bison libevent-dev
```

## Starting Daemons

After rebuilding dictionaries, restart daemons:

```bash
# Terminal 1: Semantic analyzer
RML=$(pwd) ./Bin/SemanDaemon --host 127.0.0.1 --port 8081

# Terminal 2: Syntactic/morphological analyzer
RML=$(pwd) ./Bin/SynanDaemon --host 127.0.0.1 --port 8082

# Test API
curl -G --data-urlencode "action=morph" \
     --data-urlencode "langua=Russian" \
     --data-urlencode "query=перестроить" \
     http://127.0.0.1:8082/
```

## Troubleshooting

**`RML environment variable is not set`**
```bash
export RML=$(pwd)
```

**`morph_gen: command not found`**
```bash
./rebuild_russian_dicts.sh --clean   # Full clean rebuild
```

**Permission denied**
```bash
chmod +x Scripts/dict_rebuild/*.sh
```

**Flex/Bison not found on macOS**
```bash
brew install flex bison
export FLEX_TOOL=/opt/homebrew/opt/flex/bin/flex
export BISON_TOOL=/opt/homebrew/opt/bison/bin/bison
```

## Directory Structure

```
RML/
├── Dicts/Morph/
│   ├── Russian/      ← Binary output (rebuilt)
│   ├── Ukrainian/    ← Binary output (rebuilt)
│   ├── English/      ← Binary output
│   └── German/       ← Binary output
└── Source/morph_dict/data/
    ├── Russian/      ← Source (edit here)
    ├── Ukrainian/    ← Source (edit here)
    ├── English/      ← Source
    └── German/       ← Source
```

## Adding Dictionary Entries

To add new words to any language dictionary:

1. Edit the appropriate `WordData.txt` in `Source/morph_dict/data/<Language>/`
2. Format: `слово;INFINITIVE trans,perf,; частота`
3. Run rebuild: `./Scripts/dict_rebuild/rebuild_<lang>_dicts.sh --skip-build`
4. Verify: `./Scripts/dict_rebuild/verify_<lang>_dicts.sh`
5. Restart daemons if running

## Test Sentences

### Russian
`Мы хотим перестроить здание и восстановить фасад.`

### Ukrainian
`Ми хочемо відбудувати будинок і відновити фасад.`

## References

- RML Project: https://github.com/bivex/aot
- Official site: http://www.aot.ru (Russian)
- Morph dict submodule: `Source/morph_dict/README.md`

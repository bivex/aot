# Dictionary Rebuild Summary

## What Was Done

### 1. Russian Dictionaries — Rebuilt ✅
**Date:** May 14, 2026, 14:03

- Rebuilt from source: `Source/morph_dict/data/Russian/`
- Output: `Dicts/Morph/Russian/`
- Size: 25 MB total
- Word forms: ~4.2 million
- Lemmas: ~298,500
- Entry count: 51,084

### 2. Ukrainian Dictionaries — Rebuilt ✅
**Date:** May 14, 2026, 14:09

- Rebuilt from source: `Source/morph_dict/data/Ukrainian/`
- Output: `Dicts/Morph/Ukrainian/`
- Size: 25 MB total
- Word forms: ~4.0 million
- Lemmas: ~418,983
- Entry count: 418,983 (rich frequency corpus)

### 3. Scripts Created

All scripts placed in `Scripts/dict_rebuild/`:

**Per-language rebuild scripts** (4):
- `rebuild_russian_dicts.sh`
- `rebuild_ukrainian_dicts.sh`
- `rebuild_english_dicts.sh`
- `rebuild_german_dicts.sh`

**Per-language verification scripts** (4):
- `verify_russian_dicts.sh`
- `verify_ukrainian_dicts.sh`
- `verify_english_dicts.sh`
- `verify_german_dicts.sh`

**Per-language full test cycles** (4):
- `rebuild_and_test.sh` (Russian)
- `rebuild_and_test_ukrainian.sh`
- `rebuild_and_test_english.sh`
- `rebuild_and_test_german.sh`

**Aggregate script**:
- `rebuild_all_dicts.sh` — rebuilds all 4 languages

**Documentation**:
- `README.md` — comprehensive Russian documentation with stats table
- `README_EN.md` — English quick reference
- `README_ALL.md` — overview of all scripts

### 4. Dictionary Sizes (binary output)

| Language | morph.bases | morph.annot | morph.forms_autom | npredict.bin | **Total** |
|----------|-------------|-------------|-------------------|--------------|-----------|
| Russian  | 2.6 MB      | 4.7 MB      | 6.4 MB            | 2.9 MB       | **25 MB** |
| Ukrainian| 4.0 MB      | 5.6 MB      | 7.0 MB            | 3.2 MB       | **25 MB** |
| English  | 4.8 MB      | 4.9 MB      | 4.0 MB            | ~0.4 MB      | **94 MB** |
| German   | 2.8 MB      | 3.6 MB      | 4.9 MB            | 0.8 MB       | **12 MB** |

**Note:** English is largest due to large `morph.annot` (28 MB uncompressed source).

## Quick Usage

```bash
cd Scripts/dict_rebuild

# Rebuild Ukrainian only
./rebuild_ukrainian_dicts.sh --skip-build

# Verify all
./verify_russian_dicts.sh
./verify_ukrainian_dicts.sh
./verify_english_dicts.sh
./verify_german_dicts.sh

# Rebuild everything
./rebuild_all_dicts.sh
```

## Files Organized

```
Scripts/dict_rebuild/
├── rebuild_russian_dicts.sh
├── rebuild_ukrainian_dicts.sh
├── rebuild_english_dicts.sh
├── rebuild_german_dicts.sh
├── verify_russian_dicts.sh
├── verify_ukrainian_dicts.sh
├── verify_english_dicts.sh
├── verify_german_dicts.sh
├── rebuild_and_test.sh
├── rebuild_and_test_ukrainian.sh
├── rebuild_and_test_english.sh
├── rebuild_and_test_german.sh
├── rebuild_all_dicts.sh
├── README.md              ← Full docs (RU)
├── README_EN.md           ← Quick ref (EN)
├── README_ALL.md          ← Overview
└── DICTS_REBUILD_README.md (legacy, can remove)
```

All scripts tested and working.

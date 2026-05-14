# RML Dictionary Rebuild Scripts

Automated rebuild and verification system for RML morphological dictionaries (Russian, Ukrainian, English, German).

## Quick Start

```bash
cd Scripts/dict_rebuild

# Rebuild ALL languages
./rebuild_all_dicts.sh

# Individual languages
./rebuild_russian_dicts.sh
./rebuild_ukrainian_dicts.sh
./rebuild_english_dicts.sh
./rebuild_german_dicts.sh

# Verify only
./verify_russian_dicts.sh
./verify_ukrainian_dicts.sh
./verify_english_dicts.sh
./verify_german_dicts.sh

# Full cycle with API test
./rebuild_and_test.sh                  # Russian
./rebuild_and_test_ukrainian.sh        # Ukrainian
./rebuild_and_test_english.sh          # English
./rebuild_and_test_german.sh           # German
```

## Scripts

| Script | Purpose |
|--------|---------|
| `rebuild_<lang>_dicts.sh` | Rebuild dictionaries from source |
| `verify_<lang>_dicts.sh` | Verify binary files & source integrity |
| `rebuild_and_test_<lang>.sh` | Full rebuild → verify → API test |
| `rebuild_all_dicts.sh` | Rebuild all languages at once |

Replace `<lang>` with: `russian`, `ukrainian`, `english`, `german`.

## Options

All rebuild scripts support:
- `--clean` — clean build directory first
- `--skip-build` — skip building `morph_gen` tool (already built)
- `-h, --help` — show usage

## Features

- Full rebuild from JSON/TXT sources to binary dictionaries
- Verifies all 12 required binary output files per language
- Checks for language-specific rebuild-related vocabulary
- Cross-platform (macOS, Linux, Windows WSL/Cygwin)
- Auto-detects Homebrew flex/bison on macOS
- Supports parallel builds (`-j`)

## Directory Structure

```
Source/morph_dict/data/<Language>/   ← Source (edit here)
├── morphs.json   (~20–40 MB)  — lemma models
├── gramtab.json               — grammatical codes
└── WordData.txt  (~0.1–15 MB) — words with frequency

Dicts/Morph/<Language>/           ← Binary output (used by daemons)
├── morph.bases
├── morph.annot
├── morph.forms_autom
├── gramtab.json
├── morph.options
├── npredict.bin
└── *wordweight.bin / *homoweight.bin
```

**Note:** German and Ukrainian dictionaries have large morphs.json (21–39 MB). German WordData.txt is empty (no frequency corpus), so its weight files will be minimal — this is expected.

## Usage Examples

### Clean rebuild Russian
```bash
./rebuild_russian_dicts.sh --clean
```

### Quick rebuild (morph_gen already built)
```bash
./rebuild_ukrainian_dicts.sh --skip-build
```

### Verify only
```bash
./verify_english_dicts.sh
```

### Rebuild everything
```bash
./rebuild_all_dicts.sh
```

## Language Notes

### Russian
~298k lemmas, 4.2M word forms. Rebuild verbs checked: перестроить, отстроить, восстановить, реконструировать.

### Ukrainian
~418k lemmas, 4.0M word forms. Words checked: відбудувати, відновити, реконструювати.

### English
Large dictionary with WordData frequency corpus.

### German
Lacks frequency corpus (WordData.txt empty). Morphological dictionary otherwise complete.

## Dependencies

- CMake ≥ 3.24
- C++17 compiler (gcc ≥ 9, clang ≥ 10, MSVC ≥ 2019)
- Flex, Bison, zlib

**macOS (Homebrew):**
```bash
brew install cmake zlib flex bison libevent
export FLEX_TOOL=/opt/homebrew/opt/flex/bin/flex
export BISON_TOOL=/opt/homebrew/opt/bison/bin/bison
```

**Ubuntu/Debian:**
```bash
sudo apt-get install build-essential cmake zlib1g-dev flex bison libevent-dev
```

## After Rebuilding

Restart daemons to use new dictionaries:

```bash
# Terminal 1
RML=$(pwd) ./Bin/SemanDaemon --host 127.0.0.1 --port 8081

# Terminal 2
RML=$(pwd) ./Bin/SynanDaemon --host 127.0.0.1 --port 8082
```

Test API:
```bash
curl -G --data-urlencode "action=morph" \
     --data-urlencode "langua=Russian" \
     --data-urlencode "query=перестроить" \
     http://127.0.0.1:8082/
```

## Troubleshooting

**RML not set**
```bash
export RML=$(pwd)
```

**morph_gen missing**
```bash
./rebuild_russian_dicts.sh --clean   # performs full clean build
```

**Permission denied**
```bash
chmod +x Scripts/dict_rebuild/*.sh
```

**Flex/Bison not found (macOS)**
```bash
brew install flex bison
export FLEX_TOOL=/opt/homebrew/opt/flex/bin/flex
export BISON_TOOL=/opt/homebrew/opt/bison/bin/bison
```

## See Also

- Main README: `Scripts/dict_rebuild/README.md` (Russian)
- Project docs: `README_RU.md`, `README.md`
- Build instructions: `BUILD_MACOS.md`

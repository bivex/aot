# Russian Dictionary Management Scripts

Automated rebuild and verification system for RML Russian morphological dictionaries.

## Quick Start

```bash
cd Scripts/dict_rebuild
./rebuild_and_test.sh          # Full cycle: rebuild → verify → test
```

Or individual steps:
```bash
./rebuild_russian_dicts.sh     # Rebuild dictionaries only
./verify_russian_dicts.sh      # Verify dictionaries are correct
```

## Files

- `rebuild_russian_dicts.sh` — rebuilds Russian dictionaries from source
- `verify_russian_dicts.sh` — checks all binary files and source integrity
- `rebuild_and_test.sh` — full pipeline including API test
- `README.md` — detailed documentation (Russian)

## Features

- Full rebuild from `Source/morph_dict/data/Russian/` to `Dicts/Morph/Russian/`
- Verifies presence of all 12 required binary output files
- Checks for rebuild-related verbs: перестроить, отстроить, восстановить, реконструировать
- Supports clean builds (`--clean`) and skip-build (`--skip-build`)
- Cross-platform: macOS, Linux, Windows (WSL/Cygwin)
- Auto-detects Homebrew flex/bison on macOS

## Usage

```bash
# Clean rebuild (delete build/ first)
./rebuild_russian_dicts.sh --clean

# Quick rebuild (morph_gen already built)
./rebuild_russian_dicts.sh --skip-build

# Just verify current state
./verify_russian_dicts.sh

# Full rebuild + API test
./rebuild_and_test.sh
```

See `README.md` inside this directory for complete documentation.

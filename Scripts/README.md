# Scripts Directory

This directory contains utility scripts for the RML project.

## Subdirectories

### `dict_rebuild/`
Scripts for rebuilding and verifying Russian morphological dictionaries.

- `rebuild_russian_dicts.sh` — Full rebuild of Russian dictionaries from source
- `verify_russian_dicts.sh` — Verification that dictionaries are correctly built
- `rebuild_and_test.sh` — Complete cycle: rebuild → verify → API test
- `README.md` — Detailed documentation (Russian)

See [dict_rebuild/README.md](dict_rebuild/README.md) for full usage instructions.

## Adding New Scripts

When adding scripts to this directory:

1. Add a short comment at the top with usage
2. Make executable: `chmod +x scriptname.sh`
3. Document in this README if it's generally useful
4. Prefer descriptive names over short ones

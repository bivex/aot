# Adding a New Language to AOT Morphological Dictionary

This document describes all steps required to add a new language to the AOT morphological dictionary system, based on the Spanish integration. Replace `LANG` with your language name (e.g. `French`, `Italian`).

---

## Overview

The integration touches two git repositories:
- **Main repo** (`aot`) — submodules, converters, scripts, registry config
- **Submodule** (`Source/morph_dict`) — all C++ code and morphological data

---

## Step 1: Language Enum

**File:** `Source/morph_dict/common/base_types.h`

Add a new value to `MorphLanguageEnum`:

```cpp
typedef enum {
    ...
    morphSpanish = 9,
    morphLANG = 10,       // <-- add here
} MorphLanguageEnum;
```

## Step 2: String Mappings

**File:** `Source/morph_dict/common/utilit.cpp`

### GetLanguageByString (parsing)
Add before the final `return false;`:

```cpp
else if(s == "LANG_UPPER"){
    Result = morphLANG;
    return true;
}
```

### GetStringByLanguage (display)
Add a case in the switch:

```cpp
case morphLANG: return "LANG";
```

## Step 3: GramTab Class

Create two new files patterned after an existing gramtab (e.g. `EngGramTab` or `SpaGramTab`).

### `Source/morph_dict/agramtab/LangGramTab.h`

Key decisions:
- **Gramcode encoding**: If the language needs more than ~70 gramcodes, use uppercase 2-char codes (`AA`-`ZZ`, `eStartUp = 0x4141`) like Ukrainian/Spanish. For small tagsets, lowercase (`aa`-`zz`, `eStartUp = 0x6161`) like English works.
- **POS enum**: Define all parts of speech for the language.
- **Grammem enum**: Define all grammatical categories (number, gender, case, tense, mood, person, etc.).
- Override all virtual methods from `CAgramtab`. Many can be stubs returning `false`.

```cpp
#pragma once
#include "morph_dict/agramtab/agramtab.h"

// POS enum
const size_t LANG_PART_OF_SPEECH_COUNT = N;
enum { langNOUN=0, langVERB, ... };

// Grammem enum
const size_t LANG_GRAMMEMS_COUNT = M;
enum { sgSingular=1, sgPlural=sgSingular<<1, ... };

class CLangGramTab : public CAgramtab {
public:
    CLangGramTab();
    // ... override all virtual methods
};
```

### `Source/morph_dict/agramtab/LangGramTab.cpp`

Implement:
- POS/grammem string arrays (indexed by enum values)
- `GleicheGenderNumber` — gender+number agreement
- `GleicheSubjectPredicate` — person+number agreement
- `IsMorphNoun`, `is_morph_adj`, `is_verb_form` — POS identification
- `PartOfSpeechIsProductive` — which POS can generate new words
- Stub methods for features not applicable to the language

### `Source/morph_dict/agramtab/CMakeLists.txt`

Add the new `.cpp` and `.h` to `AgramtabLib` sources.

## Step 4: Lemmatizer Class

### `Source/morph_dict/lemmatizer_base_lib/Lemmatizers.h`

Add a class that inherits from `CLemmatizer`:

```cpp
class CLemmatizerLANG : public CLemmatizer {
public:
    CLemmatizerLANG();
};
```

### `Source/morph_dict/lemmatizer_base_lib/Lemmatizers.cpp`

```cpp
CLemmatizerLANG::CLemmatizerLANG() : CLemmatizer(morphLANG) {}
```

## Step 5: Factory Registration

### `Source/morph_dict/lemmatizer_base_lib/MorphanHolder.cpp`

Add the include:
```cpp
#include "morph_dict/agramtab/LangGramTab.h"
```

Three switch statements need new cases:

1. **LoadOnlyGramtab**:
```cpp
case morphLANG: m_pGramTab = new CLangGramTab; break;
```

2. **LoadOnlyLemmatizer**:
```cpp
case morphLANG: m_pLemmatizer = new CLemmatizerLANG; break;
```

3. **Global holder + GetHolder**:
```cpp
CMorphanHolder LangHolder;

const CMorphanHolder& GetHolder(MorphLanguageEnum lang) {
    switch(lang) {
        ...
        case morphLANG: return LangHolder;
    }
}
```

### `Source/morph_dict/morph_wizard/wizard.cpp`

Add include and case in `load_gramtab`:
```cpp
#include "morph_dict/agramtab/LangGramTab.h"

case morphLANG: pGramTab = new CLangGramTab; break;
```

## Step 6: Encoding Support

### `Source/morph_dict/common/single_byte_encoding.cpp`

Add cases in three dispatch functions. For Latin-script languages, reuse English functions:

```cpp
// is_upper_vowel:
case morphLANG: return is_english_upper_vowel(x);

// is_lower_alpha:
case morphLANG: return is_english_lower(x);

// is_upper_alpha:
case morphLANG: return is_english_upper(x);
```

For non-Latin scripts (Cyrillic, etc.), write language-specific checker functions.

### `Source/morph_dict/common/utf8.cpp`

Add UTF-8 validation. For Latin-script languages:

```cpp
case morphLANG: return CheckEnglishUtf8(s);
```

For non-Latin, write a `IsUnicodeLANG` function and a `CheckLANGUtf8` wrapper.

## Step 7: UniMorph Converter (Python)

### `dev/lang_conv/unimorph_lang_to_aot.py`

Write a converter that reads UniMorph TSV (`lemma\tword\ttags`) and produces:
- `Source/morph_dict/data/LANG/morphs.json` — flexia_models + lemmas
- `Source/morph_dict/data/LANG/gramtab.json` — gramcode → POS + grammems

Key points:
- Strip accents/diacritics if the language uses single-byte encoding (AOT uses Windows-1252 for Latin scripts)
- Only allow characters A-Z after stripping (no apostrophes, hyphens, or Unicode)
- Map UniMorph POS tags to AOT POS names
- Map UniMorph feature tags to AOT grammem names
- Generate 2-character gramcodes (AA, AB, AC, ...)
- Find a `plug_noun_gram_code` for the default noun gramcode

## Step 8: Data Files

### `Source/morph_dict/data/LANG/`

Create these files:
- `project.mwz` — MorphWizard project (can be minimal JSON)
- `README.md` — brief description
- `WordData.txt` — empty or with frequency data
- `StatData.txt` — empty or with statistics

### UniMorph submodule

```
git submodule add https://github.com/unimorph/XXX.git Dicts/Morph/LANG/unimorph
```

## Step 9: Registry Config

### `Bin/rml.ini`

Add the lemmatizer dict path:

```
Software\Dialing\Lemmatizer\LANG\DictPath $RML/Dicts/Morph/LANG/
```

## Step 10: CMake Build Integration

### `Source/morph_dict/data/CMakeLists.txt`

Add the macro call and dependency:

```cmake
CreateAllMorphBinFiles(LANG)

add_custom_target(
    MorphDicts
    DEPENDS ... Spanish_Morph LANG_Morph
)
```

## Step 11: Rebuild Script

### `Scripts/dict_rebuild/rebuild_LANG_dicts.sh`

Based on `rebuild_english_dicts.sh`. Steps:
1. Run UniMorph converter
2. Build binary dicts with `morph_gen`
3. Generate prediction data with `StatDatBin`
4. Generate word weights with `word_freq_bin`

## Step 12: Tests

### Python test: `tests/test_lang.py`

Uses `TestLem --morphan` subprocess to verify word analysis:
```python
test_cases = [
    ("WORD", "NOUN", ["fem", "sg"], True),
    ...
]
```

### C++ test input: `Source/morph_dict/test_lem/test/LANG/morphan.txt`

List of test words (one per line).

### Canonical output: `morphan.txt.morph.canon`

Generate by running `TestLem --morphan` and saving the output.

### CTest registration: `Source/morph_dict/test_lem/CMakeLists.txt`

```cmake
TestLemLang(LANG test/LANG/morphan.txt --morphan)
```

### GramTab uniqueness: `Source/morph_dict/agramtab/tests/CheckGramTab/test_gramtab.cpp`

```cpp
#include "morph_dict/agramtab/LangGramTab.h"

CLangGramTab l;
check_uniq(l);
```

## Step 13: Build and Verify

```bash
# 1. Run converter
python3 dev/lang_conv/unimorph_lang_to_aot.py

# 2. Build
cd build && cmake .. -DCMAKE_BUILD_TYPE=Release
cmake --build . -- -j$(nproc)

# 3. Generate binary dicts
bash Scripts/dict_rebuild/rebuild_LANG_dicts.sh

# 4. Run tests
RML=/path/to/aot python3 tests/test_lang.py
RML=/path/to/aot ./build/Source/morph_dict/agramtab/tests/CheckGramTab/test_gramtab
```

## Step 14: Git Commits

Two commits needed:

1. **Submodule** (`Source/morph_dict/): commit all C++ changes and data files
2. **Main repo**: commit submodule pointer update, converter, rebuild script, rml.ini, tests

---

## Checklist

| Step | File(s) | Done |
|------|---------|------|
| 1. Enum value | `base_types.h` | |
| 2. String mappings | `utilit.cpp` | |
| 3. GramTab class | `LangGramTab.h`, `LangGramTab.cpp`, `CMakeLists.txt` | |
| 4. Lemmatizer class | `Lemmatizers.h`, `Lemmatizers.cpp` | |
| 5. Factory registration | `MorphanHolder.cpp`, `wizard.cpp` | |
| 6. Encoding support | `single_byte_encoding.cpp`, `utf8.cpp` | |
| 7. Converter script | `dev/lang_conv/` | |
| 8. Data files | `data/LANG/`, UniMorph submodule | |
| 9. Registry | `Bin/rml.ini` | |
| 10. CMake build | `data/CMakeLists.txt` | |
| 11. Rebuild script | `Scripts/dict_rebuild/` | |
| 12. Tests | Python + CTest + C++ | |
| 13. Build & verify | | |
| 14. Git commits | Submodule + main repo | |

# English Morphology Converter (`unimorph_to_aot_v4.py`)

This Python script is the primary tool for generating the English morphological dictionary used by the AOT engine. It merges multiple linguistic resources into a single, consistent JSON structure (`morphs.json` and `gramtab.json`), which is later compiled into high-performance binary files.

## 1. Overview
The converter processes raw inflection data, handles irregular paradigms, maps external part-of-speech (POS) tags to internal AOT standards, and optimizes the dictionary size by deduplicating inflectional models.

## 2. Data Sources
The script integrates three main types of resources:
*   **AGID (Automatically Generated Inflection Database):** Provides high-quality inflectional data for ~40,000 English verbs, nouns, and adjectives.
*   **UniMorph English:** A large-scale morphological dataset used to broaden the vocabulary coverage beyond the core dictionary.
*   **all.eng:** The legacy AOT base dictionary used to ensure consistency with existing closed-class words (prepositions, conjunctions, etc.).

## 3. Key Features

### Manual Paradigm Injection (Closed Classes)
To ensure 100% accuracy for critical linguistic units, the script manually injects hardcoded paradigms for:
*   **Suppletive Verbs:** `BE`, `HAVE`, `DO`.
*   **Personal Pronouns:** `I`, `ME`, `MY`, `MINE`, `YOU`, `HE`, `SHE`, `IT`, `WE`, `THEY` (including case and gender tagging).
*   **Particles:** `NOT`, `NEVER`.

### POS and Tag Mapping
The converter translates various tagging systems into the internal AOT Latin POS system:
*   **VBE (Verb BE):** The verb "to be" is separated from standard `VERB` to assist the syntactic analyzer in identifying copulas.
*   **Participle Mapping:** 
    *   `PRS;V.PTCP` (Present Participle) → internal tag `ing` (e.g., *running*).
    *   `PST;V.PTCP` (Past Participle) → internal tag `pp` (e.g., *broken*).
*   **Grammatical Categories:** Maps number (sg/pl), tense (prsa/pasa), person (1/2/3), and case (obj).

### Dictionary Optimization
*   **Stemming Logic:** Automatically identifies the longest common prefix (stem) for a group of word forms.
*   **Flexia Models:** Identical sets of endings are grouped into shared "flexia models," significantly reducing the final binary size.
*   **Gramcode Generation:** Automatically generates unique 2-character codes for every unique combination of POS and grammatical tags.

## 4. Technical Workflow
1.  **Initialize:** Load hardcoded paradigms for pronouns and auxiliary verbs.
2.  **Load AGID:** Parse `agid-infl.txt` to extract verb tenses and noun plurals.
3.  **Load UniMorph:** Supplement the dictionary with additional lemmas, applying fixes for known bugs (e.g., the `RIN/RUN` lemma error).
4.  **Merge `all.eng`:** Ensure all base words from the legacy source are present.
5.  **Build Gramtab:** Generate the grammatical table mapping codes to POS and attributes.
6.  **Export JSON:** Save the processed data to `morphs.json` and `gramtab.json` in the `Dicts/Morph/English/` directory.

## 5. Output Files
The script produces two files required by the `morph_gen` utility:
*   **`morphs.json`:** Contains the list of lemmas, their associated flexia models, and stems.
*   **`gramtab.json`:** Defines the grammatical categories, parts of speech, and mapping codes used in the dictionary.

## 6. Implementation Notes
*   **Casing:** All entries are converted to `UPPERCASE` to match the AOT engine's internal standard.
*   **POS Hierarchy:** The script supports 17 distinct POS tags, including `PN` (Proper Noun), `PN_ADJ` (Proper Adjective), and `ORDNUM` (Ordinal Number).
*   **Filtering:** Words containing non-standard characters (except hyphens and apostrophes) are filtered out during conversion.

---

### Usage
The script is typically invoked by the master rebuild script:
```bash
python3 dev/unimorph_conv/unimorph_to_aot_v4.py
```
After execution, run `morph_gen` to compile the resulting JSON files into binary format.

# English Language Resources in AOT

This document provides an overview of the English language dictionaries, grammatical resources, and semantic tools available in the project.

## 1. Morphological Dictionary
The morphology system is based on a comprehensive lemma list used for lemmatization and grammatical analysis.

*   **Source File:** `Dicts/SrcBinDict/all.eng` (~1.7 MB)
*   **Lemma Count:** **104,512** entries.
*   **Format:** Tab-separated list containing `Part-of-Speech`, `Lemma`, and `Internal ID`.
*   **Binary Files:** Located in `Dicts/Morph/English/`.
    *   `morph.bases`: Base forms.
    *   `morph.annot`: Morphological annotations.
    *   `gramtab.json`: Grammatical tables defining categories and tags.

## 2. Semantic-Syntactic Dictionary (AOSS)
AOSS (Advanced Open Semantic System) describes the deep structure of the language, including valencies and semantic roles.

*   **Location:** `Dicts/Aoss/`
*   **Main File:** `ross.txt` (1.3 MB)
*   **Article Count:** **2,227** `TITLE` entries.
*   **Usage:** Used for semantic parsing, disambiguation, and structural analysis.

## 3. Translation and Synonyms
The project includes large-scale databases for Russian-English translation and lexical relations.

*   **Russian-English Dictionary:** `Dicts/SrcBinDict/dict2809.txt` (**218,843** entries, 7.9 MB). Provides English equivalents for Russian words with frequency/context weights.
*   **Synonyms:** `Dicts/SrcBinDict/synonyms.txt` (**10,108** lines).

## 4. Specialized Resources
*   **Proper Names:** `Dicts/GraphAn/enames.txt` (**9,877** names). Used by the graphematic analyzer to identify people/entities.
*   **Abbreviations:** `Dicts/GraphAn/abbr.eng` (**154** entries). Lists common English abbreviations (e.g., `Mr.`, `Approx.`).
*   **Phrases & Idioms:** `Dicts/EngObor/ross.txt` (**461** entries). Describes multi-word expressions.
*   **Collocations:** `Dicts/EngCollocs/ross.txt` (**130** entries). Common word pairings.

## 5. Statistical and Linkage Data
*   **Link Grammar Data:** `Dicts/SrcBinDict/wt.link` (18 MB). Contains linkage patterns used for syntactic parsing and evaluating sentence structure probability.

## 6. Syntax Analysis (EngSynan)
*   **Location:** `Dicts/EngSynan/`
*   **Rules:** `synan.grm` and `src/simple_syn.grm`.
*   **Function:** Defines the grammar rules for the English syntactic analyzer.

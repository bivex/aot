# AOT C++ Components Overview

This document provides an inventory of the C++ executables and libraries available in the AOT project.

## 1. Daemons and Server Components
These programs provide HTTP/JSON interfaces for integration with web services.

*   **`SynanDaemon`**: The primary HTTP server for syntactic analysis. It processes text and returns dependency trees or phrasal groups.
*   **`SemanDaemon`**: HTTP server for semantic analysis, word disambiguation, and dictionary lookups.
*   **`SynanDaemonAWS`**: A specialized version of the syntactic daemon optimized for execution in AWS Lambda environments.

## 2. Morphological Tools
Used for building, testing, and inspecting morphological dictionaries.

*   **`morph_gen`**: The core compiler that transforms morphological data (JSON/MRD) into high-performance binary files (`morph.bin`, `morph.bases`, etc.).
*   **`TestLem`**: A command-line utility for testing the lemmatization of individual words.
*   **`FileLem`**: A batch processor that lemmatizes entire text files and saves the results in `.lem` format.
*   **`lemma_print`**: An inspection tool that dumps all lemmas and their associated grammatical information from a dictionary.
*   **`StatDatBin` / `word_freq_bin`**: Compilers for statistical weighting data, used to resolve morphological and syntactic homonymy.

## 3. Dictionary Utilities (`Dicts`)
Tools for managing various types of dictionaries and lexical resources.

*   **`BinaryDictsClient`**: A diagnostic tool for validating and querying binary dictionary files.
*   **`StructDictLoader`**: Utility for loading and converting structured dictionary formats.
*   **`GenFreqDict`**: A generator for frequency dictionaries based on input corpora.
*   **`AprDictGen`**: Tool for generating "apriori" dictionaries.
*   **`asp_read` / `deriv_read`**: Specialized readers for processing semantic articles (ASP) and derivational relations.

## 4. Syntax and Semantics Debugging
Specialized tools for linguistic developers to test rules and data structures.

*   **`TestSynan` / `TestMapost`**: Debugging utilities for the syntactic analyzer and post-morphological processing rules.
*   **`TestSeman`**: Testing tool for semantic relations and the Advanced Open Semantic System (AOSS).
*   **`SimpleGrammarPrecompiled`**: A tool to precompile `.grm` files into binary tables to accelerate daemon startup.

## 5. Graphematics and Statistical Indexing
Tools for lower-level text processing and high-level disambiguation.

*   **`GraphmatThick`**: A comprehensive graphematic analyzer that handles tokenization, sentence splitting, and paragraph detection.
*   **`BigramsIndex` / `Text2Bigrams`**: Tools for creating and indexing word bigrams to improve the accuracy of statistical analysis.

## 6. Core Libraries
The project is built upon several shared libraries:

*   **`LemmatizerLib`**: The heart of the morphological engine.
*   **`SynanLib` / `EngSynanLib` / `RusSynanLib`**: Language-specific and common syntactic processing logic.
*   **`SemanLib`**: Semantic processing and AOSS management.
*   **`GraphanLib`**: Low-level tokenization and character analysis.
*   **`aot_common`**: Shared utilities, networking, logging, and base classes.

---

### Location of Binaries
After compilation with `fast_build.sh`, executables are typically located in:
`build_fast/Source/...` (e.g., `build_fast/Source/www/SynanDaemon/SynanDaemon`).

cmake_minimum_required(VERSION 3.5)
project (LatSynan)

CompileSimpleGrammar(LatSynanGrammar synan.grm ${PROJECT_SOURCE_DIR}/synan.table Latin)

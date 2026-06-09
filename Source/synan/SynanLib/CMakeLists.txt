declare_cmake_min_version()

project(SynanLib)

add_library(SynanLib
        SentencesCollection.cpp
        SyntaxHolder.cpp
        SpaSyntaxOpt.cpp
        SpaSentence.cpp
        SpaFormatCaller.cpp
        SentencesCollection.h
        SyntaxHolder.h
        SpaSyntaxOpt.h
        SpaSentence.h
        SpaFormatCaller.h
)

target_link_libraries(SynanLib
    LemmatizerLib
    GerPostMorph
    MAPostLib
    SimpleGrammarLib
    SynCommonLib
    RusSynanLib
    GerSynanLib
    UkrSynanLib
    EngSynanLib
)

if (BUILD_DICTS)
    add_dependencies(SynanLib Ross)
endif()

# Tests disabled on macOS due to compatibility issues
if(NOT APPLE)
    add_subdirectory(tests)
endif()

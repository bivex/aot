declare_cmake_min_version()

project(SynanLib)

add_library(SynanLib
        SentencesCollection.cpp
        SyntaxHolder.cpp
        SpaSyntaxOpt.cpp
        SpaSentence.cpp
        SpaFormatCaller.cpp
        LatSyntaxOpt.cpp
        LatSentence.cpp
        LatFormatCaller.cpp
        FreSyntaxOpt.cpp
        FreSentence.cpp
        FreFormatCaller.cpp
        PorSyntaxOpt.cpp
        PorSentence.cpp
        PorFormatCaller.cpp
        FinSyntaxOpt.cpp
        FinSentence.cpp
        FinFormatCaller.cpp
        ItSyntaxOpt.cpp
        ItSentence.cpp
        ItFormatCaller.cpp
        SentencesCollection.h
        SyntaxHolder.h
        SpaSyntaxOpt.h
        SpaSentence.h
        SpaFormatCaller.h
        LatSyntaxOpt.h
        LatSentence.h
        LatFormatCaller.h
        FreSyntaxOpt.h
        FreSentence.h
        FreFormatCaller.h
        PorSyntaxOpt.h
        PorSentence.h
        PorFormatCaller.h
        FinSyntaxOpt.h
        FinSentence.h
        FinFormatCaller.h
        ItSyntaxOpt.h
        ItSentence.h
        ItFormatCaller.h
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

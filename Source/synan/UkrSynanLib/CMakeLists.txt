declare_cmake_min_version()

project(UkrSynanLib)

add_library(UkrSynanLib
        UkrSentence.cpp
        UkrSentence.h
        UkrSyntaxOpt.cpp
        UkrSyntaxOpt.h
        UkrFormatCaller.cpp
        UkrFormatCaller.h
        UkrOborDic.cpp
        UkrOborDic.h
        UkrThesaurus.h
)

target_link_libraries(UkrSynanLib
    SynCommonLib
    AgramtabLib
)

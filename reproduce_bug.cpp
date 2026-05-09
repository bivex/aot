#include "morph_dict/lemmatizer_base_lib/MorphanHolder.h"
#include "morphan/LemmatizerLib/LemTextCreator.h"
#include <iostream>

int main() {
    try {
        MorphLanguageEnum lang = morphEnglish;
        CLemTextCreator creator(lang);
        creator.InitGraphan();
        int count = 0;
        if (!creator.BuildLemText("The cat sat on a mat", false, count)) {
            std::cerr << "BuildLemText failed" << std::endl;
            return 1;
        }
        const CLemmatizedText& text = creator.GetLemText();
        for (int i = 0; i < text.GetWordsCount(); ++i) {
            const CLemWord& w = text.GetWord(i);
            std::cout << "Word: " << w.m_strWord 
                      << " TokenType: " << w.m_TokenType 
                      << " HasOLLE: " << w.HasDes(OLLE) 
                      << std::endl;
        }
    } catch (const std::exception& e) {
        std::cerr << "Exception: " << e.what() << std::endl;
        return 1;
    }
    return 0;
}

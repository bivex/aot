#include "morph_dict/lemmatizer_base_lib/MorphanHolder.h"
#include "synan/SynanLib/SyntaxHolder.h"
#include <iostream>

int main() {
    try {
        std::string rml = "/Volumes/External/Code/aot";
        setenv("RML", rml.c_str(), 1);
        
        CSyntaxHolder holder(morphUkrainian);
        holder.LoadSyntax();
        
        std::string text = "6. ДІЯ ДОГОВОРУ";
        std::cout << "Testing: " << text << std::endl;
        holder.GetSentencesFromSynAn(text, false);
        std::cout << "Success!" << std::endl;
    } catch (const std::exception& e) {
        std::cerr << "Error: " << e.what() << std::endl;
    } catch (...) {
        std::cerr << "Unknown error" << std::endl;
    }
    return 0;
}

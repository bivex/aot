#include "synan/SynanLib/SyntaxHolder.h"
#include <iostream>

int main() {
    try {
        std::cout << "Initializing Ukrainian Syntax..." << std::endl;
        CSyntaxHolder holder(morphUkrainian);
        std::cout << "Loading Ukrainian Syntax..." << std::endl;
        holder.LoadSyntax();
        std::cout << "Ukrainian Syntax loaded successfully!" << std::endl;

        std::string query = "Я йду додому.";
        std::cout << "Analyzing: " << query << std::endl;
        if (holder.GetSentencesFromSynAn(query, false)) {
            std::cout << "Analysis successful!" << std::endl;
        } else {
            std::cout << "Analysis failed!" << std::endl;
        }
    } catch (const std::exception& e) {
        std::cerr << "Exception: " << e.what() << std::endl;
    } catch (...) {
        std::cerr << "Unknown exception" << std::endl;
    }
    return 0;
}

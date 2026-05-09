#include "JVisualSynAnParamBuilder.h"
#include "SynanDmn.h"

#include "common/BigramsReader.h"

TSynanHttpServer::TSynanHttpServer() :
    TRMLHttpServer(),
    RussianSyntaxHolder(morphRussian),
    GermanSyntaxHolder(morphGerman),
    UkrainianSyntaxHolder(morphUkrainian),
    EnglishSyntaxHolder(morphEnglish)
{

}


std::string TSynanHttpServer::ProcessBigrams(TDaemonParsedRequest &request) {
    auto str = evhttp_find_header(&request.headers, "minBigramsFreq");
    if (!str) {
        throw CExpc("minBigramsFreq is not specified");
    }
    int minBigramsFreq = std::stoi(str);
    bool directBigrams = evhttp_find_header(&request.headers, "direct") != nullptr;
    auto sortMode = evhttp_find_header(&request.headers, "sortMode");
    if (!sortMode) {
        throw CExpc("sortMode is not specified");
    }
    std::string wordForm = request.Query;
    return GetConnectedWords(wordForm, minBigramsFreq, directBigrams, sortMode, request.Langua);
}


std::string TSynanHttpServer::ProcessMorphology(TDaemonParsedRequest &request) {
    bool withParadigms = evhttp_find_header(&request.headers, "withparadigms") != nullptr;
    const CMorphanHolder &h  = GetMHolder(request.Langua);
    std::string wordForm = request.Query;
    if (request.Langua == morphEnglish) {
        MakeUpperUtf8(wordForm);
    }
    return h.LemmatizeJson(wordForm, withParadigms);
};


std::string TSynanHttpServer::ProcessSyntax(TDaemonParsedRequest &request) {
    CSyntaxHolder *P = nullptr;
    if (request.Langua == morphRussian) {
        P = &RussianSyntaxHolder;
    } else if (request.Langua == morphGerman) {
        P = &GermanSyntaxHolder;
    } else if (request.Langua == morphUkrainian) {
        P = &UkrainianSyntaxHolder;
    } else if (request.Langua == morphEnglish) {
        P = &EnglishSyntaxHolder;
    }
    
    if (P == nullptr) {
        return "[]";
    }

    std::string query = request.Query;
    if (request.Langua == morphEnglish) {
        MakeUpperUtf8(query);
    }
    return BuildJson(P, query);
};


void TSynanHttpServer::LoadSynan(bool loadBigrams) {
    try {
        LOGI <<"Loading Russian Syntax";
        RussianSyntaxHolder.LoadSyntax();
    } catch (CExpc& e) {
        LOGE << "Failed to load Russian Syntax: " << e.what();
    }
    try {
        LOGI <<"Loading German Syntax";
        GermanSyntaxHolder.LoadSyntax();
    } catch (CExpc& e) {
        LOGE << "Failed to load German Syntax: " << e.what();
    }
    try {
        LOGI <<"Loading Ukrainian Syntax";
        UkrainianSyntaxHolder.LoadSyntax();
    } catch (CExpc& e) {
        LOGE << "Failed to load Ukrainian Syntax: " << e.what();
    }
    try {
        LOGI <<"Loading Ukrainian Morphology";
        UkrainianMorphHolder.LoadMorphology(morphUkrainian);
    } catch (CExpc& e) {
        LOGE << "Failed to load Ukrainian Morphology: " << e.what();
    }
    try {
        LOGI <<"Loading English Morphology";
        EnglishMorphHolder.LoadMorphology(morphEnglish);
    } catch (CExpc& e) {
        LOGE << "Failed to load English Morphology: " << e.what();
    }
    try {
        LOGI <<"Loading English Syntax";
        EnglishSyntaxHolder.LoadSyntax();
    } catch (CExpc& e) {
        LOGE << "Failed to load English Syntax: " << e.what();
    }

    if (loadBigrams) {
        auto path = fs::path(GetRmlVariable()) / "Dicts" / "Bigrams";
        if (!fs::exists(path))
            throw CExpc(Format("cannot find bigrams directory: %s", path.string().c_str()));
        InitializeBigrams(path.string());
    }
};

std::string TSynanHttpServer::OnParsedRequest(TDaemonParsedRequest &req) {
    if (req.Action == "morph") {
        return ProcessMorphology(req);
    } else if (req.Action == "bigrams") {
        return ProcessBigrams(req);
    } else if (req.Action == "syntax") {
        return ProcessSyntax(req);
    } else {
        throw CExpc("unknown action");
    }

}




#include "common/http_server.h"
#include "synan/SynanLib/SyntaxHolder.h"
#include "morph_dict/lemmatizer_base_lib/MorphanHolder.h"

class TSynanHttpServer : public TRMLHttpServer {
    CSyntaxHolder RussianSyntaxHolder;
    CSyntaxHolder GermanSyntaxHolder;
    CSyntaxHolder UkrainianSyntaxHolder;
    CSyntaxHolder EnglishSyntaxHolder;
    CSyntaxHolder SpanishSyntaxHolder;
    CSyntaxHolder LatinSyntaxHolder;
    CSyntaxHolder FrenchSyntaxHolder;
    CSyntaxHolder PortugueseSyntaxHolder;
    CSyntaxHolder FinnishSyntaxHolder;
    CSyntaxHolder ItalianSyntaxHolder;
    CSyntaxHolder HungarianSyntaxHolder;
    CMorphanHolder EnglishMorphHolder;
    CMorphanHolder UkrainianMorphHolder;
    CMorphanHolder SpanishMorphHolder;
    CMorphanHolder FrenchMorphHolder;
    CMorphanHolder PortugueseMorphHolder;
    CMorphanHolder FinnishMorphHolder;
    CMorphanHolder ItalianMorphHolder;
    CMorphanHolder HungarianMorphHolder;

    std::string ProcessMorphology(TDaemonParsedRequest& request);
    std::string ProcessBigrams(TDaemonParsedRequest& request);
    std::string ProcessSyntax(TDaemonParsedRequest& request);


public:
	TSynanHttpServer();
	virtual ~TSynanHttpServer() {};
	std::string OnParsedRequest(TDaemonParsedRequest&) override;
	void LoadSynan(bool loadBigrams);
};


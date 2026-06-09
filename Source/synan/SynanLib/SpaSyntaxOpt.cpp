#include "SpaSyntaxOpt.h"
#include "SpaSentence.h"

const int sSyntaxGroupTypesCount = 4;
const char sSyntaxGroupTypes [sSyntaxGroupTypesCount][30] = 
{
	"NP", "VP", "PP", "SP"
};

CSpaOborDic::CSpaOborDic(const CSyntaxOpt* Opt) : COborDic(Opt)
{
    // Basic Spanish conjunctions
    m_SimpleCoordConj.push_back({"Y", false});
    m_SimpleCoordConj.push_back({"E", false});
    m_SimpleCoordConj.push_back({"O", false});
    m_SimpleCoordConj.push_back({"U", false});
    m_SimpleCoordConj.push_back({"PERO", false});
    m_SimpleCoordConj.push_back({"SINO", false});

    m_SimpleSubConj.push_back("QUE");
    m_SimpleSubConj.push_back("PORQUE");
    m_SimpleSubConj.push_back("COMO");
    m_SimpleSubConj.push_back("SI");
    m_SimpleSubConj.push_back("CUANDO");
    m_SimpleSubConj.push_back("AUNQUE");
}

CSpaSyntaxOpt::CSpaSyntaxOpt(MorphLanguageEnum langua) : CSyntaxOpt(langua)
{
	m_IndeclinableMask = 0;
	m_SyntaxGroupTypes.clear();
	for (size_t i = 0; i < sSyntaxGroupTypesCount; i++)
		m_SyntaxGroupTypes[i] = sSyntaxGroupTypes[i];
	m_piGramTab = new CSpaGramTab();
	m_bEnableLocThesaurus = false;
	m_bEnableFinThesaurus = false;
	m_bEnableCompThesaurus = false;
	m_bEnableOmniThesaurus = false;
}

void CSpaSyntaxOpt::DestroyOptions()
{
	CSyntaxOpt::DestroyOptions();
}

void CSpaSyntaxOpt::InitOptionsLanguageSpecific()
{
	auto synan_directory = GetRegistryString("SpaSynan");
	if (synan_directory.empty()) {
		auto rml = GetRmlVariable();
		synan_directory = MakePath(rml, "Dicts/SpaSynan");
	}
	std::string strFileName = MakePath(synan_directory, "synan.grm");
	m_FormatsGrammar.InitalizeGrammar(morphSpanish, strFileName);
	m_FormatsGrammar.LoadGrammarForGLR(false);
}

bool CSpaSyntaxOpt::is_firm_group(int GroupType) const
{
	return true;
}

bool CSpaSyntaxOpt::IsGroupWithoutWeight(int GroupType, const char* cause) const
{
	return false;
}

bool CSpaSyntaxOpt::IsSimilarGroup(int type) const
{
	return false;
}

CSentence* CSpaSyntaxOpt::NewSentence() const
{
	return new CSpaSentence(this);
}

CLemmatizer* CSpaSyntaxOpt::NewLemmatizer() const
{
	return new CLemmatizerSpanish();
}

COborDic* CSpaSyntaxOpt::NewOborDic(const CSyntaxOpt* opt)
{
	return new CSpaOborDic(opt);
}

CThesaurusForSyntax* CSpaSyntaxOpt::NewThesaurus(const CSyntaxOpt* opt)
{
	return new CSpaThesaurusForSyntax(opt);
}

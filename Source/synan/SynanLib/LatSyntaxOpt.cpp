#include "LatSyntaxOpt.h"
#include "LatSentence.h"

const int latSyntaxGroupTypesCount = 4;
const char latSyntaxGroupTypes [latSyntaxGroupTypesCount][30] =
{
	"NP", "VP", "PP", "SP"
};

CLatOborDic::CLatOborDic(const CSyntaxOpt* Opt) : COborDic(Opt)
{
    // Basic Latin conjunctions
    m_SimpleCoordConj.push_back({"ET", false});
    m_SimpleCoordConj.push_back({"ATQUE", false});
    m_SimpleCoordConj.push_back({"VEL", false});
    m_SimpleCoordConj.push_back({"NEQUE", false});
    m_SimpleCoordConj.push_back({"SED", false});
    m_SimpleCoordConj.push_back({"AUT", false});

    m_SimpleSubConj.push_back("QUOD");
    m_SimpleSubConj.push_back("QUIA");
    m_SimpleSubConj.push_back("CUM");
    m_SimpleSubConj.push_back("SI");
    m_SimpleSubConj.push_back("UT");
    m_SimpleSubConj.push_back("DUM");
    m_SimpleSubConj.push_back("POSTQUAM");
}

CLatSyntaxOpt::CLatSyntaxOpt(MorphLanguageEnum langua) : CSyntaxOpt(langua)
{
	m_IndeclinableMask = 0;
	m_SyntaxGroupTypes.clear();
	for (size_t i = 0; i < latSyntaxGroupTypesCount; i++)
		m_SyntaxGroupTypes[i] = latSyntaxGroupTypes[i];
	m_piGramTab = new CLatGramTab();
	m_bEnableLocThesaurus = false;
	m_bEnableFinThesaurus = false;
	m_bEnableCompThesaurus = false;
	m_bEnableOmniThesaurus = false;
}

void CLatSyntaxOpt::DestroyOptions()
{
	CSyntaxOpt::DestroyOptions();
}

void CLatSyntaxOpt::InitOptionsLanguageSpecific()
{
	auto synan_directory = GetRegistryString("LatSynan");
	if (synan_directory.empty()) {
		auto rml = GetRmlVariable();
		synan_directory = MakePath(rml, "Dicts/LatSynan");
	}
	std::string strFileName = MakePath(synan_directory, "synan.grm");
	m_FormatsGrammar.InitalizeGrammar(morphLatin, strFileName);
	m_FormatsGrammar.LoadGrammarForGLR(false);
}

bool CLatSyntaxOpt::is_firm_group(int GroupType) const
{
	return true;
}

bool CLatSyntaxOpt::IsGroupWithoutWeight(int GroupType, const char* cause) const
{
	return false;
}

bool CLatSyntaxOpt::IsSimilarGroup(int type) const
{
	return false;
}

CSentence* CLatSyntaxOpt::NewSentence() const
{
	return new CLatSentence(this);
}

CLemmatizer* CLatSyntaxOpt::NewLemmatizer() const
{
	return new CLemmatizerLatin();
}

COborDic* CLatSyntaxOpt::NewOborDic(const CSyntaxOpt* opt)
{
	return new CLatOborDic(opt);
}

CThesaurusForSyntax* CLatSyntaxOpt::NewThesaurus(const CSyntaxOpt* opt)
{
	return new CLatThesaurusForSyntax(opt);
}

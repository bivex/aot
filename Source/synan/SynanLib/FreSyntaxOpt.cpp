#include "FreSyntaxOpt.h"
#include "FreSentence.h"

const int sFreSyntaxGroupTypesCount = 4;
const char sFreSyntaxGroupTypes[sFreSyntaxGroupTypesCount][30] =
{
	"NP", "VP", "PP", "SP"
};

CFreOborDic::CFreOborDic(const CSyntaxOpt* Opt) : COborDic(Opt)
{
	// French coordinating conjunctions
	m_SimpleCoordConj.push_back({"ET", false});
	m_SimpleCoordConj.push_back({"OU", false});
	m_SimpleCoordConj.push_back({"MAIS", false});
	m_SimpleCoordConj.push_back({"DONC", false});
	m_SimpleCoordConj.push_back({"NI", false});
	m_SimpleCoordConj.push_back({"SOIT", false});

	// French subordinating conjunctions
	m_SimpleSubConj.push_back("QUE");
	m_SimpleSubConj.push_back("PARCE");
	m_SimpleSubConj.push_back("COMME");
	m_SimpleSubConj.push_back("SI");
	m_SimpleSubConj.push_back("QUAND");
	m_SimpleSubConj.push_back("LORSQUE");
	m_SimpleSubConj.push_back("PUISQUE");
	m_SimpleSubConj.push_back("CAR");
}

CFreSyntaxOpt::CFreSyntaxOpt(MorphLanguageEnum langua) : CSyntaxOpt(langua)
{
	m_IndeclinableMask = 0;
	m_SyntaxGroupTypes.clear();
	for (size_t i = 0; i < sFreSyntaxGroupTypesCount; i++)
		m_SyntaxGroupTypes[i] = sFreSyntaxGroupTypes[i];
	m_piGramTab = new CFreGramTab();
	m_bEnableLocThesaurus = false;
	m_bEnableFinThesaurus = false;
	m_bEnableCompThesaurus = false;
	m_bEnableOmniThesaurus = false;
}

void CFreSyntaxOpt::DestroyOptions()
{
	CSyntaxOpt::DestroyOptions();
}

void CFreSyntaxOpt::InitOptionsLanguageSpecific()
{
	auto synan_directory = GetRegistryString("FreSynan");
	if (synan_directory.empty()) {
		auto rml = GetRmlVariable();
		synan_directory = MakePath(rml, "Dicts/FreSynan");
	}
	std::string strFileName = MakePath(synan_directory, "synan.grm");
	m_FormatsGrammar.InitalizeGrammar(morphFrench, strFileName);
	m_FormatsGrammar.LoadGrammarForGLR(false);
}

bool CFreSyntaxOpt::is_firm_group(int GroupType) const
{
	return true;
}

bool CFreSyntaxOpt::IsGroupWithoutWeight(int GroupType, const char* cause) const
{
	return false;
}

bool CFreSyntaxOpt::IsSimilarGroup(int type) const
{
	return false;
}

CSentence* CFreSyntaxOpt::NewSentence() const
{
	return new CFreSentence(this);
}

CLemmatizer* CFreSyntaxOpt::NewLemmatizer() const
{
	return new CLemmatizerFrench();
}

COborDic* CFreSyntaxOpt::NewOborDic(const CSyntaxOpt* opt)
{
	return new CFreOborDic(opt);
}

CThesaurusForSyntax* CFreSyntaxOpt::NewThesaurus(const CSyntaxOpt* opt)
{
	return new CFreThesaurusForSyntax(opt);
}

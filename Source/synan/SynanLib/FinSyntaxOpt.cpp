#include "FinSyntaxOpt.h"
#include "FinSentence.h"

const int sFinSyntaxGroupTypesCount = 4;
const char sFinSyntaxGroupTypes[sFinSyntaxGroupTypesCount][30] =
{
	"NP", "VP", "PP", "SP"
};

CFinOborDic::CFinOborDic(const CSyntaxOpt* Opt) : COborDic(Opt)
{
	// Finnish coordinating conjunctions
	m_SimpleCoordConj.push_back({"JA", false});
	m_SimpleCoordConj.push_back({"TAI", false});
	m_SimpleCoordConj.push_back({"VAI", false});
	m_SimpleCoordConj.push_back({"MUTTA", false});
	m_SimpleCoordConj.push_back({"JOTTA", false});
	m_SimpleCoordConj.push_back({"ELI", false});
	m_SimpleCoordConj.push_back({"SEKA", false});

	// Finnish subordinating conjunctions
	m_SimpleSubConj.push_back("ETTA");
	m_SimpleSubConj.push_back("KOSKA");
	m_SimpleSubConj.push_back("KUN");
	m_SimpleSubConj.push_back("JOS");
	m_SimpleSubConj.push_back("VAIKKA");
	m_SimpleSubConj.push_back("KUNNES");
	m_SimpleSubConj.push_back("KUIN");
	m_SimpleSubConj.push_back("ETTA");
	m_SimpleSubConj.push_back("JOLLEI");
	m_SimpleSubConj.push_back("SILLI");
	m_SimpleSubConj.push_back("NIINKUIN");
	m_SimpleSubConj.push_back("KUTEN");
	m_SimpleSubConj.push_back("ENNEKUIN");
	m_SimpleSubConj.push_back("SITTA");
	m_SimpleSubConj.push_back("ETTA");
}

CFinSyntaxOpt::CFinSyntaxOpt(MorphLanguageEnum langua) : CSyntaxOpt(langua)
{
	m_IndeclinableMask = 0;
	m_SyntaxGroupTypes.clear();
	for (size_t i = 0; i < sFinSyntaxGroupTypesCount; i++)
		m_SyntaxGroupTypes[i] = sFinSyntaxGroupTypes[i];
	m_piGramTab = new CFinGramTab();
	m_bEnableLocThesaurus = false;
	m_bEnableFinThesaurus = false;
	m_bEnableCompThesaurus = false;
	m_bEnableOmniThesaurus = false;
}

void CFinSyntaxOpt::DestroyOptions()
{
	CSyntaxOpt::DestroyOptions();
}

void CFinSyntaxOpt::InitOptionsLanguageSpecific()
{
	auto synan_directory = GetRegistryString("FinSynan");
	if (synan_directory.empty()) {
		auto rml = GetRmlVariable();
		synan_directory = MakePath(rml, "Dicts/FinSynan");
	}
	std::string strFileName = MakePath(synan_directory, "synan.grm");
	m_FormatsGrammar.InitalizeGrammar(morphFinnish, strFileName);
	m_FormatsGrammar.LoadGrammarForGLR(false);
}

bool CFinSyntaxOpt::is_firm_group(int GroupType) const
{
	return true;
}

bool CFinSyntaxOpt::IsGroupWithoutWeight(int GroupType, const char* cause) const
{
	return false;
}

bool CFinSyntaxOpt::IsSimilarGroup(int type) const
{
	return false;
}

CSentence* CFinSyntaxOpt::NewSentence() const
{
	return new CFinSentence(this);
}

CLemmatizer* CFinSyntaxOpt::NewLemmatizer() const
{
	return new CLemmatizerFinnish();
}

COborDic* CFinSyntaxOpt::NewOborDic(const CSyntaxOpt* opt)
{
	return new CFinOborDic(opt);
}

CThesaurusForSyntax* CFinSyntaxOpt::NewThesaurus(const CSyntaxOpt* opt)
{
	return new CFinThesaurusForSyntax(opt);
}

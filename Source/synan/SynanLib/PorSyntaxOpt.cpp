#include "PorSyntaxOpt.h"
#include "PorSentence.h"

const int sPorSyntaxGroupTypesCount = 4;
const char sPorSyntaxGroupTypes[sPorSyntaxGroupTypesCount][30] =
{
	"NP", "VP", "PP", "SP"
};

CPorOborDic::CPorOborDic(const CSyntaxOpt* Opt) : COborDic(Opt)
{
	// Portuguese coordinating conjunctions
	m_SimpleCoordConj.push_back({"E", false});
	m_SimpleCoordConj.push_back({"OU", false});
	m_SimpleCoordConj.push_back({"MAS", false});
	m_SimpleCoordConj.push_back({"PORTANTO", false});
	m_SimpleCoordConj.push_back({"POIS", false});
	m_SimpleCoordConj.push_back({"NEM", false});
	m_SimpleCoordConj.push_back({"PORÉM", false});
	m_SimpleCoordConj.push_back({"CONTUDO", false});
	m_SimpleCoordConj.push_back({"LOGO", false});

	// Portuguese subordinating conjunctions
	m_SimpleSubConj.push_back("QUE");
	m_SimpleSubConj.push_back("PORQUE");
	m_SimpleSubConj.push_back("COMO");
	m_SimpleSubConj.push_back("SE");
	m_SimpleSubConj.push_back("QUANDO");
	m_SimpleSubConj.push_back("ENQUANTO");
	m_SimpleSubConj.push_back("EMBORA");
	m_SimpleSubConj.push_back("AINDA");
	m_SimpleSubConj.push_back("CONFORME");
}

CPorSyntaxOpt::CPorSyntaxOpt(MorphLanguageEnum langua) : CSyntaxOpt(langua)
{
	m_IndeclinableMask = 0;
	m_SyntaxGroupTypes.clear();
	for (size_t i = 0; i < sPorSyntaxGroupTypesCount; i++)
		m_SyntaxGroupTypes[i] = sPorSyntaxGroupTypes[i];
	m_piGramTab = new CPorGramTab();
	m_bEnableLocThesaurus = false;
	m_bEnableFinThesaurus = false;
	m_bEnableCompThesaurus = false;
	m_bEnableOmniThesaurus = false;
}

void CPorSyntaxOpt::DestroyOptions()
{
	CSyntaxOpt::DestroyOptions();
}

void CPorSyntaxOpt::InitOptionsLanguageSpecific()
{
	auto synan_directory = GetRegistryString("PorSynan");
	if (synan_directory.empty()) {
		auto rml = GetRmlVariable();
		synan_directory = MakePath(rml, "Dicts/PorSynan");
	}
	std::string strFileName = MakePath(synan_directory, "synan.grm");
	m_FormatsGrammar.InitalizeGrammar(morphPortuguese, strFileName);
	m_FormatsGrammar.LoadGrammarForGLR(false);
}

bool CPorSyntaxOpt::is_firm_group(int GroupType) const
{
	return true;
}

bool CPorSyntaxOpt::IsGroupWithoutWeight(int GroupType, const char* cause) const
{
	return false;
}

bool CPorSyntaxOpt::IsSimilarGroup(int type) const
{
	return false;
}

CSentence* CPorSyntaxOpt::NewSentence() const
{
	return new CPorSentence(this);
}

CLemmatizer* CPorSyntaxOpt::NewLemmatizer() const
{
	return new CLemmatizerPortuguese();
}

COborDic* CPorSyntaxOpt::NewOborDic(const CSyntaxOpt* opt)
{
	return new CPorOborDic(opt);
}

CThesaurusForSyntax* CPorSyntaxOpt::NewThesaurus(const CSyntaxOpt* opt)
{
	return new CPorThesaurusForSyntax(opt);
}

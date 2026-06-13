#include "HunSyntaxOpt.h"
#include "HunSentence.h"
#include "HunFormatCaller.h"

const int sHunSyntaxGroupTypesCount = 4;
const char sHunSyntaxGroupTypes[sHunSyntaxGroupTypesCount][30] =
{
	"NP", "VP", "PP", "SP"
};

CHunOborDic::CHunOborDic(const CSyntaxOpt* Opt) : COborDic(Opt)
{
	m_SimpleCoordConj.push_back({"ES", false});
	m_SimpleCoordConj.push_back({"VAGY", false});
	m_SimpleCoordConj.push_back({"DE", false});
	m_SimpleCoordConj.push_back({"HANEM", false});
	m_SimpleCoordConj.push_back({"SE", false});
	m_SimpleCoordConj.push_back({"SEM", false});
	m_SimpleCoordConj.push_back({"IS", false});
	m_SimpleCoordConj.push_back({"PEDIG", false});
	m_SimpleCoordConj.push_back({"TEHAT", false});
	m_SimpleCoordConj.push_back({"VALAMINT", false});

	m_SimpleSubConj.push_back("HOGY");
	m_SimpleSubConj.push_back("HA");
	m_SimpleSubConj.push_back("MERT");
	m_SimpleSubConj.push_back("AMIKOR");
	m_SimpleSubConj.push_back("MIELUTT");
	m_SimpleSubConj.push_back("BAR");
	m_SimpleSubConj.push_back("HABAR");
	m_SimpleSubConj.push_back("MIN");
	m_SimpleSubConj.push_back("AKKOR");
	m_SimpleSubConj.push_back("UTAN");
}

CHunSyntaxOpt::CHunSyntaxOpt(MorphLanguageEnum langua) : CSyntaxOpt(langua)
{
	m_IndeclinableMask = 0;
	m_SyntaxGroupTypes.clear();
	for (size_t i = 0; i < sHunSyntaxGroupTypesCount; i++)
		m_SyntaxGroupTypes[i] = sHunSyntaxGroupTypes[i];
	m_piGramTab = new CHunGramTab();
	m_bEnableLocThesaurus = false;
	m_bEnableFinThesaurus = false;
	m_bEnableCompThesaurus = false;
	m_bEnableOmniThesaurus = false;
}

void CHunSyntaxOpt::DestroyOptions()
{
	CSyntaxOpt::DestroyOptions();
}

void CHunSyntaxOpt::InitOptionsLanguageSpecific()
{
	auto synan_directory = GetRegistryString("HunSynan");
	if (synan_directory.empty()) {
		auto rml = GetRmlVariable();
		synan_directory = MakePath(rml, "Dicts/HunSynan");
	}
	std::string strFileName = MakePath(synan_directory, "synan.grm");
	m_FormatsGrammar.InitalizeGrammar(morphHungarian, strFileName);
	m_FormatsGrammar.LoadGrammarForGLR(false);
}

bool CHunSyntaxOpt::is_firm_group(int GroupType) const
{
	return true;
}

bool CHunSyntaxOpt::IsGroupWithoutWeight(int GroupType, const char* cause) const
{
	return false;
}

bool CHunSyntaxOpt::IsSimilarGroup(int type) const
{
	return false;
}

CSentence* CHunSyntaxOpt::NewSentence() const
{
	return new CHunSentence(this);
}

CLemmatizer* CHunSyntaxOpt::NewLemmatizer() const
{
	return new CLemmatizerHungarian();
}

COborDic* CHunSyntaxOpt::NewOborDic(const CSyntaxOpt* opt)
{
	return new CHunOborDic(opt);
}

CThesaurusForSyntax* CHunSyntaxOpt::NewThesaurus(const CSyntaxOpt* opt)
{
	return new CHunThesaurusForSyntax(opt);
}

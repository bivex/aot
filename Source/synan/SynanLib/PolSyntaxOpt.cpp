#include "PolSyntaxOpt.h"
#include "PolSentence.h"
#include "PolFormatCaller.h"

const int sPolSyntaxGroupTypesCount = 4;
const char sPolSyntaxGroupTypes[sPolSyntaxGroupTypesCount][30] =
{
	"NP", "VP", "PP", "SP"
};

CPolOborDic::CPolOborDic(const CSyntaxOpt* Opt) : COborDic(Opt)
{
	m_SimpleCoordConj.push_back({"I", false});
	m_SimpleCoordConj.push_back({"ORAZ", false});
	m_SimpleCoordConj.push_back({"A", false});
	m_SimpleCoordConj.push_back({"ALE", false});
	m_SimpleCoordConj.push_back({"LUB", false});
	m_SimpleCoordConj.push_back({"ALBO", false});
	m_SimpleCoordConj.push_back({"CZY", false});
	m_SimpleCoordConj.push_back({"NI", false});
	m_SimpleCoordConj.push_back({"WIEC", false});
	m_SimpleCoordConj.push_back({"ZATEM", false});
	m_SimpleCoordConj.push_back({"BO", false});
	m_SimpleCoordConj.push_back({"WIEC", false});

	m_SimpleSubConj.push_back("ZE");
	m_SimpleSubConj.push_back("BO");
	m_SimpleSubConj.push_back("PONIEWAZ");
	m_SimpleSubConj.push_back("GDY");
	m_SimpleSubConj.push_back("JESLI");
	m_SimpleSubConj.push_back("CHOC");
	m_SimpleSubConj.push_back("ABY");
	m_SimpleSubConj.push_back("ZEBY");
	m_SimpleSubConj.push_back("GDYZE");
	m_SimpleSubConj.push_back("ZE");
}

CPolSyntaxOpt::CPolSyntaxOpt(MorphLanguageEnum langua) : CSyntaxOpt(langua)
{
	m_IndeclinableMask = 0;
	m_SyntaxGroupTypes.clear();
	for (size_t i = 0; i < sPolSyntaxGroupTypesCount; i++)
		m_SyntaxGroupTypes[i] = sPolSyntaxGroupTypes[i];
	m_piGramTab = new CPolGramTab();
	m_bEnableLocThesaurus = false;
	m_bEnableFinThesaurus = false;
	m_bEnableCompThesaurus = false;
	m_bEnableOmniThesaurus = false;
}

void CPolSyntaxOpt::DestroyOptions()
{
	CSyntaxOpt::DestroyOptions();
}

void CPolSyntaxOpt::InitOptionsLanguageSpecific()
{
	auto synan_directory = GetRegistryString("PolSynan");
	if (synan_directory.empty()) {
		auto rml = GetRmlVariable();
		synan_directory = MakePath(rml, "Dicts/PolSynan");
	}
	std::string strFileName = MakePath(synan_directory, "synan.grm");
	m_FormatsGrammar.InitalizeGrammar(morphPolish, strFileName);
	m_FormatsGrammar.LoadGrammarForGLR(false);
}

bool CPolSyntaxOpt::is_firm_group(int GroupType) const
{
	return true;
}

bool CPolSyntaxOpt::IsGroupWithoutWeight(int GroupType, const char* cause) const
{
	return false;
}

bool CPolSyntaxOpt::IsSimilarGroup(int type) const
{
	return false;
}

CSentence* CPolSyntaxOpt::NewSentence() const
{
	return new CPolSentence(this);
}

CLemmatizer* CPolSyntaxOpt::NewLemmatizer() const
{
	return new CLemmatizerPolish();
}

COborDic* CPolSyntaxOpt::NewOborDic(const CSyntaxOpt* opt)
{
	return new CPolOborDic(opt);
}

CThesaurusForSyntax* CPolSyntaxOpt::NewThesaurus(const CSyntaxOpt* opt)
{
	return new CPolThesaurusForSyntax(opt);
}

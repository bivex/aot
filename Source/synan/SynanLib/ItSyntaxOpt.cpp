#include "ItSyntaxOpt.h"
#include "ItSentence.h"
#include "ItFormatCaller.h"

const int sItSyntaxGroupTypesCount = 4;
const char sItSyntaxGroupTypes[sItSyntaxGroupTypesCount][30] =
{
	"NP", "VP", "PP", "SP"
};

CItOborDic::CItOborDic(const CSyntaxOpt* Opt) : COborDic(Opt)
{
	m_SimpleCoordConj.push_back({"E", false});
	m_SimpleCoordConj.push_back({"ED", false});
	m_SimpleCoordConj.push_back({"O", false});
	m_SimpleCoordConj.push_back({"MA", false});
	m_SimpleCoordConj.push_back({"PERO", false});
	m_SimpleCoordConj.push_back({"QUINDI", false});
	m_SimpleCoordConj.push_back({"DUNQUE", false});
	m_SimpleCoordConj.push_back({"TUTTAVIA", false});
	m_SimpleCoordConj.push_back({"INOLTRE", false});
	m_SimpleCoordConj.push_back({"OSSIA", false});

	m_SimpleSubConj.push_back("CHE");
	m_SimpleSubConj.push_back("PERCHE");
	m_SimpleSubConj.push_back("COME");
	m_SimpleSubConj.push_back("SE");
	m_SimpleSubConj.push_back("QUANDO");
	m_SimpleSubConj.push_back("MENTRE");
	m_SimpleSubConj.push_back("POICHE");
	m_SimpleSubConj.push_back("BENCHE");
	m_SimpleSubConj.push_back("SEBBENE");
	m_SimpleSubConj.push_back("ANCHE");
	m_SimpleSubConj.push_back("CIOE");
}

CItSyntaxOpt::CItSyntaxOpt(MorphLanguageEnum langua) : CSyntaxOpt(langua)
{
	m_IndeclinableMask = 0;
	m_SyntaxGroupTypes.clear();
	for (size_t i = 0; i < sItSyntaxGroupTypesCount; i++)
		m_SyntaxGroupTypes[i] = sItSyntaxGroupTypes[i];
	m_piGramTab = new CItaGramTab();
	m_bEnableLocThesaurus = false;
	m_bEnableFinThesaurus = false;
	m_bEnableCompThesaurus = false;
	m_bEnableOmniThesaurus = false;
}

void CItSyntaxOpt::DestroyOptions()
{
	CSyntaxOpt::DestroyOptions();
}

void CItSyntaxOpt::InitOptionsLanguageSpecific()
{
	auto synan_directory = GetRegistryString("ItSynan");
	if (synan_directory.empty()) {
		auto rml = GetRmlVariable();
		synan_directory = MakePath(rml, "Dicts/ItSynan");
	}
	std::string strFileName = MakePath(synan_directory, "synan.grm");
	m_FormatsGrammar.InitalizeGrammar(morphItalian, strFileName);
	m_FormatsGrammar.LoadGrammarForGLR(false);
}

bool CItSyntaxOpt::is_firm_group(int GroupType) const
{
	return true;
}

bool CItSyntaxOpt::IsGroupWithoutWeight(int GroupType, const char* cause) const
{
	return false;
}

bool CItSyntaxOpt::IsSimilarGroup(int type) const
{
	return false;
}

CSentence* CItSyntaxOpt::NewSentence() const
{
	return new CItSentence(this);
}

CLemmatizer* CItSyntaxOpt::NewLemmatizer() const
{
	return new CLemmatizerItalian();
}

COborDic* CItSyntaxOpt::NewOborDic(const CSyntaxOpt* opt)
{
	return new CItOborDic(opt);
}

CThesaurusForSyntax* CItSyntaxOpt::NewThesaurus(const CSyntaxOpt* opt)
{
	return new CItThesaurusForSyntax(opt);
}

#include "UkrSyntaxOpt.h"
#include "UkrSentence.h"

const int uSyntaxGroupTypesCount = 4;
const char uSyntaxGroupTypes [uSyntaxGroupTypesCount][30] = 
{
	"NP", "VP", "PP", "SP"
};

CUkrSyntaxOpt::CUkrSyntaxOpt(MorphLanguageEnum langua) : CSyntaxOpt(langua)
{
	m_IndeclinableMask = 0;
	m_SyntaxGroupTypes.clear();
	for (size_t i = 0; i < uSyntaxGroupTypesCount; i++)
		m_SyntaxGroupTypes[i] = uSyntaxGroupTypes[i];
	m_piGramTab = new CUkrGramTab();
	m_bEnableLocThesaurus = false;
	m_bEnableFinThesaurus = false;
	m_bEnableCompThesaurus = false;
	m_bEnableOmniThesaurus = false;
}

void CUkrSyntaxOpt::DestroyOptions()
{
	CSyntaxOpt::DestroyOptions();
}

void CUkrSyntaxOpt::InitOptionsLanguageSpecific()
{
	auto synan_directory = GetRegistryString("UkrSynan");
	if (synan_directory.empty()) {
		auto rml = GetRmlVariable();
		synan_directory = MakePath(rml, "Dicts/UkrSynan");
	}
	std::string strFileName = MakePath(synan_directory, "synan.grm");
	m_FormatsGrammar.InitalizeGrammar(morphUkrainian, strFileName);
	m_FormatsGrammar.LoadGrammarForGLR(false);
}

bool CUkrSyntaxOpt::is_firm_group(int GroupType) const
{
	return true;
}

bool CUkrSyntaxOpt::IsGroupWithoutWeight(int GroupType, const char* cause) const
{
	return false;
}

bool CUkrSyntaxOpt::IsSimilarGroup(int type) const
{
	return false;
}

CSentence* CUkrSyntaxOpt::NewSentence() const
{
	return new CUkrSentence(this);
}

CLemmatizer* CUkrSyntaxOpt::NewLemmatizer() const
{
	return new CLemmatizerUkrainian();
}

#include "UkrOborDic.h"
#include "UkrThesaurus.h"

COborDic* CUkrSyntaxOpt::NewOborDic(const CSyntaxOpt* opt)
{
	return new CUkrOborDic(opt);
}

CThesaurusForSyntax* CUkrSyntaxOpt::NewThesaurus(const CSyntaxOpt* opt)
{
	return new CUkrThesaurusForSyntax(opt);
}

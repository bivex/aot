#include "StdAfx.h"
#include "EngSyntaxOpt.h"
#include "EngSentence.h"
#include "EngOborDic.h"

const int eSyntaxGroupTypesCount = 16;
const char eSyntaxGroupTypes [eSyntaxGroupTypesCount][30] = 
{
	"DET_ADJ_NOUN", "ADJ_NOUN",  "PP",
	"NP_left", "DET_NP_left", "NP_right", "DET_NP_right",
	"SIMIL_NP", "SIMIL_ADJ", "MODIF_ADJ", "DIRECT_OBJ","PARTIC_CONSTR",
	"FOREIGN_GROUP",
	"NP", "VP", "SP"
};


CSentence* CEngSyntaxOpt::NewSentence() const {
	return new CEngSentence(this);
};

CLemmatizer *CEngSyntaxOpt::NewLemmatizer() const {
    return new CLemmatizerEnglish();
};

COborDic * CEngSyntaxOpt::NewOborDic(const CSyntaxOpt* opt)  {
    return new CEngOborDic(opt);
};

class CEngThesaurusForSyntax  : public  CThesaurusForSyntax
{
public:
	CEngThesaurusForSyntax(const CSyntaxOpt* Opt) : CThesaurusForSyntax(Opt) {};
protected:
	void AssignMainGroupsToModel(CGroups& model, const CInnerModel& piModel) {return;};
};

CThesaurusForSyntax* CEngSyntaxOpt::NewThesaurus(const CSyntaxOpt* opt) {
    return new CEngThesaurusForSyntax(opt);
};


CEngSyntaxOpt :: CEngSyntaxOpt (MorphLanguageEnum langua) : CSyntaxOpt(langua)
{
	m_IndeclinableMask = 0;
	m_SyntaxGroupTypes.clear();
	for (size_t i=0; i < eSyntaxGroupTypesCount; i++)
		m_SyntaxGroupTypes[i] = eSyntaxGroupTypes[i];
	m_piGramTab = new CEngGramTab();
m_bEnableLocThesaurus = false;
	m_bEnableFinThesaurus = false;
	m_bEnableCompThesaurus = false;
	m_bEnableOmniThesaurus = false;
	

}


void CEngSyntaxOpt::DestroyOptions ()
{
	CSyntaxOpt::DestroyOptions();
};


void CEngSyntaxOpt :: InitOptionsLanguageSpecific()
{
	auto synan_directory = GetRegistryString("EngSynan");
	std::string strFileName = MakePath(synan_directory, "synan.grm");
	m_FormatsGrammar.InitalizeGrammar(morphEnglish, strFileName);
	m_FormatsGrammar.LoadGrammarForGLR(false);
}




bool CEngSyntaxOpt::is_firm_group(int GroupType) const
{
	return GroupType >= 13; // NP, VP, SP are firm
}

bool CEngSyntaxOpt::IsGroupWithoutWeight(int GroupType, const char* cause) const
{
	return false;

};


bool CEngSyntaxOpt::IsSimilarGroup (int type) const
{
	return false;
};

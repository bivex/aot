#pragma once

#include "morph_dict/agramtab/PorGramTab.h"
#include "synan/SynCommonLib/SyntaxInit.h"
#include "synan/SynCommonLib/oborot.h"
#include "synan/SynCommonLib/ThesaurusForSyntax.h"

class CPorOborDic : public COborDic
{
public:
	CPorOborDic(const class CSyntaxOpt* Opt);
protected:
	bool ReadOborDic(const class CDictionary* piOborDic) override { return true; }
};

class CPorThesaurusForSyntax : public CThesaurusForSyntax
{
public:
	CPorThesaurusForSyntax(const class CSyntaxOpt* Opt) : CThesaurusForSyntax(Opt) {}
protected:
	void AssignMainGroupsToModel(class CGroups& model, const class CInnerModel& piModel) override {}
};

class CPorSyntaxOpt : public CSyntaxOpt
{
public:
	CPorSyntaxOpt(MorphLanguageEnum langua);
	void DestroyOptions();

	void InitOptionsLanguageSpecific();

	bool IsSimilarGroup(int type) const;
	bool IsGroupWithoutWeight(int GroupType, const char* cause) const;
	bool is_firm_group(int GroupType) const;
	CSentence* NewSentence() const override;
	virtual CLemmatizer* NewLemmatizer() const override;
	virtual COborDic* NewOborDic(const CSyntaxOpt* opt) override;
	virtual CThesaurusForSyntax* NewThesaurus(const CSyntaxOpt* opt) override;
};

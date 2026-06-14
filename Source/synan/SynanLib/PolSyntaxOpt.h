#pragma once

#include "morph_dict/agramtab/PolGramTab.h"
#include "synan/SynCommonLib/SyntaxInit.h"
#include "synan/SynCommonLib/oborot.h"
#include "synan/SynCommonLib/ThesaurusForSyntax.h"

class CPolOborDic : public COborDic
{
public:
	CPolOborDic(const class CSyntaxOpt* Opt);
protected:
	bool ReadOborDic(const class CDictionary* piOborDic) override { return true; }
};

class CPolThesaurusForSyntax : public CThesaurusForSyntax
{
public:
	CPolThesaurusForSyntax(const class CSyntaxOpt* Opt) : CThesaurusForSyntax(Opt) {}
protected:
	void AssignMainGroupsToModel(class CGroups& model, const class CInnerModel& piModel) override {}
};

class CPolSyntaxOpt : public CSyntaxOpt
{
public:
	CPolSyntaxOpt(MorphLanguageEnum langua);
	void DestroyOptions() override;
	void InitOptionsLanguageSpecific() override;
	bool is_firm_group(int GroupType) const override;
	bool IsGroupWithoutWeight(int GroupType, const char* cause) const override;
	bool IsSimilarGroup(int type) const override;
	CSentence* NewSentence() const override;
	CLemmatizer* NewLemmatizer() const override;
	COborDic* NewOborDic(const CSyntaxOpt* opt) override;
	CThesaurusForSyntax* NewThesaurus(const CSyntaxOpt* opt) override;
};

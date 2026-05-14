#pragma once

#include "morph_dict/agramtab/UkrGramTab.h"
#include "../SynCommonLib/SyntaxInit.h"

class CUkrSyntaxOpt :	public CSyntaxOpt
{
public:
    CUkrSyntaxOpt (MorphLanguageEnum langua);
	void DestroyOptions ();


	void InitOptionsLanguageSpecific();

	bool IsSimilarGroup (int type) const;
	bool IsGroupWithoutWeight(int GroupType, const char* cause) const;
	bool is_firm_group(int GroupType) const;
	CSentence* NewSentence() const override;
	virtual CLemmatizer *NewLemmatizer() const override;
	virtual COborDic * NewOborDic(const CSyntaxOpt* opt) override;
	virtual CThesaurusForSyntax* NewThesaurus(const CSyntaxOpt* opt) override;



};

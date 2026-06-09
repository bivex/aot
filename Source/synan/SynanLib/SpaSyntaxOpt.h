#pragma once

#include "morph_dict/agramtab/SpaGramTab.h"
#include "synan/SynCommonLib/SyntaxInit.h"
#include "synan/SynCommonLib/oborot.h"
#include "synan/SynCommonLib/ThesaurusForSyntax.h"

class CSpaOborDic : public COborDic 
{
public:
	CSpaOborDic(const class CSyntaxOpt* Opt);
protected:
	bool ReadOborDic(const class CDictionary* piOborDic) override { return true; }
};

class CSpaThesaurusForSyntax : public CThesaurusForSyntax
{
public:
    CSpaThesaurusForSyntax(const class CSyntaxOpt* Opt) : CThesaurusForSyntax(Opt) {}
protected:
    void AssignMainGroupsToModel(class CGroups& model, const class CInnerModel& piModel) override {}
};

class CSpaSyntaxOpt : public CSyntaxOpt
{
public:
    CSpaSyntaxOpt (MorphLanguageEnum langua);
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
